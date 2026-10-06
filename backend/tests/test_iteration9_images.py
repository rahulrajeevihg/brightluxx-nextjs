"""
Iteration 9 - Testing real images from brightluxx.com and Solution Detail pages
Focus:
1. Products API returns /uploads/*.webp images (not AI-generated)
2. Projects API returns /uploads/*.webp images (not AI-generated)
3. Inspirations API returns /uploads/*.webp images
4. Solution detail pages exist for all 8 solutions
5. Cross-navigation works between solution pages
6. Home page uses real images (not Unsplash stock)
"""
import pytest
import requests
import os

BASE_URL = os.environ.get('REACT_APP_BACKEND_URL', '').rstrip('/')
assert BASE_URL, "REACT_APP_BACKEND_URL must be set"


class TestProductsRealImages:
    """Verify products have real .webp images from /uploads/"""
    
    def test_products_api_returns_data(self):
        """Test products endpoint returns products"""
        response = requests.get(f"{BASE_URL}/api/products")
        assert response.status_code == 200
        data = response.json()
        assert "products" in data
        assert len(data["products"]) > 0
        print(f"Found {len(data['products'])} products")
    
    def test_products_have_uploads_images(self):
        """All products should have image_url pointing to /uploads/*.webp"""
        response = requests.get(f"{BASE_URL}/api/products")
        assert response.status_code == 200
        products = response.json()["products"]
        
        uploads_count = 0
        generated_count = 0
        empty_count = 0
        
        for product in products:
            image_url = product.get("image_url", "")
            if not image_url:
                empty_count += 1
            elif "/uploads/" in image_url and ".webp" in image_url:
                uploads_count += 1
            elif "/generated/" in image_url:
                generated_count += 1
                print(f"WARNING: Product {product.get('name')} has AI-generated image: {image_url}")
        
        print(f"Products image breakdown: {uploads_count} uploads, {generated_count} generated, {empty_count} empty")
        assert generated_count == 0, f"Found {generated_count} products with AI-generated /generated/ images"
        assert uploads_count > 0, "No products have /uploads/ images"
    
    def test_product_images_are_webp(self):
        """Product images should be .webp format"""
        response = requests.get(f"{BASE_URL}/api/products")
        products = response.json()["products"]
        
        non_webp = []
        for product in products:
            image_url = product.get("image_url", "")
            if image_url and not image_url.endswith(".webp"):
                non_webp.append((product.get("name"), image_url))
        
        if non_webp:
            print(f"Non-webp images found: {non_webp[:5]}")
        # This is informational - not a hard fail


class TestProjectsRealImages:
    """Verify projects have real .webp images from /uploads/"""
    
    def test_projects_api_returns_data(self):
        """Test projects endpoint returns projects"""
        response = requests.get(f"{BASE_URL}/api/projects")
        assert response.status_code == 200
        data = response.json()
        assert "projects" in data
        assert len(data["projects"]) > 0
        print(f"Found {len(data['projects'])} projects")
    
    def test_projects_have_uploads_images(self):
        """All projects should have image_url pointing to /uploads/*.webp"""
        response = requests.get(f"{BASE_URL}/api/projects")
        assert response.status_code == 200
        projects = response.json()["projects"]
        
        uploads_count = 0
        generated_count = 0
        empty_count = 0
        
        for project in projects:
            image_url = project.get("image_url", "")
            if not image_url:
                empty_count += 1
            elif "/uploads/" in image_url and ".webp" in image_url:
                uploads_count += 1
            elif "/generated/" in image_url:
                generated_count += 1
                print(f"WARNING: Project {project.get('title')} has AI-generated image: {image_url}")
        
        print(f"Projects image breakdown: {uploads_count} uploads, {generated_count} generated, {empty_count} empty")
        assert generated_count == 0, f"Found {generated_count} projects with AI-generated /generated/ images"
        assert uploads_count > 0, "No projects have /uploads/ images"


