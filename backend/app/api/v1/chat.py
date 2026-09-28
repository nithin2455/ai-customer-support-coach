from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from app.api.deps import (
    get_db, get_current_user, get_optional_current_user, get_current_customer, get_current_agent
)
from app.models.domain import (
    Conversation, Message, Customer, Agent, AIAnalysis, User, Department, CoachingFeedback, CustomerMemory, Order
)
from app.schemas.domain import (
    ProcessMessageRequest, ProcessMessageResponse, ConversationOut, MessageOut, AIAnalysisOut, CoachingPayload,
    CustomerOut, CustomerMemoryOut, AgentReplyRequest, TransferRequest
)
from app.ai.nlp_analyzer import analyze_customer_message
from app.ai.llm_coach import generate_coaching_recommendation
from app.services.stress_service import calculate_stress_score
from app.services.style_service import predict_communication_style
from app.services.memory_service import get_customer_memory_summary, get_customer_profile_summary, get_customer_timeline
from app.services.routing_service import evaluate_smart_routing
from app.services.context_service import build_full_customer_context
from app.services.workflow_service import (
    classify_query_complexity,
    generate_automated_customer_response,
    get_human_handoff_acknowledgment
)
from app.services.response_engine import process_customer_message
from app.core.languages import get_locale, detect_text_language, get_language_name
from app.services.translation_service import translate_text, translate_to_english, translate_from_english
from pydantic import BaseModel

router = APIRouter()


def _format_conversation(conv: Conversation, db: Session) -> dict:
    cust = conv.customer
    profile = get_customer_profile_summary(db, cust.id)

    agent_out = None
    if conv.agent:
        agent_user = conv.agent.user
        agent_out = {
            "id": conv.agent.id,
            "name": agent_user.name,
            "email": agent_user.email,
            "department_name": conv.agent.department.name if conv.agent.department else "General",
            "status": conv.agent.status,
            "skill_level": conv.agent.skill_level
        }

    prev_agent_out = None
    if conv.previous_agent:
        prev_user = conv.previous_agent.user
        prev_agent_out = {
            "id": conv.previous_agent.id,
            "name": prev_user.name,
            "email": prev_user.email,
            "department_name": conv.previous_agent.department.name if conv.previous_agent.department else "General",
            "status": conv.previous_agent.status,
            "skill_level": conv.previous_agent.skill_level
        }

    dept_name = conv.department.name if conv.department else "General Support"

    latest_coaching = None
    last_cust_msg = db.query(Message).filter(
        Message.conversation_id == conv.id,
        Message.sender_type == "customer"
    ).order_by(Message.created_at.desc()).first()

    if last_cust_msg and last_cust_msg.ai_analysis and last_cust_msg.ai_analysis.coaching_payload:
        latest_coaching = last_cust_msg.ai_analysis.coaching_payload

    # Format memories safely to avoid Pydantic serialization error
    memories_out = [
        {
            "id": m.id,
            "issue_summary": m.issue_summary,
            "resolution_summary": m.resolution_summary,
            "sentiment_label": m.sentiment_label,
            "stress_score": m.stress_score or 0,
            "agent_name": m.agent_name or "Sarah Jenkins",
            "key_notes": m.key_notes,
            "created_at": m.created_at
        } for m in (cust.memories or [])
    ]

    # Build full context for this conversation
    full_context = build_full_customer_context(db, conv.id)

    return {
        "id": conv.id,
        "customer": {
            "id": cust.id,
            "name": profile["name"],
            "email": profile["email"],
            "phone": cust.phone,
            "tier": cust.tier,
            "badge": profile.get("badge", "Returning Customer"),
            "total_contacts": cust.total_contacts,
            "unresolved_issues": cust.unresolved_issues,
            "current_stress_score": cust.current_stress_score,
            "predicted_style": cust.predicted_style,
            "memories": memories_out
        },
        "agent": agent_out,
        "previous_agent": prev_agent_out,
        "department_name": dept_name,
        "status": conv.status,
        "priority": conv.priority,
        "is_transferred": conv.is_transferred,
        "transfer_context": conv.transfer_context,
        "language_code": getattr(conv, "language_code", "en") or "en",
        "locale": getattr(conv, "locale", "en-IN") or "en-IN",
        "created_at": conv.created_at,
        "messages": conv.messages,
        "latest_coaching": latest_coaching,
        "full_context": full_context
    }


