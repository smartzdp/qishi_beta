"""
Python wrapper for Instagram password encryption using Node.js

This script calls the JavaScript implementation to get exact Instagram-compatible
encrypted passwords while providing a Python interface.
"""

import subprocess
import json
import os
import sys
import requests
from typing import Optional


class InstagramEncryptionWrapper:
    """
    Python wrapper for the JavaScript Instagram password encryption.
    """
    
    def __init__(self, js_script_path: str = None):
        """
        Initialize the wrapper.
        
        Args:
            js_script_path: Path to the JavaScript encryption script
        """
        if js_script_path is None:
            # Default to the silent implementation for clean output
            script_dir = os.path.dirname(os.path.abspath(__file__))
            js_script_path = os.path.join(script_dir, 'encrypt_silent.js')
        
        self.js_script_path = js_script_path
        self.fresh_keys = None
        
        # Verify Node.js is available
        try:
            result = subprocess.run(['node', '--version'], 
                                  capture_output=True, text=True, timeout=5)
            if result.returncode != 0:
                raise RuntimeError("Node.js not found or not working")
            print(f"✅ Node.js version: {result.stdout.strip()}")
        except (subprocess.TimeoutExpired, FileNotFoundError):
            raise RuntimeError("Node.js is not installed or not in PATH")
        
        # Verify JavaScript file exists
        if not os.path.exists(self.js_script_path):
            raise FileNotFoundError(f"JavaScript file not found: {self.js_script_path}")
        
        print(f"✅ JavaScript encryption script: {self.js_script_path}")
    
    def get_fresh_keys(self):
        """Get fresh encryption keys from Instagram's headers."""
        try:
            headers = {
                'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/138.0.0.0 Safari/537.36',
            }
            
            response = requests.get('https://www.instagram.com/api/v1/web/accounts/login/ajax/', 
                                  headers=headers, timeout=10)
            
            key_id = response.headers.get("ig-set-password-encryption-web-key-id")
            version = response.headers.get("ig-set-password-encryption-web-key-version")
            pub_key = response.headers.get("ig-set-password-encryption-web-pub-key")
            
            if key_id and version and pub_key:
                self.fresh_keys = {
                    'keyId': int(key_id),
                    'version': int(version),
                    'publicKey': pub_key
                }
                return True
            else:
                return False
                
        except Exception:
            return False
    
    def encrypt_password(self, password: str, timestamp: Optional[str] = None, 
                        key_id: int = None, version: int = None, public_key: str = None) -> str:
        """
        Encrypt password using JavaScript implementation.
        
        Args:
            password: Password to encrypt
            timestamp: Timestamp string (current time if None)
            key_id: Instagram key ID (fetches fresh if None)
            version: Encryption version (fetches fresh if None)
            public_key: Instagram public key (fetches fresh if None)
            
        Returns:
            Encrypted password string in Instagram format
            
        Raises:
            RuntimeError: If encryption fails
        """
        
        if timestamp is None:
            import time
            timestamp = str(int(time.time()))
        
        # Always use fresh keys if not explicitly provided
        if key_id is None or version is None or public_key is None:
            if self.fresh_keys is None:
                print("🔍 Fetching fresh encryption keys from Instagram...")
                if not self.get_fresh_keys():
                    raise RuntimeError("Failed to get encryption keys from Instagram. Please check your internet connection or try again later.")
                else:
                    print(f"✅ Got fresh keys: ID={self.fresh_keys['keyId']}, Version={self.fresh_keys['version']}")
            
            key_id = key_id or self.fresh_keys['keyId']
            version = version or self.fresh_keys['version']
            public_key = public_key or self.fresh_keys['publicKey']
        
        # Use the silent JavaScript implementation
        try:
            # Run the silent JavaScript encryption
            result = subprocess.run(
                ['node', self.js_script_path, str(key_id), public_key, password, timestamp],
                capture_output=True,
                text=True,
                timeout=30,
                cwd=os.path.dirname(self.js_script_path)
            )
            
            if result.returncode != 0:
                error_msg = result.stderr.strip()
                if error_msg.startswith("ERROR:"):
                    error_msg = error_msg.replace("ERROR:", "")
                raise RuntimeError(f"JavaScript encryption failed: {error_msg}")
            
            # The silent version outputs only the encrypted result
            encrypted_result = result.stdout.strip()
            
            if not encrypted_result or not encrypted_result.startswith("#PWD_INSTAGRAM_BROWSER:"):
                raise RuntimeError(f"Invalid encryption result: {encrypted_result}")
            
            return encrypted_result
            
        except subprocess.TimeoutExpired:
            raise RuntimeError("JavaScript encryption timed out")
        except Exception as e:
            raise RuntimeError(f"Failed to run JavaScript encryption: {str(e)}")
    
    def encrypt_with_current_timestamp(self, password: str) -> str:
        """
        Convenience method to encrypt with current timestamp.
        
        Args:
            password: Password to encrypt
            
        Returns:
            Encrypted password string
        """
        return self.encrypt_password(password)
    
    def test_encryption(self) -> bool:
        """
        Test the encryption with sample data.
        
        Returns:
            True if test passes, False otherwise
        """
        try:
            print("🧪 Testing JavaScript encryption...")
            
            test_password = "test1234"
            test_timestamp = "1758156992"
            
            encrypted = self.encrypt_password(test_password, test_timestamp)
            
            # Basic validation
            parts = encrypted.split(':')
            if len(parts) != 4:
                print(f"❌ Invalid format: expected 4 parts, got {len(parts)}")
                return False
            
            if parts[0] != "#PWD_INSTAGRAM_BROWSER":
                print(f"❌ Wrong tag: {parts[0]}")
                return False
            
            if parts[2] != test_timestamp:
                print(f"❌ Wrong timestamp: {parts[2]}")
                return False
            
            print(f"✅ Test passed! Encryption is working correctly.")
            return True
            
        except Exception as e:
            print(f"❌ Test failed: {e}")
            return False


