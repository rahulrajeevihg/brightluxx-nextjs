"""
Phase B Content Expansion Tests
Tests: new spec packs (supermarket-promotions, residential-cinema), specpacks API
"""
import pytest
import requests
import os

BASE_URL = os.environ.get('REACT_APP_BACKEND_URL', '').rstrip('/')

class TestSpecPacksAPI:
    """Test the spec packs API returns 12 packs including new ones"""
    
    def test_specpacks_returns_12_packs(self):
        """GET /api/specpacks should return 12 packs"""
        response = requests.get(f"{BASE_URL}/api/specpacks")
        assert response.status_code == 200, f"Expected 200, got {response.status_code}"
        data = response.json()
        assert "packs" in data, "Response should have 'packs' key"
        assert len(data["packs"]) == 12, f"Expected 12 packs, got {len(data['packs'])}"
    
    def test_specpacks_includes_supermarket_promotions(self):
        """GET /api/specpacks should include supermarket-promotions"""
        response = requests.get(f"{BASE_URL}/api/specpacks")
        assert response.status_code == 200
        data = response.json()
        pack_ids = [p["id"] for p in data["packs"]]
        assert "supermarket-promotions" in pack_ids, "supermarket-promotions should be in packs"
    
    def test_specpacks_includes_residential_cinema(self):
        """GET /api/specpacks should include residential-cinema"""
        response = requests.get(f"{BASE_URL}/api/specpacks")
        assert response.status_code == 200
        data = response.json()
        pack_ids = [p["id"] for p in data["packs"]]
        assert "residential-cinema" in pack_ids, "residential-cinema should be in packs"


class TestSupermarketSpecPack:
    """Test supermarket-promotions spec pack download"""
    
    def test_supermarket_download_returns_download_url(self):
        """POST /api/specpacks/supermarket-promotions/download should return download_url"""
        response = requests.post(
            f"{BASE_URL}/api/specpacks/supermarket-promotions/download",
            json={
                "email": "TEST_supermarket@example.com",
                "name": "Test User",
                "company": "Test Supermarket",
                "role": "Manager",
                "pack_id": "supermarket-promotions"
            }
        )
        assert response.status_code == 200, f"Expected 200, got {response.status_code}"
        data = response.json()
        assert "download_url" in data, "Response should have 'download_url'"
        assert data["download_url"] == "/api/specpacks/supermarket-promotions/file"
    
    def test_supermarket_file_serves_pdf(self):
        """GET /api/specpacks/supermarket-promotions/file should serve PDF"""
        response = requests.get(f"{BASE_URL}/api/specpacks/supermarket-promotions/file")
        assert response.status_code == 200, f"Expected 200, got {response.status_code}"
        assert "application/pdf" in response.headers.get("content-type", "")
        assert len(response.content) > 5000, "PDF should have substantial content"


class TestResidentialCinemaSpecPack:
    """Test residential-cinema spec pack download"""
    
    def test_residential_download_returns_download_url(self):
        """POST /api/specpacks/residential-cinema/download should return download_url"""
        response = requests.post(
            f"{BASE_URL}/api/specpacks/residential-cinema/download",
            json={
                "email": "TEST_residential@example.com",
                "name": "Test Homeowner",
                "company": "Private Villa",
                "role": "Owner",
                "pack_id": "residential-cinema"
            }
        )
        assert response.status_code == 200, f"Expected 200, got {response.status_code}"
        data = response.json()
        assert "download_url" in data, "Response should have 'download_url'"
        assert data["download_url"] == "/api/specpacks/residential-cinema/file"
    
    def test_residential_file_serves_pdf(self):
        """GET /api/specpacks/residential-cinema/file should serve PDF"""
        response = requests.get(f"{BASE_URL}/api/specpacks/residential-cinema/file")
        assert response.status_code == 200, f"Expected 200, got {response.status_code}"
        assert "application/pdf" in response.headers.get("content-type", "")
        assert len(response.content) > 5000, "PDF should have substantial content"


class TestHealthEndpoint:
    """Test health endpoint still works"""
    
    def test_health_returns_ok(self):
        """GET /api/health should return status ok"""
        response = requests.get(f"{BASE_URL}/api/health")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "ok"
        assert data["database"] == "healthy"