@router.get("/customer/me/conversations", response_model=List[ConversationOut])
def list_my_conversations(
    current_customer: Customer = Depends(get_current_customer),
    db: Session = Depends(get_db)
):
    """Fetch all conversations strictly belonging to the authenticated customer."""
    conversations = db.query(Conversation).filter(
        Conversation.customer_id == current_customer.id
    ).order_by(Conversation.created_at.desc()).all()
    return [_format_conversation(conv, db) for conv in conversations]


@router.post("/customer/me/conversations", response_model=ConversationOut)
def create_my_conversation(
    current_customer: Customer = Depends(get_current_customer),
    db: Session = Depends(get_db)
):
    """Starts a new clean conversation strictly for the authenticated customer."""
    new_conv = Conversation(
        customer_id=current_customer.id,
        agent_id=1,  # Default agent assigned for support
        department_id=1,
        status="active",
        priority="normal"
    )
    db.add(new_conv)
    db.commit()
    db.refresh(new_conv)
    return _format_conversation(new_conv, db)


@router.get("/customer/me/orders")
def list_my_orders(
    current_customer: Customer = Depends(get_current_customer),
    db: Session = Depends(get_db)
):
    """Fetch verified orders belonging strictly to the authenticated customer."""
    orders = db.query(Order).filter(
        Order.customer_id == current_customer.id
    ).order_by(Order.created_at.desc()).all()
    return [
        {
            "id": o.id,
            "order_number": o.order_number,
            "status": o.status,
            "carrier": o.carrier,
            "tracking_number": o.tracking_number,
            "estimated_delivery": o.estimated_delivery,
            "items_summary": o.items_summary,
            "shipping_address": o.shipping_address,
            "created_at": o.created_at
        } for o in orders
    ]


@router.get("/conversations", response_model=List[ConversationOut])
def list_conversations(
    db: Session = Depends(get_db),
    current_user: Optional[User] = Depends(get_optional_current_user)
):
    """Fetch active and past conversations for the Agent/Admin Workspace."""
    if current_user and current_user.role == "customer":
        # Strictly isolate customer to their own conversations if calling this endpoint
        customer_id = current_user.customer_profile.id if current_user.customer_profile else -1
        conversations = db.query(Conversation).filter(
            Conversation.customer_id == customer_id
        ).order_by(Conversation.created_at.desc()).all()
        return [_format_conversation(conv, db) for conv in conversations]

    conversations = db.query(Conversation).order_by(Conversation.created_at.desc()).all()
    return [_format_conversation(conv, db) for conv in conversations]


@router.get("/conversation/{conversation_id}", response_model=ConversationOut)
def get_conversation(
    conversation_id: int,
    db: Session = Depends(get_db),
    current_user: Optional[User] = Depends(get_optional_current_user)
):
    """Fetch single conversation details with data isolation check."""
    conv = db.query(Conversation).filter(Conversation.id == conversation_id).first()
    if not conv:
        raise HTTPException(status_code=404, detail="Conversation not found")

    # Data isolation: If caller is a customer, verify conversation ownership
    if current_user and current_user.role == "customer":
        if not current_user.customer_profile or conv.customer_id != current_user.customer_profile.id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Forbidden: You do not have permission to access another customer's conversation."
            )

    return _format_conversation(conv, db)


@router.get("/customer/{customer_id}", response_model=CustomerOut)
def get_customer(
    customer_id: int,
    db: Session = Depends(get_db),
    current_user: Optional[User] = Depends(get_optional_current_user)
):
    """Fetch specific customer profile with memory history and isolation check."""
    if current_user and current_user.role == "customer":
        if not current_user.customer_profile or current_user.customer_profile.id != customer_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Forbidden: You cannot access another customer's profile."
            )

    cust = db.query(Customer).filter(Customer.id == customer_id).first()
    if not cust:
        raise HTTPException(status_code=404, detail="Customer not found")
    profile = get_customer_profile_summary(db, cust.id)
    memories_out = [
        {
            "id": m.id,
            "issue_summary": m.issue_summary,
            "resolution_summary": m.resolution_summary,
            "sentiment_label": m.sentiment_label,
            "stress_score": m.stress_score or 0,
            "agent_name": m.agent_name or "Sarah Jenkins",
            "key_notes": m.key_notes,
            "created_at": m.created_at
        } for m in (cust.memories or [])
    ]
    return {
        "id": cust.id,
        "name": profile["name"],
        "email": profile["email"],
        "phone": cust.phone,
        "tier": cust.tier,
        "badge": profile.get("badge", "Returning Customer"),
        "total_contacts": cust.total_contacts,
        "unresolved_issues": cust.unresolved_issues,
        "current_stress_score": cust.current_stress_score,
        "predicted_style": cust.predicted_style,
        "memories": memories_out
    }


