from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from app.api.deps import get_db, get_optional_current_user
from app.models.domain import CoachingFeedback, ConversationFeedback, Conversation, User
from app.schemas.domain import FeedbackCreate, CSATFeedbackCreate

router = APIRouter()


@router.post("/feedback", summary="Log Agent Action on AI Suggestion (accepted / edited / ignored)")
def log_agent_coaching_feedback(
    req: FeedbackCreate,
    db: Session = Depends(get_db),
    current_user: Optional[User] = Depends(get_optional_current_user)
):
    if current_user and current_user.role == "customer":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Forbidden: Only agents can submit coaching feedback."
        )

    feedback = CoachingFeedback(
        conversation_id=req.conversation_id,
        message_id=req.message_id,
        agent_action=req.agent_action,
        suggested_response=req.suggested_response,
        actual_response=req.actual_response
    )
    db.add(feedback)
    db.commit()
    db.refresh(feedback)
    return {"status": "success", "feedback_id": feedback.id, "action": req.agent_action}


@router.post("/csat", summary="Log Customer CSAT Survey Feedback & Outcome")
def log_customer_csat(
    req: CSATFeedbackCreate,
    db: Session = Depends(get_db),
    current_user: Optional[User] = Depends(get_optional_current_user)
):
    conv = db.query(Conversation).filter(Conversation.id == req.conversation_id).first()
    if not conv:
        raise HTTPException(status_code=404, detail="Conversation not found")

    customer_id = conv.customer_id
    if current_user and current_user.role == "customer":
        if not current_user.customer_profile or current_user.customer_profile.id != conv.customer_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Forbidden: You cannot submit CSAT feedback for another customer's conversation."
            )
        customer_id = current_user.customer_profile.id

    feedback = ConversationFeedback(
        conversation_id=req.conversation_id,
        customer_id=customer_id,
        csat_rating=req.csat_rating,
        comments=req.comments,
        outcome=req.outcome or "Resolved"
    )
    db.add(feedback)

    # Update conversation status if outcome specified
    if req.outcome == "Escalated":
        conv.status = "escalated"
    elif req.outcome in ["Resolved", "Partially Resolved"]:
        conv.status = "resolved"

    db.commit()
    db.refresh(feedback)
    return {"status": "success", "csat_id": feedback.id, "rating": req.csat_rating, "outcome": feedback.outcome}
