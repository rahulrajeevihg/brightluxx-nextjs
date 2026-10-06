"""
Test Iteration 10: Product Detail Pages Feature
Tests:
- Product detail page API (GET /api/products/:slug)
- Related products (same category filtering)
- Lead submission from product detail (POST /api/leads with product_interest)
- Non-existent product returns 404
"""
import pytest
import requests
import os
import uuid

BASE_URL = os.environ.get('REACT_APP_BACKEND_URL', '').rstrip('/')


class TestProductDetailAPI:
    """Tests for GET /api/products/:slug endpoint"""
    
    def test_get_product_by_slug_success(self):
        """Test fetching product by slug returns correct data"""
        response = requests.get(f"{BASE_URL}/api/products/cob-microled-04mm")
        assert response.status_code == 200, f"Expected 200, got {response.status_code}"
        
        data = response.json()
        # Verify required fields
        assert data.get("slug") == "cob-microled-04mm"
        assert data.get("product_code") == "BL-COB040"
        assert data.get("name") == "COB MicroLED 0.4mm"
        assert data.get("category") == "cob-microled"
        
        # Verify specs exist
        assert "pixel_pitch" in data
        assert "brightness" in data
        assert "resolution" in data
        print(f"PASS: Product {data['slug']} returned with all required fields")
    
    def test_product_has_gallery(self):
        """Test product has gallery array with multiple images"""
        response = requests.get(f"{BASE_URL}/api/products/cob-microled-04mm")
        assert response.status_code == 200
        
        data = response.json()
        gallery = data.get("gallery", [])
        assert isinstance(gallery, list), "Gallery should be a list"
        assert len(gallery) >= 1, "Gallery should have at least 1 image"
        
        # Verify gallery images are /uploads/ paths
        for img in gallery:
            assert "/uploads/" in img, f"Gallery image should be from /uploads/: {img}"
        print(f"PASS: Product has {len(gallery)} gallery images")
    
    def test_product_has_key_specs(self):
        """Test product has key_specs array for specifications table"""
        response = requests.get(f"{BASE_URL}/api/products/cob-microled-04mm")
        assert response.status_code == 200
        
        data = response.json()
        key_specs = data.get("key_specs", [])
        assert isinstance(key_specs, list), "key_specs should be a list"
        
        # Verify key_specs have label/value format
        for spec in key_specs:
            assert "label" in spec, f"Each spec should have 'label': {spec}"
            assert "value" in spec, f"Each spec should have 'value': {spec}"
        print(f"PASS: Product has {len(key_specs)} key specifications")
    
    def test_product_not_found(self):
        """Test non-existent product returns 404"""
        response = requests.get(f"{BASE_URL}/api/products/non-existent-product-xyz")
        assert response.status_code == 404, f"Expected 404 for non-existent product, got {response.status_code}"
        
        data = response.json()
        assert "detail" in data, "404 response should have detail message"
        print(f"PASS: Non-existent product returns 404 with message: {data.get('detail')}")
    
    def test_multiple_product_slugs(self):
        """Test fetching multiple products by different slugs"""
        slugs_to_test = [
            "cob-microled-04mm",
            "bl-cob060",
            "clearfilm-led-screen"
        ]
        
        for slug in slugs_to_test:
            response = requests.get(f"{BASE_URL}/api/products/{slug}")
            assert response.status_code == 200, f"Failed to get product: {slug}"
            data = response.json()
            assert data.get("slug") == slug, f"Slug mismatch for {slug}"
        print(f"PASS: All {len(slugs_to_test)} product slugs returned correct data")


class TestRelatedProducts:
    """Tests for related products (same category filtering)"""
    
    def test_get_products_by_category(self):
        """Test filtering products by category for related products section"""
        response = requests.get(f"{BASE_URL}/api/products", params={"category": "cob-microled"})
        assert response.status_code == 200
        
        data = response.json()
        products = data.get("products", [])
        assert len(products) > 0, "Should have COB-MicroLED products"
        
        # Verify all products are from correct category
        for product in products:
            assert product.get("category") == "cob-microled", f"Product {product.get('slug')} has wrong category"
        print(f"PASS: Found {len(products)} products in 'cob-microled' category")
    
    def test_related_products_exclude_current(self):
        """Test that related products can exclude the current product"""
        # Get a product
        product_response = requests.get(f"{BASE_URL}/api/products/cob-microled-04mm")
        product = product_response.json()
        product_slug = product.get("slug")
        product_category = product.get("category")
        
        # Get related products (same category)
        related_response = requests.get(f"{BASE_URL}/api/products", params={"category": product_category})
        related_products = related_response.json().get("products", [])
        
        # Filter out current product (as frontend does)
        related_filtered = [p for p in related_products if p.get("slug") != product_slug]
        
        assert len(related_filtered) > 0, "Should have related products excluding current"
        assert all(p.get("slug") != product_slug for p in related_filtered), "Related products should not include current product"
        print(f"PASS: {len(related_filtered)} related products found (excluding current)")


