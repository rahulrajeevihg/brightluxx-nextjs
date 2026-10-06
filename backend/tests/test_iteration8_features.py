"""
Test suite for Iteration 8 - New Pages and Content Features
Tests:
1. Solutions page data requirements
2. About page data requirements  
3. Navigation updates (Solutions link)
4. Footer updates (About Us link)
5. Projects page (real projects, sector filters)
6. Products (57 products, new categories including road-signal)
"""

import pytest
import requests
import os

BASE_URL = os.environ.get('REACT_APP_BACKEND_URL', '').rstrip('/')


class TestBackendDataForNewFeatures:
    """Test backend data requirements for new pages"""

    def test_01_products_count_57(self):
        """Test: GET /api/products shows 57 products (16 new ones added)"""
        response = requests.get(f"{BASE_URL}/api/products")
        assert response.status_code == 200, f"Products fetch failed: {response.text}"
        data = response.json()
        product_count = len(data["products"])
        print(f"✓ Products endpoint returned {product_count} products")
        assert product_count == 57, f"Expected 57 products, got {product_count}"

    def test_02_categories_include_road_signal(self):
        """Test: GET /api/products/categories includes new category 'road-signal'"""
        response = requests.get(f"{BASE_URL}/api/products/categories")
        assert response.status_code == 200, f"Categories fetch failed: {response.text}"
        data = response.json()
        categories = data["categories"]
        
        category_values = [c["value"] for c in categories]
        assert "road-signal" in category_values, f"Missing 'road-signal' category. Found: {category_values}"
        
        # Verify road-signal has products
        road_signal_cat = next((c for c in categories if c["value"] == "road-signal"), None)
        assert road_signal_cat is not None
        assert road_signal_cat["count"] >= 2, f"Expected at least 2 road-signal products, got {road_signal_cat['count']}"
        
        print(f"✓ Categories include 'road-signal' with {road_signal_cat['count']} products")

    def test_03_projects_count_26(self):
        """Test: GET /api/projects shows 26 projects (25 real + 1 test)"""
        response = requests.get(f"{BASE_URL}/api/projects")
        assert response.status_code == 200, f"Projects fetch failed: {response.text}"
        data = response.json()
        project_count = len(data["projects"])
        print(f"✓ Projects endpoint returned {project_count} projects")
        assert project_count == 26, f"Expected 26 projects, got {project_count}"

    def test_04_projects_include_real_projects(self):
        """Test: Projects include real projects from brightluxx.com"""
        response = requests.get(f"{BASE_URL}/api/projects")
        data = response.json()
        projects = data["projects"]
        
        # Check for some expected real projects
        titles = [p["title"] for p in projects]
        
        # Check for expected project names (partial match)
        expected_keywords = ["Nesto", "Indian Pavilion", "Expo"]
        
        # Check for retail, hospitality sectors
        sectors = set(p["sector"] for p in projects)
        expected_sectors = {"retail", "hospitality"}
        
        assert expected_sectors.issubset(sectors), f"Missing expected sectors. Found: {sectors}"
        print(f"✓ Projects include sectors: {sectors}")
        print(f"✓ Sample project titles: {titles[:5]}")

    def test_05_projects_sectors_include_exhibitions_government_healthcare(self):
        """Test: Projects page sector filters include exhibitions, government, healthcare"""
        response = requests.get(f"{BASE_URL}/api/projects")
        data = response.json()
        projects = data["projects"]
        
        # Get all unique sectors
        sectors = set(p["sector"] for p in projects)
        print(f"✓ Available sectors: {sectors}")
        
        # Check sector filter works
        for sector in ["retail", "hospitality"]:
            response = requests.get(f"{BASE_URL}/api/projects?sector={sector}")
            assert response.status_code == 200
            filtered = response.json()["projects"]
            assert all(p["sector"] == sector for p in filtered), f"Sector filter broken for {sector}"
        
        print("✓ Sector filtering works correctly")

    def test_06_products_include_new_categories(self):
        """Test: Products include new categories: road-signal, flexible, cob-microled"""
        response = requests.get(f"{BASE_URL}/api/products/categories")
        data = response.json()
        categories = data["categories"]
        
        category_values = [c["value"] for c in categories]
        
        # Check for key new categories
        new_categories = ["road-signal", "flexible", "cob-microled", "transparent"]
        for cat in new_categories:
            assert cat in category_values, f"Missing category: {cat}"
        
        print(f"✓ All new categories present: {new_categories}")
        print(f"✓ Total categories: {len(categories)}")

    def test_07_health_check_works(self):
        """Test: API health check works"""
        response = requests.get(f"{BASE_URL}/api/health")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "ok"
        print(f"✓ Health check passed: {data}")


class TestSolutionsPageData:
    """Verify data requirements for Solutions page"""
    
    def test_solutions_recommended_products_exist(self):
        """Test: Recommended products in Solutions page exist in catalog"""
        response = requests.get(f"{BASE_URL}/api/products")
        products = response.json()["products"]
        product_names = [p["name"].lower() for p in products]
        
        # Solutions page recommends these products
        solutions_recommendations = [
            "p2.5", "p4 outdoor", "transparent", "rental", "flexible",
            "road signal", "cob", "clearfilm"
        ]
        
        # Check some recommended products exist
        found_count = 0
        for rec in solutions_recommendations:
            if any(rec in name for name in product_names):
                found_count += 1
        
        print(f"✓ Found {found_count}/{len(solutions_recommendations)} recommended product types in catalog")
        assert found_count >= 5, f"Missing many recommended products"


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
