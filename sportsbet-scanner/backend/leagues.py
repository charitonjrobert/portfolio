import json
import time
from pathlib import Path

GROUPS = [
    "soccer", "tennis", "basketball", "americanfootball", "icehockey",
    "baseball", "cricket", "mma", "boxing", "golf", "aussierules",
    "lacrosse", "rugbyleague", "darts", "politics",
]

CATALOG_FILE = Path(__file__).parent / "sports_catalog.json"
CATALOG_TTL = 7 * 24 * 3600


def load_catalog():
    if CATALOG_FILE.exists():
        try:
            with open(CATALOG_FILE, encoding="utf-8") as f:
                data = json.load(f)
            if time.time() - data.get("ts", 0) < CATALOG_TTL:
                return data.get("catalog", [])
        except Exception:
            pass
    return None


def save_catalog(catalog):
    with open(CATALOG_FILE, "w", encoding="utf-8") as f:
        json.dump({"ts": time.time(), "catalog": catalog}, f, ensure_ascii=False, indent=2)


def build_catalog(fetcher):
    cats = load_catalog()
    if cats:
        return cats
    groups_map = fetcher.discover_sport_keys(GROUPS)
    catalog = []
    for group, sports in groups_map.items():
        for s in sports:
            catalog.append({"key": s["key"], "title": s.get("title", ""), "group": group})
    save_catalog(catalog)
    return catalog


ALIASES = {
    "elveția": ["switzerland", "swiss"],
    "elvetia": ["switzerland", "swiss"],
    "elveţia": ["switzerland", "swiss"],
    "schweiz": ["switzerland", "swiss"],
    "sviteția": ["switzerland", "swiss"],
    "anglia": ["england", "epl", "premier"],
    "spania": ["spain"],
    "italia": ["italy"],
    "germania": ["germany", "german"],
    "germany": ["germany", "german"],
    "franta": ["france"],
    "franța": ["france"],
    "portugalia": ["portugal"],
    "olanda": ["netherlands", "dutch", "eredivisie"],
    "turcia": ["turkey"],
    "rusia": ["russia"],
    "grecia": ["greece"],
    "suedia": ["sweden"],
    "norvegia": ["norway"],
    "polonia": ["poland"],
    "austria": ["austria"],
    "belgia": ["belgium"],
    "brasil": ["brazil"],
    "brazilia": ["brazil"],
    "mexic": ["mexico", "ligamx"],
    "romania": ["romania"],
    "liga 1": ["romania"],
    "liga i": ["romania"],
    "super league": ["superleague", "super_league"],
    "liga elitelor": ["romania"],
    "sansa dubla": [],
    "1x2": [],
}


def _expand(query):
    q = query.strip().lower()
    expanded = [q]
    aliases = ALIASES.get(q)
    if aliases:
        expanded.extend(aliases)
    return expanded


def match_leagues(catalog, query):
    q = query.strip().lower()
    if not q:
        return []
    expanded = _expand(query)
    hits = []
    for c in catalog:
        hay = (c["key"] + " " + c["title"]).lower().replace("_", " ")
        for term in expanded:
            if term and term in hay:
                hits.append(c)
                break
        else:
            qtokens = [t for t in q.split() if len(t) >= 3]
            htokens = set(hay.split())
            if qtokens and all(t in htokens for t in qtokens):
                hits.append(c)
    dedup = {}
    for c in hits:
        dedup[c["key"]] = c
    return list(dedup.values())


def fetch_leagues(fetcher, storage, catalog_hits, cap=5):
    events_by_sport = storage.load_cache()
    used = 0
    remaining = None
    fetched = []
    for c in catalog_hits[:cap]:
        try:
            events, headers = fetcher.get_odds(c["key"])
        except Exception:
            continue
        group = c["group"]
        for ev in events:
            ev["sport_group"] = group
            ev["sport_title"] = c["title"]
        events_by_sport.setdefault(group, [])
        ids = {ev.get("id") for ev in events if ev.get("id")}
        events_by_sport[group] = [ev for ev in events_by_sport[group] if ev.get("id") not in ids]
        events_by_sport[group].extend(events)
        fetched.append({"key": c["key"], "title": c["title"], "group": group, "matches": len(events)})
        used += 1
        remaining = headers.get("remaining")
    storage.save_cache(events_by_sport)
    return {"fetched": fetched, "used": used, "remaining": remaining}


def group_catalog(catalog):
    grouped = {}
    for c in catalog:
        grouped.setdefault(c["group"], []).append(c)
    return grouped