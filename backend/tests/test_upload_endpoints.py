"""
Test suite for Admin Upload Endpoints
Tests all upload functionality for the Brightluxx CMS admin panel.
Verifies SFTP uploads to external CDN are working correctly.
"""
import pytest
import requests
import os

BASE_URL = os.environ.get('REACT_APP_BACKEND_URL', '').rstrip('/')

# Test credentials
ADMIN_EMAIL = "admin@brightluxx.com"
ADMIN_PASSWORD = os.environ.get("ADMIN_PASSWORD", "brightluxx2025")


@pytest.fixture(scope="module")
def admin_token():
    """Get admin authentication token."""
    response = requests.post(
        f"{BASE_URL}/api/admin/login",
        json={"email": ADMIN_EMAIL, "password": ADMIN_PASSWORD}
    )
    assert response.status_code == 200, f"Admin login failed: {response.text}"
    data = response.json()
    assert "token" in data, "No token in login response"
    return data["token"]


@pytest.fixture
def auth_headers(admin_token):
    """Return headers with admin auth token."""
    return {"Authorization": f"Bearer {admin_token}"}


@pytest.fixture
def test_image():
    """Create a minimal test PNG image (1x1 pixel)."""
    import base64
    # 1x1 pixel PNG
    png_data = base64.b64decode(
        'iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mNk+M9QDwADhgGAWjR9awAAAABJRU5ErkJggg=='
    )
    return ("test_image.png", png_data, "image/png")


@pytest.fixture
def test_pdf():
    """Create a minimal test PDF file."""
    pdf_content = b"""%PDF-1.4
1 0 obj<</Type/Catalog/Pages 2 0 R>>endobj
2 0 obj<</Type/Pages/Kids[3 0 R]/Count 1>>endobj
3 0 obj<</Type/Page/MediaBox[0 0 612 792]/Parent 2 0 R>>endobj
xref
0 4
0000000000 65535 f 
0000000009 00000 n 
0000000052 00000 n 
0000000101 00000 n 
trailer<</Size 4/Root 1 0 R>>
startxref
170
%%EOF"""
    return ("test_file.pdf", pdf_content, "application/pdf")


class TestAdminLogin:
    """Test admin authentication."""
    
    def test_admin_login_success(self):
        """Test successful admin login."""
        response = requests.post(
            f"{BASE_URL}/api/admin/login",
            json={"email": ADMIN_EMAIL, "password": ADMIN_PASSWORD}
        )
        assert response.status_code == 200
        data = response.json()
        assert "token" in data
        assert "admin" in data
        assert data["admin"]["email"] == ADMIN_EMAIL
        print(f"SUCCESS: Admin login returned token")
    
    def test_admin_login_invalid_credentials(self):
        """Test login with invalid credentials."""
        response = requests.post(
            f"{BASE_URL}/api/admin/login",
            json={"email": "wrong@example.com", "password": "wrongpass"}
        )
        assert response.status_code in [401, 403]
        print(f"SUCCESS: Invalid login rejected with status {response.status_code}")


class TestMainUploadEndpoint:
    """Test /api/admin/upload endpoint - main image upload."""
    
    def test_upload_image_success(self, auth_headers, test_image):
        """Test successful image upload to CDN."""
        filename, content, content_type = test_image
        files = {"file": (filename, content, content_type)}
        
        response = requests.post(
            f"{BASE_URL}/api/admin/upload",
            headers=auth_headers,
            files=files
        )
        
        assert response.status_code == 200, f"Upload failed: {response.text}"
        data = response.json()
        
        # Verify response structure
        assert data.get("success") == True, "success should be True"
        assert "url" in data, "Response should contain url"
        assert data["url"].startswith("https://files.ihgbrands.com/brightluxx/"), \
            f"URL should be CDN URL, got: {data['url']}"
        
        print(f"SUCCESS: Image uploaded to CDN: {data['url']}")
    
    def test_upload_without_auth(self, test_image):
        """Test upload without authentication fails."""
        filename, content, content_type = test_image
        files = {"file": (filename, content, content_type)}
        
        response = requests.post(
            f"{BASE_URL}/api/admin/upload",
            files=files
        )
        
        assert response.status_code in [401, 403], \
            f"Expected 401/403, got {response.status_code}"
        print(f"SUCCESS: Unauthenticated upload rejected")
    
    def test_upload_invalid_file_type(self, auth_headers):
        """Test upload with invalid file type fails."""
        files = {"file": ("test.exe", b"fake executable", "application/x-msdownload")}
        
        response = requests.post(
            f"{BASE_URL}/api/admin/upload",
            headers=auth_headers,
            files=files
        )
        
        assert response.status_code == 400, \
            f"Expected 400 for invalid file type, got {response.status_code}"
        print(f"SUCCESS: Invalid file type rejected")


