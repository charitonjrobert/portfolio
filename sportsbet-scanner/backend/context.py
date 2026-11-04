import json
import os
import re
import threading
import time
from concurrent.futures import ThreadPoolExecutor
import xml.etree.ElementTree as ET
from html import unescape
from urllib.parse import quote

import requests

NEWS_KEYWORDS = {
    "negative": {
        "injured": 1.0,
        "injury": 0.8,
        "ruled out": 1.0,
        "out for": 0.9,
        "suspended": 1.0,
        "suspension": 0.9,
        "ban": 0.7,
        "setback": 0.8,
        "misses": 0.8,
        "absent": 0.7,
        "doubtful": 0.6,
        "knock": 0.4,
        "surgery": 0.9,
        "concussion": 0.9,
        "strain": 0.6,
        "red card": 0.8,
        "out": 0.3,
        "feud": 0.6,
        "unrest": 0.6,
        "fallout": 0.6,
        "row": 0.4,
        "drama": 0.4,
        "fined": 0.5,
        "bust-up": 0.7,
        "discontent": 0.5,
        "unhappy": 0.4,
        "overweight": 0.5,
        "crisis": 0.5,
    },
    "positive": {
        "returns": 0.8,
        "back in": 0.7,
        "fit again": 0.8,
        "recovered": 0.8,
        "cleared to play": 0.9,
        "boost": 0.6,
        "welcome back": 0.6,
        "available again": 0.8,
        "passed fit": 0.9,
        "back from injury": 0.9,
        "eligible": 0.5,
        "in form": 0.5,
        "purple patch": 0.6,
        "sharp": 0.3,
        "firing": 0.4,
        "on fire": 0.5,
    },
}

GOSSIP_QUERIES = ["lineup", "team news", "injury", "suspension", "rumors", "leak", "training", "row", "tactics"]

IMPACT_CATEGORIES = {
    "suspended": [
        "suspended", "suspension", "red card", "red-card", "banned", "one-match ban",
        "two-match ban", "sent off", "sent-off", "yellow card accumulation", "suspension for",
    ],
    "injured": [
        "injured", "injury", "ruled out", "sidelined", "surgery", "strain", "knock",
        "out for", "absent", "concussion",
    ],
    "benched": [
        "benched", "dropped", "on the bench", "from the bench", "substitute",
        "omitted", "left out", "rested", "out of the squad",
    ],
    "transfers_out": [
        "leaving", "exit", "departure", "sold", "sale", "wants out", "poached",
        "release clause activated", "waving goodbye", "last game",
    ],
    "transfers_in": [
        "signing", "signs", "joins", "agrees deal", "arrival", "incoming",
        "completes move", "close to signing", "bids for",
    ],
    "returning": [
        "returns", "back in training", "fit", "recovered", "cleared to play",
        "available again", "passed fit", "welcome back", "back from injury",
    ],
}

DEFAULT_CONFIG = {
    "enabled": True,
    "news_hl": "en",
    "news_cache_hours": 12,
    "news_lookups_per_scan": 8,
    "news_lookups_per_request": 2,
    "news_requests_per_minute": 30,
    "news_weight": 0.10,
    "borderline_window_pct": 3.0,
}

# Idioms that *look* like an injury/suspension keyword but are not one.
# Real false positive from the cache: "Rico Verhoeven called out for 'historic'
# fight on Fury vs Joshua card" was scored as an INJURY for both boxers because it
# contains "out for". That fake news would have produced a fake edge.
NOISE_PATTERNS = (
    r"\bcalled out for\b", r"\bcall(?:s|ed)? out\b", r"\bspeaks? out\b", r"\bspoke out\b",
    r"\bshout[- ]out\b", r"\bout of the (?:blue|running|question|picture)\b",
    r"\bwork(?:s|ed)? out\b", r"\bworkout\b", r"\bknocked out of\b", r"\bout to (?:prove|win|make)\b",
    r"\bmissing out\b", r"\bfind(?:s|ing)? out\b", r"\bpoint(?:s|ed)? out\b", r"\btalk(?:s|ed)? out\b",
    r"\broll(?:s|ed)? out\b", r"\bcheck(?:s|ed)? out\b", r"\bdraw(?:s|n)? out\b",
    r"\breach(?:es|ed)? out\b", r"\bhand(?:s|ed)? out\b", r"\bsell(?:s|ing)? out\b",
    r"\bmisses out\b", r"\bout of contract\b", r"\bout of favour\b", r"\bout of form\b",
)

