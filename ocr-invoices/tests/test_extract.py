"""Unit tests for the regex extraction and the SQLite store (no OCR needed)."""
from __future__ import annotations

import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from ocr_invoices.extract import extract  # noqa: E402
from ocr_invoices.store import Store  # noqa: E402

SAMPLE_TEXT = """
Nordlicht Elektronik GmbH
Marktplatz 7  ·  85614 Kirchseeon
Rechnung
Rechnungsnummer: RE-2026-0441
Rechnungsdatum: 14.10.2026
Nettobetrag            1.240,00
MwSt. 19 %               235,60
Gesamtbetrag           1.475,60
Alle Beträge in EUR
Zahlbar innerhalb von 14 Tagen.
"""


def test_extracts_all_seven_fields() -> None:
    invoice = extract(SAMPLE_TEXT)
    assert invoice.vendor == "Nordlicht Elektronik GmbH"
    assert invoice.invoice_no == "RE-2026-0441"
    assert invoice.invoice_date == "14.10.2026"
    assert invoice.net == pytest.approx(1240.00)
    assert invoice.vat == pytest.approx(235.60)
    assert invoice.gross == pytest.approx(1475.60)
    assert invoice.currency == "EUR"
    assert invoice.found() == 7


def test_missing_fields_are_not_invented() -> None:
    invoice = extract("Irgendein Dokument ohne Rechnungsdaten")
    assert invoice.invoice_no is None
    assert invoice.net is None
    assert invoice.gross is None
    assert invoice.found() == 0


def test_english_amounts_and_iso_date() -> None:
    text = (
        "Acme Supply Ltd\n"
        "Invoice No: INV-9911\n"
        "2026-09-30\n"
        "Net amount 1234.56\n"
        "VAT 234.56\n"
        "Total 1469.12\n"
    )
    invoice = extract(text)
    assert invoice.invoice_no == "INV-9911"
    assert invoice.invoice_date == "2026-09-30"
    assert invoice.net == pytest.approx(1234.56)
    assert invoice.gross == pytest.approx(1469.12)


def test_gross_is_derived_when_only_net_and_vat_exist() -> None:
    invoice = extract(SAMPLE_TEXT.replace("Gesamtbetrag           1.475,60", ""))
    assert invoice.gross == pytest.approx(1475.60)


def test_store_deduplicates(tmp_path: Path) -> None:
    store = Store(tmp_path / "test.db")
    invoice = extract(SAMPLE_TEXT)
    assert store.save(invoice) is True
    assert store.save(invoice) is False
    assert len(store.all()) == 1
    store.close()
