#!/usr/bin/env python3
"""
ATOM AI Platform - Subscription, Usage, and Admin API Test Suite

Tests for new endpoints:
- GET /api/subscription/plans - Returns 3 plans (Free, Pro, Enterprise)
- GET /api/subscription - Returns user subscription with plan details
- GET /api/user/usage - Returns usage stats with limits for current period
- GET /api/user/preferences - Returns user preferences
- PUT /api/user/preferences - Updates user preferences
- GET /api/admin/stats - Returns platform statistics (admin only)
- GET /api/admin/users - Returns all users (admin only)
- POST /api/admin/users/{id}/credits - Adds credits to user (admin only)
- Admin endpoints return 403 for non-admin users
- Credits deduction on chat and code execution
- Usage logging tracks actions
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
def super_admin_token(api_client):
    """Get authentication token for super admin"""
    # First try to register, then login
    api_client.post(f"{API_URL}/auth/register", json={
        "email": SUPER_ADMIN_CREDS["email"],
        "password": SUPER_ADMIN_CREDS["password"],
        "name": "Super Admin"
    })
    
    response = api_client.post(f"{API_URL}/auth/login", json=SUPER_ADMIN_CREDS)
    if response.status_code == 200:
        return response.json().get("access_token")
    pytest.skip("Super admin login failed - skipping authenticated tests")


@pytest.fixture(scope="module")
def regular_user_token(api_client):
    """Get authentication token for regular user"""
    # First try to register, then login
    api_client.post(f"{API_URL}/auth/register", json={
        "email": REGULAR_USER_CREDS["email"],
        "password": REGULAR_USER_CREDS["password"],
        "name": "Test User"
    })
    
    response = api_client.post(f"{API_URL}/auth/login", json=REGULAR_USER_CREDS)
    if response.status_code == 200:
        return response.json().get("access_token")
    pytest.skip("Regular user login failed - skipping authenticated tests")


@pytest.fixture(scope="module")
def regular_user_id(api_client, regular_user_token):
    """Get regular user ID for admin operations"""
    headers = {"Authorization": f"Bearer {regular_user_token}"}
    response = api_client.get(f"{API_URL}/auth/me", headers=headers)
    if response.status_code == 200:
        return response.json().get("id")
    return None


class TestSubscriptionPlans:
    """Test subscription plans endpoint - GET /api/subscription/plans"""
    
    def test_get_subscription_plans_returns_3_plans(self, api_client):
        """Test that /api/subscription/plans returns 3 plans (Free, Pro, Enterprise)"""
        response = api_client.get(f"{API_URL}/subscription/plans")
        
        assert response.status_code == 200
        data = response.json()
        
        assert "plans" in data
        plans = data["plans"]
        
        # Should have exactly 3 plans
        assert len(plans) == 3
        
        plan_ids = [p["id"] for p in plans]
        assert "free" in plan_ids
        assert "pro" in plan_ids
        assert "enterprise" in plan_ids
        
        print(f"Subscription plans: {plan_ids}")
    
    def test_free_plan_has_correct_structure(self, api_client):
        """Test Free plan has correct structure and values"""
        response = api_client.get(f"{API_URL}/subscription/plans")
        assert response.status_code == 200
        
        data = response.json()
        free_plan = next(p for p in data["plans"] if p["id"] == "free")
        
        assert free_plan["name"] == "Free"
        assert free_plan["price_monthly"] == 0
        assert free_plan["credits_monthly"] == 10
        
        features = free_plan["features"]
        assert features["chat_messages"] == 50
        assert features["code_executions"] == 20
        assert features["video_generations"] == 2
        assert features["image_generations"] == 10
        assert "nova" in features["agents"]
        assert "e1" in features["modes"]
        assert features["ultra_thinking"] == False
        
        print(f"Free plan: {free_plan}")
    
    def test_pro_plan_has_correct_structure(self, api_client):
        """Test Pro plan has correct structure and values"""
        response = api_client.get(f"{API_URL}/subscription/plans")
        assert response.status_code == 200
        
        data = response.json()
        pro_plan = next(p for p in data["plans"] if p["id"] == "pro")
        
        assert pro_plan["name"] == "Pro"
        assert pro_plan["price_monthly"] == 29
        assert pro_plan["credits_monthly"] == 500
        
        features = pro_plan["features"]
        assert features["ultra_thinking"] == True
        assert features["priority_support"] == True
        assert len(features["agents"]) == 5  # All 5 agents
        assert len(features["modes"]) == 4  # All 4 modes
        
        print(f"Pro plan: {pro_plan}")
    
    def test_enterprise_plan_has_unlimited_features(self, api_client):
        """Test Enterprise plan has unlimited (-1) features"""
        response = api_client.get(f"{API_URL}/subscription/plans")
        assert response.status_code == 200
        
        data = response.json()
        enterprise_plan = next(p for p in data["plans"] if p["id"] == "enterprise")
        
        assert enterprise_plan["name"] == "Enterprise"
        assert enterprise_plan["price_monthly"] == 99
        assert enterprise_plan["credits_monthly"] == -1  # Unlimited
        
        features = enterprise_plan["features"]
        assert features["chat_messages"] == -1  # Unlimited
        assert features["code_executions"] == -1  # Unlimited
        assert features["video_generations"] == -1  # Unlimited
        assert features["image_generations"] == -1  # Unlimited
        
        print(f"Enterprise plan: {enterprise_plan}")


class TestUserSubscription:
    """Test user subscription endpoint - GET /api/subscription"""
    
    def test_get_user_subscription(self, api_client, regular_user_token):
        """Test GET /api/subscription returns user's current subscription"""
        headers = {"Authorization": f"Bearer {regular_user_token}"}
        response = api_client.get(f"{API_URL}/subscription", headers=headers)
        
        assert response.status_code == 200
        data = response.json()
        
        assert "subscription" in data
        assert "plan_details" in data
        
        subscription = data["subscription"]
        assert "plan" in subscription
        assert "status" in subscription
        assert subscription["status"] == "active"
        
        print(f"User subscription: {data}")
    
    def test_super_admin_subscription(self, api_client, super_admin_token):
        """Test super admin subscription endpoint identifies admin correctly"""
        headers = {"Authorization": f"Bearer {super_admin_token}"}
        response = api_client.get(f"{API_URL}/subscription", headers=headers)
        
        assert response.status_code == 200
        data = response.json()
        
        # Most important: super admin is identified correctly
        assert data["is_super_admin"] == True
        
        # Subscription and plan_details should be present
        assert "subscription" in data
        assert "plan_details" in data
        
        # Note: Super admin may have any plan (free/pro/enterprise) depending on when created,
        # but is_super_admin=True grants unlimited access regardless
        
        print(f"Super admin subscription: {data}")


