"""Rebuild output/extraction_raw.json (dashboard artefacts) from the disk cache.

The dashboard reads output/extraction_raw.json to render the Dashboard,
Bill Analysis and Q&A pages with real data. It is gitignored, so after a
fresh clone (or after the file is deleted) the pages show empty states.

Run this AFTER running the pipeline once (the extraction responses are cached
in .cache/, so this is instant and free — no API calls for already-processed
bills):

    python tools/rebuild_dashboard_data.py --bills data\\test\\bills --out output

Usage:
    python tools/rebuild_dashboard_data.py --bills DIR [--out output]
"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from billdecoder.config import Settings
from billdecoder.llm import LLMClient
from billdecoder.preprocess import list_bill_images
from dashboard import pipeline_ui


def main(argv=None) -> int:
    # The log messages contain "→"; ensure they print on Windows consoles.
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    except (AttributeError, ValueError):
        pass

    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--bills", required=True, help="folder with bill images")
    parser.add_argument("--out", default="output", help="output folder (default: output)")
    args = parser.parse_args(argv)

    paths = sorted(list_bill_images(args.bills))
    if not paths:
        print(f"no bill images found in {args.bills}")
        return 1
    print(f"rebuilding artefacts from {len(paths)} bill image(s)…")

    settings = Settings.from_env()
    settings.validate()
    client = LLMClient(settings)

    records, failures = pipeline_ui.process_paths(client, paths, log=print)
    pipeline_ui.write_artefacts(records, args.out)
    print(f"wrote {args.out}/extraction_raw.json with {len(records)} bill(s), "
          f"{len(failures)} failure(s)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())