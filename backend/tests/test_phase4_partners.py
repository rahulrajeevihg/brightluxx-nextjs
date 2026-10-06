"""
Phase 4: Lead Generation & Partnerships API Tests
Tests the 3 new endpoints for:
- Distribution/Franchise Request (/api/franchise-request)
- Supplier Registration (/api/supplier-registration)
- Technical Support (/api/technical-support)
"""
import pytest
import requests
import os
import uuid

BASE_URL = os.environ.get('REACT_APP_BACKEND_URL', '').rstrip('/')


class TestFranchiseRequest:
    """Tests for /api/franchise-request endpoint"""
    
    def test_franchise_request_success(self):
        """Test successful franchise/distribution request submission"""
        payload = {
            "name": f"TEST_FranchiseUser_{uuid.uuid4().hex[:6]}",
            "company": f"TEST_Company_{uuid.uuid4().hex[:6]}",
            "email": f"test_{uuid.uuid4().hex[:6]}@example.com",
            "phone": "+971501234567",
            "country": "UAE",
            "city": "Dubai",
            "business_type": "AV Integrator",
            "experience": "3-5 years",
            "message": "Interested in distribution partnership"
        }
        response = requests.post(f"{BASE_URL}/api/franchise-request", json=payload)
        
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        data = response.json()
        assert data.get("success") == True
        assert "message" in data
        print(f"Franchise request success: {data}")
    
    def test_franchise_request_required_fields_only(self):
        """Test franchise request with only required fields"""
        payload = {
            "name": f"TEST_MinimalUser_{uuid.uuid4().hex[:6]}",
            "company": f"TEST_MinimalCompany",
            "email": f"minimal_{uuid.uuid4().hex[:6]}@example.com",
            "phone": "+971509876543",
            "country": "Saudi Arabia",
            "city": "Riyadh"
        }
        response = requests.post(f"{BASE_URL}/api/franchise-request", json=payload)
        
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        data = response.json()
        assert data.get("success") == True
        print(f"Franchise minimal fields success: {data}")
    
    def test_franchise_request_missing_required_fields(self):
        """Test franchise request fails without required fields"""
        payload = {
            "name": "Incomplete User",
            "email": "incomplete@example.com"
            # Missing: company, phone, country, city
        }
        response = requests.post(f"{BASE_URL}/api/franchise-request", json=payload)
        
        # FastAPI returns 422 for validation errors
        assert response.status_code == 422, f"Expected 422, got {response.status_code}"
        print("Franchise validation error as expected")


class TestSupplierRegistration:
    """Tests for /api/supplier-registration endpoint"""
    
    def test_supplier_registration_success(self):
        """Test successful supplier registration"""
        payload = {
            "company_name": f"TEST_SupplierCo_{uuid.uuid4().hex[:6]}",
            "contact_person": f"TEST_Contact_{uuid.uuid4().hex[:6]}",
            "email": f"supplier_{uuid.uuid4().hex[:6]}@example.com",
            "phone": "+86139012345678",
            "country": "China",
            "product_category": "LED Modules & Components",
            "certifications": "ISO 9001, CE, RoHS",
            "website": "https://test-supplier.example.com",
            "message": "Premium LED module manufacturer"
        }
        response = requests.post(f"{BASE_URL}/api/supplier-registration", json=payload)
        
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        data = response.json()
        assert data.get("success") == True
        assert "message" in data
        print(f"Supplier registration success: {data}")
    
    def test_supplier_registration_required_fields_only(self):
        """Test supplier registration with only required fields"""
        payload = {
            "company_name": f"TEST_MinSupplier_{uuid.uuid4().hex[:6]}",
            "contact_person": "Min Contact",
            "email": f"minsup_{uuid.uuid4().hex[:6]}@example.com",
            "phone": "+81901234567",
            "country": "Japan",
            "product_category": "Power Supplies"
        }
        response = requests.post(f"{BASE_URL}/api/supplier-registration", json=payload)
        
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        data = response.json()
        assert data.get("success") == True
        print(f"Supplier minimal fields success: {data}")
    
    def test_supplier_registration_missing_required_fields(self):
        """Test supplier registration fails without required fields"""
        payload = {
            "company_name": "Incomplete Supplier",
            "email": "incomplete@example.com"
            # Missing: contact_person, phone, country, product_category
        }
        response = requests.post(f"{BASE_URL}/api/supplier-registration", json=payload)
        
        assert response.status_code == 422, f"Expected 422, got {response.status_code}"
        print("Supplier validation error as expected")


