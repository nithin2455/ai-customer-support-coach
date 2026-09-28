import pytest
from unittest.mock import patch
from fastapi.testclient import TestClient
from app.main import app
from app.core.database import SessionLocal
from app.models.domain import Conversation, Message, Order

client = TestClient(app)


# ==============================================================================
# 1. "Hi" → AI response (RULE_RESPONSE)
# ==============================================================================
def test_case_1_greeting():
    payload = {
        "conversation_id": 2,
        "content": "Hi",
        "sender_type": "customer"
    }
    response = client.post("/api/v1/chat/message", json=payload)
    assert response.status_code == 200
    data = response.json()

    assert data["handling_mode"] == "RULE_RESPONSE"
    assert data["requires_human"] is False
    assert data["auto_resolved"] is True
    assert "welcome to customer support" in data["response_message"]["content"].lower()


# ==============================================================================
# 2. "What are your delivery times?" → RULE_RESPONSE
# ==============================================================================
def test_case_2_delivery_times():
    payload = {
        "conversation_id": 2,
        "content": "What are your delivery times?",
        "sender_type": "customer"
    }
    response = client.post("/api/v1/chat/message", json=payload)
    assert response.status_code == 200
    data = response.json()

    assert data["handling_mode"] == "RULE_RESPONSE"
    assert data["requires_human"] is False
    assert data["auto_resolved"] is True
    assert "3–5 business days" in data["response_message"]["content"] or "business days" in data["response_message"]["content"].lower()


# ==============================================================================
# 3. "Where is my order #98213?" → RULE_RESPONSE + database lookup
# ==============================================================================
def test_case_3_order_status_known_database_lookup():
    payload = {
        "conversation_id": 1,
        "content": "Where is my order #98213?",
        "sender_type": "customer"
    }
    response = client.post("/api/v1/chat/message", json=payload)
    assert response.status_code == 200
    data = response.json()

    assert data["handling_mode"] == "RULE_RESPONSE"
    assert data["requires_human"] is False
    assert "98213" in data["response_message"]["content"]
    assert "fedex" in data["response_message"]["content"].lower()
    assert "tomorrow by 5:00 pm" in data["response_message"]["content"].lower()

    # Also test non-existent order
    payload_fake = {
        "conversation_id": 1,
        "content": "Where is my order #99999?",
        "sender_type": "customer"
    }
    res_fake = client.post("/api/v1/chat/message", json=payload_fake)
    assert res_fake.status_code == 200
    data_fake = res_fake.json()
    assert data_fake["handling_mode"] == "RULE_RESPONSE"
    assert "couldn't find order #99999" in data_fake["response_message"]["content"].lower()


# ==============================================================================
# 4. "What is your refund policy?" → RULE_RESPONSE
# ==============================================================================
def test_case_4_refund_policy():
    payload = {
        "conversation_id": 2,
        "content": "What is your refund policy?",
        "sender_type": "customer"
    }
    response = client.post("/api/v1/chat/message", json=payload)
    assert response.status_code == 200
    data = response.json()

    assert data["handling_mode"] == "RULE_RESPONSE"
    assert data["requires_human"] is False
    assert data["auto_resolved"] is True
    assert "refund" in data["response_message"]["content"].lower()
    assert "5–7 business days" in data["response_message"]["content"] or "business days" in data["response_message"]["content"]


# ==============================================================================
# 5. "I need a refund of ₹15000" → HUMAN_HANDOFF + customer acknowledgement
# ==============================================================================
def test_case_5_refund_request_human_handoff():
    payload = {
        "conversation_id": 1,
        "content": "I need a refund of ₹15000",
        "sender_type": "customer"
    }
    response = client.post("/api/v1/chat/message", json=payload)
    assert response.status_code == 200
    data = response.json()

    # Must NOT auto resolve or approve refund
    assert data["handling_mode"] == "HUMAN_HANDOFF"
    assert data["requires_human"] is True
    assert data["auto_resolved"] is False

    # Customer must receive an immediate acknowledgement
    content = data["response_message"]["content"]
    assert "support specialist" in content.lower() or "support team" in content.lower()
    assert "refund" in content.lower()

    # Conversation must be active in human agent queue
    conv_res = client.get("/api/v1/chat/conversation/1")
    assert conv_res.status_code == 200
    assert conv_res.json()["status"] == "active"


