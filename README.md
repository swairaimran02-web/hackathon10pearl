# 🧾 Utility Bill Decoder

**AI that reads Pakistani electricity bills (K-Electric / KESC, LESCO, IESCO)
from images — scans, phone photos or screenshots — and explains them in plain
English.**

Built for the **Women Tech Quest 2026 · Build with AI** hackathon (10Pearls,
Lahore), then polished into a full **Streamlit dashboard** anyone can run.
The model does the *reading* and *explaining*; **Python does all the maths** —
so the results are deterministic, auditable and reproducible.

![Python](https://img.shields.io/badge/Python-3.11%2B-3776AB) ![Tests](https://img.shields.io/badge/tests-23%20passing-22c55e) ![Model](https://img.shields.io/badge/vision%20model-Gemini%203.5%20Flash--Lite-4285F4) ![License](https://img.shields.io/badge/license-MIT-64748b) ![UI](https://img.shields.io/badge/UI-Streamlit-FF4B4B)

---

## What it produces

* **Level 1** — a structured JSON object per bill: provider, billing month,
  meter readings, units, charges, taxes, arrears and payable amounts
  (`output/level1.csv`).
* **Level 2** — a plain-English answer to every customer question about each
  bill (`output/level2.csv`).

Values are taken **exactly as printed on the bill** — never recomputed by the
model. Credits and subsidies are negative, unreadable values stay `null`
(never guessed), and personal identifiers (names, addresses, reference/meter
numbers) are excluded from all outputs.

## Screenshots

| | |
| --- | --- |
| ![Dashboard](docs/screenshots/dashboard.png) | ![Bill Analysis](docs/screenshots/bill-analysis.png) |
| **Dashboard** — live statistics from the real output files | **Bill Analysis** — every extracted field for a bill |
| ![Questions & Answers](docs/screenshots/qa.png) | ![Upload Bills](docs/screenshots/upload.png) |
| **Questions & Answers** — searchable, marked answered/unanswered | **Upload Bills** — drag & drop images, progress bar + log |

More screenshots: [Generated Reports](docs/screenshots/reports.png) ·
[Settings](docs/screenshots/settings.png).

## Key features

* **Vision-first extraction** — no OCR library, no invoice-extraction service;
  a multimodal model reads the bill directly (handles Urdu, tilted scans and
  varied layouts). [Gemini 3.5 Flash-Lite → Google AI Studio, free key].
* **The model reads, the code computes** — all arithmetic (averages, shares,
  payable math) happens in deterministic Python.
* **One batched call per bill** for all 12 Level-2 questions — stays well
  under free-tier limits.
* **On-disk response cache** — re-runs are instant and free; results are
  byte-for-byte reproducible.
* **Provider-agnostic client** — Google / OpenAI / Anthropic with an automatic
  fallback model and retry-with-backoff.
* **Six-page Streamlit dashboard** — real data end-to-end, nothing hardcoded;
  the API key is never displayed or logged.
* **Synthetic demo bill** — try the whole pipeline without any private data.

## How it works

```
bill image
   |  1. preprocess: EXIF rotate, upscale, optional deskew        (Pillow)
   v
   |  2. vision extraction -> one "bill understanding" JSON       (Gemini)
   |        Level 1 fields + monthly consumption history
   v
   |  3. validate + normalize: numbers, dates, signs, nulls        (code)
   v
   |  4. compute facts: averages, shares, counts, estimates        (code)
   +--> 5. output/level1.csv
   |
   |  6. answer all 12 questions in ONE batched call per bill      (Gemini)
   |        grounded in the normalized JSON + computed facts
   +--> 7. output/level2.csv
```

## Try it in ~3 minutes (no private data needed)

The repo ships `tools/make_sample_bill.py`, which renders a clean synthetic
K-Electric bill plus matching CSV templates, so you can run the full pipeline
on real model calls without any real customer data:

```bash
# 1. Set up
python -m venv venv
venv\Scripts\activate            # Windows   (macOS/Linux: source venv/bin/activate)
pip install -r requirements.txt

# 2. Add a free Gemini key
copy .env.example .env           # Windows   (macOS/Linux: cp .env.example .env)
# edit .env → GEMINI_API_KEY=<your key from Google AI Studio>

# 3. Generate the synthetic demo bill
python tools/make_sample_bill.py

# 4. Run the pipeline (≈2 API calls on first run, then cached)
python run.py --bills sample/bills --out output \
    --level1-template sample/csv/level1.csv \
    --level2-template sample/csv/level2.csv

# 5. Open the dashboard
streamlit run app.py            # → http://localhost:8501
```

## Your own bills

Process any folder of bill images:

```bash
python run.py --bills path/to/bills --out output/ \
    --level1-template my/level1.csv \
    --level2-template my/level2.csv
```

Useful options: `--no-questions` (Level 1 only), `--limit 2 --verbose` (quick
smoke test), `--out <dir>` (where the CSVs are written).

In the dashboard, drag & drop bill images (PNG/JPG/WEBP/BMP) — the original
file names become the bill IDs, so re-uploading an already-processed bill is
instant and free thanks to the cache.

## The dashboard

Six pages driving the **exact same `billdecoder` backend** as the CLI — the
generated CSVs are identical either way:

| Page | What actually works |
| --- | --- |
| **Dashboard** | Real statistics from `output/`: bills processed, successes, failures, questions answered + live processing log. |
| **Upload Bills** | Drag & drop images with previews, or a bills-folder path. Optional CSV templates preserve official row order. Full progress bar + log. |
| **Bill Analysis** | Every extracted bill: dates, readings, units, charges, taxes, payable amounts + monthly history chart. Missing values show "Not available" — nothing invented. |
| **Questions & Answers** | Searchable table of every question with its answer; unanswered questions marked; in-page answer generation. |
| **Generated Reports** | Download the actual `level1.csv` / `level2.csv`, previews, regeneration from processed bills. |
| **Settings** | Model config read from `.env` (key status only, never the key), "Test API connection" button, output-folder override. |

## Testing

```bash
pytest -q        # 23 tests, no API key required
```

A GitHub Actions workflow (`.github/workflows/ci.yml`) runs the same suite on
Python 3.11 and 3.12 on every push.

## Project layout

```
run.py                     Command-line entry point
app.py                     Streamlit dashboard (six pages, full workflow)
billdecoder/               Core backend (untouched by the dashboard)
  config.py                Environment + allowed-model validation
  llm.py                   Provider-agnostic client (Google/OpenAI/Anthropic)
  prompts.py               Extraction and Q&A prompts
  schema.py                Level 1 schema and controlled vocabularies
  extract.py               Image -> normalized bill object
  normalize.py             Numbers, dates, signs, null handling
  validate.py              Internal-consistency warnings (values as printed)
  calc.py                  Deterministic calculations
  level1.py / level2.py    build the two output CSVs
  preprocess.py            Image loading + light pre-processing
  io_utils.py              JSON / CSV helpers
  cache.py                 On-disk response cache
dashboard/                 Frontend-only Streamlit package (styles, components,
                           plots, state, io, pipeline glue)
tools/
  make_sample_bill.py      Renders the synthetic demo bill + templates
  rebuild_dashboard_data.py  Rebuild dashboard artefacts from the cache
  check_output.py          Validates level1/level2 CSV output
  verify_bill.py           Second-pass verification of specific fields
tests/                     Unit + dashboard smoke tests (no API key)
sample/                    Synthetic demo bill + CSV templates
data/sample_level2.csv     Sample questions to try on the training bills
DEMO_GUIDE.md              How to record a demo video for the submission
```

## Design decisions

* **Multimodal model for perception only** — reading Urdu, tilted scans and
  different layouts; and for natural-language explanation.
* **All arithmetic in code** — the hackathon rules stated calculations are
  checked against the bill, so deterministic Python keeps answers auditable.
* **One batched Level-2 call per bill** — 12 questions answered in a single
  call, staying within free-tier limits (500 requests/day, 15/min).
* **Disk cache keyed by exact inputs** — `PROMPT_VERSION + provider + model +
  tag + prompt + image` → re-runs are free and identical.

Only the models permitted by the WTQ 2026 rules are ever called
(Gemini 3.5 Flash-Lite primary, Gemini 3.1 Flash-Lite automatic backup,
optional `gpt-5-mini` / `claude-haiku-4-5` if you add those keys).

## Environment variables

See `.env.example`.

| Variable | Purpose | Example |
| --- | --- | --- |
| `MODEL_PROVIDER` | `google`, `openai` or `anthropic` | `google` |
| `MODEL_NAME` | Primary model ID | `gemini-3.5-flash-lite` |
| `FALLBACK_MODEL_NAME` | Automatic backup model | `gemini-3.1-flash-lite` |
| `GEMINI_API_KEY` | Google AI Studio key (free) | placeholder in `.env.example` |
| `OPENAI_API_KEY` | Optional | empty |
| `ANTHROPIC_API_KEY` | Optional | empty |

## Notes and assumptions

* Grey-boxed / unreadable values are returned as `null` rather than guessed.
* Credits and subsidies are negative, as required by the guide.
* PII (names, CNIC, account/consumer/meter/reference numbers) is excluded.

## License

[MIT](LICENSE) © 2026 Swaira Imran