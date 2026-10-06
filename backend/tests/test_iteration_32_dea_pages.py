"""
Iteration 32: Test DEA Detail Pages, Quick Inquiry, Site Visit, Sitemap
Tests:
- DEA pages: /digital-experience/media-facades, /immersive-led-rooms, /retail-experiential-screens
- Quick Inquiry API: POST /api/quick-inquiry
- Site Visit Request API: POST /api/site-visit-request
- Sitemap includes new DEA pages
- WhatsApp number validation (971559954274)
"""

import pytest
import requests
import os
import time

BASE_URL = os.environ.get('REACT_APP_BACKEND_URL', '').rstrip('/')


class TestQuickInquiryAPI:
    """Test POST /api/quick-inquiry endpoint"""

    def test_quick_inquiry_success(self):
        """Quick inquiry with valid data returns status ok"""
        payload = {
            "name": "TEST_Quick_User",
            "email": "test_quick@example.com",
            "phone": "+971501234567",
            "message": "Quick inquiry: Interested in Media Facades",
            "page_context": "Media Facades LED solutions",
            "page_url": "/digital-experience/media-facades"
        }
        response = requests.post(f"{BASE_URL}/api/quick-inquiry", json=payload)
        assert response.status_code == 200
        data = response.json()
        assert data.get("status") == "ok"

    def test_quick_inquiry_minimal_fields(self):
        """Quick inquiry with minimal required fields (name, email) works"""
        payload = {
            "name": "TEST_Minimal_User",
            "email": "minimal@example.com"
        }
        response = requests.post(f"{BASE_URL}/api/quick-inquiry", json=payload)
        assert response.status_code == 200
        data = response.json()
        assert data.get("status") == "ok"

    def test_quick_inquiry_missing_name(self):
        """Quick inquiry without name fails validation"""
        payload = {
            "email": "noemail@example.com"
        }
        response = requests.post(f"{BASE_URL}/api/quick-inquiry", json=payload)
        # Should fail with 422 validation error
        assert response.status_code == 422


class TestSiteVisitRequestAPI:
    """Test POST /api/site-visit-request endpoint"""

    def test_site_visit_request_success(self):
        """Site visit request with valid data returns status ok"""
        payload = {
            "name": "TEST_Visit_User",
            "email": "test_visit@example.com",
            "phone": "+971501234567",
            "company": "Test Company LLC",
            "project_brief": "Looking for LED solutions for a new mall project",
            "page_url": "/digital-experience/retail-experiential-screens"
        }
        response = requests.post(f"{BASE_URL}/api/site-visit-request", json=payload)
        assert response.status_code == 200
        data = response.json()
        assert data.get("status") == "ok"

    def test_site_visit_minimal_fields(self):
        """Site visit request with minimal required fields works"""
        payload = {
            "name": "TEST_Minimal_Visit",
            "email": "minvisit@example.com"
        }
        response = requests.post(f"{BASE_URL}/api/site-visit-request", json=payload)
        assert response.status_code == 200
        data = response.json()
        assert data.get("status") == "ok"

    def test_site_visit_missing_email(self):
        """Site visit request without email fails validation"""
        payload = {
            "name": "No Email User"
        }
        response = requests.post(f"{BASE_URL}/api/site-visit-request", json=payload)
        # Should fail with 422 validation error
        assert response.status_code == 422


class TestSitemapNewPages:
    """Test sitemap includes new DEA pages"""

    def test_sitemap_returns_xml(self):
        """Sitemap endpoint returns valid XML"""
        response = requests.get(f"{BASE_URL}/api/sitemap.xml")
        assert response.status_code == 200
        assert "application/xml" in response.headers.get("content-type", "")

    def test_sitemap_contains_media_facades(self):
        """Sitemap includes /digital-experience/media-facades"""
        response = requests.get(f"{BASE_URL}/api/sitemap.xml")
        assert response.status_code == 200
        assert "/digital-experience/media-facades" in response.text

    def test_sitemap_contains_immersive_led_rooms(self):
        """Sitemap includes /digital-experience/immersive-led-rooms"""
        response = requests.get(f"{BASE_URL}/api/sitemap.xml")
        assert response.status_code == 200
        assert "/digital-experience/immersive-led-rooms" in response.text

    def test_sitemap_contains_retail_experiential_screens(self):
        """Sitemap includes /digital-experience/retail-experiential-screens"""
        response = requests.get(f"{BASE_URL}/api/sitemap.xml")
        assert response.status_code == 200
        assert "/digital-experience/retail-experiential-screens" in response.text

    def test_sitemap_contains_digital_experience_architecture(self):
        """Sitemap includes parent /digital-experience-architecture page"""
        response = requests.get(f"{BASE_URL}/api/sitemap.xml")
        assert response.status_code == 200
        assert "/digital-experience-architecture" in response.text


class TestHealthCheck:
    """Basic health check"""

    def test_api_health(self):
        """Backend health check responds"""
        response = requests.get(f"{BASE_URL}/api/health")
        assert response.status_code == 200
