"""
Blog API CRUD Tests
Tests all blog endpoints: public listing, slug lookup, admin CRUD, publishing/featuring
"""
import pytest
import requests
import os
import uuid

BASE_URL = os.environ.get('REACT_APP_BACKEND_URL')


class TestBlogPublicEndpoints:
    """Public blog endpoints tests"""
    
    def test_get_published_blogs_success(self):
        """GET /api/blogs should return published posts"""
        response = requests.get(f"{BASE_URL}/api/blogs")
        assert response.status_code == 200
        
        data = response.json()
        assert "blogs" in data
        assert "categories" in data
        assert isinstance(data["blogs"], list)
        assert len(data["blogs"]) > 0
        
        # Verify first blog has required fields
        first_blog = data["blogs"][0]
        assert "id" in first_blog
        assert "title" in first_blog
        assert "slug" in first_blog
        assert "excerpt" in first_blog
        assert "content" in first_blog
        assert "category" in first_blog
        assert "is_published" in first_blog
        assert first_blog["is_published"] == True
        print(f"✓ GET /api/blogs returned {len(data['blogs'])} published posts")
    
    def test_get_blogs_with_category_filter(self):
        """GET /api/blogs?category=Technology should filter by category"""
        response = requests.get(f"{BASE_URL}/api/blogs?category=Technology")
        assert response.status_code == 200
        
        data = response.json()
        for blog in data["blogs"]:
            assert blog["category"] == "Technology"
        print(f"✓ Category filter works - returned {len(data['blogs'])} Technology posts")
    
    def test_get_blogs_categories_list(self):
        """GET /api/blogs should return categories list including 'All'"""
        response = requests.get(f"{BASE_URL}/api/blogs")
        assert response.status_code == 200
        
        data = response.json()
        categories = data["categories"]
        assert "All" in categories
        assert len(categories) > 1  # Should have more than just 'All'
        print(f"✓ Categories returned: {categories}")
    
    def test_get_blog_by_slug_success(self):
        """GET /api/blogs/{slug} should return single blog"""
        slug = "microled-vs-oled-2025"
        response = requests.get(f"{BASE_URL}/api/blogs/{slug}")
        assert response.status_code == 200
        
        data = response.json()
        assert "blog" in data
        blog = data["blog"]
        assert blog["slug"] == slug
        assert "title" in blog
        assert "content" in blog
        assert blog["is_published"] == True
        print(f"✓ GET /api/blogs/{slug} returned blog: {blog['title'][:50]}")
    
    def test_get_blog_by_slug_not_found(self):
        """GET /api/blogs/{slug} should return 404 for non-existent slug"""
        response = requests.get(f"{BASE_URL}/api/blogs/non-existent-slug-12345")
        assert response.status_code == 404
        
        data = response.json()
        assert "detail" in data
        print("✓ 404 returned for non-existent slug")
    
    def test_all_seeded_slugs_accessible(self):
        """Verify all 5 seeded blog slugs are accessible"""
        slugs = [
            "microled-vs-oled-2025",
            "choosing-pixel-pitch-guide",
            "led-displays-dubai-retail",
            "outdoor-led-uae-heat-guide",
            "cob-led-technology-explained"
        ]
        for slug in slugs:
            response = requests.get(f"{BASE_URL}/api/blogs/{slug}")
            assert response.status_code == 200, f"Failed to fetch slug: {slug}"
            data = response.json()
            assert data["blog"]["slug"] == slug
        print(f"✓ All {len(slugs)} seeded blog slugs accessible")


