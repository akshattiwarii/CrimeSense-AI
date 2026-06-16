# CrimeSense AI

[![Python](https://img.shields.io/badge/Python-3.10%2B-18e2f2)](https://www.python.org/)
[![No external dependencies](https://img.shields.io/badge/dependencies-stdlib_only-25f7b5)](requirements.txt)
[![AI providers](https://img.shields.io/badge/AI-OpenAI%20%7C%20OpenRouter%20%7C%20Ollama-f33486)](#ai-provider-setup)

CrimeSense AI is a Python-based police complaint triage system for cyber cell and law-enforcement workflows. It accepts free-form complaint text in English, Hindi, or Hinglish, analyzes it with an AI/ML-style pipeline, and produces a structured complaint report with category, priority, evidence checklist, extracted entities, similarity matches, and dashboard analytics.

The project is built to run locally with the Python standard library. It can use a real LLM provider when configured, and it also includes an offline fallback engine so the demo still works without API access.

## Highlights

- Free-form complaint analyzer for police and cyber cell teams
- FIR-style optional intake fields for complainant, victim, incident, and cybercrime details
- Evidence image attachment support with PDF report output
- AI provider support for OpenAI, OpenAI-compatible APIs such as OpenRouter/Groq, and local Ollama
- Offline fallback classifier for demos and resilience
- Language detection for English, Hindi, Hinglish, and mixed complaints
- Entity extraction for amounts, UPI IDs, phone numbers, URLs, emails, bank references, IP addresses, platforms, document IDs, dates, times, locations, and repeated-count patterns
- Priority engine with rule-based escalation for high-risk signals
- Evidence suggestion engine based on crime type and extracted entities
- Similar complaint detection with links to stored complaint records
- Dashboard with total complaints, category distribution, weekly vertical bar trends, most common cybercrime, and recent complaint summaries
- Browser-based PDF report generation using print styles

## Screens

```text
Analyzer       -> Create structured police/cyber complaint reports
Dashboard      -> Track category distribution and weekly complaint trends
Complaint Page -> Open stored complaint records and similar cases
```

## AI/ML Pipeline

CrimeSense AI uses a practical hybrid pipeline:

```text
Raw complaint text + optional FIR fields + evidence images
      |
      v
[Input Layer]
  - normalize text
  - detect language
  - tokenize
  - record transliteration guidance
      |
      v
[Crime Classifier]
  - LLM provider when configured
  - offline fallback classifier when no provider is available
      |
      v
[Entity Extraction]
  - regex extraction
  - LLM JSON normalization
      |
      v
[Priority Engine]
  - amount thresholds
  - threat/blackmail/minor/missing/person-risk signals
  - phishing/payment/identity evidence signals
      |
      v
[Evidence Suggestion Engine]
  - crime-specific evidence checklist
      |
      v
[Similarity Detection + Storage + Dashboard]
```

### Implemented Modules

| Module | Status | Files |
| --- | --- | --- |
| Complaint ingestion and preprocessing | Done | `crimesense_ai/preprocessing.py` |
| Crime type classification | Done | `crimesense_ai/analyzer.py`, `crimesense_ai/providers.py`, `crimesense_ai/fallback.py` |
| Entity extraction | Done | `crimesense_ai/fallback.py`, `crimesense_ai/schema.py` |
| Priority assignment | Done | `crimesense_ai/priority.py` |
| Evidence suggestion engine | Done | `crimesense_ai/evidence.py` |
| Similarity detection | Done | `crimesense_ai/storage.py` |
| Dashboard analytics | Done | `dashboard.html`, `dashboard.js` |
| PDF report | Done | `index.html`, `styles.css` |

## Categories Handled

The AI path can generate dynamic categories. The offline fallback supports common categories such as:

- UPI / OTP / cyber financial fraud
- Phishing link / fake website
- Fake job scam
- Social media harassment
- Sextortion / online blackmail
- Cyberbullying / online threat
- Ransomware / malware
- Identity theft / SIM swap
- Theft / property crime
- Missing person
- Traffic accident
- Domestic violence / threat
- General police complaint

## Quick Start

### 1. Clone

```bash
git clone https://github.com/your-username/crimesense-ai.git
cd crimesense-ai
```

### 2. Optional virtual environment

```bash
python3 -m venv .venv
source .venv/bin/activate
```

### 3. Install requirements

```bash
pip install -r requirements.txt
```

The current version uses only the Python standard library, so this command is intentionally lightweight.

### 4. Run the web app

```bash
python3 app.py --serve
```

Open:

```text
http://127.0.0.1:8000
```

Dashboard:

```text
http://127.0.0.1:8000/dashboard.html
```

## AI Provider Setup

The app works offline with `local_fallback`, but real AI output needs a provider.

Copy the template:

```bash
cp .env.example .env
```

Never commit `.env`. It is ignored by `.gitignore`.

### OpenRouter / OpenAI-Compatible APIs

Use this for OpenRouter, Groq, Together, Fireworks, LM Studio, and similar `/chat/completions` APIs.

```text
AI_PROVIDER=openai_compatible
AI_BASE_URL=https://openrouter.ai/api/v1
AI_API_KEY=your_provider_key_here
AI_MODEL=nex-agi/nex-n2-pro:free
AI_HTTP_REFERER=http://127.0.0.1:8000
AI_APP_TITLE=CrimeSense AI
```

For OpenRouter, `AI_MODEL` must be an exact model slug from your account.

### OpenAI

```text
AI_PROVIDER=openai
OPENAI_API_KEY=your_openai_key_here
OPENAI_MODEL=gpt-4.1-mini
```

### Ollama

```bash
ollama pull llama3.1
```

```text
AI_PROVIDER=ollama
OLLAMA_BASE_URL=http://127.0.0.1:11434
OLLAMA_MODEL=llama3.1
```

Restart the Python server after changing `.env`.

## Command Line Usage

Analyze direct text:

```bash
python3 app.py --text "Mujhe KYC update ke naam par link bheja gaya aur OTP maang kar Rs. 5000 nikal liye."
```

Analyze stdin:

```bash
echo "i am getting 100 otps daily without my consent" | python3 app.py
```

## API Routes

### `GET /api/status`

Returns provider configuration status without exposing API keys.

### `POST /api/analyze`

Request:

```json
{
  "complaint_text": "Mujhe KYC update ke naam par link bheja gaya...",
  "fir_details": {
    "complainant_details": {},
    "victim_details": {},
    "incident_details": {},
    "cybercrime_details": {}
  },
  "attachments": []
}
```

Response includes:

- `category`
- `department`
- `priority`
- `risk_level`
- `summary`
- `keywords`
- `evidence_checklist`
- `next_steps`
- `possible_legal_sections`
- `entities`
- `confidence`
- `needs_human_review`
- `preprocessing`
- `similar_complaints`
- `complaint_id`

### `GET /api/dashboard`

Returns totals, category distribution, weekly trends, most common cybercrime, and recent complaints.

### `GET /api/complaint?id=101`

Returns a saved complaint record.

## Storage

Analyzed complaints are stored locally in:

```text
data/complaints.json
```

This file is ignored because complaint records may contain sensitive personal data. The app creates it automatically.

## Project Structure

```text
.
├── app.py                         # CLI and web server entrypoint
├── index.html                     # Analyzer UI
├── dashboard.html                 # Analytics dashboard
├── complaint.html                 # Stored complaint detail page
├── script.js                      # Analyzer frontend logic
├── dashboard.js                   # Dashboard chart/rendering logic
├── complaint.js                   # Complaint detail frontend logic
├── styles.css                     # Dark UI theme and print/PDF styles
├── requirements.txt               # Deployment/install placeholder
├── .env.example                   # Safe environment template
├── data/
│   └── .gitkeep                   # Runtime JSON data directory
├── tests/
│   └── smoke_test.py              # Offline smoke tests
└── crimesense_ai/
    ├── analyzer.py                # Main pipeline orchestration
    ├── config.py                  # Lightweight .env loader
    ├── evidence.py                # Evidence suggestion engine
    ├── fallback.py                # Offline classifier and regex NER
    ├── preprocessing.py           # Language detection and tokenization
    ├── priority.py                # Priority/risk escalation rules
    ├── prompts.py                 # LLM system prompt
    ├── providers.py               # OpenAI/OpenRouter/Ollama providers
    ├── schema.py                  # Strict analysis schema/defaults
    └── storage.py                 # JSON storage, dashboard stats, similarity
```

## Run Checks

Compile Python files:

```bash
python3 -B -m py_compile app.py crimesense_ai/*.py
```

Run smoke tests:

```bash
python3 tests/smoke_test.py
```

Manual server check:

```bash
python3 app.py --serve
```

Then open:

```text
http://127.0.0.1:8000/api/status
```

## GitHub Publishing Checklist

- Do not commit `.env`
- Do not commit `data/complaints.json`
- Do not commit `__pycache__` or `.pyc` files
- Rotate any API key that was ever pasted into chat, screenshots, or commits
- Add a repository description such as: `AI-powered police and cyber complaint triage dashboard`
- Add topics: `python`, `ai`, `cybercrime`, `law-enforcement`, `nlp`, `openrouter`, `dashboard`

## Production Roadmap

For real deployment, add:

- Authentication and role-based access control
- Encrypted database storage
- Audit logs and officer action history
- PII redaction and retention policies
- Case status workflow
- PostgreSQL + SQLAlchemy
- HTTPS reverse proxy
- Rate limiting
- File upload scanning and storage limits
- Fine-tuned multilingual BERT classifier
- spaCy custom NER / EntityRuler
- Human approval workflow before FIR registration

## Important Disclaimer

CrimeSense AI is a triage and decision-support tool. It does not replace police judgment, legal review, FIR registration rules, or court/legal interpretation. Suggested departments, priorities, and legal sections must be reviewed by authorized officers.
