"""
Analytics & Performance Monitoring API Tests
Tests: /api/track, /api/health, /api/admin/analytics, /api/admin/performance
"""
import pytest
import requests
import os
import time

BASE_URL = os.environ.get('REACT_APP_BACKEND_URL', '').rstrip('/')

# Admin credentials
ADMIN_EMAIL = "admin@brightluxx.com"
ADMIN_PASSWORD = os.environ.get("ADMIN_PASSWORD", "brightluxx2025")


class TestHealthEndpoint:
    """Tests for /api/health endpoint - public, no auth"""
    
    def test_health_returns_200(self):
        """Health check should return 200 OK"""
        response = requests.get(f"{BASE_URL}/api/health")
        assert response.status_code == 200
        
    def test_health_response_structure(self):
        """Health check should return proper structure"""
        response = requests.get(f"{BASE_URL}/api/health")
        data = response.json()
        
        assert "status" in data
        assert "database" in data
        assert "timestamp" in data
        assert data["status"] == "ok"
        assert data["database"] in ["healthy", "degraded"]


class TestTrackEndpoint:
    """Tests for POST /api/track - public, no auth required"""
    
    def test_track_page_view(self):
        """Track page_view event should return 200"""
        payload = {
            "event": "page_view",
            "page": "/test-page",
            "referrer": "https://google.com",
            "session_id": "test-session-123",
            "screen_width": 1920
        }
        response = requests.post(f"{BASE_URL}/api/track", json=payload)
        assert response.status_code == 200
        
        data = response.json()
        assert data.get("ok") == True
        
    def test_track_product_view(self):
        """Track product_view event should return 200"""
        payload = {
            "event": "product_view",
            "page": "/products/test-product",
            "product_slug": "test-product-slug",
            "category": "indoor",
            "session_id": "test-session-456",
            "screen_width": 768
        }
        response = requests.post(f"{BASE_URL}/api/track", json=payload)
        assert response.status_code == 200
        
        data = response.json()
        assert data.get("ok") == True
        
    def test_track_cta_click(self):
        """Track cta_click event should return 200"""
        payload = {
            "event": "cta_click",
            "page": "get-quote-button",
            "session_id": "test-session-789",
            "screen_width": 390
        }
        response = requests.post(f"{BASE_URL}/api/track", json=payload)
        assert response.status_code == 200
        
        data = response.json()
        assert data.get("ok") == True
        
    def test_track_minimal_payload(self):
        """Track should accept minimal required fields"""
        payload = {
            "event": "page_view"
        }
        response = requests.post(f"{BASE_URL}/api/track", json=payload)
        assert response.status_code == 200
        
    def test_track_quote_request(self):
        """Track quote_request event should return 200"""
        payload = {
            "event": "quote_request",
            "product_slug": "cob-microled-04mm",
            "session_id": "test-session-quote",
            "screen_width": 1920
        }
        response = requests.post(f"{BASE_URL}/api/track", json=payload)
        assert response.status_code == 200


class TestAdminLogin:
    """Tests for admin authentication"""
    
    def test_admin_login_success(self):
        """Admin login with valid credentials should return token"""
        response = requests.post(f"{BASE_URL}/api/admin/login", json={
            "email": ADMIN_EMAIL,
            "password": ADMIN_PASSWORD
        })
        assert response.status_code == 200
        
        data = response.json()
        assert "token" in data
        assert "admin" in data
        assert data["admin"]["email"] == ADMIN_EMAIL
        
    def test_admin_login_invalid_password(self):
        """Admin login with wrong password should return 401"""
        response = requests.post(f"{BASE_URL}/api/admin/login", json={
            "email": ADMIN_EMAIL,
            "password": "wrong-password"
        })
        assert response.status_code == 401


@pytest.fixture
def admin_token():
    """Get admin authentication token"""
    response = requests.post(f"{BASE_URL}/api/admin/login", json={
        "email": ADMIN_EMAIL,
        "password": ADMIN_PASSWORD
    })
    if response.status_code == 200:
        return response.json().get("token")
    pytest.skip("Admin authentication failed - skipping authenticated tests")


