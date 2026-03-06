#!/usr/bin/env python3
"""
ATOM AI Platform - Stripe Checkout and Payment API Test Suite

Tests for Stripe checkout endpoints:
- POST /api/checkout/subscription - Creates Stripe checkout session for subscription plans
- POST /api/checkout/credits - Creates Stripe checkout session for credit top-ups
- GET /api/checkout/status/{session_id} - Returns payment status
- GET /api/payment/history - Returns user's payment history
- GET /api/subscription - Returns subscription details with credit_packages

Also tests edge cases:
- Invalid plan/package IDs return 400 errors
- Super admin access behavior
"""

import pytest
import requests
import os
import time

BASE_URL = os.environ.get('REACT_APP_BACKEND_URL', 'https://nano-dev-creator.preview.emergentagent.com').rstrip('/')
API_URL = f"{BASE_URL}/api"
ORIGIN_URL = "https://nano-dev-creator.preview.emergentagent.com"

# Test credentials
SUPER_ADMIN_CREDS = {
    "email": "Antoniohoshaw6@gmail.com",
    "password": "admin123"
}
REGULAR_USER_CREDS = {
    "email": "testuser@test.com",
    "password": "test123"
}

# Valid plan IDs
VALID_PLAN_IDS = ["free", "core", "pro", "enterprise"]
PAID_PLAN_IDS = ["core", "pro", "enterprise"]

# Valid credit package IDs
VALID_PACKAGE_IDS = ["small", "medium", "large", "xlarge"]


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


# ==================== SUBSCRIPTION ENDPOINT WITH CREDIT_PACKAGES ====================

class TestSubscriptionWithCreditPackages:
    """Test GET /api/subscription returns credit_packages"""
    
    def test_subscription_returns_credit_packages(self, api_client, regular_user_token):
        """Test GET /api/subscription includes credit_packages"""
        headers = {"Authorization": f"Bearer {regular_user_token}"}
        response = api_client.get(f"{API_URL}/subscription", headers=headers)
        
        assert response.status_code == 200
        data = response.json()
        
        # Check credit_packages is present
        assert "credit_packages" in data, "credit_packages not found in subscription response"
        
        credit_packages = data["credit_packages"]
        
        # Verify structure
        assert isinstance(credit_packages, dict), "credit_packages should be a dict"
        
        # Check expected packages exist
        for pkg_id in VALID_PACKAGE_IDS:
            assert pkg_id in credit_packages, f"Package '{pkg_id}' not found in credit_packages"
            
            pkg = credit_packages[pkg_id]
            assert "name" in pkg, f"Package {pkg_id} missing 'name'"
            assert "credits" in pkg, f"Package {pkg_id} missing 'credits'"
            assert "price" in pkg, f"Package {pkg_id} missing 'price'"
        
        # Verify specific values based on problem statement
        assert credit_packages["small"]["price"] == 5, "Small package price should be $5"
        assert credit_packages["small"]["credits"] == 10, "Small package credits should be 10"
        
        assert credit_packages["medium"]["price"] == 10, "Medium package price should be $10"
        assert credit_packages["medium"]["credits"] == 25, "Medium package credits should be 25"
        
        assert credit_packages["large"]["price"] == 18, "Large package price should be $18"
        assert credit_packages["large"]["credits"] == 50, "Large package credits should be 50"
        
        assert credit_packages["xlarge"]["price"] == 30, "XL package price should be $30"
        assert credit_packages["xlarge"]["credits"] == 100, "XL package credits should be 100"
        
        print(f"Credit packages verified: {list(credit_packages.keys())}")
        print(f"Package details: {credit_packages}")


# ==================== SUBSCRIPTION CHECKOUT ====================

