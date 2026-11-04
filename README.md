# Portfolio — Johannes Robert Chariton

Junior IT — Support, QA and Automation. Kirchseeon (Munich east), Germany.

Three small, finished tools. Not tutorials: each one solves a problem I had, runs on Windows,
and states its measured result and its limits.

| Project | Problem | What it proves | Stack |
|---|---|---|---|
| [ocr-invoices](ocr-invoices/) | Invoices arrive as PDFs and get typed by hand | OCR pipeline, data modelling, testing | Python, Tesseract, SQLite |
| [sportsbet-scanner](sportsbet-scanner/) | Comparing bookmaker odds by hand is slow and error-prone | Backend design, REST integration, caching, business rules | FastAPI, SQLite, vanilla JS |

## Measured results

- **ocr-invoices**: 21/21 fields extracted correctly on 3 synthetic German invoices (7 fields × 3 documents). Missing fields stay empty; the tool never guesses.
- **sportsbet-scanner**: runs locally with `config.example.json`, no keys required to start; value-bet and arbitrage logic covered by its module tests.

## Skills proven (not claimed)

| Skill | Where it is visible |
|---|---|
| Python (structured, typed, tested) | both projects |
| FastAPI / REST APIs | sportsbet-scanner `backend/` |
| SQL / SQLite schema + dedupe | `store.py`, `bets.db` model |
| OCR / Tesseract / PDF rendering | ocr-invoices `ocr.py` |
| Regex extraction and edge cases | `extract.py` + tests |
| Testing (pytest, fixtures, no-binary CI) | `tests/` |
| Windows tooling, portable dependencies | `vendor/`, no admin installs |
| Frontend basics (HTML/CSS/JS) | `dashboard/` |

## How to run

```bash
# ocr-invoices
cd ocr-invoices && python -m venv .venv
.venv/Scripts/python -m pip install -r requirements.txt
set PYTHONPATH=src
.venv/Scripts/python -m ocr_invoices --db data/invoices.db scan "sample/*.pdf"

# sportsbet-scanner
cd sportsbet-scanner
python -m pip install -r requirements.txt
python -m uvicorn main:app --app-dir backend --host 127.0.0.1 --port 8010
```

## What I would do next

- ocr-invoices: deskew and binarisation before OCR, line-item tables, DATEV export.
- sportsbet-scanner: split the backend into services, add real unit tests around the value scan.
- Add a third project: a small Playwright E2E suite with CI — the automation side is not
  represented here yet, on purpose, until it is finished.

## Note

Built with AI assistance (generation, review, test scaffolding), designed, run and verified by me.
No customer data, no API keys, no third-party content in this repository.
