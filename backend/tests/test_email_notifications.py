"""
Test Email Notification Feature - Gmail SMTP Integration
Tests for:
1. POST /api/specpacks/{pack_id}/download - captures lead and triggers email
2. POST /api/leads - contact form submission triggers email
3. Email service graceful failure handling
"""
import pytest
import requests
import os
from unittest.mock import patch, MagicMock
import sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

BASE_URL = os.environ.get('REACT_APP_BACKEND_URL', '').rstrip('/')

class TestSpecPackDownloadEndpoint:
    """Tests for POST /api/specpacks/{pack_id}/download - Lead capture + email notification"""
    
    def test_specpack_download_returns_download_url(self):
        """Test that spec pack download captures lead and returns download_url"""
        payload = {
            "name": "TEST_Email_John Doe",
            "email": "test_email_john@example.com",
            "company": "TEST Corp",
            "role": "architect"
        }
        response = requests.post(
            f"{BASE_URL}/api/specpacks/pixel-pitch/download",
            json=payload
        )
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        data = response.json()
        
        # Validate response structure
        assert "download_url" in data, "Response should contain download_url"
        assert data["download_url"] == "/api/specpacks/pixel-pitch/file"
        print(f"✓ Spec pack download returned download_url: {data['download_url']}")
    
    def test_specpack_download_with_all_fields(self):
        """Test spec pack download with all optional fields populated"""
        payload = {
            "name": "TEST_Email_Jane Smith",
            "email": "test_email_jane@example.com",
            "company": "ACME Industries",
            "role": "designer",
            "pack_id": "pixel-pitch"
        }
        response = requests.post(
            f"{BASE_URL}/api/specpacks/pixel-pitch/download",
            json=payload
        )
        assert response.status_code == 200
        data = response.json()
        assert "download_url" in data
        print(f"✓ Spec pack download with all fields successful")
    
    def test_specpack_download_minimal_fields(self):
        """Test spec pack download with only required email field"""
        payload = {
            "email": "test_email_minimal@example.com",
            "name": ""
        }
        response = requests.post(
            f"{BASE_URL}/api/specpacks/cob-mip-smd/download",
            json=payload
        )
        assert response.status_code == 200
        data = response.json()
        assert "download_url" in data
        print(f"✓ Spec pack download with minimal fields successful")
    
    def test_specpack_download_invalid_pack_returns_error(self):
        """Test that invalid pack_id returns error"""
        payload = {
            "name": "TEST_Invalid",
            "email": "test@example.com"
        }
        response = requests.post(
            f"{BASE_URL}/api/specpacks/invalid-pack-id/download",
            json=payload
        )
        assert response.status_code == 200  # API returns 200 with error message
        data = response.json()
        assert "error" in data
        print(f"✓ Invalid pack_id returns error correctly")
    
    def test_specpack_download_all_valid_packs(self):
        """Test download works for all valid spec pack IDs"""
        valid_packs = [
            "retail-hospitality", "outdoor-dooh", "corporate-control",
            "healthcare-wayfinding", "education-campus", "cob-mip-smd",
            "pixel-pitch", "brightness-nits", "ip-rating", "refresh-rate"
        ]
        for pack_id in valid_packs:
            payload = {
                "name": f"TEST_Pack_{pack_id}",
                "email": f"test_{pack_id}@example.com"
            }
            response = requests.post(
                f"{BASE_URL}/api/specpacks/{pack_id}/download",
                json=payload
            )
            assert response.status_code == 200
            data = response.json()
            assert "download_url" in data, f"Pack {pack_id} failed"
        print(f"✓ All {len(valid_packs)} spec packs download successfully")


