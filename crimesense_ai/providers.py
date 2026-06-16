import json
import os
import re
import urllib.error
import urllib.request

from .prompts import SYSTEM_PROMPT, build_user_prompt
from .schema import ANALYSIS_SCHEMA


class AIProviderError(RuntimeError):
    pass


def build_provider():
    provider_name = os.getenv("AI_PROVIDER", "openai").strip().lower()

    if provider_name == "openai":
        return OpenAIProvider()

    if provider_name == "openai_compatible":
        return OpenAICompatibleProvider()

    if provider_name == "ollama":
        return OllamaProvider()

    raise AIProviderError(f"Unsupported AI_PROVIDER: {provider_name}")


class BaseProvider:
    provider_name = "base"

    @property
    def engine_name(self):
        return f"{self.provider_name}:{self.model}"


class OpenAIProvider(BaseProvider):
    provider_name = "openai"

    def __init__(self, api_key=None, model=None, timeout=45):
        self.api_key = api_key or os.getenv("OPENAI_API_KEY")
        self.model = model or os.getenv("OPENAI_MODEL", "gpt-4.1-mini")
        self.timeout = timeout

    @property
    def available(self):
        return bool(self.api_key)

    @property
    def unavailable_reason(self):
        return "OPENAI_API_KEY not configured."

    def analyze(self, complaint_text):
        if not self.available:
            raise AIProviderError(self.unavailable_reason)

        payload = {
            "model": self.model,
            "instructions": SYSTEM_PROMPT,
            "input": build_user_prompt(complaint_text),
            "text": {
                "format": {
                    "type": "json_schema",
                    "name": "crime_complaint_analysis",
                    "schema": ANALYSIS_SCHEMA,
                    "strict": True,
                }
            },
        }

        data = post_json(
            "https://api.openai.com/v1/responses",
            payload,
            {"Authorization": f"Bearer {self.api_key}"},
            self.timeout,
            "OpenAI",
        )

        output_text = self._extract_output_text(data)
        if not output_text:
            raise AIProviderError("OpenAI response did not contain output text.")

        return parse_json_text(output_text, "OpenAI")

    @staticmethod
    def _extract_output_text(data):
        chunks = []
        for item in data.get("output", []):
            for content in item.get("content", []):
                if content.get("type") == "output_text":
                    chunks.append(content.get("text", ""))
        return "".join(chunks).strip()


class OpenAICompatibleProvider(BaseProvider):
    provider_name = "openai_compatible"

    def __init__(self, api_key=None, model=None, base_url=None, timeout=45):
        self.api_key = api_key or os.getenv("AI_API_KEY")
        self.model = model or os.getenv("AI_MODEL", "meta-llama/llama-3.1-8b-instruct")
        self.base_url = (base_url or os.getenv("AI_BASE_URL", "")).rstrip("/")
        self.timeout = timeout

    @property
    def available(self):
        return bool(self.api_key and self.base_url and self.model)

    @property
    def unavailable_reason(self):
        return "AI_API_KEY, AI_BASE_URL, or AI_MODEL is not configured."

    def analyze(self, complaint_text):
        if not self.available:
            raise AIProviderError(self.unavailable_reason)

        payload = {
            "model": self.model,
            "messages": [
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": build_user_prompt(complaint_text)},
            ],
            "temperature": 0.1,
            "response_format": {"type": "json_object"},
        }

        headers = {"Authorization": f"Bearer {self.api_key}"}
        referer = os.getenv("AI_HTTP_REFERER") or os.getenv("OPENROUTER_HTTP_REFERER")
        app_title = os.getenv("AI_APP_TITLE") or os.getenv("OPENROUTER_APP_TITLE")
        if referer:
            headers["HTTP-Referer"] = referer
        if app_title:
            headers["X-Title"] = app_title

        data = post_json(
            f"{self.base_url}/chat/completions",
            payload,
            headers,
            self.timeout,
            "AI provider",
        )

        try:
            content = data["choices"][0]["message"]["content"]
        except (KeyError, IndexError, TypeError) as exc:
            raise AIProviderError("AI provider response did not contain chat content.") from exc

        return parse_json_text(content, "AI provider")


class OllamaProvider(BaseProvider):
    provider_name = "ollama"

    def __init__(self, model=None, base_url=None, timeout=120):
        self.model = model or os.getenv("OLLAMA_MODEL", "llama3.1")
        self.base_url = (base_url or os.getenv("OLLAMA_BASE_URL", "http://127.0.0.1:11434")).rstrip("/")
        self.timeout = timeout

    @property
    def available(self):
        return bool(self.model and self.base_url)

    @property
    def unavailable_reason(self):
        return "OLLAMA_MODEL or OLLAMA_BASE_URL is not configured."

    def analyze(self, complaint_text):
        if not self.available:
            raise AIProviderError(self.unavailable_reason)

        payload = {
            "model": self.model,
            "stream": False,
            "format": "json",
            "messages": [
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": build_user_prompt(complaint_text)},
            ],
        }

        data = post_json(
            f"{self.base_url}/api/chat",
            payload,
            {},
            self.timeout,
            "Ollama",
        )

        try:
            content = data["message"]["content"]
        except (KeyError, TypeError) as exc:
            raise AIProviderError("Ollama response did not contain chat content.") from exc

        return parse_json_text(content, "Ollama")


def post_json(url, payload, headers, timeout, provider_label):
    request_headers = {"Content-Type": "application/json", **headers}
    request = urllib.request.Request(
        url,
        data=json.dumps(payload).encode("utf-8"),
        headers=request_headers,
        method="POST",
    )

    try:
        with urllib.request.urlopen(request, timeout=timeout) as response:
            return json.loads(response.read().decode("utf-8"))
    except urllib.error.HTTPError as exc:
        detail = exc.read().decode("utf-8", errors="replace")
        raise AIProviderError(f"{provider_label} API error {exc.code}: {detail}") from exc
    except urllib.error.URLError as exc:
        raise AIProviderError(f"{provider_label} network error: {exc.reason}") from exc


def parse_json_text(text, provider_label):
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        match = re.search(r"\{.*\}", text, flags=re.S)
        if not match:
            raise AIProviderError(f"{provider_label} response was not valid JSON.")
        try:
            return json.loads(match.group(0))
        except json.JSONDecodeError as exc:
            raise AIProviderError(f"{provider_label} response was not valid JSON.") from exc
