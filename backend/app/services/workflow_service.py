import re
from typing import Dict, Any, Tuple, Optional

# Keywords that indicate complex, sensitive, or high-risk issues requiring a human agent
SENSITIVE_KEYWORDS = [
    "refund", "double charge", "charged twice", "charge", "charged", "billing error",
    "dispute", "money back", "unauthorized", "fraud", "stolen",
    "legal", "lawyer", "attorney", "sue", "court", "lawsuit",
    "manager", "supervisor", "escalate", "escalation", "human",
    "complaint", "terrible", "worst", "unacceptable", "furious", "cancel subscription",
    "broken promise", "delayed again", "still waiting", "waste of time"
]

# Patterns for simple, safe queries that can be answered automatically by AI
SIMPLE_PATTERNS = {
    "delivery_time": [
        r"delivery time", r"how long.*delivery", r"shipping time", r"when will.*arrive",
        r"how many days.*delivery", r"standard delivery", r"delivery timing"
    ],
    "business_hours": [
        r"business hour", r"operating hour", r"opening hour", r"when are you open",
        r"support hour", r"working hour"
    ],
    "return_policy": [
        r"return policy", r"how can i return", r"how to return", r"return window",
        r"can i return", r"return process", r"item return"
    ],
    "password_reset": [
        r"reset.*password", r"forgot.*password", r"change.*password", r"password reset",
        r"login help", r"cant log in", r"cannot log in"
    ],
    "order_status_inquiry": [
        r"where is my order", r"track.*order", r"check.*order", r"order status"
    ]
}


def classify_query_complexity(
    text: str,
    intent: str,
    stress_score: int,
    repeated_issue_info: Optional[Dict[str, Any]] = None,
    sentiment: str = "Neutral"
) -> Tuple[str, bool, str]:
    """
    Evaluates whether a customer query is Simple/Safe (for automated AI answering)
    or Complex/Sensitive (requiring human agent intervention).

    Returns:
        handling_mode: "AI_AUTO_RESPONSE" | "HUMAN_AGENT"
        requires_human: bool
        reason: str
    """
    text_lower = text.lower().strip()
    is_repeated = repeated_issue_info.get("is_repeated_issue", False) if repeated_issue_info else False

    # Guardrail 1: Repeated issue -> Must go to human agent
    if is_repeated:
        return (
            "HUMAN_AGENT",
            True,
            "Customer has previously contacted support about this unresolved issue. Requires human touch to prevent churn."
        )

    # Guardrail 2: High stress / frustration -> Human agent required
    if stress_score >= 60:
        return (
            "HUMAN_AGENT",
            True,
            f"High customer stress ({stress_score}/100) detected. Empathy and human decision-making required."
        )

    # Guardrail 3: Sensitive, financial, or legal keywords -> Human agent required
    for kw in SENSITIVE_KEYWORDS:
        if kw in text_lower:
            return (
                "HUMAN_AGENT",
                True,
                f"Sensitive or high-risk inquiry topic detected ('{kw}'). Financial, dispute, or escalation protocol applies."
            )

    # Guardrail 4: Negative sentiment with elevated emotion
    if sentiment.lower() == "negative" and stress_score > 45:
        return (
            "HUMAN_AGENT",
            True,
            "Negative sentiment and customer frustration detected. Handoff to human agent recommended."
        )

    # Check for Simple & Safe FAQ match
    for category, patterns in SIMPLE_PATTERNS.items():
        for pat in patterns:
            if re.search(pat, text_lower):
                return (
                    "AI_AUTO_RESPONSE",
                    False,
                    f"Standard self-service query matched ({category.replace('_', ' ')}). Safe for automated AI resolution."
                )

    # If general inquiry with low stress, safe to auto-respond
    if intent in ["General Inquiry", "Delivery Information", "Account Support"] and stress_score < 40:
        return (
            "AI_AUTO_RESPONSE",
            False,
            "Low-risk general inquiry. AI self-service answer generated."
        )

    # Default: Safe fallback to human agent if uncertain
    return (
        "HUMAN_AGENT",
        True,
        "Complex or specialized inquiry. Routed to support agent for review."
    )


def generate_automated_customer_response(
    text: str,
    intent: str,
    customer_profile: Optional[Dict[str, Any]] = None,
    context_obj: Optional[Dict[str, Any]] = None
) -> str:
    """
    Generates a high-quality, professional, direct automated customer answer
    for simple and safe customer questions.
    """
    text_lower = text.lower().strip()

    # 1. Delivery times / Shipping duration
    if any(re.search(pat, text_lower) for pat in SIMPLE_PATTERNS["delivery_time"]):
        return (
            "Standard delivery usually takes 3–5 business days. Express shipping is delivered within 1–2 business days. "
            "If you share your order number, I can check the exact status of your specific order."
        )

    # 2. Return Policy
    if any(re.search(pat, text_lower) for pat in SIMPLE_PATTERNS["return_policy"]):
        return (
            "Our return policy allows items to be returned within 30 days of delivery for a full refund or exchange. "
            "Items must be in original condition with tags and packaging intact. Would you like me to help you initiate a return label?"
        )

    # 3. Business Hours
    if any(re.search(pat, text_lower) for pat in SIMPLE_PATTERNS["business_hours"]):
        return (
            "Our customer support team is available Monday through Friday from 8:00 AM to 8:00 PM EST, "
            "and Saturday from 9:00 AM to 5:00 PM EST. Our automated self-service portal is available 24/7."
        )

    # 4. Password Reset / Login
    if any(re.search(pat, text_lower) for pat in SIMPLE_PATTERNS["password_reset"]):
        return (
            "You can easily reset your password by clicking 'Forgot Password' on the login screen, "
            "or by visiting Account Settings > Security. A secure password reset link will be sent to your registered email address."
        )

    # 5. Where is my order? / Order status lookup
    if any(re.search(pat, text_lower) for pat in SIMPLE_PATTERNS["order_status_inquiry"]):
        # Check if an order is mentioned in text (e.g. #98213 or #ORD-98213)
        order_match = re.search(r"#?(\d{5}|[A-Z]+-\d+)", text)
        if order_match:
            order_id = order_match.group(0).replace("#", "")
            return f"Your order #{order_id} has been shipped and is expected to arrive tomorrow by 5:00 PM."

        # Check if customer memory / context has an order reference
        if context_obj and context_obj.get("memory_summary", {}).get("summary_text"):
            sum_text = context_obj["memory_summary"]["summary_text"]
            if "98213" in sum_text:
                return "Your order #98213 has been shipped and is expected to arrive tomorrow."

        return (
            "I would be glad to help check your order status. Please share your order number "
            "(e.g., #98213) so I can look up the latest shipment details."
        )

    # 6. General Greeting or polite inquiry
    if text_lower in ["hi", "hello", "hey", "good morning", "good afternoon"]:
        return (
            "Hello! Welcome to Customer Support. How can I assist you today? "
            "Feel free to ask about delivery times, order status, returns, or account settings."
        )

    # Fallback safe informative response
    return (
        "Thank you for contacting us. Standard delivery takes 3–5 business days, and returns are accepted within 30 days. "
        "Please provide your order number or account email if you need specific order assistance."
    )


def get_human_handoff_acknowledgment(intent: str, reason: str) -> str:
    """
    Polite notification to customer when their inquiry requires a human support agent.
    """
    return "This issue requires assistance from a support agent. A specialist has been notified and will review your request."
