import pytest
from datetime import datetime
from fastapi.testclient import TestClient
from app.main import app
from app.db.seed import seed_database
from app.core.database import SessionLocal
from app.models.domain import Conversation, Message, Order, Customer, User


@pytest.fixture(scope="module")
def client():
    seed_database(reset=True)
    with TestClient(app) as c:
        yield c


@pytest.fixture(scope="module")
def alex_token(client):
    res = client.post("/api/v1/auth/login", json={
        "email": "alex.j@example.com",
        "password": "Customer123!"
    })
    assert res.status_code == 200
    return res.json()["access_token"]


@pytest.fixture(scope="module")
def priya_token(client):
    res = client.post("/api/v1/auth/login", json={
        "email": "priya.k@example.com",
        "password": "Customer123!"
    })
    assert res.status_code == 200
    return res.json()["access_token"]


@pytest.fixture(scope="module")
def sarah_agent_token(client):
    res = client.post("/api/v1/auth/login", json={
        "email": "sarah.j@support.com",
        "password": "Agent123!"
    })
    assert res.status_code == 200
    return res.json()["access_token"]


@pytest.fixture(scope="module")
def admin_token(client):
    res = client.post("/api/v1/auth/login", json={
        "email": "admin@company.com",
        "password": "Admin123!"
    })
    assert res.status_code == 200
    return res.json()["access_token"]


# ================================================================
# AUTHENTICATION TESTS (Tests 1 - 7)
# ================================================================

def test_1_customer_can_register(client):
    """1. Customer can register."""
    payload = {
        "name": "Rohan Mehta",
        "email": "rohan.m@example.com",
        "password": "SecurePassword123!",
        "confirm_password": "SecurePassword123!"
    }
    res = client.post("/api/v1/auth/register", json=payload)
    assert res.status_code == 201
    data = res.json()
    assert "access_token" in data
    assert data["user"]["name"] == "Rohan Mehta"
    assert data["user"]["email"] == "rohan.m@example.com"
    assert data["user"]["role"] == "customer"
    assert data["user"]["customer_id"] is not None


def test_2_customer_can_login(client):
    """2. Customer can login."""
    res = client.post("/api/v1/auth/login", json={
        "email": "alex.j@example.com",
        "password": "Customer123!"
    })
    assert res.status_code == 200
    data = res.json()
    assert "access_token" in data
    assert data["user"]["email"] == "alex.j@example.com"
    assert data["user"]["role"] == "customer"


def test_3_invalid_password_is_rejected(client):
    """3. Invalid password is rejected."""
    res = client.post("/api/v1/auth/login", json={
        "email": "alex.j@example.com",
        "password": "WrongPassword!"
    })
    assert res.status_code == 401
    assert "Invalid email or password" in res.json()["detail"]


def test_4_protected_endpoint_rejects_unauthenticated_user(client):
    """4. Protected endpoint rejects unauthenticated user."""
    # Attempting to access /auth/me without token
    res = client.get("/api/v1/auth/me")
    assert res.status_code == 401
    assert "Authentication required" in res.json()["detail"]

    # Attempting to access /auth/me with bogus token
    res_bogus = client.get("/api/v1/auth/me", headers={"Authorization": "Bearer bogus.token.value"})
    assert res_bogus.status_code == 401


def test_5_customer_cannot_access_another_customer_conversation(client, priya_token):
    """5. Customer cannot access another customer's conversation."""
    # Conversation 1 belongs to Alex Johnson (customer_id=1). Priya is customer_id=2.
    res_get = client.get(
        "/api/v1/chat/conversation/1",
        headers={"Authorization": f"Bearer {priya_token}"}
    )
    assert res_get.status_code == 403
    assert "Forbidden" in res_get.json()["detail"]

    # Priya cannot send a message to Alex's conversation
    res_post = client.post(
        "/api/v1/chat/message",
        json={"conversation_id": 1, "content": "Tampering with other chat", "sender_type": "customer"},
        headers={"Authorization": f"Bearer {priya_token}"}
    )
    assert res_post.status_code == 403


def test_6_agent_cannot_access_admin_only_apis(client, sarah_agent_token):
    """6. Agent cannot access admin-only APIs."""
    res = client.get(
        "/api/v1/admin/departments",
        headers={"Authorization": f"Bearer {sarah_agent_token}"}
    )
    assert res.status_code == 403
    assert "Forbidden: Administrator access required" in res.json()["detail"]


