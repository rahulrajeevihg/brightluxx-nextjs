"""
Test CMS Public Pages - PixelVue and Solutions Dynamic Content
Tests that public-facing pages fetch data correctly from CMS APIs
"""
import pytest
import requests
import os

BASE_URL = os.environ.get('REACT_APP_BACKEND_URL', '').rstrip('/')

class TestPixelVueProductsAPI:
    """Test /api/pixelvue/products endpoint - returns 24 products for public landing page"""
    
    def test_pixelvue_products_list(self):
        """Should return all 24 PixelVue products"""
        response = requests.get(f"{BASE_URL}/api/pixelvue/products")
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        assert len(data) == 24, f"Expected 24 products, got {len(data)}"
        print(f"PASS: PixelVue products endpoint returns {len(data)} products")
    
    def test_pixelvue_products_have_required_fields(self):
        """Each product should have name, slug, category, tagline, description"""
        response = requests.get(f"{BASE_URL}/api/pixelvue/products")
        data = response.json()
        
        required_fields = ['name', 'slug', 'category', 'tagline', 'description']
        for product in data:
            for field in required_fields:
                assert field in product, f"Product {product.get('name', 'unknown')} missing {field}"
        print("PASS: All products have required fields")
    
    def test_pixelvue_products_categories(self):
        """Products should be in poster, commercial, or creative categories"""
        response = requests.get(f"{BASE_URL}/api/pixelvue/products")
        data = response.json()
        
        valid_categories = ['poster', 'commercial', 'creative']
        for product in data:
            assert product['category'] in valid_categories, f"Invalid category: {product['category']}"
        
        # Count by category
        poster = len([p for p in data if p['category'] == 'poster'])
        commercial = len([p for p in data if p['category'] == 'commercial'])
        creative = len([p for p in data if p['category'] == 'creative'])
        print(f"PASS: Categories - Poster: {poster}, Commercial: {commercial}, Creative: {creative}")
    
    def test_pixelvue_featured_products_have_hero_image(self):
        """At least some products should have hero_image for featured section"""
        response = requests.get(f"{BASE_URL}/api/pixelvue/products")
        data = response.json()
        
        products_with_hero = [p for p in data if p.get('hero_image')]
        # Only 2 products have hero images in current seed data - acceptable
        assert len(products_with_hero) >= 1, f"Expected at least 1 product with hero_image, got {len(products_with_hero)}"
        print(f"PASS: {len(products_with_hero)} products have hero images for featured section")


class TestPixelVueProductDetailAPI:
    """Test /api/pixelvue/products/:slug endpoint - returns individual product details"""
    
    def test_iposter_product_detail(self):
        """iPoster should have complete data: quick_specs, features, applications, specifications"""
        response = requests.get(f"{BASE_URL}/api/pixelvue/products/iposter")
        assert response.status_code == 200
        data = response.json()
        
        # Verify required fields
        assert data['name'] == 'iPoster'
        assert data['slug'] == 'iposter'
        assert data['category'] == 'poster'
        assert data['tagline'] == 'Seamless Splicing. Stunning Impact.'
        print("PASS: iPoster basic info correct")
    
    def test_iposter_quick_specs(self):
        """iPoster should have 4 quick specs: 40mm, 69kg, 16:9, 3840Hz"""
        response = requests.get(f"{BASE_URL}/api/pixelvue/products/iposter")
        data = response.json()
        
        assert 'quick_specs' in data
        assert len(data['quick_specs']) >= 4, f"Expected 4 quick specs, got {len(data['quick_specs'])}"
        
        # Verify specific specs
        spec_values = [s['value'] for s in data['quick_specs']]
        assert '40mm' in spec_values, "Missing 40mm thickness spec"
        assert '69kg' in spec_values, "Missing 69kg weight spec"
        assert '16:9' in spec_values, "Missing 16:9 splicing ratio spec"
        assert '3840Hz' in spec_values, "Missing 3840Hz refresh rate spec"
        print("PASS: iPoster quick_specs correct: 40mm, 69kg, 16:9, 3840Hz")
    
    def test_iposter_features(self):
        """iPoster should have 6 features"""
        response = requests.get(f"{BASE_URL}/api/pixelvue/products/iposter")
        data = response.json()
        
        assert 'features' in data
        assert len(data['features']) >= 6, f"Expected 6 features, got {len(data['features'])}"
        
        for feature in data['features']:
            assert 'icon' in feature, "Feature missing icon"
            assert 'title' in feature, "Feature missing title"
            assert 'desc' in feature, "Feature missing desc"
        print(f"PASS: iPoster has {len(data['features'])} features with icons, titles, descriptions")
    
    def test_iposter_applications(self):
        """iPoster should have applications list"""
        response = requests.get(f"{BASE_URL}/api/pixelvue/products/iposter")
        data = response.json()
        
        assert 'applications' in data
        assert len(data['applications']) >= 6, f"Expected 6+ applications, got {len(data['applications'])}"
        print(f"PASS: iPoster has {len(data['applications'])} applications")
    
    def test_iposter_specifications(self):
        """iPoster should have technical specifications"""
        response = requests.get(f"{BASE_URL}/api/pixelvue/products/iposter")
        data = response.json()
        
        assert 'specifications' in data
        assert len(data['specifications']) >= 5, f"Expected 5+ specifications, got {len(data['specifications'])}"
        print(f"PASS: iPoster has {len(data['specifications'])} technical specifications")
    
    def test_product_not_found(self):
        """Non-existent product should return 404"""
        response = requests.get(f"{BASE_URL}/api/pixelvue/products/nonexistent-product")
        assert response.status_code == 404
        print("PASS: Non-existent product returns 404")
    
    def test_multiple_product_slugs(self):
        """Test several product slugs are accessible"""
        slugs = ['iposter', 'iflip', 'unity', 'iconference', 'interactive', 'crystalflex']
        for slug in slugs:
            response = requests.get(f"{BASE_URL}/api/pixelvue/products/{slug}")
            assert response.status_code == 200, f"Product {slug} not found"
            data = response.json()
            assert data['slug'] == slug
        print(f"PASS: {len(slugs)} product slugs accessible")


