from .priority import max_amount


EVIDENCE_MAP = {
    "financial": [
        "Bank or UPI transaction screenshot",
        "UPI transaction ID / UTR / RRN",
        "Bank SMS or email alert",
        "Payment app screenshot",
        "Suspect phone number, UPI ID, or bank account detail",
    ],
    "phishing": [
        "Suspicious URL and full webpage screenshot",
        "SMS/email/chat containing the link",
        "Browser history timestamp",
        "Email headers if received by email",
    ],
    "social": [
        "Profile URL and username",
        "Chat screenshots with date/time visible",
        "Post/story/reel links if available",
        "Account ID, phone number, or email linked to suspect",
    ],
    "malware": [
        "Malicious app/file name and download source",
        "Device screenshots showing warning or lock screen",
        "Antivirus/security scan result",
        "Approximate install or compromise time",
    ],
    "identity": [
        "Aadhaar/PAN/SIM/account misuse proof",
        "KYC message or application reference",
        "Bank/telecom acknowledgement if available",
        "Screenshots of fake account or document misuse",
    ],
    "theft": [
        "Item description and identifiers such as IMEI/serial number",
        "Purchase bill or ownership proof",
        "CCTV/witness details",
        "Location and time of incident",
    ],
    "general": [
        "Complainant contact details",
        "Date, time, and location of incident",
        "Screenshots, photos, documents, or messages related to the complaint",
    ],
}


def suggest_evidence(category, entities, text):
    lowered = f"{category} {text}".lower()
    suggestions = []

    if _has_any(lowered, ["upi", "otp", "bank", "card", "loan", "financial", "transaction"]) or max_amount(entities) > 0:
        suggestions.extend(EVIDENCE_MAP["financial"])

    if _has_any(lowered, ["phishing", "kyc", "link", "fake website"]) or entities.get("urls"):
        suggestions.extend(EVIDENCE_MAP["phishing"])

    if _has_any(lowered, ["instagram", "facebook", "whatsapp", "telegram", "social", "harassment", "blackmail", "cyberbullying"]):
        suggestions.extend(EVIDENCE_MAP["social"])

    if _has_any(lowered, ["malware", "ransomware", "device locked", "virus", "app installed"]):
        suggestions.extend(EVIDENCE_MAP["malware"])

    if _has_any(lowered, ["identity", "aadhaar", "pan", "sim swap", "kyc"]):
        suggestions.extend(EVIDENCE_MAP["identity"])

    if _has_any(lowered, ["theft", "stolen", "chori", "robbery", "purse", "wallet"]):
        suggestions.extend(EVIDENCE_MAP["theft"])

    suggestions.extend(EVIDENCE_MAP["general"])
    return _dedupe(suggestions)


def _has_any(text, terms):
    return any(term in text for term in terms)


def _dedupe(items):
    seen = set()
    result = []
    for item in items:
        key = item.lower()
        if key not in seen:
            seen.add(key)
            result.append(item)
    return result
