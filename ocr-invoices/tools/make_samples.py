"""Generate three synthetic German invoices as PDFs.

All data is invented (no real companies). Ground truth is written to
sample/expected.json so the extraction accuracy can be measured.
"""
from __future__ import annotations

import json
from pathlib import Path

from reportlab.lib.pagesizes import A4
from reportlab.pdfgen import canvas

OUT = Path(__file__).resolve().parents[1] / "sample"

INVOICES = [
    {
        "file": "rechnung_001.pdf",
        "vendor": "Nordlicht Elektronik GmbH",
        "invoice_no": "RE-2026-0441",
        "invoice_date": "14.10.2026",
        "net": 1240.00,
        "vat": 235.60,
        "gross": 1475.60,
    },
    {
        "file": "rechnung_002.pdf",
        "vendor": "Alpenblick Kaffeerösterei KG",
        "invoice_no": "2026/0873",
        "invoice_date": "02.10.2026",
        "net": 385.50,
        "vat": 73.25,
        "gross": 458.75,
    },
    {
        "file": "rechnung_003.pdf",
        "vendor": "Büroservice Leuchtturm",
        "invoice_no": "BL-77310",
        "invoice_date": "28.10.2026",
        "net": 96.00,
        "vat": 18.24,
        "gross": 114.24,
    },
]


def money(value: float) -> str:
    return f"{value:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")


def draw(invoice: dict, path: Path) -> None:
    pdf = canvas.Canvas(str(path), pagesize=A4)
    pdf.setFont("Helvetica-Bold", 16)
    pdf.drawString(60, 780, invoice["vendor"])
    pdf.setFont("Helvetica", 9)
    pdf.drawString(60, 764, "Marktplatz 7  ·  85614 Kirchseeon  ·  USt-IdNr. DE123456789")
    pdf.setFont("Helvetica-Bold", 13)
    pdf.drawString(60, 720, "Rechnung")
    pdf.setFont("Helvetica", 10)
    pdf.drawString(60, 696, f"Rechnungsnummer: {invoice['invoice_no']}")
    pdf.drawString(60, 681, f"Rechnungsdatum: {invoice['invoice_date']}")
    pdf.drawString(60, 666, "Kundennummer: 4711")
    pdf.drawString(60, 630, "Artikel")
    pdf.drawString(430, 630, "Betrag")
    pdf.drawString(60, 610, "Montage und Konfiguration Arbeitsplatz")
    pdf.drawString(430, 610, money(invoice["net"] * 0.7))
    pdf.drawString(60, 594, "Material und Kleinteile")
    pdf.drawString(430, 594, money(invoice["net"] * 0.3))
    pdf.line(60, 580, 540, 580)
    pdf.drawString(330, 560, "Nettobetrag")
    pdf.drawString(430, 560, money(invoice["net"]))
    pdf.drawString(330, 544, "MwSt. 19 %")
    pdf.drawString(430, 544, money(invoice["vat"]))
    pdf.setFont("Helvetica-Bold", 10)
    pdf.drawString(330, 522, "Gesamtbetrag")
    pdf.drawString(430, 522, money(invoice["gross"]))
    pdf.setFont("Helvetica", 9)
    pdf.drawString(60, 490, "Alle Beträge in EUR.")
    pdf.drawString(60, 470, "Zahlbar innerhalb von 14 Tagen. Vielen Dank für Ihren Auftrag.")
    pdf.drawString(60, 80, "Sparkasse Ebersberg  ·  IBAN DE00 1234 5678 9012 3456 78")
    pdf.save()


def main() -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    truth = []
    for invoice in INVOICES:
        path = OUT / invoice["file"]
        draw(invoice, path)
        truth.append({key: value for key, value in invoice.items()})
        print(f"wrote {path.name}")
    (OUT / "expected.json").write_text(
        json.dumps(truth, ensure_ascii=False, indent=2), encoding="utf-8"
    )


if __name__ == "__main__":
    main()
