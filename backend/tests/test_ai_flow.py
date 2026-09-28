import pytest
from app.ai.nlp_analyzer import analyze_customer_message
from app.services.stress_service import calculate_stress_score
from app.services.style_service import predict_communication_style
from app.ai.llm_coach import generate_coaching_recommendation


def test_initial_demo_customer_message_analysis():
    demo_message = "I've been waiting for my order for a week. This is very frustrating."

    # 1. NLP Analysis
    nlp_res = analyze_customer_message(demo_message)
    assert nlp_res["sentiment"] == "Negative"
    assert "Order" in nlp_res["intent"]
    assert nlp_res["emotion"] in ["Frustration", "Anger"]

    # 2. Stress Score
    stress_res = calculate_stress_score(
        text=demo_message,
        sentiment=nlp_res["sentiment"],
        emotion=nlp_res["emotion"],
        total_contacts=3,
        unresolved_issues=1
    )
    assert stress_res["score"] >= 70
    assert stress_res["level"] == "HIGH"

    # 3. Communication Style
    style_res = predict_communication_style(demo_message, stress_res["score"])
    assert "Direct" in style_res["style"] or "Impatient" in style_res["style"]

    # 4. LLM Coaching Recommendation
    memory_summary = {"summary_text": "VIP Customer | Previous Issue: Delayed delivery"}
    coaching = generate_coaching_recommendation(
        customer_message=demo_message,
        nlp_analysis=nlp_res,
        stress_info=stress_res,
        style_info=style_res,
        memory_summary=memory_summary
    )

    assert coaching["warning"] is not None
    assert len(coaching["recommended_actions"]) > 0
    assert "frustrat" in coaching["suggested_response"].lower() or "sorry" in coaching["suggested_response"].lower()
