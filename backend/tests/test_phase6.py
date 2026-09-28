import pytest
import datetime
from fastapi.testclient import TestClient
from app.main import app
from app.core.database import SessionLocal
from app.services.routing_service import evaluate_smart_routing
from app.services.escalation_service import evaluate_intelligent_escalation
from app.services.sla_service import calculate_conversation_sla, SLA_POLICY
from app.services.context_service import build_full_customer_context

client = TestClient(app)


def test_smart_routing_evaluation():
    """Verify smart routing department assignment, priority, and routing_reason."""
    res = evaluate_smart_routing("Order Delay", 85, "I've been waiting for my order for a week.")
    assert res["department_code"] == "ORDERS"
    assert res["recommended_department"] == "Order Fulfillment & Logistics"
    assert res["priority"] in ["URGENT", "HIGH"]
    assert res["confidence"] > 0.8
    assert "routing_reason" in res
    assert len(res["routing_reason"]) > 10


def test_unknown_category_fallback():
    """Verify unknown or unclassified customer intents fall back safely to 'Other / Unclassified'."""
    res = evaluate_smart_routing("Quantum Physics Query", 10, "What is string theory?")
    assert res["department_code"] == "OTHER"
    assert res["recommended_department"] == "Other / Unclassified"
    assert res["confidence"] > 0.5


def test_priority_calculation_rules():
    """Verify priority escalation logic for high stress and repeated complaints."""
    res_urgent = evaluate_smart_routing("Complaint", 85, "This is unacceptable, I demand a manager!")
    assert res_urgent["priority"] == "URGENT"
    assert res_urgent["is_sensitive"] is True

    res_normal = evaluate_smart_routing("General Inquiry", 15, "Hi, what are your opening hours?")
    assert res_normal["priority"] in ["NORMAL", "LOW"]
    assert res_normal["is_sensitive"] is False


def test_intelligent_escalation_recommendation():
    """Verify intelligent escalation recommendation and bulleted reasoning list."""
    ctx = {
        "repeated_issue": {"is_repeated_issue": True, "issue_type": "Repeated Issue"},
        "customer": {"tier": "VIP"}
    }
    esc = evaluate_intelligent_escalation(85, "I want to talk to a manager immediately!", ctx)
    assert esc["escalation_recommended"] is True
    assert esc["escalation_tier"] == "CRITICAL"
    assert len(esc["reasons_list"]) >= 2
    assert "CRITICAL" in esc["reasons_list"][0] or "85/100" in esc["reasons_list"][0]
    assert "recommended_action" in esc


def test_sensitive_and_complex_escalation():
    """Verify keyword triggers ('legal', 'manager', 'cancel') trigger escalation recommendations."""
    esc_legal = evaluate_intelligent_escalation(40, "I will take legal action if this is not resolved.", {})
    assert esc_legal["escalation_recommended"] is True
    assert "legal" in esc_legal["escalation_reason"].lower()


def test_dynamic_sla_calculation():
    """Verify dynamic SLA targets and deadline calculations for conversation priorities."""
    db = SessionLocal()
    try:
        sla = calculate_conversation_sla(db, 1, priority="HIGH")
        assert sla["priority"] == "HIGH"
        assert sla["first_response_target_minutes"] == SLA_POLICY["HIGH"]["first_response_mins"]
        assert sla["resolution_target_minutes"] == SLA_POLICY["HIGH"]["resolution_mins"]
        assert "response_deadline" in sla
        assert "resolution_deadline" in sla
    finally:
        db.close()


def test_sla_breach_and_at_risk_detection():
    """Verify past timestamp calculation triggers breach/at-risk states correctly."""
    db = SessionLocal()
    try:
        past_time = datetime.datetime.utcnow() + datetime.timedelta(hours=5)
        sla = calculate_conversation_sla(db, 1, priority="URGENT", now=past_time)
        assert sla["is_response_breached"] is True or sla["status"] in ["Response Breached", "Resolution Breached"]
    finally:
        db.close()


def test_analytics_overview_and_routing_endpoints():
    """Verify Phase 6 operations overview, routing, SLA, and escalation analytics APIs."""
    endpoints = [
        "/api/v1/analytics/overview",
        "/api/v1/analytics/routing",
        "/api/v1/analytics/sla",
        "/api/v1/analytics/escalation"
    ]
    for ep in endpoints:
        res = client.get(ep)
        assert res.status_code == 200, f"Endpoint {ep} failed with status {res.status_code}"
        assert res.headers["content-type"].startswith("application/json")


def test_full_end_to_end_flow_phase1_to_6():
    """
    Complete End-to-End Workflow Integration Test (Phases 1-6):
    Customer Message -> NLP -> Context -> Repeated Issue -> Smart Routing -> SLA -> Escalation -> Coaching -> Agent Reply -> Feedback -> CSAT
    """
    db = SessionLocal()
    try:
        # 1. Customer sends message
        msg_payload = {"conversation_id": 1, "content": "I've been waiting for my order for a week. This is very frustrating.", "sender_type": "customer"}
        resp_msg = client.post("/api/v1/chat/message", json=msg_payload)
        assert resp_msg.status_code == 200
        msg_data = resp_msg.json()

        # 2. Verify NLP & Context components
        assert msg_data["ai_analysis"]["intent"] in ["Order Delay / Logistics", "Order Status"]
        assert msg_data["ai_analysis"]["stress_score"] >= 70
        assert "coaching" in msg_data
        assert "smart_routing" in msg_data["context"]
        assert "sla_info" in msg_data["context"]
        assert "escalation_info" in msg_data["context"]

        # 3. Agent sends reply
        agent_payload = {
            "conversation_id": 1,
            "content": "I completely understand your frustration and am checking logistics escalation ticket #LOG-98213 now.",
            "action_type": "edited",
            "suggested_response": msg_data["coaching"]["suggested_response"]
        }
        resp_reply = client.post("/api/v1/chat/agent-reply", json=agent_payload)
        assert resp_reply.status_code == 200

        # 4. Customer submits CSAT & Outcome
        csat_payload = {"conversation_id": 1, "csat_rating": 5, "comments": "Resolved quickly!", "outcome": "Resolved"}
        resp_csat = client.post("/api/v1/coaching/csat", json=csat_payload)
        assert resp_csat.status_code == 200
        assert resp_csat.json()["outcome"] == "Resolved"

        # 5. Verify analytics overview reflects interaction
        resp_analytics = client.get("/api/v1/analytics/overview")
        assert resp_analytics.status_code == 200
        assert resp_analytics.json()["total_conversations"] > 0
    finally:
        db.close()
