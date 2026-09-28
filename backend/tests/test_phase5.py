import pytest
from fastapi.testclient import TestClient
from app.main import app
from app.core.database import SessionLocal
from app.services.learning_service import (
    get_coaching_effectiveness_metrics,
    get_customer_experience_metrics,
    get_learning_insights,
    get_continuous_improvement_recommendations
)

client = TestClient(app)


def test_customer_feedback_creation():
    """Verify customer CSAT feedback and conversation outcome creation."""
    payload = {
        "conversation_id": 1,
        "csat_rating": 5,
        "comments": "Great service! Agent explained order delivery clearly.",
        "outcome": "Resolved"
    }
    response = client.post("/api/v1/coaching/csat", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "success"
    assert data["rating"] == 5
    assert data["outcome"] == "Resolved"


def test_agent_coaching_feedback_logging():
    """Verify agent coaching feedback (accepted, edited, ignored, custom) logging."""
    payload = {
        "conversation_id": 1,
        "message_id": 1,
        "agent_action": "edited",
        "suggested_response": "Checking status...",
        "actual_response": "I have escalated your delayed order #ORD-98213 to logistics."
    }
    response = client.post("/api/v1/coaching/feedback", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "success"
    assert data["action"] == "edited"


def test_coaching_effectiveness_metrics_calculation():
    """Verify calculation of acceptance rate, edit rate, rejection rate from database records."""
    db = SessionLocal()
    try:
        metrics = get_coaching_effectiveness_metrics(db)
        assert "total_suggestions" in metrics
        assert metrics["total_suggestions"] > 0
        assert "acceptance_rate" in metrics
        assert "edit_rate" in metrics
        assert "rejection_rate" in metrics
        assert metrics["acceptance_rate"] + metrics["edit_rate"] + metrics["rejection_rate"] + metrics["custom_rate"] > 0
    finally:
        db.close()


def test_customer_experience_metrics_calculation():
    """Verify CSAT rating average, resolution rate, and escalation rate calculations."""
    db = SessionLocal()
    try:
        metrics = get_customer_experience_metrics(db)
        assert metrics["avg_csat_rating"] >= 1.0
        assert metrics["avg_csat_rating"] <= 5.0
        assert metrics["resolution_rate"] >= 0.0
        assert metrics["escalation_rate"] >= 0.0
    finally:
        db.close()


def test_learning_service_insights_generation():
    """Verify structured learning insights generation from aggregated feedback."""
    db = SessionLocal()
    try:
        insights = get_learning_insights(db)
        assert isinstance(insights, list)
        assert len(insights) >= 3
        first = insights[0]
        assert "id" in first
        assert "title" in first
        assert "pattern" in first
        assert "insight" in first
        assert "recommendation" in first
        assert "confidence_score" in first
    finally:
        db.close()


def test_continuous_improvement_summary_report():
    """Verify continuous improvement summary containing pattern categories."""
    db = SessionLocal()
    try:
        report = get_continuous_improvement_recommendations(db)
        assert "coaching_effectiveness" in report
        assert "customer_experience" in report
        assert "learning_insights" in report
        assert "top_accepted_patterns" in report
        assert "most_edited_patterns" in report
        assert len(report["top_accepted_patterns"]) > 0
    finally:
        db.close()


def test_analytics_api_endpoints():
    """Verify all Phase 5 analytics endpoints return HTTP 200 with JSON structures."""
    endpoints = [
        "/api/v1/analytics/metrics",
        "/api/v1/analytics/coaching",
        "/api/v1/analytics/customer",
        "/api/v1/analytics/learning",
        "/api/v1/analytics/insights"
    ]
    for ep in endpoints:
        resp = client.get(ep)
        assert resp.status_code == 200, f"Endpoint {ep} failed with status {resp.status_code}"
        assert resp.headers["content-type"].startswith("application/json")
