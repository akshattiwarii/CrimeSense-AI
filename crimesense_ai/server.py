import json
import os
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from urllib.parse import parse_qs, urlparse

from .analyzer import analyze_complaint
from .providers import build_provider
from .storage import dashboard_stats, find_complaint, find_similar_complaints, save_complaint


class CrimeSenseHandler(SimpleHTTPRequestHandler):
    def do_GET(self):
        path = urlparse(self.path).path

        if path == "/api/status":
            try:
                provider = build_provider()
            except Exception as exc:
                self._send_json(
                    200,
                {
                    "ai_provider": os.getenv("AI_PROVIDER", "openai"),
                    "ai_configured": False,
                    "ai_model": None,
                    "ai_engine": "local_fallback",
                    "ai_engine_display": "Local fallback",
                    "provider_error": str(exc),
                    "provider_status_display": str(exc),
                },
            )
                return

            self._send_json(
                200,
                {
                    "ai_provider": os.getenv("AI_PROVIDER", "openai"),
                    "ai_configured": provider.available,
                    "ai_model": provider.model,
                    "ai_engine": provider.engine_name,
                    "ai_engine_display": _format_engine_display(provider.engine_name),
                    "provider_error": None if provider.available else provider.unavailable_reason,
                    "provider_status_display": "Connected" if provider.available else provider.unavailable_reason,
                },
            )
            return

        if path == "/api/dashboard":
            self._send_json(200, dashboard_stats())
            return

        if path == "/api/complaint":
            query = parse_qs(urlparse(self.path).query)
            complaint_id = (query.get("id") or [""])[0]
            record = find_complaint(complaint_id)
            if not record:
                self._send_json(404, {"error": "Complaint not found."})
                return
            self._send_json(200, record)
            return

        super().do_GET()

    def do_POST(self):
        if self.path != "/api/analyze":
            self.send_error(404, "Not found")
            return

        try:
            length = int(self.headers.get("Content-Length", "0"))
            payload = json.loads(self.rfile.read(length).decode("utf-8"))
            complaint_text = str(payload.get("complaint_text", ""))
            fir_details = payload.get("fir_details", {})
            attachments = payload.get("attachments", [])
            enriched_text = _build_enriched_complaint_text(complaint_text, fir_details, attachments)
            result = analyze_complaint(enriched_text)
            result["fir_details"] = fir_details if isinstance(fir_details, dict) else {}
            result["attachments"] = attachments if isinstance(attachments, list) else []
            result["similar_complaints"] = find_similar_complaints(result)
            saved_record = save_complaint(result)
            result["complaint_id"] = saved_record.get("id")
            self._send_json(200, result)
        except ValueError as exc:
            self._send_json(400, {"error": str(exc)})
        except json.JSONDecodeError:
            self._send_json(400, {"error": "Invalid JSON request."})
        except Exception as exc:
            self._send_json(500, {"error": "Analysis failed.", "detail": str(exc)})

    def _send_json(self, status_code, payload):
        body = json.dumps(payload, ensure_ascii=False, indent=2).encode("utf-8")
        self.send_response(status_code)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)


def run(host="127.0.0.1", port=8000):
    server = ThreadingHTTPServer((host, port), CrimeSenseHandler)
    print(f"CrimeSense AI running at http://{host}:{port}")
    print("Configure AI_PROVIDER in .env for real AI analysis. Without it, local fallback is used.")
    server.serve_forever()


def _format_engine_display(engine):
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


def _build_enriched_complaint_text(complaint_text, fir_details, attachments):
    if not isinstance(fir_details, dict):
        fir_details = {}

    lines = ["FIR-style complaint intake details:"]
    for section, values in fir_details.items():
        if not isinstance(values, dict):
            continue
        lines.append(f"\n{section.replace('_', ' ').title()}:")
        for key, value in values.items():
            if value:
                lines.append(f"- {key.replace('_', ' ').title()}: {value}")

    if attachments:
        lines.append("\nAttached Evidence Images:")
        for attachment in attachments:
            if isinstance(attachment, dict):
                lines.append(f"- {attachment.get('name', 'image')} ({attachment.get('type', 'image')})")

    lines.append("\nComplaint Narrative:")
    lines.append(complaint_text)
    return "\n".join(lines)
