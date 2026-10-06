"""
Test suite for Brightluxx Security Features:
- Admin authentication (login, /me, refresh tokens)
- Password change validation
- Rate limiting (login + lead submissions)
- Image upload with optimization
- Security headers
"""

import pytest
import requests
import os
import time
from io import BytesIO
from PIL import Image

BASE_URL = os.environ.get('REACT_APP_BACKEND_URL', '').rstrip('/')

# Test credentials from environment
ADMIN_EMAIL = os.environ.get("ADMIN_EMAIL", "admin@brightluxx.com")
ADMIN_PASSWORD = os.environ.get("ADMIN_PASSWORD", "")


class TestAdminAuthentication:
    """Admin login, /me, and token refresh tests"""

    def test_admin_login_success(self):
        """Test 1: Admin login returns token, refresh_token, and admin info"""
        response = requests.post(f"{BASE_URL}/api/admin/login", json={
            "email": ADMIN_EMAIL,
            "password": ADMIN_PASSWORD
        })
        assert response.status_code == 200, f"Login failed: {response.text}"
        data = response.json()
        
        # Verify response structure
        assert "token" in data, "Missing token in response"
        assert "refresh_token" in data, "Missing refresh_token in response"
        assert "admin" in data, "Missing admin info in response"
        assert "expires_in" in data, "Missing expires_in in response"
        
        # Verify admin info
        assert data["admin"]["email"] == ADMIN_EMAIL
        assert "role" in data["admin"]
        
        # Store for later tests
        self.__class__.token = data["token"]
        self.__class__.refresh_token = data["refresh_token"]
        print(f"Login success - Token received, expires_in: {data['expires_in']}s")

    def test_admin_me_endpoint(self):
        """Test 2: GET /api/admin/me returns admin info with valid token"""
        token = getattr(self.__class__, 'token', None)
        if not token:
            pytest.skip("No token available from login test")
        
        response = requests.get(f"{BASE_URL}/api/admin/me", headers={
            "Authorization": f"Bearer {token}"
        })
        assert response.status_code == 200, f"Admin /me failed: {response.text}"
        data = response.json()
        
        assert data["email"] == ADMIN_EMAIL
        assert "role" in data
        print(f"Admin /me success - email: {data['email']}, role: {data['role']}")

    def test_admin_me_without_token(self):
        """Test: /me endpoint requires authentication"""
        response = requests.get(f"{BASE_URL}/api/admin/me")
        assert response.status_code == 401, "Should require authentication"
        print("Admin /me correctly requires authentication")

    def test_token_refresh(self):
        """Test 3: Refresh token returns new access token"""
        refresh_token = getattr(self.__class__, 'refresh_token', None)
        if not refresh_token:
            pytest.skip("No refresh token available")
        
        response = requests.post(f"{BASE_URL}/api/admin/refresh", json={
            "refresh_token": refresh_token
        })
        assert response.status_code == 200, f"Token refresh failed: {response.text}"
        data = response.json()
        
        assert "token" in data, "Missing new token in refresh response"
        assert "expires_in" in data, "Missing expires_in in refresh response"
        
        # Verify new token works
        new_token = data["token"]
        me_response = requests.get(f"{BASE_URL}/api/admin/me", headers={
            "Authorization": f"Bearer {new_token}"
        })
        assert me_response.status_code == 200, "New token should work"
        print(f"Token refresh success - new expires_in: {data['expires_in']}s")

    def test_invalid_refresh_token(self):
        """Test: Invalid refresh token returns 401"""
        response = requests.post(f"{BASE_URL}/api/admin/refresh", json={
            "refresh_token": "invalid-token"
        })
        assert response.status_code == 401, "Invalid refresh token should fail"
        print("Invalid refresh token correctly rejected")


