# -*- coding: utf-8 -*-
"""Simulation wallet: demo money, placing bets, automatic settlement, performance.

Deliberately simulation only (decision Jay, 13 Oct 2026):
  * every new player starts with 100 demo units;
  * results are REAL (football-data.org + the-odds-api scores), the money is not;
  * nothing here can move real money - there is no payment integration by design
    (real-money betting would require an ONJN licence, KYC and a payment provider).
"""
import threading
import time
from datetime import datetime, timezone
from typing import Optional

from fastapi import APIRouter
from pydantic import BaseModel

from settle import GROUP_TO_KEY, norm, settle_open_bets
import sharp
import report as report_mod

MIN_STAKE = 0.5
MAX_STAKE_SHARE = 1.0  # never allow betting more than the wallet holds


def _msg(lang, ro, de, en):
    return {"ro": ro, "de": de, "en": en}.get(lang or "ro", ro)
# how far before kick-off we start trying to freeze the sharp "closing" line
CLOSING_LOOKAHEAD_MIN = 90
CLOSING_GRACE_MIN = 240  # ...and how long after kick-off we still accept the cached line


def _parse_dt(value):
    try:
        return datetime.fromisoformat(str(value).replace("Z", "+00:00"))
    except (ValueError, TypeError):
        return None


def _clv_stats(bets):
    """Average CLV and share of positive CLV across settled bets that have it."""
    vals = [float(b.get("clv_pct")) for b in bets if b.get("clv_pct") is not None]
    if not vals:
        return {"clv_avg_pct": None, "clv_positive_pct": None, "clv_sample": 0}
    return {
        "clv_avg_pct": round(sum(vals) / len(vals), 2),
        "clv_positive_pct": round(sum(1 for v in vals if v > 0) / len(vals) * 100, 1),
        "clv_sample": len(vals),
    }