class TestBlogAdminEndpoints:
    """Admin blog endpoints - requires authentication"""
    
    @pytest.fixture(scope="class")
    def admin_token(self):
        """Get admin auth token"""
        response = requests.post(f"{BASE_URL}/api/admin/login", json={
            "email": "admin@brightluxx.com",
            "password": os.environ.get("ADMIN_PASSWORD", "brightluxx2025")
        })
        if response.status_code != 200:
            pytest.skip("Admin login failed")
        return response.json()["token"]
    
    def test_admin_get_all_blogs(self, admin_token):
        """GET /api/admin/blogs should return all blogs with counts"""
        response = requests.get(f"{BASE_URL}/api/admin/blogs", headers={
            "Authorization": f"Bearer {admin_token}"
        })
        assert response.status_code == 200
        
        data = response.json()
        assert "blogs" in data
        assert "counts" in data
        
        counts = data["counts"]
        assert "total" in counts
        assert "published" in counts
        assert "drafts" in counts
        assert "featured" in counts
        assert counts["total"] >= 5  # Seeded posts
        print(f"✓ Admin blogs: {counts['total']} total, {counts['published']} published, {counts['featured']} featured")
    
    def test_admin_create_blog_draft(self, admin_token):
        """POST /api/admin/blogs should create new draft blog"""
        unique_id = str(uuid.uuid4())[:8]
        payload = {
            "title": f"TEST Draft Blog {unique_id}",
            "excerpt": "Test excerpt for draft blog",
            "content": "<p>Test content for draft blog</p>",
            "category": "Technology",
            "author": "Test Author",
            "read_time": "3 min",
            "tags": ["Test", "Draft"],
            "is_published": False,
            "featured": False
        }
        
        response = requests.post(f"{BASE_URL}/api/admin/blogs", 
            headers={
                "Authorization": f"Bearer {admin_token}",
                "Content-Type": "application/json"
            },
            json=payload
        )
        assert response.status_code == 200
        
        data = response.json()
        assert data["success"] == True
        assert "blog" in data
        blog = data["blog"]
        assert blog["title"] == payload["title"]
        assert blog["is_published"] == False
        assert "id" in blog
        assert "slug" in blog
        print(f"✓ Created draft blog with id: {blog['id']}, slug: {blog['slug']}")
        
        # Cleanup
        requests.delete(f"{BASE_URL}/api/admin/blogs/{blog['id']}", headers={
            "Authorization": f"Bearer {admin_token}"
        })
    
    def test_admin_create_blog_published(self, admin_token):
        """POST /api/admin/blogs with is_published=True should publish immediately"""
        unique_id = str(uuid.uuid4())[:8]
        payload = {
            "title": f"TEST Published Blog {unique_id}",
            "excerpt": "Test excerpt for published blog",
            "content": "<h2>Test</h2><p>Test content for published blog</p>",
            "category": "Guides",
            "author": "Test Author",
            "read_time": "5 min",
            "tags": ["Test", "Published"],
            "is_published": True,
            "featured": False
        }
        
        response = requests.post(f"{BASE_URL}/api/admin/blogs", 
            headers={
                "Authorization": f"Bearer {admin_token}",
                "Content-Type": "application/json"
            },
            json=payload
        )
        assert response.status_code == 200
        
        data = response.json()
        blog = data["blog"]
        assert blog["is_published"] == True
        assert blog["published_at"] is not None
        
        # Verify accessible via public API
        public_response = requests.get(f"{BASE_URL}/api/blogs/{blog['slug']}")
        assert public_response.status_code == 200
        print(f"✓ Created and verified published blog: {blog['slug']}")
        
        # Cleanup
        requests.delete(f"{BASE_URL}/api/admin/blogs/{blog['id']}", headers={
            "Authorization": f"Bearer {admin_token}"
        })
    
    def test_admin_update_blog(self, admin_token):
        """PUT /api/admin/blogs/{id} should update blog"""
        # First create a blog
        unique_id = str(uuid.uuid4())[:8]
        create_payload = {
            "title": f"TEST Blog to Update {unique_id}",
            "excerpt": "Original excerpt",
            "content": "<p>Original content</p>",
            "category": "Technology",
            "is_published": False
        }
        
        create_response = requests.post(f"{BASE_URL}/api/admin/blogs",
            headers={
                "Authorization": f"Bearer {admin_token}",
                "Content-Type": "application/json"
            },
            json=create_payload
        )
        blog_id = create_response.json()["blog"]["id"]
        
        # Update the blog
        update_payload = {
            "title": f"TEST Updated Blog {unique_id}",
            "excerpt": "Updated excerpt",
            "category": "Guides"
        }
        
        update_response = requests.put(f"{BASE_URL}/api/admin/blogs/{blog_id}",
            headers={
                "Authorization": f"Bearer {admin_token}",
                "Content-Type": "application/json"
            },
            json=update_payload
        )
        assert update_response.status_code == 200
        
        data = update_response.json()
        assert data["success"] == True
        assert data["blog"]["title"] == update_payload["title"]
        assert data["blog"]["excerpt"] == update_payload["excerpt"]
        assert data["blog"]["category"] == update_payload["category"]
        print(f"✓ Updated blog {blog_id}")
        
        # Cleanup
        requests.delete(f"{BASE_URL}/api/admin/blogs/{blog_id}", headers={
            "Authorization": f"Bearer {admin_token}"
        })
    
    def test_admin_toggle_publish_status(self, admin_token):
        """PUT /api/admin/blogs/{id} can toggle publish status"""
        # Create draft
        unique_id = str(uuid.uuid4())[:8]
        create_response = requests.post(f"{BASE_URL}/api/admin/blogs",
            headers={
                "Authorization": f"Bearer {admin_token}",
                "Content-Type": "application/json"
            },
            json={
                "title": f"TEST Toggle Publish {unique_id}",
                "excerpt": "Test toggle",
                "content": "<p>Test</p>",
                "category": "Technology",
                "is_published": False
            }
        )
        blog = create_response.json()["blog"]
        assert blog["is_published"] == False
        
        # Toggle to published
        toggle_response = requests.put(f"{BASE_URL}/api/admin/blogs/{blog['id']}",
            headers={
                "Authorization": f"Bearer {admin_token}",
                "Content-Type": "application/json"
            },
            json={"is_published": True}
        )
        assert toggle_response.status_code == 200
        assert toggle_response.json()["blog"]["is_published"] == True
        
        # Toggle back to draft
        toggle_back = requests.put(f"{BASE_URL}/api/admin/blogs/{blog['id']}",
            headers={
                "Authorization": f"Bearer {admin_token}",
                "Content-Type": "application/json"
            },
            json={"is_published": False}
        )
        assert toggle_back.status_code == 200
        assert toggle_back.json()["blog"]["is_published"] == False
        print(f"✓ Toggle publish status works correctly")
        
        # Cleanup
        requests.delete(f"{BASE_URL}/api/admin/blogs/{blog['id']}", headers={
            "Authorization": f"Bearer {admin_token}"
        })
    
    def test_admin_toggle_featured_status(self, admin_token):
        """PUT /api/admin/blogs/{id} can toggle featured status"""
        unique_id = str(uuid.uuid4())[:8]
        create_response = requests.post(f"{BASE_URL}/api/admin/blogs",
            headers={
                "Authorization": f"Bearer {admin_token}",
                "Content-Type": "application/json"
            },
            json={
                "title": f"TEST Toggle Featured {unique_id}",
                "excerpt": "Test featured toggle",
                "content": "<p>Test</p>",
                "category": "Technology",
                "is_published": True,
                "featured": False
            }
        )
        blog = create_response.json()["blog"]
        assert blog["featured"] == False
        
        # Toggle to featured
        toggle_response = requests.put(f"{BASE_URL}/api/admin/blogs/{blog['id']}",
            headers={
                "Authorization": f"Bearer {admin_token}",
                "Content-Type": "application/json"
            },
            json={"featured": True}
        )
        assert toggle_response.status_code == 200
        assert toggle_response.json()["blog"]["featured"] == True
        print(f"✓ Toggle featured status works correctly")
        
        # Cleanup
        requests.delete(f"{BASE_URL}/api/admin/blogs/{blog['id']}", headers={
            "Authorization": f"Bearer {admin_token}"
        })
    
    def test_admin_delete_blog(self, admin_token):
        """DELETE /api/admin/blogs/{id} should remove blog"""
        # Create a blog
        unique_id = str(uuid.uuid4())[:8]
        create_response = requests.post(f"{BASE_URL}/api/admin/blogs",
            headers={
                "Authorization": f"Bearer {admin_token}",
                "Content-Type": "application/json"
            },
            json={
                "title": f"TEST Blog to Delete {unique_id}",
                "excerpt": "To be deleted",
                "content": "<p>Delete me</p>",
                "category": "Technology",
                "is_published": False
            }
        )
        blog_id = create_response.json()["blog"]["id"]
        
        # Delete
        delete_response = requests.delete(f"{BASE_URL}/api/admin/blogs/{blog_id}",
            headers={"Authorization": f"Bearer {admin_token}"}
        )
        assert delete_response.status_code == 200
        data = delete_response.json()
        assert data["success"] == True
        
        # Verify deletion
        verify_response = requests.get(f"{BASE_URL}/api/admin/blogs",
            headers={"Authorization": f"Bearer {admin_token}"}
        )
        blog_ids = [b["id"] for b in verify_response.json()["blogs"]]
        assert blog_id not in blog_ids
        print(f"✓ Deleted blog {blog_id} and verified removal")
    
    def test_admin_delete_nonexistent_blog(self, admin_token):
        """DELETE /api/admin/blogs/{id} should return 404 for non-existent blog"""
        response = requests.delete(f"{BASE_URL}/api/admin/blogs/nonexistent-id-12345",
            headers={"Authorization": f"Bearer {admin_token}"}
        )
        assert response.status_code == 404
        print("✓ 404 returned for deleting non-existent blog")
    
    def test_admin_update_nonexistent_blog(self, admin_token):
        """PUT /api/admin/blogs/{id} should return 404 for non-existent blog"""
        response = requests.put(f"{BASE_URL}/api/admin/blogs/nonexistent-id-12345",
            headers={
                "Authorization": f"Bearer {admin_token}",
                "Content-Type": "application/json"
            },
            json={"title": "Test"}
        )
        assert response.status_code == 404
        print("✓ 404 returned for updating non-existent blog")
    
    def test_admin_slug_uniqueness(self, admin_token):
        """Creating blog with duplicate slug should generate unique slug"""
        unique_id = str(uuid.uuid4())[:8]
        payload = {
            "title": f"Test Slug Uniqueness {unique_id}",
            "slug": "test-slug-unique",
            "excerpt": "Test",
            "content": "<p>Test</p>",
            "category": "Technology"
        }
        
        # Create first blog
        response1 = requests.post(f"{BASE_URL}/api/admin/blogs",
            headers={
                "Authorization": f"Bearer {admin_token}",
                "Content-Type": "application/json"
            },
            json=payload
        )
        blog1 = response1.json()["blog"]
        
        # Create second blog with same slug
        response2 = requests.post(f"{BASE_URL}/api/admin/blogs",
            headers={
                "Authorization": f"Bearer {admin_token}",
                "Content-Type": "application/json"
            },
            json=payload
        )
        blog2 = response2.json()["blog"]
        
        # Slugs should be different
        assert blog1["slug"] != blog2["slug"]
        print(f"✓ Slug uniqueness enforced: {blog1['slug']} vs {blog2['slug']}")
        
        # Cleanup
        requests.delete(f"{BASE_URL}/api/admin/blogs/{blog1['id']}", headers={
            "Authorization": f"Bearer {admin_token}"
        })
        requests.delete(f"{BASE_URL}/api/admin/blogs/{blog2['id']}", headers={
            "Authorization": f"Bearer {admin_token}"
        })