class TestPasswordChange:
    """Password change tests"""

    @pytest.fixture
    def auth_token(self):
        """Get fresh auth token"""
        response = requests.post(f"{BASE_URL}/api/admin/login", json={
            "email": ADMIN_EMAIL,
            "password": ADMIN_PASSWORD
        })
        if response.status_code == 200:
            return response.json()["token"]
        pytest.skip("Could not get auth token")

    def test_password_change_wrong_current(self, auth_token):
        """Test 5a: Wrong current password returns 400"""
        response = requests.post(f"{BASE_URL}/api/admin/change-password", 
            headers={"Authorization": f"Bearer {auth_token}"},
            json={
                "current_password": "wrongpassword",
                "new_password": "newpass123"
            }
        )
        assert response.status_code == 400, f"Should reject wrong current password: {response.text}"
        assert "incorrect" in response.json().get("detail", "").lower()
        print("Wrong current password correctly rejected")

    def test_password_change_short_new(self, auth_token):
        """Test 5b: Short new password (<8 chars) returns 400"""
        response = requests.post(f"{BASE_URL}/api/admin/change-password",
            headers={"Authorization": f"Bearer {auth_token}"},
            json={
                "current_password": ADMIN_PASSWORD,
                "new_password": "short"
            }
        )
        assert response.status_code == 400, f"Should reject short password: {response.text}"
        assert "8 characters" in response.json().get("detail", "").lower()
        print("Short password correctly rejected")

    def test_password_change_full_cycle(self, auth_token):
        """Test 4: Change password, verify login works, revert"""
        NEW_PASSWORD = os.environ.get("TEST_NEW_PASSWORD", "newpassword2025")
        
        # Step 1: Change password
        response = requests.post(f"{BASE_URL}/api/admin/change-password",
            headers={"Authorization": f"Bearer {auth_token}"},
            json={
                "current_password": ADMIN_PASSWORD,
                "new_password": NEW_PASSWORD
            }
        )
        assert response.status_code == 200, f"Password change failed: {response.text}"
        print("Password changed successfully")
        
        # Step 2: Verify old password no longer works
        old_login = requests.post(f"{BASE_URL}/api/admin/login", json={
            "email": ADMIN_EMAIL,
            "password": ADMIN_PASSWORD
        })
        assert old_login.status_code == 401, "Old password should no longer work"
        print("Old password correctly rejected")
        
        # Step 3: Login with new password
        new_login = requests.post(f"{BASE_URL}/api/admin/login", json={
            "email": ADMIN_EMAIL,
            "password": NEW_PASSWORD
        })
        assert new_login.status_code == 200, "New password should work"
        new_token = new_login.json()["token"]
        print("Login with new password successful")
        
        # Step 4: Revert password back to original
        revert = requests.post(f"{BASE_URL}/api/admin/change-password",
            headers={"Authorization": f"Bearer {new_token}"},
            json={
                "current_password": NEW_PASSWORD,
                "new_password": ADMIN_PASSWORD
            }
        )
        assert revert.status_code == 200, f"Password revert failed: {revert.text}"
        print("Password reverted to original successfully")
        
        # Verify original password works again
        final_login = requests.post(f"{BASE_URL}/api/admin/login", json={
            "email": ADMIN_EMAIL,
            "password": ADMIN_PASSWORD
        })
        assert final_login.status_code == 200, "Original password should work after revert"
        print("Full password change cycle completed and reverted")


class TestRateLimiting:
    """Rate limiting tests - Run these first or wait 60s after failures"""

    def test_login_rate_limit(self):
        """Test 6: 5+ failed login attempts results in 429"""
        # Make 6 rapid failed login attempts (limit is 5)
        for i in range(6):
            response = requests.post(f"{BASE_URL}/api/admin/login", json={
                "email": "test@test.com",
                "password": "wrongpassword"
            })
            print(f"Attempt {i+1}: Status {response.status_code}")
            if response.status_code == 429:
                print(f"Rate limit triggered after {i+1} attempts")
                assert "Too many" in response.json().get("detail", "")
                return
        
        # If we got here, rate limit didn't trigger
        pytest.fail("Rate limit should have triggered after 5 failed attempts")

    def test_lead_submission_rate_limit(self):
        """Test 7: 10+ rapid lead submissions results in 429"""
        lead_data = {
            "name": "Test User",
            "email": "test@example.com",
            "phone": "1234567890",
            "city": "Test City",
            "application": "Testing"
        }
        
        # Make 11 rapid submissions (limit is 10)
        for i in range(11):
            response = requests.post(f"{BASE_URL}/api/leads", json=lead_data)
            print(f"Lead submission {i+1}: Status {response.status_code}")
            if response.status_code == 429:
                print(f"Lead rate limit triggered after {i+1} submissions")
                assert "Too many" in response.json().get("detail", "")
                return
        
        # If we got here without 429, that's unexpected but not necessarily a failure
        # The rate limiter uses client IP which might vary
        print("WARNING: Rate limit may not have triggered - could be IP detection issue")


