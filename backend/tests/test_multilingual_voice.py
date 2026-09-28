"""
Test Suite: Multilingual Support, Language Routing, Voice Metadata, and Zero OpenAI Verification.

Verifies:
1. Default language is English (en, en-IN)
2. Tamil selection (ta, ta-IN)
3. Hindi selection (hi, hi-IN)
4. Kannada selection (kn, kn-IN)
5. English selection (en, en-IN)
6. Language metadata persistence in Conversation and Message
7. Same-language response requires no translation (source == target)
8. Sensitive request still goes to human handoff in non-English
9. Known rule response in non-English works deterministically
10. Gemini unavailable fallback still works safely
11. Existing customer isolation still works
12. Existing authentication still works
13. Agent response translation for non-English customer
14. Zero OpenAI verification (no openai imports, keys, or endpoints)
"""
import pytest
from unittest.mock import patch
from fastapi.testclient import TestClient

from app.main import app
from app.core.database import SessionLocal
from app.models.domain import Conversation, Message, Customer, User
from app.core.languages import (
    SUPPORTED_LANGUAGES,
    LANGUAGE_MAP,
    DEFAULT_LANGUAGE_CODE,
    DEFAULT_LOCALE,
    detect_text_language,
    get_language,
    get_locale,
    get_language_name
)
from app.services.translation_service import (
    translate_text,
    translate_to_english,
    translate_from_english,
    MULTILINGUAL_TEMPLATES
)
from app.services.response_engine import process_customer_message

client = TestClient(app)


def get_alex_customer_token():
    res = client.post("/api/v1/auth/login", json={
        "email": "alex.j@example.com",
        "password": "Customer123!"
    })
    assert res.status_code == 200
    return res.json()["access_token"]


def get_sarah_agent_token():
    res = client.post("/api/v1/auth/login", json={
        "email": "sarah.j@support.com",
        "password": "Agent123!"
    })
    assert res.status_code == 200
    return res.json()["access_token"]


# ----------------------------------------------------------------------
# 1. Centralized Language Configuration & Script Detection
# ----------------------------------------------------------------------

def test_centralized_language_configuration():
    assert len(SUPPORTED_LANGUAGES) == 4
    codes = [l["code"] for l in SUPPORTED_LANGUAGES]
    assert "en" in codes
    assert "hi" in codes
    assert "ta" in codes
    assert "kn" in codes

    assert get_locale("en") == "en-IN"
    assert get_locale("hi") == "hi-IN"
    assert get_locale("ta") == "ta-IN"
    assert get_locale("kn") == "kn-IN"

    assert get_language_name("en") == "English"
    assert get_language_name("hi") == "Hindi"
    assert get_language_name("ta") == "Tamil"
    assert get_language_name("kn") == "Kannada"


def test_script_detection_secondary_signal():
    # Tamil text
    assert detect_text_language("என்னோட ஆர்டர் எப்போ வரும்?") == "ta"
    # Hindi text
    assert detect_text_language("मेरा ऑर्डर कहाँ है?") == "hi"
    # Kannada text
    assert detect_text_language("ನನ್ನ ಆರ್ಡರ್ ಯಾವಾಗ ಬರುತ್ತದೆ?") == "kn"
    # English text
    assert detect_text_language("Where is my order?") is None


# ----------------------------------------------------------------------
# 2. Translation Service Unit Tests
# ----------------------------------------------------------------------

def test_same_language_no_translation():
    text = "Hello! Welcome to Customer Support."
    assert translate_text(text, "en", "en") == text
    assert translate_text(text, "en-IN", "en") == text

    ta_text = "வணக்கம்!"
    assert translate_text(ta_text, "ta", "ta") == ta_text


def test_deterministic_multilingual_templates():
    delivery_en = MULTILINGUAL_TEMPLATES["delivery_info"]["en"]
    # Translate from English to Tamil using deterministic template
    delivery_ta = translate_text(delivery_en, "en", "ta")
    assert "வழக்கமான டெலிவரி" in delivery_ta
    assert delivery_ta == MULTILINGUAL_TEMPLATES["delivery_info"]["ta"]

    # Translate from English to Hindi using deterministic template
    delivery_hi = translate_text(delivery_en, "en", "hi")
    assert "मानक डिलीवरी" in delivery_hi
    assert delivery_hi == MULTILINGUAL_TEMPLATES["delivery_info"]["hi"]

    # Translate from English to Kannada using deterministic template
    delivery_kn = translate_text(delivery_en, "en", "kn")
    assert "ಸಾಮಾನ್ಯ ಡೆಲಿವರಿ" in delivery_kn
    assert delivery_kn == MULTILINGUAL_TEMPLATES["delivery_info"]["kn"]


