"""
Test client SDK installation and basic usage
"""
import sys
import os

# Add client_sdk to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'client_sdk', 'src'))

from whisper_asr_client import WhisperASRClient, AuthError, RateLimitError, APIError

BASE_URL = "http://localhost:5001"

def test_client_sdk():
    """Test client SDK basic functionality"""
    print("=" * 60)
    print("Whisper ASR Client SDK Test")
    print("=" * 60)
    
    # Initialize client
    print("\n1. Initializing client...")
    client = WhisperASRClient(BASE_URL)
    print(f"   ✓ Client initialized: {BASE_URL}")
    
    # Test login
    print("\n2. Testing login...")
    try:
        result = client.login("testuser", "password123")
        print(f"   ✓ Login successful")
        print(f"   Token: {result['access_token'][:50]}...")
    except AuthError as e:
        print(f"   ✗ Login failed: {e}")
        sys.exit(1)
    except Exception as e:
        print(f"   ✗ Error: {e}")
        sys.exit(1)
    
    # Test create model
    print("\n3. Testing create model...")
    try:
        model = client.create_model("tiny", device="cpu")
        instance_id = model['instance_id']
        print(f"   ✓ Model created: {instance_id}")
        print(f"   Model name: {model['model_name']}")
        print(f"   Device: {model['device']}")
    except Exception as e:
        print(f"   ✗ Create model failed: {e}")
        sys.exit(1)
    
    # Test list models
    print("\n4. Testing list models...")
    try:
        models = client.list_models()
        print(f"   ✓ List models successful")
        print(f"   Found {models['count']} model(s)")
        for m in models['models']:
            print(f"     - {m['instance_id']}: {m['model_name']} ({m['device']})")
    except Exception as e:
        print(f"   ✗ List models failed: {e}")
    
    # Test transcription (if audio file exists)
    print("\n5. Testing transcription...")
    test_audio_dir = "test_audio"
    if os.path.exists(test_audio_dir):
        # Find first WAV file
        audio_files = [f for f in os.listdir(test_audio_dir) if f.endswith('.wav')]
        if audio_files:
            audio_file = os.path.join(test_audio_dir, sorted(audio_files)[0])
            try:
                print(f"   Transcribing: {os.path.basename(audio_file)}...")
                result = client.transcribe_file(instance_id, audio_file)
                print(f"   ✓ Transcription successful!")
                print(f"   Text: {result['text'][:60]}...")
                print(f"   Language: {result['language']}")
                print(f"   Duration: {result['duration']:.2f} seconds")
            except Exception as e:
                print(f"   ✗ Transcription failed: {e}")
        else:
            print(f"   ⚠ No audio files found in {test_audio_dir}")
    else:
        print(f"   ⚠ Test audio directory not found: {test_audio_dir}")
    
    # Test delete model
    print("\n6. Testing delete model...")
    try:
        client.delete_model(instance_id)
        print(f"   ✓ Model deleted: {instance_id}")
    except Exception as e:
        print(f"   ✗ Delete model failed: {e}")
    
    # Test error handling
    print("\n7. Testing error handling...")
    try:
        # Try to delete non-existent model
        client.delete_model("non-existent-id")
        print(f"   ✗ Should have raised an error")
    except NotFoundError as e:
        print(f"   ✓ NotFoundError raised correctly: {e}")
    except APIError as e:
        print(f"   ✓ APIError raised correctly: {e}")
    except Exception as e:
        print(f"   ⚠ Unexpected error: {e}")
    
    print("\n" + "=" * 60)
    print("Client SDK Test Summary")
    print("=" * 60)
    print("✓ All tests completed!")
    print("=" * 60)

if __name__ == "__main__":
    try:
        test_client_sdk()
    except KeyboardInterrupt:
        print("\n\nTest interrupted by user")
        sys.exit(1)
    except Exception as e:
        print(f"\n✗ Error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

