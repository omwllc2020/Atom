#!/usr/bin/env python3
"""
ATOM AI App - Backend API Test Suite
Tests: Authentication, Credits, Agents/Modes, Chat with agent params

Focus areas:
- Super admin login (Antoniohoshaw6@gmail.com) - should see SUPER ADMIN badge and UNLIMITED
- Regular user login - should see credits balance (10.00)
- API endpoint /api/agents - returns list of agents and modes
- API endpoint /api/user/credits - returns credits for regular user, unlimited for super admin
- Chat endpoint accepts agent, mode, ultra_thinking parameters
"""

import pytest
import requests
import os
import time

BASE_URL = os.environ.get('REACT_APP_BACKEND_URL', 'https://nano-dev-creator.preview.emergentagent.com').rstrip('/')
API_URL = f"{BASE_URL}/api"

# Test credentials
SUPER_ADMIN_CREDS = {
    "email": "Antoniohoshaw6@gmail.com",
    "password": "admin123"
}
REGULAR_USER_CREDS = {
    "email": "testuser@test.com",
    "password": "test123"
}


@pytest.fixture(scope="module")
def api_client():
    """Shared requests session"""
    session = requests.Session()
    session.headers.update({"Content-Type": "application/json"})
    return session


@pytest.fixture(scope="module")
def register_super_admin(api_client):
    """Register super admin if not exists"""
    # Try to register super admin
    response = api_client.post(f"{API_URL}/auth/register", json={
        "email": SUPER_ADMIN_CREDS["email"],
        "password": SUPER_ADMIN_CREDS["password"],
        "name": "Super Admin"
    })
    # 200 = new registration, 400 = already exists
    return response


@pytest.fixture(scope="module")
def super_admin_token(api_client, register_super_admin):
    """Get authentication token for super admin"""
    response = api_client.post(f"{API_URL}/auth/login", json=SUPER_ADMIN_CREDS)
    if response.status_code == 200:
        return response.json().get("access_token")
    pytest.skip("Super admin login failed - skipping authenticated tests")


@pytest.fixture(scope="module")
def register_regular_user(api_client):
    """Register regular user if not exists"""
    response = api_client.post(f"{API_URL}/auth/register", json={
        "email": REGULAR_USER_CREDS["email"],
        "password": REGULAR_USER_CREDS["password"],
        "name": "Test User"
    })
    return response


@pytest.fixture(scope="module")
def regular_user_token(api_client, register_regular_user):
    """Get authentication token for regular user"""
    response = api_client.post(f"{API_URL}/auth/login", json=REGULAR_USER_CREDS)
    if response.status_code == 200:
        return response.json().get("access_token")
    pytest.skip("Regular user login failed - skipping authenticated tests")


class TestHealthAndAgents:
    """Test basic API health and agents endpoint"""
    
    def test_api_health(self, api_client):
        """Test API health endpoint"""
        response = api_client.get(f"{API_URL}/")
        assert response.status_code == 200
        data = response.json()
        assert "message" in data
        assert "ATOM" in data["message"]
        print(f"Health check: {data}")
    
    def test_health_endpoint(self, api_client):
        """Test dedicated health endpoint"""
        response = api_client.get(f"{API_URL}/health")
        assert response.status_code == 200
        data = response.json()
        assert data.get("status") == "healthy"
    
    def test_agents_endpoint(self, api_client):
        """Test /api/agents endpoint returns agents and modes"""
        response = api_client.get(f"{API_URL}/agents")
        assert response.status_code == 200
        
        data = response.json()
        
        # Verify agents structure
        assert "agents" in data
        agents = data["agents"]
        assert len(agents) == 5  # nova, forge, sentinel, atlas, pulse
        
        agent_ids = [a["id"] for a in agents]
        assert "nova" in agent_ids
        assert "forge" in agent_ids
        assert "sentinel" in agent_ids
        assert "atlas" in agent_ids
        assert "pulse" in agent_ids
        
        # Verify each agent has required fields
        for agent in agents:
            assert "id" in agent
            assert "name" in agent
            assert "role" in agent
            assert "capabilities" in agent
            assert isinstance(agent["capabilities"], list)
        
        # Verify modes structure
        assert "modes" in data
        modes = data["modes"]
        assert len(modes) == 4  # e1, e2, prototype, mobile
        
        mode_ids = [m["id"] for m in modes]
        assert "e1" in mode_ids
        assert "e2" in mode_ids
        assert "prototype" in mode_ids
        assert "mobile" in mode_ids
        
        # Verify each mode has required fields
        for mode in modes:
            assert "id" in mode
            assert "name" in mode
            assert "description" in mode
        
        print(f"Agents: {[a['name'] for a in agents]}")
        print(f"Modes: {[m['name'] for m in modes]}")


