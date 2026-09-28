from typing import Dict, Any, Optional, List
import logging

logger = logging.getLogger("escalation_service")


def evaluate_intelligent_escalation(
    stress_score: int,
    text: str,
    customer_context: Optional[Dict[str, Any]] = None,
    sla_info: Optional[Dict[str, Any]] = None
) -> Dict[str, Any]:
    """
    Phase 6 Intelligent Escalation Service.
    Evaluates stress levels, repeated unresolved issues, sensitive triggers, and SLA status
    to provide explainable escalation recommendations and bulleted justifications.
    """
    text_lower = text.lower() if text else ""
    ctx = customer_context or {}
    sla = sla_info or {}

    repeated_issue_info = ctx.get("repeated_issue", {})
    is_repeated = repeated_issue_info.get("is_repeated_issue", False)
    issue_type = repeated_issue_info.get("issue_type", "New Issue")

    sensitive_keywords = ["manager", "supervisor", "cancel", "legal", "lawyer", "unacceptable", "sue", "refund immediately"]
    has_sensitive_trigger = any(k in text_lower for k in sensitive_keywords)

    sla_status = sla.get("status", "On Track")
    is_sla_breached = sla.get("is_response_breached", False) or sla.get("is_resolution_breached", False)

    reasons_list: List[str] = []

    if stress_score >= 81:
        reasons_list.append(f"Customer stress is CRITICAL ({stress_score}/100)")
    elif stress_score >= 61:
        reasons_list.append(f"Customer stress is HIGH ({stress_score}/100)")

    if is_repeated:
        reasons_list.append(f"Issue has been reported previously ({issue_type})")

    if has_sensitive_trigger:
        reasons_list.append("Customer requested manager / legal escalation or cancellation")

    if is_sla_breached or sla_status in ["Response Breached", "Resolution Breached"]:
        reasons_list.append(f"SLA target breached ({sla_status})")
    elif sla_status == "At Risk":
        reasons_list.append("SLA deadline is At Risk (< 15 mins remaining)")

    # Escalation Tier & Recommendation
    if stress_score >= 81 or (is_repeated and stress_score >= 61) or is_sla_breached or "legal" in text_lower:
        escalation_recommended = True
        escalation_tier = "CRITICAL"
        recommended_action = "Immediate Senior Lead Action: Review ticket #LOG-98213 and contact customer directly."
    elif stress_score >= 61 or is_repeated or has_sensitive_trigger or sla_status == "At Risk":
        escalation_recommended = True
        escalation_tier = "HIGH"
        recommended_action = "High Priority Review: Check prior logistics escalation notes and expedite carrier inquiry."
    else:
        escalation_recommended = False
        escalation_tier = "NONE"
        recommended_action = "Standard Agent Handling: Follow standard resolution guidelines."

    if escalation_recommended:
        explanation_intro = f"Escalation recommended ({escalation_tier} Priority) because:"
        escalation_reason = explanation_intro + "\n" + "\n".join([f"• {r}" for r in reasons_list])
    else:
        escalation_reason = "No immediate escalation required. Ticket is within standard handling parameters."

    return {
        "escalation_recommended": escalation_recommended,
        "escalation_tier": escalation_tier,
        "escalation_reason": escalation_reason,
        "reasons_list": reasons_list,
        "recommended_action": recommended_action
    }
