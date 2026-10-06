"""
Iteration 30: Technology Selector Quiz Tests
Tests for the new Technology Selector feature that guides users through 5 questions
to recommend the right LED technology.
"""
import pytest
import requests
import os

BASE_URL = os.environ.get('REACT_APP_BACKEND_URL', '').rstrip('/')


class TestLeadsAPI:
    """Test /api/leads endpoint used by Technology Selector"""

    def test_leads_api_accepts_tech_selector_source(self):
        """Test that leads API accepts submissions from technology_selector"""
        response = requests.post(
            f"{BASE_URL}/api/leads",
            json={
                "name": "TEST_Tech_Selector_User",
                "email": "test.techselector.pytest@example.com",
                "company": "Test Company",
                "role": "Architect",
                "application": "Tech Selector: MicroLED (hospitality)",
                "source": "technology_selector"
            },
            headers={"Content-Type": "application/json"}
        )
        assert response.status_code == 200
        data = response.json()
        assert data.get("success") is True
        assert "leadId" in data
        print(f"Lead created with ID: {data['leadId']}")

    def test_leads_api_requires_email(self):
        """Test that leads API validates required fields"""
        response = requests.post(
            f"{BASE_URL}/api/leads",
            json={
                "name": "TEST_Missing_Email",
                "company": "Test Company",
                "role": "Architect",
            },
            headers={"Content-Type": "application/json"}
        )
        assert response.status_code == 422  # Validation error
        print("Validation correctly rejects missing email")

    def test_leads_api_with_various_roles(self):
        """Test leads API with different role values"""
        roles = ["Architect", "Interior Designer", "AV Consultant", "Contractor", "Project Manager", "Other"]
        for role in roles:
            response = requests.post(
                f"{BASE_URL}/api/leads",
                json={
                    "name": f"TEST_Role_{role}",
                    "email": f"test.role.{role.lower().replace(' ', '')}@example.com",
                    "company": "Test Company",
                    "role": role,
                    "application": f"Tech Selector test with role: {role}"
                },
                headers={"Content-Type": "application/json"}
            )
            assert response.status_code == 200, f"Failed for role: {role}"
        print(f"All {len(roles)} role values accepted")


class TestSitemap:
    """Test sitemap includes technology-selector"""

    def test_sitemap_returns_xml(self):
        """Test that sitemap returns valid XML"""
        response = requests.get(f"{BASE_URL}/api/sitemap.xml")
        assert response.status_code == 200
        assert "application/xml" in response.headers.get("content-type", "")
        print("Sitemap returns valid XML")

    def test_sitemap_includes_technology_selector(self):
        """Test that sitemap includes /technology-selector URL"""
        response = requests.get(f"{BASE_URL}/api/sitemap.xml")
        assert response.status_code == 200
        assert "/technology-selector" in response.text
        print("Sitemap includes /technology-selector")

    def test_sitemap_includes_design_assist(self):
        """Test that sitemap still includes /design-assist (regression)"""
        response = requests.get(f"{BASE_URL}/api/sitemap.xml")
        assert response.status_code == 200
        assert "/design-assist" in response.text
        print("Sitemap includes /design-assist (regression passed)")


class TestHealthAndBasicEndpoints:
    """Basic health and regression tests"""

    def test_health_endpoint(self):
        """Test health endpoint is responding"""
        response = requests.get(f"{BASE_URL}/api/health")
        assert response.status_code == 200
        print("Health endpoint is up")

    def test_products_endpoint(self):
        """Test products endpoint (regression)"""
        response = requests.get(f"{BASE_URL}/api/products")
        assert response.status_code == 200
        data = response.json()
        # Products endpoint returns {products: [...]}
        if isinstance(data, dict) and "products" in data:
            products = data["products"]
            assert isinstance(products, list)
            print(f"Products endpoint returns {len(products)} products")
        else:
            assert isinstance(data, list)
            print(f"Products endpoint returns {len(data)} products")

    def test_inspirations_endpoint(self):
        """Test inspirations endpoint (regression)"""
        response = requests.get(f"{BASE_URL}/api/inspirations")
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list) or isinstance(data, dict)
        print("Inspirations endpoint working")


class TestDesignAssistRegression:
    """Regression tests for Design Assist feature"""

    def test_design_assist_request_endpoint(self):
        """Test Design Assist request endpoint still works"""
        response = requests.post(
            f"{BASE_URL}/api/design-assist/request",
            json={
                "name": "TEST_DA_Regression",
                "email": "test.da.regression@example.com",
                "company": "Regression Test Corp",
                "role": "Architect",
                "project_type": "Hotel Lobby",
                "project_stage": "Schematic Design",
                "message": "Regression test for iteration 30"
            },
            headers={"Content-Type": "application/json"}
        )
        assert response.status_code == 200
        data = response.json()
        assert data.get("success") is True
        print("Design Assist request endpoint working (regression passed)")


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
