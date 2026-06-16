import re
from datetime import datetime, timezone

from .evidence import suggest_evidence
from .fallback import extract_entities, fallback_analyze
from .preprocessing import preprocess_complaint
from .priority import assign_priority
from .providers import AIProviderError, build_provider
from .schema import DEFAULT_ANALYSIS


KEYWORD_TERMS = [
    "aadhaar",
    "abuse",
    "accident",
    "assault",
    "atm",
    "bank",
    "blackmail",
    "card",
    "consent",
    "consunt",
    "chori",
    "credit card",
    "cyber stalking",
    "debit card",
    "domestic violence",
    "daily",
    "fake id",
    "fake job",
    "facebook",
    "fraud",
    "gpay",
    "harassment",
    "identity theft",
    "instagram",
    "imei",
    "job",
    "kyc",
    "link",
    "missing",
    "pan",
    "otp",
    "otps",
    "aadhaar",
    "paytm",
    "phonepe",
    "phishing",
    "purse",
    "qr",
    "rash driving",
    "registration fee",
    "robbery",
    "shopping",
    "stolen",
    "telegram",
    "theft",
    "threat",
    "upi",
    "wallet",
    "whatsapp",
]


def analyze_complaint(complaint_text, provider=None):
    preprocessing = preprocess_complaint(complaint_text)
    text = preprocessing["clean_text"]
    if not text:
        raise ValueError("Complaint text is required.")

    try:
        provider = provider or build_provider()
    except AIProviderError as exc:
        provider = None
        provider_error = summarize_provider_error(str(exc))

    engine = "local_fallback"
    provider_error = provider_error if "provider_error" in locals() else None

    try:
        if provider and provider.available:
            analysis = provider.analyze(text)
            engine = provider.engine_name
        else:
            analysis = fallback_analyze(text)
            provider_error = provider.unavailable_reason if provider else provider_error
    except AIProviderError as exc:
        analysis = fallback_analyze(text)
        provider_error = summarize_provider_error(str(exc))

    normalized = normalize_analysis(analysis, text, preprocessing)
    normalized["engine"] = engine
    normalized["engine_display"] = format_engine_display(engine)
    normalized["provider_error"] = provider_error
    normalized["provider_status_display"] = format_provider_status(provider_error)
    normalized["timestamp"] = datetime.now(timezone.utc).isoformat()
    normalized["original_complaint"] = text
    return normalized


def format_engine_display(engine):
    if engine == "local_fallback":
        return "Local fallback"

    if engine.startswith("openai_compatible:"):
        model = engine.split(":", 1)[1]
        return f"OpenRouter AI ({model})"

    if engine.startswith("openai:"):
        model = engine.split(":", 1)[1]
        return f"OpenAI ({model})"

    if engine.startswith("ollama:"):
        model = engine.split(":", 1)[1]
        return f"Local Ollama ({model})"

    return engine


def format_provider_status(provider_error):
    if provider_error:
        return provider_error
    return "Connected and completed successfully"


def summarize_provider_error(error_message):
    lower_message = error_message.lower()

    if "api key" in lower_message or "not configured" in lower_message:
        return error_message

    if "unsupported ai_provider" in lower_message:
        return error_message

    if "api error 500" in lower_message or "server_error" in lower_message:
        return "AI provider returned a temporary server error. Retrying later or changing the model may fix it."

    if "api error 401" in lower_message or "invalid_api_key" in lower_message or "unauthorized" in lower_message:
        return "AI provider rejected the API key. Rotate/update the key in .env."

    if "api error 403" in lower_message or "forbidden" in lower_message:
        return "AI provider account does not have access to this model or endpoint. Check AI_MODEL and choose an available model from your provider."

    if "api error 404" in lower_message or "model_not_found" in lower_message:
        return "Configured model or API endpoint was not found."

    if "api error 429" in lower_message or "rate_limit" in lower_message or "quota" in lower_message:
        return "AI provider rate limit or quota reached. Check usage/billing or retry later."

    if "network error" in lower_message:
        return "Network error while contacting AI provider."

    return "AI provider failed. Local fallback was used."


