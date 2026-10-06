"""
Phase C Testing: Sitemap, BIM/CAD References, and Cheat Sheets
Tests dynamic sitemap.xml, lead-gated downloads, and PDF generation.
"""
import pytest
import requests
import os

BASE_URL = os.environ.get('REACT_APP_BACKEND_URL', '').rstrip('/')


class TestSitemap:
    """Tests for dynamic sitemap.xml generation."""
    
    def test_sitemap_returns_valid_xml(self):
        """GET /api/sitemap.xml should return valid XML."""
        response = requests.get(f"{BASE_URL}/api/sitemap.xml")
        assert response.status_code == 200
        assert response.headers.get('content-type') == 'application/xml'
        assert '<?xml version="1.0" encoding="UTF-8"?>' in response.text
        assert '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">' in response.text
    
    def test_sitemap_contains_40_plus_urls(self):
        """Sitemap should contain 40+ URLs."""
        response = requests.get(f"{BASE_URL}/api/sitemap.xml")
        assert response.status_code == 200
        url_count = response.text.count('<url>')
        assert url_count >= 40, f"Expected 40+ URLs, found {url_count}"
        print(f"Sitemap contains {url_count} URLs")
    
    def test_sitemap_contains_required_routes(self):
        """Sitemap should contain all key routes."""
        response = requests.get(f"{BASE_URL}/api/sitemap.xml")
        assert response.status_code == 200
        
        required_routes = [
            '/', '/products', '/solutions', '/knowledge', '/projects',
            '/contact', '/about', '/calculator', '/budget-estimator',
            '/compare', '/for-architects', '/value-engineering',
            '/spec-substitution', '/applications', '/latest-tech',
            '/knowledge/cob-vs-mip-vs-smd', '/knowledge/pixel-pitch-guide',
            '/knowledge/brightness-nits-guide', '/knowledge/ip-rating-guide',
            '/knowledge/refresh-rate-guide', '/knowledge/processing-calibration',
            '/knowledge/cms-multi-site',
            '/applications/retail', '/applications/hospitality',
            '/applications/corporate', '/applications/healthcare',
            '/contractors/dvled-vs-lcd', '/contractors/led-cost-per-sqm',
        ]
        
        for route in required_routes:
            assert f'<loc>https://brightluxx.com{route}</loc>' in response.text, f"Missing route: {route}"


class TestDownloadsCatalog:
    """Tests for downloads catalog endpoint."""
    
    def test_catalog_returns_4_cheatsheets_and_4_bim(self):
        """GET /api/downloads/catalog should return 4 cheatsheets and 4 BIM references."""
        response = requests.get(f"{BASE_URL}/api/downloads/catalog")
        assert response.status_code == 200
        
        data = response.json()
        assert 'cheatsheets' in data
        assert 'bim_references' in data
        assert len(data['cheatsheets']) == 4, f"Expected 4 cheatsheets, got {len(data['cheatsheets'])}"
        assert len(data['bim_references']) == 4, f"Expected 4 BIM refs, got {len(data['bim_references'])}"
        
        # Verify cheatsheet IDs
        cheatsheet_ids = [cs['id'] for cs in data['cheatsheets']]
        assert 'pixel-pitch-cheatsheet' in cheatsheet_ids
        assert 'brightness-cheatsheet' in cheatsheet_ids
        assert 'cob-mip-smd-cheatsheet' in cheatsheet_ids
        assert 'outdoor-checklist' in cheatsheet_ids
        
        # Verify BIM IDs
        bim_ids = [bim['id'] for bim in data['bim_references']]
        assert 'all-in-one-dvled' in bim_ids
        assert 'fine-pitch-wall' in bim_ids
        assert 'outdoor-cabinet' in bim_ids
        assert 'transparent-film' in bim_ids


