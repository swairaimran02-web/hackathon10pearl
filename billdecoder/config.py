"""Central configuration: environment variables, model settings and paths.

Only the five models allowed by the WTQ 2026 rules may be used. Using any other
model leads to disqualification, so the settings object validates the chosen
provider/model against :data:`ALLOWED_MODELS` before anything else runs.
"""
from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path

from dotenv import load_dotenv

PROJECT_ROOT = Path(__file__).resolve().parent.parent
DEFAULT_CACHE_DIR = PROJECT_ROOT / ".cache"

# Load a local .env if present. The .env file is never part of the submission.
load_dotenv(PROJECT_ROOT / ".env")

# Exact model IDs allowed in the competition (section 3 / section 9 of the guide).
ALLOWED_MODELS: dict[str, list[str]] = {
    "google": ["gemini-3.5-flash-lite", "gemini-3.1-flash-lite"],
    "openai": ["gpt-4.1-mini", "gpt-5-mini"],
    "anthropic": ["claude-haiku-4-5"],
}

DEFAULT_MODEL: dict[str, str] = {
    "google": "gemini-3.5-flash-lite",
    "openai": "gpt-5-mini",
    "anthropic": "claude-haiku-4-5",
}

# Free backup that shares the same limits as the primary Gemini model.
DEFAULT_FALLBACK: dict[str, str] = {
    "google": "gemini-3.1-flash-lite",
    "openai": "gpt-4.1-mini",
    "anthropic": "claude-haiku-4-5",
}


@dataclass
class Settings:
    """Runtime settings resolved from the environment."""

    provider: str = "google"
    model: str = DEFAULT_MODEL["google"]
    fallback_model: str = DEFAULT_FALLBACK["google"]
    gemini_api_key: str | None = None
    openai_api_key: str | None = None
    anthropic_api_key: str | None = None
    cache_dir: Path = DEFAULT_CACHE_DIR
    temperature: float = 0.0
    max_retries: int = 4
    retry_backoff_seconds: float = 5.0

    @classmethod
    def from_env(cls) -> "Settings":
        provider = (os.getenv("MODEL_PROVIDER") or "google").strip().lower()
        if provider not in ALLOWED_MODELS:
            raise ValueError(
                f"MODEL_PROVIDER={provider!r} is not allowed. "
                f"Choose one of {sorted(ALLOWED_MODELS)}."
            )
        return cls(
            provider=provider,
            model=(os.getenv("MODEL_NAME") or DEFAULT_MODEL[provider]).strip(),
            fallback_model=(
                os.getenv("FALLBACK_MODEL_NAME") or DEFAULT_FALLBACK[provider]
            ).strip(),
            gemini_api_key=os.getenv("GEMINI_API_KEY") or os.getenv("GOOGLE_API_KEY"),
            openai_api_key=os.getenv("OPENAI_API_KEY"),
            anthropic_api_key=os.getenv("ANTHROPIC_API_KEY"),
            cache_dir=Path(os.getenv("CACHE_DIR") or DEFAULT_CACHE_DIR),
            temperature=float(os.getenv("TEMPERATURE") or "0"),
            max_retries=int(os.getenv("MAX_RETRIES") or "4"),
            retry_backoff_seconds=float(os.getenv("RETRY_BACKOFF_SECONDS") or "5"),
        )

    def api_key(self) -> str | None:
        return {
            "google": self.gemini_api_key,
            "openai": self.openai_api_key,
            "anthropic": self.anthropic_api_key,
        }.get(self.provider)

    def validate(self) -> None:
        """Raise a clear error for disallowed models or a missing API key."""
        if self.provider not in ALLOWED_MODELS:
            raise ValueError(f"MODEL_PROVIDER={self.provider!r} is not allowed.")
        if self.model not in ALLOWED_MODELS[self.provider]:
            raise ValueError(
                f"MODEL_NAME={self.model!r} is not allowed for provider "
                f"{self.provider!r}. Allowed: {ALLOWED_MODELS[self.provider]}"
            )
        if not self.api_key():
            raise ValueError(
                f"No API key found for provider {self.provider!r}. "
                "Set GEMINI_API_KEY (or GOOGLE_API_KEY) in your .env file."
            )
