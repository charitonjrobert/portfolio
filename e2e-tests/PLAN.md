# PLAN — proiect 3: e2e-tests (Playwright pe propriul produs)

> Execuție în ordine. Fiecare pas are criteriu de „gata". Limită: 3 h. Dacă pasul 4 nu e verde
> în 60 min, se taie din teste, nu din calitate.
> Nu se atinge `C:\Projects\sportsbet-app` (producție). Se testează doar copia din `_portfolio`.

## Pași

| # | Pas | Rezultat | Criteriu „gata" | Timp |
|---|---|---|---|---|
| 1 | Mediu E2E: venv separat, `pytest-playwright`, Chromium | `.venv` + browser instalat | `playwright install --dry-run` ok, `pytest --version` | 10 min |
| 2 | Harness: fixture server pe port liber, DB curat, base_url | `conftest.py` | `pytest` pornește și oprește serverul singur | 20 min |
| 3 | Page Object + 6 teste (2 UI, 4 API) | `tests/` | fiecare test are assertions reale, nu doar status 200 | 60 min |
| 4 | Rulare, fix, trace la eșec | raport verde | `6 passed` | 40 min |
| 5 | CI GitHub Actions | `.github/workflows/e2e.yml` | workflow valid, rulează headless | 15 min |
| 6 | README + commit | doc + istoric | cifre reale, limitări scrise | 20 min |

## Cele 6 teste

1. `test_gate_redirects_without_key` — fără cookie, pagina răspunde cu ecranul de acces (nu 500).
2. `test_dashboard_renders` — titlul, taburile principale, fără erori în consolă.
3. `test_api_version` — `/api/version` întoarce `assets`.
4. `test_add_and_list_bet` — POST pariu → GET îl conține cu status `open`.
5. `test_settle_bet` — settle won → status schimbat, profit calculat, al doilea settle dă 404.
6. `test_value_bets_empty_state` — fără chei API, `/api/value-bets` răspunde 200 cu listă goală, nu crapă.

## Reguli

- Fără rețea externă: testele nu cheamă the-odds-api.
- Fiecare test independent; DB șters la start de sesiune.
- Selectori după rol/text, nu după clase CSS.
- `trace: retain-on-failure`, screenshot la eșec.
- Niciun secret în repo; `config.example.json` e suficient.
