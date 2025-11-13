"""
Test transcription functionality with downloaded audio files
"""
import requests
import json
import base64
import os
import sys

BASE_URL = "http://localhost:5001"

def login():
    """Login and get token"""
    url = f"{BASE_URL}/api/auth/login"
    data = {
        "username": "testuser",
        "password": "password123"
    }
    
    response = requests.post(url, json=data)
    if response.status_code == 200:
        token = response.json().get('access_token')
        print(f"✓ Login successful")
        return token
    else:
        print(f"✗ Login failed: {response.json()}")
        return None

def create_model(token):
    """Create a model instance"""
    url = f"{BASE_URL}/api/asr/models"
    headers = {"Authorization": f"Bearer {token}"}
    data = {
        "model_name": "tiny",  # Use tiny for faster testing
        "device": "cpu"
    }
    
    response = requests.post(url, json=data, headers=headers)
    if response.status_code in [200, 201]:
        instance_id = response.json().get('instance_id')
        print(f"✓ Model created: {instance_id}")
        return instance_id
    else:
        print(f"✗ Model creation failed: {response.json()}")
        return None

def transcribe_audio(token, instance_id, audio_file_path):
    """Transcribe an audio file"""
    # Read audio file and convert to base64
    with open(audio_file_path, 'rb') as f:
        audio_bytes = f.read()
        audio_base64 = base64.b64encode(audio_bytes).decode('utf-8')
    
    url = f"{BASE_URL}/api/asr/transcribe"
    headers = {"Authorization": f"Bearer {token}"}
    data = {
        "instance_id": instance_id,
        "audio_base64": audio_base64
    }
    
    print(f"\n  Transcribing: {os.path.basename(audio_file_path)}...")
    response = requests.post(url, json=data, headers=headers)
    
    if response.status_code == 200:
        result = response.json()
        return result
    else:
        print(f"  ✗ Transcription failed: {response.json()}")
        return None

def read_expected_text(transcript_file):
    """Read expected text from transcript file"""
    if os.path.exists(transcript_file):
        with open(transcript_file, 'r', encoding='utf-8') as f:
            return f.read().strip()
    return None

