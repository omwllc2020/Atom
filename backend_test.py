#!/usr/bin/env python3
"""
Backend API Testing Suite for ATOM AI App
Tests authentication, chat, IDE features (code execution, auto-fix, projects), video, image, and site cloning endpoints
"""
import requests
import sys
import time
import json
from datetime import datetime

class AtomAPITester:
    def __init__(self, base_url="https://nano-dev-creator.preview.emergentagent.com/api"):
        self.base_url = base_url
        self.token = None
        self.user_id = None
        self.tests_run = 0
        self.tests_passed = 0
        self.test_results = []
        
    def log_test(self, name, success, response_data=None, error=None):
        """Log test result"""
        self.tests_run += 1
        if success:
            self.tests_passed += 1
            
        result = {
            "test_name": name,
            "success": success,
            "timestamp": datetime.now().isoformat(),
            "response_data": response_data,
            "error": str(error) if error else None
        }
        self.test_results.append(result)
        
        status = "✅ PASSED" if success else "❌ FAILED"
        print(f"{status} - {name}")
        if error:
            print(f"   Error: {error}")
        if response_data and success:
            print(f"   Response: {response_data}")
        print()

    def run_test(self, name, method, endpoint, expected_status, data=None, headers=None):
        """Run a single API test"""
        url = f"{self.base_url}/{endpoint}"
        test_headers = {'Content-Type': 'application/json'}
        
        # Add auth header if token exists
        if self.token:
            test_headers['Authorization'] = f'Bearer {self.token}'
            
        # Add any additional headers
        if headers:
            test_headers.update(headers)

        print(f"🔍 Testing {name}...")
        print(f"   URL: {url}")
        print(f"   Method: {method}")
        
        try:
            if method == 'GET':
                response = requests.get(url, headers=test_headers, timeout=30)
            elif method == 'POST':
                response = requests.post(url, json=data, headers=test_headers, timeout=30)
            elif method == 'DELETE':
                response = requests.delete(url, headers=test_headers, timeout=30)
            else:
                raise ValueError(f"Unsupported method: {method}")

            success = response.status_code == expected_status
            response_data = None
            
            try:
                response_data = response.json() if response.text else {}
            except:
                response_data = {"status_code": response.status_code, "text": response.text[:200]}

            if not success:
                error = f"Expected {expected_status}, got {response.status_code}. Response: {response_data}"
                self.log_test(name, False, response_data, error)
                return False, response_data
            
            self.log_test(name, True, response_data)
            return True, response_data

        except Exception as e:
            self.log_test(name, False, None, str(e))
            return False, {}

    def test_health_check(self):
        """Test basic API health"""
        success, response = self.run_test(
            "API Health Check",
            "GET", 
            "",
            200
        )
        return success

    def test_register(self):
        """Test user registration"""
        timestamp = int(time.time())
        test_email = f"test_user_{timestamp}@forge.ai"
        test_name = f"Test User {timestamp}"
        test_password = "testpass123"
        
        success, response = self.run_test(
            "User Registration",
            "POST",
            "auth/register",
            200,
            data={
                "email": test_email,
                "password": test_password,
                "name": test_name
            }
        )
        
        if success and response.get('access_token'):
            self.token = response['access_token']
            self.user_id = response.get('user', {}).get('id')
            print(f"   ✓ Token received: {self.token[:20]}...")
            print(f"   ✓ User ID: {self.user_id}")
            
        return success

    def test_login(self):
        """Test user login with existing credentials"""
        success, response = self.run_test(
            "User Login",
            "POST",
            "auth/login", 
            200,
            data={
                "email": "test@forge.ai",
                "password": "testpass123"
            }
        )
        
        if success and response.get('access_token'):
            # Use this token for subsequent tests if registration failed
            if not self.token:
                self.token = response['access_token']
                self.user_id = response.get('user', {}).get('id')
                print(f"   ✓ Fallback token from login: {self.token[:20]}...")
                
        return success

    def test_get_profile(self):
        """Test getting user profile"""
        if not self.token:
            self.log_test("Get User Profile", False, None, "No auth token available")
            return False
            
        success, response = self.run_test(
            "Get User Profile",
            "GET",
            "auth/me",
            200
        )
        return success

    def test_chat_message(self):
        """Test sending chat message to AI"""
        if not self.token:
            self.log_test("Chat Message", False, None, "No auth token available")
            return False
            
        success, response = self.run_test(
            "Send Chat Message",
            "POST",
            "chat",
            200,
            data={
                "message": "Hello, write a simple Python function to add two numbers",
                "context": None
            }
        )
        
        if success:
            self.conversation_id = response.get('conversation_id')
            print(f"   ✓ Conversation ID: {self.conversation_id}")
            
        return success

    def test_get_conversations(self):
        """Test getting user conversations"""
        if not self.token:
            self.log_test("Get Conversations", False, None, "No auth token available")
            return False
            
        success, response = self.run_test(
            "Get Conversations",
            "GET", 
            "conversations",
            200
        )
        return success

    def test_video_generation_start(self):
        """Test starting video generation"""
        if not self.token:
            self.log_test("Video Generation", False, None, "No auth token available")
            return False
            
        success, response = self.run_test(
            "Start Video Generation", 
            "POST",
            "video/generate",
            200,
            data={
                "prompt": "A simple animation of a bouncing ball",
                "size": "1280x720",
                "duration": 4
            }
        )
        
        if success:
            self.video_id = response.get('video_id')
            print(f"   ✓ Video ID: {self.video_id}")
            
        return success

    def test_video_status(self):
        """Test checking video generation status"""
        if not self.token or not hasattr(self, 'video_id'):
            self.log_test("Video Status Check", False, None, "No video ID available")
            return False
            
        success, response = self.run_test(
            "Check Video Status",
            "GET",
            f"video/status/{self.video_id}",
            200
        )
        
        if success:
            print(f"   ✓ Video status: {response.get('status')}")
            
        return success

    def test_image_generation(self):
        """Test image generation"""  
        if not self.token:
            self.log_test("Image Generation", False, None, "No auth token available")
            return False
            
        success, response = self.run_test(
            "Generate Image",
            "POST",
            "image/generate",
            200,
            data={
                "prompt": "A cute robot coding at a computer"
            }
        )
        
        if success:
            self.image_id = response.get('image_id')
            print(f"   ✓ Image ID: {self.image_id}")
            has_image = bool(response.get('image_data'))
            print(f"   ✓ Has image data: {has_image}")
            
        return success

    def test_site_cloning(self):
        """Test site cloning functionality"""
        if not self.token:
            self.log_test("Site Cloning", False, None, "No auth token available")
            return False
            
        success, response = self.run_test(
            "Clone Website",
            "POST", 
            "clone/site",
            200,
            data={
                "url": "https://example.com"
            }
        )
        
        if success:
            self.clone_id = response.get('clone_id')
            print(f"   ✓ Clone ID: {self.clone_id}")
            has_code = bool(response.get('code'))
            print(f"   ✓ Has generated code: {has_code}")
            
        return success

    def test_code_execution(self):
        """Test code execution functionality"""
        if not self.token:
            self.log_test("Code Execution", False, None, "No auth token available")
            return False
        
        # Test Python code execution
        success, response = self.run_test(
            "Execute Python Code",
            "POST",
            "code/execute",
            200,
            data={
                "code": "print('Hello from Python!')\nresult = 2 + 2\nprint(f'2 + 2 = {result}')",
                "language": "python"
            }
        )
        
        if success:
            print(f"   ✓ Output: {response.get('output', '')[:100]}...")
            print(f"   ✓ Success: {response.get('success')}")
            
        return success
    
    def test_javascript_execution(self):
        """Test JavaScript code execution"""
        if not self.token:
            self.log_test("JavaScript Execution", False, None, "No auth token available")
            return False
            
        success, response = self.run_test(
            "Execute JavaScript Code",
            "POST",
            "code/execute",
            200,
            data={
                "code": "console.log('Hello from JavaScript!');\nconst result = 2 + 2;\nconsole.log(`2 + 2 = ${result}`);",
                "language": "javascript"
            }
        )
        
        if success:
            print(f"   ✓ Output: {response.get('output', '')[:100]}...")
            print(f"   ✓ Success: {response.get('success')}")
            
        return success
    
    def test_html_execution(self):
        """Test HTML code execution"""
        if not self.token:
            self.log_test("HTML Execution", False, None, "No auth token available")
            return False
            
        success, response = self.run_test(
            "Execute HTML Code",
            "POST",
            "code/execute",
            200,
            data={
                "code": "<!DOCTYPE html><html><body><h1>Test HTML</h1></body></html>",
                "language": "html"
            }
        )
        
        if success:
            print(f"   ✓ Output: {response.get('output', '')[:50]}...")
            print(f"   ✓ Success: {response.get('success')}")
            
        return success
    
    def test_autofix_functionality(self):
        """Test auto-fix functionality"""
        if not self.token:
            self.log_test("Auto-fix", False, None, "No auth token available")
            return False
            
        # Test with broken Python code
        success, response = self.run_test(
            "Auto-fix Python Code",
            "POST",
            "code/autofix",
            200,
            data={
                "code": "print('Hello World'\n# Missing closing parenthesis",
                "language": "python",
                "error": "SyntaxError: '(' was never closed"
            }
        )
        
        if success:
            print(f"   ✓ Fixed: {response.get('success')}")
            print(f"   ✓ Explanation: {response.get('explanation', '')[:100]}...")
            
        return success
    
    def test_autofix_loop(self):
        """Test auto-fix loop functionality"""
        if not self.token:
            self.log_test("Auto-fix Loop", False, None, "No auth token available")
            return False
            
        success, response = self.run_test(
            "Auto-fix Loop",
            "POST",
            "code/autofix-loop",
            200,
            data={
                "code": "print('Hello World'\n# Missing closing parenthesis",
                "language": "python"
            }
        )
        
        if success:
            print(f"   ✓ Final success: {response.get('success')}")
            print(f"   ✓ Attempts: {response.get('total_attempts')}")
            
        return success
    
    def test_project_management(self):
        """Test project management functionality"""
        if not self.token:
            self.log_test("Project Management", False, None, "No auth token available")
            return False
        
        # Create a project
        success, response = self.run_test(
            "Create Project",
            "POST",
            "projects",
            200,
            data={
                "name": "Test Project",
                "description": "A test project for API testing"
            }
        )
        
        if success:
            self.project_id = response.get('id')
            print(f"   ✓ Project ID: {self.project_id}")
            print(f"   ✓ Default files: {len(response.get('files', []))}")
            
        return success
    
    def test_project_operations(self):
        """Test project file operations"""
        if not self.token or not hasattr(self, 'project_id'):
            self.log_test("Project Operations", False, None, "No project ID available")
            return False
        
        # Get projects
        success1, response = self.run_test(
            "Get Projects",
            "GET",
            "projects",
            200
        )
        
        # Get specific project
        success2, response = self.run_test(
            "Get Project Details",
            "GET",
            f"projects/{self.project_id}",
            200
        )
        
        # Add a file
        success3, response = self.run_test(
            "Add File to Project",
            "POST",
            f"projects/{self.project_id}/files",
            200,
            data={
                "name": "test.py",
                "content": "print('Test file')",
                "language": "python"
            }
        )
        
        # Update a file
        success4, response = self.run_test(
            "Update File in Project",
            "PUT",
            f"projects/{self.project_id}/files/test.py",
            200,
            data={
                "content": "print('Updated test file')"
            }
        )
        
        return all([success1, success2, success3, success4])

    def test_get_user_content(self):
        """Test getting user generated content"""
        if not self.token:
            return False
            
        endpoints = [
            ("Get User Videos", "videos"),
            ("Get User Images", "images"), 
            ("Get User Clones", "clones")
        ]
        
        all_success = True
        for name, endpoint in endpoints:
            success, response = self.run_test(name, "GET", endpoint, 200)
            if not success:
                all_success = False
                
        return all_success

    def run_all_tests(self):
        """Run complete test suite"""
        print("=" * 60)
        print("🚀 ATOM AI API TESTING SUITE")
        print("=" * 60)
        print(f"Testing against: {self.base_url}")
        print()
        
        # Basic connectivity
        if not self.test_health_check():
            print("❌ API health check failed - stopping tests")
            return False
            
        # Authentication flow
        self.test_register()
        if not self.token:
            print("⚠️  Registration failed, trying login...")
            self.test_login()
            
        if not self.token:
            print("❌ No authentication token - stopping tests")
            return False
            
        self.test_get_profile()
        
        # Core functionality
        self.test_chat_message()
        self.test_get_conversations()
        
        # IDE/Code execution features (NEW)
        self.test_code_execution()
        self.test_javascript_execution()  
        self.test_html_execution()
        self.test_autofix_functionality()
        self.test_autofix_loop()
        self.test_project_management()
        self.test_project_operations()
        
        # Media generation
        self.test_video_generation_start()
        self.test_video_status()
        self.test_image_generation()
        self.test_site_cloning()
        self.test_get_user_content()
        
        # Print results
        print("=" * 60)
        print("📊 TEST RESULTS SUMMARY")
        print("=" * 60)
        print(f"Tests Run: {self.tests_run}")
        print(f"Tests Passed: {self.tests_passed}")
        print(f"Tests Failed: {self.tests_run - self.tests_passed}")
        print(f"Success Rate: {(self.tests_passed/self.tests_run)*100:.1f}%")
        print()
        
        # Show failures
        failures = [r for r in self.test_results if not r['success']]
        if failures:
            print("❌ FAILED TESTS:")
            for failure in failures:
                print(f"  - {failure['test_name']}: {failure['error']}")
        else:
            print("✅ ALL TESTS PASSED!")
            
        return self.tests_passed == self.tests_run

if __name__ == "__main__":
    tester = AtomAPITester()
    success = tester.run_all_tests()
    
    # Save results to file
    with open("/app/test_results_backend.json", "w") as f:
        json.dump({
            "success": success,
            "total_tests": tester.tests_run,
            "passed_tests": tester.tests_passed, 
            "test_results": tester.test_results,
            "timestamp": datetime.now().isoformat()
        }, f, indent=2)
    
    sys.exit(0 if success else 1)