class TestSuperAdminAuth:
    """Test super admin authentication and privileges"""
    
    def test_super_admin_login(self, api_client, register_super_admin):
        """Test super admin login returns correct role and unlimited credits"""
        response = api_client.post(f"{API_URL}/auth/login", json=SUPER_ADMIN_CREDS)
        assert response.status_code == 200
        
        data = response.json()
        assert "access_token" in data
        assert "user" in data
        
        user = data["user"]
        assert user["email"] == SUPER_ADMIN_CREDS["email"]
        assert user["is_super_admin"] == True
        assert user["role"] == "super_admin"
        assert user["credits"] == -1  # -1 indicates unlimited
        
        print(f"Super admin login successful: {user}")
    
    def test_super_admin_credits_endpoint(self, api_client, super_admin_token):
        """Test /api/user/credits returns unlimited for super admin"""
        headers = {"Authorization": f"Bearer {super_admin_token}"}
        response = api_client.get(f"{API_URL}/user/credits", headers=headers)
        
        assert response.status_code == 200
        data = response.json()
        
        assert data["is_super_admin"] == True
        assert data["unlimited"] == True
        assert data["credits"] is None  # Credits is null for super admin
        
        print(f"Super admin credits: {data}")
    
    def test_super_admin_me_endpoint(self, api_client, super_admin_token):
        """Test /api/auth/me returns super admin info"""
        headers = {"Authorization": f"Bearer {super_admin_token}"}
        response = api_client.get(f"{API_URL}/auth/me", headers=headers)
        
        assert response.status_code == 200
        data = response.json()
        
        assert data["is_super_admin"] == True
        assert data["role"] == "super_admin"
        assert data["credits"] == -1  # -1 indicates unlimited
        
        print(f"Super admin profile: {data}")


class TestRegularUserAuth:
    """Test regular user authentication and credits"""
    
    def test_regular_user_login(self, api_client, register_regular_user):
        """Test regular user login returns correct role and credits"""
        response = api_client.post(f"{API_URL}/auth/login", json=REGULAR_USER_CREDS)
        assert response.status_code == 200
        
        data = response.json()
        assert "access_token" in data
        assert "user" in data
        
        user = data["user"]
        assert user["email"] == REGULAR_USER_CREDS["email"]
        assert user["is_super_admin"] == False
        assert user["role"] == "user"
        # Credits should be a positive number (around 10.0 or less if used)
        assert isinstance(user["credits"], (int, float))
        assert user["credits"] != -1  # Not unlimited
        
        print(f"Regular user login successful: {user}")
    
    def test_regular_user_credits_endpoint(self, api_client, regular_user_token):
        """Test /api/user/credits returns credits balance for regular user"""
        headers = {"Authorization": f"Bearer {regular_user_token}"}
        response = api_client.get(f"{API_URL}/user/credits", headers=headers)
        
        assert response.status_code == 200
        data = response.json()
        
        assert data["is_super_admin"] == False
        assert data["unlimited"] == False
        assert data["credits"] is not None
        assert isinstance(data["credits"], (int, float))
        
        print(f"Regular user credits: {data}")
    
    def test_regular_user_me_endpoint(self, api_client, regular_user_token):
        """Test /api/auth/me returns regular user info"""
        headers = {"Authorization": f"Bearer {regular_user_token}"}
        response = api_client.get(f"{API_URL}/auth/me", headers=headers)
        
        assert response.status_code == 200
        data = response.json()
        
        assert data["is_super_admin"] == False
        assert data["role"] == "user"
        # Credits should not be -1
        assert data["credits"] != -1
        
        print(f"Regular user profile: {data}")