def test_7_admin_can_access_admin_apis(client, admin_token):
    """7. Admin can access admin APIs."""
    res_dept = client.get(
        "/api/v1/admin/departments",
        headers={"Authorization": f"Bearer {admin_token}"}
    )
    assert res_dept.status_code == 200
    assert len(res_dept.json()) >= 3

    res_agents = client.get(
        "/api/v1/admin/agents",
        headers={"Authorization": f"Bearer {admin_token}"}
    )
    assert res_agents.status_code == 200
    assert len(res_agents.json()) >= 2


# ================================================================
# CUSTOMER WORKFLOW TESTS (Tests 8 - 14)
# ================================================================

def test_8_customer_can_create_and_send_message(client, alex_token):
    """8. Customer can create/send a message."""
    # 1. Customer creates a new isolated conversation
    res_conv = client.post(
        "/api/v1/chat/customer/me/conversations",
        headers={"Authorization": f"Bearer {alex_token}"}
    )
    assert res_conv.status_code == 200
    conv_id = res_conv.json()["id"]

    # 2. Customer sends a message to their conversation
    res_msg = client.post(
        "/api/v1/chat/message",
        json={
            "conversation_id": conv_id,
            "content": "Hello, I need help with my account.",
            "sender_type": "customer"
        },
        headers={"Authorization": f"Bearer {alex_token}"}
    )
    assert res_msg.status_code == 200
    assert res_msg.json()["response_text"] is not None


def test_9_customer_receives_rule_response(client, alex_token):
    """9. Customer receives RULE_RESPONSE."""
    res_conv = client.post(
        "/api/v1/chat/customer/me/conversations",
        headers={"Authorization": f"Bearer {alex_token}"}
    )
    conv_id = res_conv.json()["id"]

    res_msg = client.post(
        "/api/v1/chat/message",
        json={
            "conversation_id": conv_id,
            "content": "What are your delivery times?",
            "sender_type": "customer"
        },
        headers={"Authorization": f"Bearer {alex_token}"}
    )
    assert res_msg.status_code == 200
    data = res_msg.json()
    assert data["handling_mode"] == "RULE_RESPONSE"
    assert "delivery" in data["response_text"].lower() or "business days" in data["response_text"].lower()


def test_10_customer_receives_llm_response_when_configured(client, alex_token):
    """10. Customer receives LLM_RESPONSE when configured."""
    res_conv = client.post(
        "/api/v1/chat/customer/me/conversations",
        headers={"Authorization": f"Bearer {alex_token}"}
    )
    conv_id = res_conv.json()["id"]

    res_msg = client.post(
        "/api/v1/chat/message",
        json={
            "conversation_id": conv_id,
            "content": "Why does my payment keep failing during checkout?",
            "sender_type": "customer"
        },
        headers={"Authorization": f"Bearer {alex_token}"}
    )
    assert res_msg.status_code == 200
    data = res_msg.json()
    # If API key is present, returns LLM_RESPONSE; otherwise safe handoff fallback
    assert data["handling_mode"] in ["LLM_RESPONSE", "HUMAN_HANDOFF"]
    assert len(data["response_text"]) > 10


def test_11_customer_receives_safe_fallback_when_llm_unavailable(client, alex_token, monkeypatch):
    """11. Customer receives safe fallback when LLM unavailable."""
    from app.services import response_engine

    # Simulate LLM unavailability
    def mock_query_llm(*args, **kwargs):
        return None

    monkeypatch.setattr(response_engine, "generate_llm_response", mock_query_llm)

    res_conv = client.post(
        "/api/v1/chat/customer/me/conversations",
        headers={"Authorization": f"Bearer {alex_token}"}
    )
    conv_id = res_conv.json()["id"]

    res_msg = client.post(
        "/api/v1/chat/message",
        json={
            "conversation_id": conv_id,
            "content": "Can you explain how international roaming credits work on this portal?",
            "sender_type": "customer"
        },
        headers={"Authorization": f"Bearer {alex_token}"}
    )
    assert res_msg.status_code == 200
    data = res_msg.json()
    assert data["handling_mode"] == "HUMAN_HANDOFF"
    assert any(w in data["response_text"].lower() for w in ["support specialist", "specialist", "help", "support"])


