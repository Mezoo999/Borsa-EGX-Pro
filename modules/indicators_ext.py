"""مؤشرات متقدمة إضافية: Ichimoku، Keltner، Donchian، Aroon، TRIX،
Ultimate Oscillator، Chaikin Money Flow، Elder Force Index، Squeeze، Pivot Points.
"""
import numpy as np
import pandas as pd


def _atr(high, low, close, n=14):
    tr = pd.concat([(high - low), (high - close.shift()).abs(), (low - close.shift()).abs()], axis=1).max(axis=1)
    return tr.rolling(n).mean()


def add_advanced(df: pd.DataFrame) -> pd.DataFrame:
    df = df.copy()
    high, low, close, vol = df["High"], df["Low"], df["Close"], df["Volume"]

    # Ichimoku
    tenkan = (high.rolling(9).max() + low.rolling(9).min()) / 2
    kijun = (high.rolling(26).max() + low.rolling(26).min()) / 2
    df["ICH_Tenkan"] = tenkan
    df["ICH_Kijun"] = kijun
    df["ICH_SpanA"] = ((tenkan + kijun) / 2).shift(26)
    df["ICH_SpanB"] = ((high.rolling(52).max() + low.rolling(52).min()) / 2).shift(26)
    df["ICH_Chikou"] = close.shift(-26)

    # Keltner
    ema20 = close.ewm(span=20, adjust=False).mean()
    atr = _atr(high, low, close, 14)
    df["KC_Upper"] = ema20 + 2 * atr
    df["KC_Lower"] = ema20 - 2 * atr

    # Donchian
    df["DC_Upper"] = high.rolling(20).max()
    df["DC_Lower"] = low.rolling(20).min()
    df["DC_Mid"] = (df["DC_Upper"] + df["DC_Lower"]) / 2

    # Aroon
    n = 25
    df["Aroon_Up"] = high.rolling(n + 1).apply(lambda x: (int(np.argmax(x)) / n) * 100, raw=True)
    df["Aroon_Dn"] = low.rolling(n + 1).apply(lambda x: (int(np.argmin(x)) / n) * 100, raw=True)

    # TRIX
    e1 = close.ewm(span=15, adjust=False).mean()
    e2 = e1.ewm(span=15, adjust=False).mean()
    e3 = e2.ewm(span=15, adjust=False).mean()
    df["TRIX"] = e3.pct_change() * 100

    # Ultimate Oscillator
    bp = close - pd.concat([low, close.shift()], axis=1).min(axis=1)
    tr = pd.concat([high, close.shift()], axis=1).max(axis=1) - pd.concat([low, close.shift()], axis=1).min(axis=1)
    a1 = bp.rolling(7).sum() / tr.rolling(7).sum()
    a2 = bp.rolling(14).sum() / tr.rolling(14).sum()
    a3 = bp.rolling(28).sum() / tr.rolling(28).sum()
    df["UO"] = 100 * (4 * a1 + 2 * a2 + a3) / 7

    # Chaikin Money Flow (20)
    mfm = ((close - low) - (high - close)) / (high - low).replace(0, np.nan)
    mfv = mfm * vol
    df["CMF"] = mfv.rolling(20).sum() / vol.rolling(20).sum()

    # Elder Force Index
    df["ForceIndex"] = ((close - close.shift()) * vol).ewm(span=13, adjust=False).mean()

    # Squeeze (Bollinger داخل Keltner)
    bb_u = close.rolling(20).mean() + 2 * close.rolling(20).std()
    bb_l = close.rolling(20).mean() - 2 * close.rolling(20).std()
    df["Squeeze"] = (bb_u < df["KC_Upper"]) & (bb_l > df["KC_Lower"])

    return df


def ichimoku_signal(df: pd.DataFrame) -> dict:
    """إشارات Ichimoku: السعر مقابل السحابة + تقاطع Tenkan/Kijun + لون السحابة."""
    if df is None or len(df) < 60 or "ICH_SpanA" not in df.columns:
        return {"status": "unclear", "note": "بيانات غير كافية", "signals": []}
    last = df.iloc[-1]
    close = float(last["Close"])
    a, b = last.get("ICH_SpanA"), last.get("ICH_SpanB")
    tk, kj = last.get("ICH_Tenkan"), last.get("ICH_Kijun")
    sigs = []
    status = "neutral"
    if pd.notna(a) and pd.notna(b):
        top, bot = max(a, b), min(a, b)
        if close > top:
            sigs.append("السعر فوق السحابة (اتجاه صاعد)")
            status = "bullish"
        elif close < bot:
            sigs.append("السعر تحت السحابة (اتجاه هابط)")
            status = "bearish"
        else:
            sigs.append("السعر داخل السحابة (تذبذب)")
    if pd.notna(tk) and pd.notna(kj):
        if tk > kj:
            sigs.append("Tenkan فوق Kijun (زخم صاعد)")
            status = "bullish" if status != "bearish" else status
        else:
            sigs.append("Tenkan تحت Kijun (زخم هابط)")
    return {"status": status, "signals": sigs}


def pivot_points(df: pd.DataFrame) -> dict:
    """نقاط البيفوت (Classic + Camarilla) من آخر جلسة."""
    if df is None or len(df) < 2:
        return {}
    last = df.iloc[-1]
    h, l, c = float(last["High"]), float(last["Low"]), float(last["Close"])
    p = (h + l + c) / 3
    classic = {
        "P": round(p, 2),
        "R1": round(2 * p - l, 2), "R2": round(p + (h - l), 2), "R3": round(h + 2 * (p - l), 2),
        "S1": round(2 * p - h, 2), "S2": round(p - (h - l), 2), "S3": round(l - 2 * (h - p), 2),
    }
    rng = (h - l)
    camarilla = {
        "R1": round(c + rng * 1.1 / 12, 2), "R2": round(c + rng * 1.1 / 6, 2), "R3": round(c + rng * 1.1 / 4, 2),
        "S1": round(c - rng * 1.1 / 12, 2), "S2": round(c - rng * 1.1 / 6, 2), "S3": round(c - rng * 1.1 / 4, 2),
    }
    return {"classic": classic, "camarilla": camarilla}
