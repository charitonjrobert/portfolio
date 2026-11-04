# -*- coding: utf-8 -*-
"""Live alerts for watched matches / placed bets (goals, cards, status).

Source: API-Football `/fixtures?live=all` - **verified working on the free plan**
(1 request returns every live match in the world, with the event list per match).

Quota discipline (free plan = 100 requests/day, shared with other API-Football calls):
  * nothing is fetched when no watched bet/match is actually live or about to start;
  * hard minimum interval between polls (default 60s);
  * hard daily budget for live polls (default 60), persisted across restarts;
  * the first poll for a match only sets the baseline, so the client is never spammed
    with goals that happened before it started watching.
"""
import threading
import time
from datetime import datetime, timedelta, timezone

from fastapi import APIRouter
from pydantic import BaseModel

from settle import norm

MAX_KEY_EVENTS = 12


def build_router(*, storage, football, ttl, config, min_interval_s=60, polls_per_day=60, lookback_min=170, lookahead_min=20):
    router = APIRouter()
    lock = threading.Lock()
    state = {"last_poll": 0.0, "last_result": None}

    def _today():
        return datetime.now(timezone.utc).date().isoformat()

    def _budget():
        data = ttl.get("live|budget") or {}
        if data.get("day") != _today():
            data = {"day": _today(), "polls": 0}
        return data

    def _spend_poll():
        data = _budget()
        data["polls"] = int(data.get("polls", 0)) + 1
        ttl.set("live|budget", data)
        return data

    # -------------------------------------------------------------- watchlist
    class WatchIn(BaseModel):
        player: str = "demo"
        event_id: str = ""
        home: str = ""
        away: str = ""
        sport: str = "soccer"
        league: str = ""
        commence_time: str = ""

    @router.get("/api/watch")
    def watch_list(player: str = "demo"):
        rows = storage.list_watch(player or "demo")
        return {"player": player or "demo", "count": len(rows), "items": rows}

    @router.post("/api/watch")
    def watch_add(req: WatchIn):
        if not (req.home or req.event_id):
            return {"error": "Lipsește meciul."}
        watch_id = storage.add_watch({
            "player": req.player or "demo",
            "event_id": req.event_id,
            "home_team": req.home,
            "away_team": req.away,
            "sport": req.sport,
            "league": req.league,
            "commence_time": req.commence_time,
        })
        return {"ok": True, "id": watch_id, "count": len(storage.list_watch(req.player or "demo"))}

    @router.delete("/api/watch/{watch_id}")
    def watch_remove(watch_id: int):
        storage.remove_watch(watch_id)
        return {"ok": True}

    # ------------------------------------------------------------------- live
    def _candidates(player):
        """Watched matches + open bets that are live now or start very soon."""
        now = datetime.now(timezone.utc)
        window_start = now - timedelta(minutes=lookback_min)
        window_end = now + timedelta(minutes=lookahead_min)
        items = []
        seen = set()
        for w in storage.list_watch(player):
            dt = _dt(w.get("commence_time"))
            if dt is None or not (window_start <= dt <= window_end):
                continue
            key = (norm(w.get("home_team")), norm(w.get("away_team")))
            if key in seen:
                continue
            seen.add(key)
            items.append({
                "source": "watch", "watch_id": w.get("id"), "event_id": w.get("event_id"),
                "home": w.get("home_team"), "away": w.get("away_team"),
                "sport": w.get("sport") or "soccer", "league": w.get("league") or "",
                "commence_time": w.get("commence_time"),
            })
        for b in storage.list_open_bets():
            if (b.get("player") or "demo") != player:
                continue
            if (b.get("sport") or "") not in ("soccer", ""):
                continue
            dt = _dt(b.get("commence_time"))
            if dt is None or not (window_start <= dt <= window_end):
                continue
            key = (norm(b.get("home_team")), norm(b.get("away_team")))
            if key in seen:
                continue
            seen.add(key)
            items.append({
                "source": "bet", "bet_id": b.get("id"), "event_id": b.get("event_id"),
                "home": b.get("home_team"), "away": b.get("away_team"),
                "sport": b.get("sport") or "soccer", "league": "",
                "commence_time": b.get("commence_time"),
                "side": b.get("side"), "outcome": b.get("outcome"), "odds": b.get("odds"),
            })
        return items

    def _dt(value):
        try:
            return datetime.fromisoformat(str(value).replace("Z", "+00:00"))
        except (ValueError, TypeError):
            return None

    def _find_live(candidate, live_fixtures):
        nh, na = norm(candidate.get("home")), norm(candidate.get("away"))
        for fx in live_fixtures:
            teams = fx.get("teams") or {}
            ih = norm((teams.get("home") or {}).get("name"))
            ia = norm((teams.get("away") or {}).get("name"))
            if not ih or not ia:
                continue
            if (nh in ih or ih in nh) and (na in ia or ia in na):
                return fx, False
            if (nh in ia or ia in nh) and (na in ih or ih in na):
                return fx, True  # home/away swapped in the source
        return None, False

    def _event_key(fx_id, ev):
        t = ev.get("time") or {}
        return "|".join([
            str(fx_id),
            str(ev.get("type") or ""),
            str(ev.get("detail") or ""),
            str((ev.get("player") or {}).get("name") or ""),
            str(t.get("elapsed") or ""),
        ])

    @router.get("/api/live")
    def live(player: str = "demo", force: int = 0):
        player = player or "demo"
        cands = _candidates(player)
        if not cands:
            return {
                "active": False,
                "reason": "no_live_candidates",
                "candidates": 0,
                "watched": len(storage.list_watch(player)),
                "budget": _budget(),
                "polled": False,
            }
        soc = [c for c in cands if (c.get("sport") or "soccer") == "soccer"]
        if not soc:
            return {"active": False, "reason": "no_soccer_candidates", "candidates": len(cands), "polled": False}

        now = time.time()
        budget = _budget()
        if not force:
            if now - state["last_poll"] < min_interval_s:
                return {"active": True, "polled": False, "reason": "throttled",
                        "seconds_until_next": int(min_interval_s - (now - state["last_poll"])),
                        "candidates": len(soc), "budget": budget,
                        "fixtures": (state["last_result"] or {}).get("fixtures", []),
                        "events": []}
            if int(budget.get("polls", 0)) >= polls_per_day:
                return {"active": True, "polled": False, "reason": "daily_budget_reached",
                        "candidates": len(soc), "budget": budget,
                        "fixtures": (state["last_result"] or {}).get("fixtures", []), "events": []}

        with lock:
            if not force and time.time() - state["last_poll"] < min_interval_s:
                return {"active": True, "polled": False, "reason": "throttled", "candidates": len(soc),
                        "budget": _budget(), "fixtures": (state["last_result"] or {}).get("fixtures", []), "events": []}
            try:
                data, _remaining, errors = football.fixtures(live="all")
            except Exception as exc:
                return {"active": True, "polled": False, "error": str(exc), "candidates": len(soc), "budget": budget}
            state["last_poll"] = time.time()
            budget = _spend_poll()

        fixtures, events = [], []
        for cand in soc:
            fx, swapped = _find_live(cand, data or [])
            if not fx:
                fixtures.append({**cand, "found": False})
                continue
            fid = (fx.get("fixture") or {}).get("id")
            status = ((fx.get("fixture") or {}).get("status") or {})
            goals = fx.get("goals") or {}
            gh, ga = goals.get("home"), goals.get("away")
            if swapped:
                gh, ga = ga, gh
            seen_key = f"live|seen|{fid}"
            seen = ttl.get(seen_key)
            raw_events = (fx.get("events") or [])[:MAX_KEY_EVENTS]
            new_events = []
            if seen is None:
                keys = [_event_key(fid, e) for e in raw_events]
            else:
                keys = list(seen)
                for ev in raw_events:
                    k = _event_key(fid, ev)
                    if k in keys:
                        continue
                    keys.append(k)
                    team = ((ev.get("team") or {}).get("name")) or ""
                    etype = (ev.get("type") or "").lower()
                    if swapped and team:
                        team = cand.get("home") if norm(team) == norm(cand.get("away")) else cand.get("away")
                    new_events.append({
                        "kind": "goal" if etype == "goal" else ("card" if etype == "card" else etype or "event"),
                        "detail": ev.get("detail") or "",
                        "team": team,
                        "player": (ev.get("player") or {}).get("name") or "",
                        "minute": (ev.get("time") or {}).get("elapsed"),
                        "score": f"{gh}-{ga}",
                        "home": cand.get("home"),
                        "away": cand.get("away"),
                    })
            ttl.set(seen_key, keys[-60:])
            fixtures.append({
                **cand,
                "found": True,
                "fixture_id": fid,
                "score": {"home": gh, "away": ga},
                "minute": status.get("elapsed"),
                "status": status.get("short"),
                "status_long": status.get("long"),
                "league_live": ((fx.get("league") or {}).get("name")),
            })
            events.extend(new_events)

        state["last_result"] = {"fixtures": fixtures}
        return {
            "active": True,
            "polled": True,
            "candidates": len(soc),
            "fixtures": fixtures,
            "events": events,
            "budget": budget,
            "polled_at": datetime.now().isoformat(timespec="seconds"),
        }

    # ------------------------------------------------ live scores (all matches)
    @router.get("/api/livescores")
    def livescores(force: int = 0):
        """Scor live pentru TOATE meciurile din lume care rulează acum (1 cerere = toate).

        Cache 120s + buget zilnic propriu, ca sa nu strice bugetul alertelor.
        """
        now = time.time()
        cached = ttl.get("live|scores") or {}
        if cached and not force and now - float(cached.get("ts", 0)) < 120:
            return {"polled": False, "cached": True, "items": cached.get("items", []),
                    "age": int(now - float(cached.get("ts", 0)))}
        sb = ttl.get("live|scores|budget") or {}
        if sb.get("day") != _today():
            sb = {"day": _today(), "polls": 0}
        if not force and int(sb.get("polls", 0)) >= 40:
            return {"polled": False, "cached": True, "items": cached.get("items", []), "reason": "daily_budget"}
        try:
            data, _rem, _err = football.fixtures(live="all")
        except Exception as exc:
            return {"polled": False, "items": cached.get("items", []), "error": str(exc)}
        sb["polls"] = int(sb.get("polls", 0)) + 1
        ttl.set("live|scores|budget", sb)
        items = []
        for fx in data or []:
            teams = fx.get("teams") or {}
            goals = fx.get("goals") or {}
            st = (fx.get("fixture") or {}).get("status") or {}
            h = (teams.get("home") or {}).get("name")
            a = (teams.get("away") or {}).get("name")
            if not h or not a:
                continue
            items.append({
                "h": h, "a": a, "hs": goals.get("home"), "as": goals.get("away"),
                "min": st.get("elapsed"), "st": st.get("short"),
                "league": (fx.get("league") or {}).get("name"),
            })
        ttl.set("live|scores", {"ts": now, "items": items})
        return {"polled": True, "items": items, "count": len(items), "budget": sb}

    return router
