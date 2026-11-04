import time

import requests

BASE = "https://v3.football.api-sports.io"
HOST = "v3.football.api-sports.io"


class FootballAPI:
    def __init__(self, api_key="", base_url=BASE, host=HOST):
        self.api_key = api_key or ""
        self.base_url = base_url or BASE
        self.host = host or HOST
        self._status_cache = None
        self._status_cache_ts = 0.0

    def _headers(self):
        return {
            "x-apisports-key": self.api_key,
            "x-rapidapi-key": self.api_key,
            "x-rapidapi-host": self.host,
        }

    def remaining_requests(self):
        now = time.time()
        if self._status_cache is not None and now - self._status_cache_ts < 300:
            return self._status_cache
        url = f"{self.base_url}/status"
        resp = requests.get(url, headers=self._headers(), timeout=30)
        resp.raise_for_status()
        req = (resp.json().get("response") or {}).get("requests") or {}
        self._status_cache = max(0, int(req.get("limit_day", 100)) - int(req.get("current", 0)))
        self._status_cache_ts = now
        return self._status_cache

    def _get(self, path, params):
        if not self.api_key:
            raise RuntimeError(
                "Lipsă cheie API-Football. Înregistrează-te gratuit la "
                "https://dashboard.api-football.com/register și completează "
                "api_football.api_key în backend/config.json."
            )
        url = f"{self.base_url}{path}"
        resp = requests.get(url, headers=self._headers(), params=params, timeout=30)
        if resp.status_code == 429:
            time.sleep(3)
            resp = requests.get(url, headers=self._headers(), params=params, timeout=30)
        if resp.status_code == 429:
            raise RuntimeError(
                "Rate-limit API-Football (429): ai depășit limita pe minut. Încearcă din nou peste 1-2 minute."
            )
        resp.raise_for_status()
        data = resp.json()
        paging = data.get("paging") or {}
        remaining = None
        if paging.get("total") is not None and paging.get("current") is not None:
            remaining = int(paging["total"]) - int(paging["current"])
        return data.get("response", []), remaining, data.get("errors")

    def status(self):
        if not self.api_key:
            raise RuntimeError("Lipsă cheie API-Football.")
        url = f"{self.base_url}/status"
        resp = requests.get(url, headers=self._headers(), timeout=30)
        resp.raise_for_status()
        data = resp.json()
        return data.get("response", {}), data.get("errors")

    def leagues(self, search=None, country=None):
        params = {}
        if search:
            params["search"] = search
        if country:
            params["country"] = country
        return self._get("/leagues", params)

    def teams_by_name(self, name):
        return self._get("/teams", {"search": name})

    def fixtures(self, league_id=None, season=None, date=None, team_id=None, next=None, live=None, fixture_id=None):
        params = {}
        if league_id:
            params["league"] = league_id
        if season:
            params["season"] = season
        if date:
            params["date"] = date
        if team_id:
            params["team"] = team_id
        if next:
            params["next"] = next
        if live:
            params["live"] = live
        if fixture_id:
            params["id"] = fixture_id
        return self._get("/fixtures", params)

    def h2h(self, team1, team2):
        return self._get("/fixtures/headtohead", {"h2h": f"{team1}-{team2}"})

    def standings(self, league_id, season):
        return self._get("/standings", {"league": league_id, "season": season})

    def teams(self, league_id, season):
        return self._get("/teams", {"league": league_id, "season": season})

    def odds_by_fixture(self, fixture_id):
        return self._get("/odds", {"fixture": fixture_id})

    def odds_by_league(self, league_id, season, page=None):
        params = {"league": league_id, "season": season}
        if page:
            params["page"] = page
        return self._get("/odds", params)

    def predictions(self, fixture_id):
        return self._get("/predictions", {"fixture": fixture_id})

    def lineups(self, fixture_id):
        return self._get("/fixtures/lineups", {"fixture": fixture_id})

    def teams_by_id(self, team_id):
        return self._get("/teams", {"id": team_id})