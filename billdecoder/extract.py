"""Level 1: turn a bill image into a normalised JSON object."""
from __future__ import annotations

import logging
from pathlib import Path

from .llm import LLMClient
from .normalize import normalize_bill, normalize_history
from .preprocess import prepare_image
from .prompts import EXTRACTION_PROMPT
from .io_utils import parse_json

logger = logging.getLogger(__name__)


def extract_bill(client: LLMClient, image_path: str | Path) -> dict:
    """Extract and normalise one bill. Never raises on a bad model response."""
    image_path = Path(image_path)
    image_bytes, mime_type = prepare_image(image_path)
    text = client.generate(
        EXTRACTION_PROMPT,
        image_bytes=image_bytes,
        mime_type=mime_type,
        json_mode=True,
        tag=f"extract:{image_path.stem}",
    )
    raw = parse_json(text)
    if not raw:
        logger.warning("no JSON returned for %s", image_path.name)
    bill = normalize_bill(raw)
    history = normalize_history(raw.get("monthly_history") or raw.get("history"))
    return {
        "bill_id": image_path.stem,
        "bill": bill,
        "history": history,
        "raw": raw,
        "source": str(image_path),
    }
