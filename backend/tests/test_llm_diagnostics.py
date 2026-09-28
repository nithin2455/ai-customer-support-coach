"""
Comprehensive Tests for Gemini LLM Response Service, Safety, and Response Engine Flow
Verifies:
1. Gemini API key missing -> safe fallback handoff
2. Gemini API key configured -> is_gemini_configured() is True
3. Gemini successful response with mocked google-genai call -> LLM_RESPONSE
4. Gemini API failure (e.g. APIError) -> safe fallback handoff with diagnostic error
5. Gemini timeout / connection failure -> safe fallback
6. API key is never exposed (sanitization check)
7. General question uses Gemini
8. Rule-based delivery question does NOT use Gemini
9. Order lookup does NOT use Gemini
10. Refund request does NOT use Gemini
11. Manager escalation does NOT use Gemini
12. Gemini failure produces safe fallback/handoff
13. Customer message always gets a response
(Zero real API calls made in automated tests)
"""

import pytest
from unittest.mock import patch, MagicMock
from fastapi.testclient import TestClient

from app.main import app
from app.core.database import SessionLocal
from app.models.domain import Conversation, Message
from app.services.llm_response_service import (
    generate_llm_response,
    is_gemini_configured,
    get_gemini_api_key,
    get_gemini_model,
    FALLBACK_RESPONSE,
    _sanitize_error_msg
)
from app.services.response_engine import process_customer_message

client = TestClient(app)


# ------------------------------------------------------------------------------
# 1. API key is never exposed (Sanitization)
# ------------------------------------------------------------------------------
def test_sanitize_error_msg_masks_keys():
    """Verify that any raw Gemini or OpenAI API keys inside exception strings are masked."""
    test_gemini = "AIza" + "SyD1234567890abcdefghijklmnopqrstuvwx"
    raw_gemini = f"Invalid key {test_gemini} provided to API"
    sanitized = _sanitize_error_msg(raw_gemini)
    assert test_gemini not in sanitized
    assert "[REDACTED_GEMINI_KEY]" in sanitized

    test_openai = "sk-" + "proj-1234567890abcdefghijklmnop"
    raw_openai = f"Error with {test_openai} during initialization"
    sanitized_openai = _sanitize_error_msg(raw_openai)
    assert test_openai not in sanitized_openai
    assert "[REDACTED_API_KEY]" in sanitized_openai


# ------------------------------------------------------------------------------
# 2. Gemini API key missing
# ------------------------------------------------------------------------------
def test_gemini_api_key_missing():
    """When GEMINI_API_KEY is not configured or empty, returns safe fallback."""
    with patch("app.services.llm_response_service.get_gemini_api_key", return_value=""):
        assert is_gemini_configured() is False
        res = generate_llm_response("Why do online payments sometimes fail?")
        assert res["success"] is False
        assert res["is_fallback"] is True
        assert res["response_text"] == FALLBACK_RESPONSE
        assert "GEMINI_API_KEY is not configured" in res["error"]


# ------------------------------------------------------------------------------
# 3. Gemini API key configured
# ------------------------------------------------------------------------------
def test_gemini_api_key_configured():
    """When a non-default key is set, is_gemini_configured returns True."""
    with patch("app.services.llm_response_service.get_gemini_api_key", return_value="mock-gemini-test-key-12345"):
        assert is_gemini_configured() is True


# ------------------------------------------------------------------------------
# 4. Gemini successful response (mocked)
# ------------------------------------------------------------------------------
def test_successful_gemini_response_mocked():
    """When Gemini API call succeeds, returns the generated AI reply with success=True."""
    mock_ai_reply = "Online payments sometimes fail due to temporary network timeouts or 3D-Secure bank verification steps."

    mock_response = MagicMock()
    mock_response.text = mock_ai_reply

    with patch("app.services.llm_response_service.get_gemini_api_key", return_value="mock-gemini-test-key-12345"):
        with patch("google.genai.Client") as mock_client_cls:
            mock_client_instance = MagicMock()
            mock_client_instance.models.generate_content.return_value = mock_response
            mock_client_cls.return_value = mock_client_instance

            res = generate_llm_response("Why do online payments sometimes fail even when I have enough money?")
            assert res["success"] is True
            assert res["is_fallback"] is False
            assert res["error"] is None
            assert res["response_text"] == mock_ai_reply