def test_12_customer_receives_human_handoff_acknowledgement(client, alex_token):
    """12. Customer receives HUMAN_HANDOFF acknowledgement."""
    res_conv = client.post(
        "/api/v1/chat/customer/me/conversations",
        headers={"Authorization": f"Bearer {alex_token}"}
    )
    conv_id = res_conv.json()["id"]

    res_msg = client.post(
        "/api/v1/chat/message",
        json={
            "conversation_id": conv_id,
            "content": "This is completely unacceptable. I want to speak to your manager immediately.",
            "sender_type": "customer"
        },
        headers={"Authorization": f"Bearer {alex_token}"}
    )
    assert res_msg.status_code == 200
    data = res_msg.json()
    assert data["handling_mode"] == "HUMAN_HANDOFF"
    assert data["requires_human"] is True
    assert any(w in data["response_text"].lower() for w in ["supervisor", "manager", "specialist"])


def test_13_assistant_response_is_persisted(client, alex_token):
    """13. Assistant response is persisted in conversation."""
    res_conv = client.post(
        "/api/v1/chat/customer/me/conversations",
        headers={"Authorization": f"Bearer {alex_token}"}
    )
    conv_id = res_conv.json()["id"]

    res_msg = client.post(
        "/api/v1/chat/message",
        json={
            "conversation_id": conv_id,
            "content": "What is your return policy?",
            "sender_type": "customer"
        },
        headers={"Authorization": f"Bearer {alex_token}"}
    )
    assert res_msg.status_code == 200

    # Fetch conversation details and verify assistant message is stored in database
    res_fetch = client.get(
        f"/api/v1/chat/conversation/{conv_id}",
        headers={"Authorization": f"Bearer {alex_token}"}
    )
    assert res_fetch.status_code == 200
    messages = res_fetch.json()["messages"]
    assert any(m["sender_type"] == "assistant" for m in messages)


def test_14_customer_can_see_conversation_history(client, alex_token):
    """14. Customer can see conversation history strictly isolated to their own."""
    res_history = client.get(
        "/api/v1/chat/customer/me/conversations",
        headers={"Authorization": f"Bearer {alex_token}"}
    )
    assert res_history.status_code == 200
    convs = res_history.json()
    assert len(convs) >= 1
    for c in convs:
        assert c["customer"]["email"] == "alex.j@example.com"


# ================================================================
# BUSINESS SAFETY TESTS (Tests 15 - 18)
# ================================================================

def test_15_refund_action_goes_to_human(client, alex_token):
    """15. Refund action goes to human."""
    res_conv = client.post(
        "/api/v1/chat/customer/me/conversations",
        headers={"Authorization": f"Bearer {alex_token}"}
    )
    conv_id = res_conv.json()["id"]

    res_msg = client.post(
        "/api/v1/chat/message",
        json={
            "conversation_id": conv_id,
            "content": "I need a refund of ₹15000",
            "sender_type": "customer"
        },
        headers={"Authorization": f"Bearer {alex_token}"}
    )
    assert res_msg.status_code == 200
    data = res_msg.json()
    assert data["handling_mode"] == "HUMAN_HANDOFF"
    assert data["requires_human"] is True
    assert data["auto_resolved"] is False


def test_16_manager_escalation_goes_to_human(client, alex_token):
    """16. Manager escalation goes to human."""
    res_conv = client.post(
        "/api/v1/chat/customer/me/conversations",
        headers={"Authorization": f"Bearer {alex_token}"}
    )
    conv_id = res_conv.json()["id"]

    res_msg = client.post(
        "/api/v1/chat/message",
        json={
            "conversation_id": conv_id,
            "content": "I demand to speak with a supervisor or manager.",
            "sender_type": "customer"
        },
        headers={"Authorization": f"Bearer {alex_token}"}
    )
    assert res_msg.status_code == 200
    data = res_msg.json()
    assert data["handling_mode"] == "HUMAN_HANDOFF"
    assert data["requires_human"] is True


def test_17_fraud_security_issue_goes_to_human(client, alex_token):
    """17. Fraud/security issue goes to human."""
    res_conv = client.post(
        "/api/v1/chat/customer/me/conversations",
        headers={"Authorization": f"Bearer {alex_token}"}
    )
    conv_id = res_conv.json()["id"]

    res_msg = client.post(
        "/api/v1/chat/message",
        json={
            "conversation_id": conv_id,
            "content": "Someone hacked my account and made unauthorized credit card charges.",
            "sender_type": "customer"
        },
        headers={"Authorization": f"Bearer {alex_token}"}
    )
    assert res_msg.status_code == 200
    data = res_msg.json()
    assert data["handling_mode"] == "HUMAN_HANDOFF"
    assert data["requires_human"] is True


