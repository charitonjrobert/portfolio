# -*- coding: utf-8 -*-
"""Rotate the MicrobistBets access key (run when a link might have leaked).

Usage:
    python tools/rotate_key.py            # rotate + print the fresh link
    python tools/rotate_key.py --check    # only show the current key/link, change nothing

Why: the shared link IS the password. If it ends up somewhere public, this makes it
useless instantly (old cookies stop matching) and gives you a new link to send.
The server reads config.json at startup, so restart uvicorn afterwards.
"""
import io
import json
import os
import re
import secrets
import sys

BACKEND = r"C:\Projects\sportsbet-app\backend"
CONFIG = os.path.join(BACKEND, "config.json")
TUNNEL_LOG = r"C:\Users\eusun\AppData\Local\Temp\opencode\tunnel.log"


def tunnel_url():
    try:
        text = io.open(TUNNEL_LOG, encoding="utf-8", errors="ignore").read()
        hits = re.findall(r"https://[a-z0-9-]+\.trycloudflare\.com", text)
        return hits[-1] if hits else None
    except OSError:
        return None


def main():
    check = "--check" in sys.argv
    with io.open(CONFIG, encoding="utf-8") as f:
        cfg = json.load(f)
    ui = cfg.setdefault("ui", {})
    key = (ui.get("access_key") or "").strip()

    if check:
        print("cheie curenta:", key or "(lipsa)")
    else:
        key = secrets.token_urlsafe(24)
        ui["access_key"] = key
        with io.open(CONFIG, "w", encoding="utf-8") as f:
            json.dump(cfg, f, ensure_ascii=False, indent=2)
        print("CHEIE NOUA:", key)
        print("(vechea cheie nu mai functioneaza; cookie-urile vechi sunt inutile)")

    base = tunnel_url()
    if base:
        print("\nLink de trimis (cu cheie):")
        print(f"{base}/?k={key}")
    else:
        print("\nTunelul nu e pornit -> linkul local: http://127.0.0.1:8000/?k=" + key)
    if not check:
        print("\nReporneste serverul ca sa incarce cheia noua:")
        print(r"  cd C:\Projects\sportsbet-app\backend && python -m uvicorn main:app --host 127.0.0.1 --port 8000")


if __name__ == "__main__":
    main()
