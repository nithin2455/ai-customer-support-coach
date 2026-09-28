import re
from typing import Dict, Any, Optional, List, Callable, Tuple
from sqlalchemy.orm import Session
from app.models.domain import Order


class ResponseRule:
    def __init__(
        self,
        intent: str,
        patterns: List[str],
        priority: int,
        generator: Callable[[str, Optional[Dict[str, Any]], Optional[Session]], str],
        requires_db_lookup: bool = False,
        requires_human_approval: bool = False
    ):
        self.intent = intent
        self.patterns = [re.compile(p, re.IGNORECASE) for p in patterns]
        self.priority = priority
        self.generator = generator
        self.requires_db_lookup = requires_db_lookup
        self.requires_human_approval = requires_human_approval

    def matches(self, text: str) -> bool:
        t = text.strip().lower()
        return any(p.search(t) for p in self.patterns)

    def generate(self, text: str, context: Optional[Dict[str, Any]] = None, db: Optional[Session] = None) -> str:
        return self.generator(text, context, db)


# ----------------------------------------------------------------------
# Rule Response Generators
# ----------------------------------------------------------------------

def _gen_greeting(text: str, context: Optional[Dict[str, Any]], db: Optional[Session]) -> str:
    return (
        "Hello! Welcome to Customer Support. How can I assist you today? "
        "Feel free to ask about delivery times, order status, returns, or account settings."
    )


def _gen_delivery_info(text: str, context: Optional[Dict[str, Any]], db: Optional[Session]) -> str:
    return (
        "Standard delivery usually takes 3–5 business days. Express shipping is delivered within 1–2 business days. "
        "If you share your order number, I can check the exact status of your specific order."
    )


def _gen_shipping_info(text: str, context: Optional[Dict[str, Any]], db: Optional[Session]) -> str:
    return (
        "We partner with leading global carriers including FedEx, UPS, and DHL. "
        "Standard shipping is free on orders over $50. Once dispatched, you will receive real-time carrier tracking updates via email."
    )


def _extract_order_id(text: str) -> Optional[str]:
    # Matches #98213, order 98213, #ORD-98213, ORD-98213
    m = re.search(r"#?((?:ORD-)?\d{4,8})", text, re.IGNORECASE)
    if m:
        return m.group(1).replace("#", "").strip()
    return None


def _gen_order_status(text: str, context: Optional[Dict[str, Any]], db: Optional[Session]) -> str:
    order_id = _extract_order_id(text)

    # Fallback to context memory if order ID not directly in text
    if not order_id and context and context.get("memory_summary", {}).get("summary_text"):
        sum_text = context["memory_summary"]["summary_text"]
        m = re.search(r"#?((?:ORD-)?\d{4,8})", sum_text)
        if m:
            order_id = m.group(1).replace("#", "").strip()

    if not order_id:
        return (
            "I would be glad to help check your order status. Please provide your order number "
            "(e.g., #98213) so I can retrieve the shipment details."
        )

    # Clean lookup key
    norm_id = order_id.upper()
    digits_only = re.sub(r"[^\d]", "", norm_id)

    if db:
        # Check database for exact order
        order = db.query(Order).filter(
            (Order.order_number == norm_id) |
            (Order.order_number == digits_only) |
            (Order.order_number == f"ORD-{digits_only}")
        ).first()

        if order:
            carrier_part = f" via {order.carrier}" if order.carrier else ""
            tracking_part = f" (Tracking #{order.tracking_number})" if order.tracking_number else ""
            eta_part = f" and is expected to arrive {order.estimated_delivery}." if order.estimated_delivery else "."
            return f"Your order #{order.order_number} has been shipped{carrier_part}{tracking_part}{eta_part}"

    # If order does not exist in database:
    return f"I couldn't find order #{order_id}. Please verify the order number or contact support."


def _gen_return_policy(text: str, context: Optional[Dict[str, Any]], db: Optional[Session]) -> str:
    return (
        "Our return policy allows items to be returned within 30 days of delivery for a full refund or exchange. "
        "Items must be in original condition with tags and packaging intact. Prepaid return shipping labels are provided free of charge."
    )


def _gen_refund_policy(text: str, context: Optional[Dict[str, Any]], db: Optional[Session]) -> str:
    return (
        "Our refund policy: once a returned item is received and inspected at our fulfillment center, "
        "refunds are processed back to the original payment method within 5–7 business days. "
        "For items returned in original packaging within 30 days, 100% of the item price is refunded."
    )


def _gen_cancellation_policy(text: str, context: Optional[Dict[str, Any]], db: Optional[Session]) -> str:
    return (
        "Orders can be cancelled free of charge within 1 hour of placement before they enter warehouse fulfillment. "
        "To cancel an order, navigate to Account > Orders and select 'Cancel Order'. If an order has already shipped, "
        "it can be returned under our standard 30-day return policy upon arrival."
    )


def _gen_payment_methods(text: str, context: Optional[Dict[str, Any]], db: Optional[Session]) -> str:
    return (
        "We accept all major payment methods including Visa, MasterCard, American Express, Discover, PayPal, "
        "Apple Pay, Google Pay, Net Banking, and UPI. All transactions are encrypted with 256-bit SSL security."
    )


def _gen_business_hours(text: str, context: Optional[Dict[str, Any]], db: Optional[Session]) -> str:
    return (
        "Our customer support team is available Monday through Friday from 8:00 AM to 8:00 PM EST, "
        "and Saturday from 9:00 AM to 5:00 PM EST. Our automated self-service portal and AI assistant are available 24/7."
    )


