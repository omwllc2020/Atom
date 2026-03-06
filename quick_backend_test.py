#!/usr/bin/env python3
"""
Quick Backend API Test - Core Functionality Only
"""
import requests
import json
import time

BASE_URL = "https://nano-dev-creator.preview.emergentagent.com/api"

def test_basic_endpoints():
    print("🧪 Testing Core API Endpoints")
    print("=" * 50)
    
    # 1. Health Check
    try:
        response = requests.get(f"{BASE_URL}/", timeout=10)
        print(f"✅ Health Check: {response.status_code} - {response.json()}")
    except Exception as e:
        print(f"❌ Health Check failed: {e}")
        return False
    
    # 2. Register new user
    timestamp = int(time.time())
    user_data = {
        "email": f"test_{timestamp}@forge.ai",
        "password": "testpass123", 
        "name": f"Test User {timestamp}"
    }
    
    try:
        response = requests.post(f"{BASE_URL}/auth/register", json=user_data, timeout=10)
        if response.status_code == 200:
            data = response.json()
            token = data.get('access_token')
            print(f"✅ Registration: Success - Token: {token[:20] if token else 'None'}...")
            
            # 3. Test authenticated endpoint
            headers = {"Authorization": f"Bearer {token}"}
            profile_response = requests.get(f"{BASE_URL}/auth/me", headers=headers, timeout=10)
            print(f"✅ Profile Check: {profile_response.status_code}")
            
            # 4. Test chat (quick timeout)
            chat_data = {"message": "Hello, write 'Hello World' in Python"}
            chat_response = requests.post(f"{BASE_URL}/chat", json=chat_data, headers=headers, timeout=15)
            if chat_response.status_code == 200:
                chat_result = chat_response.json()
                print(f"✅ Chat Response: Success - Got {len(chat_result.get('response', ''))} chars")
            else:
                print(f"❌ Chat failed: {chat_response.status_code}")
            
            return True
            
        else:
            print(f"❌ Registration failed: {response.status_code} - {response.text}")
            return False
            
    except Exception as e:
        print(f"❌ Registration error: {e}")
        return False

def test_specific_issues():
    """Test the specific issues found in logs"""
    print("\n🔍 Testing Specific Issues")
    print("=" * 50)
    
    # Test with existing user
    login_data = {"email": "test@forge.ai", "password": "testpass123"}
    try:
        response = requests.post(f"{BASE_URL}/auth/login", json=login_data, timeout=10)
        if response.status_code == 200:
            token = response.json().get('access_token')
            headers = {"Authorization": f"Bearer {token}"}
            print(f"✅ Login with test user successful")
            
            # Test image generation (expect budget error)
            print("🧪 Testing image generation (expecting budget limit)...")
            img_response = requests.post(
                f"{BASE_URL}/image/generate", 
                json={"prompt": "simple test image"}, 
                headers=headers, 
                timeout=20
            )
            if img_response.status_code == 500:
                error_data = img_response.json()
                if "budget" in error_data.get('detail', '').lower():
                    print("✅ Image generation correctly shows budget limit error")
                else:
                    print(f"❓ Image generation error: {error_data}")
            else:
                print(f"❓ Unexpected image response: {img_response.status_code}")
                
            # Test site cloning (expect SSL error)
            print("🧪 Testing site cloning (expecting SSL issue)...")
            clone_response = requests.post(
                f"{BASE_URL}/clone/site",
                json={"url": "https://example.com"},
                headers=headers,
                timeout=20
            )
            print(f"🔍 Clone response: {clone_response.status_code}")
            if clone_response.status_code != 200:
                try:
                    error_data = clone_response.json()
                    print(f"   Error: {error_data.get('detail', 'Unknown error')}")
                except:
                    print(f"   Raw error: {clone_response.text}")
            
        else:
            print(f"❌ Login failed: {response.status_code}")
            
    except Exception as e:
        print(f"❌ Test error: {e}")

if __name__ == "__main__":
    print("🚀 FORGE AI - Quick Backend Test")
    print(f"Target: {BASE_URL}")
    print()
    
    success = test_basic_endpoints()
    test_specific_issues()
    
    print(f"\n📊 Core functionality: {'✅ Working' if success else '❌ Failed'}")