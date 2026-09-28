import os
import re
import logging
from typing import Dict, Any, Optional, List
from app.core.config import settings

logger = logging.getLogger("llm_response_service")

# Fallback response mandated by Phase 8 specification
FALLBACK_RESPONSE = (
    "I'm sorry, I couldn't complete that request automatically. "
    "I've sent your request to a support specialist so you can still get help."
)

SYSTEM_PROMPT = """You are the customer-facing support assistant for this application.

Answer customer questions clearly, politely and concisely.

Never invent:
- order status
- refunds
- payments
- account information
- company policies
- transaction details
- tracking information

Only use verified application context supplied by the backend.

You may explain general information.

You must NOT:
- approve refunds
- cancel accounts
- change payments
- promise compensation
- make legal decisions
- perform sensitive business actions

If a request requires a human agent, clearly explain that a support specialist will handle it."""


def _sanitize_error_msg(error_str: str) -> str:
    """Masks any potential raw API keys or secrets from error strings for safety."""
    if not error_str:
        return ""
    # Redact standard Gemini / Google AI Studio or OpenAI API key patterns
    sanitized = re.sub(r"AIza[A-Za-z0-9_\-]{30,}", "[REDACTED_GEMINI_KEY]", str(error_str))
    sanitized = re.sub(r"sk-[A-Za-z0-9_\-]{8,}", "[REDACTED_API_KEY]", sanitized)
    return sanitized


def get_gemini_api_key() -> str:
    """Retrieves Gemini API key from environment or application settings."""
    return (
        os.environ.get("GEMINI_API_KEY")
        or os.environ.get("GOOGLE_API_KEY")
        or settings.GEMINI_API_KEY
        or ""
    )


def get_gemini_model() -> str:
    """Retrieves Gemini model name from environment or application settings."""
    return os.environ.get("GEMINI_MODEL") or settings.GEMINI_MODEL or "gemini-3.5-flash"


def is_gemini_configured() -> bool:
    """Checks if a non-empty Gemini API key is configured."""
    key = get_gemini_api_key().strip()
    return bool(key and key != "your-gemini-api-key-here")


# Aliases for backward-compatibility if referenced elsewhere
def get_openai_api_key() -> str:
    return get_gemini_api_key()


def is_openai_configured() -> bool:
    return is_gemini_configured()


def generate_llm_response(
    customer_message: str,
    context_obj: Optional[Dict[str, Any]] = None,
    conversation_history: Optional[List[Dict[str, str]]] = None
) -> Dict[str, Any]:
    """
    Calls Google Gemini API using the official google-genai SDK
    with strict system guardrails and verified customer context.
    Returns:
        {
            "success": bool,
            "response_text": str,
            "is_fallback": bool,
            "error": Optional[str]
        }
    """
    key_configured = is_gemini_configured()
    model_name = get_gemini_model()

    # SAFE DIAGNOSTIC LOGGING - Log True/False ONLY (never the key itself)
    logger.info(f"[LLM DIAGNOSTIC] GEMINI_API_KEY configured: {key_configured}")
    logger.info(f"[LLM DIAGNOSTIC] Selected model: {model_name}")

    if not key_configured:
        logger.warning("[LLM DIAGNOSTIC] GEMINI_API_KEY is not configured or empty. Using safe fallback response.")
        return {
            "success": False,
            "response_text": FALLBACK_RESPONSE,
            "is_fallback": True,
            "error": "GEMINI_API_KEY is not configured"
        }

    preview_text = (customer_message[:60] + "...") if len(customer_message) > 60 else customer_message
    logger.info(f"[LLM DIAGNOSTIC] Attempting Gemini request for: '{preview_text}'")

    api_key = get_gemini_api_key().strip()

    try:
        from google import genai
        from google.genai import types

        # Initialize official Google GenAI client with explicit timeout
        client = genai.Client(
            api_key=api_key,
            http_options=types.HttpOptions(timeout=30000)
        )

        # Compile verified context snippet
        verified_context = ""
        if context_obj:
            cust = context_obj.get("customer", {})
            mem_summary = context_obj.get("memory_summary", {}).get("summary_text", "")
            verified_context = f"Verified Customer Context: Tier={cust.get('tier', 'Standard')}"
            if mem_summary:
                verified_context += f", History={mem_summary}"

        full_system_instruction = SYSTEM_PROMPT
        if verified_context:
            full_system_instruction += "\n\n" + verified_context

        # Build contents list
        contents = []
        if conversation_history:
            for item in conversation_history[-4:]:
                role = "user" if item.get("sender_type") == "customer" else "model"
                contents.append(types.Content(
                    role=role,
                    parts=[types.Part.from_text(text=item.get("content", ""))]
                ))

        contents.append(types.Content(
            role="user",
            parts=[types.Part.from_text(text=customer_message)]
        ))

        config = types.GenerateContentConfig(
            system_instruction=full_system_instruction,
            temperature=0.4,
            max_output_tokens=800,
            thinking_config=types.ThinkingConfig(thinking_budget=0)
        )

        models_to_try = [model_name]
        for alt in ["gemini-3.5-flash", "gemini-3.6-flash"]:
            if alt not in models_to_try:
                models_to_try.append(alt)

        response = None
        last_exc = None
        used_model = model_name

        for candidate_model in models_to_try:
            try:
                response = client.models.generate_content(
                    model=candidate_model,
                    contents=contents,
                    config=config
                )
                used_model = candidate_model
                break
            except Exception as e:
                last_exc = e
                err_str = str(e).upper()
                if any(code in err_str for code in ["429", "RESOURCE_EXHAUSTED", "404", "503", "UNAVAILABLE", "high demand"]):
                    logger.warning(f"[LLM DIAGNOSTIC] Model {candidate_model} returned {type(e).__name__} (quota/demand error). Trying next model...")
                    continue
                else:
                    raise e

        if response is None and last_exc is not None:
            raise last_exc

        reply_content = (response.text or "").strip() if response and response.text else ""
        if not reply_content:
            raise ValueError("Empty response received from Gemini API")

        logger.info(f"[LLM DIAGNOSTIC] Gemini request succeeded (model: {used_model}, response length: {len(reply_content)} chars)")
        return {
            "success": True,
            "response_text": reply_content,
            "is_fallback": False,
            "error": None
        }

    except Exception as exc:
        exc_type = type(exc).__name__
        safe_msg = _sanitize_error_msg(str(exc))
        logger.error(f"[LLM DIAGNOSTIC] Gemini request failed! Exception Type: {exc_type}, Message: {safe_msg}")
        return {
            "success": False,
            "response_text": FALLBACK_RESPONSE,
            "is_fallback": True,
            "error": f"{exc_type}: {safe_msg}"
        }