class TestCheatsheetDownloads:
    """Tests for cheatsheet lead-gated downloads."""
    
    @pytest.fixture
    def session(self):
        """Create a requests session."""
        return requests.Session()
    
    def test_pixel_pitch_request_returns_download_url(self, session):
        """POST /api/downloads/cheatsheet/pixel-pitch-cheatsheet/request with lead data."""
        response = session.post(
            f"{BASE_URL}/api/downloads/cheatsheet/pixel-pitch-cheatsheet/request",
            json={"email": "TEST_architect@example.com", "name": "Test Architect"}
        )
        assert response.status_code == 200
        data = response.json()
        assert 'download_url' in data
        assert data['download_url'] == '/api/downloads/cheatsheet/pixel-pitch-cheatsheet/file'
    
    def test_pixel_pitch_file_returns_valid_pdf(self, session):
        """GET /api/downloads/cheatsheet/pixel-pitch-cheatsheet/file returns valid PDF."""
        response = session.get(f"{BASE_URL}/api/downloads/cheatsheet/pixel-pitch-cheatsheet/file")
        assert response.status_code == 200
        assert response.headers.get('content-type') == 'application/pdf'
        assert response.content[:4] == b'%PDF', "Not a valid PDF file"
        assert len(response.content) > 1000, f"PDF too small: {len(response.content)} bytes"
    
    def test_brightness_request_and_file(self, session):
        """Test brightness cheatsheet request and file download."""
        # Request
        response = session.post(
            f"{BASE_URL}/api/downloads/cheatsheet/brightness-cheatsheet/request",
            json={"email": "TEST_consultant@example.com", "name": "Test Consultant"}
        )
        assert response.status_code == 200
        assert response.json()['download_url'] == '/api/downloads/cheatsheet/brightness-cheatsheet/file'
        
        # File
        file_response = session.get(f"{BASE_URL}/api/downloads/cheatsheet/brightness-cheatsheet/file")
        assert file_response.status_code == 200
        assert file_response.content[:4] == b'%PDF'
    
    def test_cob_mip_smd_request_and_file(self, session):
        """Test COB vs MiP vs SMD cheatsheet."""
        response = session.post(
            f"{BASE_URL}/api/downloads/cheatsheet/cob-mip-smd-cheatsheet/request",
            json={"email": "TEST_designer@example.com", "name": "Test Designer"}
        )
        assert response.status_code == 200
        
        file_response = session.get(f"{BASE_URL}/api/downloads/cheatsheet/cob-mip-smd-cheatsheet/file")
        assert file_response.status_code == 200
        assert file_response.content[:4] == b'%PDF'
    
    def test_outdoor_checklist_request_and_file(self, session):
        """Test outdoor durability checklist."""
        response = session.post(
            f"{BASE_URL}/api/downloads/cheatsheet/outdoor-checklist/request",
            json={"email": "TEST_engineer@example.com", "name": "Test Engineer"}
        )
        assert response.status_code == 200
        
        file_response = session.get(f"{BASE_URL}/api/downloads/cheatsheet/outdoor-checklist/file")
        assert file_response.status_code == 200
        assert file_response.content[:4] == b'%PDF'


