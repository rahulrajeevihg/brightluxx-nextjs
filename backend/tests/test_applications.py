"""
Test suite for Application Landing Pages and For Architects APIs.
Tests application data rendering, spec pack downloads, and page routing.
"""
import pytest
import requests
import os

BASE_URL = os.environ.get('REACT_APP_BACKEND_URL', '').rstrip('/')

class TestSpecPacksAPI:
    """Spec Pack API tests for application pages"""
    
    def test_list_specpacks_returns_10_packs(self):
        """GET /api/specpacks returns all 10 spec packs"""
        response = requests.get(f"{BASE_URL}/api/specpacks")
        assert response.status_code == 200
        data = response.json()
        assert 'packs' in data
        assert len(data['packs']) == 10
        print(f"✓ Listed {len(data['packs'])} spec packs")
    
    def test_specpacks_have_required_fields(self):
        """Each spec pack has id and title fields"""
        response = requests.get(f"{BASE_URL}/api/specpacks")
        assert response.status_code == 200
        data = response.json()
        for pack in data['packs']:
            assert 'id' in pack
            assert 'title' in pack
            print(f"  ✓ Pack {pack['id']}: {pack['title']}")
    
    def test_application_specpacks_exist(self):
        """All 5 application-specific spec packs exist"""
        response = requests.get(f"{BASE_URL}/api/specpacks")
        assert response.status_code == 200
        data = response.json()
        pack_ids = [p['id'] for p in data['packs']]
        
        expected_app_packs = [
            'retail-hospitality',
            'outdoor-dooh', 
            'corporate-control',
            'healthcare-wayfinding',
            'education-campus'
        ]
        for pack_id in expected_app_packs:
            assert pack_id in pack_ids, f"Missing application spec pack: {pack_id}"
            print(f"  ✓ Application pack exists: {pack_id}")
    
    def test_knowledge_specpacks_exist(self):
        """All 5 knowledge-based spec packs exist"""
        response = requests.get(f"{BASE_URL}/api/specpacks")
        assert response.status_code == 200
        data = response.json()
        pack_ids = [p['id'] for p in data['packs']]
        
        expected_kb_packs = [
            'cob-mip-smd',
            'pixel-pitch',
            'brightness-nits',
            'ip-rating',
            'refresh-rate'
        ]
        for pack_id in expected_kb_packs:
            assert pack_id in pack_ids, f"Missing knowledge spec pack: {pack_id}"
            print(f"  ✓ Knowledge pack exists: {pack_id}")


class TestSpecPackDownload:
    """Spec Pack gated download API tests"""
    
    def test_download_retail_hospitality_pack(self):
        """POST /api/specpacks/retail-hospitality/download returns download URL"""
        response = requests.post(
            f"{BASE_URL}/api/specpacks/retail-hospitality/download",
            json={"email": "test_apps_retail@example.com", "name": "Test User", "pack_id": "retail-hospitality"}
        )
        assert response.status_code == 200
        data = response.json()
        assert 'download_url' in data
        assert 'retail-hospitality' in data['download_url']
        print(f"✓ Download URL: {data['download_url']}")
    
    def test_download_outdoor_dooh_pack(self):
        """POST /api/specpacks/outdoor-dooh/download returns download URL"""
        response = requests.post(
            f"{BASE_URL}/api/specpacks/outdoor-dooh/download",
            json={"email": "test_apps_outdoor@example.com", "name": "Test User", "pack_id": "outdoor-dooh"}
        )
        assert response.status_code == 200
        data = response.json()
        assert 'download_url' in data
        print(f"✓ Outdoor DOOH pack download works")
    
    def test_download_corporate_control_pack(self):
        """POST /api/specpacks/corporate-control/download returns download URL"""
        response = requests.post(
            f"{BASE_URL}/api/specpacks/corporate-control/download",
            json={"email": "test_apps_corp@example.com", "name": "Test User", "pack_id": "corporate-control"}
        )
        assert response.status_code == 200
        data = response.json()
        assert 'download_url' in data
        print(f"✓ Corporate pack download works")
    
    def test_download_healthcare_pack(self):
        """POST /api/specpacks/healthcare-wayfinding/download returns download URL"""
        response = requests.post(
            f"{BASE_URL}/api/specpacks/healthcare-wayfinding/download",
            json={"email": "test_apps_health@example.com", "name": "Test User", "pack_id": "healthcare-wayfinding"}
        )
        assert response.status_code == 200
        data = response.json()
        assert 'download_url' in data
        print(f"✓ Healthcare pack download works")
    
    def test_download_education_pack(self):
        """POST /api/specpacks/education-campus/download returns download URL"""
        response = requests.post(
            f"{BASE_URL}/api/specpacks/education-campus/download",
            json={"email": "test_apps_edu@example.com", "name": "Test User", "pack_id": "education-campus"}
        )
        assert response.status_code == 200
        data = response.json()
        assert 'download_url' in data
        print(f"✓ Education pack download works")
    
    def test_download_invalid_pack_returns_error(self):
        """POST /api/specpacks/invalid-pack/download returns error"""
        response = requests.post(
            f"{BASE_URL}/api/specpacks/invalid-pack/download",
            json={"email": "test@example.com", "name": "Test", "pack_id": "invalid-pack"}
        )
        assert response.status_code == 200  # API returns 200 with error in body
        data = response.json()
        assert 'error' in data
        print(f"✓ Invalid pack returns error: {data['error']}")


