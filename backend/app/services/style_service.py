from typing import Dict, Any


def predict_communication_style(text: str, stress_score: int) -> Dict[str, Any]:
    """
    Estimates customer communication style (Direct, Impatient, Detailed, Brief, Calm)
    from text patterns and stress context. Returns guidance for the human agent.
    """
    words = text.split()
    word_count = len(words)
    text_lower = text.lower()

    # Heuristics
    is_short = word_count < 10
    is_long = word_count > 30
    has_time_urgency = any(w in text_lower for w in ["now", "immediately", "asap", "waiting", "delay", "today", "hour", "week"])
    has_question = "?" in text

    if stress_score >= 65 or (has_time_urgency and is_short):
        style = "Impatient / Direct"
        guidance = "Customer values speed and clarity. Recommend brief, direct answers with immediate action items."
    elif is_long:
        style = "Detailed / Expressive"
        guidance = "Customer provides thorough context. Acknowledge specific details mentioned and provide structured guidance."
    elif is_short:
        style = "Brief / Direct"
        guidance = "Customer is concise. Keep response focused and ask clarifying questions if needed."
    else:
        style = "Calm / Collaborative"
        guidance = "Customer is calm and open. Maintain a warm, helpful tone while providing full resolution details."

    return {
        "style": style,
        "guidance": guidance
    }
