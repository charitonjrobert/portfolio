import json
import os
import threading
import time
from datetime import datetime
from pathlib import Path

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel

from odds_fetcher import OddsFetcher
from storage import Storage
from value import find_value_bets, find_arbitrage
from bankroll import Bankroll
from context import ContextEngine
from chat import ChatService, MICROBIST_PROMPT, FOOTBALL_MARKET_KEYS, FOOTBALL_CORE_MARKETS, FOOTBALL_VALUE_FILTER
from provider_bridge import load_opencode_providers
from history import HistoryAnalyzer
from leagues import build_catalog, group_catalog, match_leagues, fetch_leagues
from football import FootballAPI
from fd import FootballData
from access import AccessGate, RateLimitGate
from ttl_cache import TtlCache
from microbist import build_router, quota_guard, note_ai_error, note_ai_ok
from betting import build_router as build_betting_router
from live import build_router as build_live_router
import logging
import logging.handlers

BACKEND_DIR = Path(__file__).parent
PROJECT_DIR = BACKEND_DIR.parent
DASHBOARD_DIR = PROJECT_DIR / "dashboard"

MONTHLY_LIMIT = 500

CONFIG_PATH = BACKEND_DIR / "config.json"
CONFIG_SEED = CONFIG_PATH if CONFIG_PATH.exists() else BACKEND_DIR / "config.example.json"
if not CONFIG_PATH.exists():
    print(f"[config] {CONFIG_PATH.name} missing, using {CONFIG_SEED.name} (no API keys).")
with open(CONFIG_SEED, encoding="utf-8") as f:
    CONFIG = json.load(f)

API_KEY = CONFIG["api_key"]
THRESHOLD = CONFIG.get("value_threshold_pct", 4.0)
KELLY_FRACTION = CONFIG.get("kelly_fraction", 0.25)

AUTO_CFG = CONFIG.get("auto_refresh", {})
AUTO_ENABLED = AUTO_CFG.get("enabled", True)
AUTO_INTERVAL_HOURS = AUTO_CFG.get("interval_hours", 6)

refresh_lock = threading.Lock()
refresh_state = {
    "last_refresh": None,
    "next_refresh": None,
    "remaining": None,
    "used_total": 0,
    "auto_enabled": AUTO_ENABLED,
    "interval_hours": AUTO_INTERVAL_HOURS,
    "refreshing": False,
}

fetcher = OddsFetcher(API_KEY, regions=CONFIG.get("regions", ["eu"]), markets=CONFIG.get("markets", ["h2h", "totals"]))
storage = Storage(
    cache_file=str(BACKEND_DIR / (CONFIG.get("cache_file") or "odds_cache.json")),
    db_file=str(BACKEND_DIR / (CONFIG.get("db_file") or "bets.db")),
)
context_engine = ContextEngine(
    config=CONFIG.get("context", {}),
    cache_file=str(BACKEND_DIR / "context_cache.json"),
)
history_analyzer = HistoryAnalyzer(str(BACKEND_DIR / "history_matches.csv"))
football = FootballAPI(CONFIG.get("api_football", {}).get("api_key", ""))
FDC = CONFIG.get("football_data", {}) or {}
football_data = FootballData(
    api_key=FDC.get("api_key", ""),
    base_url=FDC.get("base_url", "https://api.football-data.org/v4"),
)
# one shared TTL cache for every router (fixtures, analyses, scores)
shared_ttl = TtlCache(BACKEND_DIR / "cache_ttl.json", retention_seconds=86400)
def _find_opencode_dir():
    candidates = [
        os.path.expanduser("~/.config/opencode"),
        r"C:\Users\eusun\.config\opencode",
        r"C:\Users\Administrator\.config\opencode",
    ]
    for d in candidates:
        if os.path.exists(os.path.join(d, "opencode.json")) or os.path.exists(os.path.join(d, "opencode.jsonc")):
            return d
    return candidates[0]


