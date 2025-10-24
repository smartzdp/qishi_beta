
import os
from pathlib import Path
from openai import OpenAI

OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

client = OpenAI(api_key=OPENAI_API_KEY)
print("✅ OpenAI client ready")


# None realtime 
AUDIO_PATH = Path('./example.mp3') 
MODEL_NAME = "gpt-4o-transcribe"

if AUDIO_PATH.exists():
    with AUDIO_PATH.open('rb') as f:
        transcript = client.audio.transcriptions.create(
            file=f,
            model=MODEL_NAME,
            response_format='text',
        )
    print('\n--- TRANSCRIPT ---\n')
    print(transcript)
else:
    print('⚠️ Provide a valid audio file')
    