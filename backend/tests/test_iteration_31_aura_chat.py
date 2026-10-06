"""
Iteration 31: AURA Chat Assistant Tests
Tests for POST /api/chat/message and POST /api/chat/lead endpoints
"""
import pytest
import requests
import os
import time

BASE_URL = os.environ.get('REACT_APP_BACKEND_URL', '').rstrip('/')


class TestAuraChatMessage:
    """Tests for /api/chat/message endpoint"""
    
    def test_chat_message_basic(self):
        """Test basic chat message returns response"""
        session_id = f"test_chat_basic_{int(time.time())}"
        response = requests.post(f"{BASE_URL}/api/chat/message", json={
            "session_id": session_id,
            "message": "Hello, what is MicroLED?"
        }, timeout=60)
        
        assert response.status_code == 200, f"Expected 200, got {response.status_code}"
        data = response.json()
        
        # Verify response structure
        assert "response" in data, "Missing 'response' field"
        assert "message_count" in data, "Missing 'message_count' field"
        assert "show_lead_form" in data, "Missing 'show_lead_form' field"
        
        # Verify response content
        assert isinstance(data["response"], str), "Response should be string"
        assert len(data["response"]) > 10, "Response too short"
        assert data["message_count"] == 1, f"Expected message_count=1, got {data['message_count']}"
        assert data["show_lead_form"] == False, "Lead form should not show after 1 message"
        
        print(f"✓ Basic chat message test passed. Response: {data['response'][:100]}...")
    
    def test_chat_response_led_relevance(self):
        """Test AI response is relevant to LED displays"""
        session_id = f"test_chat_led_{int(time.time())}"
        response = requests.post(f"{BASE_URL}/api/chat/message", json={
            "session_id": session_id,
            "message": "What pixel pitch should I use for a hotel lobby viewing distance of 3 meters?"
        }, timeout=60)
        
        assert response.status_code == 200
        data = response.json()
        
        # Verify response mentions LED-related terms
        resp_lower = data["response"].lower()
        led_terms = ["pixel", "pitch", "led", "mm", "p1", "p2", "display", "fine", "cob", "microled", "viewing"]
        found_terms = [term for term in led_terms if term in resp_lower]
        
        assert len(found_terms) >= 2, f"Response lacks LED-specific content. Only found: {found_terms}"
        print(f"✓ LED relevance test passed. Found terms: {found_terms}")
    
    def test_message_count_increments(self):
        """Test message_count increments with each message"""
        session_id = f"test_chat_count_{int(time.time())}"
        
        for i in range(1, 4):
            response = requests.post(f"{BASE_URL}/api/chat/message", json={
                "session_id": session_id,
                "message": f"Test message {i}"
            }, timeout=60)
            
            assert response.status_code == 200
            data = response.json()
            assert data["message_count"] == i, f"Expected message_count={i}, got {data['message_count']}"
            print(f"✓ Message {i} sent, count = {data['message_count']}")
        
        print(f"✓ Message count increment test passed")
    
    def test_show_lead_form_after_three_messages(self):
        """Test show_lead_form becomes true after 3+ messages"""
        session_id = f"test_chat_lead_gate_{int(time.time())}"
        
        # Send 2 messages - should NOT show lead form
        for i in range(1, 3):
            response = requests.post(f"{BASE_URL}/api/chat/message", json={
                "session_id": session_id,
                "message": f"Question {i}: Tell me about LED technology"
            }, timeout=60)
            data = response.json()
            assert data["show_lead_form"] == False, f"Lead form should not show after {i} messages"
            print(f"✓ After {i} messages: show_lead_form = False (correct)")
        
        # Send 3rd message - should show lead form
        response = requests.post(f"{BASE_URL}/api/chat/message", json={
            "session_id": session_id,
            "message": "Question 3: What about pricing?"
        }, timeout=60)
        data = response.json()
        assert data["message_count"] >= 3, f"Expected message_count>=3, got {data['message_count']}"
        assert data["show_lead_form"] == True, "Lead form SHOULD show after 3 messages"
        print(f"✓ After 3 messages: show_lead_form = True (correct)")
    
    def test_session_isolation(self):
        """Test different sessions have separate message counts"""
        session_1 = f"test_session_1_{int(time.time())}"
        session_2 = f"test_session_2_{int(time.time())}"
        
        # Send 2 messages to session 1
        for _ in range(2):
            requests.post(f"{BASE_URL}/api/chat/message", json={
                "session_id": session_1,
                "message": "Hello from session 1"
            }, timeout=60)
        
        # Send 1 message to session 2
        response = requests.post(f"{BASE_URL}/api/chat/message", json={
            "session_id": session_2,
            "message": "Hello from session 2"
        }, timeout=60)
        
        data = response.json()
        assert data["message_count"] == 1, f"Session 2 should have count=1, got {data['message_count']}"
        print(f"✓ Session isolation test passed")


