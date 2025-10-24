"""
Speech-to-Text WebSocket service using OpenAI Realtime API
Based on examples/realtime_stt.py
"""
import asyncio
import json
import base64
import struct
import websockets
from typing import List
from fastapi import WebSocket
from backend.utils.logging import setup_logger

logger = setup_logger(__name__)

# OpenAI Realtime API configuration
RT_URL = "wss://api.openai.com/v1/realtime?intent=transcription"
EV_DELTA = "conversation.item.input_audio_transcription.delta"
EV_DONE = "conversation.item.input_audio_transcription.completed"
TARGET_SR = 24000
PCM_SCALE = 32767
CHUNK_SAMPLES = 3072  # ≈128 ms at 24 kHz


class STTWebSocketService:
    """Real-time Speech-to-Text using OpenAI Realtime API"""
    
    def __init__(self, openai_api_key: str, model: str = "gpt-4o-transcribe"):
        """
        Initialize STT service
        
        Args:
            openai_api_key: OpenAI API key
            model: STT model name
        """
        self.openai_api_key = openai_api_key
        self.model = model
    
    def _float_to_16bit_pcm(self, float32_array):
        """Convert float32 array to 16-bit PCM bytes"""
        clipped = [max(-1.0, min(1.0, x)) for x in float32_array]
        pcm16 = b''.join(struct.pack('<h', int(x * 32767)) for x in clipped)
        return pcm16
    
    def _base64_encode_audio(self, float32_array):
        """Encode audio as base64 for transmission"""
        pcm_bytes = self._float_to_16bit_pcm(float32_array)
        encoded = base64.b64encode(pcm_bytes).decode('ascii')
        return encoded
    
    def _resample_16k_to_24k(self, audio_16k):
        """Simple linear interpolation resampling from 16kHz to 24kHz"""
        # 24kHz / 16kHz = 1.5 ratio
        ratio = 1.5
        new_length = int(len(audio_16k) * ratio)
        audio_24k = []
        
        for i in range(new_length):
            # Calculate source index
            src_idx = i / ratio
            src_idx_int = int(src_idx)
            src_idx_frac = src_idx - src_idx_int
            
            if src_idx_int + 1 < len(audio_16k):
                # Linear interpolation
                val = audio_16k[src_idx_int] * (1 - src_idx_frac) + audio_16k[src_idx_int + 1] * src_idx_frac
            else:
                # Use last sample if beyond bounds
                val = audio_16k[-1]
            
            audio_24k.append(val)
        
        return audio_24k
    
    def _session(self, model: str, vad: float = 0.5) -> dict:
        """Create transcription session configuration"""
        return {
            "type": "transcription_session.update",
            "session": {
                "input_audio_format": "pcm16",
                "turn_detection": {"type": "server_vad", "threshold": vad},
                "input_audio_transcription": {"model": model},
            },
        }
    
    async def handle_websocket(self, websocket: WebSocket) -> None:
        """
        Handle WebSocket connection for real-time STT
        
        Args:
            websocket: FastAPI WebSocket connection
        """
        await websocket.accept()
        logger.info("STT WebSocket connected")
        
        try:
            # Connect to OpenAI Realtime API
            headers = {
                "Authorization": f"Bearer {self.openai_api_key}", 
                "OpenAI-Beta": "realtime=v1"
            }
            
            # For websockets 12.0, we need to use extra_headers instead of additional_headers
            # Skip SSL verification for development
            import ssl
            ssl_context = ssl.create_default_context()
            ssl_context.check_hostname = False
            ssl_context.verify_mode = ssl.CERT_NONE
            
            async with websockets.connect(RT_URL, extra_headers=list(headers.items()), max_size=None, ssl=ssl_context) as openai_ws:
                # Initialize session
                await openai_ws.send(json.dumps(self._session(self.model)))
                logger.info("Sent session initialization to OpenAI")
                
                # Start transcription receiver
                transcription_task = asyncio.create_task(
                    self._recv_transcripts(openai_ws, websocket)
                )
                
                # Connection established successfully
                logger.info("STT service connected to OpenAI Realtime API")
                
                # Handle audio data from frontend
                audio_buffer = []
                
                while True:
                    try:
                        # Receive data from frontend
                        data = await websocket.receive()
                        
                        if 'bytes' in data:
                            try:
                                # Convert bytes to float32 array (16kHz input)
                                # Ensure we have an even number of bytes for 16-bit samples
                                audio_bytes = data['bytes']
                                logger.info(f"Received audio bytes: {len(audio_bytes)} bytes")
                                
                                if len(audio_bytes) % 2 != 0:
                                    audio_bytes = audio_bytes[:-1]  # Remove odd byte
                                    logger.info(f"Removed odd byte, now: {len(audio_bytes)} bytes")
                                
                                # Unpack as little-endian 16-bit signed integers
                                num_samples = len(audio_bytes) // 2
                                logger.info(f"Unpacking {num_samples} samples")
                                
                                pcm_int16 = struct.unpack(f'<{num_samples}h', audio_bytes)
                                float_chunk_16k = [x / PCM_SCALE for x in pcm_int16]
                                
                                # Resample from 16kHz to 24kHz (simple linear interpolation)
                                float_chunk = self._resample_16k_to_24k(float_chunk_16k)
                                logger.info(f"Resampled to {len(float_chunk)} samples")
                                
                                # Send to OpenAI Realtime API
                                payload = {
                                    "type": "input_audio_buffer.append",
                                    "audio": self._base64_encode_audio(float_chunk),
                                }
                                await openai_ws.send(json.dumps(payload))
                                logger.info("Sent audio to OpenAI Realtime API")
                                
                            except Exception as e:
                                logger.error(f"Audio processing error: {e}")
                                continue
                            
                        elif 'text' in data:
                            # Control message
                            msg = json.loads(data['text'])
                            
                            if msg.get('type') == 'stop':
                                # Signal end of audio
                                await openai_ws.send(json.dumps({"type": "input_audio_buffer.commit"}))
                                logger.info("Sent commit signal to OpenAI")
                                # Wait longer for final transcription
                                await asyncio.sleep(5)
                                break
                    
                    except Exception as e:
                        logger.error(f"WebSocket error: {e}")
                        break
                
                # Wait for transcription to complete
                await transcription_task
                
        except Exception as e:
            logger.error(f"STT service error: {e}")
        finally:
            logger.info("STT WebSocket disconnected")
    
    async def _recv_transcripts(self, openai_ws, frontend_ws) -> None:
        """Receive transcripts from OpenAI and forward to frontend"""
        
        try:
            async for msg in openai_ws:
                logger.info(f"Received from OpenAI: {msg}")
                ev = json.loads(msg)
                
                typ = ev.get("type")
                logger.info(f"Message type: {typ}")
                
                if typ == EV_DELTA:
                    # Skip partial text to avoid duplication
                    delta = ev.get("delta")
                    if delta:
                        logger.info(f"Partial (not sent): {delta}")
                        
                elif typ == EV_DONE:
                    # Sentence finished - get transcript from the event
                    transcript = ev.get("transcript")
                    if transcript and transcript.strip():
                        try:
                            await frontend_ws.send_json({
                                'type': 'final_text',
                                'text': transcript.strip()
                            })
                            logger.info(f"Final: {transcript.strip()}")
                        except Exception as e:
                            logger.error(f"Error sending final text: {e}")
                else:
                    logger.info(f"Other message type: {typ}, content: {ev}")
                    
        except websockets.ConnectionClosedOK:
            logger.info("OpenAI WebSocket closed normally")
        except Exception as e:
            logger.error(f"Transcription receiver error: {e}")
        
        # Flush any remaining partial sentence
        if current:
            full_text = "".join(current)
            if full_text.strip():
                try:
                    await frontend_ws.send_json({
                        'type': 'final_text',
                        'text': full_text.strip()
                    })
                    logger.info(f"Final (flush): {full_text.strip()}")
                except Exception as e:
                    logger.error(f"Error sending final text: {e}")