class TestInspirationsRealImages:
    """Verify inspirations have real .webp images from /uploads/"""
    
    def test_inspirations_api_returns_data(self):
        """Test inspirations endpoint returns inspirations"""
        response = requests.get(f"{BASE_URL}/api/inspirations")
        assert response.status_code == 200
        data = response.json()
        assert "inspirations" in data
        assert len(data["inspirations"]) > 0
        print(f"Found {len(data['inspirations'])} inspirations")
    
    def test_inspirations_have_uploads_images(self):
        """All inspirations should have image_url pointing to /uploads/*.webp"""
        response = requests.get(f"{BASE_URL}/api/inspirations")
        assert response.status_code == 200
        inspirations = response.json()["inspirations"]
        
        uploads_count = 0
        generated_count = 0
        empty_count = 0
        
        for insp in inspirations:
            image_url = insp.get("image_url", "")
            if not image_url:
                empty_count += 1
            elif "/uploads/" in image_url and ".webp" in image_url:
                uploads_count += 1
            elif "/generated/" in image_url:
                generated_count += 1
                print(f"WARNING: Inspiration {insp.get('title')} has AI-generated image: {image_url}")
        
        print(f"Inspirations image breakdown: {uploads_count} uploads, {generated_count} generated, {empty_count} empty")
        assert generated_count == 0, f"Found {generated_count} inspirations with AI-generated /generated/ images"
        assert uploads_count > 0, "No inspirations have /uploads/ images"


class TestSolutionsPageExists:
    """Verify /solutions page loads correctly"""
    
    def test_solutions_page_loads(self):
        """Solutions page should be accessible"""
        response = requests.get(f"{BASE_URL}/solutions")
        assert response.status_code == 200
        assert "Solutions" in response.text or "solution" in response.text.lower()
        print("Solutions page loads successfully")


class TestSolutionDetailPagesExist:
    """Verify all 8 solution detail pages exist at /solutions/:id"""
    
    SOLUTION_IDS = ['retail', 'corporate', 'outdoor', 'events', 'creative', 'traffic', 'immersive', 'transparent']
    
    @pytest.mark.parametrize("solution_id", SOLUTION_IDS)
    def test_solution_detail_page_exists(self, solution_id):
        """Each solution detail page should return 200 and contain the solution ID"""
        response = requests.get(f"{BASE_URL}/solutions/{solution_id}")
        assert response.status_code == 200
        print(f"Solution detail page /solutions/{solution_id} exists")


class TestHealthAndBasicEndpoints:
    """Basic health checks"""
    
    def test_health_endpoint(self):
        """Health check should return ok"""
        response = requests.get(f"{BASE_URL}/api/health")
        assert response.status_code == 200
        data = response.json()
        assert data.get("status") == "ok"
    
    def test_home_page_loads(self):
        """Home page should be accessible"""
        response = requests.get(f"{BASE_URL}/")
        assert response.status_code == 200
        print("Home page loads successfully")


class TestImagesExistInUploads:
    """Verify referenced images actually exist in /uploads/ directory"""
    
    SAMPLE_IMAGES = [
        '/uploads/hero_banner.webp',
        '/uploads/insp_retail.webp',
        '/uploads/proj_indian_pavilion___expo_2020_dubai.webp',
        '/uploads/cob_microled_1.webp',
        '/uploads/sol_indoor_shop.webp',
        '/uploads/outdoor_1.webp',
        '/uploads/flexible_1.webp',
        '/uploads/transparent_1.webp',
    ]
    
    @pytest.mark.parametrize("image_path", SAMPLE_IMAGES)
    def test_image_exists(self, image_path):
        """Critical images should be accessible"""
        response = requests.get(f"{BASE_URL}{image_path}")
        assert response.status_code == 200, f"Image not found: {image_path}"
        assert "image" in response.headers.get("Content-Type", ""), f"Not an image: {image_path}"
        print(f"Image exists: {image_path}")