class TestAuraChatLeadCapture:
    """Tests for /api/chat/lead endpoint"""
    
    def test_lead_capture_success(self):
        """Test successful lead capture"""
        session_id = f"test_lead_capture_{int(time.time())}"
        
        response = requests.post(f"{BASE_URL}/api/chat/lead", json={
            "session_id": session_id,
            "name": "Test User",
            "email": "test@example.com",
            "company": "Test Company",
            "role": "Architect"
        }, timeout=30)
        
        assert response.status_code == 200, f"Expected 200, got {response.status_code}"
        data = response.json()
        
        assert data.get("success") == True, "Expected success=true"
        assert "message" in data, "Missing success message"
        print(f"✓ Lead capture success: {data['message']}")
    
    def test_lead_capture_minimal_fields(self):
        """Test lead capture with minimal required fields"""
        session_id = f"test_lead_minimal_{int(time.time())}"
        
        response = requests.post(f"{BASE_URL}/api/chat/lead", json={
            "session_id": session_id,
            "name": "Min User",
            "email": "min@example.com",
            "company": "Min Company",
            "role": ""  # Role is optional
        }, timeout=30)
        
        assert response.status_code == 200
        data = response.json()
        assert data.get("success") == True
        print(f"✓ Lead capture with minimal fields passed")
    
    def test_show_lead_form_false_after_capture(self):
        """Test show_lead_form becomes false after lead capture"""
        session_id = f"test_lead_then_msg_{int(time.time())}"
        
        # Send 3 messages to trigger lead form
        for i in range(3):
            response = requests.post(f"{BASE_URL}/api/chat/message", json={
                "session_id": session_id,
                "message": f"Message {i+1}"
            }, timeout=60)
        
        data = response.json()
        assert data["show_lead_form"] == True, "Lead form should show after 3 messages"
        print(f"✓ Lead form showing after 3 messages")
        
        # Capture lead
        response = requests.post(f"{BASE_URL}/api/chat/lead", json={
            "session_id": session_id,
            "name": "Captured User",
            "email": "captured@example.com",
            "company": "Captured Company",
            "role": "Engineer"
        }, timeout=30)
        assert response.status_code == 200
        print(f"✓ Lead captured successfully")
        
        # Send another message - lead form should NOT show
        response = requests.post(f"{BASE_URL}/api/chat/message", json={
            "session_id": session_id,
            "message": "Message after lead capture"
        }, timeout=60)
        
        data = response.json()
        assert data["show_lead_form"] == False, "Lead form should NOT show after capture"
        print(f"✓ After lead capture: show_lead_form = False (correct)")


class TestAuraChatIntegration:
    """End-to-end integration tests"""
    
    def test_full_conversation_flow(self):
        """Test complete conversation flow with lead capture"""
        session_id = f"test_e2e_{int(time.time())}"
        
        # Step 1: Initial greeting
        response = requests.post(f"{BASE_URL}/api/chat/message", json={
            "session_id": session_id,
            "message": "Hi, I'm planning a hotel lobby display"
        }, timeout=60)
        assert response.status_code == 200
        data = response.json()
        assert data["message_count"] == 1
        print(f"✓ Step 1: Greeting sent")
        
        # Step 2: Technical question
        response = requests.post(f"{BASE_URL}/api/chat/message", json={
            "session_id": session_id,
            "message": "What brightness do I need for an indoor lobby with large windows?"
        }, timeout=60)
        assert response.status_code == 200
        data = response.json()
        assert data["message_count"] == 2
        assert "nits" in data["response"].lower() or "brightness" in data["response"].lower()
        print(f"✓ Step 2: Technical question answered")
        
        # Step 3: Follow-up triggers lead form
        response = requests.post(f"{BASE_URL}/api/chat/message", json={
            "session_id": session_id,
            "message": "What about pricing for a 3x2 meter display?"
        }, timeout=60)
        assert response.status_code == 200
        data = response.json()
        assert data["message_count"] >= 3
        assert data["show_lead_form"] == True
        print(f"✓ Step 3: Lead form triggered")
        
        # Step 4: Capture lead
        response = requests.post(f"{BASE_URL}/api/chat/lead", json={
            "session_id": session_id,
            "name": "E2E Test User",
            "email": "e2e@hotel.com",
            "company": "Grand Hotel LLC",
            "role": "Design Manager"
        }, timeout=30)
        assert response.status_code == 200
        print(f"✓ Step 4: Lead captured")
        
        # Step 5: Continue conversation without lead form
        response = requests.post(f"{BASE_URL}/api/chat/message", json={
            "session_id": session_id,
            "message": "Thanks! Can you recommend a specific model?"
        }, timeout=60)
        assert response.status_code == 200
        data = response.json()
        assert data["show_lead_form"] == False
        print(f"✓ Step 5: Conversation continues, lead form hidden")
        
        print(f"✓✓ Full conversation flow test passed!")


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
