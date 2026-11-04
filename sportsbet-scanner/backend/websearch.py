import base64
import re
from html import unescape
from urllib.parse import urlparse

import requests

USER_AGENT = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
    "(KHTML, like Gecko) Chrome/126.0.0.0 Safari/537.36"
)


def _text(html):
    return unescape(re.sub(r"<[^>]+>", " ", html)).strip()


def _clean_url(href):
    href = unescape(href)
    if "/ck/a" in href:
        m = re.search(r"[?&]u=a1([^&]+)", href)
        if m:
            s = m.group(1)
            pad = "=" * (-len(s) % 4)
            try:
                return base64.urlsafe_b64decode(s + pad).decode("utf-8", "ignore")
            except Exception:
                pass
    return href


def web_search(query, max_results=8):
    url = "https://www.bing.com/search"
    try:
        resp = requests.get(
            url,
            params={"q": query, "setlang": "ro", "cc": "RO"},
            headers={"User-Agent": USER_AGENT},
            timeout=20,
        )
        resp.raise_for_status()
    except Exception as e:
        return {"error": f"Căutarea web a eșuat: {e}"}
    html = resp.text
    blocks = re.findall(r'<li class="b_algo".*?</li>', html, re.S)
    if not blocks:
        blocks = re.findall(r'<div class="b_algo".*?</div>\s*</li>', html, re.S)
    if not blocks:
        return {"error": "Căutarea web nu a returnat rezultate (posibil blocat de anti-bot)."}
    results = []
    for b in blocks:
        m = re.search(r'<h2[^>]*>\s*<a[^>]*href="([^"]+)"[^>]*>(.*?)</a>', b, re.S)
        if not m:
            m = re.search(r'<a[^>]*href="(https?://[^"]+)"[^>]*>(.*?)</a>', b, re.S)
        if not m:
            continue
        title = _text(m.group(2))
        url = _clean_url(m.group(1))
        p = re.search(r'<p[^>]*>(.*?)</p>', b, re.S)
        snippet = _text(p.group(1)) if p else ""
        results.append({"title": title, "url": url, "snippet": snippet})
        if len(results) >= max_results:
            break
    if not results:
        return {"error": "Căutarea web nu a găsit rezultate utile."}
    return {"query": query, "results": results}


def fetch_page(url, max_chars=6000):
    try:
        parsed = urlparse(url)
    except Exception:
        return {"error": "URL invalid."}
    if parsed.scheme not in ("http", "https"):
        return {"error": "Permise doar URL-uri http/https."}
    try:
        resp = requests.get(
            url,
            headers={"User-Agent": USER_AGENT},
            timeout=20,
        )
        resp.raise_for_status()
    except Exception as e:
        return {"error": f"Nu am putut deschide pagina: {e}"}
    text = _text(resp.text)
    text = re.sub(r"\s+", " ", text).strip()
    return {"url": url, "content": text[:max_chars]}