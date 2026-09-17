"""نظريات التحليل الفني الكلاسيكية — محسوبة على بيانات حقيقية.

- نظرية داو (Dow Theory): هيكل الاتجاه (قمم وقيعان صاعدة/هابطة).
- موجات إليوت (Elliott Wave): تصنيف عملي تقريبي (استرشادي).
- مستويات فيبوناتشي: ارتدادات وامتدادات.
كل النتائج استرشادية — لا تُعدّ نصيحة استثمارية.
"""
import pandas as pd


def _pivots(df: pd.DataFrame, window: int = 5):
    """قمم وقيعان محورية (swing highs/lows) — قوائم (index, price)."""
    highs, lows = [], []
    h = df["High"]; l = df["Low"]
    for i in range(window, len(df) - window):
        if h.iloc[i] == h.iloc[i - window:i + window + 1].max():
            highs.append((df.index[i], float(h.iloc[i])))
        if l.iloc[i] == l.iloc[i - window:i + window + 1].min():
            lows.append((df.index[i], float(l.iloc[i])))
    return highs, lows


def dow_analysis(df: pd.DataFrame, lookback: int = 120) -> dict:
    """نظرية داو: تحديد الاتجاه الأساسي من هيكل القمم والقيعان."""
    if df is None or len(df) < 40:
        return {"error": "بيانات غير كافية"}
    d = df.tail(lookback)
    highs, lows = _pivots(d)
    close = float(d["Close"].iloc[-1])

    hs = [p for _, p in highs[-3:]]
    ls = [p for _, p in lows[-3:]]

    hh = len(hs) >= 2 and hs[-1] > hs[-2]
    hl = len(ls) >= 2 and ls[-1] > ls[-2]
    lh = len(hs) >= 2 and hs[-1] < hs[-2]
    ll = len(ls) >= 2 and ls[-1] < ls[-2]

    if hh and hl:
        trend, status = "صاعد (Higher Highs + Higher Lows)", "bullish"
        advice = "الاتجاه الأساسي صاعد — الشراء مع الاتجاه أفضل من البيع ضده."
    elif lh and ll:
        trend, status = "هابط (Lower Highs + Lower Lows)", "bearish"
        advice = "الاتجاه الأساسي هابط — تجنّب الشراء وانتظر انعكاساً مؤكداً."
    else:
        trend, status = "عرضي / متذبذب", "neutral"
        advice = "لا هيكل واضح — انتظر كسر نطاق العرض قبل الدخول."

    return {
        "trend": trend, "status": status, "advice": advice,
        "last_highs": round(hs[-1], 2) if hs else None,
        "last_lows": round(ls[-1], 2) if ls else None,
        "close": round(close, 2),
    }


def elliott_analysis(df: pd.DataFrame, lookback: int = 150) -> dict:
    """موجات إليوت — تصنيف عملي تقريبي (استرشادي، وليس بديلاً عن التحليل البشري)."""
    if df is None or len(df) < 60:
        return {"error": "بيانات غير كافية"}
    d = df.tail(lookback)
    highs, lows = _pivots(d)
    close = float(d["Close"].iloc[-1])

    # آخر قمة وقاع رئيسيين — نستنتج إن كنا في موجة اندفاعية صاعدة أو تصحيحية
    last_high = highs[-1][1] if highs else close
    last_low = lows[-1][1] if lows else close
    # موضع السعر من آخر موجة
    wave_range = last_high - last_low
    pos = (close - last_low) / wave_range if wave_range > 0 else 0.5

    if close > last_high * 0.99:
        label, note = "قمة موجية (نهاية موجة صاعدة محتملة)", "قد تكون نهاية موجة اندفاعية — حذر من تصحيح (الموجات 2 أو 4)."
        status = "caution"
    elif pos < 0.618 and close < last_high:
        label, note = "تصحيح موجي (موجة 2 أو 4)", "السعر في منطقة تصحيح — فرصة دخول إذا اكتمل النموذج مع تأكيد حجم."
        status = "corrective"
    elif close > last_low * 1.05:
        label, note = "موجة اندفاعية صاعدة (موجة 1/3/5)", "السعر يتحرك صعوداً بعد قاع — استمرار محتمل بشرط عدم كسر القاع السابق."
        status = "impulse_up"
    else:
        label, note = "غير محدد بوضوح", "البنية الموجية غير واضحة — لا تعتمد على إليوت هنا وحدها."
        status = "unclear"

    return {
        "label": label, "note": note, "status": status,
        "last_high": round(last_high, 2), "last_low": round(last_low, 2),
        "position_in_wave": round(pos * 100, 1),
        "disclaimer": "موجات إليوت تقديرية بطبيعتها — استخدمها كدعم لا كقرار وحيد.",
    }


def fibonacci_levels(df: pd.DataFrame, lookback: int = 120) -> dict:
    """مستويات فيبوناتشي (ارتداد) من آخر قمة وقاع رئيسيين."""
    if df is None or len(df) < 40:
        return {"error": "بيانات غير كافية"}
    d = df.tail(lookback)
    high = float(d["High"].max())
    low = float(d["Low"].min())
    diff = high - low
    if diff <= 0:
        return {"error": "نطاق صفري"}
    levels = {}
    for ratio in (0.236, 0.382, 0.5, 0.618, 0.786):
        levels[f"{ratio*100:.1f}%"] = round(high - diff * ratio, 2)
    return {"swing_high": round(high, 2), "swing_low": round(low, 2), "levels": levels}
