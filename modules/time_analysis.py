"""التحليل الزمني — أنماط التوقيت التاريخية (مبنية على بيانات فعلية).

يساعد المستثمر على معرفة: أي أيام الأسبوع أفضل تاريخياً؟ أي شهور أقوى؟
وما نسبة الأيام الرابحة إجمالاً؟ — كلها أرقام حقيقية من التاريخ، لا توقعات.
"""
import pandas as pd

DAY_NAMES = {6: "الأحد", 0: "الاثنين", 1: "الثلاثاء", 2: "الأربعاء", 3: "الخميس"}
MONTH_NAMES = ["يناير", "فبراير", "مارس", "أبريل", "مايو", "يونيو",
               "يوليو", "أغسطس", "سبتمبر", "أكتوبر", "نوفمبر", "ديسمبر"]


def _with_ret(df: pd.DataFrame) -> pd.DataFrame:
    d = df.copy()
    d["ret"] = d["Close"].pct_change()
    return d


def day_of_week_stats(df: pd.DataFrame) -> pd.DataFrame:
    """متوسط العائد ونسبة الأيام الرابحة لكل يوم تداول (الأحد-الخميس)."""
    if df is None or len(df) < 10:
        return pd.DataFrame()
    d = _with_ret(df)
    rows = []
    for dow, name in sorted(DAY_NAMES.items()):
        sub = d[d.index.dayofweek == dow]["ret"].dropna()
        if len(sub) >= 2:
            rows.append({
                "اليوم": name,
                "متوسط العائد %": round(float(sub.mean()) * 100, 2),
                "نسبة الأيام الرابحة %": round(float((sub > 0).mean()) * 100, 1),
                "عدد الجلسات": int(len(sub)),
            })
    return pd.DataFrame(rows)


def monthly_stats(df: pd.DataFrame) -> pd.DataFrame:
    """متوسط العائد الشهري (موسمية)."""
    if df is None or len(df) < 10:
        return pd.DataFrame()
    d = _with_ret(df)
    rows = []
    for m in range(1, 13):
        sub = d[d.index.month == m]["ret"].dropna()
        if len(sub) >= 2:
            rows.append({
                "الشهر": MONTH_NAMES[m - 1],
                "متوسط العائد %": round(float(sub.mean()) * 100, 2),
                "نسبة الأيام الرابحة %": round(float((sub > 0).mean()) * 100, 1),
                "عدد الجلسات": int(len(sub)),
            })
    return pd.DataFrame(rows)


def summary(df: pd.DataFrame) -> dict:
    """ملخص زمني عام."""
    if df is None or len(df) < 10:
        return {}
    d = _with_ret(df)
    rets = d["ret"].dropna()
    pos_days = int((rets > 0).sum())
    best = d.loc[rets.idxmax()] if len(rets) else None
    worst = d.loc[rets.idxmin()] if len(rets) else None
    return {
        "إجمالي الجلسات": int(len(rets)),
        "أيام رابحة": pos_days,
        "أيام خاسرة": int(len(rets) - pos_days),
        "نسبة الأيام الرابحة %": round(float((rets > 0).mean()) * 100, 1),
        "متوسط العائد اليومي %": round(float(rets.mean()) * 100, 2),
        "أفضل يوم": (best.name.strftime("%Y-%m-%d"), round(float(best["ret"]) * 100, 2)) if best is not None else None,
        "أسوأ يوم": (worst.name.strftime("%Y-%m-%d"), round(float(worst["ret"]) * 100, 2)) if worst is not None else None,
    }