# How much a story category moves a team's outlook. Injuries and suspensions are
# the real signal; transfer chatter is weak; a returning player is a small boost.
SEVERITY = {
    "injured": -1.0,
    "suspended": -0.85,
    "benched": -0.50,
    "transfers_out": -0.35,
    "transfers_in": 0.25,
    "returning": 0.55,
}

# Bumped when the scoring logic changes, so cached teams are re-scored from their
# stored headlines instead of being refetched (0 network requests).
SCORE_VERSION = 2


def strip_noise(text):
    out = str(text or "")
    for pat in NOISE_PATTERNS:
        out = re.sub(pat, " ", out, flags=re.IGNORECASE)
    return out



def _clamp(x, lo, hi):
    return max(lo, min(hi, x))


def _strip_html(text):
    return re.sub(r"<[^>]+>", "", text)


STOP_TERMS = {
    "the", "vs", "fc", "cf", "afc", "sunday", "saturday", "monday", "tuesday",
    "wednesday", "thursday", "friday", "premier", "league", "champions", "cup",
    "team", "news", "xi", "update", "confirmed", "predicted", "ahead", "today",
    "match", "preview", "kicks", "time", "weekend", "winter", "summer", "january",
    "february", "march", "april", "may", "june", "july", "august", "september",
    "october", "november", "december", "english", "german", "spanish", "french",
    "italian", "man", "old", "trafford", "stadium", "round", "watch", "live",
}


def _tokens(text):
    """Alphanumeric tokens of length > 1 (used for team-name matching)."""
    return {t for t in "".join(ch if ch.isalnum() else " " for ch in str(text or "").lower()).split() if len(t) > 1}


def extract_players(headlines, exclude_terms=()):
    excluded = {t.strip().lower() for t in exclude_terms if t}
    players = []
    for h in headlines:
        for m in re.finditer(r"\b[A-Z][a-z]{2,}(?:\s+[A-Z][a-z]{2,}){0,2}\b", h):
            name = m.group(0)
            words = name.lower().split()
            if any(w in STOP_TERMS or w in excluded or len(w) < 3 for w in words):
                continue
            if name not in players:
                players.append(name)
    return players[:8]


def _match_keyword(keyword, text):
    if " " in keyword:
        return keyword in text
    return bool(re.search(rf"\b{re.escape(keyword)}\b", text))


def classify_headline(text, keywords=None):
    hl = strip_noise(text).lower()
    kws = keywords or IMPACT_CATEGORIES
    # Recovery phrasing must win over the bare word "injury": "returns to training
    # after injury" is a boost, not a loss (it used to be scored negative).
    if any(p in hl for p in (
        "after injury", "from injury", "back from injury", "returns to training",
        "back in training", "passed fit", "cleared to play", "available again",
        "fit again", "recovered from", "returns after", "welcome back",
    )):
        return ("returning", 0.8, False)
    if any(_match_keyword(k, hl) for k in kws["injured"]):
        sev = 1.0 if any(x in hl for x in ("ruled out", "out for", "sidelined", "surgery", "concussion")) else 0.7
        return ("injured", sev, True)
    if any(_match_keyword(k, hl) for k in kws["suspended"]):
        return ("suspended", 1.0, True)
    if any(_match_keyword(k, hl) for k in kws["benched"]):
        return ("benched", 0.6, True)
    if any(_match_keyword(k, hl) for k in kws["transfers_out"]):
        return ("transfers_out", 0.5, True)
    if any(_match_keyword(k, hl) for k in kws["transfers_in"]):
        return ("transfers_in", 0.3, False)
    if any(_match_keyword(k, hl) for k in kws["returning"]):
        return ("returning", 0.8, False)
    return None


