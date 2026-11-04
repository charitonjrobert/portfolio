# -*- coding: utf-8 -*-
"""On-demand match report for a simulation bet (added 15 Oct 2026).

Why: after a bet is settled, tapping it in the demo wallet should explain what
actually happened on the pitch (goals, cards, start/end, stoppage time, match
statistics) and - honestly - why the bet lost (or won), plus what to improve on
the next ticket.

Football data:
  * API-Football free plan lets us search `/fixtures?date=` for a day, then pull
    the full detail (`/fixtures?id=`): goals, cards, statistics, stoppage time.
  * A finished match never changes, so the fetched match data is cached ON DISK
    forever (5 years) => a report costs at most 2 API-Football requests ONCE per
    match, then zero.

The "why did it lose / what to improve" part is computed LOCALLY from numbers we
already stored when the bet was placed (model probability, odds, sharp
probability, edge, closing line, CLV). No AI and no extra request is spent on it;
the optional deep-dive is a button in the UI that asks the assistant.

The analysis is returned as language-neutral codes + numbers; the front-end
translates it (the app is trilingual RO/DE/EN, translations live in app.js).
"""
from __future__ import annotations

import unicodedata
from datetime import datetime, timedelta, timezone
from pathlib import Path

from ttl_cache import TtlCache

BACKEND_DIR = Path(__file__).resolve().parent
# Finished matches never change -> keep reports for years, not the 1-day shared cache.
MATCH_STORE = TtlCache(BACKEND_DIR / "reports.json", retention_seconds=5 * 365 * 86400)

# Safety cap so a bored user tapping every bet can never eat the API-Football day
# budget (60/day is already reserved for live alerts on a 100/day free plan).
REPORT_BUDGET_PER_DAY = 30

# Statistics worth showing, in display order (API-Football type names).
STAT_ORDER = [
    "Ball Possession", "Total Shots", "Shots on Goal", "Shots off Goal",
    "Blocked Shots", "Shots insidebox", "Shots outsidebox",
    "Corner Kicks", "Offsides", "Fouls", "Yellow Cards", "Red Cards",
    "Goalkeeper Saves", "Total passes", "Passes accurate", "Total passes %",
]

SOCCER_HINTS = ("soccer", "football", "futbol", "fussball")

# Same diacritic folding the search uses, so "Bodø/Glimt" matches API-Football's
# "Bodo/Glimt" (the two sources spell the same club differently).
_DIACRITICS = str.maketrans({
    "ø": "o", "æ": "ae", "ß": "ss", "đ": "d", "ð": "d", "þ": "th", "ł": "l",
    "ı": "i", "ĳ": "ij", "œ": "oe", "š": "s", "ž": "z", "č": "c", "ć": "c",
})


def norm(text):
    """Lowercase, strip accents and punctuation: 'Bodø/Glimt' -> 'bodoglimt'."""
    text = (text or "").translate(_DIACRITICS)
    text = unicodedata.normalize("NFKD", text)
    text = "".join(ch for ch in text if not unicodedata.combining(ch))
    return "".join(ch for ch in text.lower() if ch.isalnum())


def _parse_dt(value):
    try:
        return datetime.fromisoformat(str(value).replace("Z", "+00:00"))
    except (ValueError, TypeError):
        return None


def _f(value):
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def _stat_num(value):
    """'65%' -> 65.0 ; 12 -> 12.0 ; None -> None."""
    if value is None:
        return None
    if isinstance(value, (int, float)):
        return float(value)
    text = str(value).strip().replace("%", "")
    try:
        return float(text)
    except ValueError:
        return None


def is_football(bet):
    blob = " ".join(str(bet.get(k) or "") for k in ("sport", "sport_group", "sport_key")).lower()
    return any(h in blob for h in SOCCER_HINTS)


# ------------------------------------------------------------------ budget
def _budget(ttl):
    day = datetime.now(timezone.utc).date().isoformat()
    data = (ttl.get("report|budget") if ttl else None) or {}
    if data.get("day") != day:
        data = {"day": day, "calls": 0}
    return data


def _spend(ttl, data):
    data["calls"] = int(data.get("calls", 0)) + 1
    if ttl:
        ttl.set("report|budget", data)
    return data


