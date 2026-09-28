from typing import Dict, Any, Optional
import logging

logger = logging.getLogger("routing_service")


def evaluate_smart_routing(
    intent: str,
    stress_score: int,
    text: str,
    customer_context: Optional[Dict[str, Any]] = None
) -> Dict[str, Any]:
    """
    Phase 6 AI Smart Routing Engine.
    Determines optimal department, queue priority, sensitivity, complexity, and routing explanation
    based on intent, customer stress, message content, customer tier, and repeated issue history.
    """
    text_lower = text.lower() if text else ""
    intent_lower = intent.lower() if intent else ""
    ctx = customer_context or {}

    repeated_issue_info = ctx.get("repeated_issue", {})
    is_repeated = repeated_issue_info.get("is_repeated_issue", False)
    cust_profile = ctx.get("customer", {})
    is_vip = cust_profile.get("tier") == "VIP"

    # 1. Category / Department Matching with Safe Fallback
    if any(k in intent_lower or k in text_lower for k in ["order", "shipping", "delivery", "tracking", "package", "logistics", "delay"]):
        dept_code = "ORDERS"
        dept_name = "Order Fulfillment & Logistics"
        confidence = 0.94
    elif any(k in intent_lower or k in text_lower for k in ["billing", "payment", "charge", "invoice", "refund", "subscription"]):
        dept_code = "BILLING"
        dept_name = "Billing & Payments"
        confidence = 0.91
    elif any(k in intent_lower or k in text_lower for k in ["tech", "bug", "error", "broken", "login", "app", "crash"]):
        dept_code = "TECH"
        dept_name = "Technical Support"
        confidence = 0.89
    elif any(k in intent_lower or k in text_lower for k in ["general", "inquiry", "question", "help", "hours"]):
        dept_code = "GENERAL"
        dept_name = "Customer Care"
        confidence = 0.85
    else:
        dept_code = "OTHER"
        dept_name = "Other / Unclassified"
        confidence = 0.70

    # 2. Sensitivity & Complexity Indicators
    sensitive_triggers = ["cancel", "supervisor", "legal", "lawyer", "manager", "unacceptable", "sue", "breach", "complaint"]
    is_sensitive = stress_score >= 80 or any(k in text_lower for k in sensitive_triggers)
    is_complex = is_repeated or is_vip or len(text_lower.split()) > 25

    # 3. Priority Determination
    if is_sensitive or (is_repeated and stress_score >= 60) or (is_vip and stress_score >= 70):
        priority = "URGENT"
    elif stress_score >= 50 or is_repeated or is_complex:
        priority = "HIGH"
    elif stress_score >= 30:
        priority = "NORMAL"
    else:
        priority = "LOW"

    # 4. Explainable Routing Reason
    reasons = []
    if is_repeated:
        reasons.append(f"Repeated issue ({repeated_issue_info.get('issue_type', 'Order Delay')}) detected")
    if stress_score >= 60:
        reasons.append(f"high customer stress ({stress_score}/100)")
    if is_sensitive:
        reasons.append("sensitive complaint trigger")
    if is_vip:
        reasons.append("VIP customer account")

    if reasons:
        routing_reason = f"Routed to {dept_name} with {priority} priority due to " + ", ".join(reasons) + "."
    else:
        routing_reason = f"Standard inquiry routed to {dept_name} queue."

    return {
        "recommended_department": dept_name,
        "department_code": dept_code,
        "priority": priority,
        "routing_reason": routing_reason,
        "confidence": confidence,
        "is_sensitive": is_sensitive,
        "is_complex": is_complex
    }
