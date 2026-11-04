# -*- coding: utf-8 -*-
"""Real results -> automatic settlement of the simulation wallet.

Sources (13 Oct 2026, both verified against the live APIs):
  * football-data.org  /v4/matches?status=FINISHED  -> free, 10 req/min, 12 competitions
  * the-odds-api       /v4/sports/{key}/scores/     -> works on our key, costs 1 request of 500/month

Matching order:
  1. exact event id from the-odds-api (the ids we saved when the bet was placed);
  2. fallback: both team names + date within +-1 day (football-data.org naming differs).
Anything that cannot be matched stays open and is reported, never guessed.
"""
import time
from datetime import datetime, timedelta, timezone

import requests

ODDSAPI_SCORES = "https://api.the-odds-api.com/v4/sports/{key}/scores/"

# sport_group -> the-odds-api sport key (used when the bet has no sport_key stored)
GROUP_TO_KEY = {
    "basketball": "basketball_nba",
    "icehockey": "icehockey_nhl",
    "americanfootball": "americanfootball_nfl",
    "mma": "mma_mixed_martial_arts",
    "boxing": "boxing_boxing",
}


def norm(text):
    return "".join(ch for ch in (text or "").lower() if ch.isalnum())


def _parse_dt(value):
    try:
        return datetime.fromisoformat(str(value).replace("Z", "+00:00"))
    except (ValueError, TypeError):
        return None


def fetch_oddsapi_scores(sport_key, api_key, days_from=3, timeout=30):
    """Return (results_by_event_id, meta). Costs 1 request.

    The free plan only accepts daysFrom 1..3 (4+ returns HTTP 422), so it is clamped.
    """
    if not sport_key or not api_key:
        return {}, {"error": "missing sport key or api key"}
    try:
        days_from = max(1, min(3, int(days_from)))
    except (TypeError, ValueError):
        days_from = 3
    try:
        resp = requests.get(
            ODDSAPI_SCORES.format(key=sport_key),
            params={"daysFrom": days_from, "apiKey": api_key},
            timeout=timeout,
        )
    except requests.RequestException as exc:
        return {}, {"error": str(exc)}
    meta = {
        "status": resp.status_code,
        "remaining": resp.headers.get("x-requests-remaining"),
        "sport_key": sport_key,
    }
    if resp.status_code != 200:
        meta["error"] = resp.text[:200]
        return {}, meta
    out = {}
    for event in resp.json() or []:
        scores = {s.get("name"): s.get("score") for s in (event.get("scores") or [])}
        home, away = event.get("home_team"), event.get("away_team")
        out[event.get("id")] = {
            "home": home,
            "away": away,
            "completed": bool(event.get("completed")),
            "home_score": _num(scores.get(home)),
            "away_score": _num(scores.get(away)),
            "commence_time": event.get("commence_time"),
        }
    return out, meta


def _num(value):
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def fetch_finished_football(fd, days=6):
    """Finished football matches from football-data.org (free)."""
    if not fd or not getattr(fd, "configured", False):
        return [], {"error": "football-data.org not configured"}
    now = datetime.now(timezone.utc)
    try:
        data = fd.matches(
            date_from=(now - timedelta(days=days)).date().isoformat(),
            date_to=(now + timedelta(days=1)).date().isoformat(),
            status="FINISHED",
        )
    except Exception as exc:  # rate limit / 400 / network
        return [], {"error": str(exc)}
    out = []
    for m in data.get("matches") or []:
        ft = ((m.get("score") or {}).get("fullTime")) or {}
        out.append({
            "home": (m.get("homeTeam") or {}).get("name"),
            "away": (m.get("awayTeam") or {}).get("name"),
            "home_score": _num(ft.get("home")),
            "away_score": _num(ft.get("away")),
            "utcDate": m.get("utcDate"),
            "competition": (m.get("competition") or {}).get("name"),
            "completed": True,
        })
    return out, {"count": len(out)}


def _side_from_scores(home_score, away_score):
    if home_score is None or away_score is None:
        return None
    if home_score > away_score:
        return "home"
    if home_score < away_score:
        return "away"
    return "draw"