# --------------------------------------------------------- fixture lookup
def _match_bet_to_fixture(bet, fixtures):
    """Find the fixture whose two teams are the bet's two teams.

    Returns (fixture, swapped) where `swapped` means the source lists the teams in
    the opposite order than the bet (so the bet 'side' must be flipped), or
    (None, False). Youth/U19 sides are only used when nothing else matches.
    """
    bh, ba = norm(bet.get("home_team")), norm(bet.get("away_team"))
    if not bh or not ba:
        return None, False
    direct, swapped, youth = None, None, None
    for fx in fixtures or []:
        teams = fx.get("teams") or {}
        ih = norm((teams.get("home") or {}).get("name"))
        ia = norm((teams.get("away") or {}).get("name"))
        if not ih or not ia:
            continue
        if (bh in ih or ih in bh) and (ba in ia or ia in ba):
            cand, sw = fx, False
        elif (bh in ia or ia in bh) and (ba in ih or ih in ba):
            cand, sw = fx, True
        else:
            continue
        blob = (ih + ia)
        if any(tag in blob for tag in ("u19", "u20", "u21", "u23")) or "youth" in blob:
            youth = youth or (cand, sw)
        elif sw:
            swapped = swapped or (cand, sw)
        else:
            direct = direct or (cand, sw)
        if direct:
            break
    return direct or swapped or youth or (None, False)


def _find_fixture(football, bet, ttl, budget):
    """Locate the finished fixture on API-Football via its UTC day.

    Returns (fixture_basic, swapped, meta). `fixture_basic` is the light object
    (no events); meta carries the reason when it cannot be found.
    """
    dt = _parse_dt(bet.get("commence_time"))
    if dt is None:
        return None, False, {"reason": "no_date"}
    base = dt.astimezone(timezone.utc)
    for delta in (0, -1, 1):
        if int(budget.get("calls", 0)) >= REPORT_BUDGET_PER_DAY:
            return None, False, {"reason": "budget"}
        day = (base + timedelta(days=delta)).date().isoformat()
        try:
            fixtures, _remaining, errors = football.fixtures(date=day)
        except Exception as exc:  # network / rate-limit / bad plan
            return None, False, {"reason": "error", "error": str(exc)}
        _spend(ttl, budget)
        if errors:
            # e.g. free plan refusing a competition - do not cache, just report
            return None, False, {"reason": "api", "error": str(errors)[:200]}
        fx, swapped = _match_bet_to_fixture(bet, fixtures or [])
        if fx:
            return fx, swapped, {"day": day}
    return None, False, {"reason": "not_found"}


_DETAIL_CACHE_TTL = 5 * 365 * 86400


def _match_key(bet):
    dt = _parse_dt(bet.get("commence_time"))
    day = dt.astimezone(timezone.utc).date().isoformat() if dt else "?"
    return "|".join([day, norm(bet.get("home_team")), norm(bet.get("away_team"))])


def load_match_detail(football, bet, ttl):
    """Return (match_dict_or_None, meta). The heavy part is cached permanently."""
    key = "match|" + _match_key(bet)
    cached = MATCH_STORE.get(key, _DETAIL_CACHE_TTL)
    if cached is not None:
        return (cached or None), {"cached": True, **(cached.get("meta", {}) if cached else {})}
    if not football or not getattr(football, "api_key", ""):
        return None, {"reason": "no_key"}

    budget = _budget(ttl)
    fx, swapped, meta = _find_fixture(football, bet, ttl, budget)
    if not fx:
        # cache a genuine "not in this plan" miss, but never a transient error/budget stop
        if meta.get("reason") in ("not_found", "api"):
            MATCH_STORE.set(key, {"found": False, "meta": meta})
        return None, meta

    fid = (fx.get("fixture") or {}).get("id")
    detail = fx
    if fid and int(budget.get("calls", 0)) < REPORT_BUDGET_PER_DAY:
        try:
            rows, _r, errors = football.fixtures(fixture_id=fid)
        except Exception as exc:
            rows, errors = None, str(exc)
        _spend(ttl, budget)
        if rows and not errors:
            detail = rows[0]
    match = _detail_to_match(detail, swapped)
    match["found"] = True
    match["meta"] = {"source": "api-football", "fixture_id": fid, "swapped": swapped, **meta}
    MATCH_STORE.set(key, match)
    return match, {"source": "api-football", "fixture_id": fid, "swapped": swapped, **meta}