class TestSubscriptionCheckout:
    """Test POST /api/checkout/subscription"""
    
    def test_subscription_checkout_creates_session_for_core(self, api_client, regular_user_token):
        """Test creating checkout session for Core plan ($20)"""
        headers = {"Authorization": f"Bearer {regular_user_token}"}
        payload = {
            "plan_id": "core",
            "origin_url": ORIGIN_URL
        }
        
        response = api_client.post(f"{API_URL}/checkout/subscription", json=payload, headers=headers)
        
        assert response.status_code == 200
        data = response.json()
        
        assert "checkout_url" in data, "checkout_url not in response"
        assert "session_id" in data, "session_id not in response"
        
        # Stripe checkout URLs should contain checkout.stripe.com
        assert "checkout.stripe.com" in data["checkout_url"], "Checkout URL should contain 'checkout.stripe.com'"
        
        print(f"Core plan checkout - session_id: {data['session_id']}")
        print(f"Checkout URL contains 'checkout.stripe.com': {data['checkout_url'][:60]}...")
    
    def test_subscription_checkout_creates_session_for_pro(self, api_client, regular_user_token):
        """Test creating checkout session for Pro plan ($40)"""
        headers = {"Authorization": f"Bearer {regular_user_token}"}
        payload = {
            "plan_id": "pro",
            "origin_url": ORIGIN_URL
        }
        
        response = api_client.post(f"{API_URL}/checkout/subscription", json=payload, headers=headers)
        
        assert response.status_code == 200
        data = response.json()
        
        assert "checkout_url" in data
        assert "session_id" in data
        assert "checkout.stripe.com" in data["checkout_url"]
        
        print(f"Pro plan checkout - session_id: {data['session_id']}")
    
    def test_subscription_checkout_creates_session_for_enterprise(self, api_client, regular_user_token):
        """Test creating checkout session for Enterprise plan ($99)"""
        headers = {"Authorization": f"Bearer {regular_user_token}"}
        payload = {
            "plan_id": "enterprise",
            "origin_url": ORIGIN_URL
        }
        
        response = api_client.post(f"{API_URL}/checkout/subscription", json=payload, headers=headers)
        
        assert response.status_code == 200
        data = response.json()
        
        assert "checkout_url" in data
        assert "session_id" in data
        assert "checkout.stripe.com" in data["checkout_url"]
        
        print(f"Enterprise plan checkout - session_id: {data['session_id']}")
    
    def test_subscription_checkout_rejects_free_plan(self, api_client, regular_user_token):
        """Test that free plan checkout returns 400"""
        headers = {"Authorization": f"Bearer {regular_user_token}"}
        payload = {
            "plan_id": "free",
            "origin_url": ORIGIN_URL
        }
        
        response = api_client.post(f"{API_URL}/checkout/subscription", json=payload, headers=headers)
        
        assert response.status_code == 400
        data = response.json()
        assert "detail" in data
        
        print(f"Free plan checkout correctly rejected: {data['detail']}")
    
    def test_subscription_checkout_rejects_invalid_plan(self, api_client, regular_user_token):
        """Test that invalid plan ID returns 400"""
        headers = {"Authorization": f"Bearer {regular_user_token}"}
        payload = {
            "plan_id": "invalid_plan_xyz",
            "origin_url": ORIGIN_URL
        }
        
        response = api_client.post(f"{API_URL}/checkout/subscription", json=payload, headers=headers)
        
        assert response.status_code == 400
        data = response.json()
        assert "detail" in data
        
        print(f"Invalid plan correctly rejected: {data['detail']}")
    
    def test_subscription_checkout_rejects_missing_plan_id(self, api_client, regular_user_token):
        """Test that missing plan_id returns 400"""
        headers = {"Authorization": f"Bearer {regular_user_token}"}
        payload = {
            "origin_url": ORIGIN_URL
        }
        
        response = api_client.post(f"{API_URL}/checkout/subscription", json=payload, headers=headers)
        
        assert response.status_code == 400
        
        print(f"Missing plan_id correctly rejected")


# ==================== CREDITS CHECKOUT ====================

