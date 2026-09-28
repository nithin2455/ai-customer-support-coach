from typing import List, Optional, Any, Dict
from datetime import datetime
from pydantic import BaseModel, ConfigDict, Field, field_serializer


class MessageBase(BaseModel):
    content: str
    sender_type: str = "customer"  # customer, agent, system
    language_code: Optional[str] = "en"
    original_content: Optional[str] = None
    translated_content: Optional[str] = None


class MessageCreate(MessageBase):
    conversation_id: int


class AIAnalysisOut(BaseModel):
    intent: str
    sentiment: str
    sentiment_score: float
    emotion: str
    topic: str
    language: str
    stress_score: int
    communication_style: str
    coaching_payload: Optional[Dict[str, Any]] = None

    model_config = ConfigDict(from_attributes=True)


class MessageOut(MessageBase):
    id: int
    conversation_id: int
    created_at: datetime
    ai_analysis: Optional[AIAnalysisOut] = None

    model_config = ConfigDict(from_attributes=True)

    @field_serializer('created_at', when_used='json')
    def serialize_created_at(self, dt: datetime, _info):
        if dt.tzinfo is None:
            return dt.isoformat() + "Z"
        return dt.isoformat()


class CustomerMemoryOut(BaseModel):
    id: int
    issue_summary: str
    resolution_summary: Optional[str] = None
    sentiment_label: Optional[str] = None
    stress_score: Optional[int] = 0
    agent_name: Optional[str] = None
    key_notes: Optional[str] = None
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)

    @field_serializer('created_at', when_used='json')
    def serialize_created_at(self, dt: datetime, _info):
        if dt.tzinfo is None:
            return dt.isoformat() + "Z"
        return dt.isoformat()


class CustomerOut(BaseModel):
    id: int
    name: str
    email: str
    phone: Optional[str] = None
    tier: str
    badge: Optional[str] = "Returning Customer"
    total_contacts: int
    unresolved_issues: int
    current_stress_score: int
    predicted_style: str
    memories: List[CustomerMemoryOut] = []

    model_config = ConfigDict(from_attributes=True)


class AgentOut(BaseModel):
    id: int
    name: str
    email: str
    department_name: str
    status: str
    skill_level: str

    model_config = ConfigDict(from_attributes=True)


class CoachingStrategy(BaseModel):
    tone: str = "Empathetic and direct"
    response_length: str = "Concise"
    priority: str = "Concrete status update"
    empathy_level: str = "High"
    avoid: str = "Repeating previous troubleshooting steps"
    explanation: str = "Customer stress is high and issue has been reported previously."


class CoachingPayload(BaseModel):
    warning: Optional[str] = None
    is_repeated_issue: bool = False
    issue_type: Optional[str] = "New Issue"
    coaching_strategy: Optional[CoachingStrategy] = None
    coaching_reason: Optional[str] = None
    recommended_actions: List[str]
    empathy_guidance: str
    resolution_guidance: str
    suggested_response: str
    escalation_required: bool = False
    escalation_recommendation: Optional[str] = None
    customer_history_snippet: Optional[str] = None
    agent_continuity: Optional[Dict[str, Any]] = None


class ConversationOut(BaseModel):
    id: int
    customer: CustomerOut
    agent: Optional[AgentOut] = None
    previous_agent: Optional[AgentOut] = None
    department_name: str
    status: str
    priority: str
    is_transferred: bool = False
    transfer_context: Optional[Dict[str, Any]] = None
    language_code: Optional[str] = "en"
    locale: Optional[str] = "en-IN"
    created_at: datetime
    messages: List[MessageOut] = []
    latest_coaching: Optional[CoachingPayload] = None
    full_context: Optional[Dict[str, Any]] = None

    model_config = ConfigDict(from_attributes=True)

    @field_serializer('created_at', when_used='json')
    def serialize_created_at(self, dt: datetime, _info):
        if dt.tzinfo is None:
            return dt.isoformat() + "Z"
        return dt.isoformat()


class ProcessMessageRequest(BaseModel):
    conversation_id: int
    content: str
    sender_type: str = "customer"
    language_code: Optional[str] = None
    locale: Optional[str] = None


class ProcessMessageResponse(BaseModel):
    message_id: Optional[int] = None
    handling_mode: str = "HUMAN_HANDOFF"  # "RULE_RESPONSE" | "LLM_RESPONSE" | "HUMAN_HANDOFF"
    requires_human: bool = True
    auto_resolved: bool = False
    response_message: Optional[MessageOut] = None
    response_text: Optional[str] = None
    ai_response: Optional[str] = None
    intent: Optional[str] = None
    confidence: Optional[float] = 1.0
    status: Optional[str] = "active"
    reason: Optional[str] = None
    language_code: Optional[str] = "en"
    locale: Optional[str] = "en-IN"
    original_text: Optional[str] = None

    # Backward-compatible fields for Phase 1–7
    message: Optional[MessageOut] = None
    ai_analysis: Optional[AIAnalysisOut] = None
    coaching: Optional[CoachingPayload] = None
    context: Optional[Dict[str, Any]] = None
    coaching_suggestion: Optional[str] = None
    routing: Optional[str] = None
    priority: Optional[str] = None
    sentiment: Optional[str] = None
    stress_score: Optional[int] = 0
    communication_style: Optional[str] = "Calm"


class AgentReplyRequest(BaseModel):
    conversation_id: int
    content: str
    action_type: str = "custom"  # "accepted", "edited", "custom"
    suggested_response: Optional[str] = None
    language_code: Optional[str] = None


class TransferRequest(BaseModel):
    new_agent_id: int
    reason: Optional[str] = "Agent workload rebalancing / specialization transfer"


class FeedbackCreate(BaseModel):
    conversation_id: int
    message_id: int
    agent_action: str  # accepted, edited, ignored
    suggested_response: Optional[str] = None
    actual_response: Optional[str] = None


class CSATFeedbackCreate(BaseModel):
    conversation_id: int
    csat_rating: int  # 1-5
    comments: Optional[str] = None
    outcome: Optional[str] = "Resolved"  # Resolved, Partially Resolved, Unresolved, Escalated


class CoachingEffectivenessMetrics(BaseModel):
    total_suggestions: int
    accepted_count: int
    edited_count: int
    ignored_count: int
    custom_count: int
    acceptance_rate: float
    edit_rate: float
    rejection_rate: float
    custom_rate: float


class CustomerExperienceMetrics(BaseModel):
    avg_csat_rating: float
    resolution_rate: float
    escalation_rate: float
    avg_customer_stress: float
    repeated_issue_resolution_rate: float


class LearningInsightOut(BaseModel):
    id: str
    title: str
    pattern: str
    insight: str
    recommendation: str
    confidence_score: float
    affected_category: str

