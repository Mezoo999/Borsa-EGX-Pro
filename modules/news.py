"""طبقة الأخبار الحقيقية لكل سهم — Google News RSS (مجاني، بدون مفاتيح).

يبحث بالاسم العربي للشركة ويجلب آخر العناوين من المصادر الفعلية
(كل عنصر: عنوان + مصدر ناشر + تاريخ + رابط أصلي — بلا أي بيانات مولدة أو تجريبية).
"""
import threading
import time as _time
import xml.etree.ElementTree as ET
from email.utils import parsedate_to_datetime

import requests

_lock = threading.Lock()
_cache = {}  # key -> (ts, items)
TTL = 600  # 10 دقائق

HEADERS = {"User-Agent": "Mozilla/5.0"}


def fetch_news(query: str, limit: int = 6) -> list:
    """آخر عناوين الأخبار الحقيقية لاستعلام (اسم شركة/رمز) — من Google News بالعربية."""
    key = query.strip().lower()
    now = _time.time()
    c = _cache.get(key)
    if c and now - c[0] < TTL:
        return c[1]
    with _lock:
        c = _cache.get(key)
        if c and now - c[0] < TTL:
            return c[1]
        items = []
        try:
            url = ("https://news.google.com/rss/search"
                   f"?q={requests.utils.quote(query)}&hl=ar&gl=EG&ceid=EG:ar")
            r = requests.get(url, headers=HEADERS, timeout=10)
            if r.status_code == 200:
                root = ET.fromstring(r.content)
                for item in root.iter("item"):
                    title = (item.findtext("title") or "").strip()
                    link = (item.findtext("link") or "").strip()
                    pub_raw = (item.findtext("pubDate") or "").strip()
                    source = (item.findtext("source") or "").strip()
                    if not title:
                        continue
                    pub = ""
                    try:
                        pub = parsedate_to_datetime(pub_raw).strftime("%Y-%m-%d")
                    except Exception:
                        pub = pub_raw[:16]
                    items.append({"title": title, "link": link, "pub": pub, "source": source})
                    if len(items) >= limit:
                        break
        except Exception:
            pass
        _cache[key] = (now, items)
        return items
