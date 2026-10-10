"""Image loading and light pre-processing before sending to the vision model.

Applies EXIF rotation and upscales small images. Deskewing is optional and only
runs if OpenCV is installed; the vision models cope with moderate tilt anyway.
"""
from __future__ import annotations

import io
from pathlib import Path

from PIL import Image, ImageOps

IMAGE_SUFFIXES = {".png", ".jpg", ".jpeg", ".webp", ".bmp"}

_MIN_LONG_SIDE = 1600
_MAX_LONG_SIDE = 2600


def _maybe_deskew(image: Image.Image) -> Image.Image:
    try:
        import cv2  # type: ignore
        import numpy as np
    except ImportError:
        return image
    try:
        arr = np.array(image.convert("L"))
        coords = np.column_stack(np.where(arr < 200))
        if coords.shape[0] < 50:
            return image
        angle = cv2.minAreaRect(coords)[-1]
        if angle < -45:
            angle = 90 + angle
        if abs(angle) < 0.5 or abs(angle) > 15:
            return image
        return image.rotate(angle, resample=Image.BICUBIC, expand=True, fillcolor="white")
    except Exception:  # noqa: BLE001 - deskew is best-effort
        return image


def prepare_image(path: str | Path) -> tuple[bytes, str]:
    """Return (image_bytes, mime_type) ready for a vision model."""
    path = Path(path)
    with Image.open(path) as img:
        img = ImageOps.exif_transpose(img)
        img = img.convert("RGB")
        long_side = max(img.size)
        if long_side < _MIN_LONG_SIDE:
            scale = _MIN_LONG_SIDE / long_side
            img = img.resize(
                (int(img.width * scale), int(img.height * scale)), Image.LANCZOS
            )
        elif long_side > _MAX_LONG_SIDE:
            scale = _MAX_LONG_SIDE / long_side
            img = img.resize(
                (int(img.width * scale), int(img.height * scale)), Image.LANCZOS
            )
        img = _maybe_deskew(img)
        buffer = io.BytesIO()
        img.save(buffer, format="PNG", optimize=True)
        return buffer.getvalue(), "image/png"


def list_bill_images(folder: str | Path) -> list[Path]:
    folder = Path(folder)
    if not folder.exists():
        raise FileNotFoundError(f"bills folder not found: {folder}")
    images = [
        p for p in sorted(folder.iterdir())
        if p.is_file() and p.suffix.lower() in IMAGE_SUFFIXES
    ]
    return images