def build_chat_providers():
    providers = []
    chat_cfg = CONFIG.get("chat", {})
    manual_key = chat_cfg.get("api_key", "") or ""
    if manual_key and manual_key != "YOUR_CHAT_API_KEY":
        base_url = (chat_cfg.get("base_url", "https://api.deepseek.com/v1")).rstrip("/")
        model = chat_cfg.get("model", "deepseek-chat")
        # primary model, then the same endpoint's backup models (tried in that order) —
        # e.g. a fast sibling when the smart model is overloaded (503)
        models = [model] + [m for m in (chat_cfg.get("fallback_models") or []) if m and m != model]
        for idx, name in enumerate(models):
            providers.append(
                {
                    "name": "manual" if idx == 0 else f"manual-{idx}",
                    "base_url": base_url,
                    "api_key": manual_key,
                    "models": [name],
                    "preferred_model": name,
                }
            )
        # separate endpoints as the last resort (own key/base_url, e.g. another provider)
        for idx, fb in enumerate(chat_cfg.get("fallbacks") or []):
            fb = fb or {}
            fb_key = fb.get("api_key", "") or ""
            if not fb_key or fb_key == "YOUR_CHAT_API_KEY":
                continue
            fb_model = fb.get("model", "deepseek-chat")
            providers.append(
                {
                    "name": fb.get("name") or f"fallback-{idx + 1}",
                    "base_url": (fb.get("base_url") or "https://api.deepseek.com/v1").rstrip("/"),
                    "api_key": fb_key,
                    "models": [fb_model],
                    "preferred_model": fb_model,
                }
            )
    providers.extend(load_opencode_providers(_find_opencode_dir()))
    # stable sort keeps the configured order; keyless providers go last
    providers.sort(key=lambda p: 0 if p.get("api_key") else 1)
    if not providers:
        providers.append(
            {
                "name": "deepseek",
                "base_url": "https://api.deepseek.com/v1",
                "api_key": "",
                "models": ["deepseek-chat"],
                "preferred_model": "deepseek-chat",
            }
        )
    return providers


chat_service = ChatService(
    providers=build_chat_providers(),
    storage=storage,
    fetcher=fetcher,
    context_engine=context_engine,
    history_analyzer=history_analyzer,
    threshold=THRESHOLD,
    max_iterations=CONFIG.get("chat", {}).get("max_iterations", 6),
    borderline_window_pct=CONFIG.get("context", {}).get("borderline_window_pct", 3.0),
    system_prompt=MICROBIST_PROMPT if CONFIG.get("chat", {}).get("persona") == "microbist" else None,
    football=football,
    cached_value_bets=lambda: value_state.get("results"),
)

app = FastAPI(
    title="MicrobistBets",
    # interactive API docs are extra surface for no benefit on a private app
    docs_url=None,
    redoc_url=None,
    openapi_url=None,
)
# Access gate goes last on purpose: in Starlette the last added middleware is the outermost,
# so unauthorized requests are rejected before touching any paid source.
ACCESS_KEY = (CONFIG.get("ui", {}) or {}).get("access_key", "")
app.add_middleware(AccessGate, key=ACCESS_KEY)
# rate limiting sits in front of everything, so even a flood of unauthenticated calls stays cheap
app.add_middleware(RateLimitGate, per_minute=int(CONFIG.get("security", {}).get("requests_per_minute") or 150))


def group_of(sport_key, sport_title):
    text = f"{sport_key} {sport_title}".lower()
    for g in CONFIG["sports_groups"]:
        if g in text:
            return g
    return "other"


@app.get("/")
def dashboard():
    # always revalidate the HTML; it points at the assets, and /api/version drives the auto-reload
    return FileResponse(str(DASHBOARD_DIR / "index.html"), headers={"Cache-Control": "no-store"})


@app.get("/api/debug/providers")
def debug_providers():
    provs = []
    for p in build_chat_providers():
        provs.append({"name": p["name"], "key": bool(p.get("api_key")), "model": p.get("preferred_model")})
    raw = []
    for p in load_opencode_providers(_find_opencode_dir()):
        raw.append({"name": p["name"], "key": bool(p.get("api_key"))})
    return {"built": provs, "raw": raw, "config_dir": _find_opencode_dir()}


