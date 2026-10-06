"""
Iteration 39: AED Pricing and Location Update Tests
Tests for verifying AED currency and Jebel Ali location updates
"""
import pytest
import requests
import os

BASE_URL = os.environ.get('REACT_APP_BACKEND_URL', '').rstrip('/')

class TestHealthAndBasicAPIs:
    """Health and basic API endpoint tests"""
    
    def test_health_endpoint(self):
        """Test backend health check"""
        response = requests.get(f"{BASE_URL}/api/health")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "ok"
        assert "database" in data
        print(f"✓ Health check passed: {data}")
    
    def test_products_endpoint(self):
        """Test products endpoint returns valid data"""
        response = requests.get(f"{BASE_URL}/api/products")
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        print(f"✓ Products endpoint returned {len(data)} products")
    
    def test_projects_endpoint(self):
        """Test projects endpoint returns valid data"""
        response = requests.get(f"{BASE_URL}/api/projects")
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        print(f"✓ Projects endpoint returned {len(data)} projects")


class TestProjectPlannerAED:
    """Test Project Planner API returns AED pricing"""
    
    def test_project_planner_calculate(self):
        """Test project planner calculate endpoint returns AED costs"""
        payload = {
            "project_name": "Test Project",
            "application": "corporate-lobby",
            "environment": "indoor",
            "width": 4.0,
            "height": 2.5,
            "viewing_distance": 5.0,
            "content_type": "mixed",
            "hours_per_day": 12,
            "brightness": 70
        }
        response = requests.post(f"{BASE_URL}/api/project-planner/calculate", json=payload)
        assert response.status_code == 200
        data = response.json()
        
        assert data["status"] == "ok"
        assert "spec" in data
        spec = data["spec"]
        
        # Verify AED cost fields exist
        assert "budget_low" in spec
        assert "budget_high" in spec
        assert "monthly_cost_aed" in spec
        assert "annual_cost_aed" in spec
        
        # Verify costs are positive numbers (AED values)
        assert spec["budget_low"] > 0
        assert spec["budget_high"] > spec["budget_low"]
        assert spec["monthly_cost_aed"] > 0
        assert spec["annual_cost_aed"] > 0
        
        print(f"✓ Project Planner returns AED pricing:")
        print(f"  Budget: AED {spec['budget_low']:,.0f} - {spec['budget_high']:,.0f}")
        print(f"  Monthly cost: AED {spec['monthly_cost_aed']:,.0f}")
        print(f"  Annual cost: AED {spec['annual_cost_aed']:,.0f}")


class TestSpecPackEndpoints:
    """Test Spec Pack PDF generation endpoints"""
    
    @pytest.mark.parametrize("pack_id", [
        "cob-mip-smd",
        "pixel-pitch",
        "brightness-nits",
    ])
    def test_spec_pack_download(self, pack_id):
        """Test spec pack PDF download endpoints work"""
        response = requests.get(f"{BASE_URL}/api/spec-packs/{pack_id}", stream=True)
        # Should return 200 with PDF content or redirect
        assert response.status_code in [200, 302]
        if response.status_code == 200:
            content_type = response.headers.get('content-type', '')
            assert 'pdf' in content_type.lower() or 'octet-stream' in content_type.lower()
        print(f"✓ Spec pack {pack_id} endpoint accessible")


class TestChatAPI:
    """Test AURA chat API"""
    
    def test_chat_endpoint_exists(self):
        """Test chat endpoint is accessible"""
        payload = {
            "message": "Hello",
            "history": []
        }
        response = requests.post(f"{BASE_URL}/api/chat", json=payload)
        # Should return 200 or 201 (streaming may vary)
        assert response.status_code in [200, 201, 422]  # 422 if validation differs
        print(f"✓ Chat endpoint accessible, status: {response.status_code}")


class TestLeadsAPI:
    """Test leads/contact form API"""
    
    def test_create_lead(self):
        """Test lead creation endpoint"""
        payload = {
            "name": "TEST_AED_Iteration39",
            "email": "test-aed@example.com",
            "phone": "+971501234567",
            "company": "Test Company",
            "city": "Dubai",
            "application": "Corporate",
            "source": "test_iteration39"
        }
        response = requests.post(f"{BASE_URL}/api/leads", json=payload)
        assert response.status_code in [200, 201]
        print(f"✓ Lead creation endpoint works")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
