"""هيكل السوق الاحترافي (Market Structure / Smart Money Concepts).

- قمم وقيعان محورية وتصنيفها HH / HL / LH / LL.
- كسر الهيكل (BOS = Break of Structure) لتأكيد استمرار الاتجاه.
- تغيّر الشخصية (CHoCH = Change of Character) — إشارة انعكاس مبكّرة.
- مناطق دعم/مقاومة من تجميع القمم والقيعان المحورية.
"""
import pandas as pd


def _swings(df: pd.DataFrame, left: int = 2, right: int = 2):
    highs, lows = [], []
    h, l = df["High"].values, df["Low"].values
    n = len(df)
    for i in range(left, n - right):
        if h[i] == max(h[i - left:i + right + 1]):
            highs.append((i, float(h[i])))
        if l[i] == min(l[i - left:i + right + 1]):
            lows.append((i, float(l[i])))
    return highs, lows


def analyze_structure(df: pd.DataFrame, lookback: int = 150, left: int = 2, right: int = 2) -> dict:
    if df is None or len(df) < 30:
        return {"error": "بيانات غير كافية"}
    d = df.tail(lookback).reset_index(drop=True)
    highs, lows = _swings(d, left, right)
    close = float(d["Close"].iloc[-1])

    hl = [("HH" if highs[k][1] > highs[k - 1][1] else "LH") for k in range(1, len(highs))]
    ll = [("HL" if lows[k][1] > lows[k - 1][1] else "LL") for k in range(1, len(lows))]
    last_high_label = hl[-1] if hl else "-"
    last_low_label = ll[-1] if ll else "-"

    last_swing_high = highs[-1][1] if highs else None
    last_swing_low = lows[-1][1] if lows else None

    bos = choch = None
    if last_swing_high and close > last_swing_high:
        bos = "bullish"
        if last_high_label == "LH":
            choch = "bullish"
    if last_swing_low and close < last_swing_low:
        bos = "bearish"
        if last_low_label == "HL":
            choch = "bearish"

    if last_high_label == "HH" and last_low_label == "HL":
        trend = "صاعد (قمم وقيعان أعلى)"
    elif last_high_label == "LH" and last_low_label == "LL":
        trend = "هابط (قمم وقيعان أدنى)"
    else:
        trend = "عرضي / انتقالي"

    return {
        "trend": trend,
        "last_high_label": last_high_label, "last_low_label": last_low_label,
        "last_swing_high": round(last_swing_high, 2) if last_swing_high else None,
        "last_swing_low": round(last_swing_low, 2) if last_swing_low else None,
        "bos": bos, "choch": choch, "close": round(close, 2),
        "highs": [(int(i), round(p, 2)) for i, p in highs[-5:]],
        "lows": [(int(i), round(p, 2)) for i, p in lows[-5:]],
    }


def sr_zones(df: pd.DataFrame, lookback: int = 150, tolerance: float = 0.015) -> list:
    """مناطق دعم/مقاومة من تجميع القمم والقيعان المحورية."""
    if df is None or len(df) < 30:
        return []
    highs, lows = _swings(df.tail(lookback))
    pts = sorted([p for _, p in highs] + [p for _, p in lows])
    zones = []
    for p in pts:
        placed = False
        for z in zones:
            if abs(p - z["level"]) / z["level"] <= tolerance:
                z["level"] = (z["level"] * z["count"] + p) / (z["count"] + 1)
                z["count"] += 1
                placed = True
                break
        if not placed:
            zones.append({"level": p, "count": 1})
    zones = [z for z in zones if z["count"] >= 2]
    zones.sort(key=lambda z: z["level"])
    close = float(df["Close"].iloc[-1])
    for z in zones:
        z["level"] = round(z["level"], 2)
        z["side"] = "مقاومة" if z["level"] > close else "دعم"
        z["distance_pct"] = round((z["level"] - close) / close * 100, 2)
    return zones