# ==============================================================================
# 6. "My payment keeps failing, what should I do?" → LLM_RESPONSE or safe fallback
# ==============================================================================
def test_case_6_payment_troubleshooting():
    # Test with mocked active LLM response
    mock_reply = "Please verify your billing address matches your card and check with your bank if international charges are enabled."
    with patch("app.services.response_engine.generate_llm_response") as mock_llm:
        mock_llm.return_value = {
            "success": True,
            "response_text": mock_reply,
            "is_fallback": False,
            "error": None
        }
        payload = {
            "conversation_id": 2,
            "content": "My payment keeps failing, what should I do?",
            "sender_type": "customer"
        }
        response = client.post("/api/v1/chat/message", json=payload)
        assert response.status_code == 200
        data = response.json()

        assert data["handling_mode"] == "LLM_RESPONSE"
        assert data["requires_human"] is False
        assert mock_reply in data["response_message"]["content"]


# ==============================================================================
# 7. "Can you explain how express delivery works?" → LLM_RESPONSE or safe fallback
# ==============================================================================
def test_case_7_express_delivery_explanation():
    mock_reply = "Express delivery ships your package with priority handling to arrive within 1–2 business days via FedEx."
    with patch("app.services.response_engine.generate_llm_response") as mock_llm:
        mock_llm.return_value = {
            "success": True,
            "response_text": mock_reply,
            "is_fallback": False,
            "error": None
        }
        payload = {
            "conversation_id": 2,
            "content": "Can you explain how express delivery works?",
            "sender_type": "customer"
        }
        response = client.post("/api/v1/chat/message", json=payload)
        assert response.status_code == 200
        data = response.json()

        assert data["handling_mode"] == "LLM_RESPONSE"
        assert data["requires_human"] is False
        assert mock_reply in data["response_message"]["content"]


# ==============================================================================
# 8. "I've contacted support three times and nobody is helping me" → HUMAN_HANDOFF
# ==============================================================================
def test_case_8_repeated_unresolved_complaint():
    payload = {
        "conversation_id": 1,
        "content": "I've contacted support three times and nobody is helping me",
        "sender_type": "customer"
    }
    response = client.post("/api/v1/chat/message", json=payload)
    assert response.status_code == 200
    data = response.json()

    assert data["handling_mode"] == "HUMAN_HANDOFF"
    assert data["requires_human"] is True
    assert data["auto_resolved"] is False
    assert "support specialist" in data["response_message"]["content"].lower() or "multiple times" in data["response_message"]["content"].lower()


# ==============================================================================
# 9. "This is unacceptable. I want to speak to your manager." → HUMAN_HANDOFF
# ==============================================================================
def test_case_9_manager_escalation():
    payload = {
        "conversation_id": 1,
        "content": "This is unacceptable. I want to speak to your manager.",
        "sender_type": "customer"
    }
    response = client.post("/api/v1/chat/message", json=payload)
    assert response.status_code == 200
    data = response.json()

    assert data["handling_mode"] == "HUMAN_HANDOFF"
    assert data["requires_human"] is True
    assert data["auto_resolved"] is False
    assert "manager" in data["response_message"]["content"].lower() or "supervisor" in data["response_message"]["content"].lower()


# ==============================================================================
# 10. Unknown / general question → LLM_RESPONSE or safe fallback
# ==============================================================================
def test_case_10_unknown_general_question():
    mock_reply = "We offer complimentary festive gift wrapping on all seasonal gift purchases during checkout."
    with patch("app.services.response_engine.generate_llm_response") as mock_llm:
        mock_llm.return_value = {
            "success": True,
            "response_text": mock_reply,
            "is_fallback": False,
            "error": None
        }
        payload = {
            "conversation_id": 2,
            "content": "Do you offer gift wrapping options for holiday gifts?",
            "sender_type": "customer"
        }
        response = client.post("/api/v1/chat/message", json=payload)
        assert response.status_code == 200
        data = response.json()

        assert data["handling_mode"] == "LLM_RESPONSE"
        assert data["requires_human"] is False
        assert mock_reply in data["response_message"]["content"]


