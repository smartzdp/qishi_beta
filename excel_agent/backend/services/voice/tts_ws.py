"""
Text-to-Speech WebSocket service
Wraps examples/realtime_tts.py
"""
import asyncio
from typing import AsyncGenerator
from fastapi import WebSocket
from backend.utils.logging import setup_logger

logger = setup_logger(__name__)


class TTSWebSocketService:
    """Real-time Text-to-Speech over WebSocket"""
    
    def __init__(self, openai_api_key: str, model: str = "tts-1", voice: str = "alloy"):
        """
        Initialize TTS service
        
        Args:
            openai_api_key: OpenAI API key
            model: TTS model name
            voice: Voice name
        """
        self.openai_api_key = openai_api_key
        self.model = model
        self.voice = voice
    
    async def handle_websocket(self, websocket: WebSocket) -> None:
        """
        Handle WebSocket connection for real-time TTS
        
        Args:
            websocket: FastAPI WebSocket connection
        """
        await websocket.accept()
        logger.info("TTS WebSocket connected")
        
        try:
            from openai import AsyncOpenAI
            client = AsyncOpenAI(api_key=self.openai_api_key)
            
            while True:
                try:
                    # Receive text to speak
                    data = await websocket.receive_text()
                    
                    # Generate speech
                    response = await client.audio.speech.create(
                        model=self.model,
                        voice=self.voice,
                        input=data
                    )
                    
                    # Stream audio back
                    audio_data = response.content
                    
                    # Send in chunks
                    chunk_size = 4096
                    for i in range(0, len(audio_data), chunk_size):
                        chunk = audio_data[i:i+chunk_size]
                        await websocket.send_bytes(chunk)
                    
                    # Send end marker
                    await websocket.send_json({'type': 'end'})
                
                except Exception as e:
                    logger.error(f"TTS error: {e}")
                    break
        
        except Exception as e:
            logger.error(f"TTS WebSocket error: {e}")
        
        finally:
            logger.info("TTS WebSocket disconnected")
    
    async def synthesize(self, text: str) -> bytes:
        """
        Synthesize speech from text
        
        Args:
            text: Text to synthesize
            
        Returns:
            Audio bytes
        """
        from openai import AsyncOpenAI
        client = AsyncOpenAI(api_key=self.openai_api_key)
        
        response = await client.audio.speech.create(
            model=self.model,
            voice=self.voice,
            input=text
        )
        
        return response.content

