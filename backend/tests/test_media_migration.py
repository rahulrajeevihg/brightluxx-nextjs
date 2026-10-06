"""
Test media migration to external server (https://files.ihgbrands.com/brightluxx).
Tests CDN endpoint redirects, image transformations, and external server accessibility.
"""
import pytest
import requests
import os

BASE_URL = os.environ.get('REACT_APP_BACKEND_URL').rstrip('/')
EXTERNAL_CDN = "https://files.ihgbrands.com/brightluxx"

class TestExternalServerConnectivity:
    """Tests that the external file server is accessible and returns correct content types."""
    
    def test_external_hero_video_1_accessible(self):
        """Hero video 1 is accessible on external server."""
        url = f"{EXTERNAL_CDN}/videos/hero-video-1.mp4"
        response = requests.head(url, timeout=10)
        assert response.status_code == 200, f"Hero video 1 not accessible: {response.status_code}"
        assert response.headers.get('content-type') == 'video/mp4', f"Unexpected content-type: {response.headers.get('content-type')}"
        print(f"✓ Hero video 1 accessible, size: {response.headers.get('content-length')} bytes")
    
    def test_external_hero_video_2_accessible(self):
        """Hero video 2 is accessible on external server."""
        url = f"{EXTERNAL_CDN}/videos/hero-video-2.mp4"
        response = requests.head(url, timeout=10)
        assert response.status_code == 200, f"Hero video 2 not accessible: {response.status_code}"
        assert response.headers.get('content-type') == 'video/mp4', f"Unexpected content-type: {response.headers.get('content-type')}"
        print(f"✓ Hero video 2 accessible, size: {response.headers.get('content-length')} bytes")
    
    def test_external_hero_banner_image_accessible(self):
        """Hero banner image accessible on external server at /uploads/ path."""
        url = f"{EXTERNAL_CDN}/uploads/hero_banner.webp"
        response = requests.head(url, timeout=10)
        assert response.status_code == 200, f"Hero banner not accessible: {response.status_code}"
        assert 'image' in response.headers.get('content-type', ''), f"Unexpected content-type: {response.headers.get('content-type')}"
        print(f"✓ Hero banner accessible, size: {response.headers.get('content-length')} bytes")
    
    def test_external_product_image_accessible(self):
        """Product image (cob_microled_1.webp) accessible on external server."""
        url = f"{EXTERNAL_CDN}/uploads/cob_microled_1.webp"
        response = requests.head(url, timeout=10)
        assert response.status_code == 200, f"Product image not accessible: {response.status_code}"
        print(f"✓ Product image accessible, size: {response.headers.get('content-length')} bytes")


class TestCDNEndpointRedirect:
    """Tests that CDN endpoint correctly redirects to external server for standard requests."""
    
    def test_cdn_redirect_no_transform(self):
        """CDN endpoint returns 302 redirect when no transformation params."""
        url = f"{BASE_URL}/api/cdn/hero_banner.webp"
        response = requests.head(url, allow_redirects=False, timeout=10)
        assert response.status_code == 302, f"Expected 302 redirect, got: {response.status_code}"
        location = response.headers.get('location', '')
        assert location == f"{EXTERNAL_CDN}/uploads/hero_banner.webp", f"Unexpected redirect location: {location}"
        print(f"✓ CDN redirect to: {location}")
    
    def test_cdn_redirect_for_product_image(self):
        """CDN endpoint redirects product image to external server."""
        url = f"{BASE_URL}/api/cdn/cob_microled_1.webp"
        response = requests.head(url, allow_redirects=False, timeout=10)
        assert response.status_code == 302, f"Expected 302 redirect, got: {response.status_code}"
        location = response.headers.get('location', '')
        assert f"{EXTERNAL_CDN}/uploads/" in location, f"Redirect not pointing to external server: {location}"
        print(f"✓ Product image redirect to: {location}")
    
    def test_cdn_get_request_redirect(self):
        """CDN GET request also returns 302 redirect for standard images."""
        url = f"{BASE_URL}/api/cdn/hero_banner.webp"
        response = requests.get(url, allow_redirects=False, timeout=10)
        assert response.status_code == 302, f"Expected 302 redirect, got: {response.status_code}"
        print(f"✓ CDN GET redirect works correctly")
    
    def test_cdn_follows_redirect_to_external(self):
        """Following the redirect actually returns the image from external server."""
        url = f"{BASE_URL}/api/cdn/hero_banner.webp"
        response = requests.get(url, allow_redirects=True, timeout=15)
        assert response.status_code == 200, f"Failed to fetch image: {response.status_code}"
        assert 'image' in response.headers.get('content-type', ''), f"Unexpected content-type: {response.headers.get('content-type')}"
        assert len(response.content) > 1000, f"Image content too small: {len(response.content)} bytes"
        print(f"✓ Following redirect returns image, size: {len(response.content)} bytes")


