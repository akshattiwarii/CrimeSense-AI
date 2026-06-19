from datetime import datetime, timedelta, timezone


SAMPLE_FIRS = [
    ("FIR001", "UPI Fraud", "I received a call from a person claiming to be a bank representative. He asked me to approve a UPI collect request and Rs. 15000 was deducted from my account.", 15000, "High"),
    ("FIR002", "Phishing", "I received a fake KYC update link through SMS. After entering my banking credentials, Rs. 8500 was withdrawn from my account.", 8500, "High"),
    ("FIR003", "Fake Job Scam", "I applied for an online job and was asked to pay a registration fee of Rs. 5000. After payment, the recruiter stopped responding.", 5000, "Medium"),
    ("FIR004", "Identity Theft", "Someone created a fake Instagram profile using my photos and is impersonating me online.", 0, "High"),
    ("FIR005", "Social Media Harassment", "A person is sending abusive messages and threatening me repeatedly through Instagram.", 0, "High"),
    ("FIR006", "Online Shopping Fraud", "I ordered a mobile phone worth Rs. 12000 from an online seller but received a fake product and the seller is not responding.", 12000, "Medium"),
    ("FIR007", "Credit Card Fraud", "Unauthorized transactions worth Rs. 22000 were made using my credit card without my permission.", 22000, "High"),
    ("FIR008", "Lottery Scam", "I received a message claiming that I won a lottery and was asked to pay processing fees of Rs. 3000.", 3000, "Medium"),
    ("FIR009", "Fake Loan App", "I installed a loan application and provided my details. The app is now threatening me and demanding money.", 10000, "High"),
    ("FIR010", "UPI Fraud", "I scanned a QR code sent by a seller and Rs. 7000 was deducted instead of being credited.", 7000, "High"),
    ("FIR011", "Phishing", "I received an email appearing to be from my bank. After logging in through the provided link, Rs. 18000 was stolen.", 18000, "High"),
    ("FIR012", "Cyber Stalking", "An unknown individual is tracking my online activities and sending me messages containing personal information.", 0, "High"),
    ("FIR013", "Fake Investment Scam", "I invested Rs. 50000 in an online trading platform promising high returns. The platform disappeared after receiving the money.", 50000, "High"),
    ("FIR014", "Identity Theft", "My PAN card details were used without permission to open financial accounts.", 0, "High"),
    ("FIR015", "Online Gaming Fraud", "I purchased gaming credits worth Rs. 4000 from an online seller but never received them.", 4000, "Medium"),
    ("FIR016", "Fake Customer Care Scam", "I searched for a customer care number online and called it. The person convinced me to install an app and Rs. 25000 was stolen.", 25000, "High"),
    ("FIR017", "WhatsApp Account Hijacking", "My WhatsApp account was taken over after I shared a verification code with someone pretending to be my friend.", 0, "High"),
    ("FIR018", "E-commerce Refund Scam", "A fraudster pretending to be a refund agent asked me to share banking details and withdrew Rs. 9000.", 9000, "High"),
    ("FIR019", "Fake Scholarship Scam", "I received a scholarship offer and was asked to pay verification charges of Rs. 2000. After payment, communication stopped.", 2000, "Low"),
    ("FIR020", "Ransomware Attack", "My computer files were encrypted by malware and I was asked to pay Rs. 30000 in cryptocurrency to recover them.", 30000, "High"),
]


def sample_complaints():
    now = datetime.now(timezone.utc)
    records = []

    for index, (complaint_id, category, text, amount, priority) in enumerate(SAMPLE_FIRS):
        timestamp = now - timedelta(days=(len(SAMPLE_FIRS) - index - 1) % 7, hours=index % 6)
        records.append(
            {
                "id": complaint_id,
                "timestamp": timestamp.isoformat(),
                "category": category,
                "department": _department_for(category),
                "priority": priority,
                "risk_level": priority,
                "summary": text,
                "keywords": _keywords_for(category, text),
                "evidence_checklist": _evidence_for(category),
                "next_steps": _steps_for(category),
                "possible_legal_sections": [
                    "Officer/legal review required before applying final FIR sections."
                ],
                "entities": _entities_for(category, amount, text),
                "fir_details": {},
                "attachments": [],
                "reasoning": "Seed demo FIR record for initial dashboard analytics.",
                "confidence": 0.82,
                "needs_human_review": True,
                "similar_complaints": [],
                "original_complaint": text,
                "engine": "seed_data",
                "engine_display": "Seed demo data",
                "provider_status_display": "Demo FIR sample",
                "preprocessing": {
                    "language_detected": "English",
                    "clean_text": text,
                    "token_count": len(text.split()),
                    "tokens": text.lower().split()[:40],
                    "transliteration": "Not required for current text.",
                },
            }
        )

    return records


