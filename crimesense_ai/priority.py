import re


PRIORITY_RANK = {"Low": 0, "Medium": 1, "High": 2}
RISK_RANK = {"Low": 0, "Medium": 1, "High": 2, "Critical": 3}

HIGH_SIGNAL_RE = re.compile(
    r"\b(suicide|blackmail|threat|dhamki|minor|child|kidnap|abduction|rape|sextortion|"
    r"morphed|nude|intimate|violence|assault|weapon|emergency|missing)\b",
    re.I,
)
MEDIUM_SIGNAL_RE = re.compile(r"\b(phishing|url|link|kyc|otp|harass|fake profile|identity|aadhaar|pan)\b", re.I)


def assign_priority(category, entities, text, current_priority="Low", current_risk="Low"):
    amount = max_amount(entities)
    lowered = str(text or "").lower()
    priority = normalize_priority(current_priority)
    risk = normalize_risk(current_risk)
    reasons = []

    if amount >= 50000:
        priority, risk = _raise_priority(priority, risk, "High", "High")
        reasons.append("amount above Rs. 50,000")
    elif 5000 <= amount < 50000:
        priority, risk = _raise_priority(priority, risk, "Medium", "Medium")
        reasons.append("amount between Rs. 5,000 and Rs. 50,000")

    if HIGH_SIGNAL_RE.search(lowered):
        priority, risk = _raise_priority(priority, risk, "High", "High")
        reasons.append("high-risk safety/threat keyword")

    if MEDIUM_SIGNAL_RE.search(lowered) or _has_any(entities, ["urls", "upi_ids", "bank_references"]):
        priority, risk = _raise_priority(priority, risk, "Medium", "Medium")
        reasons.append("phishing/identity/payment evidence present")

    if "missing" in str(category or "").lower():
        priority, risk = _raise_priority(priority, risk, "High", "High")
        reasons.append("missing-person category")

    if any("multiple" in value.lower() or "daily" in value.lower() for value in entities.get("counts", [])):
        priority, risk = _raise_priority(priority, risk, "Medium", "Medium")
        reasons.append("repeated activity mentioned")

    return priority, risk, reasons


def max_amount(entities):
    amounts = []
    for value in entities.get("amounts", []):
        digits = re.sub(r"[^\d]", "", str(value))
        if digits:
            try:
                amounts.append(int(digits))
            except ValueError:
                continue
    return max(amounts, default=0)


def normalize_priority(value):
    value = str(value or "").title()
    return value if value in PRIORITY_RANK else "Low"


def normalize_risk(value):
    value = str(value or "").title()
    return value if value in RISK_RANK else "Low"


def _raise_priority(priority, risk, proposed_priority, proposed_risk):
    if PRIORITY_RANK[proposed_priority] > PRIORITY_RANK[priority]:
        priority = proposed_priority
    if RISK_RANK[proposed_risk] > RISK_RANK[risk]:
        risk = proposed_risk
    return priority, risk


def _has_any(entities, keys):
    return any(entities.get(key) for key in keys)
