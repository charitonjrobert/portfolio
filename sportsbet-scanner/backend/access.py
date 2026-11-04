# -*- coding: utf-8 -*-
"""Simple access gate for MicrobistBets.

Why: when the app is exposed through a public tunnel (cloudflared/ngrok) it has no
login of its own. Without a gate, anyone with the link could use the API and burn
the metered quotas (the-odds-api / API-Football) or see the saved bets.

How it works:
  * the key lives in config.json -> ui.access_key;
  * the client opens  https://<tunnel>/?k=<key>  once; the key is stored in an
    HttpOnly cookie and removed from the address bar (302 redirect);
  * everything is protected except a tiny allowlist (icons + manifest) so the
    browser can still render the entry page and the home-screen icon;
  * repeated wrong attempts from the same IP are slowed down.
"""
import html
import threading
import time

from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import HTMLResponse, JSONResponse, RedirectResponse

COOKIE_NAME = "mb_key"
COOKIE_MAX_AGE = 60 * 60 * 24 * 180  # 180 days: the client should not re-enter it

# Public bits (no secrets inside): needed to render the entry page and the icon.
PUBLIC_PATHS = (
    "/assets/icon-192.png",
    "/assets/icon-512.png",
    "/assets/icon-180.png",
    "/assets/manifest.webmanifest",
    "/favicon.ico",
)

_LOGIN_PAGE = """<!DOCTYPE html>
<html lang="ro"><head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1, viewport-fit=cover">
<meta name="theme-color" content="#0f1420">
<title>MicrobistBets</title>
<style>
  * {{ box-sizing: border-box; }}
  body {{ margin:0; min-height:100vh; display:flex; align-items:center; justify-content:center;
    background:#1a1220; color:#fdf6f0; padding:24px;
    font-family:"Segoe UI",system-ui,-apple-system,Roboto,Arial,sans-serif; }}
  .card {{ width:100%; max-width:380px; background:#2a1e33; border:1px solid #46324f;
    border-radius:18px; padding:22px; box-shadow:0 12px 34px rgba(0,0,0,.45); }}
  h1 {{ font-size:1.25rem; margin:0 0 4px; }}
  p {{ color:#b9a4bd; font-size:.88rem; line-height:1.5; }}
  input {{ width:100%; padding:13px 14px; font-size:16px; border-radius:12px;
    border:1px solid #2c3a52; background:#1a1220; color:#fdf6f0; margin:10px 0; }}
  button {{ width:100%; padding:14px; font-size:1rem; font-weight:700; border:0; border-radius:12px;
    background:#ff9f43; color:#2b1400; }}
  .err {{ background:rgba(255,107,122,.14); border:1px solid #ff6b7a; color:#ffc9cf;
    border-radius:10px; padding:9px 11px; font-size:.84rem; margin-bottom:6px; }}
  ul {{ margin:8px 0 0; padding-left:18px; color:#b9a4bd; font-size:.82rem; }}
</style></head>
<body>
  <form class="card" method="get" action="/">
    <h1>🎲 MicrobistBets</h1>
    <p>Aplicația e privată. Introdu cheia de acces primită.</p>
    <p>This app is private. Enter the access key you were given.<br>
       Diese App ist privat. Gib den erhaltenen Zugangsschlüssel ein.</p>
    {error}
    <input name="k" type="password" placeholder="Cheie de acces / Access key" autocomplete="off" autofocus>
    <button type="submit">Intră · Enter · Eintreten</button>
    <ul>
      <li>iPhone: deschide linkul în <b>Safari</b>, apoi <b>Partajează → Adaugă pe ecranul principal</b>.</li>
      <li>iPhone: open the link in <b>Safari</b>, then <b>Share → Add to Home Screen</b>.</li>
    </ul>
  </form>
</body></html>"""


