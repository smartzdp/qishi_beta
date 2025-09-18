#!/usr/bin/env python3
"""
Quick Instagram password encryption tool.

Usage:
    python3 encrypt_quick.py <password> <timestamp>
    python3 encrypt_quick.py <password>  # uses current timestamp
"""

import sys
import time
import getpass
import sys
import os
sys.path.append(os.path.dirname(__file__))
from encrypt_password import encrypt_instagram_password, encrypt_with_current_time

def main():
    if len(sys.argv) < 2:
        print("🔐 Instagram Password Encryption - Quick Tool")
        print("=" * 50)
        print("Usage:")
        print("  python3 encrypt_quick.py <password> <timestamp>")
        print("  python3 encrypt_quick.py <password>  # current time")
        print()
        print("Examples:")
        print("  python3 encrypt_quick.py mypassword 1758156992")
        print("  python3 encrypt_quick.py mypassword")
        print()
        
        # Interactive mode if no arguments
        password = getpass.getpass("Enter password (hidden): ").strip()
        if not password:
            print("❌ Password cannot be empty!")
            return 1
        
        timestamp_input = input("Enter timestamp (leave empty for current time): ").strip()
        
        try:
            if timestamp_input:
                encrypted = encrypt_instagram_password(password, timestamp_input)
                print(f"\n✅ Encrypted with timestamp {timestamp_input}:")
            else:
                encrypted = encrypt_with_current_time(password)
                current_time = str(int(time.time()))
                print(f"\n✅ Encrypted with current timestamp {current_time}:")
            
            print(encrypted)
            return 0
            
        except Exception as e:
            print(f"❌ Error: {e}")
            return 1
    
    password = sys.argv[1]
    
    try:
        if len(sys.argv) >= 3:
            # Use provided timestamp
            timestamp = sys.argv[2]
            encrypted = encrypt_instagram_password(password, timestamp)
            print(f"✅ Encrypted with timestamp {timestamp}:")
        else:
            # Use current timestamp
            encrypted = encrypt_with_current_time(password)
            current_time = str(int(time.time()))
            print(f"✅ Encrypted with current timestamp {current_time}:")
        
        print(encrypted)
        return 0
        
    except Exception as e:
        print(f"❌ Error: {e}")
        return 1

if __name__ == "__main__":
    sys.exit(main())
