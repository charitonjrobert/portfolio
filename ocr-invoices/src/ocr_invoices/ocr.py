"""OCR layer: turn a PDF or image into plain text.

Uses Tesseract. The binary is looked up in this order:
  1. env OCR_TESSERACT_CMD
  2. <project>/vendor/tesseract/tesseract.exe   (portable install, no admin needed)
  3. tesseract on PATH
"""
from __future__ import annotations

import os
import shutil
from pathlib import Path

import pytesseract
from PIL import Image

PROJECT_ROOT = Path(__file__).resolve().parents[2]
LANG = "deu+eng"
RENDER_DPI = 300


class OcrUnavailable(RuntimeError):
    """Raised when the Tesseract binary cannot be found."""


def _find_tesseract() -> str:
    env_cmd = os.environ.get("OCR_TESSERACT_CMD")
    if env_cmd and Path(env_cmd).exists():
        return env_cmd
    portable = PROJECT_ROOT / "vendor" / "tesseract" / "tesseract.exe"
    if portable.exists():
        os.environ.setdefault("TESSDATA_PREFIX", str(portable.parent / "tessdata"))
        return str(portable)
    on_path = shutil.which("tesseract")
    if on_path:
        return on_path
    raise OcrUnavailable(
        "Tesseract not found. Set OCR_TESSERACT_CMD or place it in vendor/tesseract/."
    )


def available() -> bool:
    try:
        _find_tesseract()
        return True
    except OcrUnavailable:
        return False


def _configure() -> None:
    pytesseract.pytesseract.tesseract_cmd = _find_tesseract()


def _pdf_pages(path: Path) -> list[Image.Image]:
    import pypdfium2 as pdfium

    pages: list[Image.Image] = []
    document = pdfium.PdfDocument(str(path))
    scale = RENDER_DPI / 72
    try:
        for index in range(len(document)):
            bitmap = document[index].render(scale=scale)
            pages.append(bitmap.to_pil().convert("RGB"))
    finally:
        document.close()
    return pages


def image_to_text(image: Image.Image) -> str:
    _configure()
    config = "--oem 3 --psm 6"
    return pytesseract.image_to_string(image, lang=LANG, config=config)


def file_to_text(path: str | Path) -> str:
    """Return the OCR text of a PDF (all pages) or of an image file."""
    target = Path(path)
    if not target.exists():
        raise FileNotFoundError(target)
    if target.suffix.lower() == ".pdf":
        chunks = [image_to_text(page) for page in _pdf_pages(target)]
        return "\n".join(chunks)
    with Image.open(target) as image:
        return image_to_text(image.convert("RGB"))
