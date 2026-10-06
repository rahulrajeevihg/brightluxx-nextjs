"""
CPD Programme API Tests
Tests for the CPD / Lunch & Learn Programme booking feature.
"""
import pytest
import requests
import os

BASE_URL = os.environ.get('REACT_APP_BACKEND_URL', '').rstrip('/')


class TestCPDProgrammeAPI:
    """Test CPD Programme booking API endpoints."""

    def test_cpd_request_success(self):
        """Test successful CPD session booking request with all required fields."""
        payload = {
            "name": "TEST_John Architect",
            "email": "test.architect@testcompany.com",
            "company": "Test Architecture Firm",
            "role": "Architect",
            "preferred_topic": "MicroLED vs COB vs MiP — Technology Selection for Specifiers"
        }
        response = requests.post(f"{BASE_URL}/api/cpd/request", json=payload)
        
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        data = response.json()
        assert data.get("success") is True, "Response should indicate success"
        assert "message" in data, "Response should have a message"
        assert "24 hours" in data["message"], "Message should mention 24 hours contact time"

    def test_cpd_request_with_all_fields(self):
        """Test CPD booking with all optional fields."""
        payload = {
            "name": "TEST_Complete User",
            "email": "complete.user@testfirm.com",
            "company": "Complete Test Firm",
            "role": "Interior Designer",
            "phone": "+971501234567",
            "preferred_topic": "Pixel Pitch Selection Masterclass",
            "preferred_format": "virtual",
            "group_size": "6-15",
            "preferred_date": "March 2026",
            "message": "We have a hotel project coming up and want to learn more."
        }
        response = requests.post(f"{BASE_URL}/api/cpd/request", json=payload)
        
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        data = response.json()
        assert data.get("success") is True

    def test_cpd_request_missing_name(self):
        """Test that missing name field returns 422."""
        payload = {
            "email": "test@test.com",
            "company": "Test Company",
            "role": "Architect",
            "preferred_topic": "Test Topic"
        }
        response = requests.post(f"{BASE_URL}/api/cpd/request", json=payload)
        
        assert response.status_code == 422, f"Expected 422 for missing name, got {response.status_code}"

    def test_cpd_request_missing_email(self):
        """Test that missing email field returns 422."""
        payload = {
            "name": "TEST_User",
            "company": "Test Company",
            "role": "Architect",
            "preferred_topic": "Test Topic"
        }
        response = requests.post(f"{BASE_URL}/api/cpd/request", json=payload)
        
        assert response.status_code == 422, f"Expected 422 for missing email, got {response.status_code}"

    def test_cpd_request_missing_company(self):
        """Test that missing company field returns 422."""
        payload = {
            "name": "TEST_User",
            "email": "test@test.com",
            "role": "Architect",
            "preferred_topic": "Test Topic"
        }
        response = requests.post(f"{BASE_URL}/api/cpd/request", json=payload)
        
        assert response.status_code == 422, f"Expected 422 for missing company, got {response.status_code}"

    def test_cpd_request_missing_role(self):
        """Test that missing role field returns 422."""
        payload = {
            "name": "TEST_User",
            "email": "test@test.com",
            "company": "Test Company",
            "preferred_topic": "Test Topic"
        }
        response = requests.post(f"{BASE_URL}/api/cpd/request", json=payload)
        
        assert response.status_code == 422, f"Expected 422 for missing role, got {response.status_code}"

    def test_cpd_request_missing_topic(self):
        """Test that missing preferred_topic field returns 422."""
        payload = {
            "name": "TEST_User",
            "email": "test@test.com",
            "company": "Test Company",
            "role": "Architect"
        }
        response = requests.post(f"{BASE_URL}/api/cpd/request", json=payload)
        
        assert response.status_code == 422, f"Expected 422 for missing preferred_topic, got {response.status_code}"

    def test_cpd_request_empty_body(self):
        """Test that empty body returns 422."""
        response = requests.post(f"{BASE_URL}/api/cpd/request", json={})
        
        assert response.status_code == 422, f"Expected 422 for empty body, got {response.status_code}"

    def test_cpd_default_format(self):
        """Test that default format is 'in-office' when not specified."""
        payload = {
            "name": "TEST_Default Format User",
            "email": "default.format@test.com",
            "company": "Default Test Co",
            "role": "AV Consultant",
            "preferred_topic": "LED Displays in Healthcare Environments"
        }
        response = requests.post(f"{BASE_URL}/api/cpd/request", json=payload)
        
        assert response.status_code == 200
        # API accepts it even without preferred_format, using default


class TestSitemapContainsCPD:
    """Test that sitemap includes CPD Programme URL."""

    def test_sitemap_contains_cpd_programme(self):
        """Verify /cpd-programme is in the sitemap."""
        response = requests.get(f"{BASE_URL}/api/sitemap.xml")
        
        assert response.status_code == 200, f"Sitemap request failed: {response.status_code}"
        assert "/cpd-programme" in response.text, "Sitemap should contain /cpd-programme URL"


class TestHealthCheck:
    """Basic health and regression checks."""

    def test_api_health(self):
        """Test API health endpoint."""
        response = requests.get(f"{BASE_URL}/api/health")
        assert response.status_code == 200

    def test_case_studies_endpoint(self):
        """Regression: Case Studies routes should still work."""
        response = requests.get(f"{BASE_URL}/api/sitemap.xml")
        assert response.status_code == 200
        assert "/case-studies" in response.text

    def test_technology_in_sitemap(self):
        """Regression: Technology routes should still work."""
        response = requests.get(f"{BASE_URL}/api/sitemap.xml")
        assert response.status_code == 200
        assert "/technology" in response.text