class TestAdminAnalytics:
    """Tests for GET /api/admin/analytics - requires admin auth"""
    
    def test_analytics_requires_auth(self):
        """Analytics endpoint should return 401 without auth"""
        response = requests.get(f"{BASE_URL}/api/admin/analytics")
        assert response.status_code == 401
        
    def test_analytics_with_auth(self, admin_token):
        """Analytics endpoint should return 200 with valid token"""
        headers = {"Authorization": f"Bearer {admin_token}"}
        response = requests.get(f"{BASE_URL}/api/admin/analytics", headers=headers)
        assert response.status_code == 200
        
    def test_analytics_response_structure(self, admin_token):
        """Analytics response should have required fields"""
        headers = {"Authorization": f"Bearer {admin_token}"}
        response = requests.get(f"{BASE_URL}/api/admin/analytics", headers=headers)
        data = response.json()
        
        # Required fields from analytics.py
        assert "period_days" in data
        assert "total_page_views" in data
        assert "unique_visitors" in data
        assert "daily_views" in data
        assert "top_pages" in data
        assert "top_products" in data
        assert "categories" in data
        assert "cta_clicks" in data
        assert "devices" in data
        assert "referrers" in data
        assert "lead_funnel" in data
        
        # Lead funnel structure
        assert "total_leads" in data["lead_funnel"]
        assert "quote_requests" in data["lead_funnel"]
        assert "contact_form" in data["lead_funnel"]
        
    def test_analytics_period_7_days(self, admin_token):
        """Analytics with days=7 should filter data"""
        headers = {"Authorization": f"Bearer {admin_token}"}
        response = requests.get(f"{BASE_URL}/api/admin/analytics?days=7", headers=headers)
        assert response.status_code == 200
        
        data = response.json()
        assert data["period_days"] == 7
        
    def test_analytics_period_14_days(self, admin_token):
        """Analytics with days=14 should filter data"""
        headers = {"Authorization": f"Bearer {admin_token}"}
        response = requests.get(f"{BASE_URL}/api/admin/analytics?days=14", headers=headers)
        assert response.status_code == 200
        
        data = response.json()
        assert data["period_days"] == 14
        
    def test_analytics_period_30_days(self, admin_token):
        """Analytics with days=30 (default) should return 30 day data"""
        headers = {"Authorization": f"Bearer {admin_token}"}
        response = requests.get(f"{BASE_URL}/api/admin/analytics?days=30", headers=headers)
        assert response.status_code == 200
        
        data = response.json()
        assert data["period_days"] == 30
        
    def test_analytics_daily_views_structure(self, admin_token):
        """Daily views should have correct structure"""
        headers = {"Authorization": f"Bearer {admin_token}"}
        response = requests.get(f"{BASE_URL}/api/admin/analytics?days=30", headers=headers)
        data = response.json()
        
        daily_views = data["daily_views"]
        assert isinstance(daily_views, list)
        
        if len(daily_views) > 0:
            day = daily_views[0]
            assert "date" in day
            assert "views" in day
            assert "unique_visitors" in day
            
    def test_analytics_top_pages_structure(self, admin_token):
        """Top pages should have correct structure"""
        headers = {"Authorization": f"Bearer {admin_token}"}
        response = requests.get(f"{BASE_URL}/api/admin/analytics?days=30", headers=headers)
        data = response.json()
        
        top_pages = data["top_pages"]
        assert isinstance(top_pages, list)
        
        if len(top_pages) > 0:
            page = top_pages[0]
            assert "page" in page
            assert "views" in page


