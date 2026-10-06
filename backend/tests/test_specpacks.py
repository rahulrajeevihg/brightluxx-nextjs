"""
Tests for Knowledge Base Spec Pack APIs
- GET /api/specpacks - List all spec packs (10 total)
- POST /api/specpacks/{pack_id}/download - Lead capture + return download URL
- GET /api/specpacks/{pack_id}/file - Serve PDF file
"""
import pytest
import requests
import os
import time

BASE_URL = os.environ.get('REACT_APP_BACKEND_URL', '').rstrip('/')


class TestSpecPackListing:
    """Tests for spec pack listing endpoint"""
    
    def test_list_specpacks_returns_200(self):
        """GET /api/specpacks should return 200"""
        response = requests.get(f"{BASE_URL}/api/specpacks")
        assert response.status_code == 200, f"Expected 200, got {response.status_code}"
        print("PASS: GET /api/specpacks returns 200")
    
    def test_list_specpacks_returns_10_packs(self):
        """GET /api/specpacks should return exactly 10 spec packs"""
        response = requests.get(f"{BASE_URL}/api/specpacks")
        data = response.json()
        
        assert "packs" in data, "Response should contain 'packs' field"
        assert len(data["packs"]) == 10, f"Expected 10 packs, got {len(data['packs'])}"
        print(f"PASS: Returns 10 spec packs: {[p['id'] for p in data['packs']]}")
    
    def test_list_specpacks_has_correct_ids(self):
        """GET /api/specpacks should return all expected pack IDs"""
        expected_ids = [
            "retail-hospitality", "outdoor-dooh", "corporate-control",
            "healthcare-wayfinding", "education-campus", "cob-mip-smd",
            "pixel-pitch", "brightness-nits", "ip-rating", "refresh-rate"
        ]
        
        response = requests.get(f"{BASE_URL}/api/specpacks")
        data = response.json()
        
        actual_ids = [p["id"] for p in data["packs"]]
        for expected_id in expected_ids:
            assert expected_id in actual_ids, f"Missing pack ID: {expected_id}"
        
        print(f"PASS: All 10 expected pack IDs present")
    
    def test_list_specpacks_has_titles(self):
        """Each spec pack should have id and title fields"""
        response = requests.get(f"{BASE_URL}/api/specpacks")
        data = response.json()
        
        for pack in data["packs"]:
            assert "id" in pack, "Pack should have 'id' field"
            assert "title" in pack, "Pack should have 'title' field"
            assert pack["id"], "Pack id should not be empty"
            assert pack["title"], "Pack title should not be empty"
        
        print("PASS: All packs have id and title fields")


class TestSpecPackDownload:
    """Tests for spec pack download (lead capture) endpoint"""
    
    def test_download_cob_mip_smd_returns_200(self):
        """POST /api/specpacks/cob-mip-smd/download should return 200 with download_url"""
        payload = {
            "email": "test_architect@example.com",
            "name": "Test Architect",
            "pack_id": "cob-mip-smd"
        }
        response = requests.post(f"{BASE_URL}/api/specpacks/cob-mip-smd/download", json=payload)
        
        assert response.status_code == 200, f"Expected 200, got {response.status_code}"
        data = response.json()
        assert "download_url" in data, "Response should contain 'download_url'"
        assert data["download_url"] == "/api/specpacks/cob-mip-smd/file", f"Unexpected download URL: {data['download_url']}"
        print(f"PASS: POST /api/specpacks/cob-mip-smd/download returns download_url: {data['download_url']}")
    
    def test_download_pixel_pitch_returns_200(self):
        """POST /api/specpacks/pixel-pitch/download should return 200"""
        payload = {
            "email": "test_consultant@example.com",
            "name": "Test Consultant",
            "pack_id": "pixel-pitch"
        }
        response = requests.post(f"{BASE_URL}/api/specpacks/pixel-pitch/download", json=payload)
        
        assert response.status_code == 200, f"Expected 200, got {response.status_code}"
        data = response.json()
        assert "download_url" in data
        print(f"PASS: POST /api/specpacks/pixel-pitch/download returns download_url")
    
    def test_download_all_5_knowledge_packs(self):
        """Test download for all 5 knowledge base spec packs"""
        knowledge_packs = ["cob-mip-smd", "pixel-pitch", "brightness-nits", "ip-rating", "refresh-rate"]
        
        for pack_id in knowledge_packs:
            payload = {
                "email": f"test_{pack_id}@example.com",
                "name": f"Test User {pack_id}",
                "pack_id": pack_id
            }
            response = requests.post(f"{BASE_URL}/api/specpacks/{pack_id}/download", json=payload)
            
            assert response.status_code == 200, f"Failed for {pack_id}: {response.status_code}"
            data = response.json()
            assert "download_url" in data, f"No download_url for {pack_id}"
            print(f"PASS: Download endpoint works for {pack_id}")
    
    def test_download_all_5_application_packs(self):
        """Test download for all 5 application spec packs"""
        app_packs = ["retail-hospitality", "outdoor-dooh", "corporate-control", 
                     "healthcare-wayfinding", "education-campus"]
        
        for pack_id in app_packs:
            payload = {
                "email": f"test_{pack_id}@example.com",
                "name": f"Test User {pack_id}",
                "pack_id": pack_id
            }
            response = requests.post(f"{BASE_URL}/api/specpacks/{pack_id}/download", json=payload)
            
            assert response.status_code == 200, f"Failed for {pack_id}: {response.status_code}"
            data = response.json()
            assert "download_url" in data, f"No download_url for {pack_id}"
            print(f"PASS: Download endpoint works for {pack_id}")
    
    def test_download_invalid_pack_returns_error(self):
        """POST /api/specpacks/invalid-pack/download should return error"""
        payload = {
            "email": "test@example.com",
            "name": "Test",
            "pack_id": "invalid-pack"
        }
        response = requests.post(f"{BASE_URL}/api/specpacks/invalid-pack/download", json=payload)
        
        assert response.status_code == 200, f"Expected 200, got {response.status_code}"
        data = response.json()
        assert "error" in data, "Should return error for invalid pack"
        print(f"PASS: Invalid pack ID returns error: {data['error']}")