def build_impact(headlines, keywords=None, team=None):
    cats = {c: [] for c in IMPACT_CATEGORIES}
    raw = 0.0
    seen = set()
    for h in relevant_headlines(headlines, team):
        cls = classify_headline(h, keywords)
        if not cls:
            continue
        cat, sev, _neg = cls
        cats[cat].append(h[:200])
        key = re.sub(r"[^a-z0-9 ]", "", str(h).lower())[:60] + "|" + cat
        if key in seen:
            continue
        seen.add(key)
        raw += SEVERITY.get(cat, 0.0) * (0.6 + 0.4 * float(sev))
    score = _clamp(raw / (1.0 + abs(raw)), -1.0, 1.0) if raw else 0.0
    return {
        "categories": {k: v[:3] for k, v in cats.items()},
        "impact_score": round(score, 3),
    }


_IMPACT_LABELS = {
    "injured":       {"ro": "Accidentați", "de": "Verletzte", "en": "Injured"},
    "suspended":     {"ro": "Suspendări/cartonage", "de": "Sperren/Karten", "en": "Suspensions/cards"},
    "benched":       {"ro": "Pe bancă/lăsați afară", "de": "Auf der Bank/aussortiert", "en": "Benched/left out"},
    "transfers_out": {"ro": "Pleacă (transfer)", "de": "Abgänge (Transfer)", "en": "Transfers out"},
    "transfers_in":  {"ro": "Vin (transfer)", "de": "Zugänge (Transfer)", "en": "Transfers in"},
    "returning":     {"ro": "Revin după accidentare", "de": "Rückkehrer", "en": "Back from injury"},
}
_IMPACT_EMPTY = {
    "ro": "Nicio știre de impact găsită.",
    "de": "Keine relevanten Meldungen gefunden.",
    "en": "No impactful news found.",
}


def _news_word(n, lang):
    if lang == "de":
        return "Meldung" if n == 1 else "Meldungen"
    if lang == "en":
        return "report" if n == 1 else "reports"
    if n == 1:
        return "știre"
    if n < 20:
        return "știri"
    return "de știri"


def summarize_impact(impact, lang="ro"):
    lang = lang if lang in ("ro", "de", "en") else "ro"
    cats = (impact or {}).get("categories", {}) or {}
    parts = []
    for key, labels in _IMPACT_LABELS.items():
        n = len(cats.get(key) or [])
        if n:
            parts.append(f"{labels[lang]}: {n} {_news_word(n, lang)}")
    return "; ".join(parts) if parts else _IMPACT_EMPTY[lang]


def fetch_team_news(team_name, hl="en", max_items=10):
    query = quote(f'"{team_name}"')
    url = f"https://news.google.com/rss/search?q={query}&hl={hl}&gl={hl}&ceid={hl}"
    try:
        resp = requests.get(url, timeout=6, headers={"User-Agent": "Mozilla/5.0"})
        root = ET.fromstring(resp.content)
        items = []
        for item in root.iter("item"):
            title = item.findtext("title") or ""
            desc = item.findtext("description") or ""
            text = _strip_html(title).strip() or _strip_html(desc).strip()
            if not text.strip():
                continue
            items.append(text)
            if len(items) >= max_items:
                break
        return items
    except Exception:
        return []


def fetch_team_gossip_bing_news(team_name, max_items=5):
    query = quote(f'"{team_name}" (suspension OR "red card" OR transfer OR bench OR "team news" OR lineup)')
    url = f"https://www.bing.com/news/search?q={query}&format=rss"
    try:
        resp = requests.get(
            url, timeout=6, headers={"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"}
        )
        root = ET.fromstring(resp.content)
        items = []
        for item in root.iter("item"):
            title = item.findtext("title") or ""
            desc = item.findtext("description") or ""
            text = _strip_html(title).strip() or _strip_html(desc).strip()
            if text.strip():
                items.append(text)
            if len(items) >= max_items:
                break
        return items
    except Exception:
        return []


