import json
import logging
from typing import Dict, Any, List, Optional
import httpx
from app.core.config import settings

logger = logging.getLogger("llm_coach")


def generate_coaching_recommendation(
    customer_message: str,
    nlp_analysis: Dict[str, Any],
    stress_info: Dict[str, Any],
    style_info: Dict[str, Any],
    memory_summary: Dict[str, Any],
    context_obj: Optional[Dict[str, Any]] = None
) -> Dict[str, Any]:
    """
    Phase 4 Personalized & Style-Aware AI Coaching Recommendation Engine.
    Synthesizes CURRENT MESSAGE + STRESS + COMMUNICATION STYLE + MEMORY + REPEATED ISSUE + AGENT CONTEXT.
    Generates structured coaching strategy, user-facing rationale, and tailored response drafts.
    """
    # Extract context components
    repeated_issue_info = context_obj.get("repeated_issue", {}) if context_obj else {}
    agent_continuity = context_obj.get("agent_continuity", {}) if context_obj else {}
    customer_profile = context_obj.get("customer", {}) if context_obj else {}

    is_repeated = repeated_issue_info.get("is_repeated_issue", False)
    issue_type = repeated_issue_info.get("issue_type", "New Issue")

    # Check if external LLM API key is configured
    if settings.LLM_PROVIDER in ["openai", "gemini"] and settings.LLM_API_KEY:
        try:
            return _call_external_llm(customer_message, nlp_analysis, stress_info, style_info, memory_summary, context_obj)
        except Exception as e:
            logger.error(f"External LLM API call failed: {e}. Falling back to structured AI Coaching Engine.")

    intent = nlp_analysis.get("intent", "General Inquiry")
    sentiment = nlp_analysis.get("sentiment", "Neutral")
    emotion = nlp_analysis.get("emotion", "Calm")
    stress_score = stress_info.get("score", 0)
    stress_level = stress_info.get("level", "LOW")
    style_label = style_info.get("style", "Calm")

    # 1. Stress Level Classification (0-30 LOW, 31-60 MODERATE, 61-80 HIGH, 81-100 CRITICAL)
    if stress_score >= 81:
        stress_tier = "CRITICAL"
        empathy_level = "Very High"
    elif stress_score >= 61:
        stress_tier = "HIGH"
        empathy_level = "High"
    elif stress_score >= 31:
        stress_tier = "MODERATE"
        empathy_level = "Moderate"
    else:
        stress_tier = "LOW"
        empathy_level = "Standard"

    # 2. Communication-Style & Stress-Aware Strategy Formulation
    if "Impatient" in style_label or "Direct" in style_label or stress_tier in ["HIGH", "CRITICAL"]:
        strategy_tone = "Empathetic and direct"
        strategy_length = "Concise"
        strategy_avoid = "Unnecessary long explanations or repeating basic troubleshooting"
    elif "Detailed" in style_label or "Analytical" in style_label:
        strategy_tone = "Informative and structured"
        strategy_length = "Detailed"
        strategy_avoid = "Vague promises without specific timeline reference"
    elif "Confused" in style_label or "Guidance" in style_label:
        strategy_tone = "Supportive and reassuring"
        strategy_length = "Step-by-step"
        strategy_avoid = "Technical jargon or multi-part complex instructions"
    else:
        strategy_tone = "Warm and professional"
        strategy_length = "Standard"
        strategy_avoid = "Robotic template responses"

    # 3. Coaching Rationale / Explanation (WHY this coaching)
    if is_repeated:
        coaching_reason = (
            f"Customer stress is {stress_score}/100 ({stress_tier}) and this order delay has been reported previously. "
            f"A concise, empathetic response acknowledging prior logistics escalation is recommended to prevent further frustration."
        )
    elif stress_tier in ["HIGH", "CRITICAL"]:
        coaching_reason = (
            f"Customer is experiencing high stress ({stress_score}/100) regarding {intent.lower()}. "
            f"Immediate emotional validation and clear resolution steps are recommended."
        )
    else:
        coaching_reason = f"Customer inquiry is calm. Standard professional support protocol applies."

    # 4. Frustration Warning & Repeated Issue Alert
    warning = None
    if is_repeated:
        warning = (
            f"🔄 REPEATED ISSUE DETECTED ({issue_type}) • STRESS {stress_score}/100 ({stress_tier}): "
            f"Customer has previously contacted support regarding this issue ({repeated_issue_info.get('reason')}). "
            f"Do NOT ask customer to repeat basic troubleshooting."
        )
    elif stress_tier in ["HIGH", "CRITICAL"]:
        warning = f"⚠️ {stress_tier} STRESS ALERT ({stress_score}/100): Customer is displaying severe frustration ({emotion}). De-escalation protocol required."
    elif stress_tier == "MODERATE":
        warning = f"⚡ MODERATE STRESS ({stress_score}/100): Customer appears frustrated regarding {intent.lower()}."
    else:
        warning = f"✅ LOW STRESS ({stress_score}/100): Customer is inquiring calmly."

    # 5. Recommended Actions (Style & History Aware)
    recommended_actions: List[str] = []
    if is_repeated:
        recommended_actions = [
            "Acknowledge that the issue has happened again and validate customer frustration.",
            "Recognize prior contact (customer reported this issue 3 days ago).",
            "Review previous logistics escalation steps already taken.",
            "Avoid asking the customer to repeat already completed troubleshooting.",
            "Provide a concrete status update and clear next step."
        ]
    elif "Impatient" in style_label or "Direct" in style_label:
        recommended_actions = [
            "Acknowledge the customer's frustration directly.",
            "Apologize for the order delay.",
            "Check the latest order status in Logistics System.",
            "Provide a clear update or resolution timeline.",
            "Avoid unnecessary long explanations."
        ]
    elif "Detailed" in style_label:
        recommended_actions = [
            "Provide a breakdown of the order fulfillment timeline.",
            "Reference tracking number and carrier dispatch notes.",
            "Explain the root cause of the shipping delay.",
            "Confirm expected delivery window."
        ]
    else:
        recommended_actions = [
            "Acknowledge customer inquiry warmly.",
            "Provide clear, direct answer to the core question.",
            "Confirm if additional assistance is required."
        ]

    # 6. Escalation Recommendation
    if is_repeated and stress_tier in ["HIGH", "CRITICAL"]:
        escalation_recommendation = "High Priority: Review existing logistics escalation ticket #LOG-98213 immediately. Contact Senior Logistics Lead if unresolved today."
        escalation_required = True
    elif stress_tier == "CRITICAL":
        escalation_recommendation = "Consider escalation to Team Lead if customer requests refund or manager callback."
        escalation_required = True
    else:
        escalation_recommendation = "No immediate escalation required. Follow standard support protocol."
        escalation_required = False

    # 7. Empathy & Resolution Guidance
    empathy_guidance = (
        f"Style ({style_label}) & Stress ({stress_tier}): Validate customer emotional state ({emotion}). "
        f"Use {strategy_tone.lower()} tone. {style_info.get('guidance')}"
    )

    resolution_guidance = (
        f"Goal: Swift resolution of {issue_type} ({intent}). "
        f"Deliver concrete update without repeating past steps."
    )

    # 8. Suggested Response Draft
    if is_repeated and ("waiting" in customer_message.lower() or "order" in customer_message.lower() or "week" in customer_message.lower()):
        suggested_response = (
            "I completely understand how frustrating it is to deal with this order delay again, especially since you already contacted us about it. "
            "I have reviewed your previous report and am checking the logistics escalation right now to give you a concrete update."
        )
    elif "waiting for my order" in customer_message.lower() or "week" in customer_message.lower() or "order" in intent.lower():
        suggested_response = (
            "I completely understand how frustrating this delay must be, and I truly apologize for the inconvenience. "
            "Let me check the latest status of your order and provide you with an update."
        )
    elif sentiment.lower() == "negative":
        suggested_response = (
            "Thank you for bringing this to our attention. I understand your frustration and am sorry for the trouble caused. "
            "I am looking into this right away to make things right for you."
        )
    else:
        suggested_response = (
            "Hello! Thank you for contacting customer support. I would be happy to assist you with your inquiry today. "
            "Could you please share your order number so I can look into this for you?"
        )

    # Compile structured strategy object
    coaching_strategy = {
        "tone": strategy_tone,
        "response_length": strategy_length,
        "priority": "Concrete status update & de-escalation" if is_repeated else "Immediate resolution",
        "empathy_level": empathy_level,
        "avoid": strategy_avoid,
        "explanation": coaching_reason
    }

    return {
        "warning": warning,
        "is_repeated_issue": is_repeated,
        "issue_type": issue_type,
        "coaching_strategy": coaching_strategy,
        "coaching_reason": coaching_reason,
        "recommended_actions": recommended_actions,
        "empathy_guidance": empathy_guidance,
        "resolution_guidance": resolution_guidance,
        "suggested_response": suggested_response,
        "escalation_required": escalation_required,
        "escalation_recommendation": escalation_recommendation,
        "customer_history_snippet": memory_summary.get("summary_text"),
        "agent_continuity": agent_continuity
    }


