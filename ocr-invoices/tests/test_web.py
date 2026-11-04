"""API tests for the dashboard (no browser, no real Tesseract)."""
from __future__ import annotations

import importlib
import sys
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

OCR_TEXT = """
Nordlicht Elektronik GmbH
Rechnungsnummer: RE-2026-0441
Rechnungsdatum: 14.10.2026
Nettobetrag            1.240,00
MwSt. 19 %               235,60
Gesamtbetrag           1.475,60
Alle Beträge in EUR
"""


@pytest.fixture()
def client(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> TestClient:
    monkeypatch.setenv("OCR_DATA_DIR", str(tmp_path))
    monkeypatch.setattr("ocr_invoices.ocr.available", lambda: True)
    monkeypatch.setattr("ocr_invoices.ocr.file_to_text", lambda *a, **k: OCR_TEXT)
    import ocr_invoices.web as web

    importlib.reload(web)
    monkeypatch.setattr(web.ocr, "file_to_text", lambda *a, **k: OCR_TEXT)
    monkeypatch.setattr(web.ocr, "available", lambda: True)
    return TestClient(web.app)


def _upload(client: TestClient) -> dict:
    response = client.post(
        "/api/scan",
        files={"file": ("rechnung.pdf", b"%PDF-1.4 fake", "application/pdf")},
    )
    assert response.status_code == 200, response.text
    return response.json()


def test_scan_stores_invoice(client: TestClient) -> None:
    body = _upload(client)
    assert body["found"] == 7
    assert body["invoice"]["invoice_no"] == "RE-2026-0441"


def test_duplicate_scan_is_rejected(client: TestClient) -> None:
    _upload(client)
    second = client.post(
        "/api/scan",
        files={"file": ("rechnung.pdf", b"%PDF-1.4 fake", "application/pdf")},
    )
    assert second.status_code == 409


def test_patch_updates_field(client: TestClient) -> None:
    invoice_id = _upload(client)["invoice"]["id"]
    response = client.patch(f"/api/invoices/{invoice_id}", json={"vendor": "Korrigiert GmbH"})
    assert response.status_code == 200
    assert response.json()["vendor"] == "Korrigiert GmbH"
    assert response.json()["missing"] == []


def test_patch_rejects_bad_number(client: TestClient) -> None:
    invoice_id = _upload(client)["invoice"]["id"]
    response = client.patch(f"/api/invoices/{invoice_id}", json={"net": "keine Zahl"})
    assert response.status_code == 400


def test_delete_removes_invoice(client: TestClient) -> None:
    invoice_id = _upload(client)["invoice"]["id"]
    assert client.delete(f"/api/invoices/{invoice_id}").status_code == 200
    assert client.get("/api/invoices").json()["invoices"] == []
    assert client.delete(f"/api/invoices/{invoice_id}").status_code == 404


def test_export_csv(client: TestClient) -> None:
    _upload(client)
    response = client.get("/api/export.csv")
    assert response.status_code == 200
    assert "RE-2026-0441" in response.text
    assert "vendor" in response.text.splitlines()[0]


def test_settings_round_trip(client: TestClient) -> None:
    saved = client.post("/api/settings", json={"lang": "deu", "dpi": 400}).json()
    assert saved["lang"] == "deu"
    assert saved["dpi"] == 400
    again = client.post("/api/settings", json={"dpi": 999}).json()
    assert again["dpi"] == 300  # invalid value falls back to the default


def test_stats_reflects_rows(client: TestClient) -> None:
    _upload(client)
    stats = client.get("/api/stats").json()
    assert stats["total"] == 1
    assert stats["complete"] == 1
    assert stats["tesseract_ready"] is True