def test_transcription():
    """Test transcription with audio files"""
    print("=" * 60)
    print("Whisper ASR Transcription Test")
    print("=" * 60)
    
    # Login
    token = login()
    if not token:
        print("\n✗ Cannot proceed without authentication token")
        sys.exit(1)
    
    # Create model
    instance_id = create_model(token)
    if not instance_id:
        print("\n✗ Cannot proceed without model instance")
        sys.exit(1)
    
    # Test audio directory
    test_audio_dir = "test_audio"
    if not os.path.exists(test_audio_dir):
        print(f"\n✗ Test audio directory not found: {test_audio_dir}")
        print("Please run download_test_audio.py first to download test audio files.")
        sys.exit(1)
    
    # Find audio files (limit to first 5, prefer .wav over .flac)
    audio_files = []
    wav_files = [f for f in sorted(os.listdir(test_audio_dir)) if f.endswith('.wav')]
    # Only use .wav files, or if no .wav files, use .flac
    files_to_test = wav_files[:5] if wav_files else [f for f in sorted(os.listdir(test_audio_dir)) if f.endswith('.flac')][:5]
    
    for file in files_to_test:
        audio_path = os.path.join(test_audio_dir, file)
        transcript_path = os.path.join(test_audio_dir, file.replace('.wav', '.txt').replace('.flac', '.txt'))
        audio_files.append({
            'audio_path': audio_path,
            'transcript_path': transcript_path,
            'name': file
        })
    
    if not audio_files:
        print(f"\n✗ No audio files found in {test_audio_dir}")
        sys.exit(1)
    
    print(f"\n✓ Found {len(audio_files)} audio file(s) (testing first 5)")
    print("-" * 60)
    
    # Test transcription for each audio file
    results = []
    for i, audio_file in enumerate(audio_files, 1):
        print(f"\n[{i}/{len(audio_files)}] Testing: {audio_file['name']}")
        
        # Read expected text
        expected_text = read_expected_text(audio_file['transcript_path'])
        if expected_text:
            print(f"  Expected: {expected_text[:60]}...")
        
        # Transcribe
        result = transcribe_audio(token, instance_id, audio_file['audio_path'])
        
        if result:
            transcribed_text = result.get('text', '').strip()
            detected_language = result.get('language', '')
            duration = result.get('duration', 0.0)
            
            print(f"  ✓ Transcription successful!")
            if transcribed_text:
                # Show first 80 characters, then full text if longer
                if len(transcribed_text) > 80:
                    print(f"    Text: {transcribed_text[:80]}...")
                    print(f"    Full text: {transcribed_text}")
                else:
                    print(f"    Text: {transcribed_text}")
            else:
                print(f"    Text: (empty)")
            print(f"    Language: {detected_language}")
            print(f"    Duration: {duration:.2f} seconds")
            
            # Compare with expected text if available
            if expected_text:
                # Normalize both texts for comparison (remove punctuation, lowercase)
                import re
                def normalize_text(text):
                    # Remove punctuation, convert to lowercase, remove extra spaces
                    text = re.sub(r'[^\w\s]', '', text.lower())
                    text = re.sub(r'\s+', ' ', text).strip()
                    return text
                
                expected_normalized = normalize_text(expected_text)
                transcribed_normalized = normalize_text(transcribed_text)
                
                # Check for similarity (word-level matching)
                expected_words = set(expected_normalized.split())
                transcribed_words = set(transcribed_normalized.split())
                
                # Calculate similarity
                if expected_words and transcribed_words:
                    common_words = expected_words.intersection(transcribed_words)
                    similarity = len(common_words) / max(len(expected_words), len(transcribed_words))
                    
                    if similarity > 0.7:
                        print(f"    ✓ Matches expected text ({similarity*100:.0f}% similarity)")
                    elif similarity > 0.5:
                        print(f"    ⚠ Partial match ({similarity*100:.0f}% similarity)")
                    else:
                        print(f"    ⚠ Low similarity ({similarity*100:.0f}% similarity)")
                elif expected_normalized in transcribed_normalized or transcribed_normalized in expected_normalized:
                    print(f"    ✓ Matches expected text (substring match)")
                else:
                    print(f"    ⚠ Different from expected text")
            
            results.append({
                'file': audio_file['name'],
                'expected': expected_text,
                'transcribed': transcribed_text,
                'language': detected_language,
                'duration': duration
            })
        else:
            results.append({
                'file': audio_file['name'],
                'expected': expected_text,
                'transcribed': None,
                'error': 'Transcription failed'
            })
    
    # Cleanup: Delete model
    print(f"\n{'='*60}")
    print("Cleaning up...")
    url = f"{BASE_URL}/api/asr/models/{instance_id}"
    headers = {"Authorization": f"Bearer {token}"}
    response = requests.delete(url, headers=headers)
    if response.status_code == 204:
        print(f"✓ Model deleted: {instance_id}")
    else:
        print(f"✗ Model deletion failed: {response.status_code}")
    
    # Summary
    print(f"\n{'='*60}")
    print("Test Summary")
    print("=" * 60)
    successful = sum(1 for r in results if r.get('transcribed') is not None)
    print(f"Total files: {len(results)}")
    print(f"Successful: {successful}")
    print(f"Failed: {len(results) - successful}")
    
    if successful > 0:
        print(f"\n✓ Transcription test completed successfully!")
    else:
        print(f"\n✗ All transcriptions failed")
        sys.exit(1)

if __name__ == "__main__":
    try:
        test_transcription()
    except KeyboardInterrupt:
        print("\n\nTest interrupted by user")
        sys.exit(1)
    except Exception as e:
        print(f"\n✗ Error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