def _detail_to_match(fx, swapped):
    fix = fx.get("fixture") or {}
    status = fix.get("status") or {}
    goals = fx.get("goals") or {}
    score = fx.get("score") or {}
    halftime = score.get("halftime") or {}
    teams = fx.get("teams") or {}
    league = fx.get("league") or {}

    gh, ga = goals.get("home"), goals.get("away")
    hth, hta = halftime.get("home"), halftime.get("away")
    if swapped:
        gh, ga = ga, gh
        hth, hta = hta, hth

    home_name = ((teams.get("home") or {}).get("name")) or ""
    away_name = ((teams.get("away") or {}).get("name")) or ""

    events, goals_list, cards_list = [], [], []
    for ev in fx.get("events") or []:
        t = ev.get("time") or {}
        team_name = (ev.get("team") or {}).get("name") or ""
        side = "home" if norm(team_name) == norm(home_name) else ("away" if norm(team_name) == norm(away_name) else "")
        rec = {
            "minute": t.get("elapsed"),
            "extra": t.get("extra"),
            "side": side,
            "team": team_name,
            "player": (ev.get("player") or {}).get("name") or "",
            "assist": (ev.get("assist") or {}).get("name") or "",
            "type": (ev.get("type") or "").lower(),
            "detail": ev.get("detail") or "",
        }
        if swapped:
            rec["side"] = {"home": "away", "away": "home"}.get(rec["side"], rec["side"])
        events.append(rec)
        if rec["type"] == "goal":
            goals_list.append(rec)
        elif rec["type"] == "card":
            cards_list.append(rec)

    stats = []
    stat_index = {}
    for block in fx.get("statistics") or []:
        team_name = ((block.get("team") or {}).get("name")) or ""
        side = "home" if norm(team_name) == norm(home_name) else ("away" if norm(team_name) == norm(away_name) else "")
        if swapped:
            side = {"home": "away", "away": "home"}.get(side, side)
        for item in block.get("statistics") or []:
            typ = item.get("type")
            if typ not in STAT_ORDER:
                continue
            row = stat_index.get(typ) or {"type": typ, "home": None, "away": None}
            row[side or "home"] = item.get("value")
            stat_index[typ] = row
    for typ in STAT_ORDER:
        if typ in stat_index:
            stats.append(stat_index[typ])

    # approximate end time: second-half kickoff if we have it, else 1h45 + stoppage
    kickoff = _parse_dt(fix.get("date"))
    extra = status.get("extra")
    extra_min = int(extra) if isinstance(extra, (int, float)) else 0
    second = (fix.get("periods") or {}).get("second")
    ended = None
    if second:
        ended = datetime.fromtimestamp(second, tz=timezone.utc) + timedelta(minutes=45 + extra_min)
    elif kickoff:
        ended = kickoff + timedelta(minutes=105 + extra_min)

    return {
        "kickoff": fix.get("date"),
        "ended": ended.isoformat() if ended else None,
        "status": status.get("short") or "",
        "status_long": status.get("long") or "",
        "minute": status.get("elapsed"),
        "extra": extra if isinstance(extra, (int, float)) else extra_min or None,
        "score": {"home": gh, "away": ga, "ht_home": hth, "ht_away": hta},
        "teams": {"home": home_name, "away": away_name},
        "league": league.get("name") or "",
        "round": league.get("round") or "",
        "venue": (fix.get("venue") or {}).get("name") or fix.get("referee") or "",
        "referee": fix.get("referee") or "",
        "goals": goals_list,
        "cards": cards_list,
        "events": events,
        "stats": stats,
    }


# ------------------------------------------------------------------ analysis
def _stat_pair(stats, name):
    for row in stats or []:
        if row.get("type") == name:
            return _stat_num(row.get("home")), _stat_num(row.get("away"))
    return None, None


