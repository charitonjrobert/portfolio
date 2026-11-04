# -*- coding: utf-8 -*-
"""MicrobistBets API layer (added 13 Oct 2026).

Friendly public endpoints on top of the existing engine:
  GET  /api/config      -> UI bootstrap (brand, languages, competitions)
  GET  /api/limits      -> quota status for every provider + friendly message/countdown
  GET  /api/fixtures    -> match picker data (upcoming, with/without odds)
  POST /api/analyze     -> probabilities + odds + news context + reasons (0 paid calls when cached)
  GET  /api/recommend   -> "Recommend me a match" (weighted random pick, 0 API calls)

None of these endpoints consume paid quota unless explicitly asked (`?live=1`).
"""
import difflib
import json
import random
import re
import threading
import time
import unicodedata
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Optional

from fastapi import APIRouter
from pydantic import BaseModel

from context import extract_players, summarize_impact
from models import predict_1x2
from settle import fetch_finished_football, fetch_oddsapi_scores
from ttl_cache import TtlCache
from value import find_value_bets
import sharp

LANGS = ("ro", "de", "en")

# --------------------------------------------------------------------------- i18n
MSG = {
    "ok": {
        "ro": "Totul e în regulă. Ai {n} cereri rămase.",
        "de": "Alles in Ordnung. Dir bleiben {n} Anfragen.",
        "en": "All good. You have {n} requests left.",
    },
    "warn": {
        "ro": "Te apropii de limită: mai ai {n} cereri. Se reînnoiește {reset}.",
        "de": "Du näherst dich dem Limit: noch {n} Anfragen. Erneuert {reset}.",
        "en": "Getting close to the limit: {n} requests left. Resets {reset}.",
    },
    "stop": {
        "ro": "Limita e atinsă. Se reînnoiește {reset}. Până atunci folosesc datele deja salvate.",
        "de": "Limit erreicht. Erneuert sich {reset}. Bis dahin nutze ich die gespeicherten Daten.",
        "en": "Limit reached. Resets {reset}. Until then I use the data already saved.",
    },
    "unlimited": {
        "ro": "Fără limită zilnică (doar un ritm de {n} cereri/minut).",
        "de": "Kein Tageslimit (nur {n} Anfragen/Minute).",
        "en": "No daily limit (just a pace of {n} requests/minute).",
    },
    "not_configured": {
        "ro": "Neactivat (lipsește cheia). Poți activa gratuit, în 2 minute.",
        "de": "Nicht aktiviert (Schlüssel fehlt). In 2 Minuten kostenlos aktivierbar.",
        "en": "Not enabled (missing key). You can enable it free in 2 minutes.",
    },
    "in_hours": {
        "ro": "în {h}h {m}m",
        "de": "in {h}h {m}m",
        "en": "in {h}h {m}m",
    },
}

LEVELS = (("green", 0.5), ("yellow", 0.2))

# Shared assistant cooldown state (module level so other modules can report rate limits).
AI_STATE = {"last_error": None, "cooldown_until": 0.0, "last_ok": None}


def note_ai_error(cooldown_s=900):
    """Report an assistant rate-limit so the UI can show a friendly countdown."""
    AI_STATE["cooldown_until"] = time.time() + max(60, int(cooldown_s))
    AI_STATE["last_error"] = datetime.now().isoformat(timespec="seconds")
    return AI_STATE["cooldown_until"]


def note_ai_ok():
    AI_STATE["cooldown_until"] = 0.0
    AI_STATE["last_ok"] = datetime.now().isoformat(timespec="seconds")


def t(key, lang, **kw):
    lang = lang if lang in LANGS else "ro"
    text = MSG.get(key, {}).get(lang) or MSG.get(key, {}).get("ro", key)
    try:
        return text.format(**kw)
    except Exception:
        return text


def _fmt_left(seconds, lang="ro"):
    if seconds is None:
        return "—"
    seconds = max(0, int(seconds))
    d, rem = divmod(seconds, 86400)
    h, rem = divmod(rem, 3600)
    m = rem // 60
    if d:
        return f"{d}z {h}h" if lang == "ro" else f"{d}d {h}h"
    if h:
        return f"{h}h {m}m"
    return f"{m}min"


def _level(remaining, limit):
    if not limit or remaining is None:
        return "unknown"
    if remaining <= 0:
        return "red"
    pct = remaining / float(limit)
    for name, threshold in LEVELS:
        if pct >= threshold:
            return name
    return "red"


def _parse_iso(value):
    if not value:
        return None
    try:
        return datetime.fromisoformat(str(value).replace("Z", "+00:00"))
    except Exception:
        return None


def _now():
    return datetime.now(timezone.utc)


def _next_month_reset():
    now = _now()
    year, month = (now.year + 1, 1) if now.month == 12 else (now.year, now.month + 1)
    return datetime(year, month, 1, tzinfo=timezone.utc)


def _next_utc_midnight():
    now = _now()
    return datetime(now.year, now.month, now.day, tzinfo=timezone.utc) + timedelta(days=1)


_DIACRITICS = str.maketrans({
    "ø": "o", "æ": "ae", "ß": "ss", "đ": "d", "ð": "d", "þ": "th", "ł": "l",
    "ı": "i", "ĳ": "ij", "œ": "oe", "š": "s", "ž": "z", "č": "c", "ć": "c",
})


def _norm(text):
    """Lowercase, strip accents and punctuation: 'München' -> 'munchen', 'Bodø/Glimt' -> 'bodoglimt'."""
    text = (text or "").translate(_DIACRITICS)
    text = unicodedata.normalize("NFKD", text)
    text = "".join(ch for ch in text if not unicodedata.combining(ch))
    return "".join(ch for ch in text.lower() if ch.isalnum())


# common nicknames so people do not have to type the official name
_ALIASES = {
    "barca": "barcelona", "psg": "paris", "juve": "juventus", "atleti": "atletico",
    "bvb": "dortmund", "utd": "united", "spurs": "tottenham", "inter": "inter",
    "bayern": "bayern", "real": "real", "sporting": "sporting", "glimt": "glimt",
    # club-name variants that the odds feed and football-data spell differently
    "internazionale": "inter", "munchen": "munich", "wolves": "wolverhampton",
    "moenchengladbach": "monchengladbach",
}

# Words that are club designators, not part of the team identity ("FC Internazionale" -> ["inter"]).
_TEAM_STOP = {
    "fc", "cf", "sc", "ac", "ssc", "afc", "cd", "ud", "rc", "ca", "ec", "af",
    "bk", "if", "ff", "fk", "sk", "nk", "club", "calcio", "the", "de", "del", "pae",
    "sv", "tsg", "vfl", "vfb", "vfr", "fsv", "osc", "cfc", "acf", "rcd", "sbv",
    "aj", "as", "us", "ss", "sm", "balompie", "futbol", "olympique", "racing",
}


def _query_tokens(q):
    """Split a user query into normalised word tokens ('FC Bayern' -> ['fc', 'bayern'])."""
    out = []
    for raw in re.split(r"[\s\-–—/.,'()]+", (q or "").strip()):
        norm = _norm(raw)
        if norm:
            out.append(_ALIASES.get(norm, norm))
    return out


def _fuzzy_score(item, tokens, needle_norm):
    """How well a fixture matches a (possibly misspelled) query. 0 = no match.

    Rules (in order):
      1. the whole query appears in the names          -> 1.00
      2. every word of the query appears inside a name -> 0.90  ("gladbach" in "monchengladbach")
      3. typo tolerance per word (similar spelling AND similar length, >= 5 chars) -> 0.85
    ALL words must match, otherwise the item is rejected - this is what stops
    "real madrid" from also returning "Atletico Madrid".
    """
    hay = _norm(item.get("home")) + _norm(item.get("away")) + _norm(item.get("league"))
    if needle_norm and needle_norm in hay:
        return 1.0
    words = [t for t in tokens if len(t) >= 3] or tokens
    if not words:
        return 0.0
    hay_tokens = [_norm(t) for t in (
        (item.get("home") or "").split() + (item.get("away") or "").split() + (item.get("league") or "").split()
    )]
    hay_tokens = [t for t in hay_tokens if t]
    scores = []
    for tok in words:
        best = 0.0
        for ht in hay_tokens:
            if len(ht) >= 3 and (tok in ht or ht in tok):
                best = max(best, 0.90)
                continue
            if len(tok) < 5 or len(ht) < 5:
                continue
            if abs(len(tok) - len(ht)) > max(1, len(tok) * 0.34):
                continue
            ratio = difflib.SequenceMatcher(None, tok, ht).ratio()
            if ratio >= 0.80:
                best = max(best, 0.85)
        if best == 0.0:
            return 0.0
        scores.append(best)
    return min(scores)


