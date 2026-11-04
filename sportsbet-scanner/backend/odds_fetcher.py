import requests


class OddsFetcher:
    BASE = "https://api.the-odds-api.com/v4"

    def __init__(self, api_key, regions=("eu",), markets=("h2h", "totals")):
        self.api_key = api_key
        self.regions = ",".join(regions)
        self.markets = ",".join(markets)

    def _headers(self, resp):
        remaining = resp.headers.get("x-requests-remaining")
        used = resp.headers.get("x-requests-used")
        return {
            "remaining": int(remaining) if remaining and remaining.isdigit() else None,
            "used": int(used) if used and used.isdigit() else None,
        }

    def get_sports(self):
        url = f"{self.BASE}/sports/"
        resp = requests.get(url, params={"apiKey": self.api_key}, timeout=30)
        resp.raise_for_status()
        return resp.json(), self._headers(resp)

    def discover_sport_keys(self, groups):
        sports, _ = self.get_sports()
        found = {}
        for s in sports:
            if not s.get("active"):
                continue
            key = s.get("key", "").lower()
            title = s.get("title", "").lower()
            for g in groups:
                if g in key or g in title:
                    found.setdefault(g, []).append(s)
        return found

    def get_odds(self, sport_key):
        url = f"{self.BASE}/sports/{sport_key}/odds/"
        params = {
            "apiKey": self.api_key,
            "regions": self.regions,
            "markets": self.markets,
            "oddsFormat": "decimal",
        }
        resp = requests.get(url, params=params, timeout=30)
        resp.raise_for_status()
        return resp.json(), self._headers(resp)

    def get_event_odds(self, sport_key, event_id, markets):
        url = f"{self.BASE}/sports/{sport_key}/events/{event_id}/odds/"
        params = {
            "apiKey": self.api_key,
            "regions": self.regions,
            "markets": ",".join(markets),
            "oddsFormat": "decimal",
        }
        resp = requests.get(url, params=params, timeout=30)
        resp.raise_for_status()
        return resp.json(), self._headers(resp)