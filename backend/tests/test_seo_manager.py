"""
SEO Manager API Tests - Testing per-page SEO management with AI auto-generation
"""
import pytest
import requests
import os

BASE_URL = os.environ.get('REACT_APP_BACKEND_URL', '').rstrip('/')

# Test credentials
ADMIN_EMAIL = "admin@brightluxx.com"
ADMIN_PASSWORD = os.environ.get("ADMIN_PASSWORD", "brightluxx2026")


@pytest.fixture(scope="module")
def api_client():
    """Shared requests session"""
    session = requests.Session()
    session.headers.update({"Content-Type": "application/json"})
    return session


@pytest.fixture(scope="module")
def auth_token(api_client):
    """Get authentication token for admin"""
    response = api_client.post(f"{BASE_URL}/api/admin/login", json={
        "email": ADMIN_EMAIL,
        "password": ADMIN_PASSWORD
    })
    if response.status_code == 200:
        data = response.json()
        return data.get("token")
    pytest.skip(f"Authentication failed - status {response.status_code}")


@pytest.fixture(scope="module")
def authenticated_client(api_client, auth_token):
    """Session with auth header"""
    api_client.headers.update({"Authorization": f"Bearer {auth_token}"})
    return api_client


class TestPublicSEOEndpoint:
    """Test public SEO meta endpoint"""
    
    def test_get_page_meta_homepage(self, api_client):
        """Test public endpoint returns SEO data for homepage"""
        response = api_client.get(f"{BASE_URL}/api/seo/page-meta?path=/")
        assert response.status_code == 200, f"Expected 200, got {response.status_code}"
        
        data = response.json()
        # Verify response structure
        assert "meta_title" in data
        assert "meta_description" in data
        assert "keywords" in data
        assert "image_alt" in data
        assert "og_title" in data
        assert "og_description" in data
        print(f"Homepage SEO meta: title='{data.get('meta_title', '')[:50]}...'")
    
    def test_get_page_meta_products(self, api_client):
        """Test public endpoint for products page"""
        response = api_client.get(f"{BASE_URL}/api/seo/page-meta?path=/products")
        assert response.status_code == 200
        
        data = response.json()
        assert "meta_title" in data
        assert "keywords" in data
        print(f"Products page SEO meta retrieved")
    
    def test_get_page_meta_nonexistent(self, api_client):
        """Test public endpoint for non-existent page returns empty data"""
        response = api_client.get(f"{BASE_URL}/api/seo/page-meta?path=/nonexistent-page-xyz")
        assert response.status_code == 200
        
        data = response.json()
        # Should return empty strings for non-existent page
        assert data.get("meta_title") == ""
        print("Non-existent page returns empty SEO data as expected")


class TestAdminSEOStats:
    """Test admin SEO stats endpoint"""
    
    def test_get_seo_stats(self, authenticated_client):
        """Test SEO stats endpoint returns correct structure"""
        response = authenticated_client.get(f"{BASE_URL}/api/admin/seo/stats")
        assert response.status_code == 200, f"Expected 200, got {response.status_code}"
        
        data = response.json()
        # Verify stats structure
        assert "total_pages" in data
        assert "avg_score" in data
        assert "optimized" in data
        assert "needs_work" in data
        
        # Verify total pages is 55 (as per SITE_PAGES list)
        assert data["total_pages"] >= 55, f"Expected at least 55 pages, got {data['total_pages']}"
        
        # Verify avg_score is a number
        assert isinstance(data["avg_score"], (int, float))
        
        print(f"SEO Stats: total={data['total_pages']}, avg_score={data['avg_score']}, optimized={data['optimized']}, needs_work={data['needs_work']}")


