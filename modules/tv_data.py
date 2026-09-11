"""طبقة الأسعار اللحظية الرسمية من TradingView (Scanner API).

هذا هو نفس المصدر الذي يقرأ منه موقع TradingView نفسه، فالأسعار تطابقه تماماً.
ملاحظة شفافة: البورصة المصرية نفسها تؤخر بياناتها ~15 دقيقة لغير المؤسسات،
وهذا التأخير ثابت في كل المنصات المجانية بما فيها TradingView نفسه.
"""
import threading
import time as _time

import requests

SCAN_URL = "https://scanner.tradingview.com/egypt/scan"
GLOBAL_URL = "https://scanner.tradingview.com/global/scan"
HEADERS = {"User-Agent": "Mozilla/5.0", "Content-Type": "application/json"}

_STOCK_COLUMNS = ["name", "description", "close", "change", "change_abs",
                  "volume", "market_cap_basic", "sector", "type"]
_INDEX_TICKERS = ["EGX:EGX30", "EGX:EGX70EWI", "EGX:EGX30TR", "EGX:EGX100"]

# ترجمة تصنيفات القطاعات العالمية من TradingView إلى العربية
SECTOR_AR = {
    "Banks": "بنوك",
    "Finance": "خدمات مالية",
    "Health Technology": "أدوية ورعاية صحية",
    "Health Services": "خدمات صحية",
    "Consumer Services": "خدمات استهلاكية",
    "Consumer Durables": "مستهلكات معيشية",
    "Consumer Non-Durables": "سلع استهلاكية",
    "Retail Trade": "تجارة وتجزئة",
    "Energy Minerals": "طاقة",
    "Non-Energy Minerals": "تعدين ومعادن",
    "Industrial Services": "خدمات صناعية",
    "Producer Manufacturing": "صناعة وتصنيع",
    "Process Industries": "صناعات تحويلية",
    "Technology Services": "تكنولوجيا",
    "Electronic Technology": "تكنولوجيا إلكترونية",
    "Communications": "اتصالات",
    "Transportation": "نقل وملاحة",
    "Utilities": "مرافق عامة",
    "Commercial Services": "خدمات تجارية",
    "Distribution Services": "توزيع وبيع",
    "Miscellaneous": "أخرى",
}

_lock = threading.Lock()
_stock_cache = {"ts": 0.0, "data": {}, "ok": False}
_index_cache = {"ts": 0.0, "data": {}, "ok": False}
STOCK_TTL = 45   # ثانية — أسعار الأسهم
INDEX_TTL = 60   # ثانية — المؤشرات


def _post_scan(url: str, payload: dict, timeout: int = 10):
    r = requests.post(url, json=payload, headers=HEADERS, timeout=timeout)
    r.raise_for_status()
    return r.json().get("data", []) or []


def _parse_stocks(rows: list) -> dict:
    out = {}
    for row in rows:
        try:
            d = row.get("d") or []
            if len(d) < 9 or d[8] != "stock":
                continue
            sym, desc, close, chg, chg_abs, vol, mcap, sector, _ = d[:9]
            if not sym or close is None:
                continue
            if sym.startswith("EGS") and sym[3:4].isdigit():
                continue  # سندات حكومية/شركات — ليست أسهم
            out[sym] = {
                "symbol": sym,
                "name_tv": desc or sym,
                "close": float(close),
                "change_pct": float(chg or 0),
                "change_abs": float(chg_abs or 0),
                "volume": int(vol or 0),
                "market_cap": float(mcap) if mcap else None,
                "sector": sector or "",
            }
        except Exception:
            continue
    return out


def snapshot(force: bool = False) -> dict:
    """كل أسهم EGX المتداولة فعلاً من TradingView — {symbol: row} بكاش 45 ثانية.

    عند فشل الاتصال تُرجع آخر نسخة محفوظة حتى لو تجاوزت مدة الكاش.
    """
    now = _time.time()
    c = _stock_cache
    if not force and c["ok"] and now - c["ts"] < STOCK_TTL:
        return c["data"]
    with _lock:
        now = _time.time()
        if not force and c["ok"] and now - c["ts"] < STOCK_TTL:
            return c["data"]
        try:
            rows = _post_scan(SCAN_URL, {
                "filter": [],
                "options": {"lang": "ar"},
                "markets": ["egypt"],
                "symbols": {"query": {"types": []}, "tickers": []},
                "columns": _STOCK_COLUMNS,
                "sort": {"sortBy": "TradesValue", "sortOrder": "desc"},
                "range": [0, 400],
            })
            data = _parse_stocks(rows)
            if data:
                c.update(ts=now, data=data, ok=True)
                return data
        except Exception:
            pass
        return c["data"]


def indices(force: bool = False) -> dict:
    """المؤشرات الرسمية EGX30 / EGX70 من TradingView — {key: row}."""
    now = _time.time()
    c = _index_cache
    if not force and c["ok"] and now - c["ts"] < INDEX_TTL:
        return c["data"]
    with _lock:
        now = _time.time()
        if not force and c["ok"] and now - c["ts"] < INDEX_TTL:
            return c["data"]
        try:
            rows = _post_scan(GLOBAL_URL, {
                "symbols": {"tickers": _INDEX_TICKERS, "query": {"types": []}},
                "columns": ["name", "description", "close", "change", "change_abs"],
                "options": {"lang": "ar"},
            })
            data = {}
            for row in rows:
                d = row.get("d") or []
                if len(d) >= 5 and d[2] is not None:
                    data[d[0]] = {
                        "name": d[0],
                        "title": d[1],
                        "value": float(d[2]),
                        "change_pct": float(d[3] or 0),
                        "change_abs": float(d[4] or 0),
                    }
            if data:
                c.update(ts=now, data=data, ok=True)
                return data
        except Exception:
            pass
        return c["data"]


def clear_cache():
    """تفريغ الكاش المحلي (يُستدعى من زر تحديث البيانات)."""
    with _lock:
        _stock_cache.update(ts=0.0, data={}, ok=False)
        _index_cache.update(ts=0.0, data={}, ok=False)


def one(symbol: str):
    """بيانات سهم واحد من اللقطة الحالية (يقبل COMI أو COMI.CA)."""
    return snapshot().get(symbol.replace(".CA", ""))


def stock_tier(symbol: str) -> str:
    """تصنيف آلي للسهم حسب القيمة السوقية الحقيقية من TradingView — بلا قوائم ثابتة يدوية."""
    row = one(symbol)
    if not row:
        return "متوسط"
    mcap = row.get("market_cap") or 0
    if mcap >= 30e9:
        return "مؤسسي قيادي 🏛️"
    if mcap >= 5e9:
        return "شركة كبيرة"
    if mcap >= 1e9:
        return "متوسط"
    return "مضاربي صغير ⚠️"


def get_registry() -> dict:
    """سجل الأسهم الحقيقي: {symbol.CA: {"name":.., "sector":.., "tv": row}}.

    الأسماء العربية المنقحة المحلية لها الأولوية، وتُستكمل بقية الأسماء
    والقطاعات من TradingView بالعربية — فلا توجد أسهم ميتة أو ناقصة.
    """
    from .data import AR_NAMES, SECTORS
    reg = {}
    for sym, row in snapshot().items():
        key = f"{sym}.CA"
        reg[key] = {
            "name": AR_NAMES.get(key) or row["name_tv"],
            "sector": SECTORS.get(key) or SECTOR_AR.get(row["sector"], "أخرى"),
            "tv": row,
        }
    return reg
