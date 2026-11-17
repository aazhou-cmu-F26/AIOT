"""Thin OpenAI-compatible client for local Ollama inference.

Same interface as OpenRouterClient so runner scripts can swap backends
without changing their call structure. Ollama exposes an OpenAI-compatible
API at http://localhost:11434/v1.

No API key is needed; "ollama" is passed as a placeholder because the
OpenAI library requires a non-empty value.
"""

from __future__ import annotations

from driver.openrouter_client import Completion

DEFAULT_BASE_URL = "http://localhost:11434/v1"


class OllamaClient:
    """One chat-completion call per ``complete``; no retries, no tools."""

    def __init__(self, base_url: str = DEFAULT_BASE_URL, timeout_s: float = 600.0):
        from openai import OpenAI

        self._client = OpenAI(
            base_url=base_url,
            api_key="ollama",
            timeout=timeout_s,
            max_retries=0,
        )

    def complete(self, model: str, messages: list[dict], sampling: dict) -> Completion:
        resp = self._client.chat.completions.create(
            model=model, messages=messages, **sampling
        )
        choice = resp.choices[0] if resp.choices else None
        return Completion(
            text=(choice.message.content or "") if choice else "",
            requested_model=model,
            resolved_model=resp.model,
            provider="ollama-local",
            response_id=resp.id,
            finish_reason=choice.finish_reason if choice else None,
            usage=resp.usage.model_dump() if resp.usage else {},
            created=resp.created,
        )
