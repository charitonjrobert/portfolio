# -*- coding: utf-8 -*-
"""Small disk-backed TTL cache.

Why: several sources are rate-limited (football-data.org = 10 requests/minute,
the-odds-api = 500/month, API-Football = 100/day). Repeating the same request
inside a short window must never touch them again.

Design choices (kept deliberately simple):
  * one JSON file, human readable, safe to delete at any time;
  * entries are pruned on load and on every write (no unbounded growth);
  * a `max_age` per entry, plus a global retention so old keys disappear.
"""
import json
import os
import threading
import time


class TtlCache:
    def __init__(self, path, retention_seconds=86400):
        self.path = str(path)
        self.retention_seconds = retention_seconds
        self._lock = threading.RLock()
        self._data = {}
        self._load()

    # ------------------------------------------------------------- internals
    def _load(self):
        if not os.path.exists(self.path):
            return
        try:
            with open(self.path, "r", encoding="utf-8") as f:
                data = json.load(f)
            if isinstance(data, dict):
                self._data = data
        except (json.JSONDecodeError, OSError):
            self._data = {}
        self._prune()

    def _save(self):
        try:
            tmp = self.path + ".tmp"
            with open(tmp, "w", encoding="utf-8") as f:
                json.dump(self._data, f, ensure_ascii=False)
            os.replace(tmp, self.path)
        except OSError:
            pass

    def _prune(self):
        now = time.time()
        dead = [
            k for k, v in self._data.items()
            if not isinstance(v, dict) or (now - float(v.get("ts", 0))) > self.retention_seconds
        ]
        for k in dead:
            self._data.pop(k, None)

    # ---------------------------------------------------------------- public
    def age(self, key):
        entry = self._data.get(key)
        if not isinstance(entry, dict):
            return None
        return round(time.time() - float(entry.get("ts", 0)), 1)

    def get(self, key, ttl=None):
        entry = self._data.get(key)
        if not isinstance(entry, dict):
            return None
        age = time.time() - float(entry.get("ts", 0))
        if ttl is not None and age > ttl:
            return None
        return entry.get("value")

    def get_entry(self, key, ttl=None):
        value = self.get(key, ttl)
        if value is None:
            return None, None
        return value, self.age(key)

    def set(self, key, value):
        with self._lock:
            self._data[key] = {"ts": time.time(), "value": value}
            self._prune()
            self._save()

    def get_or_set(self, key, ttl, loader):
        """Return (value, from_cache). Runs `loader` only on a miss."""
        value = self.get(key, ttl)
        if value is not None:
            return value, True
        value = loader()
        self.set(key, value)
        return value, False

    def clear(self, prefix=None):
        with self._lock:
            if prefix:
                for k in [k for k in self._data if k.startswith(prefix)]:
                    self._data.pop(k, None)
            else:
                self._data = {}
            self._save()

    def stats(self):
        now = time.time()
        out = []
        for k, v in self._data.items():
            if isinstance(v, dict):
                out.append({"key": k, "age_s": round(now - float(v.get("ts", 0)), 1)})
        out.sort(key=lambda x: x["age_s"])
        return {"entries": len(out), "items": out[:40], "path": self.path, "retention_s": self.retention_seconds}