# ==============================================================================
# 11. LLM API failure → Safe fallback response + HUMAN_HANDOFF
# ==============================================================================
def test_case_11_llm_failure_graceful_fallback():
    with patch("app.services.response_engine.generate_llm_response") as mock_llm:
        mock_llm.return_value = {
            "success": False,
            "response_text": "I'm sorry, I couldn't complete that request automatically. I've sent your request to a support specialist so you can still get help.",
            "is_fallback": True,
            "error": "APIConnectionError: Connection timed out"
        }
        payload = {
            "conversation_id": 2,
            "content": "Can you check if you have eco-friendly packaging?",
            "sender_type": "customer"
        }
        response = client.post("/api/v1/chat/message", json=payload)
        assert response.status_code == 200
        data = response.json()

        assert data["handling_mode"] == "HUMAN_HANDOFF"
        assert data["requires_human"] is True
        assert data["auto_resolved"] is False
        assert "couldn't complete that request automatically" in data["response_message"]["content"].lower()


# ==============================================================================
# 12. Missing OPENAI_API_KEY → App works, no crash, safe fallback returned
# ==============================================================================
def test_case_12_missing_openai_api_key_works():
    with patch("app.services.llm_response_service.get_openai_api_key", return_value=""), \
         patch("app.services.llm_response_service.get_gemini_api_key", return_value=""):
        payload = {
            "conversation_id": 2,
            "content": "How do you handle sustainable manufacturing?",
            "sender_type": "customer"
        }
        response = client.post("/api/v1/chat/message", json=payload)
        assert response.status_code == 200
        data = response.json()

        # Must not crash; returns safe handoff fallback
        assert data["handling_mode"] == "HUMAN_HANDOFF"
        assert data["requires_human"] is True
        assert "support specialist" in data["response_message"]["content"].lower()

        # Rule-based questions still work even without API key
        rule_payload = {
            "conversation_id": 2,
            "content": "What are your business hours?",
            "sender_type": "customer"
        }
        rule_response = client.post("/api/v1/chat/message", json=rule_payload)
        assert rule_response.status_code == 200
        assert rule_response.json()["handling_mode"] == "RULE_RESPONSE"
        assert "monday through friday" in rule_response.json()["response_message"]["content"].lower()


def test_case_12_missing_gemini_api_key_works():
    with patch("app.services.llm_response_service.get_gemini_api_key", return_value=""):
        payload = {
            "conversation_id": 2,
            "content": "How do you handle sustainable manufacturing?",
            "sender_type": "customer"
        }
        response = client.post("/api/v1/chat/message", json=payload)
        assert response.status_code == 200
        data = response.json()

        # Must not crash; returns safe handoff fallback
        assert data["handling_mode"] == "HUMAN_HANDOFF"
        assert data["requires_human"] is True
        assert "support specialist" in data["response_message"]["content"].lower()

        # Rule-based questions still work even without API key
        rule_payload = {
            "conversation_id": 2,
            "content": "What are your business hours?",
            "sender_type": "customer"
        }
        rule_response = client.post("/api/v1/chat/message", json=rule_payload)
        assert rule_response.status_code == 200
        assert rule_response.json()["handling_mode"] == "RULE_RESPONSE"
        assert "monday through friday" in rule_response.json()["response_message"]["content"].lower()


# ==============================================================================
# 13. Message Persistence: Both Customer & Assistant message saved in DB
# ==============================================================================
def test_message_persistence_both_sides():
    db = SessionLocal()
    try:
        initial_count = db.query(Message).filter(Message.conversation_id == 2).count()
        payload = {
            "conversation_id": 2,
            "content": "What payment methods do you accept?",
            "sender_type": "customer"
        }
        res = client.post("/api/v1/chat/message", json=payload)
        assert res.status_code == 200

        after_count = db.query(Message).filter(Message.conversation_id == 2).count()
        # Exactly 2 messages added: 1 customer message + 1 assistant message
        assert after_count == initial_count + 2

        last_msgs = db.query(Message).filter(Message.conversation_id == 2).order_by(Message.id.desc()).limit(2).all()
        assistant_m = last_msgs[0]
        customer_m = last_msgs[1]

        assert customer_m.sender_type == "customer"
        assert customer_m.content == "What payment methods do you accept?"
        assert assistant_m.sender_type == "assistant"
        assert "visa" in assistant_m.content.lower() or "payment" in assistant_m.content.lower()
    finally:
        db.close()
