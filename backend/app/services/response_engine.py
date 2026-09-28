import re
import logging
from typing import Dict, Any, Optional, List
from sqlalchemy.orm import Session

from app.models.domain import Conversation, Message
from app.services.response_rules import match_response_rule
from app.services.llm_response_service import generate_llm_response
from app.services.translation_service import translate_text, translate_to_english
from app.core.languages import detect_text_language

logger = logging.getLogger("response_engine")

# Regex patterns for sensitive financial/refund actions (distinct from informational policy questions)
REFUND_ACTION_PATTERNS = [
    r"(?:need|want|give me|issue|request|processed?|expecting).*refund",
    r"refund (?:of )?(?:₹|rs\.?|inr|\$)?\s*\d+",
    r"(?:give|get) (?:my )?money back",
    r"(?:charged|billed) (?:incorrectly|twice|wrong)",
    r"cancel and refund",
    r"charged twice",
    r"double charge",
    r"unauthorized.*charges?",
    r"stolen card|dispute.*charge",
    r"transfer.*(?:to|into) (?:my )?bank",
    r"transfer (?:of )?(?:₹|rs\.?|inr|\$)?\s*\d+",
    r"send (?:of )?(?:₹|rs\.?|inr|\$)?\s*\d+.*(?:to|into) (?:my )?bank",
    r"रीफंड|रिफंड|धनवापसी|ரீஃபண்ட்|ரீபண்ட்|மறுಪಾವತಿ"
]

# Manager and supervisor escalation patterns
MANAGER_PATTERNS = [
    r"speak (?:to|with) (?:your |a )?manager",
    r"talk (?:to|with) (?:your |a )?manager",
    r"call (?:your |a )?manager",
    r"escalate to (?:a )?supervisor",
    r"speak (?:to|with) (?:a )?supervisor",
    r"speak (?:to|with).*(?:manager|supervisor)",
    r"demand to speak",
    r"supervisor or manager",
    r"transfer.*manager",
    r"want a supervisor",
    r"प्रबंधक|मैनेजर|पर्यवेक्षक|மேலாளர்|மேனேஜர்|மேற்பார்வையாளர்|ಮ್ಯಾನೇಜರ್|ವ್ಯವಸ್ಥಾಪಕ"
]

# Security and fraud patterns
SECURITY_PATTERNS = [
    r"hacked",
    r"unauthorized.*charge",
    r"compromised",
    r"stolen card|dispute.*charge",
    r"security breach",
    r"identity theft"
]

# Legal and compliance patterns
LEGAL_PATTERNS = [
    r"legal action",
    r"contact(?:ing)? my lawyer",
    r"my attorney",
    r"sue you",
    r"lawsuit",
    r"court of law",
    r"delete my account"
]

# Repeated issue text patterns
REPEATED_ISSUE_TEXT_PATTERNS = [
    r"contacted support (?:twice|three times|\d+ times|again)",
    r"nobody is helping me",
    r"no one is helping me",
    r"contacted (?:you|us|support) (?:3|three|\d+) times",
    r"waiting for (?:my |an )?order for a week",
    r"delayed again",
    r"still not received",
    r"still waiting"
]


def _format_currency(amount_str: str) -> str:
    """Helper to clean up amount string for professional acknowledgement."""
    clean = amount_str.replace(" ", "")
    # If contains numbers, format nicely
    digits = re.sub(r"[^\d]", "", clean)
    if digits:
        val = int(digits)
        if "₹" in amount_str or "rs" in amount_str.lower() or "inr" in amount_str.lower():
            return f"₹{val:,}"
        elif "$" in amount_str:
            return f"${val:,}"
        else:
            return f"₹{val:,}"
    return amount_str