def main():
    """
    Example usage and testing.
    """
    print("Instagram Password Encryption - Python Wrapper")
    print("=" * 60)
    print("This script uses Node.js to run Instagram's exact encryption algorithm")
    print("=" * 60)
    
    try:
        # Initialize the wrapper
        wrapper = InstagramEncryptionWrapper()
        
        # Test the encryption
        if not wrapper.test_encryption():
            print("❌ Initial test failed!")
            return 1
        
        print("\\n" + "=" * 60)
        print("🎯 READY FOR USE!")
        print("=" * 60)
        
        # Example usage
        print("\\n📋 Example usage:")
        print("```python")
        print("from instagram_encrypt_wrapper import InstagramEncryptionWrapper")
        print("")
        print("wrapper = InstagramEncryptionWrapper()")
        print('encrypted = wrapper.encrypt_password("your_password", "1758156992")')
        print("print(encrypted)")
        print("```")
        
        # Interactive mode
        while True:
            print("\\n" + "-" * 40)
            print("Interactive Mode:")
            print("1. Encrypt password with custom timestamp")
            print("2. Encrypt password with current timestamp")
            print("3. Exit")
            
            choice = input("\\nEnter choice (1-3): ").strip()
            
            if choice == "1":
                password = input("Enter password: ").strip()
                timestamp = input("Enter timestamp: ").strip()
                if password and timestamp:
                    try:
                        encrypted = wrapper.encrypt_password(password, timestamp)
                        print(f"\\n🎯 ENCRYPTED RESULT:")
                        print(f"{encrypted}")
                    except Exception as e:
                        print(f"❌ Error: {e}")
            
            elif choice == "2":
                password = input("Enter password: ").strip()
                if password:
                    try:
                        encrypted = wrapper.encrypt_with_current_timestamp(password)
                        print(f"\\n🎯 ENCRYPTED RESULT:")
                        print(f"{encrypted}")
                    except Exception as e:
                        print(f"❌ Error: {e}")
            
            elif choice == "3":
                print("Goodbye!")
                break
            
            else:
                print("Invalid choice. Please enter 1, 2, or 3.")
        
        return 0
        
    except Exception as e:
        print(f"❌ Error: {e}")
        return 1


if __name__ == "__main__":
    sys.exit(main())
