from typing import Dict, Any, List
from sqlalchemy.orm import Session
from app.models.domain import CustomerMemory, Conversation, Message, AIAnalysis


def detect_repeated_issue(
    db: Session,
    customer_id: int,
    current_message: str,
    current_intent: str
) -> Dict[str, Any]:
    """
    Analyzes current customer message and intent against historical touchpoints
    and memory records to detect if this is a repeated or related unresolved issue.
    """
    memories = db.query(CustomerMemory).filter(
        CustomerMemory.customer_id == customer_id
    ).order_by(CustomerMemory.created_at.desc()).all()

    text_lower = current_message.lower()
    intent_lower = current_intent.lower()

    # Keywords matching previous order delay/status issues
    delay_keywords = ["order", "delay", "haven't arrived", "hasn't arrived", "waiting", "ship", "deliver", "tracking", "package"]
    is_order_delay_query = any(kw in text_lower for kw in delay_keywords) or "order" in intent_lower

    matched_memories: List[Dict[str, Any]] = []
    is_repeated = False
    issue_type = "New Issue"
    reason = "No matching prior issues found in interaction history."

    for mem in memories:
        mem_text = (mem.issue_summary or "").lower()
        if is_order_delay_query and any(kw in mem_text for kw in delay_keywords):
            matched_memories.append({
                "id": mem.id,
                "date": mem.created_at.strftime("%Y-%m-%d"),
                "issue_summary": mem.issue_summary,
                "resolution_summary": mem.resolution_summary,
                "sentiment": mem.sentiment_label,
                "agent_name": mem.agent_name or "Sarah Jenkins"
            })

    if matched_memories:
        is_repeated = True
        if len(matched_memories) >= 2 or "still" in text_lower or "again" in text_lower:
            issue_type = "Repeated Issue"
            reason = f"Customer previously contacted support {len(matched_memories)} times regarding the same order delay."
        else:
            issue_type = "Related Issue"
            reason = "Customer has a previous open or related touchpoint regarding order delivery."
    elif "again" in text_lower or "contacted support" in text_lower or "3 days ago" in text_lower:
        is_repeated = True
        issue_type = "Repeated Issue"
        reason = "Customer referenced prior contact regarding the same unresolved problem."

    return {
        "is_repeated_issue": is_repeated,
        "issue_type": issue_type,
        "previous_related_conversations": matched_memories,
        "reason": reason
    }
