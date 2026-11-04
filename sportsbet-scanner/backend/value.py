from itertools import combinations
from probabilities import implied_probability, remove_margin
from models import predict_1x2
from sharp import reference, sides


def _confidence(edge_pct, context, side, sport_group):
    score = 0
    # real edges (measured against the sharp market) are much smaller than the old
    # "vs the best price" ones, so the steps are tighter on purpose.
    if edge_pct >= 3.0:
        score += 2
    elif edge_pct >= 1.5:
        score += 1
    if context:
        home_score = context.get("home", {}).get("score", 0.0)
        away_score = context.get("away", {}).get("score", 0.0)
        if side == "home":
            if home_score > 0.1:
                score += 1
            if away_score < -0.1:
                score += 1
        elif side == "away":
            if away_score > 0.1:
                score += 1
            if home_score < -0.1:
                score += 1
        elif side == "draw":
            if abs(home_score) < 0.1 and abs(away_score) < 0.1:
                score += 1
    if sport_group in ("soccer", "basketball"):
        score += 1
    return min(score, 5)


def find_value_bets(events, sport_group, threshold_pct, context_engine=None, borderline_window_pct=3.0,
                    history_analyzer=None, interactive=False):
    """Value bets measured against the SHARP market (Pinnacle/exchanges), not the best price.

    Decision Jay, 14 Oct 2026: comparing against the best of ~25 bookmakers made the
    edge an outlier -> systematically optimistic. `edge_pct` is now the honest edge
    (model probability vs the sharp margin-free probability); `edge_best_pct` keeps
    the old figure for reference.

    The model equals the market unless it has extra information: news/injuries (a
    bounded tilt, `news_weight`) or H2H history. Without them the edge is exactly 0 -
    that is intentional, and `news_shift_pct` tells the UI which side the news moved.
    """
    results = []
    use_ctx = bool(context_engine and context_engine.config.get("enabled"))
    for event in events:
        pred = predict_1x2(event, sport_group, interactive=interactive)
        if not pred:
            continue
        ref = reference(event)
        sd = sides(event, ref)
        if not ref.get("probs"):
            continue  # no usable market reference -> cannot judge an edge honestly
        lambdas = None
        history_used = False
        if sport_group == "soccer" and history_analyzer:
            lambdas = history_analyzer.lambdas(event.get("home_team", ""), event.get("away_team", ""))
        if lambdas:
            pred = predict_1x2(event, sport_group, lambdas=lambdas, interactive=interactive) or pred
            history_used = True
        # The context-aware prediction must REPLACE the plain one *before* the edge
        # filter. Bug fixed 14 Oct 2026: the filter used to run on the no-news edge
        # (exactly 0, because the prior *is* the sharp market), so every side was
        # thrown out before the news tilt was ever applied -> news never changed a bet.
        context = None
        news_shift = None
        news_scores = {}
        if use_ctx:
            pred_ctx = predict_1x2(event, sport_group, context_engine=context_engine,
                                   lambdas=lambdas, interactive=interactive)
            if pred_ctx:
                context = pred_ctx.get("context")
                news_shift = pred_ctx.get("news_shift")
                news_scores = pred_ctx.get("news_score") or {}
                pred = pred_ctx
        for side, model_prob in (("home", pred["home"]), ("away", pred["away"]), ("draw", pred.get("draw"))):
            if not model_prob:
                continue
            entry = sd.get(side) or {}
            name = entry.get("name")
            market_prob = entry.get("prob")
            if name is None or market_prob is None:
                continue
            book = best_book_for_side(event, side)
            if not book:
                continue
            book_prob = implied_probability(book["price"])
            edge_pct = (model_prob - market_prob) * 100
            if edge_pct < threshold_pct - borderline_window_pct:
                continue
            if edge_pct < threshold_pct:
                continue
            results.append(
                {
                    "sport": sport_group,
                    "event_id": event.get("id"),
                    "home_team": event.get("home_team"),
                    "away_team": event.get("away_team"),
                    "commence_time": event.get("commence_time"),
                    "side": side,
                    "outcome": name,
                    "model_prob": round(model_prob, 4),
                    # --- honest market reference (sharp / consensus) ---
                    "market_prob": round(market_prob, 4),
                    "market_kind": ref.get("kind"),
                    "market_source": ref.get("bookmaker") or "",
                    "market_books": ref.get("books"),
                    "market_margin_pct": ref.get("margin_pct"),
                    "sharp_odds": entry.get("price"),
                    "fair_odds": entry.get("fair_odds"),
                    # --- the price we would actually take (best available) ---
                    "book_prob": round(book_prob, 4),
                    "odds": book["price"],
                    "bookmaker": book["bookmaker"],
                    "edge_pct": round(edge_pct, 2),
                    "edge_best_pct": round((model_prob - book_prob) * 100, 2),
                    "confidence": _confidence(edge_pct, context, side, sport_group),
                    "history_used": history_used,
                    # --- where the edge comes from: the news tilt (percentage points) ---
                    "news_shift_pct": round((news_shift or {}).get(side, 0.0), 2) if news_shift else 0.0,
                    "news_scores": news_scores or {},
                    "context": {
                        "home": context.get("home") if context else None,
                        "away": context.get("away") if context else None,
                    }
                    if context
                    else None,
                }
            )
    results.sort(key=lambda r: (r["confidence"], r["edge_pct"]), reverse=True)
    return results


def best_book_for_side(event, side):
    target = event.get("home_team") if side == "home" else event.get("away_team")
    if side == "draw":
        target = "Draw"
    best = None
    for book in event.get("bookmakers", []):
        for market in book.get("markets", []):
            if market.get("key") != "h2h":
                continue
            for outcome in market.get("outcomes", []):
                if outcome["name"] != target:
                    continue
                if best is None or outcome["price"] > best["price"]:
                    best = {"price": outcome["price"], "bookmaker": book.get("title")}
    return best


def find_arbitrage(events):
    results = []
    for event in events:
        sides = {}
        for book in event.get("bookmakers", []):
            for market in book.get("markets", []):
                if market.get("key") != "h2h":
                    continue
                for outcome in market.get("outcomes", []):
                    name = outcome["name"]
                    if name not in sides or outcome["price"] > sides[name]["price"]:
                        sides[name] = {"price": outcome["price"], "bookmaker": book.get("title")}
        if len(sides) < 2:
            continue
        for r in range(2, min(len(sides), 3) + 1):
            for combo in combinations(sides.items(), r):
                total = sum(1.0 / v["price"] for _, v in combo)
                if total < 1.0:
                    stake_fractions = [1.0 / v["price"] for _, v in combo]
                    results.append(
                        {
                            "event_id": event.get("id"),
                            "home_team": event.get("home_team"),
                            "away_team": event.get("away_team"),
                            "legs": [
                                {
                                    "outcome": name,
                                    "odds": v["price"],
                                    "bookmaker": v["bookmaker"],
                                    "stake_frac": round(frac / total, 4),
                                }
                                for (name, v), frac in zip(combo, stake_fractions)
                            ],
                            "guaranteed_return_pct": round((1.0 / total - 1.0) * 100, 2),
                        }
                    )
    results.sort(key=lambda r: r["guaranteed_return_pct"], reverse=True)
    return results