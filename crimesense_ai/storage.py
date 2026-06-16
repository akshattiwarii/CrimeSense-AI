import json
import re
import threading
from collections import Counter
from datetime import datetime, timedelta
from pathlib import Path


DATA_DIR = Path("data")
COMPLAINTS_FILE = DATA_DIR / "complaints.json"
_LOCK = threading.Lock()

CYBER_TERMS = (
    "cyber",
    "upi",
    "otp",
    "phishing",
    "online",
    "social media",
    "identity theft",
    "fake job",
    "bank/card",
    "financial fraud",
    "blackmail",
    "stalking",
)


def save_complaint(analysis):
    complaints = load_complaints()
    complaint_id = _next_complaint_id(complaints)
    record = {
        "id": complaint_id,
        "timestamp": analysis.get("timestamp"),
        "category": analysis.get("category", "Unknown"),
        "department": analysis.get("department", "Unknown"),
        "priority": analysis.get("priority", "Unknown"),
        "risk_level": analysis.get("risk_level", "Unknown"),
        "summary": analysis.get("summary", ""),
        "keywords": analysis.get("keywords", []),
        "evidence_checklist": analysis.get("evidence_checklist", []),
        "next_steps": analysis.get("next_steps", []),
        "possible_legal_sections": analysis.get("possible_legal_sections", []),
        "entities": analysis.get("entities", {}),
        "fir_details": analysis.get("fir_details", {}),
        "attachments": analysis.get("attachments", []),
        "reasoning": analysis.get("reasoning", ""),
        "confidence": analysis.get("confidence", 0),
        "needs_human_review": analysis.get("needs_human_review", True),
        "similar_complaints": analysis.get("similar_complaints", []),
        "original_complaint": analysis.get("original_complaint", ""),
        "engine": analysis.get("engine", "unknown"),
        "engine_display": analysis.get("engine_display", analysis.get("engine", "unknown")),
        "provider_status_display": analysis.get("provider_status_display", ""),
        "preprocessing": analysis.get("preprocessing", {}),
    }

    with _LOCK:
        complaints.append(record)
        DATA_DIR.mkdir(exist_ok=True)
        COMPLAINTS_FILE.write_text(json.dumps(complaints, ensure_ascii=False, indent=2), encoding="utf-8")

    return record