def _team_tokens(name):
    """Significant words of a club name, without designators like FC/CF/SC or years."""
    return [
        t for t in _query_tokens(name)
        if len(t) >= 3 and t not in _TEAM_STOP and not t.isdigit()
    ]


def _token_match(a, b):
    """Token equality plus safe prefix/typo tolerance ('inter' ~ 'internazionale')."""
    if a == b:
        return True
    if len(a) >= 3 and len(b) >= 3 and (a in b or b in a):
        return True
    if len(a) >= 5 and len(b) >= 5:
        if abs(len(a) - len(b)) <= max(1, max(len(a), len(b)) * 0.34):
            return difflib.SequenceMatcher(None, a, b).ratio() >= 0.80
    return False


def _team_sim(a, b):
    """0..1 similarity between two club names (tokens, aliases, one typo)."""
    ta, tb = _team_tokens(a), _team_tokens(b)
    if not ta or not tb:
        return 0.0
    big, small = (ta, tb) if len(ta) >= len(tb) else (tb, ta)
    used = set()
    matches = 0
    for token in big:
        for idx, other in enumerate(small):
            if idx in used:
                continue
            if _token_match(token, other):
                used.add(idx)
                matches += 1
                break
    return matches / max(len(ta), len(tb))


def _pair_sim(home_a, away_a, home_b, away_b):
    """Similarity of a fixture pair, allowing a swapped home/away orientation."""
    direct = min(_team_sim(home_a, home_b), _team_sim(away_a, away_b))
    swapped = min(_team_sim(home_a, away_b), _team_sim(away_a, home_b))
    return max(direct, swapped)


def _hours_apart(a, b):
    """Absolute difference in hours between two ISO timestamps, or None if missing."""
    da, db = _parse_iso(a), _parse_iso(b)
    if not da or not db:
        return None
    return abs((da - db).total_seconds()) / 3600.0


def _dedupe_fixtures(items):
    """Merge the same fixture coming from odds + football-data, preferring the odds copy."""
    merged = []
    for item in items:
        if not isinstance(item, dict):
            continue
        hit = None
        for idx, prev in enumerate(merged):
            if item.get("sport") != prev.get("sport"):
                continue
            gap = _hours_apart(item.get("commence_time"), prev.get("commence_time"))
            if gap is None or gap > 3.0:
                continue
            if _pair_sim(item.get("home"), item.get("away"),
                         prev.get("home"), prev.get("away")) >= 0.65:
                hit = idx
                break
        if hit is None:
            merged.append(dict(item))
            continue
        prev = merged[hit]
        keep = item if (item.get("has_odds") and not prev.get("has_odds")) else prev
        other = prev if keep is item else item
        keep = dict(keep)
        sources = set()
        for src in (keep.get("sources") or [keep.get("source")],
                    other.get("sources") or [other.get("source")]):
            sources.update(s for s in src if s)
        keep["sources"] = sorted(sources)
        merged[hit] = keep
    return merged


def _odds_state(event):
    """Why a 1X2 probability may be missing for an event."""
    books = event.get("bookmakers") or []
    if not books:
        return "no_odds"
    has_h2h = any(
        isinstance(m, dict) and m.get("key") == "h2h"
        for b in books if isinstance(b, dict)
        for m in (b.get("markets") or [])
    )
    if not has_h2h:
        return "no_h2h_market"
    return "insufficient_market"


def _filter_items(items, q, limit):
    """Search inside an already loaded list (fast, in memory): exact, prefix and fuzzy matching."""
    tokens = _query_tokens(q)
    needle = _norm(q)
    if not tokens and not needle:
        return items[:limit]
    scored = []
    for it in items:
        score = _fuzzy_score(it, tokens, needle)
        if score > 0:
            scored.append((score, it))
    scored.sort(key=lambda pair: (-pair[0], pair[1].get("commence_time") or ""))
    return [it for _, it in scored[:limit]]


# ------------------------------------------------------------------ match status
# Expected running time per sport (minutes, generous) so the list can tell "live"
# from "finished" even when the source does not hand us an explicit final score.
GROUP_DURATION_MIN = {
    "soccer": 115, "basketball": 160, "icehockey": 160,
    "tennis": 240, "mma": 190, "boxing": 190, "americanfootball": 210,
    "baseball": 200, "handball": 130,
}
DEFAULT_DURATION_MIN = 160

# sport group -> the-odds-api key (mirrors settle.py, used when an item has no sport_key)
GROUP_TO_KEY = {
    "basketball": "basketball_nba",
    "icehockey": "icehockey_nhl",
    "americanfootball": "americanfootball_nfl",
    "mma": "mma_mixed_martial_arts",
    "boxing": "boxing_boxing",
}


def _add_result(results, home, away, hs, a_s, date, source):
    if hs is None or a_s is None:
        return
    nh, na = _norm(home), _norm(away)
    if not nh or not na:
        return
    results.append({
        "nh": nh, "na": na,
        "home_score": hs, "away_score": a_s,
        "date": (date or "")[:10], "source": source,
    })


def _find_result(item, results):
    """Match a fixtures item to a known result (both team names + date within +-1 day)."""
    nh, na = _norm(item.get("home")), _norm(item.get("away"))
    if not nh or not na:
        return None
    ct = _parse_iso(item.get("commence_time"))
    cdate = ct.date() if ct else None
    for r in results:
        if not r["nh"] or not r["na"]:
            continue
        if not ((nh in r["nh"] or r["nh"] in nh) and (na in r["na"] or r["na"] in na)):
            continue
        if cdate and r["date"]:
            try:
                rd = datetime.fromisoformat(r["date"]).date()
            except Exception:
                rd = None
            if rd and abs((rd - cdate).days) > 1:
                continue
        return r
    return None


def _annotate_results(items, *, fd, odds_api_key, ttl, config, lang, notes):
    """Add `status` ('upcoming'|'live'|'finished') and the final score to each item.

    Cost rules (the-odds-api is limited to 500/month, shared with the odds refresh):
      * football          -> football-data.org FINISHED (free), cached 10 minutes;
      * every other sport -> reuse the shared `scores|<sport_key>` cache written by
        the wallet; a fresh odds-api call happens only when a candidate match is
        already past its expected duration and the daily budget still has room.
    """
    now = _now()
    rcfg = (config.get("results", {}) or {})
    scores_ttl = int(float(rcfg.get("scores_ttl_min", 360)) * 60)
    daily_cap = int(rcfg.get("max_scores_per_day", 12))
    auto_scores = bool(rcfg.get("auto_scores", True))
    lang = lang if lang in LANGS else "ro"
    results = []

    # 1) football — free source
    if fd is not None and getattr(fd, "configured", False):
        fin = ttl.get("results|fd_finished", 600) if ttl else None
        if fin is None:
            try:
                fin, _meta = fetch_finished_football(fd, days=2)
            except Exception:
                fin = []
            if ttl:
                ttl.set("results|fd_finished", fin or [])
        for m in (fin or []):
            _add_result(results, m.get("home"), m.get("away"),
                        m.get("home_score"), m.get("away_score"),
                        m.get("utcDate"), "football-data")

    # 2) other sports — reuse the shared scores cache; only a cache miss may cost 1 request
    if auto_scores:
        keys = []
        for it in items:
            if (it.get("sport") or "") == "soccer":
                continue
            key = (it.get("sport_key") or GROUP_TO_KEY.get(it.get("sport") or "", "") or "").strip()
            ct = _parse_iso(it.get("commence_time"))
            if not key or not ct:
                continue
            dur = GROUP_DURATION_MIN.get(it.get("sport"), DEFAULT_DURATION_MIN)
            if ct > now - timedelta(minutes=dur):  # not finished yet -> no score needed
                continue
            keys.append(key)
        day = now.date().isoformat()
        budget = ttl.get("results|budget", 86400) if ttl else None
        if not isinstance(budget, dict) or budget.get("day") != day:
            budget = {"day": day, "n": 0}
        used = 0
        for key in dict.fromkeys(keys):  # unique, keep order
            data = ttl.get(f"scores|{key}", scores_ttl) if ttl else None
            if data is None and odds_api_key and budget["n"] < daily_cap:
                try:
                    data, _meta = fetch_oddsapi_scores(key, odds_api_key)
                except Exception:
                    data = {}
                budget["n"] += 1
                used += 1
                if ttl:
                    ttl.set(f"scores|{key}", data or {})
            for ev in (data or {}).values():
                if isinstance(ev, dict) and ev.get("completed"):
                    _add_result(results, ev.get("home"), ev.get("away"),
                                ev.get("home_score"), ev.get("away_score"),
                                ev.get("commence_time"), "odds-api")
        if ttl and used:
            ttl.set("results|budget", budget)
        if used:
            notes.append({
                "ro": f"Am verificat {used} surse de rezultate pentru sporturile non-fotbal (buget {budget['n']}/{daily_cap} azi).",
                "de": f"{used} Ergebnis-Quellen für Nicht-Fußball geprüft (Budget {budget['n']}/{daily_cap} heute).",
                "en": f"Checked {used} result sources for non-football sports (budget {budget['n']}/{daily_cap} today).",
            }[lang])

    # 3) annotate every item, then order: live first, then upcoming, finished last
    for it in items:
        ct = _parse_iso(it.get("commence_time"))
        res = _find_result(it, results) if (ct and ct <= now) else None
        if res:
            it["status"] = "finished"
            it["home_score"] = res["home_score"]
            it["away_score"] = res["away_score"]
            it["result_source"] = res["source"]
            continue
        dur = GROUP_DURATION_MIN.get(it.get("sport"), DEFAULT_DURATION_MIN)
        if ct and ct <= now:
            it["status"] = "finished" if now >= ct + timedelta(minutes=dur) else "live"
        else:
            it["status"] = "upcoming"

    live = [it for it in items if it.get("status") == "live"]
    up = [it for it in items if it.get("status") == "upcoming"]
    fin = [it for it in items if it.get("status") == "finished"]
    live.sort(key=lambda x: x.get("commence_time") or "")
    up.sort(key=lambda x: x.get("commence_time") or "")
    fin.sort(key=lambda x: x.get("commence_time") or "", reverse=True)
    return live + up + fin


