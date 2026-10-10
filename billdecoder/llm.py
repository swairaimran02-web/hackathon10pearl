"""Provider-agnostic LLM client for the allowed models.

Supports the three allowed providers (Google, OpenAI, Anthropic), an automatic
free-tier backup model, retry with backoff, and on-disk caching of results.
"""
from __future__ import annotations

import base64
import logging
import time

from .cache import DiskCache
from .config import Settings
from .prompts import PROMPT_VERSION

logger = logging.getLogger(__name__)


class LLMError(RuntimeError):
    pass


def _is_rate_limit(err: Exception) -> bool:
    text = str(err).lower()
    return any(
        marker in text
        for marker in ("429", "rate limit", "quota", "resource_exhausted", "overloaded")
    )


class LLMClient:
    def __init__(self, settings: Settings):
        self.settings = settings
        self.cache = DiskCache(settings.cache_dir)

    # ------------------------------------------------------------------ public
    def generate(
        self,
        prompt: str,
        image_bytes: bytes | None = None,
        mime_type: str | None = None,
        json_mode: bool = False,
        tag: str = "generic",
    ) -> str:
        """Return the model's text, using the cache and a fallback model."""
        image_key = ""
        if image_bytes:
            image_key = DiskCache.make_key(
                mime_type or "", str(len(image_bytes)), image_bytes[:4096].hex()
            )
        cache_key = DiskCache.make_key(
            PROMPT_VERSION,
            self.settings.provider,
            self.settings.model,
            tag,
            "json" if json_mode else "text",
            prompt,
            image_key,
        )
        cached = self.cache.get(cache_key)
        if cached is not None:
            logger.debug("cache hit for %s", cache_key)
            return cached

        models = [self.settings.model]
        if self.settings.fallback_model and self.settings.fallback_model != self.settings.model:
            models.append(self.settings.fallback_model)

        last_error: Exception | None = None
        for model in models:
            for attempt in range(self.settings.max_retries):
                try:
                    text = self._call_once(model, prompt, image_bytes, mime_type, json_mode)
                    if text:
                        self.cache.set(cache_key, text)
                        return text
                    raise LLMError("empty response")
                except Exception as err:  # noqa: BLE001 - we re-raise below
                    last_error = err
                    if _is_rate_limit(err) or attempt < self.settings.max_retries - 1:
                        wait = self.settings.retry_backoff_seconds * (2**attempt)
                        logger.warning(
                            "model %s failed (%s); retrying in %.1fs", model, err, wait
                        )
                        time.sleep(min(wait, 60))
                        continue
                    logger.warning("model %s failed: %s", model, err)
                    break
        raise LLMError(f"all models failed: {last_error}")

    # --------------------------------------------------------------- providers
    def _call_once(
        self,
        model: str,
        prompt: str,
        image_bytes: bytes | None,
        mime_type: str | None,
        json_mode: bool,
    ) -> str:
        provider = self.settings.provider
        if provider == "google":
            return self._call_google(model, prompt, image_bytes, mime_type, json_mode)
        if provider == "openai":
            return self._call_openai(model, prompt, image_bytes, mime_type, json_mode)
        if provider == "anthropic":
            return self._call_anthropic(model, prompt, image_bytes, mime_type)
        raise LLMError(f"unsupported provider {provider!r}")

    def _call_google(self, model, prompt, image_bytes, mime_type, json_mode) -> str:
        from google import genai
        from google.genai import types as genai_types

        client = genai.Client(api_key=self.settings.gemini_api_key)
        contents: list = [prompt]
        if image_bytes:
            contents.append(
                genai_types.Part.from_bytes(
                    data=image_bytes, mime_type=mime_type or "image/png"
                )
            )
        config = genai_types.GenerateContentConfig(
            temperature=self.settings.temperature,
            response_mime_type="application/json" if json_mode else "text/plain",
        )
        response = client.models.generate_content(
            model=model, contents=contents, config=config
        )
        return (response.text or "").strip()

    def _call_openai(self, model, prompt, image_bytes, mime_type, json_mode) -> str:
        from openai import OpenAI

        client = OpenAI(api_key=self.settings.openai_api_key)
        content: list = [{"type": "text", "text": prompt}]
        if image_bytes:
            b64 = base64.b64encode(image_bytes).decode("ascii")
            content.append(
                {
                    "type": "image_url",
                    "image_url": {"url": f"data:{mime_type or 'image/png'};base64,{b64}"},
                }
            )
        kwargs: dict = {"model": model, "messages": [{"role": "user", "content": content}]}
        # gpt-5 family are reasoning models and reject a custom temperature.
        if not model.startswith("gpt-5"):
            kwargs["temperature"] = self.settings.temperature
        if json_mode:
            kwargs["response_format"] = {"type": "json_object"}
        response = client.chat.completions.create(**kwargs)
        return (response.choices[0].message.content or "").strip()

    def _call_anthropic(self, model, prompt, image_bytes, mime_type) -> str:
        import anthropic

        client = anthropic.Anthropic(api_key=self.settings.anthropic_api_key)
        content: list = []
        if image_bytes:
            content.append(
                {
                    "type": "image",
                    "source": {
                        "type": "base64",
                        "media_type": mime_type or "image/png",
                        "data": base64.b64encode(image_bytes).decode("ascii"),
                    },
                }
            )
        content.append({"type": "text", "text": prompt})
        message = client.messages.create(
            model=model,
            max_tokens=4096,
            temperature=self.settings.temperature,
            messages=[{"role": "user", "content": content}],
        )
        return "".join(
            block.text for block in message.content if getattr(block, "type", "") == "text"
        ).strip()
