"""
Iteration 35: Post CSS-Refactoring Regression Tests
Tests after global text-transform: uppercase was applied across the site
"""
import pytest
import requests
import os

BASE_URL = os.environ.get('REACT_APP_BACKEND_URL', '').rstrip('/')

class TestHealthAndBasics:
    """Basic health checks"""
    
    def test_health_endpoint(self):
        """API health check"""
        response = requests.get(f"{BASE_URL}/api/health", timeout=10)
        assert response.status_code == 200
        print("✓ Health endpoint returns 200")
    
    def test_products_endpoint(self):
        """Products API works"""
        response = requests.get(f"{BASE_URL}/api/products", timeout=10)
        assert response.status_code == 200
        data = response.json()
        # API returns {products: [...]}
        products = data.get("products", data) if isinstance(data, dict) else data
        assert isinstance(products, list)
        print(f"✓ Products endpoint returns {len(products)} products")
    
    def test_inspirations_endpoint(self):
        """Inspirations API works"""
        response = requests.get(f"{BASE_URL}/api/inspirations", timeout=10)
        assert response.status_code == 200
        data = response.json()
        # API returns {inspirations: [...]}
        items = data.get("inspirations", data) if isinstance(data, dict) else data
        assert isinstance(items, list)
        print(f"✓ Inspirations endpoint returns {len(items)} items")

class TestToolAPIs:
    """Tool-related API endpoints"""
    
    def test_project_planner_calculate(self):
        """Project planner calculation API"""
        payload = {
            "width": 4,
            "height": 2.5,
            "viewing_distance": 5,
            "content_type": "mixed",
            "environment": "indoor"
        }
        response = requests.post(
            f"{BASE_URL}/api/project-planner/calculate",
            json=payload,
            timeout=15
        )
        assert response.status_code == 200
        data = response.json()
        assert data.get("status") == "ok"
        # Check spec object contains recommended pitch
        spec = data.get("spec", {})
        assert "recommended_pitch" in spec, f"Missing recommended_pitch in spec: {spec.keys()}"
        pitch = spec.get("recommended_pitch")
        print(f"✓ Project planner returns pitch: {pitch}")
    
    def test_sitemap_xml(self):
        """Sitemap.xml is accessible"""
        response = requests.get(f"{BASE_URL}/api/sitemap.xml", timeout=10)
        assert response.status_code == 200
        assert "xml" in response.headers.get('Content-Type', '')
        assert "<urlset" in response.text
        print("✓ Sitemap.xml is valid XML")

class TestSpecpacks:
    """Specpacks download endpoints"""
    
    def test_specpacks_list(self):
        """List available specpacks"""
        response = requests.get(f"{BASE_URL}/api/specpacks", timeout=10)
        assert response.status_code == 200
        data = response.json()
        # API returns {packs: [...]}
        packs = data.get("packs", data) if isinstance(data, dict) else data
        assert isinstance(packs, list)
        print(f"✓ Specpacks endpoint returns {len(packs)} packs")

class TestChat:
    """AURA chat endpoint"""
    
    def test_chat_message(self):
        """Chat message endpoint works"""
        payload = {
            "session_id": "test_regression_35",
            "message": "What pixel pitch do you recommend for a hotel lobby?"
        }
        response = requests.post(
            f"{BASE_URL}/api/chat/message",
            json=payload,
            timeout=30  # AI responses can be slow
        )
        assert response.status_code == 200
        data = response.json()
        assert "response" in data or "error" not in data
        print("✓ Chat endpoint responds")

class TestAdminAuth:
    """Admin authentication"""
    
    def test_admin_login(self):
        """Admin login works"""
        payload = {
            "email": "admin@brightluxx.com",
            "password": os.environ.get("ADMIN_PASSWORD", "brightluxx2025")
        }
        response = requests.post(
            f"{BASE_URL}/api/admin/login",
            json=payload,
            timeout=10
        )
        assert response.status_code == 200
        data = response.json()
        assert "token" in data
        print("✓ Admin login returns token")
    
    def test_admin_invalid_login(self):
        """Invalid admin credentials return 401"""
        payload = {
            "email": "wrong@test.com",
            "password": "wrongpassword"
        }
        response = requests.post(
            f"{BASE_URL}/api/admin/login",
            json=payload,
            timeout=10
        )
        assert response.status_code == 401
        print("✓ Invalid credentials return 401")

class TestLeadsAndContact:
    """Lead capture and contact form"""
    
    def test_lead_submission(self):
        """Lead submission endpoint"""
        payload = {
            "name": "TEST_Regression35",
            "email": "regression35@test.com",
            "company": "Test Company",
            "phone": "+971555555555",
            "message": "Regression test lead"
        }
        response = requests.post(
            f"{BASE_URL}/api/leads",
            json=payload,
            timeout=10
        )
        # Either 200 or 201 is acceptable for lead creation
        assert response.status_code in [200, 201]
        print("✓ Lead submission works")

class TestDesignAssist:
    """Design assist submission"""
    
    def test_design_assist_request(self):
        """Design assist form submission via /request endpoint"""
        payload = {
            "name": "TEST_Regression35_Designer",
            "email": "designer35@test.com",
            "company": "Test Design Firm",
            "role": "Architect",  # required field
            "phone": "+971555555556",
            "project_type": "hospitality",
            "message": "Regression test design assist"
        }
        response = requests.post(
            f"{BASE_URL}/api/design-assist/request",
            json=payload,
            timeout=10
        )
        # 200 or 201 acceptable
        assert response.status_code in [200, 201]
        data = response.json()
        assert data.get("success") == True
        print("✓ Design assist request works")

if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