class TestCreditsCheckout:
    """Test POST /api/checkout/credits"""
    
    def test_credits_checkout_creates_session_for_small(self, api_client, regular_user_token):
        """Test creating checkout session for Small credit package ($5 for 10 credits)"""
        headers = {"Authorization": f"Bearer {regular_user_token}"}
        payload = {
            "package_id": "small",
            "origin_url": ORIGIN_URL
        }
        
        response = api_client.post(f"{API_URL}/checkout/credits", json=payload, headers=headers)
        
        assert response.status_code == 200
        data = response.json()
        
        assert "checkout_url" in data
        assert "session_id" in data
        assert "checkout.stripe.com" in data["checkout_url"]
        
        print(f"Small package checkout - session_id: {data['session_id']}")
    
    def test_credits_checkout_creates_session_for_medium(self, api_client, regular_user_token):
        """Test creating checkout session for Medium credit package ($10 for 25 credits)"""
        headers = {"Authorization": f"Bearer {regular_user_token}"}
        payload = {
            "package_id": "medium",
            "origin_url": ORIGIN_URL
        }
        
        response = api_client.post(f"{API_URL}/checkout/credits", json=payload, headers=headers)
        
        assert response.status_code == 200
        data = response.json()
        
        assert "checkout_url" in data
        assert "session_id" in data
        
        print(f"Medium package checkout - session_id: {data['session_id']}")
    
    def test_credits_checkout_creates_session_for_large(self, api_client, regular_user_token):
        """Test creating checkout session for Large credit package ($18 for 50 credits)"""
        headers = {"Authorization": f"Bearer {regular_user_token}"}
        payload = {
            "package_id": "large",
            "origin_url": ORIGIN_URL
        }
        
        response = api_client.post(f"{API_URL}/checkout/credits", json=payload, headers=headers)
        
        assert response.status_code == 200
        data = response.json()
        
        assert "checkout_url" in data
        assert "session_id" in data
        
        print(f"Large package checkout - session_id: {data['session_id']}")
    
    def test_credits_checkout_creates_session_for_xlarge(self, api_client, regular_user_token):
        """Test creating checkout session for XL credit package ($30 for 100 credits)"""
        headers = {"Authorization": f"Bearer {regular_user_token}"}
        payload = {
            "package_id": "xlarge",
            "origin_url": ORIGIN_URL
        }
        
        response = api_client.post(f"{API_URL}/checkout/credits", json=payload, headers=headers)
        
        assert response.status_code == 200
        data = response.json()
        
        assert "checkout_url" in data
        assert "session_id" in data
        
        print(f"XL package checkout - session_id: {data['session_id']}")
    
    def test_credits_checkout_rejects_invalid_package(self, api_client, regular_user_token):
        """Test that invalid package ID returns 400"""
        headers = {"Authorization": f"Bearer {regular_user_token}"}
        payload = {
            "package_id": "invalid_package_xyz",
            "origin_url": ORIGIN_URL
        }
        
        response = api_client.post(f"{API_URL}/checkout/credits", json=payload, headers=headers)
        
        assert response.status_code == 400
        data = response.json()
        assert "detail" in data
        
        print(f"Invalid package correctly rejected: {data['detail']}")
    
    def test_credits_checkout_rejects_missing_package_id(self, api_client, regular_user_token):
        """Test that missing package_id returns 400"""
        headers = {"Authorization": f"Bearer {regular_user_token}"}
        payload = {
            "origin_url": ORIGIN_URL
        }
        
        response = api_client.post(f"{API_URL}/checkout/credits", json=payload, headers=headers)
        
        assert response.status_code == 400
        
        print(f"Missing package_id correctly rejected")


# ==================== CHECKOUT STATUS ====================

