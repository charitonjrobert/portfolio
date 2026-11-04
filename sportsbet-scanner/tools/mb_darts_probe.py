# -*- coding: utf-8 -*-
"""mb_darts_probe.py — testeaza API-ul gratuit de darts (RapidAPI 'Darts API').

Confirma: competiții -> evenimente -> piețe -> cote. Când providerul revine, rulează:
    python tools/mb_darts_probe.py
Cheia se ia din: --key, sau env RAPIDAPI_KEY, sau
    C:\\Users\\eusun\\.config\\opencode-secrets\\rapidapi_darts_key.txt
"""
import os
import sys
import json
import argparse
import urllib.request

sys.stdout.reconfigure(encoding="utf-8", errors="replace")
HOST = "darts-api.p.rapidapi.com"
BASE = "https://" + HOST
KEYFILE = os.path.join(os.path.expanduser("~"), ".config", "opencode-secrets", "rapidapi_darts_key.txt")


def key_from_args():
    ap = argparse.ArgumentParser()
    ap.add_argument("--key", default="")
    a = ap.parse_args()
    if a.key:
        return a.key.strip()
    if os.environ.get("RAPIDAPI_KEY"):
        return os.environ["RAPIDAPI_KEY"].strip()
    if os.path.exists(KEYFILE):
        return open(KEYFILE, encoding="utf-8").read().strip()
    print("!! fara cheie (--key, RAPIDAPI_KEY sau", KEYFILE, ")"); sys.exit(2)


def call(key, path, method="GET", body=None):
    req = urllib.request.Request(
        BASE + path, method=method,
        data=(json.dumps(body).encode() if body else None),
        headers={"X-RapidAPI-Key": key, "X-RapidAPI-Host": HOST,
                 "Content-Type": "application/json"})
    try:
        with urllib.request.urlopen(req, timeout=30) as r:
            return r.status, r.read().decode("utf-8", "replace")
    except urllib.error.HTTPError as e:
        return e.code, e.read().decode("utf-8", "replace")
    except Exception as e:
        return 0, "ERR %s" % e


def main():
    key = key_from_args()
    print("cheie: %s...%s" % (key[:8], key[-6:]))
    st, body = call(key, "/competitions/3503")
    print("1) /competitions/3503 ->", st)
    print("   ", body[:400])
    if st != 200:
        print("\n(API indisponibil acum — reîncearcă mai târziu.)"); return
    try:
        comps = json.loads(body)
    except Exception:
        comps = None
    cid = None
    if isinstance(comps, list) and comps:
        cid = comps[0].get("id") or comps[0].get("competitionId")
    if not cid:
        print("(nu am gasit competitionId in raspuns)"); return
    st, body = call(key, "/event/3503/%s" % cid)
    print("2) /event/3503/%s -> %s" % (cid, st))
    print("   ", body[:400])
    try:
        evs = json.loads(body)
    except Exception:
        evs = None
    eid = None
    if isinstance(evs, list) and evs:
        eid = evs[0].get("id") or evs[0].get("eventId")
    if not eid:
        print("(nu am gasit eventId)"); return
    st, body = call(key, "/markets/3503/%s" % eid)
    print("3) /markets/3503/%s -> %s" % (eid, st))
    print("   ", body[:500])
    try:
        mk = json.loads(body)
    except Exception:
        mk = None
    mids = []
    if isinstance(mk, list):
        mids = [m.get("id") or m.get("marketId") for m in mk][:10]
    if mids:
        st, body = call(key, "/listMarketBook/3503", "POST", {"marketIds": mids})
        print("4) /listMarketBook/3503 ->", st)
        print("   ", body[:700])


if __name__ == "__main__":
    main()
