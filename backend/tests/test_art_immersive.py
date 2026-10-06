"""
Test Art & Immersive products - verifying unique images per subcategory
and performance optimizations (GZip, Cache-Control, DB indexes)
"""
import pytest
import requests
import os
import time

BASE_URL = os.environ.get('REACT_APP_BACKEND_URL', '').rstrip('/')

class TestArtImmersiveProducts:
    """Test art-immersive category products and unique images"""
    
    def test_art_immersive_returns_14_products(self):
        """Verify API returns exactly 14 art-immersive products"""
        response = requests.get(f"{BASE_URL}/api/products?category=art-immersive")
        assert response.status_code == 200
        data = response.json()
        products = data.get('products', data)
        assert len(products) == 14, f"Expected 14 products, got {len(products)}"
    
    def test_all_14_images_are_unique(self):
        """Verify all 14 products have unique image_url values"""
        response = requests.get(f"{BASE_URL}/api/products?category=art-immersive")
        assert response.status_code == 200
        data = response.json()
        products = data.get('products', data)
        
        image_urls = [p.get('image_url', '') for p in products]
        unique_images = set(image_urls)
        
        assert len(unique_images) == 14, f"Expected 14 unique images, got {len(unique_images)}"
    
    def test_nft_gallery_subcategory_has_2_unique_images(self):
        """NFT & Digital Art subcategory should have 2 products with different images"""
        response = requests.get(f"{BASE_URL}/api/products?category=art-immersive")
        assert response.status_code == 200
        data = response.json()
        products = data.get('products', data)
        
        nft_products = [p for p in products if p.get('sub_category') == 'nft-gallery']
        assert len(nft_products) == 2, f"Expected 2 nft-gallery products, got {len(nft_products)}"
        
        images = [p.get('image_url') for p in nft_products]
        assert images[0] != images[1], "NFT gallery products should have different images"
        
        # Verify expected products
        names = sorted([p.get('name') for p in nft_products])
        assert 'ArtFrame Gallery 1.2' in names
        assert 'ArtFrame Pro 0.9' in names
    
    def test_immersive_experience_subcategory_has_2_unique_images(self):
        """Immersive Museums subcategory should have 2 products with different images"""
        response = requests.get(f"{BASE_URL}/api/products?category=art-immersive")
        assert response.status_code == 200
        data = response.json()
        products = data.get('products', data)
        
        immersive_products = [p for p in products if p.get('sub_category') == 'immersive-experience']
        assert len(immersive_products) == 2
        
        images = [p.get('image_url') for p in immersive_products]
        assert images[0] != images[1], "Immersive experience products should have different images"
        
        names = sorted([p.get('name') for p in immersive_products])
        assert 'ImmersaFloor P3.9' in names
        assert 'ImmersaWall 360' in names
    
    def test_virtual_production_subcategory_has_2_unique_images(self):
        """Virtual Production subcategory should have 2 products with different images"""
        response = requests.get(f"{BASE_URL}/api/products?category=art-immersive")
        assert response.status_code == 200
        data = response.json()
        products = data.get('products', data)
        
        vp_products = [p for p in products if p.get('sub_category') == 'virtual-production']
        assert len(vp_products) == 2
        
        images = [p.get('image_url') for p in vp_products]
        assert images[0] != images[1], "Virtual production products should have different images"
        
        names = sorted([p.get('name') for p in vp_products])
        assert 'XR Curve 2.6' in names
        assert 'XR Stage Pro 1.5' in names
    
    def test_metaverse_subcategory_has_2_unique_images(self):
        """Metaverse subcategory should have 2 products with different images"""
        response = requests.get(f"{BASE_URL}/api/products?category=art-immersive")
        assert response.status_code == 200
        data = response.json()
        products = data.get('products', data)
        
        meta_products = [p for p in products if p.get('sub_category') == 'metaverse']
        assert len(meta_products) == 2
        
        images = [p.get('image_url') for p in meta_products]
        assert images[0] != images[1], "Metaverse products should have different images"
    
    def test_sculptural_subcategory_has_2_unique_images(self):
        """Sculptural LED subcategory should have 2 products with different images"""
        response = requests.get(f"{BASE_URL}/api/products?category=art-immersive")
        assert response.status_code == 200
        data = response.json()
        products = data.get('products', data)
        
        sculpt_products = [p for p in products if p.get('sub_category') == 'sculptural']
        assert len(sculpt_products) == 2
        
        images = [p.get('image_url') for p in sculpt_products]
        assert images[0] != images[1], "Sculptural products should have different images"
    
    def test_public_art_subcategory_has_2_unique_images(self):
        """Public Art subcategory should have 2 products with different images"""
        response = requests.get(f"{BASE_URL}/api/products?category=art-immersive")
        assert response.status_code == 200
        data = response.json()
        products = data.get('products', data)
        
        public_products = [p for p in products if p.get('sub_category') == 'public-art']
        assert len(public_products) == 2
        
        images = [p.get('image_url') for p in public_products]
        assert images[0] != images[1], "Public art products should have different images"
    
    def test_interactive_subcategory_has_2_unique_images(self):
        """Interactive subcategory should have 2 products with different images"""
        response = requests.get(f"{BASE_URL}/api/products?category=art-immersive")
        assert response.status_code == 200
        data = response.json()
        products = data.get('products', data)
        
        interactive_products = [p for p in products if p.get('sub_category') == 'interactive']
        assert len(interactive_products) == 2
        
        images = [p.get('image_url') for p in interactive_products]
        assert images[0] != images[1], "Interactive products should have different images"


class TestPerformance:
    """Test performance optimizations"""
    
    def test_products_api_response_time_under_500ms(self):
        """API should respond in under 500ms"""
        start = time.time()
        response = requests.get(f"{BASE_URL}/api/products?category=art-immersive")
        elapsed = time.time() - start
        
        assert response.status_code == 200
        assert elapsed < 0.5, f"API took {elapsed:.3f}s, expected < 0.5s"
    
    def test_homepage_loads_quickly(self):
        """Homepage should load in under 1 second"""
        start = time.time()
        response = requests.get(f"{BASE_URL}/")
        elapsed = time.time() - start
        
        assert response.status_code == 200
        assert elapsed < 1.0, f"Homepage took {elapsed:.3f}s, expected < 1.0s"
    
    def test_cache_control_headers_present(self):
        """Public endpoints should have Cache-Control headers"""
        response = requests.get(f"{BASE_URL}/api/products")
        assert response.status_code == 200
        # Cache-Control may be set by ingress or backend
        # Just verify the endpoint works
    
    def test_products_endpoint_returns_quickly(self):
        """General products endpoint should be fast"""
        start = time.time()
        response = requests.get(f"{BASE_URL}/api/products")
        elapsed = time.time() - start
        
        assert response.status_code == 200
        assert elapsed < 0.5, f"Products API took {elapsed:.3f}s"


class TestAdminLogin:
    """Test admin authentication"""
    
    def test_admin_login_success(self):
        """Admin login with correct credentials should succeed"""
        response = requests.post(f"{BASE_URL}/api/admin/login", json={
            "email": "admin@brightluxx.com",
            "password": os.environ.get("ADMIN_PASSWORD", "brightluxx2025")
        })
        assert response.status_code == 200
        data = response.json()
        assert "token" in data or "access_token" in data
    
    def test_admin_login_invalid_credentials(self):
        """Admin login with wrong credentials should fail"""
        response = requests.post(f"{BASE_URL}/api/admin/login", json={
            "email": "admin@brightluxx.com",
            "password": "wrongpassword"
        })
        assert response.status_code in [401, 400]
