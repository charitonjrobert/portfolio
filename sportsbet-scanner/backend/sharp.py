# -*- coding: utf-8 -*-
"""Sharp market reference (Pinnacle / exchanges) + consensus fallback.

Why (decision Jay, 14 Oct 2026):
  * the "edge" we used to show compared our model against the BEST price out of
    ~25 bookmakers. That price is an outlier, so the edge was systematically
    optimistic ("lots of value bets" that were really just bookmaker margins).
  * the honest reference is the SHARP market: Pinnacle (low margin, high limits)
    and the exchanges (Betfair, Matchbook). There the price is set by a lot of
    money, so the margin-free probabilities are the closest thing we have to the
    "true" probability of an outcome.
  * when no sharp book covers the match we fall back to the CONSENSUS: the median
    of the margin-free probabilities of every book we have. Still far better
    than a single best price.

Everything here reads the already-downloaded local cache -> 0 API requests.
"""
MIN_PRICE = 1.02  # 1.00 / 1.01 are placeholder quotes, not real prices
SHARP_BOOKS = ("pinnacle", "betfair", "matchbook", "betdaq", "smarkets")
# A book whose prices are this far off is not a usable reference:
#   * < 0.5%  -> stale/incomplete (inverse sum below 1: missing outcome or an arb)
#   * > 12%   -> not a "sharp" price any more (Betfair exchange junk showed 149%)
MIN_MARGIN = 0.5
MAX_SHARP_MARGIN = 12.0
MAX_CONSENSUS_MARGIN = 25.0


def _key(name):
    return "".join(ch for ch in str(name or "").lower() if ch.isalnum())


def h2h_books(event, min_margin=MIN_MARGIN, max_margin=MAX_CONSENSUS_MARGIN):
    """{book title: {outcome name: price}} for the h2h market, sane books only."""
    books = {}
    for book in event.get("bookmakers") or []:
        if not isinstance(book, dict):
            continue
        prices = {}
        for market in book.get("markets") or []:
            if not isinstance(market, dict) or market.get("key") != "h2h":
                continue
            for out in market.get("outcomes") or []:
                if not isinstance(out, dict):
                    continue
                name, price = out.get("name"), out.get("price")
                if name and isinstance(price, (int, float)) and price >= MIN_PRICE:
                    prices[name] = float(price)
        if len(prices) < 2:
            continue
        _, margin = _fair(prices)
        if margin < min_margin or margin > max_margin:
            continue
        books[book.get("title") or "?"] = prices
    return books


def _fair(prices):
    """Margin-free probabilities of one book's prices + its margin in percent."""
    inv = {n: 1.0 / p for n, p in prices.items() if p > 1}
    total = sum(inv.values())
    if total <= 0:
        return {}, 0.0
    return {n: v / total for n, v in inv.items()}, (total - 1.0) * 100.0


def sharp_prices(event):
    """(title, prices) from the sharpest trustworthy book; (None, {}) if none."""
    books = h2h_books(event, max_margin=MAX_SHARP_MARGIN)
    for want in SHARP_BOOKS:
        for title, prices in books.items():
            if want in _key(title):
                return title, prices
    return None, {}


def consensus_probs(event, min_books=3):
    """Median margin-free probability per outcome across all sane books -> (probs, n)."""
    rows = []
    for prices in h2h_books(event).values():
        probs, _ = _fair(prices)
        if probs:
            rows.append(probs)
    # min_books=1 is used for the displayed match analysis: one sane book is
    # better than an empty "chances" card. Value bets keep the strict default (3).
    if len(rows) < max(1, int(min_books)):
        return {}, len(rows)
    names = None
    for row in rows:
        names = set(row) if names is None else (names & set(row))
    names = names or set()
    out = {}
    for name in names:
        vals = sorted(row[name] for row in rows)
        mid = len(vals) // 2
        out[name] = vals[mid] if len(vals) % 2 else (vals[mid - 1] + vals[mid]) / 2.0
    total = sum(out.values())
    if total <= 0:
        return {}, len(rows)
    return {n: v / total for n, v in out.items()}, len(rows)


