import pytest
from fastapi.testclient import TestClient
from app.main import app
from app.core.database import SessionLocal
from app.ai.llm_coach import generate_coaching_recommendation
from app.services.context_service import build_full_customer_context

client = TestClient(app)


def test_style_aware_coaching():
    """Verify coaching strategy adapts to communication style (Impatient/Direct vs Detailed/Analytical vs Confused)."""
    db = SessionLocal()
    try:
        context = build_full_customer_context(db, 1, "I need my order status right now without excuses.")
        
        # Test Impatient / Direct style
        coaching_direct = generate_coaching_recommendation(
            customer_message="I need my order status right now without excuses.",
            nlp_analysis={"intent": "Order Status", "sentiment": "Negative", "emotion": "Frustrated"},
            stress_info={"score": 75, "level": "HIGH"},
            style_info={"style": "Impatient / Direct", "guidance": "Be direct and concise."},
            memory_summary=context["memory_summary"],
            context_obj=context
        )
        assert coaching_direct["coaching_strategy"]["tone"] == "Empathetic and direct"
        assert coaching_direct["coaching_strategy"]["response_length"] == "Concise"
        assert "troubleshooting" in coaching_direct["coaching_strategy"]["avoid"].lower() or "explanations" in coaching_direct["coaching_strategy"]["avoid"].lower()

        # Test Detailed / Analytical style
        coaching_detailed = generate_coaching_recommendation(
            customer_message="Can you break down the shipping timeline and carrier logs?",
            nlp_analysis={"intent": "Logistics Inquiry", "sentiment": "Neutral", "emotion": "Calm"},
            stress_info={"score": 20, "level": "LOW"},
            style_info={"style": "Detailed / Analytical", "guidance": "Provide structured facts."},
            memory_summary=context["memory_summary"],
            context_obj=context
        )
        assert coaching_detailed["coaching_strategy"]["tone"] == "Informative and structured"
        assert coaching_detailed["coaching_strategy"]["response_length"] == "Detailed"
    finally:
        db.close()


def test_stress_aware_coaching_tiers():
    """Verify 4-tier stress thresholds (LOW, MODERATE, HIGH, CRITICAL) assign proper empathy levels and escalation."""
    db = SessionLocal()
    try:
        context = build_full_customer_context(db, 1, "Testing stress tiers")

        # Tier: CRITICAL (81-100)
        coaching_crit = generate_coaching_recommendation(
            customer_message="This is completely unacceptable! I demand a manager immediately!",
            nlp_analysis={"intent": "Complaint", "sentiment": "Negative", "emotion": "Angry"},
            stress_info={"score": 90, "level": "CRITICAL"},
            style_info={"style": "Impatient / Direct", "guidance": "De-escalate immediately."},
            memory_summary=context["memory_summary"],
            context_obj=context
        )
        assert coaching_crit["coaching_strategy"]["empathy_level"] == "Very High"
        assert "CRITICAL STRESS ALERT" in coaching_crit["warning"]
        assert coaching_crit["escalation_required"] is True

        # Tier: LOW (0-30)
        coaching_low = generate_coaching_recommendation(
            customer_message="Hi, what are your opening hours?",
            nlp_analysis={"intent": "General Inquiry", "sentiment": "Positive", "emotion": "Calm"},
            stress_info={"score": 10, "level": "LOW"},
            style_info={"style": "Calm / Conversational", "guidance": "Warm assistance."},
            memory_summary=context["memory_summary"],
            context_obj={"repeated_issue": {"is_repeated_issue": False}, "customer": context["customer"]}
        )
        assert coaching_low["coaching_strategy"]["empathy_level"] == "Standard"
        assert coaching_low["escalation_required"] is False
    finally:
        db.close()


def test_coaching_strategy_and_rationale_generation():
    """Verify coaching_strategy dict and coaching_reason are present and correctly formatted."""
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

        assert "coaching_strategy" in coaching
        assert "tone" in coaching["coaching_strategy"]
        assert "response_length" in coaching["coaching_strategy"]
        assert "empathy_level" in coaching["coaching_strategy"]
        assert "avoid" in coaching["coaching_strategy"]
        assert "coaching_reason" in coaching
        assert len(coaching["coaching_reason"]) > 10
    finally:
        db.close()


def test_agent_response_feedback_capture():
    """Verify the /api/coaching/feedback endpoint records feedback actions."""
    feedback_payload = {
        "conversation_id": 1,
        "message_id": 1,
        "agent_action": "accepted",
        "suggested_response": "I completely understand how frustrating it is to deal with this order delay again.",
        "actual_response": "I completely understand how frustrating it is to deal with this order delay again."
    }
    response = client.post("/api/v1/coaching/feedback", json=feedback_payload)
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "success"
    assert data["action"] == "accepted"
