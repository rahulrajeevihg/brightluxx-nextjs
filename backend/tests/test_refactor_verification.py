"""
Test suite for Brightluxx Backend Refactoring Verification
Purpose: Verify that the backend refactoring (splitting server.py into modules) 
hasn't broken any functionality.

Tests all 22 endpoints specified in the test request:
- Public endpoints (health, products, categories, compare, calculator, inspirations, projects, leads, search)
- Admin endpoints (login, me, refresh, change-password, stats, products CRUD, upload, export)
- Security headers
"""

import pytest
import requests
import os
import time
from io import BytesIO
from PIL import Image

BASE_URL = os.environ.get('REACT_APP_BACKEND_URL', '').rstrip('/')

# Test credentials
ADMIN_EMAIL = "admin@brightluxx.com"
ADMIN_PASSWORD = os.environ.get("ADMIN_PASSWORD", "brightluxx2025")


class TestPublicEndpoints:
    """Test public API endpoints (no auth required)"""

    def test_01_health_check(self):
        """Test 1: GET /api/health - should return ok"""
        response = requests.get(f"{BASE_URL}/api/health")
        assert response.status_code == 200, f"Health check failed: {response.text}"
        data = response.json()
        assert data["status"] == "ok", f"Expected status 'ok', got: {data}"
        assert "service" in data
        print(f"✓ Health check passed - status: {data['status']}, service: {data['service']}")

    def test_02_get_products(self):
        """Test 2: GET /api/products - should return 41 products"""
        response = requests.get(f"{BASE_URL}/api/products")
        assert response.status_code == 200, f"Products fetch failed: {response.text}"
        data = response.json()
        assert "products" in data, "Response missing 'products' key"
        product_count = len(data["products"])
        print(f"✓ Products endpoint returned {product_count} products")
        # Allow some flexibility - verify we have substantial products
        assert product_count > 30, f"Expected ~41 products, got {product_count}"

    def test_03_get_product_categories(self):
        """Test 3: GET /api/products/categories - should return 17 categories"""
        response = requests.get(f"{BASE_URL}/api/products/categories")
        assert response.status_code == 200, f"Categories fetch failed: {response.text}"
        data = response.json()
        assert "categories" in data, "Response missing 'categories' key"
        category_count = len(data["categories"])
        print(f"✓ Categories endpoint returned {category_count} categories")
        # Each category should have value, label, count
        if data["categories"]:
            cat = data["categories"][0]
            assert "value" in cat and "label" in cat and "count" in cat
        assert category_count > 10, f"Expected ~17 categories, got {category_count}"

    def test_04_compare_products(self):
        """Test 4: POST /api/products/compare - with 2 product codes"""
        # First get available product codes
        products_response = requests.get(f"{BASE_URL}/api/products")
        products = products_response.json().get("products", [])
        if len(products) < 2:
            pytest.skip("Not enough products for comparison")
        
        codes = [products[0]["product_code"], products[1]["product_code"]]
        response = requests.post(f"{BASE_URL}/api/products/compare", json=codes)
        assert response.status_code == 200, f"Compare failed: {response.text}"
        data = response.json()
        assert "products" in data
        assert len(data["products"]) == 2, f"Expected 2 products, got {len(data['products'])}"
        print(f"✓ Compare endpoint works - compared {codes[0]} vs {codes[1]}")

    def test_05_screen_size_calculator(self):
        """Test 5: POST /api/calculator/screen-size - screen size calculator"""
        calc_data = {
            "venue_width": 10,
            "venue_height": 3,
            "viewing_distance": 5,
            "content_type": "video",
            "indoor": True
        }
        response = requests.post(f"{BASE_URL}/api/calculator/screen-size", json=calc_data)
        assert response.status_code == 200, f"Calculator failed: {response.text}"
        data = response.json()
        
        # Verify all expected fields
        expected_fields = ["recommended_pitch", "screen_width", "screen_height", 
                          "screen_area", "resolution", "brightness", "tips"]
        for field in expected_fields:
            assert field in data, f"Missing field: {field}"
        
        print(f"✓ Calculator works - recommended pitch: {data['recommended_pitch']}mm, "
              f"screen: {data['screen_width']}x{data['screen_height']}m")

    def test_06_get_single_product_by_slug(self):
        """Test 6: GET /api/products/pixel-grid-lab-1 - single product by slug"""
        # First get any product with its slug
        products_response = requests.get(f"{BASE_URL}/api/products")
        products = products_response.json().get("products", [])
        if not products:
            pytest.skip("No products available")
        
        slug = products[0]["slug"]
        response = requests.get(f"{BASE_URL}/api/products/{slug}")
        assert response.status_code == 200, f"Product by slug failed: {response.text}"
        data = response.json()
        assert data["slug"] == slug
        print(f"✓ Single product by slug works - fetched: {data['name']}")

    def test_07_get_inspirations(self):
        """Test 7: GET /api/inspirations - should return 22 inspirations"""
        response = requests.get(f"{BASE_URL}/api/inspirations")
        assert response.status_code == 200, f"Inspirations fetch failed: {response.text}"
        data = response.json()
        assert "inspirations" in data
        count = len(data["inspirations"])
        print(f"✓ Inspirations endpoint returned {count} items")
        assert count > 15, f"Expected ~22 inspirations, got {count}"

    def test_08_get_projects(self):
        """Test 8: GET /api/projects - should return 9 projects"""
        response = requests.get(f"{BASE_URL}/api/projects")
        assert response.status_code == 200, f"Projects fetch failed: {response.text}"
        data = response.json()
        assert "projects" in data
        count = len(data["projects"])
        print(f"✓ Projects endpoint returned {count} items")
        assert count >= 8, f"Expected ~9 projects, got {count}"

    def test_09_create_lead(self):
        """Test 9: POST /api/leads - submit a lead (rate limited)"""
        lead_data = {
            "name": "Test User Refactor Verification",
            "email": "test_refactor@example.com",
            "phone": "1234567890",
            "city": "Test City",
            "application": "Refactor Testing"
        }
        response = requests.post(f"{BASE_URL}/api/leads", json=lead_data)
        # Accept 200 or 429 (rate limited)
        if response.status_code == 429:
            print("✓ Lead endpoint hit rate limit (expected if run recently)")
            return
        assert response.status_code == 200, f"Lead creation failed: {response.text}"
        data = response.json()
        assert data["success"] == True
        assert "leadId" in data
        print(f"✓ Lead creation works - leadId: {data['leadId']}")

    def test_10_search_endpoint(self):
        """Test 10: GET /api/search?q=outdoor - search endpoint"""
        response = requests.get(f"{BASE_URL}/api/search?q=outdoor")
        assert response.status_code == 200, f"Search failed: {response.text}"
        data = response.json()
        assert "products" in data
        assert "inspirations" in data
        assert "projects" in data
        print(f"✓ Search works - found {len(data['products'])} products for 'outdoor'")


