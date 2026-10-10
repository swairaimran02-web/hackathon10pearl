# Demo video guide (WTQ 2026 · section 7.7)

Your final submission can earn **up to 5 bonus points** with a short demo video.
This guide tells you exactly what to show, how to record it on Windows, and how
to get it into the submission ZIP without breaking the 15 MB limit.

## 1. The official rules (what judges check)

- File goes inside the ZIP as `demo/demo.mp4` (`.mov` or `.webm` also OK).
- **Maximum 3 minutes.** Keep the whole ZIP at or under 15 MB.
- Audio and captions are **not required** — but every on-screen value must be
  readable.
- The video must show your solution working start to finish:
  1. Starting the solution (from the command line or the app).
  2. Selecting/uploading a bill, **with the bill image visible**.
  3. The Level 1 extracted fields for that bill.
  4. Level 2 answers to a few questions **about the same bill**.
  5. The solution generating `output/level1.csv` and `output/level2.csv`
     for the test bills.

## 2. Record your screen — Windows

**Easiest (built-in, no install): Snipping Tool recorder**
1. Press **`Win` + `Shift` + `R`**.
2. Click **New**, then drag a box over the area you want to record
   (choose the full screen so text stays readable).
3. Click **Record** (mic is optional — voiceover not required).
4. Click **Stop** when done, then **Save** the video (`.mp4`).
5. Move the file to your project folder as `demo/demo.mp4`.

**Alternatives**
- Xbox Game Bar: press **`Win` + `G`** → record button (mic toggle available).
- OBS Studio (free, more control): add a "Display Capture" source, hit Record,
  stop, then File → Remux if OBS names it `.mkv`.

**macOS**: `Cmd` + `Shift` + `5` → "Record Entire Screen" or "Record Selected
Portion" → Record → Stop → save.

> Tip: record a 15–30 second test clip first and play it back before you do the
> real take.

## 3. Before you press Record

- Close chat apps, email and notifications so nothing pops up over the demo.
- Use a clean desktop. Open only: a terminal (PowerShell), VS Code (optional),
  a photo viewer for the bill image, and the browser tab with the dashboard.
- **Never open your `.env` file on camera** — it contains your API key.
- Enlarge text: set the terminal to a larger font, zoom the browser
  (`Ctrl` + `+`), and keep the Windows display scaling at 100–125% so text is
  sharp.
- Have `data\test\bills\KESC_0006.png` handy (a nice, clean K-Electric bill).

## 4. The 3-minute shot list (script)

Everything below uses your real project — no fake numbers. The full pipeline run
is fast because results are cached on disk (say that in the video: "re-running
is free and reproducible").

| Time | On screen | What to say / do |
| --- | --- | --- |
| 0:00–0:20 | Project folder / VS Code | "WTQ 2026 Utility Bill Decoder — it reads K-Electric, LESCO and IESCO bill images, extracts the fields, and answers customer questions. Model: **Gemini 3.5 Flash-Lite** (an allowed model)." |
| 0:20–0:55 | PowerShell terminal | Run the full pipeline (beat 5 — CSVs are generated):<br>`python run.py --bills data\test\bills --out output --level1-template data\test\csv\level1.csv --level2-template data\test\csv\level2.csv`<br>Point at the output: "10 bills extracted, then the answers." |
| 0:55–1:30 | Bill image + Bill Analysis page | Open `data\test\bills\KESC_0006.png` so the bill is visible (beats 2 & 3). Then `streamlit run app.py`, go to **Bill Analysis**, select **KESC_0006**: show billing month, units, current bill, due date, charges/taxes, and the monthly history chart. |
| 1:30–2:00 | Questions & Answers page | Same bill (beat 4): search "KESC_0006", show 2–3 questions answered in plain English. |
| 2:00–2:35 | Reports page + terminal | **Generated Reports** page: click "Download level1.csv" and "Download level2.csv". Then run the checker:<br>`python tools\check_output.py --output output --level2-template data\test\csv\level2.csv`<br>"10 rows, 120 answers, none empty." |
| 2:35–2:55 | Terminal | Build the ZIP and show the demo is inside:<br>`python tools\package_submission.py --output output --dest wtq-submission.zip`<br>(output lists `demo/ included` and the ZIP size). |
| 2:55–3:00 | End | "Values are extracted as printed, PII is excluded, all arithmetic is done in code, and only the five allowed models are used." |

If you are going over 3 minutes, cut the Reports-page downloads and the ZIP
packaging — keep the 5 required beats.

## 5. Keep the ZIP under 15 MB

A 3-minute 1080p clip can be 15–50 MB — too big. Do one of these:

- **HandBrake (free, recommended):** open your MP4 → Preset **"Fast 720p30"** →
  in Video tab set **Constant Quality ≥ 26** → Start → save as `demo\demo.mp4`.
  A mostly-static screencast at 720p usually lands around 2–10 MB.
- **Clipchamp (Windows 11 built-in):** import video → Export → **720p**.

Target: `demo\demo.mp4` ≈ 10 MB or less (the code ZIP is only ~0.1 MB).

## 6. Package and upload

```powershell
python tools\package_submission.py --output output --dest wtq-submission.zip
```

- Confirm the output prints `demo/ included (bonus video)` and the size is
  ≤ 15 MB (the script warns if not).
- Check the ZIP contents with:
  `python -c "import zipfile; print(zipfile.ZipFile('wtq-submission.zip').namelist())"` — you should see `demo/demo.mp4`, the two `output` CSVs and the `source/` code.
- Upload **once** at https://build.womentechquest.com/submit **before 1:30 PM**,
  using the **same email you registered with**.

## 7. Final checklist

- [ ] Video ≤ 3 minutes
- [ ] `demo\demo.mp4` inside the ZIP, ZIP ≤ 15 MB
- [ ] Bill image visible + Level 1 fields + Level 2 answers for the same bill
- [ ] Both CSVs were generated by the code (not edited by hand)
- [ ] No API key / `.env` content shown on camera
- [ ] Mentioned the model used (Gemini 3.5 Flash-Lite)
- [ ] Same registered email, single submission, before 1:30 PM