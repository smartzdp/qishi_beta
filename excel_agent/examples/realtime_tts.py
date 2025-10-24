# realtime_say_as_it_thinks.py
import os, asyncio, json, base64, signal, queue
import numpy as np
import websockets
import sounddevice as sd

# ── Config ────────────────────────────────────────────────────────────────────
MODEL = os.getenv("REALTIME_MODEL", "gpt-4o-mini-realtime-preview")  # low-cost realtime model
WS_URL = f"wss://api.openai.com/v1/realtime?model={MODEL}"
API_KEY = os.environ["OPENAI_API_KEY"]
SAMPLE_RATE = 24000  # Realtime audio is PCM @ 24kHz mono
VOICE = os.getenv("REALTIME_VOICE", "alloy")  # pick a Realtime voice

# ── Simple PCM player that accepts byte chunks as they arrive ─────────────────
# ── Simple PCM player with a lock-free ring buffer ───────────────────────────
import threading
from collections import deque

class PCMPlayer:
    def __init__(self, samplerate=SAMPLE_RATE, channels=1, dtype="int16", blocksize=1200):
        self.stream = sd.RawOutputStream(
            samplerate=samplerate, channels=channels, dtype=dtype,
            blocksize=blocksize, callback=self._callback
        )
        self.framesize = 2  # 16-bit mono
        self._buf = bytearray()
        self._q = deque()           # holds incoming chunks
        self._lock = threading.Lock()
        self._silence = b"\x00" * (blocksize * self.framesize)

    def _callback(self, outdata, frames, *_):
        need = frames * self.framesize
        with self._lock:
            # Pull from queue into buffer until we have enough to fill 'need'
            while len(self._buf) < need and self._q:
                self._buf += self._q.popleft()
            if len(self._buf) >= need:
                outdata[:] = self._buf[:need]
                del self._buf[:need]
            else:
                # Not enough audio → pad with silence, keep leftovers for next callback
                outdata[:] = (self._buf + b"\x00" * (need - len(self._buf)))[:need]
                self._buf.clear()

    async def write(self, pcm_bytes: bytes):
        # non-blocking: just enqueue; callback will consume exactly what it needs
        with self._lock:
            self._q.append(pcm_bytes)

    def is_empty(self) -> bool:
        """Check if the audio queue is empty"""
        with self._lock:
            return len(self._q) == 0 and len(self._buf) == 0

    def start(self): self.stream.start()
    def stop(self):  self.stream.stop(); self.stream.close()

# ── WebSocket helpers ────────────────────────────────────────────────────────
def session_update_event():
    # Configure audio output (voice + PCM), and constrain behavior to verbatim speaking
    return {
        "type": "session.update",
        "session": {
            "instructions": "You are a text-to-speech assistant. Read the user's message exactly as written, word for word. Do not add, remove, or change any words. Just read it aloud.",
            "voice": VOICE,
            "output_audio_format": "pcm16",  # 24kHz, 16-bit, mono
            "modalities": ["text", "audio"],  # Required: both text and audio
            "turn_detection": None,  # Disable turn detection for more control
        },
    }

def new_user_item(text: str):
    # Add a user message to the conversation
    return {
        "type": "conversation.item.create",
        "item": {
            "type": "message",
            "role": "user",
            "content": [{"type": "input_text", "text": text}],
        },
    }

def create_audio_response():
    # Ask model to speak now; must include both audio and text modalities
    return {
        "type": "response.create",
        "response": {
            "modalities": ["text", "audio"],  # Both required by the API
        },
    }

def cancel_response():
    # Barge in (stop currently speaking response)
    return {"type": "response.cancel"}

# ── Receiver: read WS events, play audio deltas as they stream ───────────────
async def recv_loop(ws, player: PCMPlayer, response_done_event=None, show_transcript=True, debug=False):
    while True:
        msg = json.loads(await ws.recv())
        t = msg.get("type")
        
        if debug and ("done" in t or "audio" in t):
            print(f"\n[DEBUG] Event: {t}", flush=True)

        if t in ("response.output_audio.delta", "response.audio.delta"):
            pcm = base64.b64decode(msg["delta"])
            await player.write(pcm)

        elif t in ("response.output_audio_transcript.delta", "response.audio_transcript.delta"):
            if show_transcript:
                print(msg.get("delta", ""), end="", flush=True)

        elif t == "response.done":  # Only wait for the final response.done, not audio.done
            if response_done_event:
                if debug:
                    print(f"\n[DEBUG] Setting response_done event", flush=True)
                response_done_event.set()

        elif t == "error":
            print("Server error:", msg)