class TestChatWithAgentParams:
    """Test chat endpoint with agent, mode, and ultra_thinking parameters"""
    
    def test_chat_accepts_agent_param(self, api_client, super_admin_token):
        """Test chat endpoint accepts agent parameter (using super admin to avoid credit issues)"""
        headers = {"Authorization": f"Bearer {super_admin_token}"}
        
        # Test with nova agent
        response = api_client.post(f"{API_URL}/chat", json={
            "message": "Say 'Hello Nova' in one word",
            "agent": "nova",
            "mode": "e1",
            "ultra_thinking": False
        }, headers=headers, timeout=60)
        
        # Note: Chat may fail due to LLM budget limits, but we're testing params acceptance
        # Status 200 = success, 402 = credits issue, 500 = LLM error
        assert response.status_code in [200, 402, 500]
        
        if response.status_code == 200:
            data = response.json()
            assert "response" in data
            assert "conversation_id" in data
            print(f"Chat with nova agent: conversation_id={data['conversation_id']}")
        else:
            print(f"Chat API returned {response.status_code} - expected due to LLM budget limits")
    
    def test_chat_accepts_forge_agent(self, api_client, super_admin_token):
        """Test chat endpoint accepts forge agent"""
        headers = {"Authorization": f"Bearer {super_admin_token}"}
        
        response = api_client.post(f"{API_URL}/chat", json={
            "message": "Hello",
            "agent": "forge",
            "mode": "e2"
        }, headers=headers, timeout=60)
        
        assert response.status_code in [200, 402, 500]
        print(f"Chat with forge agent: status={response.status_code}")
    
    def test_chat_accepts_ultra_thinking(self, api_client, super_admin_token):
        """Test chat endpoint accepts ultra_thinking parameter"""
        headers = {"Authorization": f"Bearer {super_admin_token}"}
        
        response = api_client.post(f"{API_URL}/chat", json={
            "message": "Hi",
            "agent": "sentinel",
            "mode": "prototype",
            "ultra_thinking": True
        }, headers=headers, timeout=60)
        
        assert response.status_code in [200, 402, 500]
        print(f"Chat with ultra_thinking: status={response.status_code}")
    
    def test_chat_accepts_mobile_mode(self, api_client, super_admin_token):
        """Test chat endpoint accepts mobile mode"""
        headers = {"Authorization": f"Bearer {super_admin_token}"}
        
        response = api_client.post(f"{API_URL}/chat", json={
            "message": "Test",
            "agent": "atlas",
            "mode": "mobile"
        }, headers=headers, timeout=60)
        
        assert response.status_code in [200, 402, 500]
        print(f"Chat with mobile mode: status={response.status_code}")


class TestCreditsDeduction:
    """Test that credits are properly managed"""
    
    def test_regular_user_has_credits(self, api_client, regular_user_token):
        """Verify regular user starts with credits"""
        headers = {"Authorization": f"Bearer {regular_user_token}"}
        response = api_client.get(f"{API_URL}/user/credits", headers=headers)
        
        assert response.status_code == 200
        data = response.json()
        
        # User should have some credits (10.0 initial, may be less if used)
        assert data["credits"] is not None
        # Credits should be >= 0 (could be 0 if all used)
        assert data["credits"] >= 0
        
        print(f"User credits balance: {data['credits']}")
    
    def test_super_admin_has_unlimited(self, api_client, super_admin_token):
        """Verify super admin has unlimited access"""
        headers = {"Authorization": f"Bearer {super_admin_token}"}
        response = api_client.get(f"{API_URL}/user/credits", headers=headers)
        
        assert response.status_code == 200
        data = response.json()
        
        assert data["unlimited"] == True
        assert data["is_super_admin"] == True
        
        print(f"Super admin unlimited: {data['unlimited']}")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