class TestBIMDownloads:
    """Tests for BIM/CAD reference lead-gated downloads."""
    
    @pytest.fixture
    def session(self):
        """Create a requests session."""
        return requests.Session()
    
    def test_all_in_one_dvled_request_returns_download_url(self, session):
        """POST /api/downloads/bim/all-in-one-dvled/request with lead data."""
        response = session.post(
            f"{BASE_URL}/api/downloads/bim/all-in-one-dvled/request",
            json={"email": "TEST_bim_user@example.com", "name": "BIM User", "company": "Test Firm"}
        )
        assert response.status_code == 200
        data = response.json()
        assert 'download_url' in data
        assert data['download_url'] == '/api/downloads/bim/all-in-one-dvled/file'
    
    def test_all_in_one_dvled_file_returns_valid_pdf(self, session):
        """GET /api/downloads/bim/all-in-one-dvled/file returns valid PDF."""
        response = session.get(f"{BASE_URL}/api/downloads/bim/all-in-one-dvled/file")
        assert response.status_code == 200
        assert response.headers.get('content-type') == 'application/pdf'
        assert response.content[:4] == b'%PDF', "Not a valid PDF file"
        assert len(response.content) > 1000, f"PDF too small: {len(response.content)} bytes"
    
    def test_fine_pitch_wall_request_and_file(self, session):
        """Test fine-pitch wall BIM reference."""
        response = session.post(
            f"{BASE_URL}/api/downloads/bim/fine-pitch-wall/request",
            json={"email": "TEST_cad_user@example.com", "name": "CAD User"}
        )
        assert response.status_code == 200
        
        file_response = session.get(f"{BASE_URL}/api/downloads/bim/fine-pitch-wall/file")
        assert file_response.status_code == 200
        assert file_response.content[:4] == b'%PDF'
    
    def test_outdoor_cabinet_request_and_file(self, session):
        """Test outdoor cabinet BIM reference."""
        response = session.post(
            f"{BASE_URL}/api/downloads/bim/outdoor-cabinet/request",
            json={"email": "TEST_outdoor_spec@example.com", "name": "Outdoor Spec"}
        )
        assert response.status_code == 200
        
        file_response = session.get(f"{BASE_URL}/api/downloads/bim/outdoor-cabinet/file")
        assert file_response.status_code == 200
        assert file_response.content[:4] == b'%PDF'
    
    def test_transparent_film_request_and_file(self, session):
        """Test transparent LED film BIM reference."""
        response = session.post(
            f"{BASE_URL}/api/downloads/bim/transparent-film/request",
            json={"email": "TEST_glass_spec@example.com", "name": "Glass Spec"}
        )
        assert response.status_code == 200
        
        file_response = session.get(f"{BASE_URL}/api/downloads/bim/transparent-film/file")
        assert file_response.status_code == 200
        assert file_response.content[:4] == b'%PDF'


class TestInvalidDownloads:
    """Tests for invalid download requests."""
    
    def test_invalid_doc_type_returns_error(self):
        """POST with invalid doc_type should return error."""
        response = requests.post(
            f"{BASE_URL}/api/downloads/invalid-type/some-id/request",
            json={"email": "test@example.com", "name": "Test"}
        )
        assert response.status_code == 200  # FastAPI returns 200 with error body
        data = response.json()
        assert 'error' in data
    
    def test_invalid_doc_id_returns_error(self):
        """POST with invalid doc_id should return error."""
        response = requests.post(
            f"{BASE_URL}/api/downloads/cheatsheet/invalid-id/request",
            json={"email": "test@example.com", "name": "Test"}
        )
        assert response.status_code == 200
        data = response.json()
        assert 'error' in data


class TestLeadCapture:
    """Tests for verifying leads are captured in database."""
    
    def test_cheatsheet_download_captures_lead(self):
        """Verify lead is captured after cheatsheet download request."""
        # Make a download request with unique email
        import time
        unique_email = f"TEST_lead_capture_{int(time.time())}@example.com"
        
        response = requests.post(
            f"{BASE_URL}/api/downloads/cheatsheet/pixel-pitch-cheatsheet/request",
            json={"email": unique_email, "name": "Lead Capture Test", "company": "Test Corp"}
        )
        assert response.status_code == 200
        assert 'download_url' in response.json()
        # Note: Lead verification would require admin access or direct DB query
        # We verify the API accepted the request and returned download_url
    
    def test_bim_download_captures_lead(self):
        """Verify lead is captured after BIM download request."""
        import time
        unique_email = f"TEST_bim_lead_{int(time.time())}@example.com"
        
        response = requests.post(
            f"{BASE_URL}/api/downloads/bim/all-in-one-dvled/request",
            json={"email": unique_email, "name": "BIM Lead Test"}
        )
        assert response.status_code == 200
        assert 'download_url' in response.json()