class TestCheckoutStatus:
    """Test GET /api/checkout/status/{session_id}"""
    
    def test_checkout_status_with_nonexistent_session(self, api_client, regular_user_token):
        """Test status check with non-existent session returns 404"""
        headers = {"Authorization": f"Bearer {regular_user_token}"}
        fake_session_id = "cs_test_fake_session_12345"
        
        response = api_client.get(f"{API_URL}/checkout/status/{fake_session_id}", headers=headers)
        
        assert response.status_code == 404
        data = response.json()
        assert "detail" in data
        
        print(f"Non-existent session correctly returns 404: {data['detail']}")
    
    def test_checkout_status_with_real_session(self, api_client, regular_user_token):
        """Test status check with a real (but unpaid) session"""
        headers = {"Authorization": f"Bearer {regular_user_token}"}
        
        # First create a checkout session
        payload = {
            "package_id": "small",
            "origin_url": ORIGIN_URL
        }
        create_response = api_client.post(f"{API_URL}/checkout/credits", json=payload, headers=headers)
        
        if create_response.status_code != 200:
            pytest.skip("Could not create checkout session for status test")
        
        session_id = create_response.json()["session_id"]
        
        # Now check the status
        response = api_client.get(f"{API_URL}/checkout/status/{session_id}", headers=headers)
        
        assert response.status_code == 200
        data = response.json()
        
        # Should have status fields
        assert "status" in data
        assert "payment_status" in data
        
        print(f"Checkout status for {session_id}: status={data['status']}, payment_status={data['payment_status']}")


# ==================== PAYMENT HISTORY ====================

class TestPaymentHistory:
    """Test GET /api/payment/history"""
    
    def test_payment_history_returns_list(self, api_client, regular_user_token):
        """Test GET /api/payment/history returns transactions list"""
        headers = {"Authorization": f"Bearer {regular_user_token}"}
        
        response = api_client.get(f"{API_URL}/payment/history", headers=headers)
        
        assert response.status_code == 200
        data = response.json()
        
        assert "transactions" in data
        assert isinstance(data["transactions"], list)
        
        print(f"Payment history: {len(data['transactions'])} transactions")
        
        # If there are transactions, verify structure
        if len(data["transactions"]) > 0:
            tx = data["transactions"][0]
            print(f"Sample transaction: type={tx.get('type')}, amount={tx.get('amount')}, status={tx.get('status')}")
    
    def test_payment_history_limit_parameter(self, api_client, regular_user_token):
        """Test payment history limit parameter"""
        headers = {"Authorization": f"Bearer {regular_user_token}"}
        
        response = api_client.get(f"{API_URL}/payment/history?limit=5", headers=headers)
        
        assert response.status_code == 200
        data = response.json()
        
        assert len(data["transactions"]) <= 5
        
        print(f"Payment history with limit=5: {len(data['transactions'])} transactions")


# ==================== SUBSCRIPTION PLANS VERIFICATION ====================

class TestSubscriptionPlansReplit:
    """Verify subscription plans match Replit pricing model"""
    
    def test_subscription_plans_match_requirements(self, api_client):
        """Test subscription plans match specified pricing"""
        response = api_client.get(f"{API_URL}/subscription/plans")
        
        assert response.status_code == 200
        data = response.json()
        plans = data["plans"]
        
        # Find each plan
        plan_dict = {p["id"]: p for p in plans}
        
        # Free: $0, 10 credits
        assert "free" in plan_dict
        free = plan_dict["free"]
        assert free["price_monthly"] == 0, f"Free plan should be $0, got ${free['price_monthly']}"
        assert free["credits_monthly"] == 10, f"Free plan should have 10 credits, got {free['credits_monthly']}"
        
        # Core: $20, 25 credits
        assert "core" in plan_dict
        core = plan_dict["core"]
        assert core["price_monthly"] == 20, f"Core plan should be $20, got ${core['price_monthly']}"
        assert core["credits_monthly"] == 25, f"Core plan should have 25 credits, got {core['credits_monthly']}"
        
        # Pro: $40, 50 credits
        assert "pro" in plan_dict
        pro = plan_dict["pro"]
        assert pro["price_monthly"] == 40, f"Pro plan should be $40, got ${pro['price_monthly']}"
        assert pro["credits_monthly"] == 50, f"Pro plan should have 50 credits, got {pro['credits_monthly']}"
        
        # Enterprise: $99, unlimited (-1)
        assert "enterprise" in plan_dict
        enterprise = plan_dict["enterprise"]
        assert enterprise["price_monthly"] == 99, f"Enterprise plan should be $99, got ${enterprise['price_monthly']}"
        assert enterprise["credits_monthly"] == -1, f"Enterprise plan should have unlimited (-1) credits, got {enterprise['credits_monthly']}"
        
        print("All subscription plans verified:")
        print(f"  Free: ${free['price_monthly']}/mo, {free['credits_monthly']} credits")
        print(f"  Core: ${core['price_monthly']}/mo, {core['credits_monthly']} credits")
        print(f"  Pro: ${pro['price_monthly']}/mo, {pro['credits_monthly']} credits")
        print(f"  Enterprise: ${enterprise['price_monthly']}/mo, unlimited credits")