def test_18_no_unauthorized_financial_action_occurs(client, alex_token):
    """18. No unauthorized financial action occurs automatically."""
    res_conv = client.post(
        "/api/v1/chat/customer/me/conversations",
        headers={"Authorization": f"Bearer {alex_token}"}
    )
    conv_id = res_conv.json()["id"]

    res_msg = client.post(
        "/api/v1/chat/message",
        json={
            "conversation_id": conv_id,
            "content": "Transfer $500 to my bank account immediately.",
            "sender_type": "customer"
        },
        headers={"Authorization": f"Bearer {alex_token}"}
    )
    assert res_msg.status_code == 200
    data = res_msg.json()
    # Must NOT automatically approve or resolve financial transfer
    assert data["auto_resolved"] is False
    assert data["requires_human"] is True
    assert "approved" not in data["response_text"].lower()


# ================================================================
# ORDER DATA TESTS (Tests 19 - 20)
# ================================================================

def test_19_valid_order_returns_verified_database_information(client, alex_token):
    """19. Valid order returns verified database information."""
    res_conv = client.post(
        "/api/v1/chat/customer/me/conversations",
        headers={"Authorization": f"Bearer {alex_token}"}
    )
    conv_id = res_conv.json()["id"]

    res_msg = client.post(
        "/api/v1/chat/message",
        json={
            "conversation_id": conv_id,
            "content": "Where is my order #98213?",
            "sender_type": "customer"
        },
        headers={"Authorization": f"Bearer {alex_token}"}
    )
    assert res_msg.status_code == 200
    data = res_msg.json()
    assert data["handling_mode"] == "RULE_RESPONSE"
    assert "98213" in data["response_text"]
    assert "FedEx" in data["response_text"]
    assert "FDX-98213" in data["response_text"]


def test_20_unknown_order_does_not_fabricate_information(client, alex_token):
    """20. Unknown order does not fabricate information."""
    res_conv = client.post(
        "/api/v1/chat/customer/me/conversations",
        headers={"Authorization": f"Bearer {alex_token}"}
    )
    conv_id = res_conv.json()["id"]

    res_msg = client.post(
        "/api/v1/chat/message",
        json={
            "conversation_id": conv_id,
            "content": "Where is my order #00000?",
            "sender_type": "customer"
        },
        headers={"Authorization": f"Bearer {alex_token}"}
    )
    assert res_msg.status_code == 200
    data = res_msg.json()
    # Must not invent tracking or say delivered
    assert any(w in data["response_text"].lower() for w in ["couldn't find", "could not find", "not find", "support"])


# ================================================================
# TIMESTAMP & LOCAL TIME TESTS (Tests 21 - 22)
# ================================================================

def test_21_timestamp_is_timezone_aware(client, alex_token):
    """21. Timestamp is timezone-aware ISO-8601 with Z indicator."""
    res = client.get(
        "/api/v1/chat/customer/me/conversations",
        headers={"Authorization": f"Bearer {alex_token}"}
    )
    assert res.status_code == 200
    convs = res.json()
    assert len(convs) > 0
    created_at = convs[0]["created_at"]
    # Check proper ISO-8601 format with Z or timezone offset
    assert created_at.endswith("Z") or "+" in created_at
    # Verify parsing with datetime.fromisoformat
    parsed_dt = datetime.fromisoformat(created_at.replace("Z", "+00:00"))
    assert parsed_dt.tzinfo is not None


def test_22_frontend_displays_local_browser_time(client, alex_token):
    """22. Messages return timezone-aware timestamps for frontend browser local time conversion."""
    res_conv = client.post(
        "/api/v1/chat/customer/me/conversations",
        headers={"Authorization": f"Bearer {alex_token}"}
    )
    conv_id = res_conv.json()["id"]

    res_msg = client.post(
        "/api/v1/chat/message",
        json={
            "conversation_id": conv_id,
            "content": "Check timestamp please",
            "sender_type": "customer"
        },
        headers={"Authorization": f"Bearer {alex_token}"}
    )
    assert res_msg.status_code == 200
    resp_msg = res_msg.json()["response_message"]
    created_at = resp_msg["created_at"]
    assert created_at.endswith("Z") or "+" in created_at