class TestUserUsage:
    """Test user usage endpoint - GET /api/user/usage"""
    
    def test_get_user_usage(self, api_client, regular_user_token):
        """Test GET /api/user/usage returns usage stats with limits"""
        headers = {"Authorization": f"Bearer {regular_user_token}"}
        response = api_client.get(f"{API_URL}/user/usage", headers=headers)
        
        assert response.status_code == 200
        data = response.json()
        
        # Verify usage structure
        assert "usage" in data
        usage = data["usage"]
        assert "chat_messages" in usage
        assert "code_executions" in usage
        assert "video_generations" in usage
        assert "image_generations" in usage
        assert "credits_used" in usage
        
        # Verify limits structure
        assert "limits" in data
        limits = data["limits"]
        assert "chat_messages" in limits
        assert "code_executions" in limits
        
        # Verify period structure
        assert "period" in data
        period = data["period"]
        assert "start" in period
        assert "end" in period
        
        # Verify plan
        assert "plan" in data
        
        print(f"User usage: {data}")
    
    def test_super_admin_usage_is_unlimited(self, api_client, super_admin_token):
        """Test super admin usage shows unlimited"""
        headers = {"Authorization": f"Bearer {super_admin_token}"}
        response = api_client.get(f"{API_URL}/user/usage", headers=headers)
        
        assert response.status_code == 200
        data = response.json()
        
        assert data["is_unlimited"] == True
        
        print(f"Super admin usage unlimited: {data['is_unlimited']}")