# ==================== SUPER ADMIN BEHAVIOR ====================

class TestSuperAdminCheckoutBehavior:
    """Test super admin checkout behavior - super admin has unlimited so shouldn't need to checkout"""
    
    def test_super_admin_subscription_shows_unlimited(self, api_client, super_admin_token):
        """Test that super admin subscription shows unlimited (is_super_admin)"""
        headers = {"Authorization": f"Bearer {super_admin_token}"}
        
        response = api_client.get(f"{API_URL}/subscription", headers=headers)
        
        assert response.status_code == 200
        data = response.json()
        
        assert data["is_super_admin"] == True, "Super admin should have is_super_admin=True"
        
        # Super admin credits should be unlimited (-1 or null)
        credits = data.get("credits")
        print(f"Super admin subscription: is_super_admin={data['is_super_admin']}, credits={credits}")
    
    def test_super_admin_can_still_create_checkout(self, api_client, super_admin_token):
        """Test that super admin CAN still create checkout if desired (no blocking)"""
        headers = {"Authorization": f"Bearer {super_admin_token}"}
        payload = {
            "package_id": "small",
            "origin_url": ORIGIN_URL
        }
        
        response = api_client.post(f"{API_URL}/checkout/credits", json=payload, headers=headers)
        
        # Should still work - the backend doesn't block super admin from checkout
        assert response.status_code == 200
        data = response.json()
        assert "checkout_url" in data
        
        print("Super admin can create checkout (not blocked by backend)")


# ==================== AUTHENTICATION REQUIRED ====================

class TestCheckoutAuthentication:
    """Test that checkout endpoints require authentication"""
    
    def test_subscription_checkout_requires_auth(self, api_client):
        """Test POST /api/checkout/subscription requires authentication"""
        payload = {
            "plan_id": "core",
            "origin_url": ORIGIN_URL
        }
        
        response = api_client.post(f"{API_URL}/checkout/subscription", json=payload)
        
        assert response.status_code in [401, 403]
        print("Subscription checkout correctly requires authentication")
    
    def test_credits_checkout_requires_auth(self, api_client):
        """Test POST /api/checkout/credits requires authentication"""
        payload = {
            "package_id": "small",
            "origin_url": ORIGIN_URL
        }
        
        response = api_client.post(f"{API_URL}/checkout/credits", json=payload)
        
        assert response.status_code in [401, 403]
        print("Credits checkout correctly requires authentication")
    
    def test_checkout_status_requires_auth(self, api_client):
        """Test GET /api/checkout/status/{session_id} requires authentication"""
        response = api_client.get(f"{API_URL}/checkout/status/fake_session")
        
        assert response.status_code in [401, 403]
        print("Checkout status correctly requires authentication")
    
    def test_payment_history_requires_auth(self, api_client):
        """Test GET /api/payment/history requires authentication"""
        response = api_client.get(f"{API_URL}/payment/history")
        
        assert response.status_code in [401, 403]
        print("Payment history correctly requires authentication")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