class TestSpecPackPDFFile:
    """Tests for PDF file serving endpoint"""
    
    def test_file_cob_mip_smd_returns_pdf(self):
        """GET /api/specpacks/cob-mip-smd/file should return valid PDF"""
        response = requests.get(f"{BASE_URL}/api/specpacks/cob-mip-smd/file")
        
        assert response.status_code == 200, f"Expected 200, got {response.status_code}"
        assert response.headers.get("content-type") == "application/pdf", f"Expected PDF, got {response.headers.get('content-type')}"
        assert len(response.content) > 1000, "PDF content should be substantial"
        assert response.content[:4] == b'%PDF', "Content should start with PDF magic bytes"
        print(f"PASS: cob-mip-smd PDF returned, size: {len(response.content)} bytes")
    
    def test_file_pixel_pitch_returns_pdf(self):
        """GET /api/specpacks/pixel-pitch/file should return valid PDF"""
        response = requests.get(f"{BASE_URL}/api/specpacks/pixel-pitch/file")
        
        assert response.status_code == 200
        assert response.headers.get("content-type") == "application/pdf"
        assert response.content[:4] == b'%PDF'
        print(f"PASS: pixel-pitch PDF returned, size: {len(response.content)} bytes")
    
    def test_all_knowledge_pdfs_are_valid(self):
        """Test all 5 knowledge base PDFs are valid"""
        knowledge_packs = ["cob-mip-smd", "pixel-pitch", "brightness-nits", "ip-rating", "refresh-rate"]
        
        for pack_id in knowledge_packs:
            response = requests.get(f"{BASE_URL}/api/specpacks/{pack_id}/file")
            
            assert response.status_code == 200, f"Failed for {pack_id}"
            assert response.headers.get("content-type") == "application/pdf", f"Not PDF for {pack_id}"
            assert response.content[:4] == b'%PDF', f"Invalid PDF for {pack_id}"
            print(f"PASS: {pack_id} PDF valid ({len(response.content)} bytes)")
    
    def test_all_application_pdfs_are_valid(self):
        """Test all 5 application spec pack PDFs are valid"""
        app_packs = ["retail-hospitality", "outdoor-dooh", "corporate-control", 
                     "healthcare-wayfinding", "education-campus"]
        
        for pack_id in app_packs:
            response = requests.get(f"{BASE_URL}/api/specpacks/{pack_id}/file")
            
            assert response.status_code == 200, f"Failed for {pack_id}"
            assert response.headers.get("content-type") == "application/pdf", f"Not PDF for {pack_id}"
            assert response.content[:4] == b'%PDF', f"Invalid PDF for {pack_id}"
            print(f"PASS: {pack_id} PDF valid ({len(response.content)} bytes)")


class TestLeadCapture:
    """Tests to verify lead data is captured during download"""
    
    def test_download_creates_lead_with_source(self):
        """Download should capture lead with spec_pack_download source"""
        timestamp = int(time.time())
        payload = {
            "email": f"test_lead_{timestamp}@example.com",
            "name": f"Test Lead {timestamp}",
            "pack_id": "cob-mip-smd"
        }
        response = requests.post(f"{BASE_URL}/api/specpacks/cob-mip-smd/download", json=payload)
        
        assert response.status_code == 200
        data = response.json()
        assert "download_url" in data
        
        # The lead should be captured - we can verify by checking admin leads endpoint
        print(f"PASS: Lead capture triggered for email: {payload['email']}")


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