def _gen_account_help(text: str, context: Optional[Dict[str, Any]], db: Optional[Session]) -> str:
    return (
        "You can manage your account settings, update your shipping address, or reset your password by logging into your profile. "
        "To reset your password, click 'Forgot Password' on the login page, and a secure password reset link will be emailed to you."
    )


def _gen_contact_support(text: str, context: Optional[Dict[str, Any]], db: Optional[Session]) -> str:
    return (
        "You can reach our support team anytime by email at support@company.com or by calling +1-800-555-0199 "
        "during business hours (Mon–Fri 8 AM–8 PM EST). You can also continue chatting with us right here."
    )


# ----------------------------------------------------------------------
# Centralized Rules Registry (Ordered by Priority)
# ----------------------------------------------------------------------

RESPONSE_RULES: List[ResponseRule] = [
    # 1. Order Status (Priority 100 - specific inquiries like 'Where is my order #98213?')
    ResponseRule(
        intent="Order Status",
        patterns=[
            r"where is my order",
            r"status of (?:my )?order",
            r"track (?:my )?order",
            r"order status",
            r"check (?:my )?order",
            r"#\d{4,8}",
            r"order #?(?:ord-)?\d{4,8}"
        ],
        priority=100,
        generator=_gen_order_status,
        requires_db_lookup=True
    ),

    # 2. Return Policy (Priority 90)
    ResponseRule(
        intent="Return Policy",
        patterns=[
            r"return policy",
            r"how (?:do|can) i return",
            r"how to return",
            r"return window",
            r"can i return",
            r"return process",
            r"returning (?:an|my)? item"
        ],
        priority=90,
        generator=_gen_return_policy
    ),

    # 3. Refund Policy (Informational questions only; Priority 90)
    ResponseRule(
        intent="Refund Policy",
        patterns=[
            r"what is (?:the|your) refund policy",
            r"refund policy",
            r"how (?:do|does) refunds? work",
            r"explain (?:the )?refund policy",
            r"tell me about (?:the )?refund policy"
        ],
        priority=90,
        generator=_gen_refund_policy
    ),

    # 4. Cancellation Policy (Priority 85)
    ResponseRule(
        intent="Cancellation Policy",
        patterns=[
            r"cancellation policy",
            r"cancel(?:ling)? (?:an )?order policy",
            r"how (?:do|can) i cancel (?:my )?order",
            r"can i cancel (?:my )?order",
            r"order cancellation"
        ],
        priority=85,
        generator=_gen_cancellation_policy
    ),

    # 5. Delivery Times & Estimates (Priority 80)
    ResponseRule(
        intent="Delivery Information",
        patterns=[
            r"delivery time",
            r"how long.*delivery",
            r"how long.*shipping",
            r"when will.*arrive",
            r"how many days.*delivery",
            r"delivery timing",
            r"standard delivery"
        ],
        priority=80,
        generator=_gen_delivery_info
    ),

    # 6. General Shipping Information (Priority 75)
    ResponseRule(
        intent="Shipping Information",
        patterns=[
            r"shipping method",
            r"which carrier",
            r"do you ship internationally",
            r"international shipping",
            r"shipping cost",
            r"free shipping",
            r"shipping information"
        ],
        priority=75,
        generator=_gen_shipping_info
    ),

    # 7. Payment Methods (Priority 70)
    ResponseRule(
        intent="Payment Methods",
        patterns=[
            r"payment method",
            r"how can i pay",
            r"what payment.*accept",
            r"do you take (?:paypal|apple pay|credit card|upi)",
            r"accepted payment"
        ],
        priority=70,
        generator=_gen_payment_methods
    ),

    # 8. Business Hours (Priority 70)
    ResponseRule(
        intent="Business Hours",
        patterns=[
            r"business hour",
            r"operating hour",
            r"opening hour",
            r"when are you open",
            r"support hour",
            r"working hour",
            r"what time do you open"
        ],
        priority=70,
        generator=_gen_business_hours
    ),

    # 9. Account & Help Information (Priority 65)
    ResponseRule(
        intent="Account Support",
        patterns=[
            r"reset.*password",
            r"forgot.*password",
            r"change.*password",
            r"password reset",
            r"login help",
            r"cant log in",
            r"cannot log in",
            r"account setting"
        ],
        priority=65,
        generator=_gen_account_help
    ),

    # 10. Contact / Support Information (Priority 60)
    ResponseRule(
        intent="Contact Support",
        patterns=[
            r"contact (?:support|you|us|customer service)",
            r"support email",
            r"customer service phone",
            r"how to reach (?:support|a human|you)",
            r"support phone number",
            r"phone number for support"
        ],
        priority=60,
        generator=_gen_contact_support
    ),

    # 11. Polite Greeting (Priority 50)
    ResponseRule(
        intent="Greeting",
        patterns=[
            r"^(?:hi|hello|hey|good morning|good afternoon|good evening|howdy)(?:[!.\s]|$)"
        ],
        priority=50,
        generator=_gen_greeting
    )
]


def match_response_rule(
    text: str,
    context: Optional[Dict[str, Any]] = None,
    db: Optional[Session] = None
) -> Optional[Tuple[ResponseRule, str]]:
    """
    Checks incoming text against the centralized rules registry in priority order.
    Returns (matched_rule, response_text) or None if no deterministic rule matches.
    """
    sorted_rules = sorted(RESPONSE_RULES, key=lambda r: r.priority, reverse=True)
    for rule in sorted_rules:
        if rule.matches(text):
            response_text = rule.generate(text, context, db)
            return rule, response_text
    return None
