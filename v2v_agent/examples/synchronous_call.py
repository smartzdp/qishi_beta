import wave
import base64

from zhipuai import ZhipuAI

def save_audio_as_wav(audio_data, filepath):
    with wave.open(filepath, 'wb') as wav_file:
        wav_file.setnchannels(1)
        wav_file.setsampwidth(2)
        wav_file.setframerate(44100)
        wav_file.writeframes(audio_data)
    print(f"Audio saved to {filepath}")


client = ZhipuAI(api_key="your-api-key-here") # Fill in your own APIKey

response = client.chat.completions.create(
    model="glm-4-voice",  # Fill in the model name you want to call
    messages=[
        {
            "role": "user",
            "content": [
                {
                    "type": "text",
                    "text": "Hello"
                },
                {
                    "type": "input_audio",
                    "input_audio": {
                        "data": "<base64_string>",
                        "format":"wav"
                    }
                }
            ]
        },
    ],
    max_tokens=1024,
    stream=False
)
print(response)
# Get audio data
audio_data = response.choices[0].message.audio['data']
decoded_data = base64.b64decode(audio_data)
# Write the decoded data to a WAV file
with open("output.wav", 'wb') as wav_file:
    wav_file.write(decoded_data)