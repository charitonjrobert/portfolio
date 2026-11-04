"""Command line interface: scan, list, export."""
from __future__ import annotations

import argparse
import csv
import sys
from pathlib import Path

from . import ocr
from .extract import extract
from .store import Store

HEADER = ["vendor", "date", "invoice_no", "net", "vat", "gross", "currency"]


def _print_table(rows: list[list[str]]) -> None:
    widths = [max(len(str(row[i])) for row in [HEADER] + rows) for i in range(len(HEADER))]
    line = "  ".join(str(cell).ljust(widths[i]) for i, cell in enumerate(HEADER))
    print(line)
    print("-" * len(line))
    for row in rows:
        print("  ".join(str(cell).ljust(widths[i]) for i, cell in enumerate(row)))


def cmd_scan(args: argparse.Namespace) -> int:
    if not ocr.available():
        print("Tesseract not found. Set OCR_TESSERACT_CMD or run the portable install.",
              file=sys.stderr)
        return 2
    store = Store(args.db)
    rows: list[list[str]] = []
    for pattern in args.files:
        for path in sorted(Path().glob(pattern)) if any(c in pattern for c in "*?") else [Path(pattern)]:
            if not path.exists():
                print(f"! skip (not found): {path}", file=sys.stderr)
                continue
            try:
                text = ocr.file_to_text(path)
            except Exception as error:  # corrupted file, encrypted PDF, unreadable image
                print(f"! skip ({error}): {path}", file=sys.stderr)
                continue
            if not text.strip():
                print(f"! skip (no text recognised): {path}", file=sys.stderr)
                continue
            invoice = extract(text, source=str(path))
            stored = store.save(invoice)
            print(f"{'saved ' if stored else 'dup   '}{path.name}: "
                  f"{invoice.found()}/7 fields, missing: {', '.join(invoice.missing()) or '-'}")
            rows.append(invoice.table_row())
    if rows:
        print()
        _print_table(rows)
    store.close()
    return 0


def cmd_list(args: argparse.Namespace) -> int:
    store = Store(args.db)
    rows = [[row["vendor"] or "", row["invoice_date"] or "", row["invoice_no"] or "",
             "" if row["net"] is None else f"{row['net']:.2f}",
             "" if row["vat"] is None else f"{row['vat']:.2f}",
             "" if row["gross"] is None else f"{row['gross']:.2f}",
             row["currency"] or ""] for row in store.all()]
    _print_table(rows) if rows else print("(empty)")
    store.close()
    return 0


def cmd_export(args: argparse.Namespace) -> int:
    store = Store(args.db)
    with open(args.out, "w", newline="", encoding="utf-8") as handle:
        writer = csv.writer(handle, delimiter=";")
        writer.writerow(["vendor", "invoice_date", "invoice_no", "net", "vat", "gross", "currency"])
        for row in store.all():
            writer.writerow([row["vendor"], row["invoice_date"], row["invoice_no"],
                             row["net"], row["vat"], row["gross"], row["currency"]])
    print(f"exported to {args.out}")
    store.close()
    return 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="ocr_invoices", description="Invoice OCR to SQLite")
    parser.add_argument("--db", default="data/invoices.db")
    sub = parser.add_subparsers(dest="command", required=True)
    scan = sub.add_parser("scan", help="OCR files and store the fields")
    scan.add_argument("files", nargs="+")
    scan.set_defaults(func=cmd_scan)
    listing = sub.add_parser("list", help="show stored invoices")
    listing.set_defaults(func=cmd_list)
    export = sub.add_parser("export", help="write CSV")
    export.add_argument("--out", default="invoices.csv")
    export.set_defaults(func=cmd_export)
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    return args.func(args)


if __name__ == "__main__":
    raise SystemExit(main())
