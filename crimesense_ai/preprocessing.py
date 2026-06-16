import re


HINDI_SCRIPT_RE = re.compile(r"[\u0900-\u097F]")
TOKEN_RE = re.compile(r"[\w@./:-]+", re.UNICODE)

HINGLISH_TERMS = {
    "mujhe", "mera", "meri", "mere", "paise", "nikal", "nikal liye",
    "bheja", "maang", "naam", "par", "se", "hua", "hai", "nahi",
    "dhamki", "pareshan", "chori", "gumshuda", "rupaye", "roz",
}


def preprocess_complaint(text):
    raw_text = str(text or "")
    normalized_text = normalize_text(raw_text)
    language = detect_language(raw_text, normalized_text)
    tokens = tokenize(normalized_text)

    return {
        "raw_text": raw_text,
        "clean_text": normalized_text,
        "lower_text": normalized_text.lower(),
        "language": language,
        "transliteration": transliteration_note(language),
        "tokens": tokens,
        "token_count": len(tokens),
    }


def normalize_text(text):
    text = str(text or "").replace("\u00a0", " ")
    text = re.sub(r"[\r\t]+", " ", text)
    text = re.sub(r"\s+", " ", text)
    return text.strip()


def detect_language(raw_text, normalized_text=None):
    normalized_text = normalized_text if normalized_text is not None else normalize_text(raw_text)
    lowered = normalized_text.lower()
    has_devanagari = bool(HINDI_SCRIPT_RE.search(normalized_text))
    english_words = re.findall(r"\b[a-z]{3,}\b", lowered)
    hinglish_hits = sum(1 for term in HINGLISH_TERMS if term in lowered)

    if has_devanagari and english_words:
        return "Hindi/English mixed"

    if has_devanagari:
        return "Hindi"

    if hinglish_hits >= 2:
        return "Hinglish"

    if english_words:
        return "English"

    return "unknown"


def tokenize(text):
    return [token.lower() for token in TOKEN_RE.findall(text or "") if token.strip()]


def transliteration_note(language):
    if language in {"Hindi", "Hindi/English mixed"}:
        return "Recommended for production: transliterate Hindi text to Latin/English using indic-transliteration or a translation API before model training."
    if language == "Hinglish":
        return "Already romanized Hinglish; normalize spelling variants during training."
    return "Not required for current text."