@router.get("/customer/{customer_id}/memory")
def get_customer_memory(
    customer_id: int,
    db: Session = Depends(get_db),
    current_user: Optional[User] = Depends(get_optional_current_user)
):
    """Fetch memory summary for customer."""
    if current_user and current_user.role == "customer":
        if not current_user.customer_profile or current_user.customer_profile.id != customer_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Forbidden: You cannot access another customer's memory."
            )
    return get_customer_memory_summary(db, customer_id)


@router.get("/customer/{customer_id}/timeline")
def get_customer_timeline_endpoint(
    customer_id: int,
    db: Session = Depends(get_db),
    current_user: Optional[User] = Depends(get_optional_current_user)
):
    """Fetch chronological touchpoint timeline for customer."""
    if current_user and current_user.role == "customer":
        if not current_user.customer_profile or current_user.customer_profile.id != customer_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Forbidden: You cannot access another customer's timeline."
            )
    return get_customer_timeline(db, customer_id)


@router.get("/customer/{customer_id}/context")
def get_customer_context_endpoint(
    customer_id: int,
    conversation_id: Optional[int] = None,
    db: Session = Depends(get_db),
    current_user: Optional[User] = Depends(get_optional_current_user)
):
    """Fetch compiled customer context for AI coaching or transfer."""
    if current_user and current_user.role == "customer":
        if not current_user.customer_profile or current_user.customer_profile.id != customer_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Forbidden: You cannot access another customer's context."
            )
    if not conversation_id:
        conv = db.query(Conversation).filter(Conversation.customer_id == customer_id).order_by(Conversation.created_at.desc()).first()
        if not conv:
            raise HTTPException(status_code=404, detail="No conversation found for customer")
        conversation_id = conv.id
    return build_full_customer_context(db, conversation_id)


@router.post("/conversation/{conversation_id}/transfer", response_model=ConversationOut)
def transfer_conversation(
    conversation_id: int,
    req: TransferRequest,
    db: Session = Depends(get_db),
    current_user: Optional[User] = Depends(get_optional_current_user)
):
    """
    Transfers conversation to another agent with automatically generated Context Summary.
    """
    if current_user and current_user.role == "customer":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Forbidden: Customers cannot transfer conversations."
        )
    conv = db.query(Conversation).filter(Conversation.id == conversation_id).first()
    if not conv:
        raise HTTPException(status_code=404, detail="Conversation not found")

    new_agent = db.query(Agent).filter(Agent.id == req.new_agent_id).first()
    if not new_agent:
        raise HTTPException(status_code=404, detail="Target Agent not found")

    # Set previous agent & transfer flags
    conv.previous_agent_id = conv.agent_id or 1
    conv.agent_id = new_agent.id
    conv.is_transferred = True

    # Compile Context Summary for Receiving Agent
    full_ctx = build_full_customer_context(db, conversation_id)
    transfer_summary = {
        "transferred_at": full_ctx["current_analysis"],
        "reason": req.reason,
        "from_agent": conv.previous_agent.user.name if conv.previous_agent else "Sarah Jenkins",
        "to_agent": new_agent.user.name,
        "customer_name": full_ctx["customer"]["name"],
        "current_issue": full_ctx["current_message"],
        "repeated_issue_status": full_ctx["repeated_issue"]["issue_type"],
        "current_stress": full_ctx["stress_info"]["score"],
        "communication_style": full_ctx["style_info"]["style"],
        "recommended_next_action": full_ctx["repeated_issue"].get("reason") or "Provide concrete status update."
    }
    conv.transfer_context = transfer_summary
    db.commit()
    db.refresh(conv)

    return _format_conversation(conv, db)


