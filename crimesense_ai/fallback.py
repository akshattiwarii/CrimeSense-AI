import re

from .schema import DEFAULT_ANALYSIS


PATTERNS = [
    {
        "category": "Fake Job Scam",
        "department": "Cyber Cell / Economic Offences Wing",
        "priority": "Medium",
        "risk_level": "Medium",
        "terms": ["fake job", "job", "naukri", "recruitment", "offer letter", "registration fee", "training fee", "interview", "work from home", "task scam"],
        "evidence": ["Job link or advertisement", "Recruiter phone number or email", "Chat screenshots", "Payment receipt if money was paid", "Company name claimed"],
        "steps": ["Do not pay any further registration or training fee.", "Verify the company only through official channels.", "Preserve chats, job link, payment proof, and recruiter details."],
    },
    {
        "category": "Cyber Financial Fraud",
        "department": "Cyber Cell / Bank Fraud Desk",
        "priority": "High",
        "risk_level": "High",
        "terms": ["upi", "otp", "kyc", "phishing", "bank", "card", "paytm", "phonepe", "gpay", "qr", "unauthorized transaction"],
        "evidence": ["Transaction ID", "Bank or wallet SMS", "Payment app screenshot", "Suspicious URL or phone number"],
        "steps": ["Contact bank helpline and request hold or freeze.", "File cyber complaint with transaction details.", "Preserve screenshots and SMS alerts."],
    },
    {
        "category": "Phishing Link / Fake Website",
        "department": "Cyber Cell",
        "priority": "Medium",
        "risk_level": "Medium",
        "terms": ["phishing", "fake website", "fake link", "kyc link", "login link", "verify account", "bank link", "gov link", "sbi link"],
        "evidence": ["Suspicious URL", "Webpage screenshot", "SMS/email/chat containing the link", "Browser history timestamp", "Any OTP or credential sharing details"],
        "steps": ["Do not open the link again or enter credentials.", "Capture the URL and sender details.", "Change affected passwords and notify the bank/service provider."],
    },
    {
        "category": "Ransomware / Malware",
        "department": "Cyber Cell / Digital Forensics Desk",
        "priority": "High",
        "risk_level": "High",
        "terms": ["ransomware", "malware", "virus", "device locked", "phone locked", "laptop locked", "data encrypted", "data stolen", "apk", "remote access app", "anydesk"],
        "evidence": ["Device screenshots", "Malicious app/file name", "Download source or URL", "Ransom note or demand message", "Approximate compromise time"],
        "steps": ["Disconnect the affected device from the network if safe.", "Do not pay ransom without official guidance.", "Preserve the device state for forensic review."],
    },
    {
        "category": "Identity Theft / SIM Swap",
        "department": "Cyber Cell / Economic Offences Wing",
        "priority": "High",
        "risk_level": "High",
        "terms": ["identity theft", "aadhaar misuse", "pan misuse", "sim swap", "duplicate sim", "kyc misuse", "account opened", "loan in my name"],
        "evidence": ["Aadhaar/PAN/SIM misuse proof", "KYC or telecom messages", "Bank or loan account reference", "Fake profile/account screenshots"],
        "steps": ["Contact bank/telecom provider for immediate blocking.", "Collect identity document misuse proof.", "Request written acknowledgement from provider if available."],
    },
    {
        "category": "Sextortion / Online Blackmail",
        "department": "Cyber Cell / Women Safety Cell if applicable",
        "priority": "High",
        "risk_level": "High",
        "terms": ["sextortion", "nude", "intimate", "private photo", "video call recording", "blackmail", "photo viral", "morphed"],
        "evidence": ["Threat screenshots", "Profile URL or username", "Payment demand details", "Chat screenshots", "Any shared media reference without forwarding it publicly"],
        "steps": ["Do not pay or negotiate further.", "Preserve chats and account URLs.", "Escalate for urgent cyber cell review."],
    },
    {
        "category": "Cyberbullying / Online Threat",
        "department": "Cyber Cell / Local Police Station",
        "priority": "High",
        "risk_level": "High",
        "terms": ["cyberbullying", "trolling", "abusive messages", "online threat", "death threat", "dhamki", "harassment", "pareshan"],
        "evidence": ["Message screenshots", "Profile URL", "Date/time of threats", "Witness or group chat details"],
        "steps": ["Save evidence before blocking/reporting.", "Record exact usernames and URLs.", "Escalate immediately if there is physical danger."],
    },
    {
        "category": "Online Harassment / Blackmail",
        "department": "Cyber Cell / Women Safety Cell if applicable",
        "priority": "High",
        "risk_level": "High",
        "terms": ["instagram", "facebook", "whatsapp", "blackmail", "harass", "pareshan", "fake id", "photo viral", "morphed"],
        "evidence": ["Profile URL", "Chat screenshots", "Username or phone number", "Threat screenshots"],
        "steps": ["Save screenshots before blocking.", "Copy profile URL and username exactly.", "Report the account and approach cyber cell."],
    },
    {
        "category": "Missing Person",
        "department": "Missing Persons Unit / Local Police Station",
        "priority": "High",
        "risk_level": "High",
        "terms": ["missing", "gumshuda", "not reachable", "ghar nahi aaye", "last seen"],
        "evidence": ["Recent photograph", "Last known location", "Last contact time", "Phone number"],
        "steps": ["Contact nearest police station immediately.", "Collect recent photo and last-seen details.", "Share known contacts and phone details."],
    },
    {
        "category": "Traffic Accident",
        "department": "Traffic Police / Emergency Response",
        "priority": "High",
        "risk_level": "High",
        "terms": ["accident", "rash driving", "hit and run", "vehicle", "car", "bike", "injury", "road"],
        "evidence": ["Vehicle number", "Location", "Photos or videos", "Witness details", "Medical record if injured"],
        "steps": ["Call emergency services if anyone is injured.", "Note vehicle number and location.", "Preserve photos, videos, and witness details."],
    },
    {
        "category": "Theft / Property Crime",
        "department": "Local Police Station",
        "priority": "Medium",
        "risk_level": "Medium",
        "terms": ["theft", "stolen", "chori", "loot", "robbery", "mobile stolen", "wallet", "chain snatching"],
        "evidence": ["Item description", "Location", "Date and time", "CCTV or witness details", "Purchase bill or IMEI if available"],
        "steps": ["Report at local police station.", "Collect item identifiers and CCTV possibilities.", "Block stolen SIM/card if needed."],
    },
    {
        "category": "Domestic Violence / Threat",
        "department": "Women Safety Cell / Local Police Station",
        "priority": "High",
        "risk_level": "High",
        "terms": ["domestic violence", "maar", "beat", "assault", "threat", "dhamki", "husband", "dowry", "dahej"],
        "evidence": ["Medical report or injury photos", "Threat messages", "Witness details", "Date and time", "Address"],
        "steps": ["Contact emergency response if there is immediate danger.", "Preserve medical and message evidence.", "Approach women safety cell or local police station."],
    },
]


