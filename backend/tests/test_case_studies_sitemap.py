"""
Case Studies and Sitemap API Tests
Tests for the new Case Studies section endpoints and sitemap integration.
"""
import pytest
import requests
import os

BASE_URL = os.environ.get('REACT_APP_BACKEND_URL', '').rstrip('/')

class TestSitemap:
    """Sitemap API tests - verify case study URLs are in sitemap"""
    
    def test_sitemap_returns_xml(self):
        """Test sitemap endpoint returns valid XML"""
        response = requests.get(f"{BASE_URL}/api/sitemap.xml")
        assert response.status_code == 200
        assert 'application/xml' in response.headers.get('content-type', '')
        assert '<?xml version="1.0"' in response.text
        print("SUCCESS: Sitemap returns valid XML")
    
    def test_sitemap_contains_case_studies_index(self):
        """Test sitemap contains /case-studies index page"""
        response = requests.get(f"{BASE_URL}/api/sitemap.xml")
        assert response.status_code == 200
        assert '/case-studies</loc>' in response.text
        print("SUCCESS: Sitemap contains case-studies index")
    
    def test_sitemap_contains_all_case_studies(self):
        """Test sitemap contains all 8 case study detail pages"""
        response = requests.get(f"{BASE_URL}/api/sitemap.xml")
        assert response.status_code == 200
        
        case_study_ids = [
            'jumeirah-al-naseem-lobby',
            'dubai-mall-flagship-retail',
            'adnoc-hq-command-center',
            'riyadh-metro-passenger-info',
            'expo-city-dubai-event-hall',
            'cleveland-clinic-abu-dhabi',
            'the-view-at-the-palm-transparent',
            'kapsarc-3d-anamorphic'
        ]
        
        found_count = 0
        for case_id in case_study_ids:
            url = f'/case-studies/{case_id}'
            if url in response.text:
                found_count += 1
                print(f"  Found: {case_id}")
            else:
                print(f"  MISSING: {case_id}")
        
        assert found_count == 8, f"Expected 8 case studies, found {found_count}"
        print(f"SUCCESS: All {found_count} case studies found in sitemap")


class TestTechnologyPagesRegression:
    """Regression tests - Technology pages still work"""
    
    def test_sitemap_contains_technology_index(self):
        """Test sitemap contains /technology index"""
        response = requests.get(f"{BASE_URL}/api/sitemap.xml")
        assert response.status_code == 200
        assert '/technology</loc>' in response.text or 'technology"' in response.text
        print("SUCCESS: Sitemap contains technology index")
    
    def test_sitemap_contains_technology_pages(self):
        """Test sitemap contains technology detail pages"""
        response = requests.get(f"{BASE_URL}/api/sitemap.xml")
        assert response.status_code == 200
        
        tech_ids = ['microled', 'cob-led', 'transparent-led', 'fine-pitch-led']
        for tech_id in tech_ids:
            assert f'/technology/{tech_id}' in response.text, f"Missing /technology/{tech_id}"
        
        print("SUCCESS: Technology pages in sitemap")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