def process_customer_message(
    db: Session,
    conversation: Conversation,
    customer_text: str,
    context_obj: Optional[Dict[str, Any]] = None,
    selected_language: Optional[str] = None
) -> Dict[str, Any]:
    """
    Hybrid Customer Response Engine.
    Coordinates:
    1. High-risk / sensitive / financial / escalation guardrails -> HUMAN_HANDOFF
    2. Deterministic business rules (delivery, orders, policies, etc.) -> RULE_RESPONSE
    3. Safe general questions via LLM -> LLM_RESPONSE
    4. LLM failure / missing key fallback -> HUMAN_HANDOFF
    5. Localizes response to customer's selected language (English, Hindi, Tamil, Kannada)

    Always returns structured dict:
    {
        "handling_mode": "RULE_RESPONSE" | "LLM_RESPONSE" | "HUMAN_HANDOFF",
        "response_text": str,
        "requires_human": bool,
        "auto_resolved": bool,
        "intent": str,
        "reason": str,
        "confidence": float
    }
    """
    # Determine customer's language
    target_lang = (
        selected_language
        or getattr(conversation, "language_code", None)
        or detect_text_language(customer_text)
        or "en"
    ).lower().split("-")[0].split("_")[0]
    if target_lang not in ["en", "hi", "ta", "kn"]:
        target_lang = "en"

    def _format_result(res: Dict[str, Any]) -> Dict[str, Any]:
        """Ensures the customer receives the response in their selected language."""
        if target_lang != "en" and res.get("response_text"):
            res["response_text"] = translate_text(res["response_text"], source_language="en", target_language=target_lang)
        return res

    text_clean = customer_text.strip()
    text_lower = text_clean.lower()
    text_en = text_clean
    text_en_lower = text_lower

    # If customer input is non-English, translate to English for internal pattern matching
    if target_lang != "en":
        text_en = translate_to_english(text_clean, source_language=target_lang)
        text_en_lower = text_en.lower()

    # Extract NLP, stress, style, and context data if available
    nlp_res = context_obj.get("current_analysis", {}) if context_obj else {}
    stress_info = context_obj.get("stress_info", {}) if context_obj else {}
    stress_score = stress_info.get("score", 0)
    repeated_info = context_obj.get("repeated_issue", {}) if context_obj else {}
    is_repeated_context = repeated_info.get("is_repeated_issue", False)

    # ------------------------------------------------------------------
    # 1. CRITICAL SENSITIVE & ESCALATION GUARDRAILS (Step 3 & Step 6)
    # ------------------------------------------------------------------

    # A. Check for Manager / Supervisor Escalation
    if any(re.search(pat, text_lower) or re.search(pat, text_en_lower) for pat in MANAGER_PATTERNS):
        return _format_result({
            "handling_mode": "HUMAN_HANDOFF",
            "response_text": (
                "I understand you would like to speak with a manager. "
                "I have escalated your request to a support supervisor who will review your case and follow up with you directly."
            ),
            "requires_human": True,
            "auto_resolved": False,
            "intent": "Escalation",
            "reason": "Customer requested supervisor/manager escalation",
            "confidence": 0.99
        })

    # B. Check for Refund / Financial Action Requests
    # Note: Informational "What is your refund policy?" is NOT an action request
    is_policy_query = bool(
        re.search(r"what is (?:the|your) refund policy|refund policy\b", text_lower)
        or re.search(r"what is (?:the|your) refund policy|refund policy\b", text_en_lower)
    )
    is_refund_action = (
        any(re.search(pat, text_lower) or re.search(pat, text_en_lower) for pat in REFUND_ACTION_PATTERNS)
    ) and not is_policy_query

    if is_refund_action:
        amount_match = re.search(r"(?:₹|rs\.?|inr|\$)?\s*([\d,]{2,10})", text_clean, re.IGNORECASE) or re.search(r"(?:₹|rs\.?|inr|\$)?\s*([\d,]{2,10})", text_en, re.IGNORECASE)
        clean_digits = re.sub(r"[^\d]", "", amount_match.group(1)) if amount_match else ""
        action_verb = "transfer" if ("transfer" in text_lower or "send" in text_lower or "transfer" in text_en_lower) else "refund"
        if amount_match and clean_digits and int(clean_digits) > 0:
            formatted_amt = _format_currency(amount_match.group(0))
            response_text = (
                f"I can help you with your {action_verb} request. Since this involves a {action_verb} of {formatted_amt}, "
                "I need to connect you with a support specialist who can verify the transaction and process the request. "
                "I've sent your request to the support team."
            )
        else:
            response_text = (
                f"I can help with your {action_verb} request. Because this requires transaction verification, "
                "I've connected your request with a support specialist who can review and process it."
            )

        return _format_result({
            "handling_mode": "HUMAN_HANDOFF",
            "response_text": response_text,
            "requires_human": True,
            "auto_resolved": False,
            "intent": "Billing & Payments",
            "reason": f"Sensitive financial/{action_verb} action requested",
            "confidence": 0.98
        })

    # C. Check for Security, Fraud & Unauthorized Account Activity
    if any(re.search(pat, text_lower) or re.search(pat, text_en_lower) for pat in SECURITY_PATTERNS):
        return _format_result({
            "handling_mode": "HUMAN_HANDOFF",
            "response_text": (
                "I have flagged your report of unauthorized or suspicious account activity "
                "and immediately connected your case with our security and fraud specialist team for urgent review."
            ),
            "requires_human": True,
            "auto_resolved": False,
            "intent": "Security & Fraud",
            "reason": "Security, fraud, or account compromise issue detected",
            "confidence": 0.99
        })

    # D. Check for Legal / Threat / Compliance Inquiries
    if any(re.search(pat, text_lower) or re.search(pat, text_en_lower) for pat in LEGAL_PATTERNS):
        return _format_result({
            "handling_mode": "HUMAN_HANDOFF",
            "response_text": (
                "I have flagged your inquiry for our specialist support management and compliance team. "
                "A specialist has been notified and will review your file promptly."
            ),
            "requires_human": True,
            "auto_resolved": False,
            "intent": "Legal / Compliance",
            "reason": "Legal or compliance topic detected",
            "confidence": 0.99
        })

    # E. Explicit Repeated Issue Complaints in Current Text
    is_explicit_repeated_text = any(
        re.search(pat, text_lower) or re.search(pat, text_en_lower)
        for pat in REPEATED_ISSUE_TEXT_PATTERNS
    )
    if is_explicit_repeated_text:
        return _format_result({
            "handling_mode": "HUMAN_HANDOFF",
            "response_text": (
                "I see that you've contacted support multiple times regarding this issue. "
                "I have connected your request directly with a senior support specialist so this can be resolved for you as a priority."
            ),
            "requires_human": True,
            "auto_resolved": False,
            "intent": "Repeated Issue",
            "reason": "Customer indicated repeated unresolved issue in message; routed to senior specialist",
            "confidence": 0.95
        })

    # ------------------------------------------------------------------
    # 2. DETERMINISTIC RULE-BASED MATCHING (Step 1 & Step 2)
    # ------------------------------------------------------------------
    rule_match = match_response_rule(text_clean, context_obj, db)
    if not rule_match and target_lang != "en":
        # Try matching against English-translated message while preserving order numbers
        order_match = re.search(r"#?(\d{4,8})", text_clean)
        query_to_match = text_en
        if order_match and f"#{order_match.group(1)}" not in text_en:
            query_to_match = f"{text_en} #{order_match.group(1)}"
        rule_match = match_response_rule(query_to_match, context_obj, db)

    if rule_match:
        rule, rule_response_text = rule_match
        return _format_result({
            "handling_mode": "RULE_RESPONSE",
            "response_text": rule_response_text,
            "requires_human": False,
            "auto_resolved": True,
            "intent": rule.intent,
            "reason": f"Deterministic business rule matched: {rule.intent}",
            "confidence": 0.98
        })

    # ------------------------------------------------------------------
    # 3. EXISTING NLP, STRESS & REPEATED ISSUE GUARDRAILS (Step 6)
    # (Evaluated before calling LLM for open-ended queries)
    # ------------------------------------------------------------------
    if is_repeated_context:
        return _format_result({
            "handling_mode": "HUMAN_HANDOFF",
            "response_text": (
                "I see from your customer history that you have previously contacted support regarding this matter. "
                "I have connected your case with a support specialist to ensure this is resolved for you promptly."
            ),
            "requires_human": True,
            "auto_resolved": False,
            "intent": "Repeated Issue",
            "reason": "Repeated unresolved customer issue in context; human touch required",
            "confidence": 0.95
        })

    if stress_score >= 60:
        return _format_result({
            "handling_mode": "HUMAN_HANDOFF",
            "response_text": (
                "I sincerely apologize for the frustration this has caused. "
                "I've connected your case to a support specialist who can assist you directly and resolve this as quickly as possible."
            ),
            "requires_human": True,
            "auto_resolved": False,
            "intent": nlp_res.get("intent", "Customer Support"),
            "reason": f"High customer stress ({stress_score}/100) detected; empathy & human intervention required",
            "confidence": 0.95
        })

    # ------------------------------------------------------------------
    # 4. LLM API FALLBACK FOR GENERAL SAFE QUESTIONS (Step 4 & Step 5)
    # ------------------------------------------------------------------
    # Retrieve recent messages in conversation for context
    history_items: List[Dict[str, str]] = []
    if conversation and conversation.messages:
        for m in conversation.messages[-6:]:
            history_items.append({
                "sender_type": m.sender_type,
                "content": m.content
            })

    logger.info(f"[RESPONSE ENGINE] No deterministic rule matched for message '{text_clean[:50]}...'. Routing to LLM service.")

    llm_input_text = text_clean if target_lang == "en" else text_en
    llm_result = generate_llm_response(
        customer_message=llm_input_text,
        context_obj=context_obj,
        conversation_history=history_items
    )

    if llm_result and llm_result.get("success") and not llm_result.get("is_fallback"):
        logger.info("[RESPONSE ENGINE] LLM generation succeeded. Returning mode: LLM_RESPONSE.")
        return _format_result({
            "handling_mode": "LLM_RESPONSE",
            "response_text": llm_result["response_text"],
            "requires_human": False,
            "auto_resolved": True,
            "intent": nlp_res.get("intent", "General Inquiry"),
            "reason": "Answered by AI assistant via LLM",
            "confidence": 0.90
        })

    # If LLM is not configured, times out, or returns an error -> safe fallback
    fallback_text = (
        llm_result.get("response_text")
        if llm_result and llm_result.get("response_text")
        else "I'm sorry, I couldn't complete that request automatically. I've sent your request to a support specialist so you can still get help."
    )
    error_msg = llm_result.get("error") if llm_result else "LLM unavailable"
    logger.warning(f"[RESPONSE ENGINE] LLM generation unavailable or failed ({error_msg}). Routing to HUMAN_HANDOFF with safe fallback acknowledgement.")
    return _format_result({
        "handling_mode": "HUMAN_HANDOFF",
        "response_text": fallback_text,
        "requires_human": True,
        "auto_resolved": False,
        "intent": nlp_res.get("intent", "General Inquiry"),
        "reason": f"LLM unavailable ({error_msg}); safe fallback provided and routed to specialist",
        "confidence": 0.70
    })