def fallback_analyze(complaint_text):
    text = complaint_text.lower()
    best = None
    best_score = 0

    for pattern in PATTERNS:
        matched = [term for term in pattern["terms"] if term in text]
        score = len(matched)
        if matched and _has_money(text) and ("Fraud" in pattern["category"] or "Scam" in pattern["category"]):
            score += 2
        if score > best_score:
            best = (pattern, matched)
            best_score = score

    analysis = _copy_default()
    if best:
        pattern, matched = best
        analysis.update(
            {
                "category": pattern["category"],
                "department": pattern["department"],
                "priority": pattern["priority"],
                "risk_level": pattern["risk_level"],
                "keywords": matched,
                "evidence_checklist": pattern["evidence"] + analysis["evidence_checklist"],
                "next_steps": pattern["steps"],
                "confidence": min(0.75, 0.35 + best_score * 0.08),
                "reasoning": "Local fallback matched complaint terms. Configure an AI provider for semantic analysis.",
                "needs_human_review": True,
            }
        )

    analysis["summary"] = _summarize(complaint_text, analysis["category"])
    analysis["entities"] = extract_entities(complaint_text)
    analysis["language"] = "mixed/unknown"
    return analysis


def extract_entities(text):
    lowered = text.lower()
    return {
        "amounts": re.findall(r"(?:₹\s?[\d,]+|rs\.?\s?[\d,]+|inr\s?[\d,]+|[\d,]+\s?(?:rupees|rupaye))", text, flags=re.I),
        "phone_numbers": re.findall(r"(?<!\d)(?:\+91[-\s]?)?[6-9]\d{9}(?!\d)", text),
        "urls": re.findall(r"https?://[^\s]+|www\.[^\s]+", text, flags=re.I),
        "upi_ids": re.findall(r"\b[\w.-]+@[\w.-]+\b", text),
        "emails": re.findall(r"\b[\w.+-]+@[\w.-]+\.[a-z]{2,}\b", text, flags=re.I),
        "dates": re.findall(r"\b\d{1,2}[/-]\d{1,2}(?:[/-]\d{2,4})?\b", text),
        "times": re.findall(r"\b\d{1,2}:\d{2}\s*(?:am|pm)?\b|\b\d{1,2}\s*(?:am|pm)\b", text, flags=re.I),
        "payment_methods": _detect_payment_methods(lowered),
        "counts": _detect_counts(text),
        "vehicle_numbers": _detect_vehicle_numbers(text),
        "social_handles": _detect_social_handles(text),
        "platforms": _detect_platforms(lowered),
        "document_ids": _detect_document_ids(text),
        "bank_references": _detect_bank_references(text),
        "bank_accounts": _detect_bank_accounts(text),
        "ip_addresses": _detect_ip_addresses(text),
        "person_names": _detect_person_names(text),
        "locations": _detect_locations(text),
    }