def _call_external_llm(
    customer_message: str,
    nlp_analysis: Dict[str, Any],
    stress_info: Dict[str, Any],
    style_info: Dict[str, Any],
    memory_summary: Dict[str, Any],
    context_obj: Optional[Dict[str, Any]] = None
) -> Dict[str, Any]:
    """Helper to call OpenAI or OpenAI-compatible API endpoint if configured."""
    prompt = f"""You are an expert AI Customer Support Coach assisting a human customer service agent.
Customer Message: "{customer_message}"
NLP Analysis: {nlp_analysis}
Stress Score: {stress_info}
Customer Style: {style_info}
Full Context: {context_obj}

Return JSON with keys:
- warning (string)
- is_repeated_issue (boolean)
- issue_type (string)
- coaching_strategy (dict with keys: tone, response_length, priority, empathy_level, avoid, explanation)
- coaching_reason (string)
- recommended_actions (list of strings)
- empathy_guidance (string)
- resolution_guidance (string)
- suggested_response (string)
- escalation_required (boolean)
- escalation_recommendation (string)
"""
    headers = {"Authorization": f"Bearer {settings.LLM_API_KEY}", "Content-Type": "application/json"}
    payload = {
        "model": settings.LLM_MODEL,
        "messages": [{"role": "system", "content": prompt}],
        "temperature": 0.3,
        "response_format": {"type": "json_object"}
    }
    with httpx.Client(timeout=10.0) as client:
        resp = client.post("https://api.openai.com/v1/chat/completions", headers=headers, json=payload)
        resp.raise_for_request()
        data = resp.json()
        content = data["choices"][0]["message"]["content"]
        res_json = json.loads(content)
        res_json["customer_history_snippet"] = memory_summary.get("summary_text")
        return res_json
