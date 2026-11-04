"""Field extraction from OCR text. Regex first, never guesses."""
from __future__ import annotations

import re
from typing import Optional

from .models import Invoice

AMOUNT = r"(\d{1,3}(?:\.\d{3})*,\d{2}|\d+\.\d{2})"
DATE_PATTERNS = (
    r"\b(\d{2}\.\d{2}\.\d{4})\b",
    r"\b(\d{4}-\d{2}-\d{2})\b",
)
INVOICE_NO = (
    r"(?:Rechnungsnummer|Rechnungs-Nr\.?|Rechnungsnr\.?|Invoice\s*(?:No|Number)\.?)"
    r"\s*[:#]?\s*([A-Z0-9][A-Z0-9\-/]{2,})"
)
VENDOR_STOPWORDS = (
    "rechnung", "invoice", "seite", "page", "datum", "kunde", "customer",
)

NET_LABELS = r"(?:Nettobetrag|Netto(?:summe)?|Net\s+amount)"
VAT_LABELS = r"(?:MwSt\.?|USt\.?|Umsatzsteuer|VAT)"
GROSS_LABELS = r"(?:Gesamtbetrag|Gesamtsumme|Bruttobetrag|Brutto|Endbetrag|Rechnungsbetrag|Total)"


def _to_float(raw: str) -> Optional[float]:
    """Convert German (1.234,56) or English (1234.56) amounts to float."""
    if not raw:
        return None
    text = raw.strip()
    if "," in text:
        text = text.replace(".", "").replace(",", ".")
    try:
        return round(float(text), 2)
    except ValueError:
        return None


def _amount_after(text: str, label_pattern: str) -> Optional[float]:
    """Take the last amount found on the same line as the label.

    Handles both "Nettobetrag   1.240,00" and "MwSt. 19 %   235,60",
    where a percentage sits between the label and the value.
    """
    label = re.compile(label_pattern, re.IGNORECASE)
    amount = re.compile(AMOUNT)
    for line in text.splitlines():
        if not label.search(line):
            continue
        values = amount.findall(line)
        if values:
            return _to_float(values[-1])
    return None


def find_date(text: str) -> Optional[str]:
    for pattern in DATE_PATTERNS:
        match = re.search(pattern, text)
        if match:
            return match.group(1)
    return None


def find_invoice_no(text: str) -> Optional[str]:
    match = re.search(INVOICE_NO, text, re.IGNORECASE)
    return match.group(1) if match else None


def find_vendor(text: str) -> Optional[str]:
    """First meaningful line that is not a form label or a number."""
    for raw in text.splitlines():
        line = raw.strip(" \t-*|")
        if len(line) < 3 or len(line) > 60:
            continue
        lowered = line.lower()
        if any(word in lowered for word in VENDOR_STOPWORDS):
            continue
        if re.fullmatch(r"[\d\s.,/:-]+", line):
            continue
        if re.search(r"\d{5}", line):  # street/number or postal code
            continue
        if sum(ch.isalpha() for ch in line) < len(line) * 0.6:
            continue
        return line
    return None


def find_currency(text: str) -> Optional[str]:
    if "EUR" in text or "€" in text:
        return "EUR"
    if "USD" in text or "$" in text:
        return "USD"
    if "CHF" in text:
        return "CHF"
    return None


def extract(text: str, source: str = "") -> Invoice:
    """Build an Invoice from raw OCR text. Missing values stay None."""
    invoice = Invoice(source=source)
    invoice.vendor = find_vendor(text)
    invoice.invoice_date = find_date(text)
    invoice.invoice_no = find_invoice_no(text)
    invoice.net = _amount_after(text, NET_LABELS)
    invoice.vat = _amount_after(text, VAT_LABELS)
    invoice.gross = _amount_after(text, GROSS_LABELS)
    invoice.currency = find_currency(text)
    if invoice.gross is None and invoice.net is not None and invoice.vat is not None:
        invoice.gross = round(invoice.net + invoice.vat, 2)
    return invoice
