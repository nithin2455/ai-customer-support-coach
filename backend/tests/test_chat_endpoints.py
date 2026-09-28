import pytest
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)


def test_list_conversations_endpoint():
    response = client.get("/api/v1/chat/conversations")
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)
    assert len(data) > 0
    assert "customer" in data[0]
    assert data[0]["customer"]["name"] == "Alex Johnson"


def test_get_single_conversation_endpoint():
    response = client.get("/api/v1/chat/conversation/1")
    assert response.status_code == 200
    data = response.json()
    assert data["id"] == 1
    assert data["customer"]["name"] == "Alex Johnson"
    assert len(data["messages"]) > 0


def test_get_customer_profile_endpoint():
    response = client.get("/api/v1/chat/customer/1")
    assert response.status_code == 200
    data = response.json()
    assert data["id"] == 1
    assert data["name"] == "Alex Johnson"
    assert data["tier"] == "VIP"
    assert len(data["memories"]) > 0


def test_process_customer_demo_message_flow():
    demo_payload = {
        "conversation_id": 1,
        "content": "I've been waiting for my order for a week. This is very frustrating.",
        "sender_type": "customer"
    }
    response = client.post("/api/v1/chat/message", json=demo_payload)
    assert response.status_code == 200
    data = response.json()

    # Verify AI Analysis
    ai_an = data["ai_analysis"]
    assert "Order" in ai_an["intent"]
    assert ai_an["sentiment"] == "Negative"
    assert ai_an["emotion"] in ["Frustration", "Anger"]
    assert ai_an["stress_score"] >= 70

    # Verify AI Coaching Payload
    coaching = data["coaching"]
    assert coaching["warning"] is not None
    assert len(coaching["recommended_actions"]) > 0
    assert "frustrat" in coaching["suggested_response"].lower() or "sorry" in coaching["suggested_response"].lower()


def test_agent_reply_flow():
    reply_payload = {
        "conversation_id": 1,
        "content": "I completely understand how frustrating this delay must be. I am checking your order status right now.",
        "action_type": "edited",
        "suggested_response": "I completely understand how frustrating this delay must be, and I truly apologize for the inconvenience."
    }
    response = client.post("/api/v1/chat/agent-reply", json=reply_payload)
    assert response.status_code == 200
    data = response.json()
    assert data["sender_type"] == "agent"
    assert "checking your order status" in data["content"]
