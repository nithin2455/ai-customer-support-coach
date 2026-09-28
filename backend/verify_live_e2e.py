"""
Live End-to-End Verification Script for Phase 9
Tests all 14 verification criteria directly against the live running FastAPI backend:
http://127.0.0.1:8000
"""

import sys
import uuid
import httpx

BASE_URL = "http://127.0.0.1:8000/api/v1"

def log_test(title, passed, details=""):
    status = "[PASS]" if passed else "[FAIL]"
    print(f"{status} | {title}")
    if details:
        print(f"       Details: {details}")

def run_live_verification():
    print("=" * 70)
    print("STARTING LIVE END-TO-END VERIFICATION OF PHASE 9")
    print(f"Target Base URL: {BASE_URL}")
    print("=" * 70)

    unique_suffix = uuid.uuid4().hex[:6]
    test_email = f"live.cust.{unique_suffix}@example.com"
    test_password = "SecurePassword123!"
    test_name = f"Live Customer {unique_suffix}"

    with httpx.Client(timeout=30.0) as client:
        # 1. Customer registration
        reg_payload = {
            "name": test_name,
            "email": test_email,
            "password": test_password,
            "phone": "+1 555 019 9283"
        }
        r = client.post(f"{BASE_URL}/auth/register", json=reg_payload)
        passed_1 = r.status_code == 201 and "access_token" in r.json()
        customer_token = r.json().get("access_token") if passed_1 else None
        customer_user = r.json().get("user", {}) if passed_1 else {}
        log_test("1. Customer registration", passed_1, f"Status: {r.status_code}, User: {customer_user.get('email')}")

        # 2. Customer login
        login_payload = {
            "email": test_email,
            "password": test_password
        }
        r = client.post(f"{BASE_URL}/auth/login", json=login_payload)
        passed_2 = r.status_code == 200 and "access_token" in r.json()
        if passed_2:
            customer_token = r.json()["access_token"]
        log_test("2. Customer login", passed_2, f"Status: {r.status_code}, Token: {customer_token[:15]}...")

        # 3. Customer portal (/me and /chat/customer/me/conversations)
        headers_cust = {"Authorization": f"Bearer {customer_token}"}
        r_me = client.get(f"{BASE_URL}/auth/me", headers=headers_cust)
        passed_3a = r_me.status_code == 200 and r_me.json().get("email") == test_email
        
        # Create conversation for this customer
        r_conv = client.post(f"{BASE_URL}/chat/customer/me/conversations", headers=headers_cust)
        passed_3b = r_conv.status_code == 200 and "id" in r_conv.json()
        conv_id = r_conv.json().get("id") if passed_3b else None

        # Fetch customer's own conversations list
        r_list = client.get(f"{BASE_URL}/chat/customer/me/conversations", headers=headers_cust)
        passed_3c = r_list.status_code == 200 and any(c["id"] == conv_id for c in r_list.json())
        passed_3 = passed_3a and passed_3b and passed_3c
        log_test("3. Customer portal", passed_3, f"Me: {r_me.status_code}, Conv created: {conv_id}, List count: {len(r_list.json())}")

        # 4. Sending a rule-based question
        r_rule = client.post(f"{BASE_URL}/chat/message", headers=headers_cust, json={
            "conversation_id": conv_id,
            "content": "What are your delivery times and shipping options?"
        })
        resp_4 = r_rule.json()
        rule_text = resp_4.get("response_text") or (resp_4.get("response_message") or {}).get("content", "")
        passed_4 = r_rule.status_code == 200 and resp_4.get("handling_mode") == "RULE_RESPONSE" and "delivery" in rule_text.lower()
        log_test("4. Sending a rule-based question", passed_4, f"Mode: {resp_4.get('handling_mode')}, Response: {rule_text[:60]}...")

        # 5. Sending a real LLM question
        r_llm = client.post(f"{BASE_URL}/chat/message", headers=headers_cust, json={
            "conversation_id": conv_id,
            "content": "Why does my payment keep failing during international checkout?"
        })
        resp_5 = r_llm.json()
        llm_text = resp_5.get("response_text") or (resp_5.get("response_message") or {}).get("content", "")
        passed_5 = r_llm.status_code == 200 and bool(llm_text) and resp_5.get("handling_mode") in ["LLM_RESPONSE", "HUMAN_HANDOFF"]
        log_test("5. Sending a real LLM question", passed_5, f"Mode: {resp_5.get('handling_mode')}, Content: {llm_text[:60]}...")

        # 6. Refund human handoff
        r_refund = client.post(f"{BASE_URL}/chat/message", headers=headers_cust, json={
            "conversation_id": conv_id,
            "content": "I demand a refund of 15000 immediately for my damaged order!"
        })
        refund_data = r_refund.json()
        refund_text = refund_data.get("response_text") or (refund_data.get("response_message") or {}).get("content", "")
        passed_6 = (
            r_refund.status_code == 200 and 
            refund_data.get("handling_mode") == "HUMAN_HANDOFF" and
            refund_data.get("requires_human") == True and
            "refund" in refund_text.lower()
        )
        log_test("6. Refund human handoff", passed_6, f"Requires Human: {refund_data.get('requires_human')}, Handoff Ack: {refund_text[:60]}...")

        # 7. Agent receiving the handoff
        # Login as Agent (Sarah Jenkins)
        r_agent_login = client.post(f"{BASE_URL}/auth/login", json={
            "email": "sarah.j@support.com",
            "password": "Agent123!"
        })
        passed_7a = r_agent_login.status_code == 200 and "access_token" in r_agent_login.json()
        agent_token = r_agent_login.json().get("access_token")
        headers_agent = {"Authorization": f"Bearer {agent_token}"}

        # Fetch agent conversation list / queue
        r_queue = client.get(f"{BASE_URL}/chat/conversations", headers=headers_agent)
        passed_7b = r_queue.status_code == 200 and any(c["id"] == conv_id for c in r_queue.json())
        passed_7 = passed_7a and passed_7b
        log_test("7. Agent receiving the handoff", passed_7, f"Agent logged in, found conv {conv_id} in queue of {len(r_queue.json())} items")

        # 8. Agent responding
        agent_msg_content = "Hello! I am Sarah from Tier 2 Support. I have reviewed your damaged item report and initiated your refund request."
        r_agent_reply = client.post(f"{BASE_URL}/chat/agent-reply", headers=headers_agent, json={
            "conversation_id": conv_id,
            "content": agent_msg_content
        })
        passed_8 = r_agent_reply.status_code == 200 and r_agent_reply.json().get("sender_type") == "agent"
        log_test("8. Agent responding", passed_8, f"Status: {r_agent_reply.status_code}, Sender: {r_agent_reply.json().get('sender_type')}")

        # 9. Customer receiving the agent response
        r_cust_view = client.get(f"{BASE_URL}/chat/conversation/{conv_id}", headers=headers_cust)
        cust_conv = r_cust_view.json()
        messages = cust_conv.get("messages", [])
        has_agent_msg = any(m.get("sender_type") == "agent" and agent_msg_content in m.get("content", "") for m in messages)
        passed_9 = r_cust_view.status_code == 200 and has_agent_msg
        log_test("9. Customer receiving the agent response", passed_9, f"Total messages: {len(messages)}, Agent reply found: {has_agent_msg}")

        # 10. Customer cannot access another customer's data
        # Create Customer B
        email_b = f"other.cust.{unique_suffix}@example.com"
        r_reg_b = client.post(f"{BASE_URL}/auth/register", json={
            "name": "Other Customer",
            "email": email_b,
            "password": "SecurePassword123!"
        })
        token_b = r_reg_b.json().get("access_token")
        headers_cust_b = {"Authorization": f"Bearer {token_b}"}

        # Customer B attempts to access Customer A's conversation
        r_attack = client.get(f"{BASE_URL}/chat/conversation/{conv_id}", headers=headers_cust_b)
        # Customer B attempts to send message in Customer A's conversation
        r_attack_post = client.post(f"{BASE_URL}/chat/message", headers=headers_cust_b, json={
            "conversation_id": conv_id,
            "content": "Malicious intrusion attempt"
        })
        passed_10 = r_attack.status_code == 403 and r_attack_post.status_code == 403
        log_test("10. Customer cannot access another customer's data", passed_10, f"GET Conv Status: {r_attack.status_code} (Expected 403), POST Msg Status: {r_attack_post.status_code} (Expected 403)")

        # 11. Customer cannot access Agent/Admin APIs
        r_cust_agent_reply = client.post(f"{BASE_URL}/chat/agent-reply", headers=headers_cust, json={
            "conversation_id": conv_id,
            "content": "Impersonating agent"
        })
        r_cust_admin = client.get(f"{BASE_URL}/admin/departments", headers=headers_cust)
        passed_11 = r_cust_agent_reply.status_code == 403 and r_cust_admin.status_code == 403
        log_test("11. Customer cannot access Agent/Admin APIs", passed_11, f"Agent-reply: {r_cust_agent_reply.status_code}, Admin-dept: {r_cust_admin.status_code}")

        # 12. Agent cannot access Admin-only APIs
        r_agent_admin = client.get(f"{BASE_URL}/admin/departments", headers=headers_agent)
        passed_12 = r_agent_admin.status_code == 403
        log_test("12. Agent cannot access Admin-only APIs", passed_12, f"Admin endpoint status: {r_agent_admin.status_code} (Expected 403)")

        # 13. Admin can access Admin APIs
        r_admin_login = client.post(f"{BASE_URL}/auth/login", json={
            "email": "admin@company.com",
            "password": "Admin123!"
        })
        admin_token = r_admin_login.json().get("access_token")
        headers_admin = {"Authorization": f"Bearer {admin_token}"}
        r_admin_depts = client.get(f"{BASE_URL}/admin/departments", headers=headers_admin)
        r_admin_agents = client.get(f"{BASE_URL}/admin/agents", headers=headers_admin)
        passed_13 = r_admin_depts.status_code == 200 and r_admin_agents.status_code == 200
        log_test("13. Admin can access Admin APIs", passed_13, f"Depts: {r_admin_depts.status_code} ({len(r_admin_depts.json())} depts), Agents: {r_admin_agents.status_code} ({len(r_admin_agents.json())} agents)")

        # 14. Correct local timestamps (ISO-8601 with Z)
        created_at = messages[0].get("created_at") if messages else ""
        is_iso_z = bool(created_at and created_at.endswith("Z"))
        passed_14 = is_iso_z
        log_test("14. Correct local timestamps", passed_14, f"Timestamp sample: '{created_at}', timezone-aware UTC 'Z' suffix: {is_iso_z}")

    print("=" * 70)
    all_passed = all([
        passed_1, passed_2, passed_3, passed_4, passed_5, passed_6, passed_7,
        passed_8, passed_9, passed_10, passed_11, passed_12, passed_13, passed_14
    ])
    if all_passed:
        print("[SUCCESS] ALL 14 LIVE END-TO-END VERIFICATION CHECKS PASSED SUCCESSFULLY!")
    else:
        print("[FAILURE] ONE OR MORE VERIFICATION CHECKS FAILED.")
    print("=" * 70)
    return 0 if all_passed else 1

if __name__ == "__main__":
    sys.exit(run_live_verification())