class RateLimitGate(BaseHTTPMiddleware):
    """Cheap per-IP limit so a leaked key or a flood cannot hammer the app.

    Normal use is far below this (the UI makes ~6 calls on load, then a few per minute).
    """

    def __init__(self, app, per_minute=150, window_s=60):
        super().__init__(app)
        self.per_minute = per_minute
        self.window_s = window_s
        self._hits = {}
        self._lock = threading.Lock()
        self._last_prune = 0.0

    def _prune(self, now):
        if now - self._last_prune < 30:
            return
        self._last_prune = now
        for ip in [k for k, v in self._hits.items() if not v or now - v[-1] > self.window_s]:
            self._hits.pop(ip, None)

    @staticmethod
    def _client_ip(request):
        """Behind the tunnel every request arrives from 127.0.0.1, so trust the forwarded header."""
        xff = request.headers.get("x-forwarded-for") or ""
        if xff:
            return xff.split(",")[0].strip() or "?"
        return request.client.host if request.client else "?"

    async def dispatch(self, request, call_next):
        path = request.url.path
        if path.startswith("/assets/"):
            return await call_next(request)
        ip = self._client_ip(request)
        now = time.time()
        with self._lock:
            hits = [t for t in self._hits.get(ip, []) if now - t < self.window_s]
            hits.append(now)
            self._hits[ip] = hits
            self._prune(now)
            over = len(hits) > self.per_minute
        if over:
            return JSONResponse(
                {"error": "rate_limited",
                 "message": "Prea multe cereri într-un minut. Așteaptă puțin. · Too many requests per minute, wait a moment."},
                status_code=429,
                headers={"Retry-After": str(self.window_s)},
            )
        return await call_next(request)


class AccessGate(BaseHTTPMiddleware):
    def __init__(self, app, key="", failures_window_s=300, max_failures=20):
        super().__init__(app)
        self.key = (key or "").strip()
        self.failures_window_s = failures_window_s
        self.max_failures = max_failures
        self._failures = {}
        self._lock = threading.Lock()

    def _too_many(self, client):
        now = time.time()
        with self._lock:
            hits = [t for t in self._failures.get(client, []) if now - t < self.failures_window_s]
            self._failures[client] = hits
            if len(hits) >= self.max_failures:
                return True
            hits.append(now)
            return False

    async def dispatch(self, request, call_next):
        if not self.key:
            return await call_next(request)  # gate disabled

        path = request.url.path
        supplied = (
            request.query_params.get("k")
            or request.cookies.get(COOKIE_NAME)
            or request.headers.get("x-access-key")
            or ""
        )
        if supplied and supplied.strip() == self.key:
            secure = request.url.scheme == "https"
            if request.query_params.get("k"):
                # key came in the URL: store it and clean the address bar
                target = path if path and path != "/" else "/"
                response = RedirectResponse(target, status_code=302)
            else:
                response = await call_next(request)
            response.set_cookie(
                COOKIE_NAME, self.key, max_age=COOKIE_MAX_AGE,
                httponly=True, samesite="lax", secure=secure, path="/",
            )
            return response

        if any(path.startswith(p) for p in PUBLIC_PATHS):
            return await call_next(request)

        client = (request.headers.get("x-forwarded-for") or "").split(",")[0].strip() or (
            request.client.host if request.client else "?")
        throttled = self._too_many(client)
        if path.startswith("/api/"):
            return JSONResponse(
                {"error": "unauthorized",
                 "message": "Cheie de acces lipsă sau greșită. Deschide linkul primit (cu ?k=...)."},
                status_code=429 if throttled else 401,
            )
        error = ""
        if supplied:
            error = '<div class="err">Cheie greșită. Mai încearcă. · Wrong key. Try again.</div>'
        if throttled:
            error = '<div class="err">Prea multe încercări. Așteaptă un minut. · Too many attempts.</div>'
        return HTMLResponse(_LOGIN_PAGE.format(error=error), status_code=429 if throttled else 401)


def make_key():
    import secrets

    return secrets.token_urlsafe(24)