@router.post("/message", response_model=ProcessMessageResponse)
def process_message(
    req: ProcessMessageRequest,
    db: Session = Depends(get_db),
    current_user: Optional[User] = Depends(get_optional_current_user)
):
    """
    Main real-time customer message pipeline:
    Customer Message -> Context Build -> History-Aware AI Coaching -> Response
    """
    conv = db.query(Conversation).filter(Conversation.id == req.conversation_id).first()
    if not conv:
        raise HTTPException(status_code=404, detail="Conversation not found")

    # Data isolation: If caller is a customer, verify conversation ownership
    if current_user and current_user.role == "customer":
        if not current_user.customer_profile or conv.customer_id != current_user.customer_profile.id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Forbidden: You cannot send messages to another customer's conversation."
            )

    # Determine language
    selected_lang = (
        req.language_code
        or getattr(conv, "language_code", None)
        or detect_text_language(req.content)
        or "en"
    ).lower().split("-")[0].split("_")[0]
    if selected_lang not in ["en", "hi", "ta", "kn"]:
        selected_lang = "en"

    selected_locale = req.locale or get_locale(selected_lang)
    conv.language_code = selected_lang
    conv.locale = selected_locale

    english_translation = None
    if selected_lang != "en":
        english_translation = translate_to_english(req.content, source_language=selected_lang)

    # 1. Save Customer Message
    db_msg = Message(
        conversation_id=req.conversation_id,
        sender_type=req.sender_type,
        content=req.content,
        language_code=selected_lang,
        original_content=req.content,
        translated_content=english_translation
    )
    db.add(db_msg)
    db.commit()
    db.refresh(db_msg)

    # 2. Build Unified Customer Context (NLP + Memory + Repeated Issue + Timeline)
    context_obj = build_full_customer_context(db, req.conversation_id, req.content)

    nlp_res = context_obj["current_analysis"]
    stress_res = context_obj["stress_info"]
    style_res = context_obj["style_info"]
    mem_summary = context_obj["memory_summary"]

    # Update Customer state
    cust = conv.customer
    cust.current_stress_score = stress_res["score"]
    cust.predicted_style = style_res["style"]
    conv.priority = context_obj["smart_routing"]["priority"]

    # 3. Generate History-Aware AI Coaching
    coaching_res = generate_coaching_recommendation(
        customer_message=req.content,
        nlp_analysis=nlp_res,
        stress_info=stress_res,
        style_info=style_res,
        memory_summary=mem_summary,
        context_obj=context_obj
    )

    # 4. Save AI Analysis Entity
    ai_analysis_db = AIAnalysis(
        message_id=db_msg.id,
        intent=nlp_res["intent"],
        sentiment=nlp_res["sentiment"],
        sentiment_score=nlp_res["sentiment_score"],
        emotion=nlp_res["emotion"],
        topic=nlp_res["topic"],
        language=nlp_res["language"],
        stress_score=stress_res["score"],
        communication_style=style_res["style"],
        coaching_payload=coaching_res
    )
    db.add(ai_analysis_db)
    db.commit()
    db.refresh(ai_analysis_db)

    # 5. Process Message through Hybrid Customer Response Engine
    engine_result = process_customer_message(
        db=db,
        conversation=conv,
        customer_text=req.content,
        context_obj=context_obj,
        selected_language=selected_lang
    )

    handling_mode = engine_result["handling_mode"]
    requires_human = engine_result["requires_human"]
    auto_resolved = engine_result["auto_resolved"]
    response_text = engine_result["response_text"]
    intent = engine_result["intent"]
    confidence = engine_result["confidence"]
    reason = engine_result["reason"]

    # 6. Always Persist Assistant Response in Conversation
    assistant_msg = Message(
        conversation_id=conv.id,
        sender_type="assistant",
        content=response_text,
        language_code=selected_lang,
        original_content=response_text,
        translated_content=translate_to_english(response_text, source_language=selected_lang) if selected_lang != "en" else None
    )
    db.add(assistant_msg)

    # 7. Update Conversation Status & Priority
    if auto_resolved:
        conv.status = "resolved"
    else:
        conv.status = "active"
        if requires_human and conv.priority == "normal":
            conv.priority = context_obj["smart_routing"].get("priority", "HIGH")

    db.commit()
    db.refresh(assistant_msg)
    db.refresh(cust)
    db.refresh(conv)

    return {
        "message_id": db_msg.id,
        "handling_mode": handling_mode,
        "requires_human": requires_human,
        "auto_resolved": auto_resolved,
        "response_message": assistant_msg,
        "response_text": response_text,
        "ai_response": response_text,
        "intent": intent,
        "confidence": confidence,
        "status": conv.status,
        "reason": reason,
        "language_code": selected_lang,
        "locale": selected_locale,
        "original_text": req.content,

        # Backward-compatible fields
        "message": db_msg,
        "ai_analysis": ai_analysis_db,
        "coaching": coaching_res,
        "context": context_obj,
        "coaching_suggestion": coaching_res.get("suggested_response"),
        "routing": context_obj["smart_routing"].get("recommended_department", "Order Fulfillment & Logistics"),
        "priority": conv.priority,
        "sentiment": nlp_res["sentiment"],
        "stress_score": stress_res["score"],
        "communication_style": style_res["style"]
    }


