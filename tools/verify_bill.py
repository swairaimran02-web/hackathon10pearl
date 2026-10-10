"""Re-verify specific fields of a bill image with a focused second read.

Usage:
    python tools/verify_bill.py --image data/train/bills/LESCO_0005.png \
        --question "Is the consumption history showing negative values?"

This issues a separate (uncached) model call so it acts as an independent check
of the values extracted by the main pipeline.
"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from billdecoder.config import Settings
from billdecoder.llm import LLMClient
from billdecoder.preprocess import prepare_image


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description="Verify specific bill fields")
    parser.add_argument("--image", required=True, help="path to a bill image")
    parser.add_argument("--question", action="append", required=True)
    args = parser.parse_args(argv)

    settings = Settings.from_env()
    settings.validate()
    client = LLMClient(settings)

    image_bytes, mime_type = prepare_image(args.image)
    questions = "\n".join(
        f"{i}. {q}" for i, q in enumerate(args.question, start=1)
    )
    prompt = (
        "Look at this electricity bill image and answer the questions precisely. "
        "Quote the exact printed values. If a value is not printed or is covered by "
        "a grey box, say 'NOT PRINTED'. Do not guess.\n\n"
        f"{questions}"
    )
    text = client.generate(
        prompt, image_bytes=image_bytes, mime_type=mime_type, tag="verify"
    )
    print(text)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())