# ── Sender: simulate a streaming LLM by chunking a string and barge-in speak ─
async def simulate_stream_and_speak(ws, text: str, words_per_chunk=6, delay=0.35, barge_in=True):
    words = text.split()
    chunks = [" ".join(words[i:i+words_per_chunk]) for i in range(0, len(words), words_per_chunk)]

    for i, chunk in enumerate(chunks):
        # Optionally barge-in (cancel any ongoing speech) before speaking the next chunk
        if barge_in and i > 0:
            await ws.send(json.dumps(cancel_response()))
        # Add the chunk as a new user item and request an audio response
        await ws.send(json.dumps(new_user_item(chunk)))
        await ws.send(json.dumps(create_audio_response()))
        await asyncio.sleep(delay)  # mimic tokens continuing to arrive


async def llm_stream_to_speech(user_prompt: str):
    """Stream LLM output and speak it in real-time using OpenAI Realtime API"""
    from openai import OpenAI
    import re
    
    # Regular OpenAI client for text streaming
    text_client = OpenAI()
    
    # Realtime API setup for TTS
    headers = {
        "Authorization": f"Bearer {API_KEY}",
        "OpenAI-Beta": "realtime=v1",
    }
    
    player = PCMPlayer()
    player.start()
    
    try:
        async with websockets.connect(WS_URL, additional_headers=headers, max_size=None) as ws:
            # Configure TTS session
            await ws.send(json.dumps(session_update_event()))
            
            # Event to track when TTS response is done
            response_done = asyncio.Event()
            response_done.set()  # Initially set (no response in progress)
            
            # Start audio receiver with response tracking (don't show TTS transcript since we show LLM output)
            recv_task = asyncio.create_task(recv_loop(ws, player, response_done, show_transcript=False, debug=False))
            
            # Stream LLM response
            print(f"User: {user_prompt}\n")
            print("Assistant: ", end="", flush=True)
            
            stream = text_client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[{"role": "user", "content": user_prompt}],
                stream=True,
            )
            
            text_buffer = ""  # Accumulate text
            
            for chunk in stream:
                if chunk.choices[0].delta.content:
                    text = chunk.choices[0].delta.content
                    print(text, end="", flush=True)
                    text_buffer += text
                    
                    # Look for sentence endings (., !, ?, or newline)
                    sentences = re.split(r'([.!?\n]+\s*)', text_buffer)
                    
                    # If we have complete sentences, speak them
                    while len(sentences) >= 3:  # We need text + delimiter + remaining
                        sentence = sentences[0] + (sentences[1] if len(sentences) > 1 else "")
                        sentence = sentence.strip()
                        
                        if sentence:
                            # Wait for any previous TTS to complete
                            await response_done.wait()
                            
                            # Send this sentence to TTS
                            response_done.clear()
                            await ws.send(json.dumps(new_user_item(sentence)))
                            await ws.send(json.dumps(create_audio_response()))
                        
                        # Remove processed sentence from buffer
                        text_buffer = "".join(sentences[2:])
                        sentences = re.split(r'([.!?\n]+\s*)', text_buffer)
            
            # Speak any remaining text
            if text_buffer.strip():
                await response_done.wait()
                response_done.clear()
                await ws.send(json.dumps(new_user_item(text_buffer.strip())))
                await ws.send(json.dumps(create_audio_response()))
                await response_done.wait()
            
            print("\n")  # New line after streaming completes
            
            # Wait for audio queue to finish playing
            # The response is done, but audio may still be in the playback queue
            max_wait = 10  # Maximum 10 seconds to wait
            wait_count = 0
            while not player.is_empty() and wait_count < max_wait * 10:
                await asyncio.sleep(0.1)
                wait_count += 1
            
            # Add a small buffer for the last audio to finish
            await asyncio.sleep(0.5)
            
            recv_task.cancel()
            try:
                await recv_task
            except asyncio.CancelledError:
                pass
    
    finally:
        player.stop()

if __name__ == "__main__":
    # Example usage: Stream LLM response and speak it in real-time
    asyncio.run(llm_stream_to_speech("你是谁"))