class TestContactFormEndpoint:
    """Tests for POST /api/leads - Contact form submission + email notification"""
    
    def test_contact_form_submission_success(self):
        """Test contact form creates lead and returns success"""
        payload = {
            "name": "TEST_Contact_Bob",
            "email": "test_contact_bob@example.com",
            "company": "Test Company Ltd",
            "phone": "+971501234567",
            "city": "Dubai",
            "application": "Retail Display",
            "product_interest": "Indoor LED",
            "timeline": "1-3 months",
            "budget": "50000-100000",
            "message": "Test message for LED wall inquiry"
        }
        response = requests.post(
            f"{BASE_URL}/api/leads",
            json=payload
        )
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        data = response.json()
        
        # Validate response structure
        assert data.get("success") == True, "Response should have success: true"
        assert "message" in data, "Response should have message"
        assert "leadId" in data, "Response should have leadId"
        print(f"✓ Contact form submission successful, leadId: {data['leadId']}")
    
    def test_contact_form_minimal_required_fields(self):
        """Test contact form with only required fields"""
        payload = {
            "name": "TEST_Minimal_Contact",
            "email": "test_minimal_contact@example.com"
        }
        response = requests.post(
            f"{BASE_URL}/api/leads",
            json=payload
        )
        assert response.status_code == 200
        data = response.json()
        assert data.get("success") == True
        print(f"✓ Contact form with minimal fields successful")
    
    def test_contact_form_with_all_optional_fields(self):
        """Test contact form with all optional fields populated"""
        payload = {
            "name": "TEST_Full_Contact",
            "email": "test_full_contact@example.com",
            "company": "Full Test Corp",
            "phone": "+971551234567",
            "city": "Abu Dhabi",
            "application": "Corporate Meeting Room",
            "product_interest": "COB LED",
            "timeline": "3-6 months",
            "budget": "100000-200000",
            "message": "Full contact form test with all fields"
        }
        response = requests.post(
            f"{BASE_URL}/api/leads",
            json=payload
        )
        assert response.status_code == 200
        data = response.json()
        assert data.get("success") == True
        assert "leadId" in data
        print(f"✓ Contact form with all fields successful")
    
    def test_contact_form_missing_name_fails(self):
        """Test that missing required name field fails validation"""
        payload = {
            "email": "test_no_name@example.com"
        }
        response = requests.post(
            f"{BASE_URL}/api/leads",
            json=payload
        )
        # Pydantic should reject missing required field
        assert response.status_code == 422, f"Expected 422, got {response.status_code}"
        print(f"✓ Missing name field correctly rejected")
    
    def test_contact_form_missing_email_fails(self):
        """Test that missing required email field fails validation"""
        payload = {
            "name": "TEST_No_Email"
        }
        response = requests.post(
            f"{BASE_URL}/api/leads",
            json=payload
        )
        # Pydantic should reject missing required field
        assert response.status_code == 422, f"Expected 422, got {response.status_code}"
        print(f"✓ Missing email field correctly rejected")


class TestEmailServiceIntegration:
    """Tests for email service integration (non-blocking, graceful failure)"""
    
    def test_api_returns_fast_regardless_of_email(self):
        """Test that API returns quickly (email is fire-and-forget)"""
        import time
        payload = {
            "name": "TEST_Speed_Test",
            "email": "test_speed@example.com",
            "company": "Speed Corp"
        }
        
        start_time = time.time()
        response = requests.post(
            f"{BASE_URL}/api/specpacks/pixel-pitch/download",
            json=payload,
            timeout=10
        )
        elapsed = time.time() - start_time
        
        assert response.status_code == 200
        # API should return within 5 seconds (generous timeout)
        # Email sending is async/non-blocking so shouldn't delay response
        assert elapsed < 5, f"API took too long: {elapsed}s"
        print(f"✓ API returned in {elapsed:.2f}s (email is non-blocking)")
    
    def test_contact_form_returns_fast(self):
        """Test that contact form API returns quickly"""
        import time
        payload = {
            "name": "TEST_Contact_Speed",
            "email": "test_contact_speed@example.com",
            "application": "Test Application"
        }
        
        start_time = time.time()
        response = requests.post(
            f"{BASE_URL}/api/leads",
            json=payload,
            timeout=10
        )
        elapsed = time.time() - start_time
        
        assert response.status_code == 200
        assert elapsed < 5, f"API took too long: {elapsed}s"
        print(f"✓ Contact form API returned in {elapsed:.2f}s")


class TestSpecPackFileEndpoints:
    """Tests for spec pack PDF file serving"""
    
    def test_spec_pack_file_returns_pdf(self):
        """Test that spec pack file endpoint returns valid PDF"""
        response = requests.get(
            f"{BASE_URL}/api/specpacks/pixel-pitch/file",
            stream=True
        )
        assert response.status_code == 200
        assert response.headers.get("content-type") == "application/pdf"
        
        # Check PDF magic bytes
        content = response.content[:4]
        assert content == b'%PDF', f"Not a valid PDF: {content}"
        print(f"✓ Spec pack file returns valid PDF")
    
    def test_specpacks_list_endpoint(self):
        """Test that spec packs list returns all available packs"""
        response = requests.get(f"{BASE_URL}/api/specpacks")
        assert response.status_code == 200
        data = response.json()
        assert "packs" in data
        assert len(data["packs"]) == 10
        print(f"✓ Spec packs list returns {len(data['packs'])} packs")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
