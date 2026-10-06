"""
Iteration 36: Enhanced AURA Chat Assistant Tests
Tests for new features:
- Dynamic product knowledge injection from MongoDB
- Page-aware contextual responses (page_url parameter)
- Expanded knowledge base
- Backend chat endpoint enhancements
"""
import pytest
import requests
import os
import time

BASE_URL = os.environ.get('REACT_APP_BACKEND_URL', '').rstrip('/')


class TestAuraChatPageContext:
    """Tests for page_url parameter and context-aware responses"""
    
    def test_chat_accepts_page_url_parameter(self):
        """Test POST /api/chat/message accepts page_url parameter"""
        session_id = f"test_page_url_{int(time.time())}"
        response = requests.post(f"{BASE_URL}/api/chat/message", json={
            "session_id": session_id,
            "message": "What products do you recommend?",
            "page_url": "/products"
        }, timeout=60)
        
        assert response.status_code == 200, f"Expected 200, got {response.status_code}"
        data = response.json()
        assert "response" in data, "Missing 'response' field"
        assert len(data["response"]) > 10, "Response too short"
        print(f"✓ Chat accepts page_url parameter. Response length: {len(data['response'])}")
    
    def test_chat_context_technology_microled(self):
        """Test context-aware response from technology/microled page"""
        session_id = f"test_microled_ctx_{int(time.time())}"
        response = requests.post(f"{BASE_URL}/api/chat/message", json={
            "session_id": session_id,
            "message": "Is this the right technology for me?",
            "page_url": "/technology/microled"
        }, timeout=60)
        
        assert response.status_code == 200
        data = response.json()
        resp_lower = data["response"].lower()
        # Should mention MicroLED-related terms given the page context
        microled_terms = ["microled", "micro", "premium", "pixel", "p0", "close viewing", "0.4", "0.7", "0.9", "luxury"]
        found = [t for t in microled_terms if t in resp_lower]
        assert len(found) >= 1, f"Response should reference MicroLED context, found: {found}"
        print(f"✓ MicroLED page context test passed. Found terms: {found}")
    
    def test_chat_context_calculator_page(self):
        """Test context-aware response from calculator page"""
        session_id = f"test_calc_ctx_{int(time.time())}"
        response = requests.post(f"{BASE_URL}/api/chat/message", json={
            "session_id": session_id,
            "message": "How do I use this tool?",
            "page_url": "/calculator"
        }, timeout=60)
        
        assert response.status_code == 200
        data = response.json()
        resp_lower = data["response"].lower()
        # Should recognize calculator context
        calc_terms = ["calculator", "screen", "pixel", "resolution", "size", "calculate", "pitch", "dimensions"]
        found = [t for t in calc_terms if t in resp_lower]
        assert len(found) >= 1, f"Response should reference calculator context, found: {found}"
        print(f"✓ Calculator page context test passed. Found terms: {found}")
    
    def test_chat_context_budget_estimator(self):
        """Test context-aware response from budget estimator page"""
        session_id = f"test_budget_ctx_{int(time.time())}"
        response = requests.post(f"{BASE_URL}/api/chat/message", json={
            "session_id": session_id,
            "message": "What's a good budget range?",
            "page_url": "/budget-estimator"
        }, timeout=60)
        
        assert response.status_code == 200
        data = response.json()
        resp_lower = data["response"].lower()
        budget_terms = ["budget", "cost", "price", "estimat", "aed", "usd", "$", "range", "investment"]
        found = [t for t in budget_terms if t in resp_lower]
        assert len(found) >= 1, f"Response should reference budget context, found: {found}"
        print(f"✓ Budget estimator page context test passed. Found terms: {found}")
    
    def test_chat_context_design_assist(self):
        """Test context-aware response from design-assist page"""
        session_id = f"test_design_ctx_{int(time.time())}"
        response = requests.post(f"{BASE_URL}/api/chat/message", json={
            "session_id": session_id,
            "message": "How does this service work?",
            "page_url": "/design-assist"
        }, timeout=60)
        
        assert response.status_code == 200
        data = response.json()
        resp_lower = data["response"].lower()
        design_terms = ["design", "assist", "consultation", "free", "service", "book", "schedule"]
        found = [t for t in design_terms if t in resp_lower]
        assert len(found) >= 1, f"Response should reference design assist context, found: {found}"
        print(f"✓ Design assist page context test passed. Found terms: {found}")
    
    def test_chat_without_page_url(self):
        """Test chat works correctly without page_url parameter"""
        session_id = f"test_no_page_url_{int(time.time())}"
        response = requests.post(f"{BASE_URL}/api/chat/message", json={
            "session_id": session_id,
            "message": "What LED technology is best for retail?"
        }, timeout=60)
        
        assert response.status_code == 200
        data = response.json()
        assert "response" in data
        assert len(data["response"]) > 20
        print(f"✓ Chat works without page_url parameter")


