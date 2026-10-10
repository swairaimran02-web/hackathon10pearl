"""Tiny on-disk cache so repeated runs do not spend API quota.

The free Gemini tier is 500 requests/day shared between both Gemini models, so
every model call is cached, keyed by the exact inputs. Re-running the pipeline
on the same bills is then free and fully reproducible.
"""
from __future__ import annotations

import hashlib
import json
from pathlib import Path


class DiskCache:
    def __init__(self, root: Path | str):
        self.root = Path(root)
        self.root.mkdir(parents=True, exist_ok=True)

    @staticmethod
    def make_key(*parts: str) -> str:
        digest = hashlib.sha256()
        for part in parts:
            digest.update((part or "").encode("utf-8", errors="ignore"))
            digest.update(b"\x1f")  # unit separator between fields
        return digest.hexdigest()[:32]

    def _path(self, key: str) -> Path:
        return self.root / f"{key}.json"

    def get(self, key: str):
        path = self._path(key)
        if not path.exists():
            return None
        try:
            return json.loads(path.read_text(encoding="utf-8"))
        except (json.JSONDecodeError, OSError):
            return None

    def set(self, key: str, value) -> None:
        path = self._path(key)
        tmp = path.with_suffix(".tmp")
        tmp.write_text(
            json.dumps(value, ensure_ascii=False, indent=2), encoding="utf-8"
        )
        tmp.replace(path)
