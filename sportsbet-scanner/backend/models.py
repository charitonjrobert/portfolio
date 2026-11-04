from probabilities import poisson_1x2
from sharp import reference, sides, h2h_books

DEFAULT_LAMBDAS = {
    "soccer": 1.4,
    "basketball": 0.0,
    "tennis": 0.0,
    "darts": 0.0,
}


def market_sides(event):
    """Home/draw/away margin-free odds from the sharp (or consensus) market.

    Fix (14 Oct 2026): the old prior used the LOWEST h2h price per outcome across
    books - a single 1.01 placeholder (Betfair lay quotes) flipped the favourite
    (Real Madrid 85%) into a fake 51% underdog. We now use the market reference,
    which drops placeholders and takes the sharp book / median consensus.
    """
    sd = sides(event, reference(event, min_consensus_books=1))
    home = sd.get("home") or {}
    away = sd.get("away") or {}
    if home.get("prob") is None or away.get("prob") is None:
        return None
    return {
        "home": home["prob"],
        "draw": (sd.get("draw") or {}).get("prob"),
        "away": away["prob"],
        "kind": sd.get("kind"),
        "bookmaker": sd.get("bookmaker"),
    }


def team_strength_from_odds(home_odds, away_odds, draw_odds=None):
    """Legacy helper kept for callers: margin-free probabilities from raw prices."""
    raw = [1.0 / home_odds] if home_odds and home_odds > 1 else []
    if draw_odds and draw_odds > 1:
        raw.append(1.0 / draw_odds)
    if away_odds and away_odds > 1:
        raw.append(1.0 / away_odds)
    total = sum(raw)
    if total <= 0:
        return (0.0, 0.0) if not draw_odds else (0.0, 0.0, 0.0)
    clean = [p / total for p in raw]
    if draw_odds:
        return clean[0], clean[1], clean[2]
    return clean[0], clean[1]


def fit_lambdas(ph, pd, pa):
    """Market-implied expected goals (display only).

    We no longer derive the model from an arbitrary Poisson shape: the Poisson is
    used ONLY when real H2H history exists. Here we simply fit a Poisson whose
    draw share matches the market, so the UI can still show "expected goals".
    """
    if not pd or pd <= 0 or not ph or not pa:
        total = 2.6
        ratio = (ph or 0.5) / max(1e-6, (ph or 0.5) + (pa or 0.5))
        return round(total * ratio, 2), round(total * (1 - ratio), 2)
    share = min(0.85, max(0.15, 0.5 + (ph - pa)))
    best, best_err = (1.4, 1.4), 1e9
    t = 0.4
    while t <= 4.81:
        lam_h, lam_a = t * share, t * (1.0 - share)
        if lam_h > 0.05 and lam_a > 0.05:
            h, d, a = poisson_1x2(lam_h, lam_a)
            tot = h + d + a
            if tot > 0:
                err = (d / tot - pd) ** 2
                if err < best_err:
                    best_err, best = err, (lam_h, lam_a)
        t += 0.1
    return round(best[0], 2), round(best[1], 2)