def build_analysis(bet, match):
    """Deterministic, honest read of the bet: numbers only, no AI.

    Returns codes the front-end turns into text (`verdict`, `flags`) plus the
    raw metrics that back them up, so nothing is asserted without a number.
    """
    side = (bet.get("side") or "").strip()
    if match and match.get("meta", {}).get("swapped"):
        side = {"home": "away", "away": "home"}.get(side, side)
    idx = 0 if side == "home" else (1 if side == "away" else None)

    odds = _f(bet.get("odds"))
    implied = round(100.0 / odds, 1) if odds and odds > 1 else None
    model = _f(bet.get("model_prob"))
    sharp = _f(bet.get("sharp_prob"))
    if sharp is None:
        sharp = _f(bet.get("closing_prob"))
    edge = _f(bet.get("edge_pct"))
    clv = _f(bet.get("clv_pct"))
    won = bet.get("status") == "won"

    metrics = {
        "model_prob": round(model * 100, 1) if model is not None else None,
        "market_prob": round(sharp * 100, 1) if sharp is not None else None,
        "implied_prob": implied,
        "edge_pct": edge,
        "clv_pct": clv,
        "odds": odds,
        "sharp_odds": _f(bet.get("sharp_odds")),
    }

    stats = (match or {}).get("stats") or []
    sot = _stat_pair(stats, "Shots on Goal")
    shots = _stat_pair(stats, "Total Shots")
    poss = _stat_pair(stats, "Ball Possession")
    bet_sot = sot[idx] if idx is not None else None
    opp_sot = sot[1 - idx] if idx is not None else None
    bet_shots = shots[idx] if idx is not None else None
    opp_shots = shots[1 - idx] if idx is not None else None
    bet_poss = poss[idx] if idx is not None else None
    opp_poss = poss[1 - idx] if idx is not None else None

    dominated = bool(
        bet_sot is not None and opp_sot is not None
        and bet_sot > opp_sot + 1 and (bet_shots or 0) >= (opp_shots or 0)
    )
    outplayed = bool(
        bet_sot is not None and opp_sot is not None and opp_sot >= bet_sot + 2
    )

    margin = None
    score = (match or {}).get("score") or {}
    if score.get("home") is not None and score.get("away") is not None:
        margin = abs(int(score["home"]) - int(score["away"]))

    flags = []
    if edge is not None and edge < 3.0:
        flags.append("low_edge")
    if clv is not None and clv < 0:
        flags.append("negative_clv")
    if sharp is not None and implied is not None and implied < sharp * 100 - 5:
        flags.append("against_sharp")
    if model is not None and sharp is not None and model > sharp + 0.12:
        flags.append("model_vs_market")
    if bet_sot is not None and bet_sot <= 2 and not won:
        flags.append("few_chances")
    if (match or {}).get("cards") and len(match["cards"]) >= 5:
        flags.append("many_cards")

    if won:
        verdict = "won_lucky" if outplayed else "won"
    elif dominated:
        verdict = "lost_bad_beat"
    elif outplayed:
        verdict = "lost_outplayed"
    elif margin is not None and margin <= 1:
        verdict = "lost_narrow"
    elif sharp is not None and sharp >= 0.5:
        verdict = "lost_upset"
    else:
        verdict = "lost"

    # a compact, honest extra reading (still a code - the UI localizes it)
    readings = []
    if dominated:
        readings.append("dominated_but_lost")
    if outplayed:
        readings.append("outplayed")
    if margin == 0 and not won:
        readings.append("draw_killed")
    if clv is not None and clv > 0:
        readings.append("beat_closing")
    elif clv is not None and clv < 0:
        readings.append("worse_than_closing")

    return {
        "verdict": verdict,
        "flags": flags,
        "readings": readings,
        "metrics": metrics,
        "stats_side": {
            "shots_on_goal": bet_sot, "shots_on_goal_opp": opp_sot,
            "shots": bet_shots, "shots_opp": opp_shots,
            "possession": bet_poss, "possession_opp": opp_poss,
        },
    }


# ------------------------------------------------------------------ entry
def build_report(storage, football, ttl, bet):
    """Assemble the full report payload for one bet (safe to call for any status)."""
    match, meta = (None, {"reason": "not_football"})
    if is_football(bet):
        match, meta = load_match_detail(football, bet, ttl)

    if not match:
        # degrade: use the score we stored at settlement, no pitch detail
        match_public = {
            "found": False,
            "score": _score_from_text(bet.get("result_score")),
            "teams": {"home": bet.get("home_team") or "", "away": bet.get("away_team") or ""},
            "kickoff": bet.get("commence_time"),
            "source": "stored",
        }
    else:
        match_public = dict(match)
        match_public["source"] = match.get("meta", {}).get("source", "api-football")
        match_public.pop("meta", None)

    analysis = build_analysis(bet, match)

    return {
        "ok": True,
        "bet": {
            "id": bet.get("id"),
            "event": bet.get("event"),
            "outcome": bet.get("outcome"),
            "side": bet.get("side"),
            "odds": bet.get("odds"),
            "stake": bet.get("stake"),
            "status": bet.get("status"),
            "won": bet.get("status") == "won",
            "profit": bet.get("profit"),
            "bookmaker": bet.get("bookmaker"),
            "sport": bet.get("sport") or bet.get("sport_group"),
            "commence_time": bet.get("commence_time"),
            "settled_at": bet.get("settled_at"),
        },
        "match": match_public,
        "analysis": analysis,
        "meta": meta,
    }


def _score_from_text(text):
    if not text or "-" not in str(text):
        return {"home": None, "away": None}
    try:
        h, a = str(text).split("-", 1)
        return {"home": int(h.strip()), "away": int(a.strip())}
    except ValueError:
        return {"home": None, "away": None}