def _match_by_names(bet, finished):
    """Fallback matcher: both teams + date within +-1 day."""
    bh, ba = norm(bet.get("home_team")), norm(bet.get("away_team"))
    if not bh or not ba:
        return None
    bet_dt = _parse_dt(bet.get("commence_time"))
    for item in finished:
        ih, ia = norm(item.get("home")), norm(item.get("away"))
        if not ih or not ia:
            continue
        ok = (bh in ih or ih in bh) and (ba in ia or ia in ba)
        if not ok:
            continue
        if bet_dt is not None:
            item_dt = _parse_dt(item.get("utcDate"))
            if item_dt is not None and abs((item_dt - bet_dt).total_seconds()) > 36 * 3600:
                continue
        return item
    return None


def settle_open_bets(storage, odds_api_key, fd, ttl=None, max_scores_calls=4, ttl_seconds=1800):
    """Settle every open simulation bet that now has a real result.

    Returns a summary dict (settled list, still_open, sources used, quota left).
    """
    open_bets = storage.list_open_bets()
    if not open_bets:
        return {"settled": [], "matched": 0, "still_open": 0, "note": "no open bets"}

    by_key = {}
    for bet in open_bets:
        key = (bet.get("sport_key") or GROUP_TO_KEY.get(bet.get("sport") or "", "") or "").strip()
        by_key.setdefault(key, []).append(bet)

    results_by_key = {}
    fd_finished = []
    sources = []
    calls = 0
    for key, bets in by_key.items():
        needs_scores = any(b.get("event_id") and key for b in bets)
        if needs_scores and calls < max_scores_calls:
            cache_key = f"scores|{key}"
            cached = ttl.get(cache_key, ttl_seconds) if ttl else None
            if cached is None:
                data, meta = fetch_oddsapi_scores(key, odds_api_key)
                calls += 1
                results_by_key[key] = data
                sources.append({"sport_key": key, "events": len(data), **meta})
                if ttl:
                    ttl.set(cache_key, data)
            else:
                results_by_key[key] = cached
                sources.append({"sport_key": key, "events": len(cached), "cached": True})
        if not fd_finished and (key == "" or "soccer" in (key or "").lower()):
            fd_finished, meta = fetch_finished_football(fd)
            if fd_finished:
                sources.append({"source": "football-data.org", **meta})

    settled, unmatched = [], []
    for bet in open_bets:
        key = (bet.get("sport_key") or GROUP_TO_KEY.get(bet.get("sport") or "", "") or "").strip()
        event_id = str(bet.get("event_id") or "")
        hit = (results_by_key.get(key) or {}).get(event_id)
        side = None
        score_text = ""
        if hit and hit.get("completed"):
            side = _side_from_scores(hit.get("home_score"), hit.get("away_score"))
            score_text = f"{int(hit['home_score'])}-{int(hit['away_score'])}" if side else ""
        if side is None:
            fallback = _match_by_names(bet, fd_finished)
            if fallback:
                side = _side_from_scores(fallback.get("home_score"), fallback.get("away_score"))
                if side:
                    score_text = f"{int(fallback['home_score'])}-{int(fallback['away_score'])}"
        if side is None:
            unmatched.append({"id": bet.get("id"), "event": bet.get("event")})
            continue
        bet_side = (bet.get("side") or "").strip()
        if bet_side not in ("home", "draw", "away"):
            unmatched.append({"id": bet.get("id"), "event": bet.get("event"), "reason": "unknown side"})
            continue
        won = bet_side == side
        updated = storage.resolve_bet(bet.get("id"), won, score_text)
        if updated:
            settled.append({
                "id": updated.get("id"),
                "event": updated.get("event"),
                "outcome": updated.get("outcome"),
                "result": score_text,
                "won": won,
                "profit": updated.get("profit"),
            })

    return {
        "settled": settled,
        "settled_count": len(settled),
        "still_open": len(unmatched),
        "still_open_examples": unmatched[:5],
        "sources": sources,
        "scores_api_calls": calls,
    }