class TestCaseStudiesUpload:
    """Test /api/admin/case-studies/upload-image endpoint."""
    
    def test_case_study_image_upload(self, auth_headers, test_image):
        """Test case study image upload."""
        filename, content, content_type = test_image
        files = {"file": (filename, content, content_type)}
        
        response = requests.post(
            f"{BASE_URL}/api/admin/case-studies/upload-image",
            headers=auth_headers,
            files=files
        )
        
        assert response.status_code == 200, f"Upload failed: {response.text}"
        data = response.json()
        
        assert data.get("success") == True
        assert "image_url" in data, "Response should contain image_url"
        assert "case-studies" in data["image_url"], \
            f"URL should contain 'case-studies', got: {data['image_url']}"
        
        print(f"SUCCESS: Case study image uploaded: {data['image_url']}")


class TestBlogUpload:
    """Test /api/admin/blogs/upload-image endpoint."""
    
    def test_blog_image_upload(self, auth_headers, test_image):
        """Test blog image upload."""
        filename, content, content_type = test_image
        files = {"file": (filename, content, content_type)}
        
        response = requests.post(
            f"{BASE_URL}/api/admin/blogs/upload-image",
            headers=auth_headers,
            files=files
        )
        
        assert response.status_code == 200, f"Upload failed: {response.text}"
        data = response.json()
        
        assert data.get("success") == True
        assert "image_url" in data, "Response should contain image_url"
        assert "blog" in data["image_url"], \
            f"URL should contain 'blog', got: {data['image_url']}"
        
        print(f"SUCCESS: Blog image uploaded: {data['image_url']}")


class TestHomepageUpload:
    """Test /api/admin/homepage/upload-image endpoint."""
    
    def test_homepage_image_upload(self, auth_headers, test_image):
        """Test homepage image upload."""
        filename, content, content_type = test_image
        files = {"file": (filename, content, content_type)}
        
        response = requests.post(
            f"{BASE_URL}/api/admin/homepage/upload-image",
            headers=auth_headers,
            files=files
        )
        
        assert response.status_code == 200, f"Upload failed: {response.text}"
        data = response.json()
        
        assert data.get("success") == True
        assert "url" in data, "Response should contain url"
        assert "homepage" in data["url"], \
            f"URL should contain 'homepage', got: {data['url']}"
        
        print(f"SUCCESS: Homepage image uploaded: {data['url']}")


class TestResourcesUpload:
    """Test /api/admin/resources/upload endpoint."""
    
    def test_resource_pdf_upload(self, auth_headers, test_pdf):
        """Test resource PDF upload."""
        filename, content, content_type = test_pdf
        files = {"file": (filename, content, content_type)}
        
        response = requests.post(
            f"{BASE_URL}/api/admin/resources/upload",
            headers=auth_headers,
            files=files
        )
        
        assert response.status_code == 200, f"Upload failed: {response.text}"
        data = response.json()
        
        assert data.get("success") == True
        assert "file_url" in data, "Response should contain file_url"
        assert "resources" in data["file_url"], \
            f"URL should contain 'resources', got: {data['file_url']}"
        
        print(f"SUCCESS: Resource PDF uploaded: {data['file_url']}")


class TestMultipleUpload:
    """Test /api/admin/upload/multiple endpoint."""
    
    def test_multiple_image_upload(self, auth_headers, test_image):
        """Test multiple image upload."""
        filename, content, content_type = test_image
        files = [
            ("files", (f"test1_{filename}", content, content_type)),
            ("files", (f"test2_{filename}", content, content_type)),
        ]
        
        response = requests.post(
            f"{BASE_URL}/api/admin/upload/multiple",
            headers=auth_headers,
            files=files
        )
        
        assert response.status_code == 200, f"Upload failed: {response.text}"
        data = response.json()
        
        assert data.get("success") == True
        assert "uploaded" in data
        assert data.get("count", 0) >= 1, "Should have uploaded at least 1 file"
        
        print(f"SUCCESS: Multiple images uploaded, count: {data.get('count')}")


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