def normalize_analysis(analysis, complaint_text, preprocessing=None):
    preprocessing = preprocessing or preprocess_complaint(complaint_text)
    normalized = {
        **DEFAULT_ANALYSIS,
        **(analysis or {}),
    }

    normalized["keywords"] = _as_string_list(normalized.get("keywords"))
    normalized["evidence_checklist"] = _as_string_list(normalized.get("evidence_checklist"))
    normalized["next_steps"] = _as_string_list(normalized.get("next_steps"))
    normalized["possible_legal_sections"] = _as_string_list(normalized.get("possible_legal_sections"))
    normalized["entities"] = merge_entities(
        _normalize_entities(normalized.get("entities")),
        extract_entities(complaint_text),
    )
    priority, risk_level, priority_reasons = assign_priority(
        normalized.get("category"),
        normalized["entities"],
        complaint_text,
        normalized.get("priority"),
        normalized.get("risk_level"),
    )
    normalized["priority"] = priority
    normalized["risk_level"] = risk_level
    normalized["evidence_checklist"] = _dedupe_preserve_order(
        [
            *suggest_evidence(normalized.get("category"), normalized["entities"], complaint_text),
            *normalized["evidence_checklist"],
        ]
    )
    normalized["confidence"] = _clamp_float(normalized.get("confidence"), 0, 1, 0.35)
    normalized["needs_human_review"] = bool(normalized.get("needs_human_review"))

    for key in ["category", "department", "priority", "risk_level", "summary", "reasoning", "language"]:
        normalized[key] = str(normalized.get(key) or DEFAULT_ANALYSIS[key]).strip()

    if preprocessing.get("language") != "unknown":
        normalized["language"] = preprocessing["language"]

    if normalized["priority"] not in {"High", "Medium", "Low"}:
        normalized["priority"] = "Medium"

    if normalized["risk_level"] not in {"Critical", "High", "Medium", "Low"}:
        normalized["risk_level"] = normalized["priority"]

    if not normalized["summary"]:
        normalized["summary"] = " ".join(complaint_text.split())[:220]

    if not normalized["possible_legal_sections"]:
        normalized["possible_legal_sections"] = list(DEFAULT_ANALYSIS["possible_legal_sections"])

    if not normalized["keywords"]:
        normalized["keywords"] = infer_keywords(complaint_text, normalized)

    normalized["preprocessing"] = {
        "language_detected": normalized["language"],
        "clean_text": preprocessing.get("clean_text", ""),
        "token_count": preprocessing.get("token_count", 0),
        "tokens": preprocessing.get("tokens", [])[:40],
        "transliteration": preprocessing.get("transliteration", ""),
    }

    if priority_reasons:
        normalized["reasoning"] = f"{normalized['reasoning']} Priority rule signals: {', '.join(priority_reasons)}."

    return normalized


def infer_keywords(complaint_text, analysis):
    text = complaint_text.lower()
    keywords = []

    for term in KEYWORD_TERMS:
        if term in text:
            keywords.append(term)

    for values in analysis.get("entities", {}).values():
        for value in values:
            if value and value not in keywords:
                keywords.append(value)

    if not keywords:
        category_words = re.findall(r"[A-Za-z][A-Za-z0-9/-]{2,}", analysis.get("category", ""))
        keywords.extend(category_words[:3])

    if not keywords:
        complaint_words = re.findall(r"[A-Za-z][A-Za-z0-9/-]{3,}", complaint_text)
        keywords.extend(complaint_words[:5])

    return _dedupe_preserve_order(keywords)[:8]


def _as_string_list(value):
    if not isinstance(value, list):
        return []
    return [str(item).strip() for item in value if str(item).strip()]


def _dedupe_preserve_order(items):
    seen = set()
    result = []
    for item in items:
        normalized = str(item).strip()
        key = normalized.lower()
        if normalized and key not in seen:
            seen.add(key)
            result.append(normalized)
    return result


def _normalize_entities(value):
    base = {key: [] for key in DEFAULT_ANALYSIS["entities"]}
    if not isinstance(value, dict):
        return base
    for key in base:
        base[key] = _as_string_list(value.get(key))
    return base


def merge_entities(primary, detected):
    merged = {key: list(primary.get(key, [])) for key in DEFAULT_ANALYSIS["entities"]}
    for key in merged:
        merged[key] = _dedupe_preserve_order([*merged[key], *detected.get(key, [])])
    return merged


def _clamp_float(value, minimum, maximum, default):
    try:
        number = float(value)
    except (TypeError, ValueError):
        return default
    return max(minimum, min(maximum, number))