class TestUserPreferences:
    """Test user preferences endpoints - GET/PUT /api/user/preferences"""
    
    def test_get_user_preferences(self, api_client, regular_user_token):
        """Test GET /api/user/preferences returns user preferences"""
        headers = {"Authorization": f"Bearer {regular_user_token}"}
        response = api_client.get(f"{API_URL}/user/preferences", headers=headers)
        
        assert response.status_code == 200
        data = response.json()
        
        # Verify preferences structure
        assert "default_agent" in data
        assert "default_mode" in data
        assert "ultra_thinking" in data
        assert "theme" in data
        
        print(f"User preferences: {data}")
    
    def test_update_user_preferences(self, api_client, regular_user_token):
        """Test PUT /api/user/preferences updates preferences"""
        headers = {"Authorization": f"Bearer {regular_user_token}"}
        
        # Update preferences
        new_preferences = {
            "default_agent": "forge",
            "default_mode": "e2",
            "ultra_thinking": True,
            "theme": "light"
        }
        
        response = api_client.put(f"{API_URL}/user/preferences", json=new_preferences, headers=headers)
        
        assert response.status_code == 200
        data = response.json()
        
        assert data["status"] == "updated"
        assert "preferences" in data
        
        prefs = data["preferences"]
        assert prefs["default_agent"] == "forge"
        assert prefs["default_mode"] == "e2"
        assert prefs["ultra_thinking"] == True
        assert prefs["theme"] == "light"
        
        print(f"Updated preferences: {prefs}")
        
        # Restore original preferences
        original_prefs = {
            "default_agent": "nova",
            "default_mode": "e1",
            "ultra_thinking": False,
            "theme": "dark"
        }
        api_client.put(f"{API_URL}/user/preferences", json=original_prefs, headers=headers)
    
    def test_get_updated_preferences_verify_persistence(self, api_client, regular_user_token):
        """Test GET preferences after update to verify persistence"""
        headers = {"Authorization": f"Bearer {regular_user_token}"}
        
        # First update
        new_preferences = {
            "default_agent": "sentinel",
            "default_mode": "prototype",
            "ultra_thinking": False,
            "theme": "dark"
        }
        api_client.put(f"{API_URL}/user/preferences", json=new_preferences, headers=headers)
        
        # Then GET to verify persistence
        response = api_client.get(f"{API_URL}/user/preferences", headers=headers)
        assert response.status_code == 200
        data = response.json()
        
        assert data["default_agent"] == "sentinel"
        assert data["default_mode"] == "prototype"
        
        print(f"Verified preferences persistence: {data}")
        
        # Restore original
        original_prefs = {
            "default_agent": "nova",
            "default_mode": "e1",
            "ultra_thinking": False,
            "theme": "dark"
        }
        api_client.put(f"{API_URL}/user/preferences", json=original_prefs, headers=headers)


class TestAdminStats:
    """Test admin stats endpoint - GET /api/admin/stats"""
    
    def test_admin_stats_for_super_admin(self, api_client, super_admin_token):
        """Test GET /api/admin/stats returns platform statistics for admin"""
        headers = {"Authorization": f"Bearer {super_admin_token}"}
        response = api_client.get(f"{API_URL}/admin/stats", headers=headers)
        
        assert response.status_code == 200
        data = response.json()
        
        # Verify users stats
        assert "users" in data
        users = data["users"]
        assert "total" in users
        assert "active" in users
        assert "premium" in users
        assert "free" in users
        assert users["total"] >= 1  # At least the super admin
        
        # Verify content stats
        assert "content" in data
        content = data["content"]
        assert "conversations" in content
        assert "projects" in content
        assert "videos" in content
        assert "images" in content
        
        print(f"Admin stats: {data}")
    
    def test_admin_stats_forbidden_for_regular_user(self, api_client, regular_user_token):
        """Test GET /api/admin/stats returns 403 for non-admin users"""
        headers = {"Authorization": f"Bearer {regular_user_token}"}
        response = api_client.get(f"{API_URL}/admin/stats", headers=headers)
        
        assert response.status_code == 403
        
        print(f"Admin stats correctly returns 403 for regular user")


