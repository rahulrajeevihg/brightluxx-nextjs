"""
Test sub-category filtering for art-immersive products
Tests the new sub_category query parameter added to /api/products endpoint
"""
import pytest
import requests
import os

BASE_URL = os.environ.get('REACT_APP_BACKEND_URL', '').rstrip('/')

class TestSubCategoryFiltering:
    """Test sub-category filtering for art-immersive products"""
    
    def test_api_products_nft_gallery_returns_2_products(self):
        """NFT Gallery sub-category should return exactly 2 products"""
        response = requests.get(f"{BASE_URL}/api/products", params={
            "category": "art-immersive",
            "sub_category": "nft-gallery"
        })
        assert response.status_code == 200
        data = response.json()
        products = data.get("products", [])
        print(f"NFT Gallery products: {[p.get('name') for p in products]}")
        assert len(products) == 2, f"Expected 2 NFT Gallery products, got {len(products)}"
        # Verify product names contain expected keywords
        names = [p.get('name', '').lower() for p in products]
        assert any('artframe' in n for n in names), "Expected ArtFrame products in NFT Gallery"
    
    def test_api_products_virtual_production_returns_2_products(self):
        """Virtual Production sub-category should return exactly 2 products"""
        response = requests.get(f"{BASE_URL}/api/products", params={
            "category": "art-immersive",
            "sub_category": "virtual-production"
        })
        assert response.status_code == 200
        data = response.json()
        products = data.get("products", [])
        print(f"Virtual Production products: {[p.get('name') for p in products]}")
        assert len(products) == 2, f"Expected 2 Virtual Production products, got {len(products)}"
        # Verify product names contain expected keywords
        names = [p.get('name', '').lower() for p in products]
        assert any('xr' in n for n in names), "Expected XR products in Virtual Production"
    
    def test_api_products_metaverse_returns_2_products(self):
        """Metaverse sub-category should return exactly 2 products"""
        response = requests.get(f"{BASE_URL}/api/products", params={
            "category": "art-immersive",
            "sub_category": "metaverse"
        })
        assert response.status_code == 200
        data = response.json()
        products = data.get("products", [])
        print(f"Metaverse products: {[p.get('name') for p in products]}")
        assert len(products) == 2, f"Expected 2 Metaverse products, got {len(products)}"
    
    def test_api_products_immersive_experience_returns_2_products(self):
        """Immersive Experience sub-category should return exactly 2 products"""
        response = requests.get(f"{BASE_URL}/api/products", params={
            "category": "art-immersive",
            "sub_category": "immersive-experience"
        })
        assert response.status_code == 200
        data = response.json()
        products = data.get("products", [])
        print(f"Immersive Experience products: {[p.get('name') for p in products]}")
        assert len(products) == 2, f"Expected 2 Immersive Experience products, got {len(products)}"
    
    def test_api_products_sculptural_returns_2_products(self):
        """Sculptural sub-category should return exactly 2 products"""
        response = requests.get(f"{BASE_URL}/api/products", params={
            "category": "art-immersive",
            "sub_category": "sculptural"
        })
        assert response.status_code == 200
        data = response.json()
        products = data.get("products", [])
        print(f"Sculptural products: {[p.get('name') for p in products]}")
        assert len(products) == 2, f"Expected 2 Sculptural products, got {len(products)}"
    
    def test_api_products_public_art_returns_2_products(self):
        """Public Art sub-category should return exactly 2 products"""
        response = requests.get(f"{BASE_URL}/api/products", params={
            "category": "art-immersive",
            "sub_category": "public-art"
        })
        assert response.status_code == 200
        data = response.json()
        products = data.get("products", [])
        print(f"Public Art products: {[p.get('name') for p in products]}")
        assert len(products) == 2, f"Expected 2 Public Art products, got {len(products)}"
    
    def test_api_products_interactive_returns_2_products(self):
        """Interactive sub-category should return exactly 2 products"""
        response = requests.get(f"{BASE_URL}/api/products", params={
            "category": "art-immersive",
            "sub_category": "interactive"
        })
        assert response.status_code == 200
        data = response.json()
        products = data.get("products", [])
        print(f"Interactive products: {[p.get('name') for p in products]}")
        assert len(products) == 2, f"Expected 2 Interactive products, got {len(products)}"
    
    def test_api_products_art_immersive_no_sub_returns_all_14(self):
        """Art-immersive without sub-category should return all 14 products"""
        response = requests.get(f"{BASE_URL}/api/products", params={
            "category": "art-immersive"
        })
        assert response.status_code == 200
        data = response.json()
        products = data.get("products", [])
        print(f"All Art-Immersive products: {len(products)}")
        assert len(products) == 14, f"Expected 14 art-immersive products, got {len(products)}"
    
    def test_api_products_all_returns_products(self):
        """All products endpoint should return products"""
        response = requests.get(f"{BASE_URL}/api/products")
        assert response.status_code == 200
        data = response.json()
        products = data.get("products", [])
        print(f"Total products: {len(products)}")
        assert len(products) > 0, "Expected products to be returned"
    
    def test_homepage_loads(self):
        """Homepage should load correctly"""
        response = requests.get(f"{BASE_URL}/")
        assert response.status_code == 200
        assert len(response.text) > 0


class TestSubCategoryDataIntegrity:
    """Verify sub-category data integrity"""
    
    def test_all_subcategories_sum_to_14(self):
        """Sum of all sub-category products should equal 14"""
        subcategories = [
            'nft-gallery', 'immersive-experience', 'virtual-production',
            'metaverse', 'sculptural', 'public-art', 'interactive'
        ]
        total = 0
        for sub in subcategories:
            response = requests.get(f"{BASE_URL}/api/products", params={
                "category": "art-immersive",
                "sub_category": sub
            })
            assert response.status_code == 200
            products = response.json().get("products", [])
            total += len(products)
            print(f"{sub}: {len(products)} products")
        
        print(f"Total from all subcategories: {total}")
        assert total == 14, f"Expected 14 total products across subcategories, got {total}"
    
    def test_each_subcategory_has_unique_products(self):
        """Each sub-category should have unique products (no duplicates across subcategories)"""
        subcategories = [
            'nft-gallery', 'immersive-experience', 'virtual-production',
            'metaverse', 'sculptural', 'public-art', 'interactive'
        ]
        all_product_ids = []
        for sub in subcategories:
            response = requests.get(f"{BASE_URL}/api/products", params={
                "category": "art-immersive",
                "sub_category": sub
            })
            products = response.json().get("products", [])
            for p in products:
                pid = p.get('id') or p.get('_id')
                all_product_ids.append(pid)
        
        unique_ids = set(all_product_ids)
        print(f"Total product IDs: {len(all_product_ids)}, Unique: {len(unique_ids)}")
        assert len(all_product_ids) == len(unique_ids), "Found duplicate products across subcategories"