def _detect_payment_methods(text):
    methods = []
    for label, pattern in [
        ("UPI", r"\bupi\b|phonepe|gpay|google pay|paytm|bhim"),
        ("Card", r"\bcard\b|credit card|debit card|atm"),
        ("Net Banking", r"net banking|internet banking"),
        ("Wallet", r"\bwallet\b"),
        ("Bank Transfer", r"bank transfer|imps|neft|rtgs"),
    ]:
        if re.search(pattern, text, flags=re.I):
            methods.append(label)
    return methods


def _detect_counts(text):
    count_patterns = [
        r"\b\d+\s*(?:otp|otps|message|messages|sms|call|calls|email|emails|link|links|transaction|transactions|request|requests)\b(?:\s*(?:daily|per day|every day|a day|roz|har din))?",
        r"\b(?:daily|per day|every day|a day|roz|har din)\s+\d+\s*(?:otp|otps|message|messages|sms|call|calls|email|emails|link|links|transaction|transactions|request|requests)\b",
    ]
    matches = []
    for pattern in count_patterns:
        matches.extend(re.findall(pattern, text, flags=re.I))
    return _dedupe(matches)


def _detect_vehicle_numbers(text):
    return _dedupe(re.findall(r"\b[A-Z]{2}\s?\d{1,2}\s?[A-Z]{1,3}\s?\d{3,4}\b", text, flags=re.I))


def _detect_social_handles(text):
    handles = re.findall(r"(?<![\w.])@[\w_.]{3,30}\b", text)
    profile_urls = re.findall(r"(?:instagram|facebook|x|twitter|telegram|whatsapp)\.com/[^\s]+", text, flags=re.I)
    return _dedupe([*handles, *profile_urls])


def _detect_platforms(text):
    platforms = []
    for label, pattern in [
        ("Instagram", r"\binstagram\b|\binsta\b"),
        ("Facebook", r"\bfacebook\b|\bfb\b"),
        ("WhatsApp", r"\bwhatsapp\b"),
        ("Telegram", r"\btelegram\b"),
        ("X/Twitter", r"\btwitter\b|\bx\.com\b"),
        ("YouTube", r"\byoutube\b"),
        ("OLX", r"\bolx\b"),
        ("Amazon", r"\bamazon\b"),
        ("Flipkart", r"\bflipkart\b"),
    ]:
        if re.search(pattern, text, flags=re.I):
            platforms.append(label)
    return platforms


def _detect_document_ids(text):
    ids = []
    for label, pattern in [
        ("Aadhaar reference", r"\baadhaar\b(?:\s*(?:no|number|card))?(?:\s*[:#-]?\s*)?\d{4}\s?\d{4}\s?\d{4}"),
        ("PAN reference", r"\bpan\b(?:\s*(?:no|number|card))?(?:\s*[:#-]?\s*)?[A-Z]{5}\d{4}[A-Z]\b"),
        ("Passport reference", r"\bpassport\b(?:\s*(?:no|number))?(?:\s*[:#-]?\s*)?[A-Z]\d{7}\b"),
        ("IMEI reference", r"\bimei\b(?:\s*(?:no|number))?(?:\s*[:#-]?\s*)?\d{14,16}\b"),
    ]:
        ids.extend(re.findall(pattern, text, flags=re.I))
    return _dedupe(ids)


