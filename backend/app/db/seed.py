import datetime
from sqlalchemy.orm import Session
from app.core.database import SessionLocal, engine, Base
from app.models.domain import (
    User, Department, Agent, Customer, Conversation, Message,
    CustomerMemory, AIAnalysis, Order
)
from app.services.context_service import build_full_customer_context
from app.ai.llm_coach import generate_coaching_recommendation


from app.core.security import hash_password


def seed_database(reset: bool = False):
    print("[*] Initializing Database Schema & Seeding Data...")
    if reset:
        Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)
    db: Session = SessionLocal()

    try:
        # Check if already seeded with new columns and hashed passwords
        if not reset and db.query(User).first():
            try:
                test_conv = db.query(Conversation).first()
                test_order = db.query(Order).first()
                test_user = db.query(User).first()
                if test_conv and hasattr(test_conv, 'previous_agent_id') and test_order and test_user and test_user.hashed_password:
                    print("[+] Database schema up to date with seed data.")
                    return
            except Exception:
                db.rollback()
                print("[*] Schema outdated. Re-creating tables...")
                Base.metadata.drop_all(bind=engine)
                Base.metadata.create_all(bind=engine)

        # Clear existing records if schema changed
        try:
            db.query(Order).delete()
        except Exception:
            pass
        db.query(AIAnalysis).delete()
        db.query(Message).delete()
        db.query(Conversation).delete()
        db.query(CustomerMemory).delete()
        db.query(Customer).delete()
        db.query(Agent).delete()
        db.query(User).delete()
        db.query(Department).delete()
        db.commit()

        # 1. Create Departments
        d_orders = Department(name="Order Fulfillment & Logistics", code="ORDERS", description="Handles order status, shipping delays, and logistics.")
        d_billing = Department(name="Billing & Payments", code="BILLING", description="Handles invoicing, refunds, and payment inquiries.")
        d_tech = Department(name="Technical Support", code="TECH", description="Handles app errors, account access, and bugs.")
        db.add_all([d_orders, d_billing, d_tech])
        db.commit()

        # 2. Create Users (Agents & Customers & Admin) with hashed passwords
        agent_pwd = hash_password("Agent123!")
        cust_pwd = hash_password("Customer123!")
        admin_pwd = hash_password("Admin123!")

        u_agent1 = User(name="Sarah Jenkins", email="sarah.j@support.com", role="agent", hashed_password=agent_pwd)
        u_agent2 = User(name="Michael Brown", email="michael.b@support.com", role="agent", hashed_password=agent_pwd)
        u_cust1 = User(name="Alex Johnson", email="alex.j@example.com", role="customer", hashed_password=cust_pwd)
        u_cust2 = User(name="Priya Kumar", email="priya.k@example.com", role="customer", hashed_password=cust_pwd)
        u_cust3 = User(name="John Smith", email="john.s@example.com", role="customer", hashed_password=cust_pwd)
        u_admin = User(name="System Administrator", email="admin@company.com", role="admin", hashed_password=admin_pwd)
        db.add_all([u_agent1, u_agent2, u_cust1, u_cust2, u_cust3, u_admin])
        db.commit()

        # 3. Create Agent Profiles
        ag1 = Agent(user_id=u_agent1.id, department_id=d_orders.id, status="available", skill_level="senior")
        ag2 = Agent(user_id=u_agent2.id, department_id=d_orders.id, status="available", skill_level="senior")
        db.add_all([ag1, ag2])
        db.commit()

        # 4. Create Customer Profiles
        cust1 = Customer(
            user_id=u_cust1.id,
            phone="+1 (555) 234-5678",
            tier="VIP",
            total_contacts=3,
            unresolved_issues=1,
            current_stress_score=85,
            predicted_style="Impatient / Direct"
        )
        cust2 = Customer(
            user_id=u_cust2.id,
            phone="+1 (555) 876-5432",
            tier="Standard",
            total_contacts=1,
            unresolved_issues=0,
            current_stress_score=15,
            predicted_style="Calm"
        )
        cust3 = Customer(
            user_id=u_cust3.id,
            phone="+1 (555) 345-6789",
            tier="Standard",
            total_contacts=2,
            unresolved_issues=1,
            current_stress_score=78,
            predicted_style="Direct"
        )
        db.add_all([cust1, cust2, cust3])
        db.commit()

        # Seed Orders for Customer Order Status Lookup
        ord1 = Order(
            order_number="98213",
            customer_id=cust1.id,
            status="In Transit",
            carrier="FedEx",
            tracking_number="FDX-982130421",
            estimated_delivery="tomorrow by 5:00 PM",
            items_summary="Ergonomic Desk Chair (Black)",
            shipping_address="742 Evergreen Terrace, Springfield"
        )
        ord2 = Order(
            order_number="ORD-98213",
            customer_id=cust1.id,
            status="In Transit",
            carrier="FedEx",
            tracking_number="FDX-982130421",
            estimated_delivery="tomorrow by 5:00 PM",
            items_summary="Ergonomic Desk Chair (Black)",
            shipping_address="742 Evergreen Terrace, Springfield"
        )
        ord3 = Order(
            order_number="55120",
            customer_id=cust2.id,
            status="Delivered",
            carrier="UPS",
            tracking_number="1Z999AA10123456784",
            estimated_delivery="Delivered on Sept 10",
            items_summary="Wireless Mechanical Keyboard",
            shipping_address="100 Main Street, Seattle, WA"
        )
        db.add_all([ord1, ord2, ord3])
        db.commit()

        # 5. Create Chronological Customer Memories for Alex Johnson (Timeline)
        now = datetime.datetime.utcnow()
        mem1 = CustomerMemory(
            customer_id=cust1.id,
            issue_summary="Order #ORD-98213 delayed by 2 days",
            resolution_summary="Order status checked in tracking database. Issued $15 courtesy credit.",
            sentiment_label="Negative",
            stress_score=65,
            agent_name="Sarah Jenkins",
            key_notes="Customer inquired calmly about minor shipping delay.",
            created_at=now - datetime.timedelta(days=7)
        )
        mem2 = CustomerMemory(
            customer_id=cust1.id,
            issue_summary="Order #ORD-98213 still not delivered after 5 days",
            resolution_summary="Escalated ticket to Senior Logistics Operations team.",
            sentiment_label="Negative",
            stress_score=80,
            agent_name="Sarah Jenkins",
            key_notes="Customer expressed impatience. Escalation priority raised.",
            created_at=now - datetime.timedelta(days=3)
        )
        db.add_all([mem1, mem2])
        db.commit()

        # 6. Create Active Conversation for Alex Johnson (Interaction 3 - Current Demo Message)
        conv1 = Conversation(
            customer_id=cust1.id,
            agent_id=ag1.id,
            previous_agent_id=ag1.id,
            department_id=d_orders.id,
            status="active",
            priority="URGENT",
            created_at=now
        )
        db.add(conv1)
        db.commit()

        # Demo Message for Alex Johnson
        demo_text = "I've been waiting for my order for a week. This is very frustrating."
        msg1 = Message(conversation_id=conv1.id, sender_type="customer", content=demo_text, created_at=now)
        db.add(msg1)
        db.commit()

        # 7. Run Context Service & History-Aware AI Coaching for Alex Johnson
        context_payload = build_full_customer_context(db, conv1.id, demo_text)
        coaching_res = generate_coaching_recommendation(
            customer_message=demo_text,
            nlp_analysis=context_payload["current_analysis"],
            stress_info=context_payload["stress_info"],
            style_info=context_payload["style_info"],
            memory_summary=context_payload["memory_summary"],
            context_obj=context_payload
        )

        ai_an1 = AIAnalysis(
            message_id=msg1.id,
            intent=context_payload["current_analysis"]["intent"],
            sentiment=context_payload["current_analysis"]["sentiment"],
            sentiment_score=context_payload["current_analysis"]["sentiment_score"],
            emotion=context_payload["current_analysis"]["emotion"],
            topic=context_payload["current_analysis"]["topic"],
            language=context_payload["current_analysis"]["language"],
            stress_score=context_payload["stress_info"]["score"],
            communication_style=context_payload["style_info"]["style"],
            coaching_payload=coaching_res
        )
        db.add(ai_an1)
        db.commit()

        # 8. Create Conversation for Priya Kumar (AI Resolved Query)
        conv2 = Conversation(
            customer_id=cust2.id,
            agent_id=ag1.id,
            department_id=d_orders.id,
            status="resolved",
            priority="NORMAL",
            created_at=now - datetime.timedelta(minutes=15)
        )
        db.add(conv2)
        db.commit()
        msg2_cust = Message(
            conversation_id=conv2.id,
            sender_type="customer",
            content="What are your delivery times?",
            created_at=now - datetime.timedelta(minutes=15)
        )
        msg2_ai = Message(
            conversation_id=conv2.id,
            sender_type="assistant",
            content="Standard delivery usually takes 3–5 business days. Express shipping is delivered within 1–2 business days. If you share your order number, I can check the exact status of your specific order.",
            created_at=now - datetime.timedelta(minutes=14)
        )
        db.add_all([msg2_cust, msg2_ai])
        db.commit()

        # 9. Create Conversation for John Smith (Needs Agent / High Priority Billing)
        conv3 = Conversation(
            customer_id=cust3.id,
            agent_id=ag1.id,
            department_id=d_billing.id,
            status="active",
            priority="HIGH",
            created_at=now - datetime.timedelta(minutes=30)
        )
        db.add(conv3)
        db.commit()
        msg3_cust = Message(
            conversation_id=conv3.id,
            sender_type="customer",
            content="I've been charged twice and I need a refund immediately.",
            created_at=now - datetime.timedelta(minutes=30)
        )
        db.add(msg3_cust)
        db.commit()

        # 8. Seed Historical Coaching Feedback & Customer CSAT/Outcome Feedback for Phase 5 Analytics
        from app.models.domain import CoachingFeedback, ConversationFeedback
        db.query(CoachingFeedback).delete()
        db.query(ConversationFeedback).delete()
        db.commit()

        # Seed Coaching Feedback
        cf1 = CoachingFeedback(conversation_id=conv1.id, message_id=msg1.id, agent_action="accepted", suggested_response="Checking status now...", actual_response="Checking status now...")
        cf2 = CoachingFeedback(conversation_id=conv1.id, message_id=msg1.id, agent_action="edited", suggested_response="Checking logistics delay...", actual_response="I've escalated your order #ORD-98213 directly to logistics.")
        cf3 = CoachingFeedback(conversation_id=conv1.id, message_id=msg1.id, agent_action="accepted", suggested_response="Courtesy credit applied.", actual_response="Courtesy credit applied.")
        cf4 = CoachingFeedback(conversation_id=conv1.id, message_id=msg1.id, agent_action="edited", suggested_response="Apologies for delay.", actual_response="Apologies for delay, tracking says delivery tomorrow by 5pm.")
        cf5 = CoachingFeedback(conversation_id=conv1.id, message_id=msg1.id, agent_action="ignored", suggested_response="Please verify address.", actual_response="Checking database.")
        cf6 = CoachingFeedback(conversation_id=conv1.id, message_id=msg1.id, agent_action="custom", suggested_response="Draft", actual_response="Custom agent reply.")
        cf7 = CoachingFeedback(conversation_id=conv1.id, message_id=msg1.id, agent_action="accepted", suggested_response="Order status updated.", actual_response="Order status updated.")
        cf8 = CoachingFeedback(conversation_id=conv1.id, message_id=msg1.id, agent_action="accepted", suggested_response="Refund initiated.", actual_response="Refund initiated.")
        db.add_all([cf1, cf2, cf3, cf4, cf5, cf6, cf7, cf8])
        db.commit()

        # Seed Conversation Customer Feedback
        csat1 = ConversationFeedback(conversation_id=conv1.id, customer_id=cust1.id, csat_rating=5, comments="Agent resolved my issue quickly.", outcome="Resolved")
        csat2 = ConversationFeedback(conversation_id=conv1.id, customer_id=cust1.id, csat_rating=4, comments="Good explanation of shipping delay.", outcome="Resolved")
        csat3 = ConversationFeedback(conversation_id=conv1.id, customer_id=cust2.id, csat_rating=5, comments="Very helpful and polite.", outcome="Resolved")
        csat4 = ConversationFeedback(conversation_id=conv1.id, customer_id=cust1.id, csat_rating=2, comments="Had to contact support twice.", outcome="Partially Resolved")
        csat5 = ConversationFeedback(conversation_id=conv1.id, customer_id=cust2.id, csat_rating=4, comments="Quick response.", outcome="Resolved")
        db.add_all([csat1, csat2, csat3, csat4, csat5])
        db.commit()

        print("[+] Database successfully seeded with customer support workflows, historical feedback, and learning data!")

    except Exception as e:
        db.rollback()
        print(f"[-] Error seeding database: {e}")
    finally:
        db.close()


if __name__ == "__main__":
    seed_database(reset=True)
