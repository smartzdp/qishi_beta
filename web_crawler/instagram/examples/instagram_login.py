"""
Instagram Login Implementation

Combines password encryption with the actual login API request
using the exact request structure from Instagram's frontend.
"""

import requests
import json
import time
import getpass
import urllib.parse
import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'src'))
from instagram_encrypt_wrapper import InstagramEncryptionWrapper


class InstagramLogin:
    """
    Instagram login manager with proper password encryption.
    """
    
    def __init__(self):
        self.session = requests.Session()
        self.encryptor = InstagramEncryptionWrapper()
        self.csrf_token = None
        self.encryption_keys = None
        
        # Set headers matching Instagram's request
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/138.0.0.0 Safari/537.36',
            'Accept': '*/*',
            'Accept-Language': 'en',
            'Accept-Encoding': 'gzip, deflate, br, zstd',
            'Content-Type': 'application/x-www-form-urlencoded',
            'Origin': 'https://www.instagram.com',
            'Referer': 'https://www.instagram.com/',
            'Sec-Fetch-Dest': 'empty',
            'Sec-Fetch-Mode': 'cors',
            'Sec-Fetch-Site': 'same-origin',
            'X-Requested-With': 'XMLHttpRequest',
            'X-IG-App-ID': '936619743392459',
            'X-IG-WWW-Claim': '0',
            'X-Instagram-AJAX': '1027248754',
            'Sec-CH-UA': '"Not)A;Brand";v="8", "Chromium";v="138", "Google Chrome";v="138"',
            'Sec-CH-UA-Mobile': '?0',
            'Sec-CH-UA-Platform': '"macOS"',
        })
    
    def get_encryption_keys(self):
        """Extract fresh encryption keys from Instagram's headers."""
        print("🔍 Getting fresh encryption keys from Instagram...")
        
        try:
            # Try the endpoint that returns encryption headers
            response = self.session.get('https://www.instagram.com/api/v1/web/accounts/login/ajax/')
            
            # Look for encryption headers
            key_id = response.headers.get("ig-set-password-encryption-web-key-id")
            version = response.headers.get("ig-set-password-encryption-web-key-version")  
            pub_key = response.headers.get("ig-set-password-encryption-web-pub-key")
            
            if key_id and version and pub_key:
                self.encryption_keys = {
                    'keyId': int(key_id),
                    'version': int(version),
                    'publicKey': pub_key
                }
                print(f"✅ Got fresh encryption keys:")
                print(f"   Key ID: {self.encryption_keys['keyId']}")
                print(f"   Version: {self.encryption_keys['version']}")
                print(f"   Public Key: {self.encryption_keys['publicKey'][:20]}...")
                return True
            else:
                print("❌ Could not find encryption headers from Instagram")
                print("   Instagram may have changed their API or blocked the request")
                return False
                
        except Exception as e:
            print(f"❌ Error getting encryption keys: {e}")
            return False
    
    def get_csrf_token(self):
        """Get CSRF token from Instagram login page."""
        print("🔍 Getting CSRF token...")
        
        try:
            response = self.session.get('https://www.instagram.com/accounts/login/')
            response.raise_for_status()
            
            # Extract CSRF token from cookies
            csrf_token = None
            for cookie in self.session.cookies:
                if cookie.name == 'csrftoken':
                    csrf_token = cookie.value
                    break
            
            if csrf_token:
                self.csrf_token = csrf_token
                self.session.headers['X-CSRFToken'] = csrf_token
                print(f"✅ Got CSRF token: {csrf_token[:20]}...")
                return True
            else:
                print("❌ Could not find CSRF token")
                return False
                
        except Exception as e:
            print(f"❌ Error getting CSRF token: {e}")
            return False
    
    def login(self, username, password):
        """
        Perform Instagram login with encrypted password.
        
        Args:
            username: Instagram username or email
            password: Plain text password
            
        Returns:
            True if login successful, False otherwise
        """
        print(f"🚀 Starting Instagram login for: {username}")
        
        # Step 1: Get fresh encryption keys
        if not self.get_encryption_keys():
            return False
        
        # Step 2: Get CSRF token
        if not self.get_csrf_token():
            return False
        
        # Step 3: Encrypt password with current timestamp and fresh keys
        print("🔐 Encrypting password with fresh keys...")
        try:
            current_timestamp = str(int(time.time()))
            encrypted_password = self.encryptor.encrypt_password(
                password, 
                current_timestamp,
                self.encryption_keys['keyId'],
                self.encryption_keys['version'],
                self.encryption_keys['publicKey']
            )
            print(f"✅ Password encrypted with timestamp: {current_timestamp}")
            print(f"   Using Key ID: {self.encryption_keys['keyId']}, Version: {self.encryption_keys['version']}")
            print(f"   Encrypted: {encrypted_password[:50]}...")
            
        except Exception as e:
            print(f"❌ Password encryption failed: {e}")
            return False
        
        # Step 4: Prepare login payload (matching Instagram's exact structure)
        login_data = {
            'enc_password': encrypted_password,
            'caaF2DebugGroup': '0',
            'isPrivacyPortalReq': 'false',
            'loginAttemptSubmissionCount': '1',  # Start with 1, Instagram increments this
            'optIntoOneTap': 'false',
            'queryParams': '{}',
            'trustedDeviceRecords': '{}',
            'username': username,
            'jazoest': '22729'  # This might need to be calculated, but using sample value
        }
        
        # Step 5: Send login request
        print("📤 Sending login request...")
        
        try:
            response = self.session.post(
                'https://www.instagram.com/api/v1/web/accounts/login/ajax/',
                data=login_data,
                timeout=30
            )
            
            print(f"📥 Response status: {response.status_code}")
            print(f"📋 Response headers:")
            for header, value in response.headers.items():
                if 'ig-' in header.lower() or 'csrf' in header.lower():
                    print(f"   {header}: {value}")
            
            if response.status_code == 200:
                try:
                    result = response.json()
                    print(f"📊 Response JSON: {json.dumps(result, indent=2)}")
                    
                    if result.get('authenticated'):
                        print("✅ Login successful!")
                        return True
                    elif result.get('message'):
                        print(f"❌ Login failed: {result['message']}")
                    elif result.get('errors'):
                        print(f"❌ Login errors: {result['errors']}")
                    else:
                        print(f"❌ Login failed with response: {result}")
                        
                except json.JSONDecodeError:
                    print(f"❌ Non-JSON response: {response.text}")
            else:
                print(f"❌ HTTP Error {response.status_code}: {response.text}")
            
            return False
            
        except Exception as e:
            print(f"❌ Login request failed: {e}")
            return False
    
    def get_session_info(self):
        """Get session information after successful login."""
        try:
            response = self.session.get('https://www.instagram.com/')
            if response.status_code == 200:
                print("✅ Session is active")
                return True
            else:
                print(f"❌ Session check failed: {response.status_code}")
                return False
        except Exception as e:
            print(f"❌ Session check error: {e}")
            return False


