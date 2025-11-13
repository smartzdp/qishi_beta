"""
Simple API test script
Test authentication and ASR endpoints
"""
import requests
import json
import time
import sys

BASE_URL = "http://localhost:5001"

def test_login():
    """Test login endpoint"""
    print("\n=== Testing Login ===")
    url = f"{BASE_URL}/api/auth/login"
    data = {
        "username": "testuser",
        "password": "password123"
    }
    
    try:
        response = requests.post(url, json=data)
        print(f"Status Code: {response.status_code}")
        print(f"Response: {json.dumps(response.json(), indent=2)}")
        
        if response.status_code == 200:
            token = response.json().get('access_token')
            print(f"✓ Login successful! Token: {token[:50]}...")
            return token
        else:
            print(f"✗ Login failed: {response.json()}")
            return None
    except requests.exceptions.ConnectionError:
        print("✗ Cannot connect to server. Make sure the server is running.")
        return None
    except Exception as e:
        print(f"✗ Error: {e}")
        return None

def test_register():
    """Test register endpoint"""
    print("\n=== Testing Register ===")
    url = f"{BASE_URL}/api/auth/register"
    data = {
        "username": "testuser2",
        "email": "test2@example.com",
        "password": "password123",
        "confirm_password": "password123"
    }
    
    try:
        response = requests.post(url, json=data)
        print(f"Status Code: {response.status_code}")
        print(f"Response: {json.dumps(response.json(), indent=2)}")
        
        if response.status_code == 201:
            print("✓ Registration successful!")
            return True
        else:
            print(f"✗ Registration failed: {response.json()}")
            return False
    except requests.exceptions.ConnectionError:
        print("✗ Cannot connect to server. Make sure the server is running.")
        return False
    except Exception as e:
        print(f"✗ Error: {e}")
        return False

def test_create_model(token):
    """Test create model endpoint"""
    print("\n=== Testing Create Model ===")
    url = f"{BASE_URL}/api/asr/models"
    headers = {"Authorization": f"Bearer {token}"}
    data = {
        "model_name": "tiny",  # Use tiny for faster testing
        "device": "cpu"
    }
    
    try:
        response = requests.post(url, json=data, headers=headers)
        print(f"Status Code: {response.status_code}")
        print(f"Response: {json.dumps(response.json(), indent=2)}")
        
        if response.status_code in [200, 201]:
            instance_id = response.json().get('instance_id')
            if instance_id:
                print(f"✓ Model created successfully! Instance ID: {instance_id}")
                return instance_id
            else:
                print(f"✗ Model creation failed: No instance_id in response")
                return None
        else:
            print(f"✗ Model creation failed: {response.json()}")
            return None
    except Exception as e:
        print(f"✗ Error: {e}")
        return None

def test_list_models(token):
    """Test list models endpoint"""
    print("\n=== Testing List Models ===")
    url = f"{BASE_URL}/api/asr/models"
    headers = {"Authorization": f"Bearer {token}"}
    
    try:
        response = requests.get(url, headers=headers)
        print(f"Status Code: {response.status_code}")
        print(f"Response: {json.dumps(response.json(), indent=2)}")
        
        if response.status_code == 200:
            models = response.json().get('models', [])
            print(f"✓ Found {len(models)} model(s)")
            return True
        else:
            print(f"✗ List models failed: {response.json()}")
            return False
    except Exception as e:
        print(f"✗ Error: {e}")
        return False

def test_delete_model(token, instance_id):
    """Test delete model endpoint"""
    print(f"\n=== Testing Delete Model ===")
    url = f"{BASE_URL}/api/asr/models/{instance_id}"
    headers = {"Authorization": f"Bearer {token}"}
    
    try:
        response = requests.delete(url, headers=headers)
        print(f"Status Code: {response.status_code}")
        
        if response.status_code == 204:
            print(f"✓ Model deleted successfully!")
            return True
        else:
            print(f"✗ Model deletion failed: {response.text}")
            return False
    except Exception as e:
        print(f"✗ Error: {e}")
        return False

if __name__ == "__main__":
    print("=" * 50)
    print("Whisper ASR API Test")
    print("=" * 50)
    
    # Test login
    token = test_login()
    if not token:
        print("\n✗ Cannot proceed without authentication token")
        sys.exit(1)
    
    # Test register (optional)
    # test_register()
    
    # Test create model
    instance_id = test_create_model(token)
    
    # Test list models
    test_list_models(token)
    
    # Test delete model
    if instance_id:
        test_delete_model(token, instance_id)
    
    print("\n" + "=" * 50)
    print("Test completed!")
    print("=" * 50)

