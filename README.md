# WTQ 2026 - Utility Bill Decoder

An AI-powered assistant that reads Pakistani electricity bills
(**K-Electric / KESC, LESCO, IESCO**) from images (scans, photos, screenshots)
and explains them in plain English.

It produces the two required result files:

* **Level 1** - one JSON object per bill with the billing details, readings,
  charges, taxes and payable amounts (`output/level1.csv`).
* **Level 2** - a plain-English answer to every customer question about each
  bill (`output/level2.csv`).

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

Design principle: **the model reads and explains, the code does the maths.**
Numbers are extracted with a multimodal model, then every calculation is done in
Python so the answers are deterministic and reproducible.

## Requirements

* Python 3.11 or later (developed on **Python 3.14**).
* An API key for one of the allowed models (a free Google AI Studio Gemini key
  is enough).

## Setup

```bash
# 1. Create and activate a virtual environment
python -m venv venv
# Windows
venv\Scripts\activate
# macOS / Linux
# source venv/bin/activate

# 2. Install dependencies
pip install -r requirements.txt

# 3. Configure your API key
copy .env.example .env      # Windows
# cp .env.example .env      # macOS / Linux
# then edit .env and set GEMINI_API_KEY=...
```

## Run

Process a folder of bills and generate both CSV files:

```bash
python run.py --bills test/bills --out output/ \
    --level1-template test/csv/level1.csv \
    --level2-template test/csv/level2.csv
```

Useful options:

```bash
python run.py --bills train/bills --out output/ --no-questions   # Level 1 only
python run.py --bills train/bills --limit 2 --verbose            # quick smoke test
```

Run the interactive demo:

```bash
streamlit run app.py
```

Run the unit tests (no API key needed):

```bash
pytest -q
```

## Output

| File | Contents |
| --- | --- |
| `output/level1.csv` | 10 rows. `bill_id` plus one JSON object per bill in `json`. |
| `output/level2.csv` | 120 rows. `bill_id`, `question_id`, `question` and the `answer`. |
| `output/extraction_raw.json` | Debug only: raw model output and history per bill. |

The CSV files are written with Python's `csv` module, so commas, quotes and
line breaks are quoted correctly and every JSON object stays on one line.

## Project layout

```
run.py                     Command-line entry point
app.py                     Streamlit demo
billdecoder/
  config.py                Environment + allowed-model validation
  llm.py                   Provider-agnostic client (Google / OpenAI / Anthropic)
  prompts.py               Extraction and Q&A prompts
  schema.py                Level 1 schema and controlled vocabularies
  extract.py               Image -> normalized bill object
  normalize.py             Numbers, dates, signs, null handling
  calc.py                  Deterministic calculations
  level1.py                builds output/level1.csv
  level2.py                builds output/level2.csv
  preprocess.py            Image loading and light pre-processing
  io_utils.py              JSON / CSV helpers
  cache.py                 On-disk response cache
tests/                     Unit tests for normalization
```

## AI usage

Only the models allowed by the WTQ 2026 rules are called. Using any other model
leads to disqualification.

| Purpose | Model | Provider | Access |
| --- | --- | --- | --- |
| Bill reading (vision) + answering questions (primary) | `gemini-3.5-flash-lite` | Google (google-genai) | Free (Google AI Studio) |
| Automatic backup if the primary fails | `gemini-3.1-flash-lite` | Google (google-genai) | Free (Google AI Studio) |
| Optional fallback (only if `OPENAI_API_KEY` is set) | `gpt-5-mini` | OpenAI | Paid |

* **Models / APIs / services used by the solution:** Google Gemini via the
  `google-genai` SDK (primary and backup), optionally OpenAI `gpt-5-mini`.
* **Other services:** none. No Azure, Textract, Mindee or other extraction
  services are used.
* **AI tools used to write the code:** GitHub Copilot / an AI coding assistant
  were used for pair-programming. (Update this line to list exactly what you used.)
* **Local OCR:** not required; the vision model reads the bills directly.
  `opencv-python-headless` can be installed for optional deskewing.

### Why this design

* The multimodal model is used only for perception (reading Urdu, tilted scans
  and different layouts) and for natural-language explanation.
* All arithmetic is done in code, because the guide states that calculations
  are checked against the bill and recommends using code for them.
* All 12 questions for a bill are answered in a single call to stay well within
  the free tier (500 requests/day shared across both Gemini models).
* Every model response is cached on disk, keyed by the exact inputs, so re-runs
  are free and reproducible.

## Environment variables

See `.env.example`. Required: the API key for the provider you use.

| Variable | Purpose | Example |
| --- | --- | --- |
| `MODEL_PROVIDER` | `google`, `openai` or `anthropic` | `google` |
| `MODEL_NAME` | Primary model ID | `gemini-3.5-flash-lite` |
| `FALLBACK_MODEL_NAME` | Backup model ID | `gemini-3.1-flash-lite` |
| `GEMINI_API_KEY` | Google AI Studio key | placeholder in `.env.example` |
| `OPENAI_API_KEY` | Optional | empty |
| `ANTHROPIC_API_KEY` | Optional | empty |

> The model ID is written two ways in the organizers' PDF
> (`gemini-3.5-flashlite` vs `gemini-3.5-flash-lite`). Copy the exact ID shown in
> Google AI Studio.

## Notes and assumptions

* Grey-boxed / unreadable values are returned as `null` rather than guessed.
* Credits and subsidies are negative, as required by the guide.
* PII (names, CNIC, account, consumer, meter, reference numbers) is excluded.