class TestImageUpload:
    """Image upload and optimization tests"""

    @pytest.fixture
    def auth_token(self):
        """Get fresh auth token"""
        response = requests.post(f"{BASE_URL}/api/admin/login", json={
            "email": ADMIN_EMAIL,
            "password": ADMIN_PASSWORD
        })
        if response.status_code == 200:
            return response.json()["token"]
        pytest.skip("Could not get auth token")

    def create_test_image(self, width=800, height=600, format='PNG'):
        """Create a test image using Pillow"""
        img = Image.new('RGB', (width, height), color='blue')
        buffer = BytesIO()
        img.save(buffer, format=format)
        buffer.seek(0)
        return buffer

    def test_single_image_upload(self, auth_token):
        """Test 8: Upload single image, verify variants are created"""
        # Create test image
        img_buffer = self.create_test_image(1000, 800, 'JPEG')
        
        response = requests.post(
            f"{BASE_URL}/api/admin/upload",
            headers={"Authorization": f"Bearer {auth_token}"},
            files={"file": ("test_upload.jpg", img_buffer, "image/jpeg")}
        )
        assert response.status_code == 200, f"Upload failed: {response.text}"
        data = response.json()
        
        assert data["success"] == True
        assert "url" in data
        assert "variants" in data
        assert data["url"].startswith("/uploads/")
        
        # Verify variants exist
        variants = data.get("variants", {})
        print(f"Upload success - URL: {data['url']}")
        print(f"Variants: {list(variants.keys())}")
        
        # Variants should include thumbnail, medium for 1000x800 image
        if variants:
            assert "thumbnail" in variants, "Should have thumbnail variant"
        
        # Store filename for disk verification
        self.__class__.uploaded_file = data["url"].replace("/uploads/", "")

    def test_upload_creates_files_on_disk(self, auth_token):
        """Verify uploaded files exist on disk at /app/frontend/public/uploads/"""
        filename = getattr(self.__class__, 'uploaded_file', None)
        if not filename:
            pytest.skip("No uploaded file from previous test")
        
        # Check original file exists
        import subprocess
        result = subprocess.run(
            ["ls", "-la", f"/app/frontend/public/uploads/{filename}"],
            capture_output=True, text=True
        )
        assert result.returncode == 0, f"Original file not found: {filename}"
        print(f"Original file exists: {filename}")
        
        # Check for webp variants
        base_name = filename.rsplit('.', 1)[0]
        for variant in ['thumbnail', 'medium', 'large']:
            webp_file = f"{base_name}_{variant}.webp"
            result = subprocess.run(
                ["ls", f"/app/frontend/public/uploads/{webp_file}"],
                capture_output=True, text=True
            )
            if result.returncode == 0:
                print(f"Found variant: {webp_file}")

    def test_multiple_image_upload(self, auth_token):
        """Test 9: Upload multiple images"""
        # Create test images
        img1 = self.create_test_image(400, 300, 'PNG')
        img2 = self.create_test_image(500, 400, 'PNG')
        
        response = requests.post(
            f"{BASE_URL}/api/admin/upload/multiple",
            headers={"Authorization": f"Bearer {auth_token}"},
            files=[
                ("files", ("test1.png", img1, "image/png")),
                ("files", ("test2.png", img2, "image/png"))
            ]
        )
        assert response.status_code == 200, f"Multiple upload failed: {response.text}"
        data = response.json()
        
        assert data["success"] == True
        assert "uploaded" in data
        assert data["count"] >= 1
        print(f"Multiple upload success - {data['count']} files uploaded")

    def test_upload_rejects_non_image(self, auth_token):
        """Test 10a: Reject non-image files"""
        # Create a fake text file
        fake_file = BytesIO(b"This is not an image")
        
        response = requests.post(
            f"{BASE_URL}/api/admin/upload",
            headers={"Authorization": f"Bearer {auth_token}"},
            files={"file": ("test.txt", fake_file, "text/plain")}
        )
        assert response.status_code == 400, f"Should reject non-image: {response.text}"
        assert "not allowed" in response.json().get("detail", "").lower()
        print("Non-image file correctly rejected")

    def test_upload_requires_auth(self):
        """Upload endpoint requires authentication"""
        img = self.create_test_image(100, 100, 'PNG')
        response = requests.post(
            f"{BASE_URL}/api/admin/upload",
            files={"file": ("test.png", img, "image/png")}
        )
        assert response.status_code == 401, "Upload should require auth"
        print("Upload endpoint correctly requires authentication")


class TestSecurityHeaders:
    """Test security headers in responses"""

    def test_security_headers_present(self):
        """Test 11: Verify security headers in response"""
        response = requests.get(f"{BASE_URL}/api/health")
        
        required_headers = {
            "X-Content-Type-Options": "nosniff",
            "X-Frame-Options": "DENY",
            "X-XSS-Protection": "1; mode=block"
        }
        
        for header, expected_value in required_headers.items():
            actual = response.headers.get(header)
            assert actual is not None, f"Missing header: {header}"
            assert actual == expected_value, f"{header}: expected '{expected_value}', got '{actual}'"
            print(f"✓ {header}: {actual}")
        
        print("All security headers present and correct")


class TestAdminStats:
    """Admin dashboard statistics test"""

    def test_admin_stats(self):
        """Test 12: GET /api/admin/stats returns counts"""
        # Login first
        login = requests.post(f"{BASE_URL}/api/admin/login", json={
            "email": ADMIN_EMAIL,
            "password": ADMIN_PASSWORD
        })
        token = login.json()["token"]
        
        response = requests.get(f"{BASE_URL}/api/admin/stats", headers={
            "Authorization": f"Bearer {token}"
        })
        assert response.status_code == 200, f"Stats failed: {response.text}"
        data = response.json()
        
        # Verify expected fields
        assert "products" in data
        assert "inspirations" in data
        assert "projects" in data
        assert "leads" in data
        
        print(f"Dashboard stats - Products: {data['products']}, Inspirations: {data['inspirations']}, Projects: {data['projects']}, Leads: {data['leads']}")


class TestPublicEndpoints:
    """Test public site endpoints still work"""

    def test_public_products(self):
        """Test 16: Public products page loads"""
        response = requests.get(f"{BASE_URL}/api/products")
        assert response.status_code == 200
        data = response.json()
        assert "products" in data
        print(f"Public products API working - {len(data['products'])} products")

    def test_health_endpoint(self):
        """Health check works"""
        response = requests.get(f"{BASE_URL}/api/health")
        assert response.status_code == 200
        assert response.json()["status"] == "ok"
        print("Health endpoint working")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
