"""
Tests for Contractor Lead Generation section - iteration 21
Tests: Value Engineering Hub, Contractor SEO pages, Spec Substitution Service
"""
import pytest
import requests
import os
from io import BytesIO

BASE_URL = os.environ.get('REACT_APP_BACKEND_URL', '').rstrip('/')


class TestSpecSubstitutionAPI:
    """POST /api/spec-substitution endpoint tests"""

    def test_spec_substitution_success(self):
        """Test spec substitution submission with valid data"""
        # Multipart form data (not JSON)
        data = {
            'name': 'TEST_John Contractor',
            'email': 'test_contractor@example.com',
            'company': 'TEST_Construction LLC',
            'phone': '+971501234567',
            'projectName': 'TEST_Hotel Lobby LED Wall',
            'description': 'Need P1.5 MiP LED wall 4m x 2.5m for hotel lobby. Original spec is P1.2 COB.',
        }
        
        response = requests.post(f"{BASE_URL}/api/spec-substitution", data=data)
        
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        result = response.json()
        assert result.get('success') == True
        assert 'submission_id' in result
        assert len(result['submission_id']) == 8  # UUID first 8 chars
        print(f"✓ Spec substitution created with submission_id: {result['submission_id']}")

    def test_spec_substitution_with_file_upload(self):
        """Test spec substitution with file attachment"""
        data = {
            'name': 'TEST_Jane Engineer',
            'email': 'test_engineer@example.com',
            'company': 'TEST_AV Integrators',
            'phone': '+971509876543',
            'projectName': 'TEST_Conference Room Display',
            'description': 'Need alternative for P0.9 COB video wall in boardroom',
        }
        
        # Create a test file
        test_file_content = b"This is a test BOQ file content"
        files = {'files': ('TEST_BOQ.pdf', BytesIO(test_file_content), 'application/pdf')}
        
        response = requests.post(f"{BASE_URL}/api/spec-substitution", data=data, files=files)
        
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        result = response.json()
        assert result.get('success') == True
        assert 'submission_id' in result
        print(f"✓ Spec substitution with file upload - submission_id: {result['submission_id']}")

    def test_spec_substitution_minimal_required_fields(self):
        """Test spec substitution with only required fields (name, email, company)"""
        data = {
            'name': 'TEST_Minimal User',
            'email': 'test_minimal@example.com',
            'company': 'TEST_Company',
        }
        
        response = requests.post(f"{BASE_URL}/api/spec-substitution", data=data)
        
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        result = response.json()
        assert result.get('success') == True
        print("✓ Spec substitution works with minimal required fields")

    def test_spec_substitution_missing_required_name(self):
        """Test spec substitution fails without name"""
        data = {
            'email': 'test_noname@example.com',
            'company': 'TEST_Company',
        }
        
        response = requests.post(f"{BASE_URL}/api/spec-substitution", data=data)
        
        # FastAPI Form(...) returns 422 for missing required fields
        assert response.status_code == 422, f"Expected 422 for missing name, got {response.status_code}"
        print("✓ Validation rejects missing name field")

    def test_spec_substitution_missing_required_email(self):
        """Test spec substitution fails without email"""
        data = {
            'name': 'TEST_No Email User',
            'company': 'TEST_Company',
        }
        
        response = requests.post(f"{BASE_URL}/api/spec-substitution", data=data)
        
        assert response.status_code == 422, f"Expected 422 for missing email, got {response.status_code}"
        print("✓ Validation rejects missing email field")

    def test_spec_substitution_missing_required_company(self):
        """Test spec substitution fails without company"""
        data = {
            'name': 'TEST_No Company User',
            'email': 'test_nocompany@example.com',
        }
        
        response = requests.post(f"{BASE_URL}/api/spec-substitution", data=data)
        
        assert response.status_code == 422, f"Expected 422 for missing company, got {response.status_code}"
        print("✓ Validation rejects missing company field")

    def test_spec_substitution_multiple_files(self):
        """Test spec substitution with multiple file attachments (max 5)"""
        data = {
            'name': 'TEST_Multi File User',
            'email': 'test_multifile@example.com',
            'company': 'TEST_Multi Files LLC',
            'projectName': 'TEST_Multi File Project',
        }
        
        # Create multiple test files
        files = [
            ('files', ('TEST_BOQ1.pdf', BytesIO(b"File 1 content"), 'application/pdf')),
            ('files', ('TEST_BOQ2.xlsx', BytesIO(b"File 2 content"), 'application/vnd.ms-excel')),
            ('files', ('TEST_Drawing.dwg', BytesIO(b"File 3 content"), 'application/octet-stream')),
        ]
        
        response = requests.post(f"{BASE_URL}/api/spec-substitution", data=data, files=files)
        
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        result = response.json()
        assert result.get('success') == True
        print("✓ Spec substitution handles multiple file uploads")


class TestHealthEndpoint:
    """Basic health check to ensure API is running"""

    def test_health_check(self):
        """Verify API is healthy"""
        response = requests.get(f"{BASE_URL}/api/health")
        
        assert response.status_code == 200
        data = response.json()
        assert data.get('status') == 'ok'
        print("✓ API health check passed")


class TestExistingAPIsStillWork:
    """Verify contractor feature didn't break existing APIs"""

    def test_specpacks_list_still_works(self):
        """Verify /api/specpacks still returns spec packs"""
        response = requests.get(f"{BASE_URL}/api/specpacks")
        
        assert response.status_code == 200
        data = response.json()
        # Response format is {"packs": [...]}
        assert 'packs' in data
        packs = data['packs']
        assert isinstance(packs, list)
        assert len(packs) > 0
        print(f"✓ /api/specpacks returns {len(packs)} spec packs")

    def test_leads_endpoint_still_works(self):
        """Verify /api/leads still accepts contact form submissions"""
        payload = {
            'name': 'TEST_API Check User',
            'email': 'test_apicheck@example.com',
            'message': 'Testing that existing lead API still works',
        }
        
        response = requests.post(f"{BASE_URL}/api/leads", json=payload)
        
        assert response.status_code == 200
        data = response.json()
        assert data.get('success') == True
        print("✓ /api/leads contact form endpoint still works")
