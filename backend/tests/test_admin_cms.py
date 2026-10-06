"""
Admin CMS API Tests - Testing PixelVue, Solutions, Product Families, Technologies, Applications APIs
Tests CRUD operations for admin CMS functionality
"""
import pytest
import requests
import os

BASE_URL = os.environ.get('REACT_APP_BACKEND_URL', '').rstrip('/')

class TestPixelVueAPI:
    """PixelVue Products API Tests"""
    
    def test_get_all_products_public(self):
        """Test public endpoint returns active products"""
        response = requests.get(f"{BASE_URL}/api/pixelvue/products")
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        # All returned products should be active
        for product in data:
            assert product.get('is_active') == True
        print(f"✓ Public PixelVue products: {len(data)} active products")

    def test_get_all_products_admin(self):
        """Test admin endpoint returns all products"""
        response = requests.get(f"{BASE_URL}/api/pixelvue/admin/products")
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        assert len(data) == 24, f"Expected 24 products, got {len(data)}"
        print(f"✓ Admin PixelVue products: {len(data)} products (expected: 24)")

    def test_get_products_by_category(self):
        """Test category filtering"""
        for category in ['poster', 'commercial', 'creative']:
            response = requests.get(f"{BASE_URL}/api/pixelvue/products?category={category}")
            assert response.status_code == 200
            data = response.json()
            for product in data:
                assert product.get('category') == category
            print(f"✓ {category} category: {len(data)} products")

    def test_get_categories(self):
        """Test categories endpoint"""
        response = requests.get(f"{BASE_URL}/api/pixelvue/categories")
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        categories = [c['category'] for c in data]
        assert 'poster' in categories or 'commercial' in categories or 'creative' in categories
        print(f"✓ Categories: {data}")

    def test_get_product_by_slug(self):
        """Test getting product by slug"""
        # First get all products to get a valid slug
        response = requests.get(f"{BASE_URL}/api/pixelvue/admin/products")
        products = response.json()
        if products:
            slug = products[0]['slug']
            response = requests.get(f"{BASE_URL}/api/pixelvue/products/{slug}")
            assert response.status_code == 200
            data = response.json()
            assert data['slug'] == slug
            print(f"✓ Get product by slug '{slug}': OK")

    def test_get_product_by_invalid_slug(self):
        """Test 404 for invalid slug"""
        response = requests.get(f"{BASE_URL}/api/pixelvue/products/invalid-nonexistent-slug")
        assert response.status_code == 404
        print("✓ Invalid slug returns 404")

    def test_product_structure(self):
        """Test product has all required fields"""
        response = requests.get(f"{BASE_URL}/api/pixelvue/admin/products")
        products = response.json()
        if products:
            product = products[0]
            required_fields = ['id', 'name', 'slug', 'category', 'tagline', 'description', 'is_active', 'order']
            for field in required_fields:
                assert field in product, f"Missing field: {field}"
            # Optional array fields
            optional_fields = ['quick_specs', 'features', 'applications', 'specifications', 'faqs']
            for field in optional_fields:
                assert field in product, f"Missing optional field: {field}"
            print("✓ Product structure validation passed")


class TestSolutionsAPI:
    """Solutions/Industries API Tests"""

    def test_get_all_solutions_public(self):
        """Test public endpoint"""
        response = requests.get(f"{BASE_URL}/api/solutions")
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        print(f"✓ Public solutions: {len(data)} solutions")

    def test_get_all_solutions_admin(self):
        """Test admin endpoint"""
        response = requests.get(f"{BASE_URL}/api/solutions/admin/all")
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        assert len(data) == 11, f"Expected 11 solutions, got {len(data)}"
        print(f"✓ Admin solutions: {len(data)} solutions (expected: 11)")

    def test_get_solution_by_slug(self):
        """Test getting solution by slug"""
        response = requests.get(f"{BASE_URL}/api/solutions/admin/all")
        solutions = response.json()
        if solutions:
            slug = solutions[0]['slug']
            response = requests.get(f"{BASE_URL}/api/solutions/{slug}")
            assert response.status_code == 200
            data = response.json()
            assert data['slug'] == slug
            print(f"✓ Get solution by slug '{slug}': OK")

    def test_solution_structure(self):
        """Test solution has required fields"""
        response = requests.get(f"{BASE_URL}/api/solutions/admin/all")
        solutions = response.json()
        if solutions:
            solution = solutions[0]
            required_fields = ['id', 'title', 'slug', 'tagline', 'description', 'icon', 'is_active']
            for field in required_fields:
                assert field in solution, f"Missing field: {field}"
            print("✓ Solution structure validation passed")