@router.post("/agent-reply", response_model=MessageOut)
def send_agent_reply(
    req: AgentReplyRequest,
    db: Session = Depends(get_db),
    current_user: Optional[User] = Depends(get_optional_current_user)
):
    """
    Human agent submits their final response.
    If the customer's selected language is non-English, automatically translates the agent's
    English response into the customer's selected language while preserving original English for the agent.
    Logs feedback on whether AI suggestion was accepted, edited, or written manually.
    """
    if current_user and current_user.role == "customer":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Forbidden: Customers are not permitted to submit agent replies."
        )

    conv = db.query(Conversation).filter(Conversation.id == req.conversation_id).first()
    if not conv:
        raise HTTPException(status_code=404, detail="Conversation not found")

    customer_lang = getattr(conv, "language_code", "en") or "en"
    customer_facing_content = req.content
    if customer_lang != "en":
        customer_facing_content = translate_from_english(req.content, target_language=customer_lang)

    # 1. Save Human Agent Message (content is customer-facing, original_content is agent input)
    agent_msg = Message(
        conversation_id=req.conversation_id,
        sender_type="agent",
        content=customer_facing_content,
        language_code=customer_lang,
        original_content=req.content,
        translated_content=customer_facing_content
    )
    db.add(agent_msg)
    db.commit()
    db.refresh(agent_msg)

    # 2. Log Coaching Feedback
    last_cust_msg = db.query(Message).filter(
        Message.conversation_id == conv.id,
        Message.sender_type == "customer"
    ).order_by(Message.created_at.desc()).first()

    if last_cust_msg:
        feedback = CoachingFeedback(
            conversation_id=conv.id,
            message_id=last_cust_msg.id,
            agent_action=req.action_type,
            suggested_response=req.suggested_response,
            actual_response=req.content
        )
        db.add(feedback)
        db.commit()

    return agent_msg


class TranslateRequest(BaseModel):
    text: str
    source_language: Optional[str] = "en"
    target_language: str


class TranslateResponse(BaseModel):
    original_text: str
    translated_text: str
    source_language: str
    target_language: str


@router.post("/translate", response_model=TranslateResponse)
def translate_text_endpoint(req: TranslateRequest):
    """Translates text between supported languages (English, Hindi, Tamil, Kannada)."""
    res = translate_text(req.text, req.source_language, req.target_language)
    return {
        "original_text": req.text,
        "translated_text": res,
        "source_language": req.source_language or "en",
        "target_language": req.target_language
    }


@router.post("/routing/analyze")
def analyze_routing_endpoint(req: ProcessMessageRequest, db: Session = Depends(get_db)):
    """Analyze text or customer context to evaluate smart routing recommendations."""
    full_ctx = build_full_customer_context(db, req.conversation_id, req.content)
    return full_ctx["smart_routing"]


@router.get("/escalation/{conversation_id}")
def get_escalation_endpoint(conversation_id: int, db: Session = Depends(get_db)):
    """Evaluate intelligent escalation status for a conversation."""
    full_ctx = build_full_customer_context(db, conversation_id)
    return full_ctx["escalation_info"]


@router.get("/sla/{conversation_id}")
def get_sla_endpoint(conversation_id: int, db: Session = Depends(get_db)):
    """Calculate real-time dynamic SLA metrics for a conversation."""
    full_ctx = build_full_customer_context(db, conversation_id)
    return full_ctx["sla_info"]