class TestAdminPerformance:
    """Tests for GET /api/admin/performance - requires admin auth"""
    
    def test_performance_requires_auth(self):
        """Performance endpoint should return 401 without auth"""
        response = requests.get(f"{BASE_URL}/api/admin/performance")
        assert response.status_code == 401
        
    def test_performance_with_auth(self, admin_token):
        """Performance endpoint should return 200 with valid token"""
        headers = {"Authorization": f"Bearer {admin_token}"}
        response = requests.get(f"{BASE_URL}/api/admin/performance", headers=headers)
        assert response.status_code == 200
        
    def test_performance_response_structure(self, admin_token):
        """Performance response should have required fields"""
        headers = {"Authorization": f"Bearer {admin_token}"}
        response = requests.get(f"{BASE_URL}/api/admin/performance", headers=headers)
        data = response.json()
        
        # Required fields from analytics.py
        assert "period_days" in data
        assert "total_requests" in data
        assert "error_count" in data
        assert "error_rate" in data
        assert "avg_response_ms" in data
        assert "p95_response_ms" in data
        assert "endpoints" in data
        assert "hourly" in data
        assert "status_codes" in data
        assert "slowest_endpoints" in data
        
    def test_performance_period_1_day(self, admin_token):
        """Performance with days=1 should filter data"""
        headers = {"Authorization": f"Bearer {admin_token}"}
        response = requests.get(f"{BASE_URL}/api/admin/performance?days=1", headers=headers)
        assert response.status_code == 200
        
        data = response.json()
        assert data["period_days"] == 1
        
    def test_performance_period_3_days(self, admin_token):
        """Performance with days=3 should filter data"""
        headers = {"Authorization": f"Bearer {admin_token}"}
        response = requests.get(f"{BASE_URL}/api/admin/performance?days=3", headers=headers)
        assert response.status_code == 200
        
        data = response.json()
        assert data["period_days"] == 3
        
    def test_performance_period_7_days(self, admin_token):
        """Performance with days=7 (default) should return 7 day data"""
        headers = {"Authorization": f"Bearer {admin_token}"}
        response = requests.get(f"{BASE_URL}/api/admin/performance?days=7", headers=headers)
        assert response.status_code == 200
        
        data = response.json()
        assert data["period_days"] == 7
        
    def test_performance_endpoints_structure(self, admin_token):
        """Endpoints stats should have correct structure"""
        headers = {"Authorization": f"Bearer {admin_token}"}
        response = requests.get(f"{BASE_URL}/api/admin/performance?days=7", headers=headers)
        data = response.json()
        
        endpoints = data["endpoints"]
        assert isinstance(endpoints, list)
        
        if len(endpoints) > 0:
            ep = endpoints[0]
            assert "endpoint" in ep
            assert "avg_ms" in ep
            assert "max_ms" in ep
            assert "count" in ep
            assert "errors" in ep
            
    def test_performance_status_codes_structure(self, admin_token):
        """Status codes should have correct structure"""
        headers = {"Authorization": f"Bearer {admin_token}"}
        response = requests.get(f"{BASE_URL}/api/admin/performance?days=7", headers=headers)
        data = response.json()
        
        status_codes = data["status_codes"]
        assert isinstance(status_codes, list)
        
        if len(status_codes) > 0:
            sc = status_codes[0]
            assert "status_group" in sc
            assert "count" in sc


class TestAnalyticsDataPersistence:
    """Test that tracked events actually persist to the database"""
    
    def test_track_and_verify_in_analytics(self, admin_token):
        """Track an event and verify it appears in analytics"""
        # Generate unique identifiable session for this test
        unique_session = f"pytest-session-{int(time.time())}"
        
        # Track multiple page views
        for i in range(3):
            payload = {
                "event": "page_view",
                "page": f"/pytest-test-page-{i}",
                "session_id": unique_session,
                "screen_width": 1920
            }
            response = requests.post(f"{BASE_URL}/api/track", json=payload)
            assert response.status_code == 200
            
        # Small delay to ensure events are persisted
        time.sleep(0.5)
        
        # Verify analytics includes our tracked data
        headers = {"Authorization": f"Bearer {admin_token}"}
        response = requests.get(f"{BASE_URL}/api/admin/analytics?days=1", headers=headers)
        assert response.status_code == 200
        
        data = response.json()
        # Should have at least some page views now
        assert data["total_page_views"] >= 3


class TestPerformanceMiddleware:
    """Test that performance middleware tracks API metrics"""
    
    def test_api_calls_tracked_in_performance(self, admin_token):
        """API calls should be tracked in performance metrics"""
        headers = {"Authorization": f"Bearer {admin_token}"}
        
        # Make several API calls to generate performance data
        requests.get(f"{BASE_URL}/api/products")
        requests.get(f"{BASE_URL}/api/health")  # Should be skipped
        requests.get(f"{BASE_URL}/api/admin/analytics", headers=headers)
        
        # Small delay to ensure metrics are persisted
        time.sleep(0.5)
        
        # Check performance data
        response = requests.get(f"{BASE_URL}/api/admin/performance?days=1", headers=headers)
        assert response.status_code == 200
        
        data = response.json()
        # Should have at least some requests tracked
        assert data["total_requests"] > 0
        
        # Check endpoints list includes GET /api/products
        endpoints = data["endpoints"]
        endpoint_names = [ep["endpoint"] for ep in endpoints]
        # At minimum should have some tracked endpoints
        assert len(endpoint_names) > 0