def load_complaints():
    if not COMPLAINTS_FILE.exists():
        return []

    try:
        data = json.loads(COMPLAINTS_FILE.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        return []

    if not isinstance(data, list):
        return []

    return [_normalize_record(record, index) for index, record in enumerate(data, start=1)]


def find_complaint(complaint_id):
    for record in load_complaints():
        if str(record.get("id")) == str(complaint_id):
            return record
    return None


def find_similar_complaints(analysis, limit=5, threshold=0.35):
    current_text = _similarity_text(analysis)
    current_tokens = _tokens(current_text)
    matches = []

    if not current_tokens:
        return []

    for record in load_complaints():
        score = _similarity_score(current_tokens, analysis, record)
        if score >= threshold:
            matches.append(
                {
                    "id": record.get("id"),
                    "similarity": round(score * 100),
                    "category": record.get("category", "Unknown"),
                    "priority": record.get("priority", "Unknown"),
                    "summary": record.get("summary", ""),
                    "timestamp": record.get("timestamp"),
                    "url": f"complaint.html?id={record.get('id')}",
                }
            )

    matches.sort(key=lambda item: item["similarity"], reverse=True)
    return matches[:limit]


def dashboard_stats():
    complaints = load_complaints()
    categories = Counter(record.get("category", "Unknown") for record in complaints)
    daily = Counter(_date_key(record.get("timestamp")) for record in complaints)
    weekly_days = _last_seven_days()
    cyber_categories = Counter(
        record.get("category", "Unknown")
        for record in complaints
        if _is_cyber_category(record.get("category", ""))
    )

    recent = list(reversed(complaints[-8:]))

    return {
        "total_complaints": len(complaints),
        "category_distribution": [
            {"category": category, "count": count}
            for category, count in categories.most_common()
        ],
        "weekly_trends": [
            {
                "date": day.isoformat(),
                "day": day.strftime("%a %d %b"),
                "count": daily[day.isoformat()],
            }
            for day in weekly_days
        ],
        "most_common_cybercrime": _top_counter_item(cyber_categories),
        "recent_complaints": recent,
    }


def _normalize_record(record, fallback_id):
    normalized = dict(record) if isinstance(record, dict) else {}
    normalized.setdefault("id", fallback_id)
    normalized.setdefault("timestamp", None)
    normalized.setdefault("category", "Unknown")
    normalized.setdefault("department", "Unknown")
    normalized.setdefault("priority", "Unknown")
    normalized.setdefault("risk_level", "Unknown")
    normalized.setdefault("summary", "")
    normalized.setdefault("keywords", [])
    normalized.setdefault("evidence_checklist", [])
    normalized.setdefault("next_steps", [])
    normalized.setdefault("possible_legal_sections", [])
    normalized.setdefault("entities", {})
    normalized.setdefault("fir_details", {})
    normalized.setdefault("attachments", [])
    normalized.setdefault("reasoning", "")
    normalized.setdefault("confidence", 0)
    normalized.setdefault("needs_human_review", True)
    normalized.setdefault("similar_complaints", [])
    normalized.setdefault("original_complaint", "")
    normalized.setdefault("engine", "unknown")
    normalized.setdefault("engine_display", normalized.get("engine", "unknown"))
    normalized.setdefault("provider_status_display", "")
    normalized.setdefault("preprocessing", {})
    return normalized


def _next_complaint_id(complaints):
    ids = []
    for record in complaints:
        try:
            ids.append(int(record.get("id", 0)))
        except (TypeError, ValueError):
            continue
    return max(ids, default=100) + 1


def _similarity_score(current_tokens, analysis, record):
    other_tokens = _tokens(_similarity_text(record))
    if not other_tokens:
        return 0

    overlap = len(current_tokens & other_tokens)
    union = len(current_tokens | other_tokens)
    token_score = overlap / union if union else 0

    category_boost = 0.12 if _same_text(analysis.get("category"), record.get("category")) else 0
    department_boost = 0.06 if _same_text(analysis.get("department"), record.get("department")) else 0
    keyword_boost = _keyword_overlap(analysis.get("keywords", []), record.get("keywords", [])) * 0.18

    return min(1, token_score * 0.72 + category_boost + department_boost + keyword_boost)


def _similarity_text(record):
    entities = record.get("entities") or {}
    entity_values = []
    if isinstance(entities, dict):
        for values in entities.values():
            if isinstance(values, list):
                entity_values.extend(str(value) for value in values)

    parts = [
        record.get("original_complaint", ""),
        record.get("summary", ""),
        record.get("category", ""),
        record.get("department", ""),
        " ".join(record.get("keywords", []) if isinstance(record.get("keywords"), list) else []),
        " ".join(entity_values),
    ]
    return " ".join(part for part in parts if part)


def _tokens(text):
    stopwords = {
        "the", "and", "for", "with", "from", "that", "this", "hai", "hua", "kar",
        "mujhe", "mera", "meri", "your", "you", "are", "was", "were", "been",
        "complaint", "classified", "as", "case", "report",
    }
    return {
        token
        for token in re.findall(r"[a-zA-Z0-9@._/-]{3,}", text.lower())
        if token not in stopwords
    }


def _same_text(left, right):
    return str(left or "").strip().lower() == str(right or "").strip().lower()


def _keyword_overlap(left, right):
    left_set = {str(item).lower() for item in left if str(item).strip()}
    right_set = {str(item).lower() for item in right if str(item).strip()}
    if not left_set or not right_set:
        return 0
    return len(left_set & right_set) / len(left_set | right_set)


def _date_key(timestamp):
    if not timestamp:
        return "Unknown"

    try:
        parsed = datetime.fromisoformat(timestamp.replace("Z", "+00:00"))
    except ValueError:
        return "Unknown"

    return parsed.date().isoformat()


def _last_seven_days():
    today = datetime.now().date()
    return [today - timedelta(days=offset) for offset in range(6, -1, -1)]


def _is_cyber_category(category):
    lowered = category.lower()
    return any(term in lowered for term in CYBER_TERMS)


def _top_counter_item(counter):
    if not counter:
        return {"category": "No cybercrime complaints yet", "count": 0}

    category, count = counter.most_common(1)[0]
    return {"category": category, "count": count}