class TestBlogAuthentication:
    """Test authentication requirements for admin endpoints"""
    
    def test_admin_blogs_requires_auth(self):
        """GET /api/admin/blogs should require authentication"""
        response = requests.get(f"{BASE_URL}/api/admin/blogs")
        assert response.status_code in [401, 403]
        print("✓ Admin blogs requires authentication")
    
    def test_create_blog_requires_auth(self):
        """POST /api/admin/blogs should require authentication"""
        response = requests.post(f"{BASE_URL}/api/admin/blogs", json={
            "title": "Test",
            "excerpt": "Test",
            "content": "Test",
            "category": "Technology"
        })
        assert response.status_code in [401, 403]
        print("✓ Create blog requires authentication")
    
    def test_update_blog_requires_auth(self):
        """PUT /api/admin/blogs/{id} should require authentication"""
        response = requests.put(f"{BASE_URL}/api/admin/blogs/test-id", json={
            "title": "Test"
        })
        assert response.status_code in [401, 403]
        print("✓ Update blog requires authentication")
    
    def test_delete_blog_requires_auth(self):
        """DELETE /api/admin/blogs/{id} should require authentication"""
        response = requests.delete(f"{BASE_URL}/api/admin/blogs/test-id")
        assert response.status_code in [401, 403]
        print("✓ Delete blog requires authentication")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