class TestSpecPackPDFServing:
    """PDF file serving tests for For Architects page direct downloads"""
    
    def test_serve_retail_hospitality_pdf(self):
        """GET /api/specpacks/retail-hospitality/file returns valid PDF"""
        response = requests.get(f"{BASE_URL}/api/specpacks/retail-hospitality/file")
        assert response.status_code == 200
        assert response.headers['content-type'] == 'application/pdf'
        assert response.content[:4] == b'%PDF'
        print(f"✓ retail-hospitality PDF: {len(response.content)} bytes")
    
    def test_serve_outdoor_dooh_pdf(self):
        """GET /api/specpacks/outdoor-dooh/file returns valid PDF"""
        response = requests.get(f"{BASE_URL}/api/specpacks/outdoor-dooh/file")
        assert response.status_code == 200
        assert response.headers['content-type'] == 'application/pdf'
        assert response.content[:4] == b'%PDF'
        print(f"✓ outdoor-dooh PDF: {len(response.content)} bytes")
    
    def test_serve_corporate_control_pdf(self):
        """GET /api/specpacks/corporate-control/file returns valid PDF"""
        response = requests.get(f"{BASE_URL}/api/specpacks/corporate-control/file")
        assert response.status_code == 200
        assert response.headers['content-type'] == 'application/pdf'
        assert response.content[:4] == b'%PDF'
        print(f"✓ corporate-control PDF: {len(response.content)} bytes")
    
    def test_serve_healthcare_pdf(self):
        """GET /api/specpacks/healthcare-wayfinding/file returns valid PDF"""
        response = requests.get(f"{BASE_URL}/api/specpacks/healthcare-wayfinding/file")
        assert response.status_code == 200
        assert response.headers['content-type'] == 'application/pdf'
        assert response.content[:4] == b'%PDF'
        print(f"✓ healthcare-wayfinding PDF: {len(response.content)} bytes")
    
    def test_serve_education_pdf(self):
        """GET /api/specpacks/education-campus/file returns valid PDF"""
        response = requests.get(f"{BASE_URL}/api/specpacks/education-campus/file")
        assert response.status_code == 200
        assert response.headers['content-type'] == 'application/pdf'
        assert response.content[:4] == b'%PDF'
        print(f"✓ education-campus PDF: {len(response.content)} bytes")
    
    def test_all_10_pdfs_are_valid(self):
        """All 10 spec pack PDFs are valid"""
        all_packs = [
            'cob-mip-smd', 'pixel-pitch', 'brightness-nits', 'ip-rating', 'refresh-rate',
            'retail-hospitality', 'outdoor-dooh', 'corporate-control', 'healthcare-wayfinding', 'education-campus'
        ]
        for pack_id in all_packs:
            response = requests.get(f"{BASE_URL}/api/specpacks/{pack_id}/file")
            assert response.status_code == 200, f"PDF failed for {pack_id}"
            assert response.headers['content-type'] == 'application/pdf'
            assert response.content[:4] == b'%PDF', f"Invalid PDF header for {pack_id}"
            print(f"  ✓ {pack_id}: {len(response.content)} bytes")


class TestHealthCheck:
    """Basic health check for backend"""
    
    def test_backend_health(self):
        """GET /api/health returns ok status"""
        response = requests.get(f"{BASE_URL}/api/health")
        assert response.status_code == 200
        data = response.json()
        assert data['status'] == 'ok'
        print(f"✓ Backend healthy: {data}")