def do_refresh():
    if not refresh_lock.acquire(blocking=False):
        return {"error": "Refresh deja în curs, încearcă peste câteva secunde."}
    refresh_state["refreshing"] = True
    try:
        if not API_KEY or API_KEY == "YOUR_API_KEY":
            return {"error": "API key missing. Set it in backend/config.json."}
        context_engine.begin_scan()
        try:
            catalog = build_catalog(fetcher)
        except Exception as e:
            return {"error": f"Sports list fetch failed: {e}"}

        events_by_sport = {}
        used = 0
        remaining = None
        from_cache = []
        preferred = CONFIG.get("preferred_sports", {})
        by_group = group_catalog(catalog)
        cache_ttl_h = float(CONFIG.get("auto_refresh", {}).get("cache_ttl_hours", 6))
        cached_all = storage.load_cache()
        for sport_group, pref_keys in preferred.items():
            cats = by_group.get(sport_group, [])
            chosen_list = [c for c in cats if c["key"] in pref_keys]
            if not chosen_list:
                chosen_list = sorted(cats, key=lambda c: c.get("title", ""))[:1]
            group_events = []
            for chosen in chosen_list:
                sport_key = chosen["key"]
                # Refoloseste cotele din cache daca liga e proaspata (< cache_ttl_hours)
                age_h = storage.league_age_hours(sport_key)
                cached_events = []
                if age_h is not None and age_h < cache_ttl_h:
                    cached_events = [
                        ev for ev in cached_all.get(sport_group, [])
                        if isinstance(ev, dict) and ev.get("sport_key") == sport_key
                    ]
                if cached_events:
                    events = cached_events
                    headers = {}
                    from_cache.append(chosen.get("title") or sport_key)
                else:
                    try:
                        events, headers = fetcher.get_odds(sport_key)
                        storage.mark_league(sport_key)
                    except Exception as e:
                        continue
                    used += 1
                for ev in events:
                    ev["sport_group"] = sport_group
                    ev["sport_title"] = chosen.get("title")
                group_events.extend(events)
                rem = headers.get("remaining")
                if rem is not None:
                    remaining = rem
            events_by_sport[sport_group] = group_events

        events_by_sport = storage.merge_cache(events_by_sport)
        try:
            storage.prune_expired(int(CONFIG.get("cache", {}).get("retention_hours", 48)))
        except Exception:
            pass
        now = time.time()
        refresh_state["last_refresh"] = now
        refresh_state["next_refresh"] = now + refresh_state["interval_hours"] * 3600
        refresh_state["remaining"] = remaining
        refresh_state["sport_count"] = len(events_by_sport)
        if remaining is not None:
            refresh_state["used_total"] = MONTHLY_LIMIT - remaining
        try:
            _scan_value_bets()
        except Exception:
            pass
        return {
            "refreshed": True,
            "sports": {g: len(v) for g, v in events_by_sport.items()},
            "requests_used": used,
            "requests_remaining": remaining,
            "leagues_from_cache": from_cache,
        }
    finally:
        refresh_state["refreshing"] = False
        refresh_lock.release()


@app.get("/api/refresh")
def refresh(force: int = 0):
    ok, msg = quota_guard(refresh_state, MONTHLY_LIMIT)
    if not ok and not force:
        return {"error": msg, "guard": True, "remaining": refresh_state.get("remaining")}
    return do_refresh()


@app.get("/api/refresh/status")
def refresh_status():
    now = time.time()
    last = refresh_state.get("last_refresh")
    next_ts = refresh_state.get("next_refresh")
    return {
        "auto_enabled": refresh_state["auto_enabled"],
        "interval_hours": refresh_state["interval_hours"],
        "refreshing": refresh_state["refreshing"],
        "last_refresh": last,
        "last_refresh_ago_min": round((now - last) / 60, 1) if last else None,
        "next_refresh": next_ts,
        "next_refresh_in_min": round((next_ts - now) / 60, 1) if next_ts else None,
        "requests_remaining": refresh_state.get("remaining"),
        "requests_used_total": refresh_state.get("used_total"),
        "monthly_limit": MONTHLY_LIMIT,
        "sport_count": refresh_state.get("sport_count", 0),
        "estimated_refreshes_left": (
            int(refresh_state.get("remaining", 0) / max(refresh_state.get("sport_count", 1), 1))
            if refresh_state.get("remaining") is not None
            else 0
        ),
    }


class AutoIn(BaseModel):
    enabled: bool


@app.post("/api/refresh/auto")
def set_auto(req: AutoIn):
    refresh_state["auto_enabled"] = req.enabled
    return {"auto_enabled": req.enabled}