def fetch_team_gossip_bing_injuries(team_name, max_items=5):
    query = quote(f'"{team_name}" injury OR "ruled out" OR sidelined OR out')
    url = f"https://www.bing.com/news/search?q={query}&format=rss"
    try:
        resp = requests.get(
            url, timeout=6, headers={"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"}
        )
        root = ET.fromstring(resp.content)
        items = []
        for item in root.iter("item"):
            title = item.findtext("title") or ""
            desc = item.findtext("description") or ""
            text = _strip_html(title).strip() or _strip_html(desc).strip()
            if text.strip():
                items.append(text)
            if len(items) >= max_items:
                break
        return items
    except Exception:
        return []


def fetch_team_gossip_bing_web(team_name, max_items=5):
    query = quote(f'"{team_name}" injury lineup news')
    url = f"https://www.bing.com/search?q={query}"
    try:
        resp = requests.get(
            url, timeout=6, headers={"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"}
        )
        html = resp.text
        snippets = re.findall(r'<p[^>]*class="b_lineclamp[^"]*"[^>]*>(.*?)</p>', html, re.DOTALL)
        items = []
        for s in snippets[:max_items]:
            text = _strip_html(unescape(s)).strip()
            if text:
                items.append(text)
        return items
    except Exception:
        return []


def _dedupe(items):
    seen = set()
    out = []
    for it in items:
        key = re.sub(r"[^a-z0-9 ]", "", it.lower())[:120]
        if key and key not in seen:
            seen.add(key)
            out.append(it)
    return out


def score_news(headlines, keywords=None):
    kws = keywords or NEWS_KEYWORDS
    pos = 0.0
    neg = 0.0
    for headline in headlines:
        hl = strip_noise(headline).lower()
        for word, w in kws["negative"].items():
            if _match_keyword(word, hl):
                neg += w
        for word, w in kws["positive"].items():
            if _match_keyword(word, hl):
                pos += w
    n = max(len(headlines), 1)
    return _clamp((pos - neg) / n, -1.0, 1.0)


def _mentions_team(headline, team):
    """Does this story actually name the team (and not just sit on its news page)?"""
    if not headline or not team:
        return True
    toks = {t for t in _tokens(team) if len(t) >= 4 and t not in STOP_TERMS}
    if not toks:
        return True
    hl = " " + "".join(ch if ch.isalnum() else " " for ch in str(headline).lower()) + " "
    return any(f" {t}" in hl for t in toks)


def relevant_headlines(headlines, team=None):
    """Stories that really name the team; falls back to all when nothing matches."""
    if not team:
        return list(headlines)
    hit = [h for h in headlines if _mentions_team(h, team)]
    return hit or list(headlines)


def severity_score(headlines, team=None):
    """News score in [-1, 1] driven by the SEVERITY of the stories, not their count.

    Old behaviour (`score_news`): keyword hits were averaged over ALL headlines, so a
    single confirmed "ruled out" among 13 neutral headlines yielded ~0.07 -> a tilt of
    ~0.2%, i.e. invisible (below any threshold). That is why news never changed a bet.

    Now: every distinct story counts once (repeated copies are deduped), category
    severities add up and SATURATE, so one confirmed key absence is a strong signal
    while ten copies of the same story are not ten times stronger.
    """
    raw = 0.0
    seen = set()
    for h in relevant_headlines(headlines, team):
        cls = classify_headline(h)
        if not cls:
            continue
        cat, sev, _neg = cls
        key = re.sub(r"[^a-z0-9 ]", "", str(h).lower())[:60] + "|" + cat
        if key in seen:
            continue
        seen.add(key)
        raw += SEVERITY.get(cat, 0.0) * (0.6 + 0.4 * float(sev))
    if raw == 0.0:
        return 0.0
    return round(_clamp(raw / (1.0 + abs(raw)), -1.0, 1.0), 3)