def _department_for(category):
    lowered = category.lower()
    if any(term in lowered for term in ["upi", "phishing", "cyber", "ransomware", "identity", "whatsapp"]):
        return "Cyber Cell"
    if any(term in lowered for term in ["credit card", "loan", "investment", "refund", "lottery"]):
        return "Cyber Cell / Economic Offences Wing"
    return "Cyber Cell / Local Police Station"


def _keywords_for(category, text):
    words = [part.strip(".,").lower() for part in category.split()]
    for term in ["upi", "kyc", "instagram", "credit card", "loan", "ransomware", "whatsapp", "refund"]:
        if term in text.lower():
            words.append(term)
    return list(dict.fromkeys(words))[:8]


def _evidence_for(category):
    lowered = category.lower()
    if any(term in lowered for term in ["upi", "credit card", "loan", "investment", "refund", "shopping", "gaming"]):
        return ["Transaction screenshot", "Bank SMS/email alert", "Payment reference ID", "Suspect contact or account details"]
    if "phishing" in lowered:
        return ["Suspicious URL", "SMS/email screenshot", "Browser history", "Bank transaction proof"]
    if any(term in lowered for term in ["identity", "social", "stalking", "whatsapp"]):
        return ["Profile URL or username", "Chat screenshots", "Date/time of messages", "Account recovery details if available"]
    if "ransomware" in lowered:
        return ["Ransom note screenshot", "Encrypted file samples", "Crypto wallet/payment demand", "Device details"]
    return ["Complaint text", "Screenshots", "Date/time", "Suspect contact details"]


def _steps_for(category):
    lowered = category.lower()
    if any(term in lowered for term in ["upi", "phishing", "credit card", "refund", "investment", "loan"]):
        return ["Contact bank/payment provider immediately.", "Collect transaction references.", "Preserve all messages and screenshots."]
    if "ransomware" in lowered:
        return ["Disconnect affected device from network.", "Do not delete evidence.", "Escalate to cyber forensic desk."]
    return ["Preserve evidence.", "Record suspect identifiers.", "Route to cyber cell for review."]


def _entities_for(category, amount, text):
    return {
        "amounts": [f"Rs. {amount}"] if amount else [],
        "phone_numbers": [],
        "urls": ["fake KYC/update link"] if "link" in text.lower() else [],
        "upi_ids": [],
        "emails": [],
        "dates": [],
        "times": [],
        "payment_methods": _payment_methods(category, text),
        "counts": [],
        "vehicle_numbers": [],
        "social_handles": [],
        "platforms": _platforms(text),
        "document_ids": ["PAN reference"] if "PAN" in text else [],
        "bank_references": [],
        "bank_accounts": [],
        "ip_addresses": [],
        "person_names": [],
        "locations": [],
    }


def _payment_methods(category, text):
    lowered = f"{category} {text}".lower()
    methods = []
    if "upi" in lowered:
        methods.append("UPI")
    if "credit card" in lowered:
        methods.append("Card")
    if any(term in lowered for term in ["bank", "withdrawn", "transaction"]):
        methods.append("Bank Transfer")
    if "cryptocurrency" in lowered:
        methods.append("Cryptocurrency")
    return methods


def _platforms(text):
    lowered = text.lower()
    platforms = []
    for label in ["Instagram", "WhatsApp"]:
        if label.lower() in lowered:
            platforms.append(label)
    return platforms