class TestAdminUsers:
    """Test admin users endpoint - GET /api/admin/users"""
    
    def test_admin_users_for_super_admin(self, api_client, super_admin_token):
        """Test GET /api/admin/users returns all users for admin"""
        headers = {"Authorization": f"Bearer {super_admin_token}"}
        response = api_client.get(f"{API_URL}/admin/users", headers=headers)
        
        assert response.status_code == 200
        data = response.json()
        
        assert "users" in data
        assert "total" in data
        
        users = data["users"]
        assert len(users) >= 1  # At least super admin
        
        # Verify user structure (no password field)
        for user in users:
            assert "id" in user
            assert "email" in user
            assert "name" in user
            assert "password" not in user  # Password should be excluded
        
        print(f"Admin users: total={data['total']}, users retrieved={len(users)}")
    
    def test_admin_users_forbidden_for_regular_user(self, api_client, regular_user_token):
        """Test GET /api/admin/users returns 403 for non-admin users"""
        headers = {"Authorization": f"Bearer {regular_user_token}"}
        response = api_client.get(f"{API_URL}/admin/users", headers=headers)
        
        assert response.status_code == 403
        
        print(f"Admin users correctly returns 403 for regular user")
    
    def test_admin_users_pagination(self, api_client, super_admin_token):
        """Test admin users pagination with skip and limit"""
        headers = {"Authorization": f"Bearer {super_admin_token}"}
        
        # Test with skip and limit
        response = api_client.get(f"{API_URL}/admin/users?skip=0&limit=10", headers=headers)
        
        assert response.status_code == 200
        data = response.json()
        
        assert data["skip"] == 0
        assert data["limit"] == 10
        
        print(f"Admin users pagination: skip={data['skip']}, limit={data['limit']}")


class TestAdminAddCredits:
    """Test admin add credits endpoint - POST /api/admin/users/{id}/credits"""
    
    def test_admin_add_credits_to_user(self, api_client, super_admin_token, regular_user_id):
        """Test POST /api/admin/users/{id}/credits adds credits to user"""
        if not regular_user_id:
            pytest.skip("Regular user ID not available")
        
        headers = {"Authorization": f"Bearer {super_admin_token}"}
        
        # First get current credits
        response = api_client.get(f"{API_URL}/admin/users/{regular_user_id}", headers=headers)
        if response.status_code != 200:
            pytest.skip("Could not get user info")
        
        initial_credits = response.json().get("credits", 0)
        
        # Add credits
        amount_to_add = 50.0
        response = api_client.post(f"{API_URL}/admin/users/{regular_user_id}/credits?amount={amount_to_add}", headers=headers)
        
        assert response.status_code == 200
        data = response.json()
        
        assert data["status"] == "credits_added"
        assert data["amount"] == amount_to_add
        assert data["user_id"] == regular_user_id
        
        # Verify credits were actually added by getting user again
        response = api_client.get(f"{API_URL}/admin/users/{regular_user_id}", headers=headers)
        updated_credits = response.json().get("credits", 0)
        
        assert updated_credits == initial_credits + amount_to_add
        
        print(f"Admin added {amount_to_add} credits: initial={initial_credits}, updated={updated_credits}")
    
    def test_admin_add_credits_forbidden_for_regular_user(self, api_client, regular_user_token, regular_user_id):
        """Test POST /api/admin/users/{id}/credits returns 403 for non-admin"""
        if not regular_user_id:
            pytest.skip("Regular user ID not available")
        
        headers = {"Authorization": f"Bearer {regular_user_token}"}
        response = api_client.post(f"{API_URL}/admin/users/{regular_user_id}/credits?amount=10", headers=headers)
        
        assert response.status_code == 403
        
        print(f"Admin add credits correctly returns 403 for regular user")
    
    def test_admin_add_credits_not_found_for_invalid_user(self, api_client, super_admin_token):
        """Test POST /api/admin/users/{id}/credits returns 404 for non-existent user"""
        headers = {"Authorization": f"Bearer {super_admin_token}"}
        
        fake_user_id = "non-existent-user-id-12345"
        response = api_client.post(f"{API_URL}/admin/users/{fake_user_id}/credits?amount=10", headers=headers)
        
        assert response.status_code == 404
        
        print(f"Admin add credits correctly returns 404 for invalid user")


