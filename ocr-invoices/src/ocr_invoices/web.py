"""Local dashboard for ocr-invoices: scan, review, correct, export.

Run with:  python -m ocr_invoices.web
"""
from __future__ import annotations

import csv
import io
import os
import shutil
from pathlib import Path
from typing import Any

from fastapi import FastAPI, HTTPException, Request, UploadFile
from fastapi.responses import FileResponse, HTMLResponse, JSONResponse, StreamingResponse
from fastapi.staticfiles import StaticFiles

from . import ocr
from .extract import extract
from .models import FIELDS
from .settings import Settings
from .store import Store

PACKAGE_DIR = Path(__file__).resolve().parent
WEB_DIR = PACKAGE_DIR / "web"
PROJECT_ROOT = PACKAGE_DIR.parents[1]
DATA_DIR = Path(os.environ.get("OCR_DATA_DIR") or (PROJECT_ROOT / "data"))

app = FastAPI(title="OCR Invoices", version="0.2.0")
store = Store(DATA_DIR / "invoices.db")
settings = Settings(DATA_DIR / "settings.json")
(DATA_DIR / "files").mkdir(parents=True, exist_ok=True)


def _row_to_dict(row: Any) -> dict[str, Any]:
    return {
        "id": row["id"],
        "vendor": row["vendor"],
        "invoice_date": row["invoice_date"],
        "invoice_no": row["invoice_no"],
        "net": row["net"],
        "vat": row["vat"],
        "gross": row["gross"],
        "currency": row["currency"],
        "source": row["source"],
        "has_file": bool(row["file_path"]),
        "created_at": row["created_at"],
        "missing": [name for name in FIELDS if row[name] in (None, "")],
    }


@app.get("/", response_class=HTMLResponse)
def index() -> str:
    return (WEB_DIR / "index.html").read_text(encoding="utf-8")


app.mount("/static", StaticFiles(directory=str(WEB_DIR)), name="static")


@app.get("/api/invoices")
def list_invoices() -> dict[str, Any]:
    return {"invoices": [_row_to_dict(row) for row in store.all()]}


@app.patch("/api/invoices/{invoice_id}")
async def patch_invoice(invoice_id: int, request: Request) -> dict[str, Any]:
    if store.get(invoice_id) is None:
        raise HTTPException(404, "invoice not found")
    payload = await request.json()
    if not isinstance(payload, dict):
        raise HTTPException(400, "expected a JSON object")
    clean: dict[str, Any] = {}
    for key, value in payload.items():
        if key not in FIELDS:
            continue
        if key in ("net", "vat", "gross"):
            if value in (None, ""):
                clean[key] = None
                continue
            try:
                clean[key] = round(float(str(value).replace(",", ".")), 2)
            except ValueError:
                raise HTTPException(400, f"{key} must be a number")
        else:
            clean[key] = str(value).strip()
    try:
        row = store.update(invoice_id, clean)
    except ValueError as error:
        raise HTTPException(409, str(error))
    return _row_to_dict(row)


@app.delete("/api/invoices/{invoice_id}")
def delete_invoice(invoice_id: int) -> dict[str, Any]:
    row = store.get(invoice_id)
    if row is None:
        raise HTTPException(404, "invoice not found")
    if row["file_path"]:
        Path(row["file_path"]).unlink(missing_ok=True)
    store.delete(invoice_id)
    return {"ok": True}


@app.post("/api/scan")
async def scan(file: UploadFile) -> dict[str, Any]:
    options = settings.load()
    if options["tesseract_cmd"]:
        import os

        os.environ["OCR_TESSERACT_CMD"] = options["tesseract_cmd"]
    if not ocr.available():
        raise HTTPException(503, "Tesseract not found. Set the path in the options.")

    suffix = Path(file.filename or "upload").suffix.lower()
    if suffix not in (".pdf", ".png", ".jpg", ".jpeg", ".tif", ".tiff"):
        raise HTTPException(400, f"unsupported file type: {suffix or 'none'}")

    upload_dir = DATA_DIR / "files"
    upload_dir.mkdir(parents=True, exist_ok=True)
    temporary = upload_dir / f"_upload{suffix}"
    with temporary.open("wb") as handle:
        shutil.copyfileobj(file.file, handle)

    try:
        text = ocr.file_to_text(temporary, lang=options["lang"], dpi=options["dpi"])
    except Exception as error:
        temporary.unlink(missing_ok=True)
        raise HTTPException(422, f"OCR failed: {error}")
    if not text.strip():
        temporary.unlink(missing_ok=True)
        raise HTTPException(422, "no text recognised in this file")

    invoice = extract(text, source=file.filename or temporary.name)
    stored = store.save(invoice)
    if not stored:
        temporary.unlink(missing_ok=True)
        raise HTTPException(409, "this invoice is already in the database")

    row = [r for r in store.all() if r["invoice_no"] == invoice.invoice_no][-1]
    if options["keep_original"]:
        final = upload_dir / f"{row['id']}{suffix}"
        temporary.replace(final)
        store.connection.execute(
            "UPDATE invoices SET file_path = ? WHERE id = ?", (str(final), row["id"])
        )
        store.connection.commit()
    else:
        temporary.unlink(missing_ok=True)

    return {"invoice": _row_to_dict(store.get(row["id"])), "found": invoice.found()}


@app.get("/api/files/{invoice_id}")
def get_file(invoice_id: int) -> FileResponse:
    row = store.get(invoice_id)
    if row is None or not row["file_path"]:
        raise HTTPException(404, "no original stored for this invoice")
    path = Path(row["file_path"])
    if not path.exists():
        raise HTTPException(404, "original file is missing on disk")
    return FileResponse(path)


@app.get("/api/export.csv")
def export_csv() -> StreamingResponse:
    buffer = io.StringIO()
    writer = csv.writer(buffer, delimiter=";")
    writer.writerow(list(FIELDS))
    for row in store.all():
        writer.writerow([row[name] for name in FIELDS])
    buffer.seek(0)
    return StreamingResponse(
        iter([buffer.getvalue()]),
        media_type="text/csv; charset=utf-8",
        headers={"Content-Disposition": 'attachment; filename="invoices.csv"'},
    )


@app.get("/api/settings")
def get_settings() -> dict[str, Any]:
    return settings.load()


@app.post("/api/settings")
async def post_settings(request: Request) -> dict[str, Any]:
    payload = await request.json()
    if not isinstance(payload, dict):
        raise HTTPException(400, "expected a JSON object")
    return settings.save(payload)


@app.get("/api/stats")
def stats() -> dict[str, Any]:
    rows = store.all()
    complete = sum(1 for row in rows if all(row[name] not in (None, "") for name in FIELDS))
    return {
        "total": len(rows),
        "complete": complete,
        "with_missing_fields": len(rows) - complete,
        "last_scan": rows[-1]["created_at"] if rows else None,
        "tesseract_ready": ocr.available(),
        "lang": settings.load()["lang"],
    }


def main() -> None:
    import uvicorn

    uvicorn.run(app, host="127.0.0.1", port=8020)


if __name__ == "__main__":
    main()
