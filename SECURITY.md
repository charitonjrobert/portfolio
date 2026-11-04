# Security policy

## Reporting

If you find a vulnerability in this code, write to charitonjrobert@gmail.com with:

- the affected project and file,
- what you did to trigger it,
- what you expected and what happened.

Do not open a public issue for a security problem. You will get an answer within 7 days.

## Scope

This repository contains portfolio projects that run locally:

- `ocr-invoices` — local dashboard, no authentication by design (bind to 127.0.0.1 only).
- `sportsbet-scanner` — local instance; the deployed variant uses an access key and a rate limit.
- `e2e-tests` — test code, no service.

No secrets are stored in this repository. `backend/config.json` is absent on purpose;
`backend/config.example.json` contains empty keys.
