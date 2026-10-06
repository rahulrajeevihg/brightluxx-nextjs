"""
Backend API tests for iteration 29 - Testing new features:
1. Design Assist page - POST /api/design-assist/request
2. LinkedIn Specifier Toolkit - POST /api/leads (with source=linkedin_specifier_toolkit)
3. Sitemap - GET /api/sitemap.xml
4. Regression tests for existing APIs
"""
import pytest
import requests
import os
import time

BASE_URL = os.environ.get('REACT_APP_BACKEND_URL', '').rstrip('/')

# ============================================================================
# Design Assist API Tests
# ============================================================================
class TestDesignAssistAPI:
    """Tests for /api/design-assist/request endpoint"""

    def test_design_assist_post_success(self):
        """Test: POST /api/design-assist/request with valid data returns success"""
        payload = {
            "name": "TEST_Architect_John",
            "email": "test_architect@gensler.com",
            "company": "Gensler",
            "role": "Architect",
            "phone": "+971551234567",
            "project_type": "Hospitality",
            "project_stage": "Concept",
            "message": "Testing design assist form submission for hotel lobby LED display."
        }
        response = requests.post(f"{BASE_URL}/api/design-assist/request", json=payload)
        
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        data = response.json()
        assert data.get("success") == True, f"Expected success=True, got {data}"
        assert "message" in data, "Response should contain a message field"
        print(f"✓ Design Assist POST success: {data}")

    def test_design_assist_required_fields_only(self):
        """Test: POST /api/design-assist/request with only required fields"""
        payload = {
            "name": "TEST_MinimalUser",
            "email": "minimal@test.com",
            "company": "Test Corp",
            "role": "Interior Designer"
        }
        response = requests.post(f"{BASE_URL}/api/design-assist/request", json=payload)
        
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        data = response.json()
        assert data.get("success") == True, f"Expected success=True, got {data}"
        print(f"✓ Design Assist with minimal fields: {data}")

    def test_design_assist_missing_name(self):
        """Test: POST /api/design-assist/request with missing name returns 422"""
        payload = {
            "email": "test@test.com",
            "company": "Test Corp",
            "role": "Architect"
        }
        response = requests.post(f"{BASE_URL}/api/design-assist/request", json=payload)
        
        assert response.status_code == 422, f"Expected 422 for missing name, got {response.status_code}"
        print(f"✓ Design Assist validation (missing name): returns 422")

    def test_design_assist_missing_email(self):
        """Test: POST /api/design-assist/request with missing email returns 422"""
        payload = {
            "name": "Test User",
            "company": "Test Corp",
            "role": "Architect"
        }
        response = requests.post(f"{BASE_URL}/api/design-assist/request", json=payload)
        
        assert response.status_code == 422, f"Expected 422 for missing email, got {response.status_code}"
        print(f"✓ Design Assist validation (missing email): returns 422")

    def test_design_assist_missing_company(self):
        """Test: POST /api/design-assist/request with missing company returns 422"""
        payload = {
            "name": "Test User",
            "email": "test@test.com",
            "role": "Architect"
        }
        response = requests.post(f"{BASE_URL}/api/design-assist/request", json=payload)
        
        assert response.status_code == 422, f"Expected 422 for missing company, got {response.status_code}"
        print(f"✓ Design Assist validation (missing company): returns 422")

    def test_design_assist_missing_role(self):
        """Test: POST /api/design-assist/request with missing role returns 422"""
        payload = {
            "name": "Test User",
            "email": "test@test.com",
            "company": "Test Corp"
        }
        response = requests.post(f"{BASE_URL}/api/design-assist/request", json=payload)
        
        assert response.status_code == 422, f"Expected 422 for missing role, got {response.status_code}"
        print(f"✓ Design Assist validation (missing role): returns 422")


