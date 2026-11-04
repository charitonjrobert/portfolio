"""User-editable OCR options, persisted next to the database."""
from __future__ import annotations

import json
from pathlib import Path
from typing import Any

DEFAULTS: dict[str, Any] = {
    "lang": "deu+eng",
    "dpi": 300,
    "tesseract_cmd": "",
    "keep_original": True,
}

ALLOWED_LANG = ("deu+eng", "deu", "eng")
ALLOWED_DPI = (150, 300, 400)


class Settings:
    def __init__(self, path: str | Path = "data/settings.json") -> None:
        self.path = Path(path)
        self.path.parent.mkdir(parents=True, exist_ok=True)

    def load(self) -> dict[str, Any]:
        data = dict(DEFAULTS)
        if self.path.exists():
            try:
                stored = json.loads(self.path.read_text(encoding="utf-8"))
                if isinstance(stored, dict):
                    data.update({k: v for k, v in stored.items() if k in DEFAULTS})
            except (OSError, json.JSONDecodeError):
                pass
        return self.validate(data)

    def save(self, incoming: dict[str, Any]) -> dict[str, Any]:
        merged = {**self.load(), **{k: v for k, v in incoming.items() if k in DEFAULTS}}
        clean = self.validate(merged)
        self.path.write_text(json.dumps(clean, ensure_ascii=False, indent=2), encoding="utf-8")
        return clean

    @staticmethod
    def validate(values: dict[str, Any]) -> dict[str, Any]:
        clean = dict(DEFAULTS)
        clean["lang"] = values.get("lang") if values.get("lang") in ALLOWED_LANG else DEFAULTS["lang"]
        try:
            dpi = int(values.get("dpi", DEFAULTS["dpi"]))
        except (TypeError, ValueError):
            dpi = DEFAULTS["dpi"]
        clean["dpi"] = dpi if dpi in ALLOWED_DPI else DEFAULTS["dpi"]
        clean["tesseract_cmd"] = str(values.get("tesseract_cmd") or "").strip()
        clean["keep_original"] = bool(values.get("keep_original", True))
        return clean
