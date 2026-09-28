import logging
from typing import Dict, Any, Optional
from app.core.config import settings

logger = logging.getLogger("nlp_analyzer")

# Global pipeline placeholders
sentiment_pipe = None
classifier_pipe = None

if settings.USE_HF_LOCAL_MODELS:
    try:
        from transformers import pipeline
        logger.info("Initializing Hugging Face transformers pipelines...")
        sentiment_pipe = pipeline("sentiment-analysis", model="distilbert-base-uncased-finetuned-sst-2-english")
        classifier_pipe = pipeline("zero-shot-classification", model="facebook/bart-large-mnli")
    except Exception as e:
        logger.warning(f"Failed to load HF transformers models locally: {e}. Falling back to rule-based engine.")


from app.core.languages import detect_text_language, get_language_name, get_language
from app.services.translation_service import translate_to_english


def analyze_customer_message(text: str, language: Optional[str] = None) -> Dict[str, Any]:
    """
    Performs NLP analysis on incoming customer message:
    - Sentiment & confidence score
    - Intent classification
    - Emotion detection
    - Topic extraction
    - Language identification
    """
    detected_lang_code = language or detect_text_language(text) or "en"
    lang_name = get_language_name(detected_lang_code)

    # For non-English messages, analyze the English translation so standard heuristics/models work accurately
    analysis_text = text
    if detected_lang_code != "en":
        analysis_text = translate_to_english(text, source_language=detected_lang_code)

    text_lower = analysis_text.lower()

    # If HF pipelines are loaded locally
    if sentiment_pipe and classifier_pipe:
        try:
            sent_res = sentiment_pipe(analysis_text[:512])[0]
            sentiment_label = sent_res["label"].title()  # Positive / Negative
            sentiment_score = float(sent_res["score"])

            candidate_intents = ["Order Delay Issue", "Billing and Refund", "Technical Bug", "General Complaint", "Account Support"]
            intent_res = classifier_pipe(analysis_text, candidate_intents)
            intent_label = intent_res["labels"][0]

            candidate_emotions = ["Frustration", "Anger", "Confusion", "Satisfaction", "Neutral"]
            emotion_res = classifier_pipe(analysis_text, candidate_emotions)
            emotion_label = emotion_res["labels"][0]

            return {
                "sentiment": sentiment_label,
                "sentiment_score": round(sentiment_score, 2),
                "intent": intent_label,
                "emotion": emotion_label,
                "topic": intent_label.split()[0],
                "language": lang_name
            }
        except Exception as e:
            logger.error(f"HF pipeline error: {e}, falling back to intelligent heuristics.")

    # Intelligent Fallback Engine (Fast & reliable for local dev & demo)
    sentiment_label = "Neutral"
    sentiment_score = 0.65
    emotion_label = "Calm"
    intent_label = "General Inquiry"
    topic = "General"

    neg_words = ["waiting", "delay", "frustrating", "terrible", "bad", "slow", "broken", "issue", "problem", "angry", "upset", "worst", "hate"]
    pos_words = ["thanks", "thank you", "great", "awesome", "helpful", "good", "love", "resolved", "fixed"]

    neg_count = sum(1 for w in neg_words if w in text_lower)
    pos_count = sum(1 for w in pos_words if w in text_lower)

    if neg_count > pos_count:
        sentiment_label = "Negative"
        sentiment_score = round(0.70 + min(neg_count * 0.08, 0.28), 2)
    elif pos_count > neg_count:
        sentiment_label = "Positive"
        sentiment_score = round(0.75 + min(pos_count * 0.08, 0.23), 2)

    # Intent & Emotion heuristics
    if any(k in text_lower for k in ["order", "package", "deliver", "ship", "track", "delay", "waiting for my order"]):
        intent_label = "Order Delay / Logistics"
        topic = "Order Status"
    elif any(k in text_lower for k in ["bill", "charge", "refund", "card", "cost", "money"]):
        intent_label = "Billing & Payment"
        topic = "Refund Request"
    elif any(k in text_lower for k in ["error", "bug", "crash", "log in", "password", "app"]):
        intent_label = "Technical Issue"
        topic = "App Glitch"
    elif sentiment_label == "Negative":
        intent_label = "Customer Complaint"
        topic = "Service Complaint"

    if "frustrat" in text_lower or "wait" in text_lower:
        emotion_label = "Frustration"
    elif any(k in text_lower for k in ["angry", "mad", "unacceptable", "furious"]):
        emotion_label = "Anger"
    elif "confus" in text_lower or "don't understand" in text_lower or "why" in text_lower:
        emotion_label = "Confusion"
    elif sentiment_label == "Positive":
        emotion_label = "Satisfaction"

    return {
        "sentiment": sentiment_label,
        "sentiment_score": sentiment_score,
        "intent": intent_label,
        "emotion": emotion_label,
        "topic": topic,
        "language": lang_name
    }