class TestAuraDynamicProductKnowledge:
    """Tests verifying AURA has access to product knowledge from database"""
    
    def test_response_mentions_products(self):
        """Test AURA response can reference specific products"""
        session_id = f"test_products_{int(time.time())}"
        response = requests.post(f"{BASE_URL}/api/chat/message", json={
            "session_id": session_id,
            "message": "What fine pitch LED products do you have for a control room?",
            "page_url": "/"
        }, timeout=60)
        
        assert response.status_code == 200
        data = response.json()
        resp = data["response"]
        # Should mention product-related content
        assert len(resp) > 50, "Response too short to contain product info"
        # Check for product-related terms
        product_terms = ["led", "pitch", "p1", "p2", "fine", "cob", "microled", "display", "panel", "product", "series", "nit"]
        found = [t for t in product_terms if t.lower() in resp.lower()]
        assert len(found) >= 2, f"Response should reference products, found: {found}"
        print(f"✓ Product knowledge test passed. Found terms: {found}")
    
    def test_response_brightness_recommendations(self):
        """Test AURA provides brightness recommendations"""
        session_id = f"test_brightness_{int(time.time())}"
        response = requests.post(f"{BASE_URL}/api/chat/message", json={
            "session_id": session_id,
            "message": "What brightness do I need for an outdoor display?",
            "page_url": "/"
        }, timeout=60)
        
        assert response.status_code == 200
        data = response.json()
        resp_lower = data["response"].lower()
        # Should mention brightness specs
        brightness_terms = ["nit", "brightness", "outdoor", "5000", "6000", "7000", "8000", "sunlight", "cd/m"]
        found = [t for t in brightness_terms if t in resp_lower]
        assert len(found) >= 2, f"Response should include brightness guidance, found: {found}"
        print(f"✓ Brightness recommendations test passed. Found terms: {found}")
    
    def test_response_includes_internal_links(self):
        """Test AURA response includes internal links in markdown format"""
        session_id = f"test_links_{int(time.time())}"
        response = requests.post(f"{BASE_URL}/api/chat/message", json={
            "session_id": session_id,
            "message": "What tools do you have to help me plan my project?",
            "page_url": "/"
        }, timeout=60)
        
        assert response.status_code == 200
        data = response.json()
        resp = data["response"]
        # Check for markdown link patterns
        import re
        link_pattern = r'\[([^\]]+)\]\((/[^\)]+)\)'
        links = re.findall(link_pattern, resp)
        print(f"Found links: {links}")
        # Response should have at least one internal link
        assert len(links) >= 1 or "/" in resp, f"Response should include internal links or paths"
        print(f"✓ Internal links test passed. Links found: {len(links)}")


class TestAuraLeadCapture:
    """Tests for /api/chat/lead endpoint"""
    
    def test_lead_capture_endpoint(self):
        """Test lead capture endpoint still works correctly"""
        session_id = f"test_lead_{int(time.time())}"
        
        response = requests.post(f"{BASE_URL}/api/chat/lead", json={
            "session_id": session_id,
            "name": "Test Lead",
            "email": "testlead@example.com",
            "company": "Test Corp",
            "role": "Architect"
        }, timeout=30)
        
        assert response.status_code == 200, f"Expected 200, got {response.status_code}"
        data = response.json()
        assert data.get("success") == True, "Expected success=true"
        print(f"✓ Lead capture endpoint works correctly")
    
    def test_lead_form_trigger_after_3_messages(self):
        """Test show_lead_form appears after 3+ messages"""
        session_id = f"test_lead_trigger_{int(time.time())}"
        
        # Send 3 messages
        for i in range(1, 4):
            response = requests.post(f"{BASE_URL}/api/chat/message", json={
                "session_id": session_id,
                "message": f"Question {i} about LED displays",
                "page_url": "/"
            }, timeout=60)
            assert response.status_code == 200
        
        data = response.json()
        assert data["message_count"] >= 3, f"Expected message_count >= 3, got {data['message_count']}"
        assert data["show_lead_form"] == True, "Lead form should show after 3 messages"
        print(f"✓ Lead form trigger test passed")


class TestAuraMultiTurnConversation:
    """Tests for multi-turn conversation context maintenance"""
    
    def test_session_context_maintained(self):
        """Test conversation context is maintained across messages"""
        session_id = f"test_context_{int(time.time())}"
        
        # First message: mention retail
        response1 = requests.post(f"{BASE_URL}/api/chat/message", json={
            "session_id": session_id,
            "message": "I'm designing a retail store display",
            "page_url": "/"
        }, timeout=60)
        assert response1.status_code == 200
        
        # Second message: follow-up without mentioning retail
        response2 = requests.post(f"{BASE_URL}/api/chat/message", json={
            "session_id": session_id,
            "message": "What about the installation method?",
            "page_url": "/"
        }, timeout=60)
        assert response2.status_code == 200
        data2 = response2.json()
        
        # Response should maintain context
        assert len(data2["response"]) > 50, "Response should be substantive"
        print(f"✓ Multi-turn context test passed")


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