def main():
    """Interactive login test."""
    print("🔐 Instagram Login with Password Encryption")
    print("=" * 60)
    print("This combines our password encryption with Instagram's login API")
    print("=" * 60)
    
    login_manager = InstagramLogin()
    
    # Get credentials
    username = input("Enter username/email: ").strip()
    if not username:
        print("❌ Username cannot be empty!")
        return 1
    
    password = getpass.getpass("Enter password (hidden): ").strip()
    if not password:
        print("❌ Password cannot be empty!")
        return 1
    
    print("\n" + "=" * 60)
    print("⚠️  IMPORTANT WARNINGS:")
    print("   - This is for educational purposes only")
    print("   - Respect Instagram's terms of service")
    print("   - Use your own credentials only")
    print("   - Be aware of rate limiting")
    print("=" * 60)
    
    confirm = input("\nProceed with login? (y/n): ").strip().lower()
    if confirm not in ['y', 'yes']:
        print("Login cancelled.")
        return 0
    
    # Attempt login
    print("\n" + "=" * 60)
    success = login_manager.login(username, password)
    
    if success:
        print("\n🎉 Login successful!")
        login_manager.get_session_info()
    else:
        print("\n❌ Login failed!")
        print("\nPossible reasons:")
        print("   - Invalid credentials")
        print("   - Two-factor authentication required")
        print("   - Account locked or restricted")
        print("   - Rate limiting")
        print("   - CAPTCHA required")
    
    return 0 if success else 1


if __name__ == "__main__":
    import sys
    sys.exit(main())