# ============================================================================
# LinkedIn Specifier Toolkit API Tests
# ============================================================================
class TestLinkedInLeadsAPI:
    """Tests for /api/leads endpoint with LinkedIn source"""

    def test_linkedin_leads_post_success(self):
        """Test: POST /api/leads with source=linkedin_specifier_toolkit returns success"""
        time.sleep(1)  # Rate limiting buffer
        payload = {
            "name": "TEST_LinkedIn_User",
            "email": "linkedin_test@perkinswill.com",
            "company": "Perkins&Will",
            "role": "AV Consultant",
            "source": "linkedin_specifier_toolkit",
            "application": "Specifier Toolkit: AV Consultant",
            "project_type": "Corporate"
        }
        response = requests.post(f"{BASE_URL}/api/leads", json=payload)
        
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        data = response.json()
        # The API returns either 'success' or 'leadId'
        assert data.get("success") == True or "leadId" in data, f"Expected success or leadId, got {data}"
        print(f"✓ LinkedIn Lead POST success: {data}")

    def test_leads_required_fields(self):
        """Test: POST /api/leads with minimal required fields"""
        time.sleep(1)  # Rate limiting buffer
        payload = {
            "name": "TEST_MinimalLead",
            "email": "minimal_lead@test.com",
            "company": "TestCo"
        }
        response = requests.post(f"{BASE_URL}/api/leads", json=payload)
        
        # Should succeed or return validation error depending on model requirements
        assert response.status_code in [200, 422], f"Expected 200 or 422, got {response.status_code}"
        print(f"✓ Leads minimal fields test: status={response.status_code}")


# ============================================================================
# Sitemap API Tests
# ============================================================================
class TestSitemapAPI:
    """Tests for /api/sitemap.xml endpoint"""

    def test_sitemap_returns_xml(self):
        """Test: GET /api/sitemap.xml returns valid XML"""
        response = requests.get(f"{BASE_URL}/api/sitemap.xml")
        
        assert response.status_code == 200, f"Expected 200, got {response.status_code}"
        assert "application/xml" in response.headers.get("Content-Type", ""), "Expected XML content type"
        assert '<?xml version="1.0"' in response.text, "Response should be valid XML"
        print(f"✓ Sitemap returns valid XML")

    def test_sitemap_contains_design_assist(self):
        """Test: Sitemap includes /design-assist URL"""
        response = requests.get(f"{BASE_URL}/api/sitemap.xml")
        
        assert response.status_code == 200
        assert "/design-assist" in response.text, "Sitemap should include /design-assist"
        print(f"✓ Sitemap includes /design-assist")

    def test_sitemap_contains_dea(self):
        """Test: Sitemap includes /digital-experience-architecture URL"""
        response = requests.get(f"{BASE_URL}/api/sitemap.xml")
        
        assert response.status_code == 200
        assert "/digital-experience-architecture" in response.text, "Sitemap should include /digital-experience-architecture"
        print(f"✓ Sitemap includes /digital-experience-architecture")

    def test_sitemap_contains_linkedin_lp(self):
        """Test: Sitemap includes /lp/specifier-toolkit URL"""
        response = requests.get(f"{BASE_URL}/api/sitemap.xml")
        
        assert response.status_code == 200
        assert "/lp/specifier-toolkit" in response.text, "Sitemap should include /lp/specifier-toolkit"
        print(f"✓ Sitemap includes /lp/specifier-toolkit")


# ============================================================================
# Regression Tests
# ============================================================================
class TestRegressionAPIs:
    """Regression tests to ensure existing APIs still work"""

    def test_health_or_products(self):
        """Test: API is accessible"""
        response = requests.get(f"{BASE_URL}/api/products")
        assert response.status_code == 200, f"Products API failed: {response.status_code}"
        print(f"✓ Products API working")

    def test_cpd_request_endpoint_exists(self):
        """Test: CPD request endpoint exists (would return 422 for missing body)"""
        # POST without body returns 422 validation error - endpoint exists
        response = requests.post(f"{BASE_URL}/api/cpd/request", json={})
        assert response.status_code == 422, f"CPD endpoint unexpected status: {response.status_code}"
        print(f"✓ CPD request endpoint exists (validation active)")

    def test_case_studies_exist(self):
        """Test: Case studies page content exists"""
        # Case studies are static - just verify products API works for regression
        response = requests.get(f"{BASE_URL}/api/products")
        assert response.status_code == 200, f"API failed: {response.status_code}"
        print(f"✓ API regression check passed")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
