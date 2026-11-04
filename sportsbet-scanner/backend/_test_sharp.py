# -*- coding: utf-8 -*-
"""Offline check (0 API calls): how optimistic was the old edge vs the sharp one?"""
import json
from collections import Counter

from sharp import reference, SHARP_BOOKS, h2h_books
from value import find_value_bets, best_book_for_side
from probabilities import implied_probability
from models import predict_1x2

cache = json.load(open("odds_cache.json", encoding="utf-8"))

kinds = Counter()
sharp_books = Counter()
rows = []
for group, events in cache.items():
    if not isinstance(events, list):
        continue
    for ev in events:
        ref = reference(ev)
        kinds[ref["kind"]] += 1
        if ref["kind"] == "sharp":
            sharp_books[ref["bookmaker"]] += 1
        if ref["kind"] == "None":
            continue
        pred = predict_1x2(ev, group)
        if not pred:
            continue
        for side in ("home", "draw", "away"):
            mp = pred.get(side)
            if not mp:
                continue
            from sharp import outcome_name
            name = outcome_name(ev, side)
            market = (ref.get("probs") or {}).get(name)
            book = best_book_for_side(ev, side)
            if market is None or not book:
                continue
            edge_real = (mp - market) * 100
            edge_best = (mp - implied_probability(book["price"])) * 100
            rows.append((group, ev.get("home_team"), ev.get("away_team"), side,
                         round(mp, 3), round(market, 3), round(edge_real, 2), round(edge_best, 2)))

print("referinte de piata gasite:")
for k, v in kinds.most_common():
    print(f"   {str(k):<10} {v}")
print("case folosite ca referinta sharp:", dict(sharp_books))

n = len(rows)
avg_real = sum(r[6] for r in rows) / n if n else 0
avg_best = sum(r[7] for r in rows) / n if n else 0
print(f"\n{n} selecții analizate")
print(f"   avantaj mediu FAȚĂ DE PIAȚA SHARP : {avg_real:+.2f}%")
print(f"   avantaj mediu FAȚĂ DE CEA MAI BUNĂ COTĂ: {avg_best:+.2f}%")
big = [r for r in rows if r[7] >= 4.0]
big_real_pos = [r for r in big if r[6] > 0]
print(f"   vechi: {len(big)} selecții cu 'avantaj' >= 4%  ->  dintre ele, reale pozitive: {len(big_real_pos)} ({round(100*len(big_real_pos)/max(1,len(big)))}%)")

print("\nexemple (cele mai mari avantaje vechi), real vs vechi:")
for r in sorted(rows, key=lambda r: -r[7])[:8]:
    print(f"   {r[1][:22]:<22} – {r[2][:22]:<22} {r[3]:<5} model {r[4]*100:4.1f}% | piața {r[5]*100:4.1f}% | real {r[6]:+6.2f}% | vechi {r[7]:+6.2f}%")

vbs = []
for group, events in cache.items():
    if isinstance(events, list):
        vbs.extend(find_value_bets(events, group, 4.0))
print(f"\nfind_value_bets (prag 4% real): {len(vbs)} value bets")
for vb in vbs[:6]:
    print(f"   {vb['home_team'][:20]:<20} {vb['side']:<5} real {vb['edge_pct']:+.2f}% (vechi {vb['edge_best_pct']:+.2f}%) sursa={vb['market_kind']}/{vb['market_source']}")
