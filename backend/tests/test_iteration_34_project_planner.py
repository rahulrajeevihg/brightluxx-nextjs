"""
Tests for Project Planner API endpoints (/api/project-planner/calculate and /api/project-planner/pdf)
Also tests Installation Guide in sitemap and navbar integration
"""
import pytest
import requests
import os

BASE_URL = os.environ.get('REACT_APP_BACKEND_URL', '').rstrip('/')

class TestProjectPlannerAPI:
    """Project Planner /api/project-planner/calculate endpoint tests"""

    def test_calculate_returns_ok_with_valid_data(self):
        """Test basic calculation with valid data"""
        response = requests.post(
            f"{BASE_URL}/api/project-planner/calculate",
            json={
                "width": 4.0,
                "height": 2.5,
                "viewing_distance": 5.0,
                "content_type": "mixed",
                "environment": "indoor"
            }
        )
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "ok"
        assert "spec" in data

    def test_calculate_returns_correct_spec_structure(self):
        """Test that calculate returns all required spec fields"""
        response = requests.post(
            f"{BASE_URL}/api/project-planner/calculate",
            json={
                "width": 4.0,
                "height": 2.5,
                "viewing_distance": 5.0,
                "content_type": "mixed",
                "environment": "indoor"
            }
        )
        assert response.status_code == 200
        spec = response.json()["spec"]
        
        # Check all expected fields exist
        required_fields = [
            "ideal_pitch", "recommended_pitch", "premium_pitch", "tech", "area",
            "max_kw", "avg_kw", "daily_kwh", "monthly_kwh", "monthly_cost_aed",
            "annual_cost_aed", "heat_btu", "heat_tons", "max_amps", "breaker",
            "install_method", "budget_low", "budget_high", "min_viewing",
            "optimal_viewing", "max_viewing"
        ]
        for field in required_fields:
            assert field in spec, f"Missing field: {field}"

    def test_calculate_default_inputs_p15_pitch(self):
        """Test that default 4m x 2.5m, 5m distance, mixed content -> P1.5 pitch"""
        response = requests.post(
            f"{BASE_URL}/api/project-planner/calculate",
            json={
                "width": 4.0,
                "height": 2.5,
                "viewing_distance": 5.0,
                "content_type": "mixed",
                "environment": "indoor"
            }
        )
        spec = response.json()["spec"]
        assert spec["recommended_pitch"] == 1.5, f"Expected P1.5, got P{spec['recommended_pitch']}"

    def test_calculate_max_power_4m_x_25m(self):
        """Test max power for 4m x 2.5m @ P1.5 = 4.8kW (480W/sqm * 10sqm)"""
        response = requests.post(
            f"{BASE_URL}/api/project-planner/calculate",
            json={
                "width": 4.0,
                "height": 2.5,
                "viewing_distance": 5.0,
                "content_type": "mixed",
                "environment": "indoor"
            }
        )
        spec = response.json()["spec"]
        assert spec["max_kw"] == 4.8, f"Expected 4.8kW, got {spec['max_kw']}kW"
        assert spec["area"] == 10.0, f"Expected 10.0 sqm, got {spec['area']} sqm"

    def test_calculate_avg_power_with_brightness(self):
        """Test average power at 70% brightness (default): 1.19kW"""
        response = requests.post(
            f"{BASE_URL}/api/project-planner/calculate",
            json={
                "width": 4.0,
                "height": 2.5,
                "viewing_distance": 5.0,
                "content_type": "mixed",
                "environment": "indoor",
                "brightness": 70
            }
        )
        spec = response.json()["spec"]
        # 170W/sqm avg * 10sqm * 0.70 brightness = 1.19kW -> rounded to 1.2
        assert spec["avg_kw"] == 1.2, f"Expected 1.2kW avg, got {spec['avg_kw']}kW"

    def test_calculate_install_method_indoor_medium(self):
        """Test indoor 10sqm (medium) -> Wall-Mounted or Recessed"""
        response = requests.post(
            f"{BASE_URL}/api/project-planner/calculate",
            json={
                "width": 4.0,
                "height": 2.5,
                "viewing_distance": 5.0,
                "environment": "indoor"
            }
        )
        spec = response.json()["spec"]
        assert spec["install_method"] == "Wall-Mounted or Recessed", f"Got: {spec['install_method']}"

    def test_calculate_budget_range_p15_10sqm(self):
        """Test budget range for P1.5 @ 10sqm: $2200/sqm * 10 * 0.8 to $2200 * 10 * 1.3"""
        response = requests.post(
            f"{BASE_URL}/api/project-planner/calculate",
            json={
                "width": 4.0,
                "height": 2.5,
                "viewing_distance": 5.0
            }
        )
        spec = response.json()["spec"]
        # Low: 2200 * 10 * 0.8 = 17600
        # High: 2200 * 10 * 1.3 = 28600
        assert spec["budget_low"] == 17600.0, f"Expected $17,600, got ${spec['budget_low']}"
        assert spec["budget_high"] == 28600.0, f"Expected $28,600, got ${spec['budget_high']}"

    def test_calculate_outdoor_environment(self):
        """Test outdoor environment selects appropriate installation method"""
        response = requests.post(
            f"{BASE_URL}/api/project-planner/calculate",
            json={
                "width": 4.0,
                "height": 2.5,
                "viewing_distance": 10.0,
                "environment": "outdoor"
            }
        )
        spec = response.json()["spec"]
        assert "Ground" in spec["install_method"] or "IP65" in spec["install_method"]

    def test_calculate_different_content_types(self):
        """Test content type affects pitch calculation (text=tighter, video=wider)"""
        # Text content at 5m -> pitch 5/(3*0.8) = 2.08 -> P1.9
        response_text = requests.post(
            f"{BASE_URL}/api/project-planner/calculate",
            json={"width": 4, "height": 2.5, "viewing_distance": 5, "content_type": "text"}
        )
        # Video content at 5m -> pitch 5/(3*1.2) = 1.39 -> P1.5
        response_video = requests.post(
            f"{BASE_URL}/api/project-planner/calculate",
            json={"width": 4, "height": 2.5, "viewing_distance": 5, "content_type": "video"}
        )
        text_pitch = response_text.json()["spec"]["recommended_pitch"]
        video_pitch = response_video.json()["spec"]["recommended_pitch"]
        # Text allows wider pitch (further viewing OK), video needs tighter pitch
        assert text_pitch >= video_pitch, f"Text pitch {text_pitch} should be >= video pitch {video_pitch}"