class TestCDNTransformations:
    """Tests CDN endpoint with transformation parameters (w, h, q, f)."""
    
    def test_cdn_transform_width_only(self):
        """CDN fetches and transforms when width parameter provided."""
        url = f"{BASE_URL}/api/cdn/hero_banner.webp?w=400"
        response = requests.get(url, timeout=15)
        assert response.status_code == 200, f"Transform failed: {response.status_code}"
        assert 'image' in response.headers.get('content-type', ''), f"Unexpected content-type: {response.headers.get('content-type')}"
        # Transformed image should be smaller than original (79260 bytes)
        assert len(response.content) < 79260, f"Transformed image not smaller than original"
        print(f"✓ Width transform returns image, size: {len(response.content)} bytes")
    
    def test_cdn_transform_width_and_height(self):
        """CDN applies both width and height transformations."""
        url = f"{BASE_URL}/api/cdn/hero_banner.webp?w=300&h=200"
        response = requests.get(url, timeout=15)
        assert response.status_code == 200, f"Transform failed: {response.status_code}"
        assert 'image' in response.headers.get('content-type', '')
        print(f"✓ Width+height transform works, size: {len(response.content)} bytes")
    
    def test_cdn_transform_quality(self):
        """CDN applies quality transformation."""
        url = f"{BASE_URL}/api/cdn/hero_banner.webp?q=50"
        response = requests.get(url, timeout=15)
        assert response.status_code == 200, f"Quality transform failed: {response.status_code}"
        print(f"✓ Quality transform works, size: {len(response.content)} bytes")
    
    def test_cdn_transform_format_jpeg(self):
        """CDN converts to JPEG format when f=jpeg."""
        url = f"{BASE_URL}/api/cdn/hero_banner.webp?f=jpeg&w=400"
        response = requests.get(url, timeout=15)
        assert response.status_code == 200, f"Format transform failed: {response.status_code}"
        content_type = response.headers.get('content-type', '')
        assert 'jpeg' in content_type or 'jpg' in content_type, f"Expected JPEG, got: {content_type}"
        print(f"✓ Format transform to JPEG works, content-type: {content_type}")
    
    def test_cdn_transform_all_params(self):
        """CDN applies all transformation parameters together."""
        url = f"{BASE_URL}/api/cdn/hero_banner.webp?w=200&h=150&q=70&f=webp"
        response = requests.get(url, timeout=15)
        assert response.status_code == 200, f"All params transform failed: {response.status_code}"
        print(f"✓ All params transform works, size: {len(response.content)} bytes")


class TestCDNCacheHeaders:
    """Tests CDN cache headers are set correctly."""
    
    def test_redirect_has_cache_headers(self):
        """Redirect response includes cache-control headers."""
        url = f"{BASE_URL}/api/cdn/hero_banner.webp"
        response = requests.head(url, allow_redirects=False, timeout=10)
        cache_control = response.headers.get('cache-control', '')
        assert 'max-age' in cache_control or 'public' in cache_control, f"Missing cache headers: {cache_control}"
        print(f"✓ Redirect cache-control: {cache_control}")
    
    def test_transform_has_cache_headers(self):
        """Transformed image response includes cache-control headers."""
        url = f"{BASE_URL}/api/cdn/hero_banner.webp?w=400"
        response = requests.get(url, timeout=15)
        cache_control = response.headers.get('cache-control', '')
        assert 'max-age' in cache_control or 'public' in cache_control, f"Missing cache headers: {cache_control}"
        print(f"✓ Transform cache-control: {cache_control}")