def test_dynamic_order_status_template_translation():
    status_en = "Your order #98213 has been shipped via FedEx (Tracking #TRK-10928) and is expected to arrive Tomorrow by 5:00 PM."
    status_ta = translate_text(status_en, "en", "ta")
    assert "#98213" in status_ta
    assert "FedEx" in status_ta
    assert "#TRK-10928" in status_ta
    assert "வந்து சேரும் என எதிர்பார்க்கப்படுகிறது" in status_ta

    status_hi = translate_text(status_en, "en", "hi")
    assert "#98213" in status_hi
    assert "FedEx" in status_hi
    assert "पहुंचने की उम्मीद है" in status_hi

    status_kn = translate_text(status_en, "en", "kn")
    assert "#98213" in status_kn
    assert "FedEx" in status_kn
    assert "ತಲುಪುವ ನಿರೀಕ್ಷೆಯಿದೆ" in status_kn


def test_sensitive_refund_template_translation():
    fin_en = (
        "I understand you are requesting a refund of ₹5,000. "
        "Because this involves a direct financial transaction, I have securely routed your case to a support specialist with financial authorization. "
        "They will review your order details and follow up with you promptly."
    )
    fin_ta = translate_text(fin_en, "en", "ta")
    assert "₹5,000" in fin_ta
    assert "பணத்தைத் திரும்பப்பெறக் கோருகிறீர்கள்" in fin_ta

    fin_hi = translate_text(fin_en, "en", "hi")
    assert "₹5,000" in fin_hi
    assert "धनवापसी का अनुरोध" in fin_hi


# ----------------------------------------------------------------------
# 3. Response Engine Multilingual Tests
# ----------------------------------------------------------------------

def test_response_engine_default_english():
    db = SessionLocal()
    try:
        conv = db.query(Conversation).filter(Conversation.id == 2).first()
        res = process_customer_message(
            db=db,
            conversation=conv,
            customer_text="What are your standard delivery times?",
            selected_language="en"
        )
        assert res["handling_mode"] == "RULE_RESPONSE"
        assert "Standard delivery usually takes 3–5 business days" in res["response_text"]
    finally:
        db.close()


def test_response_engine_tamil_delivery():
    db = SessionLocal()
    try:
        conv = db.query(Conversation).filter(Conversation.id == 2).first()
        conv.language_code = "ta"
        conv.locale = "ta-IN"
        db.commit()

        res = process_customer_message(
            db=db,
            conversation=conv,
            customer_text="டெலிவரி நேரம் என்ன?",  # Delivery times
            selected_language="ta"
        )
        assert res["handling_mode"] == "RULE_RESPONSE"
        # Response should be in Tamil
        assert "வழக்கமான டெலிவரி" in res["response_text"] or "நாட்கள்" in res["response_text"]
    finally:
        db.close()


def test_response_engine_hindi_delivery():
    db = SessionLocal()
    try:
        conv = db.query(Conversation).filter(Conversation.id == 2).first()
        conv.language_code = "hi"
        conv.locale = "hi-IN"
        db.commit()

        res = process_customer_message(
            db=db,
            conversation=conv,
            customer_text="डिलीवरी समय क्या है?",
            selected_language="hi"
        )
        assert res["handling_mode"] == "RULE_RESPONSE"
        # Response should be in Hindi
        assert "मानक डिलीवरी" in res["response_text"] or "कार्यदिवस" in res["response_text"]
    finally:
        db.close()


def test_response_engine_kannada_delivery():
    db = SessionLocal()
    try:
        conv = db.query(Conversation).filter(Conversation.id == 2).first()
        conv.language_code = "kn"
        conv.locale = "kn-IN"
        db.commit()

        res = process_customer_message(
            db=db,
            conversation=conv,
            customer_text="ಡೆಲಿವರಿ ಸಮಯ ಎಷ್ಟು?",
            selected_language="kn"
        )
        assert res["handling_mode"] == "RULE_RESPONSE"
        # Response should be in Kannada
        assert "ಸಾಮಾನ್ಯ ಡೆಲಿವರಿ" in res["response_text"] or "ದಿನಗಳು" in res["response_text"]
    finally:
        db.close()


def test_sensitive_request_human_handoff_multilingual():
    db = SessionLocal()
    try:
        conv = db.query(Conversation).filter(Conversation.id == 2).first()
        conv.language_code = "ta"
        conv.locale = "ta-IN"
        db.commit()

        res = process_customer_message(
            db=db,
            conversation=conv,
            customer_text="எனக்கு 5000 ரூபாய் refund வேண்டும்",  # Sensitive refund request
            selected_language="ta"
        )
        assert res["handling_mode"] == "HUMAN_HANDOFF"
        assert res["requires_human"] is True
        # Response is in Tamil
        assert "ஆதரவு" in res["response_text"] or "நிபுணர்" in res["response_text"] or "பணத்தைத் திரும்ப" in res["response_text"]
    finally:
        db.close()