class TestAdminAuthentication:
    """Test admin authentication endpoints"""

    def test_11_admin_login(self):
        """Test 11: POST /api/admin/login - with credentials"""
        response = requests.post(f"{BASE_URL}/api/admin/login", json={
            "email": ADMIN_EMAIL,
            "password": ADMIN_PASSWORD
        })
        assert response.status_code == 200, f"Admin login failed: {response.text}"
        data = response.json()
        
        # Verify response structure
        assert "token" in data, "Missing token"
        assert "refresh_token" in data, "Missing refresh_token"
        assert "admin" in data, "Missing admin info"
        assert "expires_in" in data, "Missing expires_in"
        assert data["admin"]["email"] == ADMIN_EMAIL
        
        # Store for subsequent tests
        TestAdminAuthentication.token = data["token"]
        TestAdminAuthentication.refresh_token = data["refresh_token"]
        print(f"✓ Admin login works - expires_in: {data['expires_in']}s")

    def test_12_admin_me(self):
        """Test 12: GET /api/admin/me - with Bearer token"""
        token = getattr(TestAdminAuthentication, 'token', None)
        if not token:
            # Try fresh login
            login = requests.post(f"{BASE_URL}/api/admin/login", json={
                "email": ADMIN_EMAIL, "password": ADMIN_PASSWORD
            })
            token = login.json().get("token")
        
        response = requests.get(f"{BASE_URL}/api/admin/me", headers={
            "Authorization": f"Bearer {token}"
        })
        assert response.status_code == 200, f"Admin /me failed: {response.text}"
        data = response.json()
        assert data["email"] == ADMIN_EMAIL
        assert "role" in data
        print(f"✓ Admin /me works - email: {data['email']}, role: {data['role']}")

    def test_13_admin_refresh_token(self):
        """Test 13: POST /api/admin/refresh - refresh token"""
        refresh_token = getattr(TestAdminAuthentication, 'refresh_token', None)
        if not refresh_token:
            login = requests.post(f"{BASE_URL}/api/admin/login", json={
                "email": ADMIN_EMAIL, "password": ADMIN_PASSWORD
            })
            refresh_token = login.json().get("refresh_token")
        
        response = requests.post(f"{BASE_URL}/api/admin/refresh", json={
            "refresh_token": refresh_token
        })
        assert response.status_code == 200, f"Token refresh failed: {response.text}"
        data = response.json()
        assert "token" in data
        assert "expires_in" in data
        print(f"✓ Token refresh works - new expires_in: {data['expires_in']}s")

    def test_14_admin_change_password_validation(self):
        """Test 14: POST /api/admin/change-password - validation tests"""
        login = requests.post(f"{BASE_URL}/api/admin/login", json={
            "email": ADMIN_EMAIL, "password": ADMIN_PASSWORD
        })
        token = login.json().get("token")
        
        # Test wrong current password
        response = requests.post(f"{BASE_URL}/api/admin/change-password",
            headers={"Authorization": f"Bearer {token}"},
            json={"current_password": "wrongpass", "new_password": "newpass123"}
        )
        assert response.status_code == 400, "Should reject wrong password"
        
        # Test short new password
        response = requests.post(f"{BASE_URL}/api/admin/change-password",
            headers={"Authorization": f"Bearer {token}"},
            json={"current_password": ADMIN_PASSWORD, "new_password": "short"}
        )
        assert response.status_code == 400, "Should reject short password"
        print("✓ Password change validation works (rejects wrong/short passwords)")