class TestProductImagesViaAPI:
    """Tests that product images from API are accessible via CDN."""
    
    def test_products_api_returns_images(self):
        """Products API returns products with image URLs."""
        url = f"{BASE_URL}/api/products"
        response = requests.get(url, timeout=10)
        assert response.status_code == 200, f"Products API failed: {response.status_code}"
        
        data = response.json()
        products = data.get('products', data) if isinstance(data, dict) else data
        assert len(products) > 0, "No products returned"
        
        products_with_images = [p for p in products if p.get('image_url')]
        assert len(products_with_images) == len(products), f"Some products missing images: {len(products_with_images)}/{len(products)}"
        print(f"✓ All {len(products)} products have image_url")
    
    def test_first_5_product_images_accessible(self):
        """First 5 product images are accessible via CDN."""
        url = f"{BASE_URL}/api/products"
        response = requests.get(url, timeout=10)
        data = response.json()
        products = data.get('products', data) if isinstance(data, dict) else data
        
        for i, product in enumerate(products[:5]):
            image_url = product.get('image_url', '')
            if image_url.startswith('/api/cdn/'):
                full_url = f"{BASE_URL}{image_url}"
            else:
                full_url = f"{BASE_URL}/api/cdn/{image_url.lstrip('/')}"
            
            img_response = requests.head(full_url, allow_redirects=False, timeout=10)
            # Should be 302 redirect or 200 if transformation
            assert img_response.status_code in [200, 302], f"Product {i} image not accessible: {img_response.status_code}"
            print(f"✓ Product '{product.get('name', f'#{i}')}' image accessible")


class TestProjectImagesViaAPI:
    """Tests that project/case study images are accessible via CDN."""
    
    def test_projects_api_returns_images(self):
        """Projects API returns projects with image URLs."""
        url = f"{BASE_URL}/api/projects"
        response = requests.get(url, timeout=10)
        assert response.status_code == 200, f"Projects API failed: {response.status_code}"
        
        data = response.json()
        projects = data.get('projects', data) if isinstance(data, dict) else data
        assert len(projects) > 0, "No projects returned"
        
        projects_with_images = [p for p in projects if p.get('image_url')]
        print(f"✓ {len(projects_with_images)}/{len(projects)} projects have image_url")
    
    def test_first_3_project_images_accessible(self):
        """First 3 project images are accessible via CDN."""
        url = f"{BASE_URL}/api/projects"
        response = requests.get(url, timeout=10)
        data = response.json()
        projects = data.get('projects', data) if isinstance(data, dict) else data
        
        for i, project in enumerate(projects[:3]):
            image_url = project.get('image_url', '')
            if not image_url:
                continue
                
            if image_url.startswith('/api/cdn/'):
                full_url = f"{BASE_URL}{image_url}"
            else:
                full_url = f"{BASE_URL}/api/cdn/{image_url.lstrip('/')}"
            
            img_response = requests.head(full_url, allow_redirects=False, timeout=10)
            assert img_response.status_code in [200, 302], f"Project {i} image not accessible: {img_response.status_code}"
            print(f"✓ Project '{project.get('title', f'#{i}')}' image accessible")


class TestCDN404Handling:
    """Tests CDN returns 404 for non-existent images."""
    
    def test_nonexistent_image_returns_404(self):
        """CDN returns 404 for image that doesn't exist on external server."""
        url = f"{BASE_URL}/api/cdn/definitely_nonexistent_image_xyz123.webp"
        response = requests.get(url, timeout=10)
        assert response.status_code == 404, f"Expected 404, got: {response.status_code}"
        print(f"✓ Non-existent image correctly returns 404")
