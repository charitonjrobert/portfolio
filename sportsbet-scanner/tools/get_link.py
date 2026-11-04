# -*- coding: utf-8 -*-
"""get_link.py - citeste URL-ul tunelului cloudflared + cheia de acces -> afiseaza linkul clientului.

Rulat de start_sportsbet.bat dupa ce serverul + tunelul au pornit.
"""
import os
import re
import json
import time

BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))  # sportsbet-app/
TOOLS = os.path.join(BASE, "tools")


def find_url():
    for log in ("cloudflared_err.log", "cloudflared_out.log"):
        p = os.path.join(TOOLS, log)
        if os.path.exists(p):
            try:
                txt = open(p, encoding="utf-8", errors="replace").read()
            except Exception:
                txt = open(p, errors="replace").read()
            m = re.search(r"https://[a-z0-9-]+\.trycloudflare\.com", txt)
            if m:
                return m.group(0)
    return None


url = None
for _ in range(15):  # pana la ~30s extra (pe langa cei 15s din bat)
    url = find_url()
    if url:
        break
    time.sleep(2)

key = None
cfg = os.path.join(BASE, "backend", "config.json")
if os.path.exists(cfg):
    try:
        key = json.load(open(cfg, encoding="utf-8")).get("ui", {}).get("access_key")
    except Exception:
        pass

print()
print("=" * 64)
if url:
    print("LINK CLIENT (MicrobistBets):")
    print((url + "/?k=" + key) if key else url)
else:
    print("!! Nu am gasit URL-ul tunelului inca.")
    print("   Verifica tools/cloudflared_err.log (linia cu trycloudflare.com).")
print("=" * 64)
print()
