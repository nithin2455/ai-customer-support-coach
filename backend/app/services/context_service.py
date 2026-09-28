from typing import Dict, Any, Optional
from sqlalchemy.orm import Session
from app.models.domain import Conversation, Customer, Message, Agent
from app.services.memory_service import get_customer_profile_summary, get_customer_timeline, get_customer_memory_summary
from app.services.repeated_issue_service import detect_repeated_issue
from app.services.routing_service import evaluate_smart_routing
from app.services.escalation_service import evaluate_intelligent_escalation
from app.services.sla_service import calculate_conversation_sla
from app.services.stress_service import calculate_stress_score
from app.services.style_service import predict_communication_style
from app.ai.nlp_analyzer import analyze_customer_message


def build_full_customer_context(
    db: Session,
    conversation_id: int,
    current_message_text: Optional[str] = None
) -> Dict[str, Any]:
    """
    Reusable Context-Building Service for AI Coaching, Chat Processing, Agent Transfer,
    Routing, SLA Tracking, and Escalation Evaluation.
    Compiles customer memory, interaction timeline, repeated issue status, agent continuity,
    NLP signals, Smart Routing, SLA status, and Intelligent Escalation recommendations.
    """
    conv = db.query(Conversation).filter(Conversation.id == conversation_id).first()
    if not conv:
        raise ValueError(f"Conversation ID {conversation_id} not found")

    customer = conv.customer
    profile = get_customer_profile_summary(db, customer.id)
    timeline = get_customer_timeline(db, customer.id)
    memory_summary = get_customer_memory_summary(db, customer.id)

    # Determine latest customer message text if not provided
    if not current_message_text:
        last_cust_msg = db.query(Message).filter(
            Message.conversation_id == conversation_id,
            Message.sender_type == "customer"
        ).order_by(Message.created_at.desc()).first()
        current_message_text = last_cust_msg.content if last_cust_msg else "Customer opened ticket."

    # 1. NLP Analysis (language-aware)
    nlp_analysis = analyze_customer_message(
        current_message_text,
        language=getattr(conv, "language_code", "en")
    )

    # 2. Stress Score
    stress_info = calculate_stress_score(
        text=current_message_text,
        sentiment=nlp_analysis["sentiment"],
        emotion=nlp_analysis["emotion"],
        total_contacts=customer.total_contacts,
        unresolved_issues=customer.unresolved_issues
    )

    # 3. Communication Style
    style_info = predict_communication_style(current_message_text, stress_info["score"])

    # 4. Repeated Issue Detection
    repeated_issue_info = detect_repeated_issue(
        db=db,
        customer_id=customer.id,
        current_message=current_message_text,
        current_intent=nlp_analysis["intent"]
    )

    # 5. Agent Continuity & Transfer Info
    curr_agent_name = conv.agent.user.name if conv.agent else "Sarah Jenkins"
    prev_agent_name = conv.previous_agent.user.name if conv.previous_agent else profile.get("previous_agent", "Sarah Jenkins")

    if conv.is_transferred and conv.previous_agent_id:
        continuity_status = "Transferred with Full Context"
        continuity_recommendation = f"Conversation transferred from {prev_agent_name} to {curr_agent_name}. Review transfer summary."
    elif prev_agent_name == curr_agent_name:
        continuity_status = "Previous Agent Available & Assigned"
        continuity_recommendation = f"Agent Continuity Maintained ({curr_agent_name})."
    else:
        continuity_status = "Continuity Recommended"
        continuity_recommendation = f"Customer previously worked with {prev_agent_name}."

    agent_continuity = {
        "current_agent_id": conv.agent_id,
        "current_agent_name": curr_agent_name,
        "previous_agent_id": conv.previous_agent_id,
        "previous_agent_name": prev_agent_name,
        "is_transferred": conv.is_transferred,
        "continuity_status": continuity_status,
        "continuity_recommendation": continuity_recommendation,
        "transfer_context": conv.transfer_context
    }

    # 6. Smart Routing Evaluation
    context_builder_obj = {"repeated_issue": repeated_issue_info, "customer": profile}
    routing_info = evaluate_smart_routing(nlp_analysis["intent"], stress_info["score"], current_message_text, context_builder_obj)

    # 7. Dynamic SLA Calculation
    sla_info = calculate_conversation_sla(db, conversation_id, routing_info["priority"])

    # 8. Intelligent Escalation Recommendation
    escalation_info = evaluate_intelligent_escalation(stress_info["score"], current_message_text, context_builder_obj, sla_info)

    return {
        "conversation_id": conversation_id,
        "customer": profile,
        "current_message": current_message_text,
        "current_analysis": nlp_analysis,
        "stress_info": stress_info,
        "style_info": style_info,
        "memory_summary": memory_summary,
        "timeline": timeline,
        "repeated_issue": repeated_issue_info,
        "agent_continuity": agent_continuity,
        "smart_routing": routing_info,
        "sla_info": sla_info,
        "escalation_info": escalation_info
    }
