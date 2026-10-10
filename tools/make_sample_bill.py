"""Generate a synthetic K-Electric style sample bill + CSV templates.

The organizers' own test bills cannot be redistributed, so this tool renders a
clean, synthetic utility bill (PIL) plus matching Level 1 / Level 2 CSV
templates. Anyone cloning the repo can then run the full pipeline on real
model calls without any private data:

    python tools/make_sample_bill.py
    python run.py --bills sample/bills --out output \
        --level1-template sample/csv/level1.csv \
        --level2-template sample/csv/level2.csv

The numbers on the bill are designed to reconcile exactly (charges + taxes =
current bill = payable) so extraction produces no advisory warnings.
"""
from __future__ import annotations

import csv
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

ROOT = Path(__file__).resolve().parent.parent
OUT_BILL = ROOT / "sample" / "bills" / "KESC_DEMO.png"
OUT_L1 = ROOT / "sample" / "csv" / "level1.csv"
OUT_L2 = ROOT / "sample" / "csv" / "level2.csv"

# ------------------------------- bill contents ------------------------------
BILL_ID = "KESC_DEMO"

META = [
    ("Provider", "K-Electric (KESC)"),
    ("Account demo", "KE-DEMO-0001"),
    ("Tariff", "A-2(b)"),
    ("Billing month", "2026-09"),
    ("Reading date", "2026-09-08"),
    ("Issue date", "2026-09-09"),
    ("Due date", "2026-10-03"),
]

METER = [
    ("Sanctioned load", "5 kW"),
    ("Previous reading", "5,949.00"),
    ("Current reading", "6,625.00"),
    ("Units consumed", "676"),
]

CHARGES = [
    ("Energy charges (676 x 40.00)", "27,040.00"),
    ("Fixed charges", "600.00"),
    ("Fuel price adjustment (676 x 3.50)", "2,366.00"),
    ("Total charges", "30,006.00"),
]

TAXES = [
    ("GST (15% of 30,006.00)", "4,500.90"),
    ("Total taxes & duties", "4,500.90"),
]

AMOUNTS = [
    ("Current bill", "34,506.90"),
    ("Arrears (previous dues)", "0.00"),
    ("Payable within due date", "34,506.90"),
    ("Payable after due date", "36,006.90"),
]

HISTORY = [
    ("2025-10", 402), ("2025-11", 385), ("2025-12", 411), ("2026-01", 376),
    ("2026-02", 350), ("2026-03", 402), ("2026-04", 388), ("2026-05", 415),
    ("2026-06", 431), ("2026-07", 452), ("2026-08", 468), ("2026-09", 676),
]

# ----------------------------------- draw -----------------------------------
def _font(size: int, bold: bool = False) -> ImageFont.FreeTypeFont | ImageFont.ImageFont:
    candidates = [
        r"C:\Windows\Fonts\arialbd.ttf" if bold else r"C:\Windows\Fonts\arial.ttf",
        r"C:\Windows\Fonts\segoeuib.ttf" if bold else r"C:\Windows\Fonts\segoeui.ttf",
        "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf" if bold
        else "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
    ]
    for path in candidates:
        if Path(path).exists():
            return ImageFont.truetype(path, size)
    return ImageFont.load_default()


def _table(draw: ImageDraw.ImageDraw, x: int, y: int, rows: list[tuple[str, str]],
           col2_x: int, size: int) -> int:
    font = _font(size)
    for left, right in rows:
        draw.text((x, y), left, fill="#1E293B", font=font)
        draw.text((col2_x, y), right, fill="#0F172A", font=font)
        y += size + 14
    return y


def generate() -> None:
    W, H = 1000, 1500
    img = Image.new("RGB", (W, H), "#FFFFFF")
    d = ImageDraw.Draw(img)

    # Header band
    d.rectangle([0, 0, W, 120], fill="#0B1B4D")
    d.text((40, 32), "K-Electric (KESC)", fill="#FFFFFF", font=_font(42, bold=True))
    d.text((40, 88), "Electricity Bill - Demo", fill="#CBD5E1", font=_font(20))
    d.text((W - 340, 52), "BILL", fill="#FFC53D", font=_font(30, bold=True))

    y = 170
    d.text((40, y), "Billing information", fill="#0B1B4D", font=_font(26, bold=True))
    y = _table(d, 40, y + 10, META, 380, 22) + 20

    d.text((40, y), "Meter information", fill="#0B1B4D", font=_font(26, bold=True))
    y = _table(d, 40, y + 10, METER, 380, 22) + 20

    col2_x = 620
    d.text((40, y), "Charges (PKR)", fill="#0B1B4D", font=_font(26, bold=True))
    y = _table(d, 40, y + 10, CHARGES, col2_x, 22) + 20

    d.text((40, y), "Taxes & duties (PKR)", fill="#0B1B4D", font=_font(26, bold=True))
    y = _table(d, 40, y + 10, TAXES, col2_x, 22) + 20

    d.text((40, y), "Amounts (PKR)", fill="#0B1B4D", font=_font(26, bold=True))
    y = _table(d, 40, y + 10, AMOUNTS, col2_x, 22) + 20

    # Monthly history summary
    d.text((40, y), "Monthly consumption history (units)", fill="#0B1B4D",
           font=_font(26, bold=True))
    y += 40
    bar_w, gap, chart_h = 60, 14, 100
    max_u = max(u for _, u in HISTORY)
    x = 40
    small = _font(13)
    for month, units in HISTORY:
        bar_h = int(chart_h * units / max_u)
        d.rectangle([x, y + chart_h - bar_h, x + bar_w, y + chart_h], fill="#2563EB")
        d.text((x + 6, y + chart_h - bar_h - 18), str(units), fill="#1E293B", font=small)
        d.text((x + bar_w // 2 - 8, y + chart_h + 6), month[2:], fill="#475569", font=small)
        x += bar_w + gap
    y += chart_h + 40

    d.line([40, y, W - 40, y], fill="#CBD5E1", width=2)
    d.text((40, y + 14), "Demo bill - generated by tools/make_sample_bill.py",
           fill="#64748B", font=_font(16))

    OUT_BILL.parent.mkdir(parents=True, exist_ok=True)
    img.save(OUT_BILL)
    print(f"wrote {OUT_BILL}")

    # Level 1 template (bill_id, empty json - filled by the pipeline)
    OUT_L1.parent.mkdir(parents=True, exist_ok=True)
    with OUT_L1.open("w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(["bill_id", "json"])
        w.writerow([BILL_ID, ""])
    print(f"wrote {OUT_L1}")

    # Level 2 template - generic customer questions for the demo bill
    questions = [
        "How many units did I use this month?",
        "How much of my bill is taxes?",
        "What percentage of my bill is taxes?",
        "What is the effective cost per unit this month?",
        "How much do I have to pay before the due date?",
        "What happens if I pay after the due date?",
        "How many months in my history went above 400 units?",
        "What was my average consumption over the last 12 months?",
        "How much are fuel price adjustments on this bill?",
        "What are my previous dues (arrears)?",
        "What is my current reading and how many units did I use since last month?",
        "What tariff is applied on my bill?",
    ]
    with OUT_L2.open("w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(["bill_id", "question_id", "question", "answer"])
        for i, q in enumerate(questions, start=1):
            w.writerow([BILL_ID, f"Q{i}", q, ""])
    print(f"wrote {OUT_L2}")


if __name__ == "__main__":
    generate()