import sys, re, xml.etree.ElementTree as ET
sys.path.insert(0, 'backend')
import requests
from urllib.parse import quote

UA = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0 Safari/537.36"}

q = quote('"Arsenal" injury lineup')

urls = {
    "bing-news-rss": f"https://www.bing.com/news/search?q={q}&format=rss",
    "bing-web": f"https://www.bing.com/search?q={q}",
    "ddg-lite": f"https://lite.duckduckgo.com/lite/?q={q}",
}

for name, url in urls.items():
    try:
        r = requests.get(url, timeout=15, headers=UA)
        print(name, "status:", r.status_code, "len:", len(r.text))
        if name == "bing-news-rss":
            try:
                root = ET.fromstring(r.content)
                items = [it.findtext("title") for it in root.iter("item")][:4]
                print("  titles:", [t[:80] for t in items if t])
            except Exception as e:
                print("  rss err:", e, r.text[:150])
        else:
            snips = re.findall(r'<p[^>]*class="b_lineclamp[^"]*"[^>]*>(.*?)</p>', r.text, re.DOTALL)
            print("  bing snippets:", len(snips), [re.sub(r"<[^>]+>", "", s)[:80] for s in snips[:3]])
    except Exception as e:
        print(name, "EXC", e)