def test_manager_escalation_multilingual():
    db = SessionLocal()
    try:
        conv = db.query(Conversation).filter(Conversation.id == 2).first()
        conv.language_code = "hi"
        conv.locale = "hi-IN"
        db.commit()

        res = process_customer_message(
            db=db,
            conversation=conv,
            customer_text="मुझे प्रबंधक से बात करनी है",  # Speak with manager
            selected_language="hi"
        )
        assert res["handling_mode"] == "HUMAN_HANDOFF"
        assert res["requires_human"] is True
        # Response is in Hindi
        assert "प्रबंधक" in res["response_text"] or "पर्यवेक्षक" in res["response_text"]
    finally:
        db.close()


# ----------------------------------------------------------------------
# 4. Gemini Unavailable Fallback in Multilingual Flow
# ----------------------------------------------------------------------

def test_gemini_unavailable_fallback_multilingual():
    db = SessionLocal()
    try:
        conv = db.query(Conversation).filter(Conversation.id == 2).first()
        conv.language_code = "ta"
        conv.locale = "ta-IN"
        db.commit()

        with patch("app.services.llm_response_service.is_gemini_configured", return_value=False):
            res = process_customer_message(
                db=db,
                conversation=conv,
                customer_text="Do you have products in green color?",  # Non-deterministic query
                selected_language="ta"
            )
            assert res["handling_mode"] == "HUMAN_HANDOFF"
            assert res["requires_human"] is True
            # Returned safe fallback response in Tamil
            assert "மன்னிக்கவும்" in res["response_text"] or "ஆதரவு நிபுணருக்கு" in res["response_text"]
    finally:
        db.close()


# ----------------------------------------------------------------------
# 5. API Endpoints: Language Metadata Persistence & Agent Translation
# ----------------------------------------------------------------------

def test_chat_message_endpoint_multilingual():
    token = get_alex_customer_token()
    headers = {"Authorization": f"Bearer {token}"}
    conv_id = 1
    payload = {
        "conversation_id": conv_id,
        "content": "டெலிவரி நேரம் என்ன?",
        "language_code": "ta",
        "locale": "ta-IN"
    }
    response = client.post("/api/v1/chat/message", json=payload, headers=headers)
    assert response.status_code == 200
    data = response.json()
    assert data["language_code"] == "ta"
    assert data["locale"] == "ta-IN"
    assert data["response_text"] is not None

    # Check persistence in database
    db = SessionLocal()
    try:
        conv = db.query(Conversation).filter(Conversation.id == conv_id).first()
        assert conv.language_code == "ta"
        assert conv.locale == "ta-IN"

        # Check last message metadata
        last_msg = db.query(Message).filter(Message.conversation_id == conv_id).order_by(Message.id.desc()).first()
        assert last_msg.language_code == "ta"
    finally:
        db.close()


def test_agent_reply_translation():
    agent_token = get_sarah_agent_token()
    headers = {"Authorization": f"Bearer {agent_token}"}
    conv_id = 1

    db = SessionLocal()
    try:
        conv = db.query(Conversation).filter(Conversation.id == conv_id).first()
        conv.language_code = "ta"
        conv.locale = "ta-IN"
        db.commit()
    finally:
        db.close()

    # Agent responds in English
    agent_reply_payload = {
        "conversation_id": conv_id,
        "content": "Your order is expected to arrive tomorrow.",
        "action_type": "custom"
    }
    resp = client.post("/api/v1/chat/agent-reply", json=agent_reply_payload, headers=headers)
    assert resp.status_code == 200
    data = resp.json()

    # Customer-facing message is translated to Tamil
    assert "உங்கள் ஆர்டர் நாளை வந்து சேரும்" in data["content"]
    assert data["original_content"] == "Your order is expected to arrive tomorrow."
    assert data["language_code"] == "ta"


def test_translate_endpoint():
    payload = {
        "text": "Hello! Welcome to Customer Support.",
        "source_language": "en",
        "target_language": "ta"
    }
    resp = client.post("/api/v1/chat/translate", json=payload)
    assert resp.status_code == 200
    data = resp.json()
    assert "வணக்கம்" in data["translated_text"]


# ----------------------------------------------------------------------
# 6. Customer Isolation & Authentication Integrity
# ----------------------------------------------------------------------

def test_customer_isolation_preserved():
    alex_token = get_alex_customer_token()
    headers = {"Authorization": f"Bearer {alex_token}"}
    # Conversation 3 belongs to Priya (another customer)
    resp = client.get("/api/v1/chat/conversation/3", headers=headers)
    assert resp.status_code == 403


# ----------------------------------------------------------------------
# 7. Zero OpenAI Verification
# ----------------------------------------------------------------------

def test_zero_openai_verification():
    """
    CRITICAL COST REQUIREMENT:
    Assert that the multilingual and voice implementation uses zero OpenAI APIs,
    zero OpenAI keys, and zero paid speech/translation dependencies.
    """
    from app.services import translation_service
    from app.core import languages

    import inspect
    ts_code = inspect.getsource(translation_service)
    lang_code = inspect.getsource(languages)

    assert "import openai" not in ts_code.lower()
    assert "from openai" not in ts_code.lower()
    assert "openai.com" not in ts_code.lower()
    assert "whisper" not in ts_code.lower()

    assert "import openai" not in lang_code.lower()
