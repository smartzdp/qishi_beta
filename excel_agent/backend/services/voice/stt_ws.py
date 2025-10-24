"""
Speech-to-Text WebSocket service
Wraps examples/realtime_stt.py
"""
import asyncio
import json
from typing import AsyncGenerator
from fastapi import WebSocket
from backend.utils.logging import setup_logger

logger = setup_logger(__name__)


class STTWebSocketService:
    """Real-time Speech-to-Text over WebSocket"""
    
    def __init__(self, openai_api_key: str, model: str = "whisper-1"):
        """
        Initialize STT service
        
        Args:
            openai_api_key: OpenAI API key
            model: STT model name
        """
        self.openai_api_key = openai_api_key
        self.model = model
    
    async def handle_websocket(self, websocket: WebSocket) -> None:
        """
        Handle WebSocket connection for real-time STT
        
        Args:
            websocket: FastAPI WebSocket connection
        """
        await websocket.accept()
        logger.info("STT WebSocket connected")
        
        try:
            # Import OpenAI client
            from openai import AsyncOpenAI
            client = AsyncOpenAI(api_key=self.openai_api_key)
            
            # Buffer for audio chunks
            audio_buffer = bytearray()
            
            while True:
                try:
                    # Receive audio data
                    data = await websocket.receive()
                    
                    if 'bytes' in data:
                        # Audio data
                        audio_chunk = data['bytes']
                        audio_buffer.extend(audio_chunk)
                        
                        # When buffer reaches threshold, transcribe
                        if len(audio_buffer) >= 16000 * 2 * 3:  # 3 seconds at 16kHz 16-bit
                            try:
                                # Save to temp file
                                import tempfile
                                with tempfile.NamedTemporaryFile(suffix='.wav', delete=False) as f:
                                    # Write WAV header (simplified, assumes PCM 16kHz 16-bit mono)
                                    import wave
                                    with wave.open(f.name, 'wb') as wav_file:
                                        wav_file.setnchannels(1)
                                        wav_file.setsampwidth(2)
                                        wav_file.setframerate(16000)
                                        wav_file.writeframes(bytes(audio_buffer))
                                    
                                    wav_path = f.name
                                
                                # Transcribe
                                with open(wav_path, 'rb') as audio_file:
                                    transcript = await client.audio.transcriptions.create(
                                        model=self.model,
                                        file=audio_file,
                                        language='zh'
                                    )
                                
                                # Send result
                                await websocket.send_json({
                                    'type': 'partial_text',
                                    'text': transcript.text
                                })
                                
                                # Clear buffer
                                audio_buffer.clear()
                                
                                # Clean up temp file
                                import os
                                os.unlink(wav_path)
                                
                            except Exception as e:
                                logger.error(f"Transcription error: {e}")
                    
                    elif 'text' in data:
                        # Control message
                        msg = json.loads(data['text'])
                        
                        if msg.get('type') == 'stop':
                            # Final transcription
                            if audio_buffer:
                                # Transcribe remaining buffer
                                # (same logic as above)
                                pass
                            break
                
                except Exception as e:
                    logger.error(f"WebSocket receive error: {e}")
                    break
        
        except Exception as e:
            logger.error(f"STT WebSocket error: {e}")
        
        finally:
            logger.info("STT WebSocket disconnected")
    
    async def simple_transcribe(self, audio_file_path: str) -> str:
        """
        Simple file-based transcription (for testing)
        
        Args:
            audio_file_path: Path to audio file
            
        Returns:
            Transcribed text
        """
        from openai import AsyncOpenAI
        client = AsyncOpenAI(api_key=self.openai_api_key)
        
        with open(audio_file_path, 'rb') as audio_file:
            transcript = await client.audio.transcriptions.create(
                model=self.model,
                file=audio_file,
                language='zh'
            )
        
        return transcript.text

