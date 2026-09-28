from typing import List, Dict, Any, Optional
from sqlalchemy.orm import Session
from app.models.domain import CustomerMemory, Customer, Conversation, Message


def get_customer_profile_summary(db: Session, customer_id: int) -> Dict[str, Any]:
    """
    Builds enhanced Customer Profile summary including classification badges.
    """
    customer = db.query(Customer).filter(Customer.id == customer_id).first()
    if not customer:
        return {}

    memories = db.query(CustomerMemory).filter(
        CustomerMemory.customer_id == customer_id
    ).order_by(CustomerMemory.created_at.desc()).all()

    # Classification Badge
    if customer.total_contacts > 2 or customer.unresolved_issues > 0:
        customer_badge = "Repeated Issue Customer"
    elif customer.total_contacts > 1:
        customer_badge = "Returning Customer"
    else:
        customer_badge = "New Customer"

    latest_mem = memories[0] if memories else None

    return {
        "id": customer.id,
        "name": customer.user.name,
        "email": customer.user.email,
        "phone": customer.phone,
        "tier": customer.tier,
        "badge": customer_badge,
        "total_contacts": customer.total_contacts,
        "unresolved_issues": customer.unresolved_issues,
        "current_stress_score": customer.current_stress_score,
        "predicted_style": customer.predicted_style,
        "previous_issue": latest_mem.issue_summary if latest_mem else "None",
        "previous_resolution": latest_mem.resolution_summary if latest_mem else "None",
        "previous_sentiment": latest_mem.sentiment_label if latest_mem else "Neutral",
        "previous_stress_score": latest_mem.stress_score if latest_mem else 70,
        "previous_agent": latest_mem.agent_name if latest_mem else "Sarah Jenkins"
    }


def get_customer_timeline(db: Session, customer_id: int) -> List[Dict[str, Any]]:
    """
    Generates chronological customer interaction timeline from stored records.
    """
    memories = db.query(CustomerMemory).filter(
        CustomerMemory.customer_id == customer_id
    ).order_by(CustomerMemory.created_at.asc()).all()

    timeline = []
    for idx, mem in enumerate(memories, start=1):
        timeline.append({
            "step": f"Touchpoint {idx}",
            "date": mem.created_at.strftime("%Y-%m-%d"),
            "issue": mem.issue_summary,
            "sentiment": mem.sentiment_label or "Negative",
            "stress_score": mem.stress_score or 75,
            "agent": mem.agent_name or "Sarah Jenkins",
            "resolution": mem.resolution_summary or "Pending logistics update",
            "status": "Unresolved" if not mem.resolution_summary or "awaiting" in (mem.resolution_summary or "").lower() else "Resolved"
        })

    return timeline


def get_customer_memory_summary(db: Session, customer_id: int) -> Dict[str, Any]:
    """
    Surfaces recent customer history and unresolved issues.
    """
    profile = get_customer_profile_summary(db, customer_id)
    memories = db.query(CustomerMemory).filter(
        CustomerMemory.customer_id == customer_id
    ).order_by(CustomerMemory.created_at.desc()).limit(3).all()

    summary_lines = [
        f"Customer: {profile.get('name')} | Tier: {profile.get('tier')} | Classification: {profile.get('badge')}",
        f"Total Contacts: {profile.get('total_contacts')} | Unresolved Issues: {profile.get('unresolved_issues')}"
    ]

    formatted_memories = []
    for mem in memories:
        res = mem.resolution_summary if mem.resolution_summary else "Pending resolution"
        summary_lines.append(f"• Prior Touchpoint ({mem.created_at.strftime('%Y-%m-%d')}): {mem.issue_summary} [Agent: {mem.agent_name or 'Sarah Jenkins'} | Resolution: {res}]")
        formatted_memories.append({
            "id": mem.id,
            "issue_summary": mem.issue_summary,
            "resolution_summary": mem.resolution_summary,
            "sentiment_label": mem.sentiment_label,
            "stress_score": mem.stress_score or 0,
            "agent_name": mem.agent_name or "Sarah Jenkins",
            "key_notes": mem.key_notes,
            "created_at": mem.created_at.isoformat() if hasattr(mem.created_at, 'isoformat') else str(mem.created_at)
        })

    return {
        "summary_text": "\n".join(summary_lines),
        "profile": profile,
        "memories": formatted_memories
    }
