import datetime
from typing import Dict, Any, Optional
from sqlalchemy.orm import Session
from app.models.domain import Conversation, Message

# Configurable SLA Targets Policy (Minutes)
SLA_POLICY = {
    "URGENT": {"first_response_mins": 15, "resolution_mins": 120},
    "HIGH": {"first_response_mins": 30, "resolution_mins": 240},
    "NORMAL": {"first_response_mins": 120, "resolution_mins": 720},
    "LOW": {"first_response_mins": 240, "resolution_mins": 1440}
}


def calculate_conversation_sla(
    db: Session,
    conversation_id: int,
    priority: str = "HIGH",
    now: Optional[datetime.datetime] = None
) -> Dict[str, Any]:
    """
    Phase 6 Dynamic SLA Tracking Service.
    Calculates SLA status, response deadlines, resolution deadlines, and breach/at-risk states
    from actual conversation and message timestamps in PostgreSQL.
    """
    if now is None:
        now = datetime.datetime.utcnow()

    conv = db.query(Conversation).filter(Conversation.id == conversation_id).first()
    if not conv:
        start_time = now
        conv_status = "active"
    else:
        start_time = conv.created_at or now
        conv_status = conv.status

    target = SLA_POLICY.get(priority.upper(), SLA_POLICY["NORMAL"])
    resp_mins = target["first_response_mins"]
    res_mins = target["resolution_mins"]

    resp_deadline = start_time + datetime.timedelta(minutes=resp_mins)
    res_deadline = start_time + datetime.timedelta(minutes=res_mins)

    # Check if agent has already responded
    has_agent_replied = False
    if conv and conv.messages:
        has_agent_replied = any(m.sender_type == "agent" for m in conv.messages)

    resp_remaining_sec = int((resp_deadline - now).total_seconds())
    res_remaining_sec = int((res_deadline - now).total_seconds())

    is_response_breached = not has_agent_replied and resp_remaining_sec < 0
    is_resolution_breached = conv_status != "resolved" and res_remaining_sec < 0
    is_at_risk = not is_response_breached and not is_resolution_breached and (resp_remaining_sec < 900 or res_remaining_sec < 1800)

    if conv_status == "resolved":
        status = "Resolved"
    elif is_response_breached:
        status = "Response Breached"
    elif is_resolution_breached:
        status = "Resolution Breached"
    elif is_at_risk:
        status = "At Risk"
    else:
        status = "On Track"

    return {
        "status": status,
        "priority": priority.upper(),
        "first_response_target_minutes": resp_mins,
        "resolution_target_minutes": res_mins,
        "response_deadline": resp_deadline.isoformat(),
        "resolution_deadline": res_deadline.isoformat(),
        "response_time_remaining_seconds": max(resp_remaining_sec, 0),
        "resolution_time_remaining_seconds": max(res_remaining_sec, 0),
        "is_response_breached": is_response_breached,
        "is_resolution_breached": is_resolution_breached,
        "is_at_risk": is_at_risk
    }