class TestAdminSEOPages:
    """Test admin SEO pages list endpoint"""
    
    def test_list_all_pages(self, authenticated_client):
        """Test listing all SEO pages"""
        response = authenticated_client.get(f"{BASE_URL}/api/admin/seo/pages")
        assert response.status_code == 200, f"Expected 200, got {response.status_code}"
        
        data = response.json()
        assert isinstance(data, list)
        assert len(data) >= 55, f"Expected at least 55 pages, got {len(data)}"
        
        # Verify page structure
        first_page = data[0]
        assert "id" in first_page
        assert "path" in first_page
        assert "name" in first_page
        assert "category" in first_page
        assert "meta_title" in first_page
        assert "meta_description" in first_page
        assert "keywords" in first_page
        assert "score" in first_page
        assert "score_breakdown" in first_page
        
        # Verify categories exist
        categories = set(p["category"] for p in data)
        expected_categories = {"Main", "Product Family", "Lifestyle", "Content", "Other", "SEO Landing"}
        assert categories.intersection(expected_categories), f"Expected categories not found. Got: {categories}"
        
        print(f"Listed {len(data)} pages with categories: {categories}")
    
    def test_page_has_score_breakdown(self, authenticated_client):
        """Test that pages have proper score breakdown"""
        response = authenticated_client.get(f"{BASE_URL}/api/admin/seo/pages")
        assert response.status_code == 200
        
        data = response.json()
        first_page = data[0]
        
        breakdown = first_page.get("score_breakdown", {})
        # Verify breakdown has all 5 components
        expected_keys = {"title", "description", "keywords", "slug", "image_alt"}
        assert set(breakdown.keys()) == expected_keys, f"Expected breakdown keys {expected_keys}, got {set(breakdown.keys())}"
        
        # Verify each breakdown item has score, max, tip
        for key, val in breakdown.items():
            assert "score" in val, f"Missing 'score' in {key} breakdown"
            assert "max" in val, f"Missing 'max' in {key} breakdown"
            assert "tip" in val, f"Missing 'tip' in {key} breakdown"
        
        print(f"Score breakdown verified: {breakdown}")


class TestAdminSEOPageUpdate:
    """Test admin SEO page update endpoint"""
    
    def test_update_page_seo(self, authenticated_client):
        """Test updating SEO data for a page"""
        # First get a page to update
        response = authenticated_client.get(f"{BASE_URL}/api/admin/seo/pages")
        assert response.status_code == 200
        
        pages = response.json()
        # Find a page that's not homepage (to avoid affecting AI-generated content)
        test_page = None
        for p in pages:
            if p["path"] == "/faq":
                test_page = p
                break
        
        if not test_page:
            test_page = pages[-1]  # Use last page
        
        page_id = test_page["id"]
        
        # Update the page
        update_data = {
            "meta_title": "TEST_FAQ - Frequently Asked Questions | Brightluxx LED",
            "meta_description": "TEST_Find answers to common questions about Brightluxx LED displays, installation, pricing, and support services in UAE and GCC region.",
            "keywords": ["LED FAQ", "LED display questions", "Brightluxx support"],
            "image_alt": "TEST_Brightluxx LED display FAQ section"
        }
        
        response = authenticated_client.put(
            f"{BASE_URL}/api/admin/seo/pages/{page_id}",
            json=update_data
        )
        assert response.status_code == 200, f"Expected 200, got {response.status_code}"
        
        updated = response.json()
        assert updated["meta_title"] == update_data["meta_title"]
        assert updated["meta_description"] == update_data["meta_description"]
        assert updated["keywords"] == update_data["keywords"]
        assert updated["image_alt"] == update_data["image_alt"]
        
        # Verify score updated
        assert "score" in updated
        assert updated["score"] > 0, "Score should be > 0 after adding SEO data"
        
        print(f"Updated page {test_page['name']}: new score = {updated['score']}")
        
        # Verify persistence with GET
        response = authenticated_client.get(f"{BASE_URL}/api/admin/seo/pages/{page_id}")
        assert response.status_code == 200
        
        fetched = response.json()
        assert fetched["meta_title"] == update_data["meta_title"]
        print("Update persisted successfully")


