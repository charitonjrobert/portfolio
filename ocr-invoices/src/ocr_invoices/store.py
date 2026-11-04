"""SQLite storage with de-duplication on (vendor, invoice_no)."""
from __future__ import annotations

import sqlite3
from pathlib import Path
from typing import Any

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
    file_path    TEXT,
    created_at   TEXT NOT NULL DEFAULT (datetime('now')),
    UNIQUE (vendor, invoice_no)
);
"""

EDITABLE = ("vendor", "invoice_date", "invoice_no", "net", "vat", "gross", "currency")


class Store:
    def __init__(self, path: str | Path = "data/invoices.db") -> None:
        self.path = Path(path)
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self.connection = sqlite3.connect(self.path, check_same_thread=False)
        self.connection.row_factory = sqlite3.Row
        self.connection.executescript(SCHEMA)
        self._migrate()

    def _migrate(self) -> None:
        columns = {row[1] for row in self.connection.execute("PRAGMA table_info(invoices)")}
        if "file_path" not in columns:
            self.connection.execute("ALTER TABLE invoices ADD COLUMN file_path TEXT")
            self.connection.commit()

    def save(self, invoice: Invoice, file_path: str | None = None) -> bool:
        """Insert the invoice. Returns False when it was already stored."""
        if not invoice.invoice_no and not invoice.vendor:
            return False
        try:
            self.connection.execute(
                """INSERT INTO invoices
                   (vendor, invoice_date, invoice_no, net, vat, gross, currency, source, file_path)
                   VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)""",
                (invoice.vendor, invoice.invoice_date, invoice.invoice_no,
                 invoice.net, invoice.vat, invoice.gross, invoice.currency,
                 invoice.source, file_path),
            )
            self.connection.commit()
            return True
        except sqlite3.IntegrityError:
            return False

    def all(self) -> list[sqlite3.Row]:
        return list(self.connection.execute("SELECT * FROM invoices ORDER BY id"))

    def get(self, invoice_id: int) -> sqlite3.Row | None:
        return self.connection.execute(
            "SELECT * FROM invoices WHERE id = ?", (invoice_id,)
        ).fetchone()

    def update(self, invoice_id: int, fields: dict[str, Any]) -> sqlite3.Row | None:
        """Patch editable fields. Unknown keys and empty strings are ignored."""
        patch = {k: v for k, v in fields.items() if k in EDITABLE and v != ""}
        if not patch:
            return self.get(invoice_id)
        assignments = ", ".join(f"{key} = ?" for key in patch)
        values = [patch[key] for key in patch] + [invoice_id]
        try:
            self.connection.execute(f"UPDATE invoices SET {assignments} WHERE id = ?", values)
            self.connection.commit()
        except sqlite3.IntegrityError:
            raise ValueError("duplicate invoice")
        return self.get(invoice_id)

    def delete(self, invoice_id: int) -> bool:
        cursor = self.connection.execute("DELETE FROM invoices WHERE id = ?", (invoice_id,))
        self.connection.commit()
        return cursor.rowcount > 0

    def close(self) -> None:
        self.connection.close()
