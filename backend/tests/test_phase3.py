import pytest
from fastapi.testclient import TestClient
from app.main import app
from app.core.database import SessionLocal
from app.services.memory_service import get_customer_profile_summary, get_customer_timeline, get_customer_memory_summary
from app.services.repeated_issue_service import detect_repeated_issue
from app.services.context_service import build_full_customer_context
from app.ai.llm_coach import generate_coaching_recommendation

client = TestClient(app)


def test_customer_memory_and_profile_summary():
    db = SessionLocal()
    try:
        profile = get_customer_profile_summary(db, 1)
        assert profile["name"] == "Alex Johnson"
        assert profile["tier"] == "VIP"
        assert profile["badge"] in ["Repeated Issue Customer", "Returning Customer"]

        mem_summary = get_customer_memory_summary(db, 1)
        assert "Alex Johnson" in mem_summary["summary_text"]
        assert len(mem_summary["memories"]) > 0
    finally:
        db.close()


def test_customer_interaction_timeline():
    db = SessionLocal()
    try:
        timeline = get_customer_timeline(db, 1)
        assert isinstance(timeline, list)
        assert len(timeline) >= 2
        assert "Touchpoint 1" in timeline[0]["step"]
        assert timeline[0]["agent"] == "Sarah Jenkins"
    finally:
        db.close()


def test_repeated_issue_detection():
    db = SessionLocal()
    try:
        current_msg = "My order still hasn't arrived. I contacted support three days ago."
        current_intent = "Order Delay / Logistics"
        res = detect_repeated_issue(db, 1, current_msg, current_intent)
        assert res["is_repeated_issue"] is True
        assert res["issue_type"] in ["Repeated Issue", "Related Issue"]
        assert "previously contacted support" in res["reason"].lower() or "delay" in res["reason"].lower()
    finally:
        db.close()


def test_compiled_context_service():
    db = SessionLocal()
    try:
        context = build_full_customer_context(db, 1, "I've been waiting for my order for a week. This is very frustrating.")
        assert context["customer"]["name"] == "Alex Johnson"
        assert context["repeated_issue"]["is_repeated_issue"] is True
        assert len(context["timeline"]) > 0
        assert "agent_continuity" in context
    finally:
        db.close()


def test_history_aware_coaching():
    db = SessionLocal()
    try:
        context = build_full_customer_context(db, 1, "I've been waiting for my order for a week. This is very frustrating.")
        coaching = generate_coaching_recommendation(
            customer_message=context["current_message"],
            nlp_analysis=context["current_analysis"],
            stress_info=context["stress_info"],
            style_info=context["style_info"],
            memory_summary=context["memory_summary"],
            context_obj=context
        )

        assert coaching["is_repeated_issue"] is True
        assert "REPEATED ISSUE" in coaching["warning"]
        # History-aware rule: do not ask customer to repeat basic troubleshooting
        actions_str = " ".join(coaching["recommended_actions"]).lower()
        assert "troubleshooting" in actions_str or "logistics" in actions_str or "frustration" in actions_str
    finally:
        db.close()


def test_conversation_transfer_api():
    transfer_payload = {
        "new_agent_id": 2,
        "reason": "Escalating order delay to Senior Logistics Operations Agent"
    }
    response = client.post("/api/v1/chat/conversation/1/transfer", json=transfer_payload)
    assert response.status_code == 200
    data = response.json()
    assert data["is_transferred"] is True
    assert data["agent"]["name"] == "Michael Brown"
    assert data["previous_agent"]["name"] == "Sarah Jenkins"
    assert data["transfer_context"]["reason"] == transfer_payload["reason"]
