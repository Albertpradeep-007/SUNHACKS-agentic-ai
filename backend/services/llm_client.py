from __future__ import annotations

from dataclasses import dataclass
from functools import lru_cache

from openai import OpenAI

from config import settings


@dataclass(frozen=True)
class LLMRuntime:
    provider: str
    model: str
    client: OpenAI


def _provider_order() -> list[str]:
    preferred = (settings.llm_provider or "groq").strip().lower()
    if preferred == "openai":
        return ["openai", "groq"]
    if preferred == "auto":
        return ["groq", "openai"]
    return ["groq", "openai"]


@lru_cache(maxsize=1)
def get_llm_runtime() -> LLMRuntime | None:
    for provider in _provider_order():
        if provider == "groq" and settings.groq_api_key:
            return LLMRuntime(
                provider="groq",
                model=settings.groq_model,
                client=OpenAI(api_key=settings.groq_api_key, base_url=settings.groq_base_url),
            )
        if provider == "openai" and settings.openai_api_key:
            return LLMRuntime(
                provider="openai",
                model=settings.openai_model,
                client=OpenAI(api_key=settings.openai_api_key),
            )
    return None


def chat_completion(system_prompt: str, user_prompt: str, temperature: float = 0.2) -> str | None:
    runtime = get_llm_runtime()
    if runtime is None:
        return None

    try:
        response = runtime.client.chat.completions.create(
            model=runtime.model,
            temperature=temperature,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt},
            ],
        )
        if not response.choices:
            return None
        content = response.choices[0].message.content
        return str(content).strip() if content else None
    except Exception:
        return None