# ------------------------------------------------------------------------------
# 5. Gemini API failure & timeout
# ------------------------------------------------------------------------------
def test_gemini_api_failure():
    """When Gemini API throws an exception (e.g. 503 or quota error), returns safe fallback."""
    with patch("app.services.llm_response_service.get_gemini_api_key", return_value="mock-gemini-test-key-12345"):
        with patch("google.genai.Client") as mock_client_cls:
            mock_client_instance = MagicMock()
            mock_client_instance.models.generate_content.side_effect = RuntimeError("503 Service Unavailable")
            mock_client_cls.return_value = mock_client_instance

            res = generate_llm_response("What is the difference between a debit card and a credit card?")
            assert res["success"] is False
            assert res["is_fallback"] is True
            assert res["response_text"] == FALLBACK_RESPONSE
            assert "RuntimeError" in res["error"]


def test_gemini_timeout_failure():
    """When Gemini API times out, returns safe fallback gracefully without unhandled exception."""
    with patch("app.services.llm_response_service.get_gemini_api_key", return_value="mock-gemini-test-key-12345"):
        with patch("google.genai.Client") as mock_client_cls:
            mock_client_instance = MagicMock()
            mock_client_instance.models.generate_content.side_effect = TimeoutError("Request timed out after 15 seconds")
            mock_client_cls.return_value = mock_client_instance

            res = generate_llm_response("Can you explain how refund timelines work?")
            assert res["success"] is False
            assert res["is_fallback"] is True
            assert res["response_text"] == FALLBACK_RESPONSE
            assert "TimeoutError" in res["error"]


# ------------------------------------------------------------------------------
# 6. General safe question uses Gemini (End-to-End through Response Engine)
# ------------------------------------------------------------------------------
def test_general_question_uses_gemini():
    """End-to-end API test verifying unmatched general questions route to Gemini."""
    mock_ai_reply = "A debit card deducts money directly from your bank balance, while a credit card borrows money up to a credit limit."

    mock_response = MagicMock()
    mock_response.text = mock_ai_reply

    with patch("app.services.llm_response_service.get_gemini_api_key", return_value="AIzaSyMockKey12345"):
        with patch("google.genai.Client") as mock_client_cls:
            mock_client_instance = MagicMock()
            mock_client_instance.models.generate_content.return_value = mock_response
            mock_client_cls.return_value = mock_client_instance

            payload = {
                "conversation_id": 1,
                "content": "What is the difference between a debit card and a credit card?",
                "sender_type": "customer"
            }
            res = client.post("/api/v1/chat/message", json=payload)
            assert res.status_code == 200
            data = res.json()
            assert data["handling_mode"] == "LLM_RESPONSE"
            assert data["requires_human"] is False
            assert mock_ai_reply in data["response_text"]


# ------------------------------------------------------------------------------
# 7. Rule-based delivery question does NOT use Gemini
# ------------------------------------------------------------------------------
def test_rule_based_delivery_question_does_not_use_gemini():
    """Verify deterministic rule matching bypasses Gemini completely."""
    with patch("app.services.llm_response_service.generate_llm_response") as mock_gemini:
        db = SessionLocal()
        try:
            conv = db.query(Conversation).first()
            result = process_customer_message(
                db=db,
                conversation=conv,
                customer_text="What are your delivery times and shipping options?"
            )
            # Gemini must NOT be called
            mock_gemini.assert_not_called()
            assert result["handling_mode"] == "RULE_RESPONSE"
            assert result["requires_human"] is False
            assert "business days" in result["response_text"].lower()
        finally:
            db.close()


