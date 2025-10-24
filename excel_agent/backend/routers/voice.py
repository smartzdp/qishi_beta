"""
Voice router: WebSocket endpoints for STT and TTS
"""
from fastapi import APIRouter, WebSocket, Depends
from backend.deps import get_settings
from backend.services.voice import STTWebSocketService, TTSWebSocketService
from backend.utils.logging import setup_logger

logger = setup_logger(__name__)
router = APIRouter(prefix="/ws", tags=["voice"])


@router.websocket("/stt")
async def websocket_stt(
    websocket: WebSocket,
    settings = Depends(get_settings)
):
    """
    WebSocket endpoint for real-time Speech-to-Text
    
    Args:
        websocket: WebSocket connection
        settings: App settings
    """
    stt_service = STTWebSocketService(
        openai_api_key=settings.openai_api_key,
        model=settings.stt_model
    )
    
    await stt_service.handle_websocket(websocket)


@router.websocket("/tts")
async def websocket_tts(
    websocket: WebSocket,
    settings = Depends(get_settings)
):
    """
    WebSocket endpoint for real-time Text-to-Speech
    
    Args:
        websocket: WebSocket connection
        settings: App settings
    """
    tts_service = TTSWebSocketService(
        openai_api_key=settings.openai_api_key,
        model=settings.tts_model,
        voice=settings.tts_voice
    )
    
    await tts_service.handle_websocket(websocket)