class TestCreditsDeductionOnCodeExecution:
    """Test credits deduction on code execution"""
    
    def test_code_execution_deducts_credits(self, api_client, regular_user_token):
        """Test that code execution deducts credits from regular user"""
        headers = {"Authorization": f"Bearer {regular_user_token}"}
        
        # Get initial credits
        response = api_client.get(f"{API_URL}/user/credits", headers=headers)
        initial_credits = response.json().get("credits", 0)
        
        # Execute some Python code
        code_request = {
            "code": "print('Hello World')",
            "language": "python"
        }
        response = api_client.post(f"{API_URL}/code/execute", json=code_request, headers=headers)
        
        # Should succeed or fail due to credits
        assert response.status_code in [200, 402]
        
        if response.status_code == 200:
            # Check output
            data = response.json()
            assert data["success"] == True
            assert "Hello World" in data["output"]
            
            # Get updated credits
            response = api_client.get(f"{API_URL}/user/credits", headers=headers)
            updated_credits = response.json().get("credits", 0)
            
            # Credits should be deducted (code_execution costs 0.05)
            assert updated_credits < initial_credits
            
            print(f"Code execution: initial={initial_credits}, updated={updated_credits}, deducted={initial_credits - updated_credits}")
        else:
            print(f"Code execution returned 402 - insufficient credits")


class TestUsageLogging:
    """Test usage logging tracks actions"""
    
    def test_usage_history_endpoint(self, api_client, regular_user_token):
        """Test GET /api/user/usage/history returns usage logs"""
        headers = {"Authorization": f"Bearer {regular_user_token}"}
        
        response = api_client.get(f"{API_URL}/user/usage/history", headers=headers)
        
        assert response.status_code == 200
        data = response.json()
        
        assert "history" in data
        assert "total" in data
        
        # History should be a list
        assert isinstance(data["history"], list)
        
        print(f"Usage history: total={data['total']}, entries={len(data['history'])}")
    
    def test_usage_history_with_action_filter(self, api_client, regular_user_token):
        """Test usage history with action filter"""
        headers = {"Authorization": f"Bearer {regular_user_token}"}
        
        response = api_client.get(f"{API_URL}/user/usage/history?action=code_execution", headers=headers)
        
        assert response.status_code == 200
        data = response.json()
        
        # All entries should be code_execution if any
        for entry in data["history"]:
            if "action" in entry:
                assert entry["action"] == "code_execution"
        
        print(f"Usage history filtered by code_execution: {len(data['history'])} entries")


class TestAdminUsage:
    """Test admin platform usage endpoint - GET /api/admin/usage"""
    
    def test_admin_usage_for_super_admin(self, api_client, super_admin_token):
        """Test GET /api/admin/usage returns platform usage for admin"""
        headers = {"Authorization": f"Bearer {super_admin_token}"}
        response = api_client.get(f"{API_URL}/admin/usage", headers=headers)
        
        assert response.status_code == 200
        data = response.json()
        
        assert "period_days" in data
        assert "usage_by_action" in data
        assert data["period_days"] == 30  # Default
        
        print(f"Admin platform usage: {data}")
    
    def test_admin_usage_forbidden_for_regular_user(self, api_client, regular_user_token):
        """Test GET /api/admin/usage returns 403 for non-admin"""
        headers = {"Authorization": f"Bearer {regular_user_token}"}
        response = api_client.get(f"{API_URL}/admin/usage", headers=headers)
        
        assert response.status_code == 403
        
        print(f"Admin usage correctly returns 403 for regular user")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