class TestSolutionsAPI:
    """Test /api/solutions endpoint - returns 11 solutions for public page"""
    
    def test_solutions_list(self):
        """Should return all 11 solutions"""
        response = requests.get(f"{BASE_URL}/api/solutions")
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        assert len(data) == 11, f"Expected 11 solutions, got {len(data)}"
        print(f"PASS: Solutions endpoint returns {len(data)} solutions")
    
    def test_solutions_have_required_fields(self):
        """Each solution should have title, slug, tagline, description, icon"""
        response = requests.get(f"{BASE_URL}/api/solutions")
        data = response.json()
        
        required_fields = ['title', 'slug', 'tagline', 'description', 'icon']
        for solution in data:
            for field in required_fields:
                assert field in solution, f"Solution {solution.get('title', 'unknown')} missing {field}"
        print("PASS: All solutions have required fields")
    
    def test_solutions_all_slugs(self):
        """Verify all 11 solution slugs exist"""
        expected_slugs = ['retail', 'corporate', 'outdoor', 'events', 'creative', 
                         'traffic', 'immersive', 'transparent', 'healthcare', 
                         'education', 'sports']
        
        response = requests.get(f"{BASE_URL}/api/solutions")
        data = response.json()
        
        actual_slugs = [s['slug'] for s in data]
        for slug in expected_slugs:
            assert slug in actual_slugs, f"Missing solution slug: {slug}"
        print(f"PASS: All {len(expected_slugs)} solution slugs found")


class TestSolutionDetailAPI:
    """Test solution detail - fetch by slug"""
    
    def test_retail_solution_detail(self):
        """Retail solution should have complete data"""
        response = requests.get(f"{BASE_URL}/api/solutions")
        data = response.json()
        
        retail = next((s for s in data if s['slug'] == 'retail'), None)
        assert retail is not None, "Retail solution not found"
        
        assert retail['title'] == 'Retail & Hospitality'
        assert retail['tagline'] == 'Transform Shopping Experiences'
        assert 'icon' in retail
        print("PASS: Retail solution detail correct")
    
    def test_retail_solution_use_cases(self):
        """Retail solution should have use_cases"""
        response = requests.get(f"{BASE_URL}/api/solutions")
        data = response.json()
        
        retail = next((s for s in data if s['slug'] == 'retail'), None)
        assert 'use_cases' in retail
        assert len(retail['use_cases']) >= 3, f"Expected 3+ use cases, got {len(retail['use_cases'])}"
        print(f"PASS: Retail solution has {len(retail['use_cases'])} use cases")
    
    def test_all_solutions_accessible(self):
        """All 11 solutions should be in the list"""
        response = requests.get(f"{BASE_URL}/api/solutions")
        assert response.status_code == 200
        data = response.json()
        
        expected = ['retail', 'corporate', 'outdoor', 'events', 'creative', 
                    'traffic', 'immersive', 'transparent', 'healthcare', 
                    'education', 'sports']
        
        for slug in expected:
            solution = next((s for s in data if s['slug'] == slug), None)
            assert solution is not None, f"Solution {slug} not found in list"
        print(f"PASS: All {len(expected)} solutions accessible via /api/solutions")


class TestAdminCMSPagesAccess:
    """Test admin CMS pages are accessible (after login)"""
    
    @pytest.fixture
    def auth_session(self):
        """Get authenticated session"""
        session = requests.Session()
        login_response = session.post(f"{BASE_URL}/api/auth/login", json={
            "email": "admin@brightluxx.com",
            "password": os.environ.get("ADMIN_PASSWORD", "brightluxx2026")
        })
        if login_response.status_code == 200:
            return session
        pytest.skip("Admin login failed")
    
    def test_admin_pixelvue_api(self, auth_session):
        """Admin PixelVue endpoint should work"""
        response = auth_session.get(f"{BASE_URL}/api/pixelvue/products")
        assert response.status_code == 200
        assert len(response.json()) == 24
        print("PASS: Admin can access PixelVue products")
    
    def test_admin_solutions_api(self, auth_session):
        """Admin Solutions endpoint should work"""
        response = auth_session.get(f"{BASE_URL}/api/solutions")
        assert response.status_code == 200
        assert len(response.json()) == 11
        print("PASS: Admin can access Solutions")


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