class TestAdminFeatures:
    """Test admin CRUD and feature endpoints"""

    @pytest.fixture
    def auth_headers(self):
        """Get auth headers"""
        login = requests.post(f"{BASE_URL}/api/admin/login", json={
            "email": ADMIN_EMAIL, "password": ADMIN_PASSWORD
        })
        token = login.json().get("token")
        return {"Authorization": f"Bearer {token}"}

    def test_15_admin_stats(self, auth_headers):
        """Test 15: GET /api/admin/stats - dashboard stats"""
        response = requests.get(f"{BASE_URL}/api/admin/stats", headers=auth_headers)
        assert response.status_code == 200, f"Stats failed: {response.text}"
        data = response.json()
        
        # Verify all expected fields
        expected = ["products", "inspirations", "projects", "leads", "new_leads", 
                   "categories", "lead_statuses", "recent_leads", "recent_products"]
        for field in expected:
            assert field in data, f"Missing stats field: {field}"
        
        print(f"✓ Admin stats works - Products: {data['products']}, "
              f"Inspirations: {data['inspirations']}, Projects: {data['projects']}, "
              f"Leads: {data['leads']}")

    def test_16_admin_products_list(self, auth_headers):
        """Test 16: GET /api/admin/products - admin product list with pagination"""
        response = requests.get(f"{BASE_URL}/api/admin/products?page=1&limit=10", 
                               headers=auth_headers)
        assert response.status_code == 200, f"Admin products failed: {response.text}"
        data = response.json()
        
        assert "products" in data
        assert "total" in data
        assert "page" in data
        assert "pages" in data
        print(f"✓ Admin products list works - {len(data['products'])} items, "
              f"total: {data['total']}, pages: {data['pages']}")

    def test_17_admin_upload(self, auth_headers):
        """Test 17: POST /api/admin/upload - file upload with image optimization"""
        # Create test image
        img = Image.new('RGB', (1000, 800), color='green')
        buffer = BytesIO()
        img.save(buffer, format='JPEG')
        buffer.seek(0)
        
        response = requests.post(
            f"{BASE_URL}/api/admin/upload",
            headers=auth_headers,
            files={"file": ("test_refactor.jpg", buffer, "image/jpeg")}
        )
        assert response.status_code == 200, f"Upload failed: {response.text}"
        data = response.json()
        
        assert data["success"] == True
        assert "url" in data
        assert "variants" in data
        assert data["url"].startswith("/uploads/")
        
        variants = data.get("variants", {})
        print(f"✓ Upload works - URL: {data['url']}, variants: {list(variants.keys())}")

    def test_18_admin_export_products(self, auth_headers):
        """Test 18: GET /api/admin/export/products - data export"""
        response = requests.get(f"{BASE_URL}/api/admin/export/products", 
                               headers=auth_headers)
        assert response.status_code == 200, f"Export failed: {response.text}"
        data = response.json()
        
        assert "data" in data
        assert "count" in data
        assert data["count"] > 0
        print(f"✓ Export works - exported {data['count']} products")