def outcome_name(event, side):
    """Map home / draw / away to the outcome name used inside the odds payload."""
    home, away = event.get("home_team"), event.get("away_team")
    if side == "home":
        return home
    if side == "away":
        return away
    if side == "draw":
        for book in event.get("bookmakers") or []:
            for market in book.get("markets") or []:
                if market.get("key") != "h2h":
                    continue
                for out in market.get("outcomes") or []:
                    name = out.get("name")
                    if name and name not in (home, away):
                        return name
    return None


def _tokens(text):
    return {t for t in "".join(ch if ch.isalnum() else " " for ch in str(text or "").lower()).split() if len(t) > 1}


def _match_name(names, team):
    """Find the outcome name that belongs to `team` (exact -> prefix -> token overlap)."""
    if not team or not names:
        return None
    key = _key(team)
    for name in names:
        if _key(name) == key:
            return name
    for name in names:
        k2 = _key(name)
        if k2 and (k2 in key or key in k2) and min(len(k2), len(key)) >= 5:
            return name
    toks = _tokens(team)
    best, best_score = None, 0
    for name in names:
        score = len(toks & _tokens(name))
        if score > best_score:
            best, best_score = name, score
    return best if best_score > 0 else None


def sides(event, ref=None):
    """Map the market reference onto home / draw / away (robust to naming differences).

    Each side: {"name", "prob", "price" (actionable - sharp only), "fair_odds"}.
    """
    ref = ref if ref is not None else reference(event)
    probs = ref.get("probs") or {}
    out = {"kind": ref.get("kind"), "bookmaker": ref.get("bookmaker"),
           "margin_pct": ref.get("margin_pct"), "home": None, "draw": None, "away": None}
    if not probs:
        return out
    names = list(probs)
    used = set()
    hn = _match_name(names, event.get("home_team"))
    if hn:
        used.add(hn)
    an = _match_name([n for n in names if n not in used], event.get("away_team"))
    if an:
        used.add(an)
    rest = [n for n in names if n not in used]
    dn = rest[0] if len(rest) == 1 else None
    prices = ref.get("prices") or {}
    fair = ref.get("fair_odds") or {}
    for side, name in (("home", hn), ("away", an), ("draw", dn)):
        if not name:
            continue
        out[side] = {"name": name, "prob": probs[name], "price": prices.get(name),
                     "fair_odds": fair.get(name)}
    return out


def reference(event, min_consensus_books=3):
    """Best available estimate of the market's probabilities (sharp first).

    Returns:
      kind          'sharp' | 'consensus' | None
      bookmaker     the sharp book used (None for consensus)
      books         how many books fed the consensus
      probs         {outcome name: probability}  (margin free)
      prices        {outcome name: price}  -> only when kind == 'sharp' (actionable)
      fair_odds     {outcome name: fair decimal odds} (1 / probability)
      margin_pct    the sharp book's margin (0 for consensus: it is already removed)
    """
    title, prices = sharp_prices(event)
    if prices:
        probs, margin = _fair(prices)
        if probs:
            return {
                "kind": "sharp",
                "bookmaker": title,
                "books": 1,
                "probs": probs,
                "prices": prices,
                "fair_odds": {n: round(1.0 / p, 3) for n, p in probs.items() if p > 0},
                "margin_pct": round(margin, 2),
            }
    probs, n = consensus_probs(event, min_books=min_consensus_books)
    if probs:
        return {
            "kind": "consensus",
            "bookmaker": None,
            "books": n,
            "probs": probs,
            "prices": {},  # no single actionable price: it is a median, not a book
            "fair_odds": {k: round(1.0 / v, 3) for k, v in probs.items() if v > 0},
            "margin_pct": 0.0,
        }
    return {"kind": None, "bookmaker": None, "books": 0, "probs": {}, "prices": {},
            "fair_odds": {}, "margin_pct": 0.0}
