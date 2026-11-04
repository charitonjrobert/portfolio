# -*- coding: utf-8 -*-
"""football-data.org client (free tier: 10 req/min, 12 competitions).

Used for UPCOMING football fixtures (which API-Football's free plan does not expose).
Docs: https://www.football-data.org/documentation/quickstart
"""
import threading
import time

import requests

BASE = "https://api.football-data.org/v4"

# Free-tier ("Tier One") competitions only.
FREE_COMPETITIONS = {
    "PL": "Premier League",
    "PD": "La Liga",
    "SA": "Serie A",
    "BL1": "Bundesliga",
    "FL1": "Ligue 1",
    "DED": "Eredivisie",
    "PPL": "Primeira Liga",
    "ELC": "Championship",
    "BSA": "Brasileirao Serie A",
    "CL": "Champions League",
    "EC": "Euro",
    "WC": "World Cup",
}

REGISTER_URL = "https://www.football-data.org/client/register"


class FootballData:
    """Minimal client with a hard 10 requests/minute throttle (free tier)."""

    RATE_LIMIT_PER_MIN = 10

    def __init__(self, api_key="", base_url=BASE):
        self.api_key = (api_key or "").strip()
        self.base_url = (base_url or BASE).rstrip("/")
        self._lock = threading.Lock()
        self._window_start = 0.0
        self._window_count = 0
        self._last_meta = {}
        self._last_error = None

    @property
    def configured(self):
        return bool(self.api_key)

    def _throttle(self):
        # football-data.org asks clients to honour its response headers (10/min on the free tier).
        meta = self._last_meta or {}
        avail = str(meta.get("x-requests-available-minute") or "")
        reset = str(meta.get("x-requestcounter-reset") or "")
        if avail == "0" and reset.isdigit():
            with self._lock:
                time.sleep(min(61, max(1, int(reset))))
                self._window_start = time.time()
                self._window_count = 0
                self._last_meta = {}
        with self._lock:
            now = time.time()
            if now - self._window_start >= 60:
                self._window_start = now
                self._window_count = 0
            if self._window_count >= self.RATE_LIMIT_PER_MIN:
                wait = 60.0 - (now - self._window_start)
                if wait > 0:
                    time.sleep(wait)
                self._window_start = time.time()
                self._window_count = 0
            self._window_count += 1
            return self._window_count

    def _get(self, path, params=None):
        if not self.configured:
            raise RuntimeError(
                "Missing football-data.org API key. Register free at "
                + REGISTER_URL
                + " and put the token in backend/config.json -> football_data.api_key"
            )
        self._throttle()
        resp = requests.get(
            self.base_url + path,
            headers={"X-Auth-Token": self.api_key},
            params=params or {},
            timeout=30,
        )
        meta = {k.lower(): v for k, v in resp.headers.items() if k.lower().startswith("x-requests")}
        if meta:
            self._last_meta = meta
        if resp.status_code == 429:
            self._last_error = "rate-limit: max 10 requests/minute"
            raise RuntimeError("football-data.org rate limit hit (10 requests/minute). Try again in a minute.")
        if resp.status_code in (400, 403):
            self._last_error = resp.text[:200]
            raise RuntimeError(f"football-data.org error {resp.status_code}: {resp.text[:200]}")
        resp.raise_for_status()
        self._last_error = None
        return resp.json()

    # --- public API -------------------------------------------------------
    def matches(self, date_from=None, date_to=None, competitions=None, status="SCHEDULED"):
        """Scheduled matches in a date range (defaults: today -> +14 days)."""
        params = {}
        if date_from:
            params["dateFrom"] = date_from
        if date_to:
            params["dateTo"] = date_to
        if competitions:
            params["competitions"] = ",".join(competitions) if isinstance(competitions, (list, tuple)) else competitions
        if status:
            params["status"] = status
        return self._get("/matches", params)

    def competition_matches(self, code, date_from=None, date_to=None, status="SCHEDULED"):
        params = {}
        if date_from:
            params["dateFrom"] = date_from
        if date_to:
            params["dateTo"] = date_to
        if status:
            params["status"] = status
        return self._get(f"/competitions/{code}/matches", params)

    def standings(self, code, season=None):
        params = {}
        if season:
            params["season"] = season
        return self._get(f"/competitions/{code}/standings", params)

    def competitions(self):
        return self._get("/competitions")

    def limit_info(self):
        """Last known rate-limit headers (free tier is 10/minute)."""
        meta = dict(self._last_meta)
        avail = meta.get("x-requests-available-minute")
        return {
            "configured": self.configured,
            "limit_per_minute": self.RATE_LIMIT_PER_MIN,
            "used_this_minute": self._window_count,
            "available_minute": int(avail) if str(avail or "").isdigit() else None,
            "last_counter_reset_s": meta.get("x-requestcounter-reset"),
            "last_error": self._last_error,
            "competitions": FREE_COMPETITIONS,
            "register_url": REGISTER_URL,
        }
