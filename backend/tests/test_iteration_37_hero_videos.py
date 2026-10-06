"""
Iteration 37 - Homepage Hero Videos Testing
Tests for Sora 2-generated hero videos on Brightluxx homepage
"""
import pytest
import requests
import os

BASE_URL = os.environ.get('REACT_APP_BACKEND_URL', '').rstrip('/')

class TestHealthAndBackendAPIs:
    """Test backend health and core APIs"""
    
    def test_health_endpoint(self):
        """Test health endpoint returns 200"""
        response = requests.get(f"{BASE_URL}/api/health", timeout=10)
        assert response.status_code == 200
        print(f"Health endpoint: {response.status_code}")
    
    def test_products_endpoint(self):
        """Test products API returns data"""
        response = requests.get(f"{BASE_URL}/api/products", timeout=10)
        assert response.status_code == 200
        data = response.json()
        assert "products" in data
        print(f"Products endpoint: {response.status_code}, count: {len(data['products'])}")
    
    def test_projects_endpoint(self):
        """Test projects API returns data"""
        response = requests.get(f"{BASE_URL}/api/projects", timeout=10)
        assert response.status_code == 200
        data = response.json()
        assert "projects" in data
        print(f"Projects endpoint: {response.status_code}, count: {len(data['projects'])}")
    
    def test_featured_products_endpoint(self):
        """Test featured products filter works"""
        response = requests.get(f"{BASE_URL}/api/products?featured=true", timeout=10)
        assert response.status_code == 200
        data = response.json()
        assert "products" in data
        print(f"Featured products: {len(data['products'])} items")
    
    def test_featured_projects_endpoint(self):
        """Test featured projects filter works"""
        response = requests.get(f"{BASE_URL}/api/projects?featured=true", timeout=10)
        assert response.status_code == 200
        data = response.json()
        assert "projects" in data
        print(f"Featured projects: {len(data['projects'])} items")


class TestHeroVideoFiles:
    """Test hero video files accessibility"""
    
    def test_hero_video_1_accessible(self):
        """Test hero-video-1.mp4 returns 200"""
        response = requests.head(f"{BASE_URL}/videos/hero-video-1.mp4", timeout=15)
        assert response.status_code == 200
        content_type = response.headers.get('content-type', '')
        print(f"Hero video 1: {response.status_code}, type: {content_type}")
    
    def test_hero_video_2_accessible(self):
        """Test hero-video-2.mp4 returns 200"""
        response = requests.head(f"{BASE_URL}/videos/hero-video-2.mp4", timeout=15)
        assert response.status_code == 200
        content_type = response.headers.get('content-type', '')
        print(f"Hero video 2: {response.status_code}, type: {content_type}")
    
    def test_hero_poster_image_accessible(self):
        """Test poster fallback image is accessible"""
        # Use GET instead of HEAD as CDN may not support HEAD
        response = requests.get(f"{BASE_URL}/api/cdn/hero_banner.webp", timeout=10)
        assert response.status_code == 200
        print(f"Poster image: {response.status_code}")


class TestHomepageStaticAssets:
    """Test homepage static assets"""
    
    def test_homepage_returns_200(self):
        """Test homepage returns 200 (React SPA - content is client-rendered)"""
        response = requests.get(f"{BASE_URL}/", timeout=10)
        assert response.status_code == 200
        # React SPA returns HTML shell, content is client-rendered
        assert 'html' in response.text.lower()
        print("Homepage loads correctly")
    
    def test_cdn_logo_accessible(self):
        """Test Brightluxx logo is accessible"""
        # Use GET instead of HEAD as CDN may not support HEAD
        response = requests.get(f"{BASE_URL}/api/cdn/brightluxx_logo_white.webp", timeout=10)
        assert response.status_code == 200
        print(f"Logo accessible: {response.status_code}")


class TestChatEndpoint:
    """Test AURA chat endpoint still works"""
    
    def test_chat_message_endpoint(self):
        """Test chat message endpoint accepts requests"""
        response = requests.post(
            f"{BASE_URL}/api/chat/message",
            json={
                "session_id": "test_iteration_37",
                "message": "What LED displays do you offer?",
                "page_url": "/"
            },
            timeout=30
        )
        assert response.status_code == 200
        data = response.json()
        assert "response" in data
        print(f"Chat endpoint works, response length: {len(data['response'])} chars")
