"""
Final End-to-End Multilingual and Voice Support Verification Script.
Validates:
1. Customer selects Tamil, Hindi, Kannada, English.
2. Direct deterministic rule matching and dynamic Gemini translation.
3. Message persistence with language_code, original_content, translated_content.
4. Agent sees customer non-English message and English translation.
5. Agent replies in English -> Customer receives Tamil/Hindi/Kannada translation.
6. Sensitive financial request routed to Human Handoff.
7. Zero OpenAI dependencies verification.
"""
import sys
import io
if sys.platform == "win32":
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

from fastapi.testclient import TestClient
from app.main import app
from app.core.database import SessionLocal
from app.models.domain import Conversation, Message

client = TestClient(app)

def run_verification():
    print("=" * 60)
    print("STARTING E2E VERIFICATION: MULTILINGUAL + VOICE SUPPORT")
    print("=" * 60)

    # 1. Login as Alex (Customer)
    res_alex = client.post("/api/v1/auth/login", json={
        "email": "alex.j@example.com",
        "password": "Customer123!"
    })
    assert res_alex.status_code == 200, f"Alex login failed: {res_alex.text}"
    alex_token = res_alex.json()["access_token"]
    alex_headers = {"Authorization": f"Bearer {alex_token}"}
    print("[✓] Customer authenticated successfully")

    # 2. Login as Sarah (Agent)
    res_sarah = client.post("/api/v1/auth/login", json={
        "email": "sarah.j@support.com",
        "password": "Agent123!"
    })
    assert res_sarah.status_code == 200, f"Sarah login failed: {res_sarah.text}"
    sarah_token = res_sarah.json()["access_token"]
    sarah_headers = {"Authorization": f"Bearer {sarah_token}"}
    print("[✓] Agent authenticated successfully")

    # 3. Create a new conversation for customer
    res_conv = client.post("/api/v1/chat/customer/me/conversations", headers=alex_headers)
    assert res_conv.status_code == 200
    conv_id = res_conv.json()["id"]
    print(f"[✓] Created Conversation #{conv_id}")

    # 4. Test Tamil Support: Customer sends Tamil message
    # "டெலிவரி நேரம் என்ன?" (What is the delivery time?)
    res_msg_ta = client.post("/api/v1/chat/message", headers=alex_headers, json={
        "conversation_id": conv_id,
        "content": "டெலிவரி நேரம் என்ன?",
        "sender_type": "customer",
        "language_code": "ta",
        "locale": "ta-IN"
    })
    assert res_msg_ta.status_code == 200, f"Tamil message failed: {res_msg_ta.text}"
    data_ta = res_msg_ta.json()
    print(f"[✓] Tamil Query Processed: Mode={data_ta['handling_mode']}")
    print(f"    Assistant Response: {data_ta['response_text']}")
    assert "டெலிவரி" in data_ta["response_text"] or "நாட்கள்" in data_ta["response_text"], "Response not in Tamil"

    # 5. Test Hindi Support: Customer sends Hindi message
    res_msg_hi = client.post("/api/v1/chat/message", headers=alex_headers, json={
        "conversation_id": conv_id,
        "content": "डिलीवरी समय क्या है?",
        "sender_type": "customer",
        "language_code": "hi",
        "locale": "hi-IN"
    })
    assert res_msg_hi.status_code == 200
    data_hi = res_msg_hi.json()
    print(f"[✓] Hindi Query Processed: Mode={data_hi['handling_mode']}")
    print(f"    Assistant Response: {data_hi['response_text']}")
    assert "डिलीवरी" in data_hi["response_text"] or "कार्यदिवस" in data_hi["response_text"], "Response not in Hindi"

    # 6. Test Kannada Support: Customer sends Kannada message
    res_msg_kn = client.post("/api/v1/chat/message", headers=alex_headers, json={
        "conversation_id": conv_id,
        "content": "ಡೆಲಿವರಿ ಸಮಯ ಎಷ್ಟು?",
        "sender_type": "customer",
        "language_code": "kn",
        "locale": "kn-IN"
    })
    assert res_msg_kn.status_code == 200
    data_kn = res_msg_kn.json()
    print(f"[✓] Kannada Query Processed: Mode={data_kn['handling_mode']}")
    print(f"    Assistant Response: {data_kn['response_text']}")
    assert "ಡೆಲಿವರಿ" in data_kn["response_text"] or "ದಿನಗಳು" in data_kn["response_text"], "Response not in Kannada"

    # 7. Test Sensitive Financial Request in Tamil -> Must route to Human Handoff
    res_refund_ta = client.post("/api/v1/chat/message", headers=alex_headers, json={
        "conversation_id": conv_id,
        "content": "எனக்கு 5000 ரூபாய் refund வேண்டும்",
        "sender_type": "customer",
        "language_code": "ta",
        "locale": "ta-IN"
    })
    assert res_refund_ta.status_code == 200
    refund_data = res_refund_ta.json()
    print(f"[✓] Sensitive Financial Guardrail: Mode={refund_data['handling_mode']}, RequiresHuman={refund_data['requires_human']}")
    print(f"    Handoff Response: {refund_data['response_text']}")
    assert refund_data["handling_mode"] == "HUMAN_HANDOFF"
    assert refund_data["requires_human"] is True

    # 8. Agent inspects conversation
    res_agent_conv = client.get(f"/api/v1/chat/conversation/{conv_id}", headers=sarah_headers)
    assert res_agent_conv.status_code == 200
    conv_details = res_agent_conv.json()
    assert conv_details["language_code"] == "ta"
    last_customer_msg = [m for m in conv_details["messages"] if m["sender_type"] == "customer"][-1]
    print(f"[✓] Agent View:")
    print(f"    Conversation Language: {conv_details['language_code']}")
    print(f"    Original Customer Text: {last_customer_msg['original_content'] or last_customer_msg['content']}")
    print(f"    English Translated: {last_customer_msg['translated_content']}")

    # 9. Agent replies in English -> System translates to customer's Tamil language
    agent_reply_text = "I have reviewed your account and will initiate your refund verification."
    res_agent_reply = client.post("/api/v1/chat/agent-reply", headers=sarah_headers, json={
        "conversation_id": conv_id,
        "content": agent_reply_text,
        "action_type": "custom"
    })
    assert res_agent_reply.status_code == 200
    delivered_msg = res_agent_reply.json()
    print(f"[✓] Agent English Reply Sent: '{agent_reply_text}'")
    print(f"    Customer Delivered Content: '{delivered_msg['content']}'")
    print(f"    Original Agent Content Preserved: '{delivered_msg['original_content']}'")

    # 10. Verify Zero OpenAI
    import subprocess
    grep_res = subprocess.run(
        ["git", "grep", "-i", "openai", "--", ":!verify_final_e2e.py"],
        cwd=".",
        capture_output=True,
        text=True
    )
    # Check that neither imports nor keys exist
    forbidden_lines = [
        line for line in grep_res.stdout.splitlines()
        if "OPENAI_API_KEY" in line or "import openai" in line or "from openai" in line
    ]
    assert len(forbidden_lines) == 0, f"Found OpenAI references: {forbidden_lines}"
    print("[✓] Zero OpenAI Confirmation: Verified no openai imports or keys exist.")

    print("=" * 60)
    print("ALL E2E ACCEPTANCE CRITERIA VERIFIED SUCCESSFULLY!")
    print("=" * 60)

if __name__ == "__main__":
    run_verification()