def _detect_bank_references(text):
    refs = []
    patterns = [
        r"\b(?:txn|transaction|utr|rrn|ref|reference)\s*(?:id|no|number)?\s*[:#-]?\s*[A-Z0-9-]{6,}\b",
        r"\baccount\s*(?:no|number)?\s*[:#-]?\s*(?:x{2,}|\*{2,})?\d{3,18}\b",
        r"\b(?:card)\s*(?:ending|last\s*four|last\s*4)?\s*(?:with|in)?\s*[:#-]?\s*(?:x{2,}|\*{2,})?\d{4}\b",
    ]
    for pattern in patterns:
        refs.extend(re.findall(pattern, text, flags=re.I))
    return _dedupe(refs)


def _detect_bank_accounts(text):
    patterns = [
        r"\b(?:account|a/c|acct)\s*(?:no|number)?\s*[:#-]?\s*(?:x{2,}|\*{2,})?\d{6,18}\b",
        r"\bifsc\s*[:#-]?\s*[A-Z]{4}0[A-Z0-9]{6}\b",
    ]
    matches = []
    for pattern in patterns:
        matches.extend(re.findall(pattern, text, flags=re.I))
    return _dedupe(matches)


def _detect_ip_addresses(text):
    return _dedupe(
        re.findall(
            r"\b(?:(?:25[0-5]|2[0-4]\d|1?\d?\d)\.){3}(?:25[0-5]|2[0-4]\d|1?\d?\d)\b",
            text,
        )
    )


def _detect_person_names(text):
    patterns = [
        r"\b(?:accused|suspect|person|ladka|aadmi|recruiter|caller)\s+(?:named|name|ka naam|called)?\s*[:\-]?\s*([A-Z][a-z]+(?:\s+[A-Z][a-z]+){0,2})\b",
        r"\b(?:mera naam|my name is|complainant name)\s*[:\-]?\s*([A-Z][a-z]+(?:\s+[A-Z][a-z]+){0,2})\b",
    ]
    names = []
    for pattern in patterns:
        names.extend(re.findall(pattern, text, flags=re.I))
    return _dedupe(names)


def _detect_locations(text):
    locations = []
    patterns = [
        r"\b(?:near|at|in|outside)\s+([A-Za-z][A-Za-z0-9 .'-]{2,40}?)(?=\s+(?:at|on|vehicle|car|bike|scooter|with|from|account|card|upi)\b|[,.]|$)",
        r"\b(?:sector|block)\s+[A-Z0-9-]{1,8}(?:\s+(?:market|mall|road|street|station))?\b",
        r"\b[A-Za-z0-9.'-]+\s+(?:road|street|nagar|market|mall|station|bus stand|airport)\b",
    ]
    for pattern in patterns:
        matches = re.findall(pattern, text, flags=re.I)
        locations.extend(matches)
    return _drop_contained_locations(_dedupe(_clean_locations(locations)))


def _clean_locations(locations):
    blocked_starts = ("account", "card", "upi", "transaction", "utr", "ref", "reference", "id ")
    cleaned = []
    for location in locations:
        normalized = " ".join(str(location).strip(" .,-").split())
        if not normalized:
            continue
        if normalized.lower().startswith(blocked_starts):
            continue
        cleaned.append(normalized)
    return cleaned


def _drop_contained_locations(locations):
    result = []
    for location in sorted(locations, key=len, reverse=True):
        lowered = location.lower()
        if any(lowered in existing.lower() for existing in result):
            continue
        result.append(location)
    return list(reversed(result))


def _dedupe(items):
    result = []
    seen = set()
    for item in items:
        normalized = " ".join(str(item).split())
        key = normalized.lower()
        if normalized and key not in seen:
            seen.add(key)
            result.append(normalized)
    return result


def _has_money(text):
    return bool(re.search(r"₹|rs\.?\s?\d+|inr\s?\d+|paise|money|amount|transaction", text, flags=re.I))


def _summarize(text, category):
    clean = " ".join(text.strip().split())
    if len(clean) > 190:
        clean = clean[:187].strip() + "..."
    return f"{clean} Classified as {category}."


def _copy_default():
    return {
        **DEFAULT_ANALYSIS,
        "keywords": list(DEFAULT_ANALYSIS["keywords"]),
        "evidence_checklist": list(DEFAULT_ANALYSIS["evidence_checklist"]),
        "next_steps": list(DEFAULT_ANALYSIS["next_steps"]),
        "entities": {key: list(value) for key, value in DEFAULT_ANALYSIS["entities"].items()},
    }
