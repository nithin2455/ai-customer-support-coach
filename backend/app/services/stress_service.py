import re
from typing import Dict, Any


def calculate_stress_score(
    text: str,
    sentiment: str,
    emotion: str,
    total_contacts: int = 1,
    unresolved_issues: int = 0
) -> Dict[str, Any]:
    """
    Calculates a 0-100 customer stress score based on:
    - Sentiment severity
    - Emotion classification
    - Contact history & unresolved tickets
    - High-stress keywords & text markers
    """
    score = 0
    text_lower = text.lower()

    # 1. Sentiment Weight (Max 35)
    if sentiment.lower() == "negative":
        score += 35
    elif sentiment.lower() == "neutral":
        score += 10
    else:
        score += 0

    # 2. Emotion Weight (Max 25)
    if emotion.lower() in ["anger", "angry"]:
        score += 25
    elif emotion.lower() in ["frustration", "frustrated"]:
        score += 20
    elif emotion.lower() in ["confusion", "confused"]:
        score += 10

    # 3. Keyword / Trigger Phrase Detection (Max 20)
    high_stress_keywords = [
        "waiting for a week", "waiting for weeks", "unacceptable",
        "ridiculous", "frustrating", "terrible", "worst", "cancel",
        "demand", "refund", "supervisor", "manager", "lawyer", "legal",
        "scam", "waste of time", "nobody helped"
    ]
    matched_triggers = [kw for kw in high_stress_keywords if kw in text_lower]
    score += min(len(matched_triggers) * 8, 20)

    # 4. History Factors (Max 15)
    score += min(unresolved_issues * 6, 12)
    if total_contacts > 2:
        score += 5

    # 5. Text Caps & Punctuation (Max 5)
    if "!" in text or text.isupper():
        score += 5

    # Cap score to 0-100
    final_score = min(max(score, 0), 100)

    # Category label
    if final_score >= 70:
        level = "HIGH"
    elif final_score >= 40:
        level = "MEDIUM"
    else:
        level = "LOW"

    return {
        "score": final_score,
        "level": level,
        "matched_triggers": matched_triggers
    }
