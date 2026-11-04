"""SQLite storage with de-duplication on (vendor, invoice_no)."""
from __future__ import annotations

import sqlite3
from pathlib import Path

from .models import Invoice

SCHEMA = """
CREATE TABLE IF NOT EXISTS invoices (
    id           INTEGER PRIMARY KEY AUTOINCREMENT,
    vendor       TEXT,
    invoice_date TEXT,
    invoice_no   TEXT,
    net          REAL,
    vat          REAL,
    gross        REAL,
    currency     TEXT,
    source       TEXT,
    created_at   TEXT NOT NULL DEFAULT (datetime('now')),
    UNIQUE (vendor, invoice_no)
);
"""


class Store:
    def __init__(self, path: str | Path = "data/invoices.db") -> None:
        self.path = Path(path)
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self.connection = sqlite3.connect(self.path)
        self.connection.row_factory = sqlite3.Row
        self.connection.executescript(SCHEMA)

    def save(self, invoice: Invoice) -> bool:
        """Insert the invoice. Returns False when it was already stored."""
        if not invoice.invoice_no and not invoice.vendor:
            return False
        try:
            self.connection.execute(
                """INSERT INTO invoices
                   (vendor, invoice_date, invoice_no, net, vat, gross, currency, source)
                   VALUES (?, ?, ?, ?, ?, ?, ?, ?)""",
                (invoice.vendor, invoice.invoice_date, invoice.invoice_no,
                 invoice.net, invoice.vat, invoice.gross, invoice.currency, invoice.source),
            )
            self.connection.commit()
            return True
        except sqlite3.IntegrityError:
            return False

    def all(self) -> list[sqlite3.Row]:
        return list(self.connection.execute("SELECT * FROM invoices ORDER BY id"))

    def close(self) -> None:
        self.connection.close()