class TestProjectPlannerPDF:
    """Project Planner PDF generation endpoint tests"""

    def test_pdf_returns_application_pdf_content_type(self):
        """Test PDF endpoint returns application/pdf"""
        response = requests.post(
            f"{BASE_URL}/api/project-planner/pdf",
            json={
                "width": 4.0,
                "height": 2.5,
                "viewing_distance": 5.0,
                "name": "TEST_User",
                "email": "test@example.com"
            }
        )
        assert response.status_code == 200
        assert "application/pdf" in response.headers.get("Content-Type", "")

    def test_pdf_returns_non_empty_content(self):
        """Test PDF endpoint returns actual PDF content"""
        response = requests.post(
            f"{BASE_URL}/api/project-planner/pdf",
            json={
                "width": 4.0,
                "height": 2.5,
                "viewing_distance": 5.0,
                "name": "TEST_User",
                "email": "test@example.com"
            }
        )
        assert len(response.content) > 1000, "PDF should be larger than 1KB"
        # PDF files start with %PDF
        assert response.content[:4] == b'%PDF', "Content should be a PDF file"

    def test_pdf_generates_without_lead_info(self):
        """Test PDF generates even without lead info (no name/email)"""
        response = requests.post(
            f"{BASE_URL}/api/project-planner/pdf",
            json={
                "width": 4.0,
                "height": 2.5,
                "viewing_distance": 5.0
            }
        )
        assert response.status_code == 200
        assert "application/pdf" in response.headers.get("Content-Type", "")


class TestSitemapIntegration:
    """Test that sitemap includes new pages"""

    def test_sitemap_includes_project_planner(self):
        """Test sitemap includes /project-planner URL"""
        response = requests.get(f"{BASE_URL}/api/sitemap.xml")
        assert response.status_code == 200
        assert "/project-planner" in response.text

    def test_sitemap_includes_installation_guide(self):
        """Test sitemap includes /installation-guide URL"""
        response = requests.get(f"{BASE_URL}/api/sitemap.xml")
        assert response.status_code == 200
        assert "/installation-guide" in response.text


class TestHealthCheck:
    """Basic health check"""

    def test_health_check(self):
        """Test health endpoint is accessible"""
        response = requests.get(f"{BASE_URL}/api/health")
        assert response.status_code == 200
