## Kurzfassung (Deutsch)

End-to-End-Tests für die Anwendung in [`../sportsbet-scanner`](../sportsbet-scanner).
Die Suite startet die echte Anwendung auf einem freien Port mit frischer Datenbank, prüft
API und Oberfläche und beendet sie danach. Keine Mocks des Backends.

Gemessen: 6 Tests grün in 2,8 s (Chromium headless). Ein echter Startfehler wurde gefunden:
Die Anwendung brach ohne `config.json` ab.

# e2e-tests

End-to-end tests for the app in [`../sportsbet-scanner`](../sportsbet-scanner).
Not a tutorial on a demo site: these tests drive my own product, with its own database,
and they caught one real startup bug (see below).

## Result

**6 tests, all passing, 2.8 s** (Chromium headless, Windows 11, Python 3.11).

| Test | What it protects |
|---|---|
| `test_api_version` | the app answers and reports its asset version |
| `test_add_and_list_bet` | a bet written through the API appears in the list with status `open` |
| `test_settle_bet_and_reject_double_settle` | settling works once; the second attempt returns 404 instead of double-counting profit |
| `test_value_bets_without_api_keys` | without API keys the endpoint answers with an empty result, it does not crash |
| `test_dashboard_renders_without_console_errors` | the page loads with **zero** console errors |
| `test_tabs_switch_to_my_bets` | tab navigation still works after UI changes |

## How it works

- `conftest.py` starts the real app with `uvicorn` on a **free port**, with a **fresh database**,
  and stops it when the session ends. No mocks of the backend.
- `pages/dashboard_page.py` is a Page Object: selectors live there, tests read like prose.
- Tests are independent: the API tests use `requests`, the UI tests use Playwright.
- Traces and screenshots are kept only on failure.

```bash
python -m venv .venv
.venv/Scripts/python -m pip install -r requirements.txt
.venv/Scripts/python -m pip install -r ../sportsbet-scanner/requirements.txt
.venv/Scripts/python -m playwright install chromium
.venv/Scripts/python -m pytest
```

## What the tests actually caught

**One real bug.** The app crashed at startup with a raw traceback when `config.json` was missing
(the portfolio copy ships only `config.example.json`). Now it falls back to the example, prints one
clear line and starts. That fix is in `../sportsbet-scanner/backend/main.py`.

The other five tests did not find a defect — they **lock in** behaviour that already worked
(no double settle, clean console, tab switching). That is their job: they would fail the day
someone breaks it. Saying "the tests found five bugs" would be a lie.

## Limits

- No external API is called: live odds, value bets and the AI chat need keys and are out of scope.
- The gate (access key) is disabled in the example config, so its redirect logic is not covered yet.
- Linux CI runs the same suite; Windows is the primary target.

## Next

- Cover the access gate with a second app instance that has a key set.
- Add a visual check for the dashboard (screenshot diff) once the layout stabilises.
- Move the duplicated "start the app" logic into a small `tools/serve.py` helper.