def _auto_refresh_loop():
    while True:
        time.sleep(max(refresh_state["interval_hours"], 1) * 3600)
        if refresh_state["auto_enabled"] and not refresh_lock.locked():
            try:
                do_refresh()
            except Exception:
                pass


value_state = {"results": None, "updated": None}


def _scan_value_bets():
    """Recalculeaza value bets DIN CACHE (0 requesturi API) si le salveaza rubricat."""
    context_engine.begin_scan()
    results = []
    for group, events in storage.load_cache().items():
        if not isinstance(events, list):
            continue
        results.extend(
            find_value_bets(
                events,
                group,
                THRESHOLD,
                context_engine=context_engine,
                borderline_window_pct=CONFIG.get("context", {}).get("borderline_window_pct", 3.0),
                history_analyzer=history_analyzer,
            )
        )
    results.sort(key=lambda vb: vb.get("edge_pct", 0), reverse=True)
    ts = datetime.now().isoformat(timespec="seconds")
    for vb in results:
        storage.add_snapshot(
            {
                "ts": ts,
                "sport": vb.get("sport", ""),
                "event": f"{vb.get('home_team', '')} vs {vb.get('away_team', '')}",
                "outcome": vb.get("side", ""),
                "odds": vb.get("odds", 0),
                "bookmaker": vb.get("bookmaker", ""),
                "edge_pct": vb.get("edge_pct", 0),
            }
        )
    value_state["results"] = results
    value_state["updated"] = ts
    return results


VALUE_SCAN_MINUTES = float(CONFIG.get("auto_refresh", {}).get("value_scan_minutes", 30))


def _value_scan_loop():
    while True:
        time.sleep(VALUE_SCAN_MINUTES * 60)
        try:
            _scan_value_bets()
        except Exception:
            pass


@app.on_event("startup")
def _start_auto_refresh():
    cache = storage.load_cache()
    try:
        removed = storage.prune_expired(int(CONFIG.get("cache", {}).get("retention_hours", 48)))
        if removed:
            print(f"[cache] pruned {removed} finished events from the odds cache")
    except Exception:
        pass
    if AUTO_CFG.get("refresh_on_startup", True) and not cache:
        try:
            do_refresh()
        except Exception:
            pass
    else:
        cache_file = Path(storage.cache_file)
        if cache and cache_file.exists():
            mtime = cache_file.stat().st_mtime
            now = time.time()
            refresh_state["last_refresh"] = mtime
            refresh_state["next_refresh"] = mtime + refresh_state["interval_hours"] * 3600
    threading.Thread(target=_auto_refresh_loop, daemon=True).start()
    threading.Thread(target=_value_scan_loop, daemon=True).start()
    # prima scanare in fundal, ca sa nu blocam pornirea serverului
    threading.Thread(
        target=lambda: _safe(lambda: _scan_value_bets()), daemon=True
    ).start()


def _safe(fn):
    try:
        fn()
    except Exception:
        pass


@app.get("/api/odds")
def odds():
    return storage.load_cache()


@app.get("/api/value-bets")
def value_bets():
    if value_state["results"] is not None:
        return value_state["results"]
    try:
        return _scan_value_bets()
    except Exception:
        return []


@app.get("/api/value-bets/auto")
def value_bets_auto():
    """Value bets rubricate pe sport, din ultima scanare automata (fara blocare)."""
    results = value_state["results"] or []
    groups = {}
    for vb in results:
        groups.setdefault(vb.get("sport", "other"), []).append(vb)
    return {
        "updated": value_state["updated"],
        "count": len(results),
        "scanning": value_state["results"] is None,
        "groups": dict(sorted(groups.items(), key=lambda kv: -len(kv[1]))),
    }


@app.get("/api/leagues")
def leagues_list():
    try:
        catalog = build_catalog(fetcher)
    except Exception as e:
        return {"error": f"Catalog fetch failed: {e}", "total": 0, "groups": {}}
    return {"total": len(catalog), "groups": group_catalog(catalog)}


class LeagueFetchIn(BaseModel):
    query: str
    cap: int = 5