class TestAdminSEOAIGeneration:
    """Test AI generation endpoint - Note: This uses GPT-5.2 and may take 5-10 seconds"""
    
    def test_ai_generate_single_field(self, authenticated_client):
        """Test AI generation for a single field"""
        # Get a page with low score
        response = authenticated_client.get(f"{BASE_URL}/api/admin/seo/pages")
        assert response.status_code == 200
        
        pages = response.json()
        # Find a page with low score (not homepage which was already AI-generated)
        test_page = None
        for p in pages:
            if p["score"] < 40 and p["path"] != "/":
                test_page = p
                break
        
        if not test_page:
            # Use any page that's not homepage
            for p in pages:
                if p["path"] != "/":
                    test_page = p
                    break
        
        if not test_page:
            pytest.skip("No suitable test page found")
        
        page_id = test_page["id"]
        original_score = test_page["score"]
        
        print(f"Testing AI generation on '{test_page['name']}' (score: {original_score})")
        
        # Generate only meta_title
        response = authenticated_client.post(
            f"{BASE_URL}/api/admin/seo/ai-generate",
            json={"page_id": page_id, "fields": ["meta_title"]}
        )
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        
        data = response.json()
        
        # Check for error
        if "error" in data:
            pytest.fail(f"AI generation failed: {data['error']}")
        
        assert "generated" in data
        assert "meta_title" in data["generated"]
        assert len(data["generated"]["meta_title"]) > 0
        
        print(f"AI generated meta_title: '{data['generated']['meta_title']}'")
    
    def test_ai_generate_all_fields(self, authenticated_client):
        """Test AI generation for all fields - may take 5-10 seconds"""
        # Get a page with low score
        response = authenticated_client.get(f"{BASE_URL}/api/admin/seo/pages")
        assert response.status_code == 200
        
        pages = response.json()
        # Find a page with low score
        test_page = None
        for p in pages:
            if p["score"] < 30 and p["path"] not in ["/", "/products", "/contact"]:
                test_page = p
                break
        
        if not test_page:
            for p in pages:
                if p["path"] not in ["/", "/products", "/contact"]:
                    test_page = p
                    break
        
        if not test_page:
            pytest.skip("No suitable test page found")
        
        page_id = test_page["id"]
        original_score = test_page["score"]
        
        print(f"Testing AI Generate All on '{test_page['name']}' (original score: {original_score})")
        
        # Generate all fields
        response = authenticated_client.post(
            f"{BASE_URL}/api/admin/seo/ai-generate",
            json={
                "page_id": page_id,
                "fields": ["meta_title", "meta_description", "keywords", "image_alt", "og_title", "og_description"]
            },
            timeout=30  # Allow longer timeout for AI generation
        )
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        
        data = response.json()
        
        if "error" in data:
            pytest.fail(f"AI generation failed: {data['error']}")
        
        assert "generated" in data
        assert "page" in data
        
        generated = data["generated"]
        # Verify all fields were generated
        assert "meta_title" in generated
        assert "meta_description" in generated
        assert "keywords" in generated
        assert "image_alt" in generated
        
        # Verify score improved
        new_score = data["page"]["score"]
        print(f"Score changed from {original_score} to {new_score}")
        
        # Score should improve after AI generation
        if original_score < 30:
            assert new_score > original_score, f"Score should improve after AI generation (was {original_score}, now {new_score})"
        
        print(f"AI generated all fields successfully. New score: {new_score}")


class TestSEOSeed:
    """Test SEO seed endpoint"""
    
    def test_seed_pages(self, authenticated_client):
        """Test seeding pages (should be idempotent)"""
        response = authenticated_client.post(f"{BASE_URL}/api/admin/seo/seed")
        assert response.status_code == 200
        
        data = response.json()
        assert "seeded" in data
        assert "total_pages" in data
        assert data["total_pages"] >= 55
        
        print(f"Seed result: seeded={data['seeded']}, total_pages={data['total_pages']}")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