def predict_1x2(event, sport_group, average_goals=None, lambdas=None, context=None, context_engine=None,
                interactive=False):
    """Probabilities for 1X2 / two-way markets.

    Architecture (fixed 14 Oct 2026, decision Jay):
      * the prior is the SHARP market (Pinnacle/exchanges) or the median consensus,
        margin-free - not a single bookmaker's worst price;
      * the model only moves away from that prior when it has real information:
        - news/injuries (context engine, multiplicative tilt), and
        - H2H history lambdas (blended in), which we rarely have.
      Before, a fixed Poisson shape was always applied, which invented a +4..+8%
      "edge" on every favourite out of nothing.

    `interactive=True` (a user asked for THIS match) gives the news engine its own
    lookup budget, so a match analysis is never starved by the background scan.
    """
    ms = market_sides(event)
    if not ms:
        return None
    ph, pd, pa = ms["home"], ms["draw"], ms["away"]
    ctx = None
    if context_engine:
        ctx = context_engine.get_event_context(event.get("home_team"), event.get("away_team"),
                                               interactive=interactive)
    if sport_group == "soccer" and pd is not None:
        base = [ph, pd, pa]
        news_shift = {"home": 0.0, "draw": 0.0, "away": 0.0}
        if context_engine:
            base = context_engine.apply_adjustment(base, ctx)
            # how much the news alone moved each probability (percentage points)
            news_shift = {
                "home": round((base[0] - ph) * 100, 2),
                "draw": round((base[1] - pd) * 100, 2),
                "away": round((base[2] - pa) * 100, 2),
            }
        ph, pd, pa = base
        lam_h, lam_a = fit_lambdas(ph, pd, pa)
        kind = "market"
        if lambdas:
            hist = poisson_1x2(lambdas.get("home", 1.4), lambdas.get("away", 1.4))
            tot = sum(hist)
            if tot > 0:
                hist = [x / tot for x in hist]
                blended = [(hist[i] + (ph, pd, pa)[i]) / 2 for i in range(3)]
                tot2 = sum(blended)
                ph, pd, pa = [x / tot2 for x in blended]
            kind = "poisson"
        return {
            "home": ph,
            "draw": pd,
            "away": pa,
            "type": kind,
            "market_kind": ms.get("kind"),
            "context": ctx if context_engine else None,
            "news_shift": news_shift,
            "news_score": {
                "home": ((ctx or {}).get("home") or {}).get("score", 0.0),
                "away": ((ctx or {}).get("away") or {}).get("score", 0.0),
            } if context_engine else {"home": 0.0, "away": 0.0},
            "lambdas": {"home": lam_h, "away": lam_a},
        }
    # Two-way sports (basketball, tennis, boxing, MMA) - but the market reference may
    # still carry a THIRD outcome (a real draw, e.g. boxing). Renormalising over
    # home/away alone then invented a fake edge equal to the draw's probability mass
    # (Anthony Joshua - Tyson Fury showed +2.43% out of thin air, with zero news).
    # Keep the third outcome, and let the news tilt these markets too.
    news_shift = {"home": 0.0, "draw": 0.0, "away": 0.0}
    if context_engine:
        if pd is None:
            pre = [ph, pa]
            adj = context_engine.apply_adjustment(pre, ctx)
            tot = sum(adj)
            if tot > 0:
                news_shift = {"home": round((adj[0] / tot - pre[0]) * 100, 2), "draw": 0.0,
                              "away": round((adj[1] / tot - pre[1]) * 100, 2)}
            ph, pa = adj
        else:
            adj = context_engine.apply_adjustment([ph, pd, pa], ctx)
            news_shift = {
                "home": round((adj[0] - ph) * 100, 2),
                "draw": round((adj[1] - pd) * 100, 2),
                "away": round((adj[2] - pa) * 100, 2),
            }
            ph, pd, pa = adj
    if pd is None:
        total = ph + pa
        if total <= 0:
            return None
        ph, pa = ph / total, pa / total
    return {
        "home": ph,
        "draw": pd,
        "away": pa,
        "type": "market",
        "market_kind": ms.get("kind"),
        "context": ctx if context_engine else None,
        "news_shift": news_shift,
        "news_score": {
            "home": ((ctx or {}).get("home") or {}).get("score", 0.0),
            "away": ((ctx or {}).get("away") or {}).get("score", 0.0),
        } if context_engine else {"home": 0.0, "away": 0.0},
    }


def predict_totals(event, sport_group):
    totals = extract_totals(event)
    if not totals:
        return None
    if sport_group == "soccer":
        lam = DEFAULT_LAMBDAS["soccer"] * 2
        over = 1.0
        for outcome in totals:
            point = outcome.get("point")
            name = outcome.get("name", "").lower()
            if point is None:
                continue
            if "over" in name:
                from probabilities import poisson_pmf

                over = 1.0 - sum(poisson_pmf(k, lam) for k in range(int(point) + 1))
                return {"point": point, "over": over, "under": 1.0 - over, "type": "poisson"}
    return None


def extract_h2h(event):
    """Median h2h price per outcome (placeholders < 1.02 dropped).

    Kept for compatibility; `predict_1x2` now uses the sharp market reference.
    """
    books = h2h_books(event)
    if len(books) < 1:
        return None
    names = None
    for prices in books.values():
        names = set(prices) if names is None else (names & set(prices))
    names = names or set()
    if len(names) < 2:
        return None
    out = {}
    for name in names:
        vals = sorted(prices[name] for prices in books.values() if name in prices)
        mid = len(vals) // 2
        out[name] = {"price": vals[mid] if len(vals) % 2 else (vals[mid - 1] + vals[mid]) / 2.0,
                     "bookmaker": "median"}
    return {"home": out.get(event.get("home_team")), "away": out.get(event.get("away_team")),
            "draw": out.get("Draw")}


def extract_totals(event):
    best = {}
    for book in event.get("bookmakers", []):
        for market in book.get("markets", []):
            if market.get("key") != "totals":
                continue
            for outcome in market.get("outcomes", []):
                point = outcome.get("point")
                if point is None:
                    continue
                bucket = best.setdefault(point, {})
                name = outcome["name"]
                if name not in bucket or outcome["price"] < bucket[name]["price"]:
                    bucket[name] = {"price": outcome["price"], "bookmaker": book.get("title")}
    return best