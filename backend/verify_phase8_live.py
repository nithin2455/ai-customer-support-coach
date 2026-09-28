import sys
import time
import json
import httpx

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")
if hasattr(sys.stderr, "reconfigure"):
    sys.stderr.reconfigure(encoding="utf-8")
from app.db.seed import seed_database
from app.core.config import settings
from app.services.llm_response_service import is_gemini_configured, get_gemini_model

BASE_URL = "http://127.0.0.1:8000/api/v1"


def run_live_verification():
    print("=" * 75)
    print("PHASE 8 — GEMINI LLM PROVIDER & RESPONSE ENGINE LIVE VERIFICATION")
    print("=" * 75)

    with httpx.Client(base_url=BASE_URL, timeout=30.0, follow_redirects=True) as client:
        # 1. Server Health
        try:
            health = client.get("/health").json()
            print(f"[+] Backend Server Online: {health}")
        except Exception as e:
            print(f"[-] Could not connect to FastAPI server at {BASE_URL}: {e}")
            sys.exit(1)

        gemini_ready = is_gemini_configured()
        selected_model = get_gemini_model()
        print(f"[*] GEMINI_API_KEY configured: {gemini_ready}")
        print(f"[*] GEMINI_MODEL selected:     {selected_model}")

        # ------------------------------------------------------------------
        # CASE A: "Hi" -> AI greeting (RULE_RESPONSE)
        # ------------------------------------------------------------------
        print("\n" + "-" * 65)
        print("CASE A: Greeting")
        print("Customer Question: 'Hi'")
        print("-" * 65)
        payload_a = {
            "conversation_id": 2,
            "content": "Hi",
            "sender_type": "customer"
        }
        res_a = client.post("/chat/message", json=payload_a).json()
        print(f"Handling Mode:   {res_a.get('handling_mode')}")
        print(f"Requires Human:  {res_a.get('requires_human')}")
        print(f"Auto Resolved:   {res_a.get('auto_resolved')}")
        print(f"Response Text:   {res_a.get('response_text')}")
        assert res_a.get("handling_mode") == "RULE_RESPONSE", "CASE A handling mode failed!"
        assert res_a.get("auto_resolved") is True, "CASE A auto_resolved failed!"
        assert "welcome" in res_a.get("response_text", "").lower(), "CASE A greeting failed!"
        print("[PASS] CASE A PASSED: Deterministic rule-based greeting returned.")

        # ------------------------------------------------------------------
        # CASE B: "How long does standard delivery take?" -> Rule-based answer
        # ------------------------------------------------------------------
        print("\n" + "-" * 65)
        print("CASE B: Rule-Based Delivery Question")
        print("Customer Question: 'How long does standard delivery take?'")
        print("-" * 65)
        payload_b = {
            "conversation_id": 2,
            "content": "How long does standard delivery take?",
            "sender_type": "customer"
        }
        res_b = client.post("/chat/message", json=payload_b).json()
        print(f"Handling Mode:   {res_b.get('handling_mode')}")
        print(f"Requires Human:  {res_b.get('requires_human')}")
        print(f"Auto Resolved:   {res_b.get('auto_resolved')}")
        print(f"Response Text:   {res_b.get('response_text')}")
        assert res_b.get("handling_mode") == "RULE_RESPONSE", "CASE B handling mode failed!"
        assert res_b.get("auto_resolved") is True, "CASE B auto_resolved failed!"
        assert "business days" in res_b.get("response_text", "").lower(), "CASE B missing delivery info!"
        print("[PASS] CASE B PASSED: Deterministic rule answered standard delivery question.")

        # ------------------------------------------------------------------
        # CASE C: "Where is my order #98213?" -> Verified DB Lookup
        # ------------------------------------------------------------------
        print("\n" + "-" * 65)
        print("CASE C: Verified Database Order Lookup")
        print("Customer Question: 'Where is my order #98213?'")
        print("-" * 65)
        payload_c = {
            "conversation_id": 2,
            "content": "Where is my order #98213?",
            "sender_type": "customer"
        }
        res_c = client.post("/chat/message", json=payload_c).json()
        print(f"Handling Mode:   {res_c.get('handling_mode')}")
        print(f"Requires Human:  {res_c.get('requires_human')}")
        print(f"Auto Resolved:   {res_c.get('auto_resolved')}")
        print(f"Response Text:   {res_c.get('response_text')}")
        assert res_c.get("handling_mode") == "RULE_RESPONSE", "CASE C handling mode failed!"
        assert "98213" in res_c.get("response_text", ""), "Order number missing in response!"
        assert "FedEx" in res_c.get("response_text", ""), "Carrier FedEx missing from DB record!"
        print("[PASS] CASE C PASSED: Real Order retrieved from database without hallucination.")

        # ------------------------------------------------------------------
        # CASE D: "Why do online payments sometimes fail even when I have enough money in my account?"
        # -> REAL Gemini LLM response
        # ------------------------------------------------------------------
        print("\n" + "-" * 65)
        print("CASE D: General Question via Real Gemini LLM")
        print("Customer Question: 'Why do online payments sometimes fail even when I have enough money in my account?'")
        print("-" * 65)
        payload_d = {
            "conversation_id": 2,
            "content": "Why do online payments sometimes fail even when I have enough money in my account?",
            "sender_type": "customer"
        }
        res_d = client.post("/chat/message", json=payload_d).json()
        print(f"Handling Mode:   {res_d.get('handling_mode')}")
        print(f"Requires Human:  {res_d.get('requires_human')}")
        print(f"Auto Resolved:   {res_d.get('auto_resolved')}")
        print(f"Response Text:\n{res_d.get('response_text')}")
        if gemini_ready:
            assert res_d.get("handling_mode") == "LLM_RESPONSE", f"Expected LLM_RESPONSE, got {res_d.get('handling_mode')}"
            assert res_d.get("requires_human") is False
            assert "support specialist" not in res_d.get("response_text", "").lower(), "Received fallback instead of Gemini response!"
            print("[PASS] CASE D PASSED: Live Google Gemini response successfully generated.")
        else:
            assert res_d.get("handling_mode") == "HUMAN_HANDOFF"
            print("[PASS] CASE D PASSED: Safe fallback returned gracefully (Gemini unconfigured).")

        # ------------------------------------------------------------------
        # CASE E: "What is the difference between a debit card and a credit card?"
        # -> REAL Gemini LLM response
        # ------------------------------------------------------------------
        print("\n" + "-" * 65)
        print("CASE E: Financial Concept Question via Real Gemini LLM")
        print("Customer Question: 'What is the difference between a debit card and a credit card?'")
        print("-" * 65)
        payload_e = {
            "conversation_id": 2,
            "content": "What is the difference between a debit card and a credit card?",
            "sender_type": "customer"
        }
        res_e = client.post("/chat/message", json=payload_e).json()
        print(f"Handling Mode:   {res_e.get('handling_mode')}")
        print(f"Requires Human:  {res_e.get('requires_human')}")
        print(f"Auto Resolved:   {res_e.get('auto_resolved')}")
        print(f"Response Text:\n{res_e.get('response_text')}")
        if gemini_ready:
            assert res_e.get("handling_mode") == "LLM_RESPONSE", f"Expected LLM_RESPONSE, got {res_e.get('handling_mode')}"
            assert res_e.get("requires_human") is False
            assert "support specialist" not in res_e.get("response_text", "").lower(), "Received fallback instead of Gemini response!"
            print("[PASS] CASE E PASSED: Live Google Gemini response successfully generated.")
        else:
            assert res_e.get("handling_mode") == "HUMAN_HANDOFF"
            print("[PASS] CASE E PASSED: Safe fallback returned gracefully (Gemini unconfigured).")

        # ------------------------------------------------------------------
        # CASE F: "I need a refund of ₹15,000." -> Immediate safe acknowledgement + Human handoff
        # ------------------------------------------------------------------
        print("\n" + "-" * 65)
        print("CASE F: Financial Safety & Human Handoff (Refund Request)")
        print("Customer Question: 'I need a refund of ₹15,000.'")
        print("-" * 65)
        payload_f = {
            "conversation_id": 1,
            "content": "I need a refund of ₹15,000.",
            "sender_type": "customer"
        }
        res_f = client.post("/chat/message", json=payload_f).json()
        print(f"Handling Mode:   {res_f.get('handling_mode')}")
        print(f"Requires Human:  {res_f.get('requires_human')}")
        print(f"Auto Resolved:   {res_f.get('auto_resolved')}")
        print(f"Response Text:   {res_f.get('response_text')}")
        assert res_f.get("handling_mode") == "HUMAN_HANDOFF", "CASE F handling mode failed!"
        assert res_f.get("requires_human") is True, "CASE F requires_human failed!"
        assert res_f.get("auto_resolved") is False, "CASE F auto_resolved must be false!"
        assert "refund" in res_f.get("response_text", "").lower(), "CASE F missing refund acknowledgement!"
        assert "₹15,000" in res_f.get("response_text", ""), "CASE F missing amount in acknowledgement!"
        print("[PASS] CASE F PASSED: Immediate safe acknowledgement returned & routed to human handoff.")

        # ------------------------------------------------------------------
        # CASE G: "This is unacceptable. I want to speak to your manager." -> Escalation/human workflow
        # ------------------------------------------------------------------
        print("\n" + "-" * 65)
        print("CASE G: Manager Escalation Request")
        print("Customer Question: 'This is unacceptable. I want to speak to your manager.'")
        print("-" * 65)
        payload_g = {
            "conversation_id": 1,
            "content": "This is unacceptable. I want to speak to your manager.",
            "sender_type": "customer"
        }
        res_g = client.post("/chat/message", json=payload_g).json()
        print(f"Handling Mode:   {res_g.get('handling_mode')}")
        print(f"Requires Human:  {res_g.get('requires_human')}")
        print(f"Auto Resolved:   {res_g.get('auto_resolved')}")
        print(f"Response Text:   {res_g.get('response_text')}")
        assert res_g.get("handling_mode") == "HUMAN_HANDOFF", "CASE G handling mode failed!"
        assert res_g.get("requires_human") is True, "CASE G requires_human failed!"
        assert "manager" in res_g.get("response_text", "").lower() or "supervisor" in res_g.get("response_text", "").lower()
        print("[PASS] CASE G PASSED: Manager escalation handoff handled safely.")

    print("\n" + "=" * 75)
    print("ALL 7 LIVE CASES (A THROUGH G) VERIFIED SUCCESSFULLY!")
    print("=" * 75)


if __name__ == "__main__":
    run_live_verification()