@app.post("/api/leagues/fetch")
def leagues_fetch(req: LeagueFetchIn):
    try:
        catalog = build_catalog(fetcher)
    except Exception as e:
        return {"error": f"Catalog fetch failed: {e}"}
    hits = match_leagues(catalog, req.query)
    if not hits:
        return {
            "error": f"Nicio ligă găsită pentru '{req.query}'.",
            "hits": [],
            "total_leagues": len(catalog),
        }
    return fetch_leagues(fetcher, storage, hits, cap=req.cap)


@app.get("/api/football/leagues")
def football_leagues(query: str = "romania"):
    if not football.api_key:
        return {"error": "Lipsă cheie API-Football. Completează api_football.api_key în backend/config.json."}
    try:
        data, remaining, errors = football.leagues(search=query)
        if not data and query.strip():
            data, remaining, errors = football.leagues(country=query)
    except Exception as e:
        return {"error": str(e)}
    out = []
    for item in data[:25]:
        lg = item.get("league", {}) or {}
        country = item.get("country", {}) or {}
        out.append({
            "id": lg.get("id"),
            "name": lg.get("name"),
            "type": lg.get("type"),
            "country": country.get("name"),
        })
    return {"query": query, "leagues": out, "requests_remaining": remaining}


@app.get("/api/football/fixtures")
def football_fixtures(query: str = "azi"):
    if not football.api_key:
        return {"error": "Lipsă cheie API-Football. Completează api_football.api_key în backend/config.json."}
    try:
        today = datetime.now().date().isoformat()
        rem = football.remaining_requests()
        fx_data, _, errors = football.fixtures(date=today)
        if query.strip().lower() in ("", "azi", "today", "toate", "lume"):
            matches = []
            for fx in fx_data[:30]:
                teams = fx.get("teams", {}) or {}
                home = teams.get("home", {}) or {}
                away = teams.get("away", {}) or {}
                lg = fx.get("league", {}) or {}
                matches.append({
                    "league": lg.get("name"),
                    "country": lg.get("country"),
                    "date": fx.get("fixture", {}).get("date"),
                    "home": home.get("name"),
                    "away": away.get("name"),
                    "status": fx.get("fixture", {}).get("status", {}).get("short"),
                })
            return {"scope": "toată lumea - meciurile de azi", "matches": matches, "requests_remaining": rem}
        lg_data, _, _ = football.leagues(search=query)
        if not lg_data and query.strip():
            lg_data, _, _ = football.leagues(country=query)
        if not lg_data:
            return {"error": f"Nicio ligă găsită pentru '{query}'.", "requests_remaining": rem}
        lg = (lg_data[0].get("league") or {}).get("id")
        name = (lg_data[0].get("league") or {}).get("name")
        fx_data = [f for f in fx_data if (f.get("league") or {}).get("id") == lg]
    except Exception as e:
        return {"error": str(e)}
    matches = []
    for fx in fx_data[:15]:
        teams = fx.get("teams", {}) or {}
        home = teams.get("home", {}) or {}
        away = teams.get("away", {}) or {}
        matches.append({
            "date": fx.get("fixture", {}).get("date"),
            "home": home.get("name"),
            "away": away.get("name"),
            "status": fx.get("fixture", {}).get("status", {}).get("short"),
        })
    return {"league": name, "matches": matches, "requests_remaining": rem}


