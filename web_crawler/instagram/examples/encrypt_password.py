"""
Simple Python interface for Instagram password encryption.

This provides a clean Python API that uses the JavaScript implementation
for maximum compatibility with Instagram's encryption.
"""

import time
import getpass
import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'src'))
from instagram_encrypt_wrapper import InstagramEncryptionWrapper

# Global wrapper instance
_wrapper = None

def get_wrapper():
    """Get or create the wrapper instance."""
    global _wrapper
    if _wrapper is None:
        _wrapper = InstagramEncryptionWrapper()
    return _wrapper

def encrypt_instagram_password(password: str, timestamp: str = None) -> str:
    """
    Encrypt a password for Instagram login.
    
    Args:
        password: The password to encrypt
        timestamp: Optional timestamp (uses current time if None)
        
    Returns:
        Encrypted password string ready for Instagram API
        
    Example:
        >>> encrypted = encrypt_instagram_password("mypassword", "1758156992")
        >>> print(encrypted)
        #PWD_INSTAGRAM_BROWSER:10:1758156992:...
    """
    wrapper = get_wrapper()
    return wrapper.encrypt_password(password, timestamp)

def encrypt_with_current_time(password: str) -> str:
    """
    Encrypt a password using current timestamp.
    
    Args:
        password: The password to encrypt
        
    Returns:
        Encrypted password string
        
    Example:
        >>> encrypted = encrypt_with_current_time("mypassword")
        >>> print(encrypted)
        #PWD_INSTAGRAM_BROWSER:10:1758157123:...
    """
    wrapper = get_wrapper()
    return wrapper.encrypt_with_current_timestamp(password)

# Interactive usage
if __name__ == "__main__":
    print("🔐 Instagram Password Encryption - Interactive Mode")
    print("=" * 60)
    print("This tool uses JavaScript implementation for exact Instagram compatibility")
    print("=" * 60)
    
    while True:
        print("\nOptions:")
        print("1. Encrypt with custom password and timestamp")
        print("2. Encrypt with current timestamp")
        print("3. Exit")
        
        choice = input("\nEnter choice (1-3): ").strip()
        
        if choice == "1":
            print("\n" + "-" * 40)
            password = getpass.getpass("Enter password (hidden): ").strip()
            if not password:
                print("❌ Password cannot be empty!")
                continue
                
            timestamp = input("Enter timestamp: ").strip()
            if not timestamp:
                print("❌ Timestamp cannot be empty!")
                continue
            
            try:
                print("\n🔐 Encrypting...")
                encrypted = encrypt_instagram_password(password, timestamp)
                
                print("\n" + "=" * 60)
                print("✅ ENCRYPTION SUCCESSFUL!")
                print("=" * 60)
                print(f"Password: {password}")
                print(f"Timestamp: {timestamp}")
                print("\n🎯 ENCRYPTED RESULT:")
                print(f"{encrypted}")
                print("\n📋 Copy this for Instagram login!")
                print("=" * 60)
                
            except Exception as e:
                print(f"\n❌ Encryption failed: {e}")
        
        elif choice == "2":
            print("\n" + "-" * 40)
            password = getpass.getpass("Enter password (hidden): ").strip()
            if not password:
                print("❌ Password cannot be empty!")
                continue
            
            try:
                current_time = str(int(time.time()))
                print(f"\n🔐 Encrypting with current timestamp: {current_time}")
                encrypted = encrypt_with_current_time(password)
                
                print("\n" + "=" * 60)
                print("✅ ENCRYPTION SUCCESSFUL!")
                print("=" * 60)
                print(f"Password: {password}")
                print(f"Timestamp: {current_time} (current time)")
                print("\n🎯 ENCRYPTED RESULT:")
                print(f"{encrypted}")
                print("\n📋 Copy this for Instagram login!")
                print("=" * 60)
                
            except Exception as e:
                print(f"\n❌ Encryption failed: {e}")
        
        elif choice == "3":
            print("\n👋 Goodbye!")
            break
        
        else:
            print("\n❌ Invalid choice. Please enter 1, 2, or 3.")
        
        # Ask if user wants to continue
        if choice in ["1", "2"]:
            continue_choice = input("\nEncrypt another password? (y/n): ").strip().lower()
            if continue_choice not in ["y", "yes"]:
                print("\n👋 Goodbye!")
                break
