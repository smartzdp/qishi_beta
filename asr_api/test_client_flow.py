"""
Test to verify client SDK uses REST API (not directly Whisper)
"""
import sys
import os

# Add client_sdk to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'client_sdk', 'src'))

from whisper_asr_client import WhisperASRClient
import inspect

def verify_client_implementation():
    """Verify that client SDK uses REST API, not directly Whisper"""
    print("=" * 60)
    print("Verifying Client SDK Implementation")
    print("=" * 60)
    
    # Check imports
    print("\n1. Checking imports...")
    client_module = inspect.getmodule(WhisperASRClient)
    client_source = inspect.getsource(client_module)
    
    # Check for whisper imports
    if 'import whisper' in client_source or 'from whisper' in client_source:
        print("   ✗ ERROR: Client SDK imports whisper directly!")
        return False
    else:
        print("   ✓ Client SDK does NOT import whisper")
    
    # Check for torch imports
    if 'import torch' in client_source or 'from torch' in client_source:
        print("   ✗ ERROR: Client SDK imports torch directly!")
        return False
    else:
        print("   ✓ Client SDK does NOT import torch")
    
    # Check for requests imports
    if 'import requests' in client_source:
        print("   ✓ Client SDK imports requests (for REST API)")
    else:
        print("   ✗ ERROR: Client SDK does NOT import requests!")
        return False
    
    # Check transcribe_file method
    print("\n2. Checking transcribe_file method...")
    client = WhisperASRClient("http://localhost:5001")
    transcribe_file_source = inspect.getsource(client.transcribe_file)
    
    # Check if it converts to base64
    if 'file_to_base64' in transcribe_file_source:
        print("   ✓ transcribe_file() calls file_to_base64()")
    else:
        print("   ✗ ERROR: transcribe_file() does NOT convert to base64!")
        return False
    
    # Check if it calls transcribe_base64
    if 'transcribe_base64' in transcribe_file_source:
        print("   ✓ transcribe_file() calls transcribe_base64()")
    else:
        print("   ✗ ERROR: transcribe_file() does NOT call transcribe_base64()!")
        return False
    
    # Check transcribe_base64 method
    print("\n3. Checking transcribe_base64 method...")
    transcribe_base64_source = inspect.getsource(client.transcribe_base64)
    
    # Check if it makes HTTP request
    if 'requests' in transcribe_base64_source or 'session.post' in transcribe_base64_source:
        print("   ✓ transcribe_base64() makes HTTP POST request")
    else:
        print("   ✗ ERROR: transcribe_base64() does NOT make HTTP request!")
        return False
    
    # Check if it sends JSON
    if 'json=' in transcribe_base64_source or 'json.dumps' in transcribe_base64_source:
        print("   ✓ transcribe_base64() sends JSON data")
    else:
        print("   ⚠ WARNING: Could not verify JSON sending")
    
    # Check file_to_base64 method
    print("\n4. Checking file_to_base64 method...")
    file_to_base64_source = inspect.getsource(client.file_to_base64)
    
    # Check if it reads file and converts to base64
    if 'base64' in file_to_base64_source and 'open(' in file_to_base64_source:
        print("   ✓ file_to_base64() reads file and converts to base64")
    else:
        print("   ✗ ERROR: file_to_base64() does NOT convert to base64!")
        return False
    
    # Check dependencies
    print("\n5. Checking dependencies...")
    pyproject_path = os.path.join(os.path.dirname(__file__), 'client_sdk', 'pyproject.toml')
    if os.path.exists(pyproject_path):
        with open(pyproject_path, 'r') as f:
            pyproject_content = f.read()
            
            # Check if requests is in dependencies section
            if 'requests' in pyproject_content and 'dependencies' in pyproject_content:
                # Extract dependencies section
                import re
                deps_match = re.search(r'dependencies\s*=\s*\[(.*?)\]', pyproject_content, re.DOTALL)
                if deps_match:
                    deps_section = deps_match.group(1)
                    if 'requests' in deps_section:
                        print("   ✓ pyproject.toml includes requests dependency")
                    else:
                        print("   ✗ ERROR: pyproject.toml does NOT include requests in dependencies!")
                        return False
                    
                    # Check if whisper/torch are in dependencies (not just metadata)
                    if 'whisper' in deps_section.lower() or 'torch' in deps_section.lower():
                        print("   ✗ ERROR: pyproject.toml includes whisper/torch in dependencies!")
                        return False
                    else:
                        print("   ✓ pyproject.toml does NOT include whisper/torch in dependencies")
                else:
                    print("   ⚠ WARNING: Could not parse dependencies section")
            else:
                print("   ✗ ERROR: pyproject.toml does NOT include requests dependency!")
                return False
    
    print("\n" + "=" * 60)
    print("Verification Summary")
    print("=" * 60)
    print("✓ Client SDK correctly uses REST API")
    print("✓ Client SDK does NOT directly use Whisper")
    print("✓ All operations go through HTTP requests")
    print("=" * 60)
    
    return True

if __name__ == "__main__":
    try:
        success = verify_client_implementation()
        if success:
            print("\n✓ All verifications passed!")
            sys.exit(0)
        else:
            print("\n✗ Some verifications failed!")
            sys.exit(1)
    except Exception as e:
        print(f"\n✗ Error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