def _pick_headline(headlines, keywords, want_positive):
    kws = keywords or NEWS_KEYWORDS
    for h in headlines:
        hl = h.lower()
        hit = any(_match_keyword(word, hl) for word in kws["positive"] if want_positive) or (
            any(_match_keyword(word, hl) for word in kws["negative"]) and not want_positive
        )
        if hit:
            return h
    return None



def _run_with_budget(jobs, budget=4.5):
    """Run callables in parallel but never wait longer than the given budget in seconds.

    Slow jobs keep running in the background and their result is simply discarded,
    so one hanging news site cannot delay the whole analysis.
    """
    pool = ThreadPoolExecutor(max_workers=max(1, len(jobs)))
    futures = [pool.submit(job) for job in jobs]
    deadline = time.time() + budget
    out = []
    for fut in futures:
        remaining = deadline - time.time()
        if remaining <= 0:
            out.append(None)
            continue
        try:
            out.append(fut.result(timeout=remaining))
        except Exception:
            out.append(None)
    pool.shutdown(wait=False)
    return out

class ContextEngine:
    def __init__(self, config=None, cache_file="context_cache.json"):
        self.config = dict(DEFAULT_CONFIG)
        if config:
            self.config.update(config)
        self.cache_file = cache_file
        self.cache = self._load()
        self.lookups_this_scan = 0
        self.lookups_this_request = 0
        self._req_window = []
        self._lock = threading.Lock()

    def _load(self):
        if not os.path.exists(self.cache_file):
            return {}
        try:
            with open(self.cache_file, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            return {}

    def _save(self):
        with open(self.cache_file, "w", encoding="utf-8") as f:
            json.dump(self.cache, f, ensure_ascii=False, indent=2)

    def _is_fresh(self, team):
        entry = self.cache.get(team)
        if not entry:
            return False
        age_hours = (time.time() - entry.get("ts", 0)) / 3600
        return age_hours < self.config["news_cache_hours"]

    def begin_scan(self):
        self.lookups_this_scan = 0

    def begin_request(self):
        """Reset the per-request budget of the interactive path.

        Why: the background scan burns the shared budget on its first few teams, so
        every later user analysis used to get `score 0.0` (no news at all) until the
        next scan. Interactive requests now have their own budget.
        """
        self.lookups_this_request = 0

    def _request_budget_ok(self):
        cap = int(self.config.get("news_lookups_per_request", 2) or 0)
        if self.lookups_this_request >= cap:
            return False
        window = int(self.config.get("news_requests_per_minute", 30) or 0)
        now = time.time()
        with self._lock:
            self._req_window = [t for t in getattr(self, "_req_window", []) if now - t < 60]
            if window and len(self._req_window) >= window:
                return False
            self._req_window.append(now)
        self.lookups_this_request += 1
        return True

    def _rescore(self, team, entry):
        """Re-derive score/impact from the stored headlines with the current logic."""
        headlines = entry.get("headlines", []) or []
        impact = build_impact(headlines, team=team) if headlines else {"categories": {}, "impact_score": 0.0}
        score = severity_score(headlines, team=team) if headlines else 0.0
        entry["score"] = score
        entry["impact"] = impact
        entry["score_version"] = SCORE_VERSION
        with self._lock:
            self.cache[team] = entry
            self._save()
        return entry

    def get_team_context(self, team, interactive=False):
        if not self.config.get("enabled"):
            return {"team": team, "score": 0.0, "headlines": []}
        if not team:
            return {"team": team, "score": 0.0, "headlines": []}
        if self._is_fresh(team):
            entry = self.cache[team]
            if entry.get("score_version") != SCORE_VERSION:
                entry = self._rescore(team, entry)
            impact = entry.get("impact") or build_impact(entry.get("headlines", []), team=team)
            return {
                "team": team,
                "score": entry.get("score", 0.0),
                "impact": impact,
                "impact_summary": summarize_impact(impact),
                "headlines": entry.get("headlines", []),
            }
        if interactive:
            if not self._request_budget_ok():
                return {"team": team, "score": 0.0, "headlines": []}
        elif self.lookups_this_scan >= self.config["news_lookups_per_scan"]:
            return {"team": team, "score": 0.0, "headlines": []}
        if not interactive:
            self.lookups_this_scan += 1
        hl = self.config.get("news_hl", "en")
        jobs = (
            lambda: fetch_team_news(team, hl=hl),
            lambda: fetch_team_gossip_bing_news(team),
            lambda: fetch_team_gossip_bing_injuries(team),
            lambda: fetch_team_gossip_bing_web(team),
        )

        def _safe(job):
            try:
                return job() or []
            except Exception:
                return []

        # four sources in parallel, with a HARD time budget: whatever arrived in ~4s is used,
        # the rest is ignored (a slow news site must never freeze the analysis).
        chunks = _run_with_budget([lambda job=job: _safe(job) for job in jobs], budget=4.5)
        headlines = _dedupe([h for chunk in chunks for h in chunk])[:14]
        # Score exactly the headlines we store, so a later re-score from the cache
        # returns the same number (no "the value changed by itself" surprises).
        kept = headlines[:6]
        score = severity_score(kept, team=team) if kept else 0.0
        impact = (
            build_impact(kept, team=team)
            if kept
            else {"categories": {}, "impact_score": 0.0}
        )
        entry = {
            "ts": time.time(),
            "score": score,
            "score_version": SCORE_VERSION,
            "headlines": kept,
            "impact": impact,
            "positive_headline": _pick_headline(kept, None, True),
            "negative_headline": _pick_headline(kept, None, False),
        }
        with self._lock:
            self.cache[team] = entry
            self._save()
        return {
            "team": team,
            "score": score,
            "impact": impact,
            "impact_summary": summarize_impact(impact),
            "headlines": headlines[:6],
            "gossip_count": len(headlines),
        }

    def get_event_context(self, home, away, interactive=False):
        # both teams at the same time, same hard budget
        if interactive:
            self.begin_request()
        jobs = [lambda t=t: self.get_team_context(t, interactive=interactive) for t in (home, away)]
        results = _run_with_budget(jobs, budget=5.0)
        empty = {"team": "", "score": 0.0, "headlines": []}
        return {"home": results[0] or empty, "away": results[1] or empty}


    def apply_adjustment(self, probs, context, weight=None):
        """Bounded tilt of the market probabilities by the news mood.

        `score` per team is in [-1, 1]; `weight` (news_weight) caps how far a single
        team can move (0.25 = at most ~25% relative on that side).

        The draw moves only with the DIFFERENCE between the two teams. The old version
        used the SUM, so when both teams had bad news the draw was pushed up on its own
        - and because the same story often lands on both teams' news pages, that
        produced a mechanical run of fake "draw value" (48 value bets, most on the
        draw). Equal news on both sides must mean "no information", not a draw edge.
        """
        if not context:
            return probs
        w = weight if weight is not None else self.config["news_weight"]
        home_score = context.get("home", {}).get("score", 0.0)
        away_score = context.get("away", {}).get("score", 0.0)
        adjusted = list(probs)
        if len(adjusted) == 3:
            adjusted[0] *= 1.0 + home_score * w
            adjusted[2] *= 1.0 + away_score * w
            # The draw follows the AVERAGE mood (both teams weakened -> fewer goals ->
            # slightly more draws) times a damping for how one-sided the news is.
            # Using `home + away` before made equal news on both sides inflate the draw
            # by itself (renormalisation), which produced a run of fake "draw value".
            # With this form, identical scores on both teams are an exact no-op.
            avg = (home_score + away_score) / 2.0
            delta = abs(home_score - away_score)
            adjusted[1] *= (1.0 + avg * w) * (1.0 - delta * w * 0.25)
        else:
            adjusted[0] *= 1.0 + home_score * w
            adjusted[1] *= 1.0 + away_score * w
        total = sum(adjusted)
        if total <= 0:
            return probs
        return [p / total for p in adjusted]