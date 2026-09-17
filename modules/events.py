"""تقويم الأحداث — التوزيعات وتجزئة الأسهم والمواعيد القادمة (من Yahoo Finance).

ملاحظة: تغطية بيانات EGX على Yahoo محدودة — تُعرض المتاح فقط.
"""
from datetime import datetime, timezone


def _fmt_ts(ts):
    try:
        return datetime.fromtimestamp(int(ts), tz=timezone.utc).strftime("%Y-%m-%d")
    except Exception:
        return None


def get_events(symbol: str, ticker=None) -> dict:
    if ticker is None:
        import yfinance as yf
        ticker = yf.Ticker(symbol)

    out = {"dividends": [], "splits": [], "upcoming": []}
    try:
        divs = ticker.dividends
        if divs is not None and len(divs):
            for dt, v in list(divs.items())[-10:]:
                out["dividends"].append({"date": str(dt)[:10], "value": round(float(v), 4)})
    except Exception:
        pass
    try:
        spl = ticker.splits
        if spl is not None and len(spl):
            for dt, v in list(spl.items())[-5:]:
                out["splits"].append({"date": str(dt)[:10], "ratio": float(v)})
    except Exception:
        pass
    try:
        info = ticker.info or {}
        exd = info.get("exDividendDate")
        if exd:
            out["upcoming"].append({"type": "تاريخ استحقاق التوزيعات القادم", "date": _fmt_ts(exd)})
        dd = info.get("dividendDate")
        if dd:
            out["upcoming"].append({"type": "تاريخ صرف التوزيعات", "date": _fmt_ts(dd)})
        et = info.get("earningsTimestamp") or info.get("earningsTimestampStart")
        if et:
            out["upcoming"].append({"type": "إعلان الأرباح المتوقع", "date": _fmt_ts(et)})
    except Exception:
        pass
    return out
