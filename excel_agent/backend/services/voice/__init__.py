"""
Voice services (STT and TTS)
"""
from backend.services.voice.stt_ws import STTWebSocketService
from backend.services.voice.tts_ws import TTSWebSocketService

__all__ = ['STTWebSocketService', 'TTSWebSocketService']

