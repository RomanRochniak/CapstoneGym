import hashlib
import logging
from dataclasses import dataclass
from typing import Any, Dict, List, Optional

import httpx
from django.conf import settings
from django.core.cache import cache

logger = logging.getLogger(__name__)

SYSTEM_PROMPT = (
    "You are RoshaClub AI Fitness Assistant. "
    "You help with gym motivation, general training guidance, and explain how the RoshaClub site works "
    "(programs, memberships, trainers, community). "
    "You MUST use only the provided SITE_CONTEXT for names, prices, programs, trainers, and memberships. "
    "If something is not in SITE_CONTEXT, say you don't know and suggest where on the site to check. "
    "Rules: do NOT provide medical advice, diagnosis, or injury treatment. "
    "If the user asks for a personalized plan, diet plan, supplements for health conditions, or anything medical, "
    "recommend contacting a real trainer. "
    "Keep answers short, practical, and professional."
)


@dataclass(frozen=True)
class LLMResponse:
    text: str
    provider: str
    model: str
    meta: Dict[str, Any]


class BaseProvider:
    name: str
    model: str

    def chat(self, messages: List[Dict[str, str]]) -> LLMResponse:
        raise NotImplementedError


class OllamaProvider(BaseProvider):
    def __init__(self) -> None:
        self.name = "ollama"
        self.model = getattr(settings, "OLLAMA_MODEL", "qwen2.5:7b")
        self.base_url = getattr(settings, "OLLAMA_BASE_URL", "http://127.0.0.1:11434").rstrip("/")

    def chat(self, messages: List[Dict[str, str]]) -> LLMResponse:
        timeout = httpx.Timeout(getattr(settings, "AI_TIMEOUT_SECONDS", 20))

        url = f"{self.base_url}/v1/chat/completions"
        payload = {
            "model": self.model,
            "messages": messages,
            "stream": False,
            "temperature": 0.7,
        }

        with httpx.Client(timeout=timeout) as client:
            r = client.post(url, json=payload)
            r.raise_for_status()
            data = r.json()

        text = ""
        choices = data.get("choices") or []
        if choices:
            msg = (choices[0].get("message") or {})
            text = (msg.get("content") or "").strip()

        if not text:
            text = "I didn't get a response. Please try again."

        return LLMResponse(text=text, provider=self.name, model=self.model, meta={})


class GeminiProvider(BaseProvider):
    def __init__(self) -> None:
        self.name = "gemini"
        self.model = getattr(settings, "GEMINI_MODEL", "gemini-1.5-flash")
        self.api_key = getattr(settings, "GEMINI_API_KEY", "")

    def chat(self, messages: List[Dict[str, str]]) -> LLMResponse:
        if not self.api_key:
            raise RuntimeError("GEMINI_API_KEY is missing")

        timeout = httpx.Timeout(getattr(settings, "AI_TIMEOUT_SECONDS", 20))
        url = f"https://generativelanguage.googleapis.com/v1beta/models/{self.model}:generateContent"
        params = {"key": self.api_key}

        prompt = self._messages_to_prompt(messages)
        payload = {"contents": [{"parts": [{"text": prompt}]}]}

        with httpx.Client(timeout=timeout) as client:
            r = client.post(url, params=params, json=payload)
            r.raise_for_status()
            data = r.json()

        text = ""
        candidates = data.get("candidates") or []
        if candidates:
            parts = (((candidates[0].get("content") or {}).get("parts")) or [])
            if parts:
                text = (parts[0].get("text") or "").strip()

        if not text:
            text = "I didn't get a response. Please try again."

        return LLMResponse(text=text, provider=self.name, model=self.model, meta={})

    def _messages_to_prompt(self, messages: List[Dict[str, str]]) -> str:
        lines: List[str] = []
        for m in messages:
            role = m.get("role")
            content = m.get("content", "")
            if role == "system":
                lines.append(f"SYSTEM: {content}")
            elif role == "user":
                lines.append(f"USER: {content}")
            else:
                lines.append(f"ASSISTANT: {content}")
        lines.append("ASSISTANT:")
        return "\n".join(lines)


class LLMService:
    def __init__(self) -> None:
        self.provider = self._get_provider()

    def _get_provider(self) -> BaseProvider:
        p = (getattr(settings, "AI_PROVIDER", "ollama") or "ollama").lower().strip()
        if p == "gemini":
            return GeminiProvider()
        return OllamaProvider()

    def _cache_key(self, messages: List[Dict[str, str]]) -> str:
        raw = "|".join([f"{m.get('role')}:{m.get('content')}" for m in messages[-12:]])
        h = hashlib.sha256(raw.encode("utf-8")).hexdigest()[:24]
        return f"ai:resp:{self.provider.name}:{self.provider.model}:{h}"

    def generate_response(
        self,
        user_message: str,
        conversation_history: List[Dict[str, str]],
        site_context: Optional[Dict[str, Any]] = None,
        suggestions: Optional[Dict[str, Any]] = None,
    ) -> LLMResponse:
        site_context_text = ""
        if site_context:
            site_context_text = f"SITE_CONTEXT (authoritative, do not invent): {site_context}"

        suggestions_text = ""
        if suggestions:
            suggestions_text = f"SUGGESTIONS (candidates picked by backend): {suggestions}"

        system_block = SYSTEM_PROMPT
        if site_context_text:
            system_block = system_block + " " + site_context_text
        if suggestions_text:
            system_block = system_block + " " + suggestions_text

        messages = [{"role": "system", "content": system_block}] + conversation_history + [
            {"role": "user", "content": user_message}
        ]

        ck = self._cache_key(messages)
        cached = cache.get(ck)
        if cached:
            return LLMResponse(
                text=cached["text"],
                provider=cached["provider"],
                model=cached["model"],
                meta=cached.get("meta", {}),
            )

        try:
            resp = self.provider.chat(messages)
        except httpx.TimeoutException:
            logger.warning("AI timeout provider=%s model=%s", self.provider.name, self.provider.model)
            raise
        except Exception:
            logger.exception("AI provider error provider=%s model=%s", self.provider.name, self.provider.model)
            raise

        cache.set(
            ck,
            {"text": resp.text, "provider": resp.provider, "model": resp.model, "meta": resp.meta},
            timeout=getattr(settings, "AI_CACHE_SECONDS", 120),
        )
        return resp