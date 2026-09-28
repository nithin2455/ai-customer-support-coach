import pytest
from fastapi.testclient import TestClient
from app.main import app
from app.core.database import SessionLocal
from app.models.domain import Conversation, Message, CoachingFeedback

client = TestClient(app)


def test_simple_question_ai_auto_response():
    """
    DEMO 1: Simple & Safe Question Workflow.
    Customer asks: 'What are your delivery times?'
    AI must:
    1. Detect Simple + Safe query
    2. Automatically generate and send the answer
    3. Persist the response with sender_type='assistant'
    4. Mark status as resolved (AI Resolved)
    5. Require no human agent intervention
    """
    payload = {
        "conversation_id": 2,  # Priya Kumar's conversation
        "content": "What are your delivery times?",
        "sender_type": "customer"
    }
    response = client.post("/api/v1/chat/message", json=payload)
    assert response.status_code == 200
    data = response.json()

    # Verify AI Auto-Response Mode
    assert data["handling_mode"] in ["AI_AUTO_RESPONSE", "RULE_RESPONSE"]
    assert data["requires_human"] is False
    assert data["auto_resolved"] is True
    assert data["ai_response"] is not None
    assert "business days" in data["ai_response"].lower() or "delivery" in data["ai_response"].lower()

    # Verify that the AI response was actually persisted as a message in the conversation
    assert data["response_message"] is not None
    assert data["response_message"]["sender_type"] == "assistant"
    assert len(data["response_message"]["content"]) > 10

    # Verify conversation status in database
    conv_res = client.get("/api/v1/chat/conversation/2")
    assert conv_res.status_code == 200
    conv_data = conv_res.json()
    assert conv_data["status"] == "resolved"
    # Ensure customer can see the assistant message in the conversation thread
    messages = conv_data["messages"]
    assert any(m["sender_type"] == "assistant" and "delivery" in m["content"].lower() for m in messages)


def test_complex_question_human_handoff():
    """
    DEMO 2: Complex Customer Workflow.
    Customer says: 'I've been waiting for my order for a week. This is very frustrating.'
    AI must:
    1. Detect High Stress + Repeated Issue
    2. Route to Human Agent (handling_mode == 'HUMAN_AGENT')
    3. NOT auto-resolve or auto-send the resolution
    4. Generate AI coaching recommendations for the human agent
    """
    payload = {
        "conversation_id": 1,  # Alex Johnson's conversation
        "content": "I've been waiting for my order for a week. This is very frustrating.",
        "sender_type": "customer"
    }
    response = client.post("/api/v1/chat/message", json=payload)
    assert response.status_code == 200
    data = response.json()

    # Must require human agent
    assert data["handling_mode"] in ["HUMAN_AGENT", "HUMAN_HANDOFF"]
    assert data["requires_human"] is True
    assert data["auto_resolved"] is False

    # AI coaching must be present for human agent
    assert data["coaching"] is not None
    assert data["coaching"]["suggested_response"] is not None
    assert len(data["coaching"]["recommended_actions"]) > 0

    # Conversation status must remain active for human attention
    conv_res = client.get("/api/v1/chat/conversation/1")
    assert conv_res.status_code == 200
    assert conv_res.json()["status"] == "active"


def test_sensitive_billing_question_human_handoff():
    """
    Sensitive financial/billing dispute:
    Customer: 'I've been charged twice and I want a refund immediately.'
    AI must NOT automatically resolve; must route to human agent in Billing.
    """
    payload = {
        "conversation_id": 3,  # John Smith's conversation
        "content": "I've been charged twice and I want a refund immediately.",
        "sender_type": "customer"
    }
    response = client.post("/api/v1/chat/message", json=payload)
    assert response.status_code == 200
    data = response.json()

    assert data["handling_mode"] in ["HUMAN_AGENT", "HUMAN_HANDOFF"]
    assert data["requires_human"] is True
    assert data["auto_resolved"] is False
    assert "Billing" in data["routing"] or "Billing" in data["context"]["smart_routing"]["recommended_department"]


def test_high_stress_requires_human_agent():
    """
    High-stress customer message must always be handed to a human agent.
    """
    payload = {
        "conversation_id": 1,
        "content": "This service is completely terrible and unacceptable! I am furious!",
        "sender_type": "customer"
    }
    response = client.post("/api/v1/chat/message", json=payload)
    assert response.status_code == 200
    data = response.json()

    assert data["handling_mode"] in ["HUMAN_AGENT", "HUMAN_HANDOFF"]
    assert data["requires_human"] is True
    assert data["stress_score"] >= 60


def test_agent_final_response_and_coaching_feedback_persistence():
    """
    Verifies human agent retains total decision authority:
    Agent reviews suggestion, edits it, and sends final response.
    Ensures coaching feedback is recorded in database.
    """
    db = SessionLocal()
    try:
        reply_payload = {
            "conversation_id": 1,
            "content": "I sincerely apologize for the delay. I have checked with our logistics team and your package is scheduled for delivery tomorrow.",
            "action_type": "edited",
            "suggested_response": "I apologize for the delay. Let me check your order status."
        }
        res = client.post("/api/v1/chat/agent-reply", json=reply_payload)
        assert res.status_code == 200
        msg_out = res.json()
        assert msg_out["sender_type"] == "agent"
        assert "scheduled for delivery tomorrow" in msg_out["content"]

        # Check that CoachingFeedback was persisted in database
        fb = db.query(CoachingFeedback).filter(
            CoachingFeedback.conversation_id == 1,
            CoachingFeedback.agent_action == "edited"
        ).order_by(CoachingFeedback.created_at.desc()).first()

        assert fb is not None
        assert fb.agent_action == "edited"
        assert "scheduled for delivery tomorrow" in fb.actual_response
    finally:
        db.close()


def test_order_status_automated_answering_with_known_order():
    """
    When customer asks 'Where is my order #98213?', AI answers with concrete tracking details.
    """
    payload = {
        "conversation_id": 2,
        "content": "Where is my order #98213?",
        "sender_type": "customer"
    }
    response = client.post("/api/v1/chat/message", json=payload)
    assert response.status_code == 200
    data = response.json()

    assert data["handling_mode"] in ["AI_AUTO_RESPONSE", "RULE_RESPONSE"]
    assert data["requires_human"] is False
    assert "98213" in data["ai_response"]
    assert "shipped" in data["ai_response"].lower() or "arrive" in data["ai_response"].lower()