@app.get("/api/football/odds")
def football_odds(query: str = "romania", market: str = ""):
    if not football.api_key:
        return {"error": "Lipsă cheie API-Football. Completează api_football.api_key în backend/config.json."}
    try:
        today = datetime.now().date().isoformat()
        rem = football.remaining_requests()
        lg_data, _, _ = football.leagues(search=query)
        if not lg_data and query.strip():
            lg_data, _, _ = football.leagues(country=query)
        if not lg_data:
            return {"error": f"Nicio ligă găsită pentru '{query}'.", "requests_remaining": rem}
        lg = (lg_data[0].get("league") or {}).get("id")
        name = (lg_data[0].get("league") or {}).get("name")
        country = (lg_data[0].get("country") or {}).get("name")
        fx_data, _, _ = football.fixtures(date=today)
        fx_data = [f for f in fx_data if (f.get("league") or {}).get("id") == lg]
        if not fx_data:
            return {"error": f"Nicio echipă din {name} nu joacă astăzi.", "requests_remaining": rem}
        results = []
        for fx in fx_data[:3]:
            fid = (fx.get("fixture") or {}).get("id")
            teams = fx.get("teams", {}) or {}
            home = (teams.get("home") or {}).get("name")
            away = (teams.get("away") or {}).get("name")
            if not fid:
                continue
            od, _, errors = football.odds_by_fixture(fid)
            time.sleep(0.9)
            if errors:
                results.append({"match": f"{home} vs {away}", "note": str(errors)})
                continue
            bets = {}
            for item in od:
                for bm in item.get("bookmakers", []):
                    for bet in bm.get("bets", []):
                        nm = bet.get("name")
                        for v in bet.get("values", []):
                            key = f"{nm}: {v.get('value')}"
                            price = float(v.get("odd"))
                            if key not in bets or price > bets[key]["price"]:
                                bets[key] = {"price": price, "book": bm.get("name")}
            wanted = FOOTBALL_MARKET_KEYS.get(market.strip().lower(), FOOTBALL_CORE_MARKETS)
            filtered = {}
            for k, val in bets.items():
                nm = k.rsplit(":", 1)[0].strip()
                if nm not in wanted:
                    continue
                v = k.rsplit(":", 1)[1].strip()
                allowed = FOOTBALL_VALUE_FILTER.get(nm)
                if allowed and v not in allowed:
                    continue
                filtered[k] = val
            results.append({"match": f"{home} vs {away}", "odds": filtered})
        return {"league": name, "country": country, "market": market or "principale", "matches": results, "requests_remaining": rem}
    except Exception as e:
        return {"error": str(e)}


@app.get("/api/football/match")
def football_match(query: str = "", team_a: str = "", team_b: str = "", fixture_id: str = ""):
    if not football.api_key:
        return {"error": "Lipsă cheie API-Football. Completează api_football.api_key în backend/config.json."}
    return chat_service._football_match(
        query=query or None,
        team_a=team_a or None,
        team_b=team_b or None,
        fixture_id=fixture_id or None,
    )


@app.get("/api/history")
def history(team_a: str = "", team_b: str = ""):
    if not team_a or not team_b:
        return {"overall": history_analyzer.overall(), "matches": len(history_analyzer.matches)}
    return {
        "h2h": history_analyzer.h2h(team_a, team_b),
        "scoreline_frequency": history_analyzer.scoreline_frequency(team_a, team_b),
        "repeated_patterns": history_analyzer.repeated_patterns(team_a, team_b),
        "lambdas": history_analyzer.lambdas(team_a, team_b),
        "goal_averages": history_analyzer.goal_averages(team_a, team_b),
    }


class HistoryIn(BaseModel):
    csv: str


@app.post("/api/history")
def add_history(req: HistoryIn):
    count = history_analyzer.save_csv(req.csv)
    return {"ok": True, "total_matches": count}


@app.get("/api/context")
def context(team: str = ""):
    if not team:
        return {"error": "Parametrul team e obligatoriu."}
    return context_engine.get_team_context(team)


class ChatIn(BaseModel):
    messages: list
    lang: str = "ro"


@app.post("/api/chat")
def chat(req: ChatIn):
    lang = req.lang if req.lang in ("ro", "de", "en") else "ro"
    disabled = {
        "ro": "Chat-ul e dezactivat în config.",
        "de": "Der Chat ist in der Konfiguration deaktiviert.",
        "en": "Chat is disabled in the config.",
    }[lang]
    if not CONFIG.get("chat", {}).get("enabled", True):
        return {"reply": disabled, "tools_used": []}
    try:
        result = chat_service.chat(req.messages, lang=lang)
    except Exception as e:
        error = {
            "ro": f"Eroare internă la chat: {e}",
            "de": f"Interner Chat-Fehler: {e}",
            "en": f"Internal chat error: {e}",
        }[lang]
        return {"reply": error, "tools_used": [], "provider": "error"}
    try:
        last_user = ""
        for m in req.messages:
            if isinstance(m, dict) and m.get("role") == "user":
                last_user = str(m.get("content", ""))
        if last_user:
            storage.add_chat("user", last_user)
            storage.add_chat("assistant", str(result.get("reply", "")))
    except Exception:
        pass
    try:
        blob = (str(result.get("reply", "")) + " " + str(result.get("provider", ""))).lower()
        if result.get("provider") == "error" or "429" in blob or "rate limit" in blob or "rate-limit" in blob:
            note_ai_error(600)
        elif result.get("reply"):
            note_ai_ok()
    except Exception:
        pass
    return result


