"""التحليل الزمني — أنماط التوقيت التاريخية (مبنية على بيانات فعلية).

يساعد المستثمر على معرفة: أي أيام الأسبوع أفضل تاريخياً؟ أي شهور أقوى؟
وما نسبة الأيام الرابحة إجمالاً؟ — كلها أرقام حقيقية من التاريخ، لا توقعات.
"""
import numpy as np
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


def run_lengths(df) -> dict:
    """متوسط وأطول مدة موجة صعود/هبوط متتالية (بأيام)."""
    if df is None or len(df) < 20:
        return {}
    d = _with_ret(df)
    s = np.sign(d["ret"].fillna(0).values)
    runs_up, runs_dn = [], []
    i, n = 0, len(s)
    while i < n:
        if s[i] == 0:
            i += 1
            continue
        j = i
        while j < n and s[j] == s[i]:
            j += 1
        (runs_up if s[i] > 0 else runs_dn).append(j - i)
        i = j
    return {
        "avg_up_run": round(float(np.mean(runs_up)), 1) if runs_up else None,
        "avg_down_run": round(float(np.mean(runs_dn)), 1) if runs_dn else None,
        "max_up_run": int(max(runs_up)) if runs_up else None,
        "max_down_run": int(max(runs_dn)) if runs_dn else None,
    }


def dominant_cycle(df, max_lag: int = 60) -> dict:
    """الدورة السائدة (بأيام) عبر الارتباط الذاتي للعوائد — استرشادي وصريح."""
    if df is None or len(df) < max_lag * 2:
        return {}
    rets = _with_ret(df)["ret"].dropna().values
    if len(rets) < max_lag * 2:
        return {}
    rets = rets - rets.mean()
    best_lag, best_corr = None, 0.0
    for lag in range(5, max_lag):
        a, b = rets[:-lag], rets[lag:]
        if len(a) < 30:
            continue
        c = float(np.corrcoef(a, b)[0, 1])
        if c > best_corr:
            best_corr, best_lag = c, lag
    if best_lag is None or best_corr < 0.08:
        return {"dominant_period": None, "correlation": round(best_corr, 3),
                "note": "لا دورة واضحة (العوائد شبه عشوائية)"}
    return {"dominant_period": best_lag, "correlation": round(best_corr, 3),
            "note": f"دورة تقريبية كل ~{best_lag} جلسة (ارتباط ضعيف = استرشادي فقط)"}


def quarterly_stats(df):
    """متوسط العائد لكل ربع سنوي."""
    if df is None or len(df) < 20:
        return pd.DataFrame()
    d = _with_ret(df)
    d["q"] = d.index.quarter
    rows = []
    for q in range(1, 5):
        sub = d[d["q"] == q]["ret"].dropna()
        if len(sub) >= 2:
            rows.append({"الربع": f"Q{q}", "متوسط العائد %": round(float(sub.mean()) * 100, 2),
                         "نسبة الأيام الرابحة %": round(float((sub > 0).mean()) * 100, 1),
                         "عدد الجلسات": int(len(sub))})
    return pd.DataFrame(rows)


def monthly_heatmap(df):
    """خريطة حرارية: صفوف = سنة، أعمدة = شهور (متوسط العائد %)."""
    if df is None or len(df) < 40:
        return pd.DataFrame()
    d = _with_ret(df).dropna(subset=["ret"])
    piv = d.pivot_table(index=d.index.year, columns=d.index.month, values="ret", aggfunc="mean") * 100
    piv = piv.round(2)
    piv.columns = [MONTH_NAMES[m - 1] for m in piv.columns]
    piv.index.name = "السنة"
    return piv
