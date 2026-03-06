#!/usr/bin/env python3
"""
Debug Backend Issues - Get detailed error information
"""
import requests
import json
import time

BASE_URL = "https://nano-dev-creator.preview.emergentagent.com/api"

def debug_chat_error():
    """Get detailed chat error"""
    # Register a new user
    timestamp = int(time.time())
    user_data = {
        "email": f"debug_{timestamp}@forge.ai",
        "password": "testpass123", 
        "name": f"Debug User {timestamp}"
    }
    
    response = requests.post(f"{BASE_URL}/auth/register", json=user_data, timeout=10)
    if response.status_code != 200:
        print("Failed to register user")
        return
        
    token = response.json().get('access_token')
    headers = {"Authorization": f"Bearer {token}"}
    
    # Try chat with detailed error handling
    chat_data = {"message": "Hello, write 'Hello World' in Python"}
    
    print("🧪 Testing Chat Endpoint...")
    try:
        chat_response = requests.post(f"{BASE_URL}/chat", json=chat_data, headers=headers, timeout=30)
        print(f"Status Code: {chat_response.status_code}")
        print(f"Response Headers: {dict(chat_response.headers)}")
        
        try:
            response_json = chat_response.json()
            print(f"Response JSON: {json.dumps(response_json, indent=2)}")
        except:
            print(f"Raw Response: {chat_response.text}")
            
    except Exception as e:
        print(f"Request failed: {e}")

def test_existing_user_login():
    """Test with the exact credentials from the testing requirements"""
    print("🧪 Testing with provided test credentials...")
    
    # Use exact credentials from requirements
    login_data = {
        "email": "test@forge.ai",
        "password": "testpass123"
    }
    
    try:
        response = requests.post(f"{BASE_URL}/auth/login", json=login_data, timeout=10)
        print(f"Login Status: {response.status_code}")
        
        if response.status_code != 200:
            try:
                error_data = response.json()
                print(f"Login Error: {json.dumps(error_data, indent=2)}")
            except:
                print(f"Raw Login Error: {response.text}")
        else:
            data = response.json()
            print(f"Login Success: User {data.get('user', {}).get('email')}")
            return data.get('access_token')
            
    except Exception as e:
        print(f"Login request failed: {e}")
        
    return None

def check_dependencies():
    """Check if the required dependencies are working"""
    print("🧪 Checking Dependencies...")
    
    # Check if emergentintegrations is working
    try:
        import sys
        sys.path.append('/app/backend')
        
        # Try to import the integration
        from emergentintegrations.llm.chat import LlmChat
        print("✅ emergentintegrations import successful")
        
        # Check if we can create a chat instance
        chat = LlmChat(api_key="test_key", session_id="test_session")
        print("✅ LlmChat instance creation successful")
        
    except Exception as e:
        print(f"❌ Dependency error: {e}")

if __name__ == "__main__":
    print("🔍 DEBUGGING BACKEND ISSUES")
    print("=" * 50)
    
    # Test existing user login first
    token = test_existing_user_login()
    
    # Debug chat functionality
    debug_chat_error()
    
    # Check dependencies
    check_dependencies()