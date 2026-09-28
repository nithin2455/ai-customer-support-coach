import datetime
from sqlalchemy import Column, Integer, String, Text, DateTime, ForeignKey, Float, Boolean, JSON
from sqlalchemy.orm import relationship
from app.core.database import Base


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    email = Column(String, unique=True, index=True, nullable=False)
    name = Column(String, nullable=False)
    role = Column(String, default="customer")  # customer, agent, admin
    hashed_password = Column(String, nullable=True)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)

    agent_profile = relationship("Agent", back_populates="user", uselist=False)
    customer_profile = relationship("Customer", back_populates="user", uselist=False)


class Department(Base):
    __tablename__ = "departments"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False)
    code = Column(String, unique=True, nullable=False)
    description = Column(Text, nullable=True)

    agents = relationship("Agent", back_populates="department")
    conversations = relationship("Conversation", back_populates="department")


class Agent(Base):
    __tablename__ = "agents"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    department_id = Column(Integer, ForeignKey("departments.id"), nullable=True)
    status = Column(String, default="available")  # available, busy, offline
    skill_level = Column(String, default="senior")  # junior, intermediate, senior

    user = relationship("User", back_populates="agent_profile")
    department = relationship("Department", back_populates="agents")
    conversations = relationship("Conversation", back_populates="agent", foreign_keys="[Conversation.agent_id]")


class Customer(Base):
    __tablename__ = "customers"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    phone = Column(String, nullable=True)
    tier = Column(String, default="Standard")  # VIP, Standard
    total_contacts = Column(Integer, default=1)
    unresolved_issues = Column(Integer, default=0)
    current_stress_score = Column(Integer, default=0)
    predicted_style = Column(String, default="Calm")

    user = relationship("User", back_populates="customer_profile")
    conversations = relationship("Conversation", back_populates="customer")
    memories = relationship("CustomerMemory", back_populates="customer")


class Conversation(Base):
    __tablename__ = "conversations"

    id = Column(Integer, primary_key=True, index=True)
    customer_id = Column(Integer, ForeignKey("customers.id"), nullable=False)
    agent_id = Column(Integer, ForeignKey("agents.id"), nullable=True)
    previous_agent_id = Column(Integer, ForeignKey("agents.id"), nullable=True)
    department_id = Column(Integer, ForeignKey("departments.id"), nullable=True)
    status = Column(String, default="active")  # active, pending, resolved, escalated
    priority = Column(String, default="normal")  # low, normal, high, urgent
    is_transferred = Column(Boolean, default=False)
    transfer_context = Column(JSON, nullable=True)
    language_code = Column(String, default="en")
    locale = Column(String, default="en-IN")
    created_at = Column(DateTime, default=datetime.datetime.utcnow)
    resolved_at = Column(DateTime, nullable=True)

    customer = relationship("Customer", back_populates="conversations")
    agent = relationship("Agent", back_populates="conversations", foreign_keys=[agent_id])
    previous_agent = relationship("Agent", foreign_keys=[previous_agent_id])
    department = relationship("Department", back_populates="conversations")
    messages = relationship("Message", back_populates="conversation", cascade="all, delete-orphan")
    feedbacks = relationship("ConversationFeedback", back_populates="conversation")


class Message(Base):
    __tablename__ = "messages"

    id = Column(Integer, primary_key=True, index=True)
    conversation_id = Column(Integer, ForeignKey("conversations.id"), nullable=False)
    sender_type = Column(String, nullable=False)  # customer, agent, system
    content = Column(Text, nullable=False)
    language_code = Column(String, default="en")
    original_content = Column(Text, nullable=True)
    translated_content = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)

    conversation = relationship("Conversation", back_populates="messages")
    ai_analysis = relationship("AIAnalysis", back_populates="message", uselist=False)


class CustomerMemory(Base):
    __tablename__ = "customer_memory"

    id = Column(Integer, primary_key=True, index=True)
    customer_id = Column(Integer, ForeignKey("customers.id"), nullable=False)
    conversation_id = Column(Integer, ForeignKey("conversations.id"), nullable=True)
    issue_summary = Column(Text, nullable=False)
    resolution_summary = Column(Text, nullable=True)
    sentiment_label = Column(String, nullable=True)
    stress_score = Column(Integer, default=0)
    agent_name = Column(String, nullable=True)
    key_notes = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)

    customer = relationship("Customer", back_populates="memories")


class AIAnalysis(Base):
    __tablename__ = "ai_analysis"

    id = Column(Integer, primary_key=True, index=True)
    message_id = Column(Integer, ForeignKey("messages.id"), nullable=False)
    intent = Column(String, nullable=False)
    sentiment = Column(String, nullable=False)
    sentiment_score = Column(Float, default=0.0)
    emotion = Column(String, nullable=False)
    topic = Column(String, nullable=False)
    language = Column(String, default="English")
    stress_score = Column(Integer, default=0)
    communication_style = Column(String, default="Calm")
    coaching_payload = Column(JSON, nullable=True)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)

    message = relationship("Message", back_populates="ai_analysis")


class CoachingFeedback(Base):
    __tablename__ = "coaching_feedback"

    id = Column(Integer, primary_key=True, index=True)
    conversation_id = Column(Integer, ForeignKey("conversations.id"), nullable=False)
    message_id = Column(Integer, ForeignKey("messages.id"), nullable=False)
    agent_action = Column(String, nullable=False)  # accepted, edited, ignored
    suggested_response = Column(Text, nullable=True)
    actual_response = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)


class ConversationFeedback(Base):
    __tablename__ = "conversation_feedback"

    id = Column(Integer, primary_key=True, index=True)
    conversation_id = Column(Integer, ForeignKey("conversations.id"), nullable=False)
    customer_id = Column(Integer, ForeignKey("customers.id"), nullable=False)
    csat_rating = Column(Integer, nullable=False)  # 1 to 5
    comments = Column(Text, nullable=True)
    outcome = Column(String, default="Resolved")  # Resolved, Partially Resolved, Unresolved, Escalated
    created_at = Column(DateTime, default=datetime.datetime.utcnow)

    conversation = relationship("Conversation", back_populates="feedbacks")


class Order(Base):
    __tablename__ = "orders"

    id = Column(Integer, primary_key=True, index=True)
    order_number = Column(String, unique=True, index=True, nullable=False)
    customer_id = Column(Integer, ForeignKey("customers.id"), nullable=True)
    status = Column(String, default="Shipped")  # Processing, Shipped, In Transit, Delivered, Cancelled
    carrier = Column(String, default="FedEx")
    tracking_number = Column(String, nullable=True)
    estimated_delivery = Column(String, default="Tomorrow by 5:00 PM")
    items_summary = Column(Text, nullable=True)
    shipping_address = Column(String, nullable=True)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)

    customer = relationship("Customer")