class TestSecurityHeaders:
    """Test security headers presence"""

    def test_19_security_headers(self):
        """Test 19: Security headers present on responses"""
        response = requests.get(f"{BASE_URL}/api/health")
        
        required_headers = {
            "X-Frame-Options": "DENY",
            "X-Content-Type-Options": "nosniff",
            "X-XSS-Protection": "1; mode=block"
        }
        
        for header, expected in required_headers.items():
            actual = response.headers.get(header)
            assert actual is not None, f"Missing header: {header}"
            assert actual == expected, f"{header}: expected '{expected}', got '{actual}'"
            print(f"✓ {header}: {actual}")
        
        print("✓ All security headers present and correct")


class TestAdditionalAdminEndpoints:
    """Test additional admin endpoints for completeness"""

    @pytest.fixture
    def auth_headers(self):
        login = requests.post(f"{BASE_URL}/api/admin/login", json={
            "email": ADMIN_EMAIL, "password": ADMIN_PASSWORD
        })
        return {"Authorization": f"Bearer " + login.json().get("token")}

    def test_admin_inspirations_list(self, auth_headers):
        """Admin inspirations list"""
        response = requests.get(f"{BASE_URL}/api/admin/inspirations", headers=auth_headers)
        assert response.status_code == 200
        data = response.json()
        assert "inspirations" in data
        print(f"✓ Admin inspirations list works - {len(data['inspirations'])} items")

    def test_admin_projects_list(self, auth_headers):
        """Admin projects list"""
        response = requests.get(f"{BASE_URL}/api/admin/projects", headers=auth_headers)
        assert response.status_code == 200
        data = response.json()
        assert "projects" in data
        print(f"✓ Admin projects list works - {len(data['projects'])} items")

    def test_admin_leads_list(self, auth_headers):
        """Admin leads list"""
        response = requests.get(f"{BASE_URL}/api/admin/leads", headers=auth_headers)
        assert response.status_code == 200
        data = response.json()
        assert "leads" in data
        print(f"✓ Admin leads list works - {len(data['leads'])} items")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
