#!/usr/bin/env python3
"""
Instagram Password Encryption & Login Tool

Main entry point for the Instagram encryption and login system.
"""

import sys
import os

# Add src directory to path
sys.path.append(os.path.join(os.path.dirname(__file__), 'src'))

def main():
    print("🔐 Instagram Password Encryption & Login System")
    print("=" * 60)
    print("Choose what you want to do:")
    print()
    print("1. Encrypt password only")
    print("2. Complete Instagram login")
    print("3. Quick command-line encryption")
    print("4. Exit")
    print()
    
    choice = input("Enter choice (1-4): ").strip()
    
    if choice == "1":
        print("\n🔐 Starting password encryption...")
        os.system(f"cd {os.path.dirname(__file__)} && python3 examples/encrypt_password.py")
    
    elif choice == "2":
        print("\n🚀 Starting Instagram login...")
        os.system(f"cd {os.path.dirname(__file__)} && python3 examples/instagram_login.py")
    
    elif choice == "3":
        print("\n⚡ Quick encryption mode...")
        os.system(f"cd {os.path.dirname(__file__)} && python3 examples/encrypt_quick.py")
    
    elif choice == "4":
        print("\n👋 Goodbye!")
        return 0
    
    else:
        print("\n❌ Invalid choice. Please enter 1-4.")
        return 1
    
    return 0

if __name__ == "__main__":
    sys.exit(main())
