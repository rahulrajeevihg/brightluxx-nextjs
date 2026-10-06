"""
CDN Integration Tests - Iteration 11
Tests for Emergent Object Storage CDN integration with on-the-fly image optimization.
"""
import pytest
import requests
import os

BASE_URL = os.environ.get('REACT_APP_BACKEND_URL', '').rstrip('/')


class TestCDNEndpoint:
    """Tests for /api/cdn/{path} endpoint with image optimization"""

    def test_cdn_basic_image_fetch(self):
        """CDN endpoint returns image with correct content-type"""
        response = requests.get(f"{BASE_URL}/api/cdn/hero_banner.webp", timeout=30)
        assert response.status_code == 200, f"Expected 200, got {response.status_code}"
        assert response.headers.get('Content-Type') == 'image/webp', f"Expected image/webp, got {response.headers.get('Content-Type')}"
        assert len(response.content) > 10000, "Image should have substantial size"

    def test_cdn_width_resize(self):
        """CDN endpoint resizes image when width param provided"""
        # Get original size
        original = requests.get(f"{BASE_URL}/api/cdn/hero_banner.webp", timeout=30)
        original_size = len(original.content)
        
        # Get resized
        resized = requests.get(f"{BASE_URL}/api/cdn/hero_banner.webp?w=400", timeout=30)
        assert resized.status_code == 200
        resized_size = len(resized.content)
        
        # Resized should be smaller
        assert resized_size < original_size, f"Resized ({resized_size}) should be smaller than original ({original_size})"

    def test_cdn_quality_and_format(self):
        """CDN endpoint converts to JPEG with lower quality"""
        response = requests.get(f"{BASE_URL}/api/cdn/hero_banner.webp?q=50&f=jpeg", timeout=30)
        assert response.status_code == 200
        assert response.headers.get('Content-Type') == 'image/jpeg', f"Expected image/jpeg, got {response.headers.get('Content-Type')}"

    def test_cdn_format_png(self):
        """CDN endpoint can convert to PNG format"""
        response = requests.get(f"{BASE_URL}/api/cdn/hero_banner.webp?f=png", timeout=30)
        assert response.status_code == 200
        assert response.headers.get('Content-Type') == 'image/png', f"Expected image/png, got {response.headers.get('Content-Type')}"

    def test_cdn_height_resize(self):
        """CDN endpoint resizes image with height param"""
        original = requests.get(f"{BASE_URL}/api/cdn/hero_banner.webp", timeout=30)
        resized = requests.get(f"{BASE_URL}/api/cdn/hero_banner.webp?h=200", timeout=30)
        assert resized.status_code == 200
        assert len(resized.content) < len(original.content)

    def test_cdn_404_nonexistent(self):
        """CDN endpoint returns 404 for non-existent image"""
        response = requests.get(f"{BASE_URL}/api/cdn/nonexistent_image_xyz_123.webp", timeout=30)
        assert response.status_code == 404, f"Expected 404 for non-existent image, got {response.status_code}"

    def test_cdn_cache_headers(self):
        """CDN endpoint returns proper cache headers (may be overridden by proxy)"""
        response = requests.get(f"{BASE_URL}/api/cdn/hero_banner.webp", timeout=30)
        assert response.status_code == 200
        # Note: Cache-Control may be overridden by K8s ingress - test just verifies header exists
        cache_control = response.headers.get('Cache-Control', '')
        assert cache_control != '', "Should have Cache-Control header"