def build_router(*, storage, fd, ttl, config, football=None, odds_api_key="", auto_settle_minutes=30):
    router = APIRouter()
    lock = threading.Lock()
    state = {"last_settle": 0.0, "last_result": None}

    def player_of(name):
        return storage.ensure_player((name or "demo").strip() or "demo")

    def find_event(event_id="", home="", away=""):
        cache = storage.load_cache()
        nh, na = norm(home), norm(away)
        for group, events in cache.items():
            if not isinstance(events, list):
                continue
            for ev in events:
                if not isinstance(ev, dict):
                    continue
                if event_id and str(ev.get("id")) == str(event_id):
                    return ev, group
                eh, ea = norm(ev.get("home_team")), norm(ev.get("away_team"))
                if nh and na and ((nh in eh or eh in nh) and (na in ea or ea in na)):
                    return ev, group
        return None, None

    def maybe_auto_settle(force=False):
        """Settle at most once per `auto_settle_minutes` so opening the wallet is cheap."""
        now = time.time()
        if not force and now - state["last_settle"] < auto_settle_minutes * 60:
            return None
        if not storage.list_open_bets():
            state["last_settle"] = now
            return {"settled_count": 0, "note": "no open bets"}
        with lock:
            if not force and time.time() - state["last_settle"] < auto_settle_minutes * 60:
                return None
            capture_closing()
            result = settle_open_bets(storage, odds_api_key, fd, ttl=ttl)
            state["last_settle"] = time.time()
            state["last_result"] = result
            return result

    def capture_closing():
        """Freeze the sharp price just before kick-off -> the CLV baseline.

        Runs on the local cache only (0 API calls) and only for open bets that
        don't have a closing line yet. Captured while the match is at most
        CLOSING_LOOKAHEAD_MIN away from kick-off; up to CLOSING_GRACE_MIN after it
        started it is stored as 'approx' (the cache still holds the last pre-match
        line when no refresh happened in between).
        """
        now = datetime.now(timezone.utc)
        captured = 0
        for bet in storage.list_open_bets():
            if bet.get("closing_odds"):
                continue
            ct = _parse_dt(bet.get("commence_time"))
            if not ct:
                continue
            minutes = (ct - now).total_seconds() / 60.0
            if minutes > CLOSING_LOOKAHEAD_MIN or minutes < -CLOSING_GRACE_MIN:
                continue
            event, _group = find_event(bet.get("event_id"), bet.get("home_team"), bet.get("away_team"))
            if not event:
                continue
            ref = sharp.reference(event)
            entry = (sharp.sides(event, ref).get(bet.get("side") or "") or {})
            price, prob = entry.get("price"), entry.get("prob")
            if not price and not prob:
                continue
            storage.set_closing(bet.get("id"), price, prob, "pre" if minutes >= 0 else "approx")
            captured += 1
        return captured

    # ------------------------------------------------------------------ wallet
    @router.get("/api/wallet")
    def wallet(player: str = "demo", settle: int = 1):
        if settle:
            capture_closing()  # local only: freeze the sharp price before kick-off
        auto = maybe_auto_settle() if settle else None
        p = player_of(player)
        bets = storage.list_wallet_bets(p["name"])
        settled = [b for b in bets if b.get("status") in ("won", "lost")]
        staked = sum(float(b.get("stake") or 0) for b in settled)
        profit = sum(float(b.get("profit") or 0) for b in settled)
        open_bets = [b for b in bets if b.get("status") == "open"]
        clv = _clv_stats(settled)
        return {
            "player": p["name"],
            "balance": p["balance"],
            "initial": p["initial"],
            "open_count": len(open_bets),
            "settled_count": len(settled),
            "won": len([b for b in settled if b.get("status") == "won"]),
            "staked": round(staked, 2),
            "profit": round(profit, 2),
            "roi_pct": round(profit / staked * 100, 2) if staked else 0.0,
            "edge_estimate_avg": (
                round(sum(float(b.get("edge_pct") or 0) for b in settled) / len(settled), 2) if settled else 0.0
            ),
            **clv,
            "pending_closing": len([b for b in open_bets if not b.get("closing_odds")]),
            "simulation": True,
            "currency": "demo",
            "auto_settle": auto,
        }

    @router.get("/api/wallet/bets")
    def bets(player: str = "demo", limit: int = 100, settle: int = 1):
        if settle:
            maybe_auto_settle()
        capture_closing()
        p = player_of(player)
        rows = storage.list_wallet_bets(p["name"], limit=limit)
        return {"player": p["name"], "count": len(rows), "bets": rows}

    @router.get("/api/wallet/bet/{bet_id}/report")
    def bet_report(bet_id: int, lang: str = "ro"):
        """What actually happened in the match + why the bet won/lost (on demand).

        Football: at most 2 API-Football requests ONCE per match, then cached on
        disk forever. Everything else is computed locally (free).
        """
        bet = storage.get_bet(bet_id)
        if not bet:
            return {"error": _msg(lang, "Pariul nu există.", "Diese Wette existiert nicht.", "This bet does not exist.")}
        try:
            return report_mod.build_report(storage, football, ttl, bet)
        except Exception as exc:  # never 500 on a report
            return {"ok": False, "error": str(exc), "bet": {"id": bet_id}}

    class BetIn(BaseModel):
        player: str = "demo"
        event_id: str = ""
        home: str = ""
        away: str = ""
        side: str
        odds: float
        stake: float
        edge_pct: float = 0.0
        bookmaker: str = ""
        model_prob: Optional[float] = None
        lang: str = "ro"

    @router.post("/api/wallet/bet")
    def place_bet(req: BetIn):
        p = player_of(req.player)
        side = (req.side or "").strip().lower()
        if side not in ("home", "draw", "away"):
            return {"error": _msg(req.lang, "Alege un rezultat (1, X sau 2).", "Wähle ein Ergebnis (1, X oder 2).", "Choose an outcome (1, X or 2).")}
        try:
            stake = round(float(req.stake), 2)
            odds = float(req.odds)
        except (TypeError, ValueError):
            return {"error": _msg(req.lang, "Miza sau cota nu sunt valide.", "Einsatz oder Quote sind ungültig.", "Stake or odds are invalid.")}
        if stake < MIN_STAKE:
            return {"error": _msg(req.lang, f"Miza minimă e {MIN_STAKE} (demo).", f"Der Mindesteinsatz ist {MIN_STAKE} (Demo).", f"The minimum stake is {MIN_STAKE} (demo).")}
        if odds < 1.01:
            return {"error": _msg(req.lang, "Cotă invalidă.", "Ungültige Quote.", "Invalid odds.")}
        if stake > p["balance"]:
            return {"error": _msg(req.lang,
                                  f"Nu ai destui bani demo. Sold: {p['balance']}. Miza cerută: {stake}.",
                                  f"Nicht genug Demo-Guthaben. Guthaben: {p['balance']}. Einsatz: {stake}.",
                                  f"Not enough demo balance. Balance: {p['balance']}. Stake: {stake}.")}

        event, group = find_event(req.event_id, req.home, req.away)
        if not event:
            return {"error": _msg(req.lang,
                                  "Nu găsesc meciul în cotele curente. Dă refresh la cote și încearcă din nou.",
                                  "Das Spiel ist nicht in den aktuellen Quoten. Aktualisiere die Quoten und versuche es erneut.",
                                  "The match is not in the current odds. Refresh the odds and try again.")}
        commence = event.get("commence_time")
        started = False
        try:
            dt = datetime.fromisoformat(str(commence).replace("Z", "+00:00"))
            started = dt < datetime.now(timezone.utc)
        except (ValueError, TypeError):
            pass
        if started:
            return {"error": _msg(req.lang,
                                  "Meciul a început deja — nu se mai poate paria pe el (simulare corectă).",
                                  "Das Spiel hat bereits begonnen — darauf kann nicht mehr gewettet werden (korrekte Simulation).",
                                  "The match has already started — betting is closed (correct simulation).")}

        home_team = event.get("home_team") or req.home
        away_team = event.get("away_team") or req.away
        label = home_team if side == "home" else ("Egal" if side == "draw" else away_team)
        # sharp reference at the moment of the bet -> the CLV baseline (local cache only)
        try:
            _ref = sharp.reference(event)
            _entry = sharp.sides(event, _ref).get(side) or {}
            sharp_odds = _entry.get("price")
            sharp_prob = _entry.get("prob")
        except Exception:
            sharp_odds, sharp_prob = None, None
        new_balance = storage.add_balance(p["name"], -stake)
        bet_id = storage.add_wallet_bet({
            "event": f"{home_team} vs {away_team}",
            "outcome": label,
            "side": side,
            "market": "h2h",
            "stake": stake,
            "odds": odds,
            "edge_pct": req.edge_pct,
            "model_prob": req.model_prob,
            "bookmaker": req.bookmaker,
            "status": "open",
            "profit": 0,
            "sport_group": group or event.get("sport_group") or "",
            "sport": group or event.get("sport_group") or "",
            "sport_key": event.get("sport_key") or GROUP_TO_KEY.get(group or "", ""),
            "player": p["name"],
            "event_id": event.get("id") or req.event_id,
            "home_team": home_team,
            "away_team": away_team,
            "commence_time": commence,
            "sharp_odds": sharp_odds,
            "sharp_prob": sharp_prob,
        })
        return {
            "ok": True,
            "bet_id": bet_id,
            "balance": new_balance,
            "message": _msg(req.lang,
                            f"Pariu demo plasat: {label} @ {odds} cu {stake} (bani demo).",
                            f"Demo-Wette platziert: {label} @ {odds} mit Einsatz {stake} (Demo-Guthaben).",
                            f"Demo bet placed: {label} @ {odds} with stake {stake} (demo money)."),
            "potential_return": round(stake * odds, 2),
            "simulation": True,
        }

    @router.delete("/api/wallet/bet/{bet_id}")
    def cancel_bet(bet_id: int, lang: str = "ro"):
        bet = storage.delete_bet(bet_id)
        if not bet:
            return {"error": _msg(lang, "Pariul nu există.", "Diese Wette existiert nicht.", "This bet does not exist.")}
        p = player_of(bet.get("player") or "demo")
        return {"ok": True, "cancelled": bet.get("id"), "balance": p["balance"],
                "note": _msg(lang,
                             "Pariu anulat; miza demo a fost returnată." if bet.get("status") == "open" else "Pariu deja încheiat.",
                             "Wette storniert; der Demo-Einsatz wurde zurückerstattet." if bet.get("status") == "open" else "Wette bereits abgeschlossen.",
                             "Bet cancelled; the demo stake was returned." if bet.get("status") == "open" else "Bet already settled.")}

    @router.post("/api/wallet/reset")
    def reset(player: str = "demo", clear_history: int = 1, lang: str = "ro"):
        p = player_of(player)
        removed = 0
        if clear_history:
            for bet in storage.list_wallet_bets(p["name"], limit=1000):
                storage.delete_bet(bet.get("id"))
                removed += 1
        balance = storage.reset_player(p["name"])
        return {"ok": True, "player": p["name"], "balance": balance, "removed_bets": removed,
                "note": _msg(lang, f"Sold demo resetat la {balance}.", f"Demo-Guthaben auf {balance} zurückgesetzt.", f"Demo balance reset to {balance}.")}

    # -------------------------------------------------------------- settlement
    @router.post("/api/wallet/settle")
    def settle_now():
        result = maybe_auto_settle(force=True)
        return result or {"settled_count": 0}

    # ------------------------------------------------------------- performance
    @router.get("/api/wallet/performance")
    def performance(player: str = "demo"):
        capture_closing()
        p = player_of(player)
        bets = storage.list_wallet_bets(p["name"], limit=1000)
        settled = [b for b in bets if b.get("status") in ("won", "lost")]
        staked = sum(float(b.get("stake") or 0) for b in settled)
        profit = sum(float(b.get("profit") or 0) for b in settled)
        won = [b for b in settled if b.get("status") == "won"]
        per_sport = {}
        for b in settled:
            key = b.get("sport") or "other"
            row = per_sport.setdefault(key, {"bets": 0, "won": 0, "staked": 0.0, "profit": 0.0})
            row["bets"] += 1
            row["won"] += 1 if b.get("status") == "won" else 0
            row["staked"] += float(b.get("stake") or 0)
            row["profit"] += float(b.get("profit") or 0)
        for row in per_sport.values():
            row["staked"] = round(row["staked"], 2)
            row["profit"] = round(row["profit"], 2)
            row["roi_pct"] = round(row["profit"] / row["staked"] * 100, 2) if row["staked"] else 0.0
        est_edge = sum(float(b.get("edge_pct") or 0) for b in settled) / len(settled) if settled else 0.0
        # CLV: the honest "did we beat the closing market price" measure, overall and per sport.
        per_sport_clv = {}
        for b in settled:
            if b.get("clv_pct") is None:
                continue
            key = b.get("sport") or "other"
            row = per_sport_clv.setdefault(key, {"bets": 0, "sum": 0.0, "positive": 0})
            row["bets"] += 1
            row["sum"] += float(b.get("clv_pct") or 0)
            row["positive"] += 1 if float(b.get("clv_pct") or 0) > 0 else 0
        for row in per_sport_clv.values():
            row["clv_avg_pct"] = round(row["sum"] / row["bets"], 2) if row["bets"] else 0.0
            row["clv_positive_pct"] = round(row["positive"] / row["bets"] * 100, 1) if row["bets"] else 0.0
            del row["sum"]
        clv = _clv_stats(settled)
        return {
            "player": p["name"],
            "balance": p["balance"],
            "initial": p["initial"],
            "bets_total": len(bets),
            "settled": len(settled),
            "open": len(bets) - len(settled),
            "won": len(won),
            "win_rate_pct": round(len(won) / len(settled) * 100, 1) if settled else 0.0,
            "staked": round(staked, 2),
            "profit": round(profit, 2),
            "roi_pct": round(profit / staked * 100, 2) if staked else 0.0,
            "edge_estimated_avg_pct": round(est_edge, 2),
            "edge_realized_avg_pct": round(profit / staked * 100, 2) if staked else 0.0,
            **clv,
            "per_sport_clv": per_sport_clv,
            "per_sport": per_sport,
            "recent": settled[:10],
            "simulation": True,
        }

    return router