def build_router(
    *,
    storage,
    context_engine,
    football,
    fd,
    history_analyzer,
    config,
    refresh_state,
    value_state,
    threshold=4.0,
    borderline_window_pct=3.0,
    monthly_limit=500,
    backend_dir=None,
    scan_value_bets=None,
    ttl=None,
    odds_api_key="",
):
    router = APIRouter()
    state_file = Path(backend_dir or ".") / "limits_state.json"
    limits_cache = {"ts": 0.0, "providers": {}}
    lock = threading.Lock()

    cache_cfg = (config.get("cache", {}) or {})
    fixtures_ttl = int(float(cache_cfg.get("fixtures_ttl_min", 30)) * 60)
    analyze_ttl = int(float(cache_cfg.get("analyze_ttl_min", 30)) * 60)
    ttl = ttl if ttl is not None else TtlCache(Path(backend_dir or ".") / "cache_ttl.json", retention_seconds=86400)

    def _out(key, payload):
        """Store a payload in the server cache and mark it as fresh in the response."""
        try:
            ttl.set(key, payload)
        except Exception:
            pass
        payload = dict(payload)
        payload["cached"] = False
        payload["cached_age_s"] = 0
        return payload

    def _load_state():
        try:
            data = json.loads(Path(state_file).read_text(encoding="utf-8"))
        except Exception:
            return
        if isinstance(data, dict):
            limits_cache.update({k: v for k, v in data.items() if k in ("ts", "providers")})
            AI_STATE.update(data.get("ai_state") or {})

    def _save_state():
        try:
            Path(state_file).write_text(
                json.dumps(
                    {"ts": limits_cache["ts"], "providers": limits_cache["providers"], "ai_state": AI_STATE},
                    ensure_ascii=False,
                    indent=2,
                ),
                encoding="utf-8",
            )
        except Exception:
            pass

    _load_state()

    # ------------------------------------------------------------------ limits
    def _odds_provider(lang):
        remaining = refresh_state.get("remaining")
        resets_at = _next_month_reset()
        left = (resets_at - _now()).total_seconds()
        if remaining is None:
            level, message = "unknown", MSG["ok"]["en"]
            message = {
                "ro": "Nu am încă un status proaspăt al cotelor (se citește la următoarea reîmprospătare).",
                "de": "Noch kein frischer Status der Quoten (wird beim nächsten Aktualisieren gelesen).",
                "en": "No fresh odds status yet (read on the next refresh).",
            }[lang]
        else:
            level = _level(remaining, monthly_limit)
            if level == "green":
                message = t("ok", lang, n=remaining)
            elif level == "yellow":
                message = t("warn", lang, n=remaining, reset=_fmt_left(left, lang))
            else:
                message = t("stop", lang, reset=_fmt_left(left, lang))
        return {
            "id": "the_odds_api",
            "label": {"ro": "Cote live (the-odds-api)", "de": "Live-Quoten (the-odds-api)", "en": "Live odds (the-odds-api)"}[lang],
            "kind": "monthly",
            "used": (monthly_limit - remaining) if remaining is not None else None,
            "limit": monthly_limit,
            "remaining": remaining,
            "level": level,
            "resets_at": resets_at.isoformat(),
            "resets_in_s": int(left),
            "resets_in_human": _fmt_left(left, lang),
            "message": message,
        }

    def _api_football_provider(lang, live=False):
        remaining, limit = None, 100
        configured = bool(getattr(football, "api_key", ""))
        if configured:
            if live:
                try:
                    remaining = football.remaining_requests()
                except Exception:
                    remaining = None
            if remaining is None:
                remaining = limits_cache["providers"].get("api_football", {}).get("remaining")
        resets_at = _next_utc_midnight()
        left = (resets_at - _now()).total_seconds()
        if not configured:
            level, message = "unknown", t("not_configured", lang)
        elif remaining is None:
            level, message = "unknown", {
                "ro": "Status necitit (îl citesc doar când ceri tu, ca să nu consum).",
                "de": "Status nicht gelesen (lese ich nur auf Anfrage, um nichts zu verbrauchen).",
                "en": "Status not read (read only on demand, to avoid consuming).",
            }[lang]
        else:
            level = _level(remaining, limit)
            message = t("ok", lang, n=remaining) if level == "green" else (
                t("warn", lang, n=remaining, reset=_fmt_left(left, lang)) if level == "yellow"
                else t("stop", lang, reset=_fmt_left(left, lang))
            )
        return {
            "id": "api_football",
            "label": {"ro": "Detalii meciuri (API-Football)", "de": "Spieldetails (API-Football)", "en": "Match details (API-Football)"}[lang],
            "kind": "daily",
            "used": (limit - remaining) if remaining is not None else None,
            "limit": limit,
            "remaining": remaining,
            "level": level,
            "resets_at": resets_at.isoformat(),
            "resets_in_s": int(left),
            "resets_in_human": _fmt_left(left, lang),
            "message": message,
        }

    def _fd_provider(lang):
        info = fd.limit_info()
        if not info.get("configured"):
            return {
                "id": "football_data",
                "label": {"ro": "Meciuri viitoare (football-data.org)", "de": "Kommende Spiele (football-data.org)", "en": "Upcoming matches (football-data.org)"}[lang],
                "kind": "minute",
                "used": info.get("used_this_minute"),
                "limit": info.get("limit_per_minute"),
                "remaining": None,
                "level": "unknown" if not info.get("configured") else "green",
                "message": t("not_configured", lang),
                "register_url": info.get("register_url"),
                "resets_in_s": 60 - int(time.time()) % 60,
                "resets_in_human": "1min",
                "resets_at": None,
            }
        return {
            "id": "football_data",
            "label": {"ro": "Meciuri viitoare (football-data.org)", "de": "Kommende Spiele (football-data.org)", "en": "Upcoming matches (football-data.org)"}[lang],
            "kind": "minute",
            "used": info.get("used_this_minute"),
            "limit": info.get("limit_per_minute"),
            "remaining": info.get("available_minute"),
            "level": "green",
            "message": t("unlimited", lang, n=info.get("limit_per_minute") or 10),
            "resets_at": None,
            "resets_in_s": 60 - int(time.time()) % 60,
            "resets_in_human": "1min",
        }

    def _ai_provider(lang):
        chat_cfg = config.get("chat", {}) or {}
        configured = bool(chat_cfg.get("api_key")) and chat_cfg.get("enabled", True)
        cooldown = AI_STATE.get("cooldown_until", 0)
        left = max(0, cooldown - time.time())
        if not configured:
            level, message = "unknown", {
                "ro": "Nu e activat.", "de": "Nicht aktiviert.", "en": "Not enabled."
            }[lang]
        elif left > 0:
            level = "yellow"
            message = {
                "ro": f"Asistentul e în pauză ({_fmt_left(left, lang)}) — revin automat.",
                "de": f"Der Assistent pausiert ({_fmt_left(left, lang)}) — kommt automatisch zurück.",
                "en": f"Assistant is cooling down ({_fmt_left(left, lang)}) — back automatically.",
            }[lang]
        else:
            level, message = "green", {
                "ro": "Asistentul (Miki) e disponibil. Are un ritm generos de cereri, nu o limită zilnică.",
                "de": "Assistent (Miki) ist verfügbar. Großzügiges Tempo, kein Tageslimit.",
                "en": "Assistant (Miki) is available. Generous pace, no daily limit.",
            }[lang]
        return {
            "id": "ai_chat",
            "label": {"ro": "Asistent (Miki)", "de": "Assistent (Miki)", "en": "Assistant (Miki)"}[lang],
            "kind": "pace",
            "used": None,
            "limit": None,
            "remaining": None,
            "level": level,
            "message": message,
            "resets_at": None,
            "resets_in_s": int(left),
            "resets_in_human": _fmt_left(left, lang) if left else "—",
        }

    @router.get("/api/config")
    def ui_config():
        ui = config.get("ui", {}) or {}
        return {
            "brand": ui.get("brand", "MicrobistBets"),
            "assistant": ui.get("assistant", "Miki"),
            "default_lang": ui.get("default_lang", "ro"),
            "languages": ui.get("languages", list(LANGS)),
            "recommend": config.get("recommend", {}),
            "sources": {
                "odds": bool(config.get("api_key")),
                "api_football": bool((config.get("api_football") or {}).get("api_key")),
                "football_data": fd.configured,
                "ai": bool((config.get("chat") or {}).get("api_key")),
            },
        }

    @router.get("/api/limits")
    def limits(lang: str = "ro", live: int = 0):
        providers = [
            _odds_provider(lang),
            _api_football_provider(lang, live=bool(live)),
            _fd_provider(lang),
            _ai_provider(lang),
        ]
        with lock:
            limits_cache["ts"] = time.time()
            limits_cache["providers"] = {p["id"]: p for p in providers}
            _save_state()
        worst = "green"
        for p in providers:
            if p["level"] == "unknown":
                continue
            if p["level"] == "red":
                worst = "red"
                break
            if p["level"] == "yellow":
                worst = "yellow"
        return {"generated_at": datetime.now().isoformat(timespec="seconds"), "overall": worst, "providers": providers}

    @router.post("/api/limits/ai-error")
    def ai_error(cooldown_s: int = 900):
        """Called by the chat layer when the model rate-limits, so the UI can show a friendly countdown."""
        note_ai_error(cooldown_s)
        _save_state()
        return {"ok": True, "cooldown_until": AI_STATE["cooldown_until"]}

    # ------------------------------------------------------------------ cache
    @router.get("/api/version")
    def version():
        """Asset fingerprint so an open app (or an installed PWA) reloads itself after a deploy."""
        newest = 0
        try:
            dash = Path(backend_dir or ".").resolve().parent / "dashboard"
            for name in ("app.js", "style.css", "index.html"):
                p = dash / name
                if p.exists():
                    newest = max(newest, int(p.stat().st_mtime))
        except OSError:
            pass
        return {"assets": newest}

    @router.get("/api/cache/status")
    def cache_status():
        odds = storage.load_cache()
        total = sum(len(v) for v in odds.values() if isinstance(v, list))
        now = _now()
        upcoming = 0
        for events in odds.values():
            if not isinstance(events, list):
                continue
            for ev in events:
                ct = _parse_iso((ev or {}).get("commence_time"))
                if ct and ct > now - timedelta(hours=3):
                    upcoming += 1
        return {
            "server": ttl.stats(),
            "ttl_seconds": {"fixtures": fixtures_ttl, "analyze": analyze_ttl},
            "odds_cache": {"events_total": total, "events_upcoming": upcoming},
        }

    @router.post("/api/cache/clear")
    def cache_clear(scope: str = "server", prefix: str = ""):
        cleared = 0
        if scope in ("server", "all"):
            before = ttl.stats()["entries"]
            ttl.clear(prefix or None)
            cleared += before
        pruned = 0
        if scope in ("odds", "all"):
            try:
                pruned = storage.prune_expired(int(cache_cfg.get("retention_hours", 48)))
            except Exception:
                pruned = 0
        return {"ok": True, "cleared_entries": cleared, "pruned_events": pruned}

    # ---------------------------------------------------------------- fixtures
    @router.get("/api/fixtures")
    def fixtures(days: str = "7", q: str = "", lang: str = "ro", limit: int = 200, sport: str = "", nocache: int = 0):
        # One cached BASE list per (days, lang, sport); the search/filter runs in memory afterwards.
        # Before this, every distinct query/limit was its own cache key -> the server rebuilt the whole
        # list (and called football-data.org) on almost every search, which felt like "nothing happens".
        cache_key = f"fixtures|v3|{days}|{lang}|{sport}|base"
        if not nocache:
            cached, age = ttl.get_entry(cache_key, fixtures_ttl)
            # a degraded payload (one source down) is only reused for a minute
            if cached is not None and cached.get("degraded") and age is not None and age > 60:
                cached = None
            if cached is not None:
                shown = _filter_items(cached.get("items") or [], q, max(1, int(limit)))
                return {
                    "count": len(shown),
                    "days": days,
                    "query": q,
                    "items": shown,
                    "with_odds": sum(1 for it in shown if it.get("has_odds")),
                    "notes": cached.get("notes") or [],
                    "degraded": cached.get("degraded"),
                    "generated_at": cached.get("generated_at"),
                    "cached": True,
                    "cached_age_s": age,
                }
        now = _now()
        try:
            horizon = {"0": 1, "1": 2, "7": 8, "all": 60}.get(str(days).lower())
        except Exception:
            horizon = 8
        if horizon is None:
            try:
                horizon = max(1, int(days)) + 1
            except Exception:
                horizon = 8
        end = now + timedelta(days=horizon)
        notes = []
        items = []

        # 1) matches WITH odds, from the local cache (0 API calls)
        from_cache = 0
        wanted_sports = {s.strip() for s in (sport or "").split(",") if s.strip()}
        for group, events in storage.load_cache().items():
            if not isinstance(events, list):
                continue
            if wanted_sports and group not in wanted_sports:
                continue
            for ev in events:
                if not isinstance(ev, dict):
                    continue
                ct = _parse_iso(ev.get("commence_time"))
                if not ct or ct < now - timedelta(hours=3) or ct > end:
                    continue
                odds = {}
                for book in ev.get("bookmakers", []) or []:
                    for market in book.get("markets", []) or []:
                        if market.get("key") != "h2h":
                            continue
                        for out in market.get("outcomes", []) or []:
                            name = out.get("name")
                            price = out.get("price")
                            if not name or not price or price < 1.02:
                                continue  # 1.00/1.01 are placeholder quotes, not real prices
                            key = "home" if name == ev.get("home_team") else ("away" if name == ev.get("away_team") else "draw")
                            if key not in odds or price > odds[key]:
                                odds[key] = price
                items.append({
                    "id": ev.get("id"),
                    "source": "odds",
                    "sport": group,
                    "sport_key": ev.get("sport_key"),
                    "league": ev.get("sport_title") or group,
                    "home": ev.get("home_team"),
                    "away": ev.get("away_team"),
                    "commence_time": ev.get("commence_time"),
                    "has_odds": bool(odds),
                    "odds": odds or None,
                })
                from_cache += 1
        if from_cache:
            notes.append({"ro": f"{from_cache} meciuri cu cote (din memoria locală, 0 cereri).",
                          "de": f"{from_cache} Spiele mit Quoten (aus dem lokalen Speicher, 0 Anfragen).",
                          "en": f"{from_cache} matches with odds (local cache, 0 requests)."}[lang if lang in LANGS else "ro"])

        # 2) upcoming football fixtures without odds (football-data.org)
        fd_error = None
        fd_max_days = int((config.get("football_data", {}) or {}).get("days_ahead", 10) or 10)
        if fd.configured and (not wanted_sports or "soccer" in wanted_sports):
            try:
                # the free tier rejects periods longer than 10 days -> clamp the window
                fd_end = min(end, now + timedelta(days=fd_max_days))
                data = fd.matches(
                    date_from=now.date().isoformat(),
                    date_to=fd_end.date().isoformat(),
                    status="SCHEDULED",
                )
                fd_upcoming = []
                for m in (data.get("matches") or []):
                    comp = m.get("competition") or {}
                    home = (m.get("homeTeam") or {}).get("name")
                    away = (m.get("awayTeam") or {}).get("name")
                    if not home or not away:
                        continue
                    item = {
                        "id": f"fd-{m.get('id')}",
                        "source": "football-data",
                        "sport": "soccer",
                        "league": comp.get("name"),
                        "competition_code": comp.get("code"),
                        "home": home,
                        "away": away,
                        "commence_time": m.get("utcDate"),
                        "has_odds": False,
                        "odds": None,
                    }
                    fd_upcoming.append(item)
                    items.append(dict(item))
                # keep a light index so /api/analyze can recognise scheduled football matches (0 extra requests)
                ttl.set("fd|upcoming", {
                    "fetched_at": datetime.now().isoformat(timespec="seconds"),
                    "items": fd_upcoming,
                })
                notes.append({"ro": "Meciurile viitoare de fotbal vin de la football-data.org (fără cote — cotele se iau separat, gratuit, când există).",
                              "de": "Kommende Fußballspiele kommen von football-data.org (ohne Quoten).",
                              "en": "Upcoming football fixtures come from football-data.org (no odds)."}[lang if lang in LANGS else "ro"])
                if horizon > fd_max_days:
                    notes.append({"ro": f"Fotbalul e afișat doar pentru următoarele {fd_max_days} zile (limita sursei gratuite); restul listei rămâne disponibil.",
                                  "de": f"Fußball wird nur für die nächsten {fd_max_days} Tage angezeigt (Limit der Gratis-Quelle).",
                                  "en": f"Football is shown for the next {fd_max_days} days only (free source limit); the rest of the list is still available."}[lang if lang in LANGS else "ro"])
            except Exception as e:
                fd_error = str(e)
                notes.append({
                    "ro": "football-data.org este temporar indisponibil; lista cu cote rămâne disponibilă.",
                    "de": "football-data.org ist vorübergehend nicht erreichbar; die Quotenliste bleibt verfügbar.",
                    "en": "football-data.org is temporarily unavailable; the odds list is still available.",
                }[lang if lang in LANGS else "ro"])
        elif not fd.configured and (not wanted_sports or "soccer" in wanted_sports):
            notes.append({"ro": "Pentru meciuri viitoare de fotbal activează football-data.org (cheie gratuită, 2 minute).",
                          "de": "Für kommende Fußballspiele aktiviere football-data.org (kostenloser Schlüssel, 2 Minuten).",
                          "en": "For upcoming football fixtures enable football-data.org (free key, 2 minutes)."}[lang if lang in LANGS else "ro"])

        # dedupe (prefer the one WITH odds) + search filter
        merged = _dedupe_fixtures(items)
        # mark each match as upcoming / live / finished (+ final score when we have one),
        # then order live -> upcoming -> finished so past games stop crowding the top
        merged = _annotate_results(
            merged, fd=fd, odds_api_key=odds_api_key, ttl=ttl,
            config=config, lang=lang, notes=notes,
        )
        base = _out(cache_key, {
            "items": merged,
            "notes": notes,
            "degraded": bool(fd_error),
            "generated_at": datetime.now().isoformat(timespec="seconds"),
        })
        shown = _filter_items(base.get("items") or [], q, max(1, int(limit)))
        return {
            "count": len(shown),
            "days": days,
            "query": q,
            "items": shown,
            "with_odds": sum(1 for it in shown if it.get("has_odds")),
            "notes": base.get("notes") or [],
            "degraded": base.get("degraded"),
            "generated_at": base.get("generated_at"),
            "cached": base.get("cached"),
            "cached_age_s": base.get("cached_age_s"),
        }

    # ---------------------------------------------------------------- analysis
    class AnalyzeIn(BaseModel):
        home: str
        away: str
        sport: str = "soccer"
        event_id: Optional[str] = None
        commence_time: Optional[str] = None
        lang: str = "ro"

    def _find_event(home, away, sport, event_id=None, commence_time=None):
        """Find the cached odds event for a fixture.

        The old version returned the first substring match and ignored the kickoff
        date: "Venezia FC" did not find "Venezia", and "Union Berlin vs Köln" on
        1 Nov could return the same teams' match from 27 Oct. We now score the
        team names fuzzily and prefer the event closest to the requested kickoff.
        """
        cache = storage.load_cache()
        groups = [sport] + [g for g in cache.keys() if g != sport]
        now = _now()
        best = None
        best_key = None
        for group in groups:
            events = cache.get(group)
            if not isinstance(events, list):
                continue
            for ev in events:
                if not isinstance(ev, dict):
                    continue
                if event_id and str(ev.get("id")) == str(event_id):
                    return ev, group

                sim = _pair_sim(home, away, ev.get("home_team"), ev.get("away_team"))
                if sim < 0.65:
                    continue

                if commence_time:
                    gap = _hours_apart(commence_time, ev.get("commence_time"))
                    if gap is not None and gap > 36.0:
                        continue
                    proximity = -(gap if gap is not None else 999.0)
                else:
                    ct = _parse_iso(ev.get("commence_time"))
                    proximity = -abs((ct - now).total_seconds()) / 3600.0 if ct else -9999.0

                has_h2h = 0
                for book in ev.get("bookmakers") or []:
                    if any(isinstance(m, dict) and m.get("key") == "h2h"
                           for m in (book.get("markets") or [])):
                        has_h2h = 1
                        break
                key = (round(sim, 3), proximity, has_h2h)
                if best_key is None or key > best_key:
                    best_key = key
                    best = (ev, group)
        return best if best else (None, None)

    def _localize_ctx(ctx, lang):
        """Return the team-context with the news impact summary rendered in `lang`.

        The engine builds `impact_summary` in Romanian; the app is trilingual, so
        we re-render it from the structured category counts for every language.
        """
        if not ctx or lang == "ro":
            return ctx
        out = dict(ctx)
        for side in ("home", "away"):
            team = ctx.get(side)
            if not isinstance(team, dict):
                continue
            t = dict(team)
            t["impact_summary"] = summarize_impact(team.get("impact"), lang)
            out[side] = t
        return out

    def _reasons(pred, best_odds, value_bets, ctx, lang, market=None):
        out = []
        L = lang if lang in LANGS else "ro"
        if value_bets:
            vb = max(value_bets, key=lambda v: v.get("edge_pct", 0))
            shift = vb.get("news_shift_pct") or 0.0
            line = {
                "ro": f"Modelul meu vede șansa „{vb['outcome'] or vb['side']}” la {round(vb['model_prob']*100)}%, "
                      f"iar piața o evaluează la {round((vb.get('market_prob') or 0)*100)}% → avantaj real de {vb['edge_pct']}%.",
                "de": f"Mein Modell sieht „{vb['outcome'] or vb['side']}“ bei {round(vb['model_prob']*100)}%, "
                      f"der Markt bei {round((vb.get('market_prob') or 0)*100)}% → echter Vorteil {vb['edge_pct']}%.",
                "en": f"My model puts „{vb['outcome'] or vb['side']}“ at {round(vb['model_prob']*100)}%, "
                      f"the market at {round((vb.get('market_prob') or 0)*100)}% → {vb['edge_pct']}% real edge.",
            }[L]
            if abs(shift) >= 0.3:
                line += {
                    "ro": f" Avantajul vine din știri: știrile au mutat șansa acestui rezultat cu {shift:+.1f} pp.",
                    "de": f" Der Vorteil kommt aus den Nachrichten: sie haben diese Wahrscheinlichkeit um {shift:+.1f} pp verschoben.",
                    "en": f" The edge comes from the news: they moved this probability by {shift:+.1f} pp.",
                }[L]
            out.append(line)
        if market and market.get("sides"):
            src = market.get("bookmaker") or ""
            if market.get("kind") == "sharp":
                label = {"ro": f"piața sharp ({src})", "de": f"den Sharp-Markt ({src})", "en": f"the sharp market ({src})"}[L]
            elif market.get("kind") == "consensus":
                books = market.get("books") or 0
                if L == "de":
                    label = "den Konsens aus einem Buchmacher" if books == 1 else f"den Konsens aus {books} Buchmachern"
                elif L == "en":
                    label = "the consensus of one bookmaker" if books == 1 else f"the consensus of {books} bookmakers"
                else:
                    label = "consensul unei case" if books == 1 else f"consensul a {books} case"
            else:
                label = {"ro": "piața", "de": "den Markt", "en": "the market"}[L]
            out.append({
                "ro": f"Avantajul e măsurat față de {label} (fără marjă), nu față de cea mai bună cotă — "
                      "altfel orice casă cu o cotă atipică pare „valoare”.",
                "de": f"Der Vorteil wird gegen {label} (ohne Marge) gemessen, nicht gegen die beste Quote — "
                      "sonst wirkt jeder Ausreißer wie „Value“.",
                "en": f"The edge is measured against {label} (margin-free), not against the best price — "
                      "otherwise any outlier price looks like „value”.",
            }[L])
            if not value_bets:
                ns = (pred or {}).get("news_shift") or {}
                moved = {s: v for s, v in ns.items() if abs(v) >= 0.3}
                if moved:
                    names = {
                        "home": (ctx.get("home") or {}).get("team") or "home",
                        "away": (ctx.get("away") or {}).get("team") or "away",
                        "draw": {"ro": "egal", "de": "Unentschieden", "en": "draw"}[L],
                    }
                    detail = ", ".join(f"{names.get(s, s)} {v:+.1f} pp" for s, v in moved.items())
                    out.append({
                        "ro": f"Știrile mută probabilitățile ({detail}), dar nu suficient cât să bată marja pieței — "
                              "deci nu văd un avantaj real pe care să te pun să pariezi.",
                        "de": f"Die Nachrichten verschieben die Wahrscheinlichkeiten ({detail}), aber nicht genug, "
                              "um die Marktmarge zu schlagen — kein echter Vorteil.",
                        "en": f"The news does move the probabilities ({detail}), but not enough to beat the market "
                              "margin — so no real edge I'd have you bet on.",
                    }[L])
                else:
                    out.append({
                        "ro": "Aici modelul meu nu are informație în plus față de piață, deci nu văd niciun avantaj real. "
                              "Prefer să spun asta decât să-ți vând o „ocazie” care nu există.",
                        "de": "Hier habe ich keine Zusatzinformation gegenüber dem Markt, also sehe ich keinen echten Vorteil. "
                              "Das sage ich lieber, als eine „Chance“ zu verkaufen, die es nicht gibt.",
                        "en": "Here I have no extra information versus the market, so I see no real edge. "
                              "Better to say that than to sell an „opportunity\" that isn't there.",
                    }[L])
        if pred and pred.get("lambdas"):
            out.append({
                "ro": f"Goluri estimate: {pred['lambdas']['home']} – {pred['lambdas']['away']} (implicite din cotele pieței).",
                "de": f"Erwartete Tore: {pred['lambdas']['home']} – {pred['lambdas']['away']} (aus den Marktquoten abgeleitet).",
                "en": f"Expected goals: {pred['lambdas']['home']} – {pred['lambdas']['away']} (implied by the market odds).",
            }[L])
        if ctx:
            for side_key, team in (("home", ctx.get("home")), ("away", ctx.get("away"))):
                if not team:
                    continue
                score = team.get("score") or 0
                if abs(score) >= 0.1:
                    direction = {"ro": "pozitiv" if score > 0 else "negativ",
                                 "de": "positiv" if score > 0 else "negativ",
                                 "en": "positive" if score > 0 else "negative"}[L]
                    out.append({
                        "ro": f"Tonul știrilor pentru {team.get('team')}: {direction} ({round(score,2)}). {team.get('impact_summary') or ''}".strip(),
                        "de": f"Nachrichten-Stimmung für {team.get('team')}: {direction} ({round(score,2)}). {team.get('impact_summary') or ''}".strip(),
                        "en": f"News mood for {team.get('team')}: {direction} ({round(score,2)}). {team.get('impact_summary') or ''}".strip(),
                    }[L])
        if best_odds:
            out.append({
                "ro": "Cota afișată e cea mai bună găsită la casele monitorizate (unde ai putea paria efectiv).",
                "de": "Die angezeigte Quote ist die beste der überwachten Buchmacher (wo du wirklich wetten könntest).",
                "en": "The shown price is the best found among the monitored bookmakers (where you could actually bet).",
            }[L])
        return out

    # Sports where "playing at home" is not a meaningful edge.
    _NO_HOME_EDGE = {"tennis", "boxing", "mma", "mixed_martial_arts", "table_tennis", "tabletennis", "esports"}

    # A team name can be a city/region/person too ("Lyon" -> a crash in Lyon County, Kansas).
    # Google-News headlines are matched by name only, so before we present one as a REASON we
    # drop civic/incident headlines that carry no sport context at all (honesty > recall).
    _CIVIC_RE = re.compile(
        r"\b(county|police|sheriff|crash|highway|interstate|city council|election|weather|storm|"
        r"flood|shooting|stabbing|arrested|charged|car accident|hospital|parish|township|"
        r"fire|obituary|lottery)\b", re.I)
    _NOISE_RE = re.compile(
        r"\b(tickets?|general sale|on sale|hospitality|kick[- ]off|parking|where to watch|"
        r"live stream|streaming|tv channel|how to watch|team news and|predicted xi)\b", re.I)
    _SPORT_RE = re.compile(
        r"\b(fc|cf|club|football|soccer|liga|league|serie|bundesliga|premier|europa|champions|"
        r"uefa|fifa|cup|coach|manager|squad|lineup|line-up|goal|match|fixture|derby|transfer|"
        r"loan|signing|midfielder|defender|striker|winger|keeper|goalkeeper|captain|team|"
        r"training|season|spiel|fussball|verein|trainer|mannschaft)\b", re.I)

    _TEAM_STOP = {"fc", "cf", "sc", "ac", "afc", "bc", "sk", "fk", "cs", "cd", "rc", "us", "sv",
                  "vfl", "vfb", "bk", "if", "ff", "cfr", "ks", "as", "ss", "ssc", "sd", "ud",
                  "ca", "club", "the", "and", "ltd", "city"}

    def _fold_text(s):
        t = (s or "").translate(_DIACRITICS)
        t = unicodedata.normalize("NFKD", t)
        t = "".join(ch for ch in t if not unicodedata.combining(ch)).lower()
        return " " + " ".join(re.split(r"[^a-z0-9]+", t)) + " "

    def _team_tokens(name):
        return [w for w in re.split(r"\s+", _fold_text(name).strip()) if len(w) >= 4 and w not in _TEAM_STOP]

    def _counter_credible(items, own=None, other=None):
        """Keep only headlines that look like real sport news about THIS team.

        Two filters, both honesty-driven:
          * civic/incident/admin noise is dropped (a team name can be a city too);
          * a headline whose *opponent* is mentioned before our team is dropped
            (e.g. "Celtic's injury scare ... ahead of Benfica" is not Benfica news).
        """
        own_tokens = _team_tokens(own) if own else []
        other_tokens = _team_tokens(other) if other else []
        out = []
        for h in items or []:
            s = str(h or "")
            if not s.strip():
                continue
            if _NOISE_RE.search(s):
                continue
            if _CIVIC_RE.search(s) and not _SPORT_RE.search(s):
                continue
            if own_tokens:
                text = _fold_text(s)

                def _first(tokens):
                    idxs = [text.find(" " + t + " ") for t in tokens]
                    idxs = [i for i in idxs if i >= 0]
                    return min(idxs) if idxs else -1

                i_own, i_other = _first(own_tokens), _first(other_tokens)
                if i_own < 0 and i_other >= 0:
                    continue                      # mentions only the opponent
                if 0 <= i_other < i_own:
                    continue                      # opponent named first
            out.append(s)
        return out

    def _counter_case(probabilities, ctx, market_block, group="", home_name="", away_name=""):
        """Local-first counter-case: real, external factors that could flip the result.

        Everything is derived from data we already have (team news/impact categories,
        home advantage, the draw price and the sharp market) — zero extra requests and
        nothing invented: when there is no grounded reason, `factors` stays empty and
        `grounded` is False (the dashboard says so honestly).

        The output is LANGUAGE-NEUTRAL (codes + numbers); the dashboard translates it.
        `balance_pct` is how credible the upset looks once these factors are weighed —
        it is NOT a model probability (the 1X2 keeps summing to ~100%).
        """
        if not probabilities:
            return None
        ph, pa, pd = probabilities.get("home"), probabilities.get("away"), probabilities.get("draw")
        if ph is None or pa is None:
            return None

        under_side, fav_side = ("home", "away") if ph <= pa else ("away", "home")
        under_p, fav_p = (ph, pa) if under_side == "home" else (pa, ph)
        team_of = {"home": home_name, "away": away_name}
        ctx_side = (ctx or {}).get(under_side) or {}
        under_team = ctx_side.get("team") or team_of.get(under_side) or under_side
        ctx_fav = (ctx or {}).get(fav_side) or {}
        fav_team = ctx_fav.get("team") or team_of.get(fav_side) or fav_side

        def _cats(side):
            return (((ctx or {}).get(side) or {}).get("impact") or {}).get("categories") or {}

        factors = []

        # 1) bad news at the favourite (injuries / suspensions / left out / departures)
        fc = _cats(fav_side)
        bad_items = _counter_credible((fc.get("injured") or []) + (fc.get("suspended") or [])
                                      + (fc.get("benched") or []) + (fc.get("transfers_out") or []),
                                      own=fav_team, other=under_team)
        if bad_items:
            n = len(bad_items)
            factors.append({
                "code": "fav_bad_news", "side": fav_side, "team": fav_team,
                "pp": round(min(6.0, 1.4 * n), 1),
                "support_pct": int(min(90, 25 + 15 * n)),
                "evidence": bad_items[:2],
            })

        # 2) good news at the underdog (players returning / signings)
        uc = _cats(under_side)
        good_items = _counter_credible((uc.get("returning") or []) + (uc.get("transfers_in") or []),
                                       own=under_team, other=fav_team)
        if good_items:
            n = len(good_items)
            factors.append({
                "code": "underdog_good_news", "side": under_side, "team": under_team,
                "pp": round(min(3.0, 0.8 * n), 1),
                "support_pct": int(min(70, 20 + 14 * n)),
                "evidence": good_items[:2],
            })

        # 3) the underdog plays at home
        if under_side == "home" and str(group or "").lower().replace(" ", "_").replace("-", "_") not in _NO_HOME_EDGE:
            factors.append({"code": "underdog_home", "side": "home", "team": under_team,
                            "pp": 4.0, "support_pct": 50, "evidence": []})

        # 4) the draw is a live threat (tight match)
        if pd is not None and pd >= 0.22:
            factors.append({"code": "draw_threat", "side": "draw",
                            "pp": round(min(4.0, (pd - 0.20) * 25), 1),
                            "support_pct": int(min(75, round(pd * 200))), "evidence": []})

        # 5) the sharp market rates the underdog higher than my model
        msides = (market_block or {}).get("sides") or {}
        mp = (msides.get(under_side) or {}).get("prob")
        if mp is not None and mp > under_p + 0.02:
            factors.append({"code": "market_skeptic", "side": under_side, "team": under_team,
                            "pp": round(min(4.0, (mp - under_p) * 35.0), 1),
                            "support_pct": int(min(70, round((mp - under_p) * 800))),
                            "evidence": []})

        # 6) the favourite isn't actually strong (win chance under ~42%)
        if fav_p < 0.42:
            gap = 0.42 - fav_p
            factors.append({"code": "thin_edge", "side": fav_side, "team": fav_team,
                            "pp": round(min(3.0, gap * 20), 1),
                            "support_pct": int(min(70, 30 + round(gap * 120))), "evidence": []})

        # Drop noise: a factor that would move the chance by less than half a point
        # is not worth showing (the user would just see a meaningless "+0 pp").
        factors = [f for f in factors if (f.get("pp") or 0) >= 0.5]

        factors.sort(key=lambda f: -(f.get("pp") or 0))
        factors = factors[:5]

        model_pct = int(round(under_p * 100))
        raw_pp = sum(f.get("pp") or 0 for f in factors)
        cap = min(55.0, model_pct + 20.0)  # an upset case is never a certainty
        balance_pct = int(round(min(cap, model_pct + raw_pp)))
        grounded = any(f.get("evidence") for f in factors)
        if not factors:
            confidence = "none"
        elif raw_pp >= 8 and grounded:
            confidence = "high"
        elif raw_pp >= 4:
            confidence = "medium"
        else:
            confidence = "low"

        return {
            "underdog": {"side": under_side, "team": under_team, "model_pct": model_pct},
            "favourite": {"side": fav_side, "team": fav_team, "model_pct": int(round(fav_p * 100))},
            "balance_pct": balance_pct,
            "delta_pp": balance_pct - model_pct,
            "confidence": confidence,
            "grounded": grounded,
            "factors": factors,
        }

    @router.post("/api/analyze")
    def analyze(req: AnalyzeIn, nocache: int = 0):
        lang = req.lang if req.lang in LANGS else "ro"
        # The cached payload now includes `counter`; bump the scheme so older
        # entries (written before the counter-case existed) are not served.
        cache_key = f"analyze|v4|{_norm(req.home)}|{_norm(req.away)}|{_norm(req.commence_time or '')}|{lang}"
        if not nocache:
            cached, age = ttl.get_entry(cache_key, analyze_ttl)
            if cached is not None:
                payload = dict(cached)
                payload["cached"] = True
                payload["cached_age_s"] = age
                return payload
        event, group = _find_event(req.home, req.away, req.sport, req.event_id, req.commence_time)
        sources = []
        if not event:
            ctx = _localize_ctx(context_engine.get_event_context(req.home, req.away, interactive=True), lang)
            # Recognise a scheduled football match from the football-data.org index (no extra requests).
            fixture = None
            best_fixture = 0.0
            for it in ((ttl.get("fd|upcoming", 7200) or {}).get("items") or []):
                sim = _pair_sim(req.home, req.away, it.get("home"), it.get("away"))
                if sim < 0.65:
                    continue
                if req.commence_time:
                    gap = _hours_apart(req.commence_time, it.get("commence_time"))
                    if gap is not None and gap > 36.0:
                        continue
                if sim > best_fixture:
                    best_fixture = sim
                    fixture = it
            reason = {
                "ro": "Nu găsesc cote pentru acest meci în sursele monitorizate, iar fără cote nu pot estima probabilități.",
                "de": "Ich finde für dieses Spiel keine Quoten in den überwachten Quellen — ohne Quoten kann ich keine Wahrscheinlichkeiten berechnen.",
                "en": "I can't find odds for this match in the monitored sources, and without odds I can't estimate probabilities.",
            }[lang]
            if fixture:
                reason = {
                    "ro": f"Meciul e în program ({fixture.get('league') or 'fotbal'}, {fixture.get('commence_time', '')[:16].replace('T', ' ')}), "
                          "dar casele de pariuri încă nu au publicat cote pentru el în sursele mele. Imediat ce apar cotele "
                          "(la următoarea reîmprospătare), analiza completă devine disponibilă.",
                    "de": f"Das Spiel steht im Plan ({fixture.get('league') or 'Fußball'}), aber die Buchmacher haben noch keine Quoten "
                          "veröffentlicht. Sobald Quoten erscheinen, ist die volle Analyse verfügbar.",
                    "en": f"The match is scheduled ({fixture.get('league') or 'football'}) but bookmakers haven't published odds yet in my "
                          "sources. As soon as odds appear, the full analysis becomes available.",
                }[lang]
            return _out(cache_key, {
                "found": False,
                "has_odds": False,
                "match": {"home": req.home, "away": req.away, "sport": req.sport,
                          "league": (fixture or {}).get("league"),
                          "commence_time": (fixture or {}).get("commence_time")},
                "fixture": fixture,
                "probabilities": None,
                "probabilities_note": "no_odds",
                "odds_status": "none",
                "best_odds": None,
                "value_bets": [],
                "context": ctx,
                "reasons": [reason],
                "sources": ["news"] + (["fixtures"] if fixture else []),
                "note": {"ro": "Sfat: apasă „Alege un meci” și dă click pe meciul dorit.",
                         "de": "Tipp: Öffne „Spiel wählen“ und klicke auf das gewünschte Spiel.",
                         "en": "Tip: open „Pick a match” and click the match."}[lang],
            })

        home_name = event.get("home_team") or req.home
        away_name = event.get("away_team") or req.away
        ctx = _localize_ctx(context_engine.get_event_context(home_name, away_name, interactive=True), lang)
        sources.append("odds")

        lambdas = None
        if group == "soccer" and history_analyzer:
            try:
                lambdas = history_analyzer.lambdas(home_name, away_name)
            except Exception:
                lambdas = None
        pred = predict_1x2(event, group, lambdas=lambdas, context_engine=context_engine, interactive=True)
        if not pred:
            pred = predict_1x2(event, group, lambdas=lambdas, interactive=True)
        if context_engine and context_engine.config.get("enabled"):
            sources.append("news")

        best_odds, best_book = {}, {}
        for book in event.get("bookmakers", []) or []:
            for market in book.get("markets", []) or []:
                if market.get("key") != "h2h":
                    continue
                for out in market.get("outcomes", []) or []:
                    name = out.get("name")
                    price = out.get("price")
                    if not price or price < 1.02:
                        continue
                    if name not in best_odds or price > best_odds[name]:
                        best_odds[name] = price
                        best_book[name] = book.get("title")

        # --- honest market reference (sharp book or median consensus, margin-free) ---
        # For the displayed analysis one sane book is enough; value bets still use
        # the stricter default of 3 books inside value.find_value_bets().
        ref = sharp.reference(event, min_consensus_books=1)
        sd = sharp.sides(event, ref)
        market_block = None
        if ref.get("probs"):
            market_block = {
                "kind": ref.get("kind"),
                "bookmaker": ref.get("bookmaker") or "",
                "books": ref.get("books"),
                "margin_pct": ref.get("margin_pct"),
                "sides": {},
            }
            for side in ("home", "draw", "away"):
                entry = sd.get(side)
                if not entry:
                    continue
                market_block["sides"][side] = {
                    "name": entry.get("name"),
                    "prob": round(entry.get("prob") or 0, 4),
                    "price": entry.get("price"),
                    "fair_odds": entry.get("fair_odds"),
                }

        try:
            vbs = find_value_bets(
                [event], group, threshold,
                context_engine=context_engine,
                borderline_window_pct=borderline_window_pct,
                history_analyzer=history_analyzer,
                interactive=True,
            )
        except Exception:
            vbs = []

        probabilities = None
        if pred:
            probabilities = {
                "home": round(pred.get("home") or 0, 4),
                "draw": round(pred["draw"], 4) if pred.get("draw") is not None else None,
                "away": round(pred.get("away") or 0, 4),
                "type": pred.get("type"),
            }
        probabilities_note = None
        odds_status = "ok"
        if not probabilities:
            odds_status = _odds_state(event)
            probabilities_note = odds_status
        headline_items = (ctx.get("home", {}) or {}).get("headlines", []) + (ctx.get("away", {}) or {}).get("headlines", [])
        ct = _parse_iso(event.get("commence_time"))
        _dur = GROUP_DURATION_MIN.get(event.get("sport_group") or group, DEFAULT_DURATION_MIN)
        is_past = bool(ct and _now() >= ct + timedelta(minutes=_dur))
        return _out(cache_key, {
            "found": True,
            "has_odds": True,
            "match": {
                "home": home_name,
                "away": away_name,
                "league": event.get("sport_title"),
                "sport": event.get("sport_group") or group,
                "commence_time": event.get("commence_time"),
                "event_id": event.get("id"),
                "is_past": is_past,
            },
            "probabilities": probabilities,
            "probabilities_note": probabilities_note,
            "odds_status": odds_status,
            "best_odds": best_odds or None,
            "best_bookmakers": best_book or None,
            "market": market_block,
            "value_bets": vbs,
            "context": ctx,
            "news": {
                "shift_pct": (pred or {}).get("news_shift") or None,
                "scores": (pred or {}).get("news_score") or None,
                "weight": context_engine.config.get("news_weight"),
            } if pred else None,
            "players": extract_players(headline_items, exclude_terms=[home_name, away_name]),
            "reasons": _reasons(pred, best_odds, vbs, ctx, lang, market=market_block),
            "counter": _counter_case(probabilities, ctx, market_block,
                                     group=event.get("sport_group") or group,
                                     home_name=home_name, away_name=away_name),
            "sources": sources,
            "disclaimer": {
                "ro": "Probabilitățile sunt estimate de model, nu certitudini. Pariază responsabil.",
                "de": "Wahrscheinlichkeiten sind Modellschätzungen, keine Gewissheiten. Spiele verantwortungsvoll.",
                "en": "Probabilities are model estimates, not certainties. Bet responsibly.",
            }[lang],
        })

    # ------------------------------------------------------------- recommend
    @router.get("/api/recommend")
    def recommend(lang: str = "ro", min_stars: int = 2, min_prob: float = 0.45,
                  min_odds: float = 1.30, max_odds: float = 6.0,
                  min_edge: float = 4.0, max_edge: float = 25.0,
                  exclude: str = "", sport: str = ""):
        lang = lang if lang in LANGS else "ro"
        exclude_ids = {x.strip() for x in (exclude or "").split(",") if x.strip()}
        results = value_state.get("results")
        if results is None and scan_value_bets:
            try:
                results = scan_value_bets()
            except Exception:
                results = []
        results = results or []
        now = _now()

        def base_ok(vb):
            return (
                vb.get("event_id") and str(vb.get("event_id")) not in exclude_ids
                and _parse_iso(vb.get("commence_time"))
                and _parse_iso(vb.get("commence_time")) > now - timedelta(hours=1)
            )

        # Podeaua de "avantaj real" NU coboara niciodata sub pragul de onestitate
        # (value_threshold_pct, acum 2.0) - altfel recomandarea respinge exact pariurile
        # pe care scanarea le-a acceptat (ex. edge 2.43% cadea intre 2.0 si vechiul 4.0/2.5).
        edge_floor = float(threshold or 0.0) or float(min_edge)
        strict_edge = max(float(min_edge), edge_floor)
        ladders = [
            ("strict", dict(stars=min_stars, prob=min_prob, o=(min_odds, max_odds), e=(strict_edge, max_edge))),
            ("relaxed_prob", dict(stars=min_stars, prob=0.35, o=(min_odds, max_odds), e=(edge_floor, 30.0))),
            ("relaxed_stars", dict(stars=1, prob=0.30, o=(1.20, 9.0), e=(edge_floor, 35.0))),
            ("best_available", dict(stars=0, prob=0.0, o=(1.01, 50.0), e=(edge_floor, 99.0))),
        ]

        def matches(vb, f, ignore_exclude=False):
            if not ignore_exclude:
                if not base_ok(vb):
                    return False
            else:
                ct = _parse_iso(vb.get("commence_time"))
                if not (vb.get("event_id") and ct and ct > now - timedelta(hours=1)):
                    return False
            return (
                (vb.get("confidence") or 0) >= f["stars"]
                and (vb.get("model_prob") or 0) >= f["prob"]
                and f["o"][0] <= (vb.get("odds") or 0) <= f["o"][1]
                and f["e"][0] <= (vb.get("edge_pct") or 0) <= f["e"][1]
            )

        chosen_pool, used_label = [], "strict"
        for label, f in ladders:
            pool = [vb for vb in results if matches(vb, f)]
            if pool:
                chosen_pool, used_label = pool, label
                break

        if not chosen_pool:
            # Distinge "nu exista nimic" de "ai vazut deja tot ce exista".
            loose = ladders[-1][1]
            available = [vb for vb in results if matches(vb, loose, ignore_exclude=True)]
            if available:
                msg = {
                    "ro": f"Am găsit {len(available)} "
                          f"{'variantă' if len(available) == 1 else 'variante'} cu avantaj real, "
                          "dar le-ai văzut deja pe toate. Așteaptă următoarea reîmprospătare a cotelor.",
                    "de": f"Es gibt {len(available)} Option(en) mit echtem Vorteil, aber du hast sie "
                          "schon alle gesehen. Warte auf die nächste Quoten-Aktualisierung.",
                    "en": f"There {'is' if len(available) == 1 else 'are'} {len(available)} option(s) "
                          "with a real edge, but you have already seen them all. "
                          "Wait for the next odds refresh.",
                }[lang]
            else:
                msg = {
                    "ro": "Nu am găsit nimic solid acum. Încearcă din nou după următoarea reîmprospătare a cotelor.",
                    "de": "Aktuell nichts Solides gefunden. Versuche es nach der nächsten Quoten-Aktualisierung erneut.",
                    "en": "Nothing solid right now. Try again after the next odds refresh.",
                }[lang]
            return {
                "pick": None,
                "count": 0,
                "relaxed": False,
                "alternatives": 0,
                "message": msg,
            }

        weights = [max(0.1, (vb.get("confidence") or 1)) * max(0.1, (vb.get("edge_pct") or 0)) for vb in chosen_pool]
        pick = random.choices(chosen_pool, weights=weights, k=1)[0]
        return {
            "pick": pick,
            "count": len(chosen_pool),
            "relaxed": used_label != "strict",
            "relaxed_label": used_label,
            "alternatives": max(0, len(chosen_pool) - 1),
            "message": (
                ({"ro": "Am găsit o singură variantă care trece filtrele. Uite-o:",
                  "de": "Ich habe genau eine Option gefunden, die die Filter besteht. Hier ist sie:",
                  "en": "I found exactly one option that passes the filters. Here it is:"}[lang]
                 if len(chosen_pool) == 1 else
                 {"ro": f"Am găsit {len(chosen_pool)} variante care trec filtrele. Uite una:",
                  "de": f"{len(chosen_pool)} Optionen passen zu den Filtern. Hier eine:",
                  "en": f"{len(chosen_pool)} options pass the filters. Here's one:"}[lang])
                if used_label == "strict" else
                {"ro": f"Singura variantă cu avantaj real acum (peste pragul de {edge_floor:.0f}%) — fără filtre de încredere:",
                 "de": f"Die einzige Option mit echtem Vorteil (über {edge_floor:.0f}%) — ohne Zuversichtsfilter:",
                 "en": f"The only option with a real edge (above the {edge_floor:.0f}% floor) — no confidence filters:"}[lang]
                if used_label == "best_available" else
                {"ro": "Nu am găsit nimic peste 2★ acum, așa că am relaxat filtrele — asta e cea mai bună variantă disponibilă:",
                 "de": "Nichts über 2★ gefunden, Filter gelockert — das ist die beste verfügbare Option:",
                 "en": "Nothing above 2★ right now, so I relaxed the filters — here's the best available option:"}[lang]
            ),
        }

    return router


def quota_guard(refresh_state, monthly_limit=500, min_remaining=25):
    """Return (ok, message) so callers can avoid burning the last requests."""
    remaining = refresh_state.get("remaining")
    if remaining is None:
        return True, None
    if remaining <= 0:
        return False, "Limita lunară de cote e atinsă. Folosesc datele deja salvate; se reînnoiește la 1 ale lunii viitoare."
    if remaining < min_remaining:
        return False, f"Am doar {remaining} cereri de cote rămase luna asta — le păstrez pentru cazuri importante."
    return True, None
