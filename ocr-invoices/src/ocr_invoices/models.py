"""Data model for one invoice extracted from a scanned document."""
from __future__ import annotations

from dataclasses import dataclass, asdict
from typing import Optional

FIELDS = ("vendor", "invoice_date", "invoice_no", "net", "vat", "gross", "currency")


@dataclass
class Invoice:
    vendor: Optional[str] = None
    invoice_date: Optional[str] = None
    invoice_no: Optional[str] = None
    net: Optional[float] = None
    vat: Optional[float] = None
    gross: Optional[float] = None
    currency: Optional[str] = None
    source: str = ""

    def found(self) -> int:
        """How many of the seven target fields were extracted."""
        return sum(1 for name in FIELDS if getattr(self, name) not in (None, ""))

    def missing(self) -> list[str]:
        return [name for name in FIELDS if getattr(self, name) in (None, "")]

    def as_row(self) -> dict:
        return asdict(self)

    def table_row(self) -> list[str]:
        def fmt(value: Optional[float]) -> str:
            return "" if value is None else f"{value:.2f}"
        return [
            self.vendor or "",
            self.invoice_date or "",
            self.invoice_no or "",
            fmt(self.net),
            fmt(self.vat),
            fmt(self.gross),
            self.currency or "",
        ]