class TestTechnicalSupport:
    """Tests for /api/technical-support endpoint"""
    
    def test_technical_support_normal_urgency(self):
        """Test technical support with normal urgency"""
        payload = {
            "name": f"TEST_SupportUser_{uuid.uuid4().hex[:6]}",
            "company": f"TEST_SupportCo_{uuid.uuid4().hex[:6]}",
            "email": f"support_{uuid.uuid4().hex[:6]}@example.com",
            "phone": "+971504567890",
            "product": "BLX P2.5 Indoor Panel",
            "issue_type": "Dead Pixels / LED Failure",
            "description": "Several pixels not lighting up in the center of display",
            "urgency": "normal"
        }
        response = requests.post(f"{BASE_URL}/api/technical-support", json=payload)
        
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        data = response.json()
        assert data.get("success") == True
        assert "message" in data
        print(f"Technical support (normal) success: {data}")
    
    def test_technical_support_priority_urgency(self):
        """Test technical support with priority urgency"""
        payload = {
            "name": f"TEST_PriorityUser_{uuid.uuid4().hex[:6]}",
            "company": "Priority Client Corp",
            "email": f"priority_{uuid.uuid4().hex[:6]}@example.com",
            "phone": "+971505551234",
            "product": "BLX P3.9 Outdoor",
            "issue_type": "Image Quality Issues",
            "description": "Display flickering during daytime hours",
            "urgency": "priority"
        }
        response = requests.post(f"{BASE_URL}/api/technical-support", json=payload)
        
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        data = response.json()
        assert data.get("success") == True
        print(f"Technical support (priority) success: {data}")
    
    def test_technical_support_urgent_urgency(self):
        """Test technical support with urgent/emergency urgency"""
        payload = {
            "name": f"TEST_UrgentUser_{uuid.uuid4().hex[:6]}",
            "company": "Live Event Venue",
            "email": f"urgent_{uuid.uuid4().hex[:6]}@example.com",
            "phone": "+971509999999",
            "product": "BLX P1.8 Premium",
            "issue_type": "Display Not Turning On",
            "description": "URGENT: Main display completely black, event in 2 hours!",
            "urgency": "urgent"
        }
        response = requests.post(f"{BASE_URL}/api/technical-support", json=payload)
        
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        data = response.json()
        assert data.get("success") == True
        print(f"Technical support (urgent) success: {data}")
    
    def test_technical_support_required_fields_only(self):
        """Test technical support with only required fields"""
        payload = {
            "name": f"TEST_MinSupport_{uuid.uuid4().hex[:6]}",
            "company": "Minimal Company",
            "email": f"minsup_{uuid.uuid4().hex[:6]}@example.com",
            "phone": "+971501111111",
            "description": "General support inquiry"
        }
        response = requests.post(f"{BASE_URL}/api/technical-support", json=payload)
        
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        data = response.json()
        assert data.get("success") == True
        print(f"Technical support minimal fields success: {data}")
    
    def test_technical_support_missing_required_fields(self):
        """Test technical support fails without required fields"""
        payload = {
            "name": "Incomplete User",
            "email": "incomplete@example.com"
            # Missing: company, phone, description
        }
        response = requests.post(f"{BASE_URL}/api/technical-support", json=payload)
        
        assert response.status_code == 422, f"Expected 422, got {response.status_code}"
        print("Technical support validation error as expected")


class TestHealthAndIntegration:
    """Health check and integration tests"""
    
    def test_health_endpoint(self):
        """Verify API is healthy"""
        response = requests.get(f"{BASE_URL}/api/health")
        assert response.status_code == 200
        data = response.json()
        assert data.get("status") == "ok"
        print("Health check passed")


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
