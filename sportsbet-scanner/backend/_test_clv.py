# -*- coding: utf-8 -*-
"""Offline check of the sharp-reference / CLV additions (no API calls, temp DB)."""
import os
import tempfile

from storage import Storage
from sharp import reference, sides

tmp = tempfile.mkdtemp()
db = os.path.join(tmp, "t.db")
cache = os.path.join(tmp, "c.json")

st = Storage(cache_file=cache, db_file=db)
p = st.ensure_player("client")
print("player initial:", p["initial"])

st.add_wallet_bet({
    "event": "A vs B", "outcome": "A", "side": "home", "market": "h2h",
    "stake": 10.0, "odds": 2.10, "edge_pct": 1.4, "model_prob": 0.52,
    "bookmaker": "Pinnacle", "status": "open", "profit": 0, "sport_group": "soccer",
    "sport": "soccer", "sport_key": "soccer_x", "player": "client", "event_id": "ev1",
    "home_team": "A", "away_team": "B", "commence_time": "2026-10-15T18:00:00Z",
    "sharp_odds": 2.05, "sharp_prob": 0.4878,
})
bets = st.list_wallet_bets("client")
b = bets[0]
print("bet salvat: id", b["id"], "sharp_odds", b.get("sharp_odds"), "sharp_prob", b.get("sharp_prob"),
      "closing_odds", b.get("closing_odds"), "clv_pct", b.get("clv_pct"))

st.set_closing(b["id"], 2.00, 0.50, "pre")
b = st.list_wallet_bets("client")[0]
print("dupa closing: closing_odds", b.get("closing_odds"), "kind", b.get("closing_kind"))

# ar trebui sa NU suprascrie a doua oara
st.set_closing(b["id"], 1.50, 0.66, "pre")
b = st.list_wallet_bets("client")[0]
print("a doua incercare (nu trebuie sa schimbe):", b.get("closing_odds"))

res = st.resolve_bet(b["id"], won=True, score_text="2-1")
print("dupa settle: status", res["status"], "profit", res["profit"], "clv_pct", res["clv_pct"],
      "(asteptat (2.10/2.00-1)*100 = 5.0)")

st.add_wallet_bet({
    "event": "C vs D", "outcome": "C", "side": "home", "market": "h2h",
    "stake": 5.0, "odds": 1.90, "edge_pct": -0.5, "model_prob": 0.52,
    "bookmaker": "Betfair", "status": "open", "profit": 0, "sport_group": "basketball",
    "sport": "basketball", "sport_key": "basketball_x", "player": "client", "event_id": "ev2",
    "home_team": "C", "away_team": "D", "commence_time": "2026-10-16T18:00:00Z",
    "sharp_odds": None, "sharp_prob": None,
})
b2 = st.list_wallet_bets("client")[0]
st.set_closing(b2["id"], 2.10, 0.476, "pre")  # closing mai bun -> CLV negativ
r2 = st.resolve_bet(b2["id"], won=False, score_text="0-1")
print("bet 2: clv_pct", r2["clv_pct"], "(asteptat (1.90/2.10-1)*100 = -9.52)")

# fara closing -> clv ramane None
st.add_wallet_bet({
    "event": "E vs F", "outcome": "E", "side": "home", "market": "h2h",
    "stake": 5.0, "odds": 1.80, "player": "client", "status": "open", "profit": 0,
    "sport": "soccer", "home_team": "E", "away_team": "F", "commence_time": "2026-10-17T18:00:00Z",
})
b3 = st.list_wallet_bets("client")[0]
r3 = st.resolve_bet(b3["id"], won=True, score_text="1-0")
print("bet 3 (fara closing): clv_pct", r3["clv_pct"], "(asteptat None)")

settled = [x for x in st.list_wallet_bets("client", limit=100) if x.get("status") in ("won", "lost")]
print("total settled:", len(settled), "| balances:", st.ensure_player("client")["balance"])

# --- sharp pe un eveniment real din cache ---
import json
cache_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "odds_cache.json")
data = json.load(open(cache_path, encoding="utf-8"))
shown = 0
for group, events in data.items():
    if not isinstance(events, list):
        continue
    for ev in events:
        ref = reference(ev)
        if ref["kind"] != "sharp":
            continue
        sd = sides(ev, ref)
        if not sd.get("home") or not sd.get("away"):
            continue
        print(f"\n[{group}] {ev.get('home_team')} - {ev.get('away_team')} | ref={ref['bookmaker']} "
              f"marja={ref['margin_pct']}%")
        for side in ("home", "draw", "away"):
            e = sd.get(side)
            if e:
                print(f"   {side:<5} {e['name'][:22]:<22} prob={e['prob']*100:5.1f}% "
                      f"sharp_odds={e.get('price')} fair={e.get('fair_odds')}")
        shown += 1
        if shown >= 2:
            break
    if shown >= 2:
        break
print("\nTOTUL OK")