class TestLeadSubmissionFromProductDetail:
    """Tests for POST /api/leads with product_interest field"""
    
    def test_create_lead_from_product_detail(self):
        """Test creating lead from product detail page quote form"""
        unique_email = f"test_product_detail_{uuid.uuid4().hex[:8]}@test.com"
        
        lead_data = {
            "name": "Test Lead Iteration10",
            "email": unique_email,
            "phone": "+971501234567",
            "message": "Testing product detail quote form",
            "product_interest": "BL-COB040",
            "application": "cob-microled",
            "source": "product_detail"
        }
        
        response = requests.post(f"{BASE_URL}/api/leads", json=lead_data)
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        
        data = response.json()
        assert data.get("success") is True, "Lead submission should succeed"
        assert "leadId" in data, "Response should include leadId"
        print(f"PASS: Lead created successfully with leadId: {data.get('leadId')}")
    
    def test_create_lead_without_city(self):
        """Test lead creation works without city field (city is now optional)"""
        unique_email = f"test_no_city_{uuid.uuid4().hex[:8]}@test.com"
        
        lead_data = {
            "name": "Test No City Lead",
            "email": unique_email,
            "phone": "+971501234567",
            "application": "outdoor",
            "product_interest": "BL-OP5SMD"
            # NO city field - should work
        }
        
        response = requests.post(f"{BASE_URL}/api/leads", json=lead_data)
        assert response.status_code == 200, f"Lead without city should succeed: {response.text}"
        
        data = response.json()
        assert data.get("success") is True
        print("PASS: Lead created successfully without city field")
    
    def test_create_lead_with_product_interest(self):
        """Test lead with product_interest field is accepted"""
        unique_email = f"test_interest_{uuid.uuid4().hex[:8]}@test.com"
        
        lead_data = {
            "name": "Test Product Interest",
            "email": unique_email,
            "phone": "",
            "message": "Interested in transparent LED",
            "product_interest": "BL-CLR02",
            "application": "transparent",
            "source": "product_detail"
        }
        
        response = requests.post(f"{BASE_URL}/api/leads", json=lead_data)
        assert response.status_code == 200, f"Expected 200, got {response.status_code}"
        print("PASS: Lead with product_interest field accepted")
    
    def test_lead_requires_name_and_email(self):
        """Test lead creation fails without required fields"""
        lead_data = {
            "phone": "+971501234567",
            "message": "Missing required fields"
        }
        
        response = requests.post(f"{BASE_URL}/api/leads", json=lead_data)
        assert response.status_code == 422, "Should fail validation without name/email"
        print("PASS: Lead validation correctly requires name and email")


class TestProductDetailPageData:
    """Tests to verify product detail page has all required data"""
    
    def test_product_has_all_display_fields(self):
        """Test product has all fields needed for detail page display"""
        response = requests.get(f"{BASE_URL}/api/products/cob-microled-04mm")
        assert response.status_code == 200
        
        product = response.json()
        
        # Fields needed for product info section
        required_fields = ["slug", "name", "product_code", "category", "tagline", "description"]
        for field in required_fields:
            assert field in product, f"Missing required field: {field}"
        
        # Fields needed for specs quick view
        spec_fields = ["pixel_pitch", "brightness", "resolution"]
        for field in spec_fields:
            assert field in product, f"Missing spec field: {field}"
        
        # Fields needed for gallery
        assert "gallery" in product or "image_url" in product, "Product needs gallery or image_url"
        
        print(f"PASS: Product has all required display fields")
    
    def test_outdoor_product_detail(self):
        """Test outdoor product has correct category for related products"""
        # Get an outdoor product
        response = requests.get(f"{BASE_URL}/api/products", params={"category": "outdoor"})
        products = response.json().get("products", [])
        
        if len(products) > 0:
            outdoor_slug = products[0].get("slug")
            detail_response = requests.get(f"{BASE_URL}/api/products/{outdoor_slug}")
            assert detail_response.status_code == 200
            
            product = detail_response.json()
            assert product.get("category") == "outdoor"
            print(f"PASS: Outdoor product {outdoor_slug} has correct category")
        else:
            pytest.skip("No outdoor products found to test")
    
    def test_transparent_product_detail(self):
        """Test transparent LED product detail"""
        response = requests.get(f"{BASE_URL}/api/products", params={"category": "transparent"})
        products = response.json().get("products", [])
        
        if len(products) > 0:
            slug = products[0].get("slug")
            detail_response = requests.get(f"{BASE_URL}/api/products/{slug}")
            assert detail_response.status_code == 200
            
            product = detail_response.json()
            assert product.get("category") == "transparent"
            print(f"PASS: Transparent product {slug} detail works correctly")
        else:
            pytest.skip("No transparent products found to test")