class TestProductFamiliesAPI:
    """Product Families API Tests"""

    def test_get_all_families_public(self):
        """Test public endpoint"""
        response = requests.get(f"{BASE_URL}/api/product-families")
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        print(f"✓ Public product families: {len(data)} families")

    def test_get_all_families_admin(self):
        """Test admin endpoint"""
        response = requests.get(f"{BASE_URL}/api/product-families/admin/all")
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        assert len(data) == 5, f"Expected 5 families, got {len(data)}"
        print(f"✓ Admin product families: {len(data)} families (expected: 5)")

    def test_get_family_by_slug(self):
        """Test getting family by slug"""
        response = requests.get(f"{BASE_URL}/api/product-families/admin/all")
        families = response.json()
        if families:
            slug = families[0]['slug']
            response = requests.get(f"{BASE_URL}/api/product-families/{slug}")
            assert response.status_code == 200
            data = response.json()
            assert data['slug'] == slug
            print(f"✓ Get family by slug '{slug}': OK")

    def test_family_structure(self):
        """Test family has required fields"""
        response = requests.get(f"{BASE_URL}/api/product-families/admin/all")
        families = response.json()
        if families:
            family = families[0]
            required_fields = ['id', 'name', 'slug', 'tagline', 'description', 'brand_color', 'is_active']
            for field in required_fields:
                assert field in family, f"Missing field: {field}"
            print("✓ Product family structure validation passed")


class TestTechnologiesAPI:
    """Technologies API Tests"""

    def test_get_all_technologies_public(self):
        """Test public endpoint"""
        response = requests.get(f"{BASE_URL}/api/technologies")
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        print(f"✓ Public technologies: {len(data)} technologies")

    def test_get_all_technologies_admin(self):
        """Test admin endpoint"""
        response = requests.get(f"{BASE_URL}/api/technologies/admin/all")
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        assert len(data) == 6, f"Expected 6 technologies, got {len(data)}"
        print(f"✓ Admin technologies: {len(data)} technologies (expected: 6)")

    def test_get_technology_by_slug(self):
        """Test getting technology by slug"""
        response = requests.get(f"{BASE_URL}/api/technologies/admin/all")
        technologies = response.json()
        if technologies:
            slug = technologies[0]['slug']
            response = requests.get(f"{BASE_URL}/api/technologies/{slug}")
            assert response.status_code == 200
            data = response.json()
            assert data['slug'] == slug
            print(f"✓ Get technology by slug '{slug}': OK")

    def test_technology_structure(self):
        """Test technology has required fields"""
        response = requests.get(f"{BASE_URL}/api/technologies/admin/all")
        technologies = response.json()
        if technologies:
            tech = technologies[0]
            required_fields = ['id', 'name', 'slug', 'tagline', 'description', 'icon', 'color', 'is_active']
            for field in required_fields:
                assert field in tech, f"Missing field: {field}"
            print("✓ Technology structure validation passed")


class TestApplicationsAPI:
    """Applications API Tests"""

    def test_get_all_applications_public(self):
        """Test public endpoint"""
        response = requests.get(f"{BASE_URL}/api/applications")
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        print(f"✓ Public applications: {len(data)} applications")

    def test_get_all_applications_admin(self):
        """Test admin endpoint"""
        response = requests.get(f"{BASE_URL}/api/applications/admin/all")
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        assert len(data) == 8, f"Expected 8 applications, got {len(data)}"
        print(f"✓ Admin applications: {len(data)} applications (expected: 8)")

    def test_get_application_by_slug(self):
        """Test getting application by slug"""
        response = requests.get(f"{BASE_URL}/api/applications/admin/all")
        applications = response.json()
        if applications:
            slug = applications[0]['slug']
            response = requests.get(f"{BASE_URL}/api/applications/{slug}")
            assert response.status_code == 200
            data = response.json()
            assert data['slug'] == slug
            print(f"✓ Get application by slug '{slug}': OK")

    def test_application_structure(self):
        """Test application has required fields"""
        response = requests.get(f"{BASE_URL}/api/applications/admin/all")
        applications = response.json()
        if applications:
            app = applications[0]
            required_fields = ['id', 'name', 'slug', 'tagline', 'description', 'icon', 'color', 'is_active']
            for field in required_fields:
                assert field in app, f"Missing field: {field}"
            print("✓ Application structure validation passed")


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