# ------------------------------------------------------------------------------
# 8. Order lookup does NOT use Gemini
# ------------------------------------------------------------------------------
def test_order_lookup_does_not_use_gemini():
    """Verify database order lookups bypass Gemini completely."""
    with patch("app.services.llm_response_service.generate_llm_response") as mock_gemini:
        db = SessionLocal()
        try:
            conv = db.query(Conversation).first()
            result = process_customer_message(
                db=db,
                conversation=conv,
                customer_text="Where is my order #98213?"
            )
            # Gemini must NOT be called
            mock_gemini.assert_not_called()
            assert result["handling_mode"] == "RULE_RESPONSE"
            assert "98213" in result["response_text"]
            assert "fedex" in result["response_text"].lower()
        finally:
            db.close()


# ------------------------------------------------------------------------------
# 9. Refund request does NOT use Gemini
# ------------------------------------------------------------------------------
def test_refund_request_does_not_use_gemini():
    """Verify sensitive financial refund requests bypass Gemini and route directly to human handoff."""
    with patch("app.services.llm_response_service.generate_llm_response") as mock_gemini:
        db = SessionLocal()
        try:
            conv = db.query(Conversation).first()
            result = process_customer_message(
                db=db,
                conversation=conv,
                customer_text="I need a refund of ₹15,000 for my order right now!"
            )
            # Gemini must NOT be called
            mock_gemini.assert_not_called()
            assert result["handling_mode"] == "HUMAN_HANDOFF"
            assert result["requires_human"] is True
            assert "refund" in result["response_text"].lower()
            assert "₹15,000" in result["response_text"]
        finally:
            db.close()


# ------------------------------------------------------------------------------
# 10. Manager escalation does NOT use Gemini
# ------------------------------------------------------------------------------
def test_manager_escalation_does_not_use_gemini():
    """Verify escalation/supervisor requests bypass Gemini and route directly to human handoff."""
    with patch("app.services.llm_response_service.generate_llm_response") as mock_gemini:
        db = SessionLocal()
        try:
            conv = db.query(Conversation).first()
            result = process_customer_message(
                db=db,
                conversation=conv,
                customer_text="This is unacceptable. I want to speak to your manager."
            )
            # Gemini must NOT be called
            mock_gemini.assert_not_called()
            assert result["handling_mode"] == "HUMAN_HANDOFF"
            assert result["requires_human"] is True
            assert "manager" in result["response_text"].lower() or "supervisor" in result["response_text"].lower()
        finally:
            db.close()


# ------------------------------------------------------------------------------
# 11. Gemini failure produces safe fallback / handoff
# ------------------------------------------------------------------------------
def test_gemini_failure_produces_safe_fallback():
    """Verify when Gemini fails, response engine provides safe fallback acknowledgement."""
    with patch("app.services.llm_response_service.get_gemini_api_key", return_value=""):
        payload = {
            "conversation_id": 1,
            "content": "Can you explain your international warranty terms?",
            "sender_type": "customer"
        }
        res = client.post("/api/v1/chat/message", json=payload)
        assert res.status_code == 200
        data = res.json()
        assert data["handling_mode"] == "HUMAN_HANDOFF"
        assert data["requires_human"] is True
        assert FALLBACK_RESPONSE in data["response_text"]


# ------------------------------------------------------------------------------
# 12. Customer message always gets a response
# ------------------------------------------------------------------------------
def test_customer_message_always_gets_a_response():
    """Verify that every customer message produces a non-empty, meaningful response."""
    payload = {
        "conversation_id": 1,
        "content": "A completely random and unexpected question about astronomy.",
        "sender_type": "customer"
    }
    res = client.post("/api/v1/chat/message", json=payload)
    assert res.status_code == 200
    data = res.json()
    assert bool(data.get("response_text"))
    assert data["handling_mode"] in ["RULE_RESPONSE", "LLM_RESPONSE", "HUMAN_HANDOFF"]