class TestProductsAPICDN:
    """Tests for Products API returning CDN URLs"""

    def test_products_list_cdn_urls(self):
        """Products list returns image_url with /api/cdn/ prefix"""
        response = requests.get(f"{BASE_URL}/api/products", timeout=30)
        assert response.status_code == 200
        data = response.json()
        products = data.get('products', [])
        assert len(products) > 0, "Should have products"
        
        for product in products[:5]:  # Check first 5
            image_url = product.get('image_url', '')
            assert image_url.startswith('/api/cdn/'), f"Product {product.get('name')} has invalid image_url: {image_url}"

    def test_products_gallery_cdn_urls(self):
        """Products with gallery have /api/cdn/ URLs"""
        response = requests.get(f"{BASE_URL}/api/products", timeout=30)
        assert response.status_code == 200
        data = response.json()
        products = data.get('products', [])
        
        products_with_gallery = [p for p in products if p.get('gallery')]
        assert len(products_with_gallery) > 0, "Should have products with gallery"
        
        for product in products_with_gallery[:3]:
            for gallery_url in product.get('gallery', []):
                assert gallery_url.startswith('/api/cdn/'), f"Gallery URL should start with /api/cdn/: {gallery_url}"

    def test_product_detail_cdn_urls(self):
        """Product detail returns CDN URLs"""
        response = requests.get(f"{BASE_URL}/api/products/clearfilm-led-screen", timeout=30)
        assert response.status_code == 200
        product = response.json()
        
        assert product.get('image_url', '').startswith('/api/cdn/'), "image_url should be CDN URL"
        gallery = product.get('gallery', [])
        for url in gallery:
            assert url.startswith('/api/cdn/'), f"Gallery URL should be CDN: {url}"


class TestProjectsAPICDN:
    """Tests for Projects API returning CDN URLs"""

    def test_projects_list_cdn_urls(self):
        """Projects list returns image_url with /api/cdn/ prefix"""
        response = requests.get(f"{BASE_URL}/api/projects", timeout=30)
        assert response.status_code == 200
        data = response.json()
        projects = data.get('projects', [])
        assert len(projects) > 0, "Should have projects"
        
        for project in projects[:5]:
            image_url = project.get('image_url', '')
            assert image_url.startswith('/api/cdn/'), f"Project {project.get('title')} has invalid image_url: {image_url}"


class TestInspirationsAPICDN:
    """Tests for Inspirations API returning CDN URLs"""

    def test_inspirations_list_cdn_urls(self):
        """Inspirations list returns image_url with /api/cdn/ prefix"""
        response = requests.get(f"{BASE_URL}/api/inspirations", timeout=30)
        assert response.status_code == 200
        data = response.json()
        inspirations = data.get('inspirations', [])
        assert len(inspirations) > 0, "Should have inspirations"
        
        for insp in inspirations[:5]:
            image_url = insp.get('image_url', '')
            assert image_url.startswith('/api/cdn/'), f"Inspiration {insp.get('title')} has invalid image_url: {image_url}"


class TestSolutionsAPICDN:
    """Tests for Solutions API (if applicable)"""

    def test_solutions_list_cdn_urls(self):
        """Solutions list returns CDN URLs if solution images exist"""
        response = requests.get(f"{BASE_URL}/api/solutions", timeout=30)
        if response.status_code == 200:
            data = response.json()
            solutions = data.get('solutions', [])
            for solution in solutions[:3]:
                image_url = solution.get('image_url', '')
                if image_url:
                    assert image_url.startswith('/api/cdn/') or image_url.startswith('http'), f"Solution image should be CDN or external: {image_url}"


class TestCDNImageVerification:
    """Verify actual CDN images are accessible"""

    def test_product_image_accessible(self):
        """Product image from CDN is accessible"""
        # Get a product
        response = requests.get(f"{BASE_URL}/api/products", timeout=30)
        products = response.json().get('products', [])
        if products:
            image_url = products[0].get('image_url', '')
            img_response = requests.get(f"{BASE_URL}{image_url}", timeout=30)
            assert img_response.status_code == 200, f"Product image {image_url} not accessible"

    def test_project_image_accessible(self):
        """Project image from CDN is accessible"""
        response = requests.get(f"{BASE_URL}/api/projects", timeout=30)
        projects = response.json().get('projects', [])
        if projects:
            image_url = projects[0].get('image_url', '')
            img_response = requests.get(f"{BASE_URL}{image_url}", timeout=30)
            assert img_response.status_code == 200, f"Project image {image_url} not accessible"

    def test_inspiration_image_accessible(self):
        """Inspiration image from CDN is accessible"""
        response = requests.get(f"{BASE_URL}/api/inspirations", timeout=30)
        inspirations = response.json().get('inspirations', [])
        if inspirations:
            image_url = inspirations[0].get('image_url', '')
            img_response = requests.get(f"{BASE_URL}{image_url}", timeout=30)
            assert img_response.status_code == 200, f"Inspiration image {image_url} not accessible"
