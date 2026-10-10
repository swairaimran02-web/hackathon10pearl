"""Package the submission ZIP with the required structure (section 7).

Creates a ZIP containing:
    output/level1.csv
    output/level2.csv
    source/  (code: run.py, app.py, billdecoder/, dashboard/, tools/, tests/,
              README.md, .env.example, requirements.txt, requirements.lock.txt)
    demo/    (optional bonus video, section 7.7: demo.mp4/.mov/.webm, <=3 min)

The ZIP must be 15 MB or smaller, and must NOT contain .env or API keys.

Usage:
    python tools/package_submission.py --output output --dest wtq-submission.zip
"""
from __future__ import annotations

import argparse
import sys
import zipfile
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent

SOURCE_ITEMS = [
    "README.md",
    ".env.example",
    "requirements.txt",
    "requirements.lock.txt",
    "run.py",
    "app.py",
    "billdecoder",
    "dashboard",
    ".streamlit",
    "tools",
    "tests",
]

FORBIDDEN = {".env", ".cache", "notes", "venv", "data", "__pycache__", "output"}


def add_dir(zf: zipfile.ZipFile, root: Path, arc_prefix: str, folder: str) -> None:
    source_dir = root / folder
    if not source_dir.exists():
        return
    for path in sorted(source_dir.rglob("*")):
        if path.is_file() and not any(part in FORBIDDEN for part in path.parts):
            zf.write(path, f"{arc_prefix}/{folder}/{path.relative_to(source_dir)}")


def add_demo(zf: zipfile.ZipFile) -> bool:
    """Add the optional demo/ folder (7.7: demo.mp4/.mov/.webm, <=3 min)."""
    demo_dir = PROJECT_ROOT / "demo"
    if not demo_dir.exists():
        return False
    added = 0
    for path in sorted(demo_dir.rglob("*")):
        if path.is_file():
            zf.write(path, f"demo/{path.relative_to(demo_dir)}")
            added += 1
    return added > 0


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description="Package the submission ZIP")
    parser.add_argument("--output", default="output", help="folder with the CSVs")
    parser.add_argument("--dest", default="wtq-submission.zip")
    args = parser.parse_args(argv)

    output_dir = PROJECT_ROOT / args.output
    dest = Path(args.dest)

    missing = []
    for required in ("level1.csv", "level2.csv"):
        if not (output_dir / required).exists():
            missing.append(required)
    if missing:
        print(f"Missing required files in {output_dir}: {missing}", file=sys.stderr)
        return 1

    with zipfile.ZipFile(dest, "w", zipfile.ZIP_DEFLATED) as zf:
        for csv_file in ("level1.csv", "level2.csv"):
            zf.write(output_dir / csv_file, f"output/{csv_file}")
        for item in SOURCE_ITEMS:
            item_path = PROJECT_ROOT / item
            if item_path.is_file():
                zf.write(item_path, f"source/{item}")
            elif item_path.is_dir():
                add_dir(zf, PROJECT_ROOT, "source", item)
        if add_demo(zf):
            print("  demo/ included (bonus video)")
        else:
            print("  demo/ not found - skipping (optional)")

    size_bytes = dest.stat().st_size
    size_mb = size_bytes / (1024 * 1024)
    print(f"wrote {dest} ({size_mb:.1f} MB)")
    with zipfile.ZipFile(dest) as zf:
        for name in sorted(zf.namelist()):
            print(f"  {name}")
    if size_bytes > 15 * 1024 * 1024:
        print("WARNING: ZIP exceeds 15 MB - remove the demo video or compress images")
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())