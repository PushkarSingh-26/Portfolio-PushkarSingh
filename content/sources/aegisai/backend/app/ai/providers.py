"""LLM provider abstraction (Phase 13.2).

No provider lock-in. All providers are called over their REST APIs using
`requests` (no heavy SDKs), selected by `AI_PROVIDER`. When the provider is
"none" (default) or unavailable, `get_provider()` returns None and the response
generator falls back to a deterministic, evidence-grounded summary.
"""

import logging

import requests

from backend.app.config import get_settings

log = logging.getLogger("ai.providers")

DEFAULT_MODELS = {
    "gemini": "gemini-1.5-flash",
    "openai": "gpt-4o-mini",
    "ollama": "llama3",
}
TIMEOUT = 60


class LLMProvider:
    name = "base"

    def complete(self, system: str, prompt: str) -> str:  # pragma: no cover
        raise NotImplementedError

    def available(self) -> bool:  # pragma: no cover
        return True


class GeminiProvider(LLMProvider):
    name = "gemini"

    def __init__(self, api_key: str, model: str, temperature: float):
        self.api_key, self.model, self.temperature = api_key, model, temperature

    def available(self) -> bool:
        return bool(self.api_key)

    def complete(self, system: str, prompt: str) -> str:
        url = (f"https://generativelanguage.googleapis.com/v1beta/models/"
               f"{self.model}:generateContent?key={self.api_key}")
        body = {
            "system_instruction": {"parts": [{"text": system}]},
            "contents": [{"parts": [{"text": prompt}]}],
            "generationConfig": {"temperature": self.temperature},
        }
        r = requests.post(url, json=body, timeout=TIMEOUT)
        r.raise_for_status()
        return r.json()["candidates"][0]["content"]["parts"][0]["text"]


class OpenAIProvider(LLMProvider):
    name = "openai"

    def __init__(self, api_key: str, base_url: str, model: str, temperature: float):
        self.api_key, self.base_url = api_key, base_url.rstrip("/")
        self.model, self.temperature = model, temperature

    def available(self) -> bool:
        return bool(self.api_key)

    def complete(self, system: str, prompt: str) -> str:
        r = requests.post(
            f"{self.base_url}/chat/completions",
            headers={"Authorization": f"Bearer {self.api_key}"},
            json={"model": self.model, "temperature": self.temperature,
                  "messages": [{"role": "system", "content": system},
                               {"role": "user", "content": prompt}]},
            timeout=TIMEOUT,
        )
        r.raise_for_status()
        return r.json()["choices"][0]["message"]["content"]


class OllamaProvider(LLMProvider):
    name = "ollama"

    def __init__(self, url: str, model: str, temperature: float):
        self.url, self.model, self.temperature = url.rstrip("/"), model, temperature

    def available(self) -> bool:
        try:
            requests.get(f"{self.url}/api/tags", timeout=3).raise_for_status()
            return True
        except requests.RequestException:
            return False

    def complete(self, system: str, prompt: str) -> str:
        r = requests.post(
            f"{self.url}/api/chat",
            json={"model": self.model, "stream": False,
                  "options": {"temperature": self.temperature},
                  "messages": [{"role": "system", "content": system},
                               {"role": "user", "content": prompt}]},
            timeout=TIMEOUT,
        )
        r.raise_for_status()
        return r.json()["message"]["content"]


def get_provider() -> LLMProvider | None:
    """Return the configured provider, or None to use the deterministic fallback."""
    s = get_settings()
    provider = (s.ai_provider or "none").lower()
    if provider == "none":
        return None
    model = s.ai_model or DEFAULT_MODELS.get(provider, "")
    try:
        if provider == "gemini":
            p = GeminiProvider(s.gemini_api_key, model, s.ai_temperature)
        elif provider == "openai":
            p = OpenAIProvider(s.openai_api_key, s.openai_base_url, model, s.ai_temperature)
        elif provider == "ollama":
            p = OllamaProvider(s.ollama_url, model, s.ai_temperature)
        else:
            return None
    except Exception as exc:  # noqa: BLE001
        log.warning("provider init failed: %s", exc)
        return None
    return p if p.available() else None