@app.get("/api/chat/history")
def chat_history(limit: int = 200):
    return {"messages": storage.list_chats(limit=limit)}


@app.delete("/api/chat/history")
def chat_clear():
    storage.clear_chats()
    return {"ok": True}


@app.get("/api/arbitrage")
def arbitrage():
    cache = storage.load_cache()
    results = []
    for group, events in cache.items():
        for arb in find_arbitrage(events):
            arb["sport"] = group
            results.append(arb)
    return results


@app.get("/api/bets")
def bets():
    all_bets = storage.list_bets()
    grouped = {}
    for b in all_bets:
        grouped.setdefault(b.get("sport_group") or "other", []).append(b)
    return {"bets": all_bets, "grouped": dict(sorted(grouped.items()))}


class BetIn(BaseModel):
    event: str
    outcome: str
    stake: float
    odds: float
    edge_pct: float = 0.0
    sport_group: str = ""


@app.post("/api/bets")
def add_bet(bet: BetIn):
    rec = {
        "event": bet.event,
        "outcome": bet.outcome,
        "stake": bet.stake,
        "odds": bet.odds,
        "edge_pct": bet.edge_pct,
        "sport_group": bet.sport_group or _guess_sport_group(bet.event),
        "status": "open",
    }
    storage.add_bet(rec)
    return {"ok": True, "sport_group": rec["sport_group"]}


def _guess_sport_group(event_text):
    """Deduce rubrica de sport din textul evenimentului cautat in cache."""
    text = (event_text or "").lower()
    for group, events in storage.load_cache().items():
        for ev in events if isinstance(events, list) else []:
            if not isinstance(ev, dict):
                continue
            pair = f"{ev.get('home_team', '')} vs {ev.get('away_team', '')}".lower()
            if pair and pair == text:
                return ev.get("sport_group") or group
    return ""


@app.post("/api/bets/{bet_id}/settle")
def settle_bet(bet_id: int, won: bool = True):
    result = storage.settle_bet(bet_id, won)
    if result is None:
        return JSONResponse({"error": "Bet not found or already settled."}, status_code=404)
    return result


@app.get("/api/stats")
def stats():
    bankroll = Bankroll()
    for b in storage.list_bets():
        bankroll.bets.append(b)
        if b["status"] == "open":
            bankroll.balance -= b["stake"]
        else:
            bankroll.balance = bankroll.initial + sum(
                x.get("profit", 0) for x in storage.list_bets() if x["status"] != "open"
            )
    return bankroll.summary()


microbist_router = build_router(
    storage=storage,
    context_engine=context_engine,
    football=football,
    fd=football_data,
    history_analyzer=history_analyzer,
    config=CONFIG,
    refresh_state=refresh_state,
    value_state=value_state,
    threshold=THRESHOLD,
    borderline_window_pct=CONFIG.get("context", {}).get("borderline_window_pct", 3.0),
    monthly_limit=MONTHLY_LIMIT,
    backend_dir=BACKEND_DIR,
    scan_value_bets=_scan_value_bets,
    ttl=shared_ttl,
    odds_api_key=API_KEY,
)
app.include_router(microbist_router)

betting_router = build_betting_router(
    storage=storage,
    fd=football_data,
    ttl=shared_ttl,
    config=CONFIG,
    football=football,
    odds_api_key=API_KEY,
    auto_settle_minutes=float(CONFIG.get("wallet", {}).get("auto_settle_minutes", 30)),
)
app.include_router(betting_router)

live_router = build_live_router(
    storage=storage,
    football=football,
    ttl=shared_ttl,
    config=CONFIG,
    min_interval_s=float(CONFIG.get("live", {}).get("min_interval_s", 60)),
    polls_per_day=int(CONFIG.get("live", {}).get("polls_per_day", 60)),
)
app.include_router(live_router)

app.mount("/assets", StaticFiles(directory=str(DASHBOARD_DIR)), name="assets")


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="127.0.0.1", port=8000)
