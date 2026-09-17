"""كشف أنماط الشموع اليابانية (موسّع) — انعكاسية واستمرارية.

يوفّر:
- detect_last(df): أحدث نمط على آخر شمعة/شمعتين.
- pattern_series(df): عمودان pat_bull / pat_bear لكل شمعة (لرسم العلامات على الشارت).
"""


def _c(o, c, h, l):
    return dict(o=float(o), c=float(c), h=float(h), l=float(l),
                body=abs(float(c) - float(o)), rng=(float(h) - float(l)) or 1e-9,
                up=float(c) >= float(o))


def _patterns_at(rows, i):
    """يكشف النماذج عند الشمعة i (باستخدام آخر 3 شموع)."""
    out = []
    if i < 3:
        return out
    p1 = _c(rows[i - 2]["Open"], rows[i - 2]["Close"], rows[i - 2]["High"], rows[i - 2]["Low"])
    p2 = _c(rows[i - 1]["Open"], rows[i - 1]["Close"], rows[i - 1]["High"], rows[i - 1]["Low"])
    p3 = _c(rows[i]["Open"], rows[i]["Close"], rows[i]["High"], rows[i]["Low"])

    # مطرقة / رجل معلقة
    lower3 = min(p3["o"], p3["c"]) - p3["l"]
    upper3 = p3["h"] - max(p3["o"], p3["c"])
    if p3["body"] <= 0.35 * p3["rng"] and lower3 >= 2 * p3["body"] and upper3 <= 0.3 * p3["rng"]:
        out.append(("Hammer (مطرقة)" if not p2["up"] else "Hanging Man (رجل معلقة)",
                    "bullish" if not p2["up"] else "bearish"))
    # شهاب / مطرقة مقلوبة
    if p3["body"] <= 0.35 * p3["rng"] and upper3 >= 2 * p3["body"] and lower3 <= 0.3 * p3["rng"]:
        out.append(("Shooting Star (شهاب)" if p2["up"] else "Inverted Hammer (مطرقة مقلوبة)",
                    "bearish" if p2["up"] else "bullish"))
    # ابتلاع
    if (not p1["up"]) and p3["up"] and p3["c"] >= p1["o"] and p3["o"] <= p1["c"] and p3["body"] > p1["body"]:
        out.append(("Bullish Engulfing (ابتلاع شرائي)", "bullish"))
    if p1["up"] and (not p3["up"]) and p3["c"] <= p1["o"] and p3["o"] >= p1["c"] and p3["body"] > p1["body"]:
        out.append(("Bearish Engulfing (ابتلاع بيعي)", "bearish"))
    # Harami
    if (not p1["up"]) and p3["up"] and p3["o"] > p1["c"] and p3["c"] < p1["o"]:
        out.append(("Bullish Harami (هرامي شرائي)", "bullish"))
    if p1["up"] and (not p3["up"]) and p3["o"] < p1["c"] and p3["c"] > p1["o"]:
        out.append(("Bearish Harami (هرامي بيعي)", "bearish"))
    # نجمة الصباح/المساء (3 شموع)
    if (not p1["up"]) and p2["body"] <= 0.4 * p2["rng"] and p3["up"] and p3["c"] > (p1["o"] + p1["c"]) / 2:
        out.append(("Morning Star (نجمة الصباح)", "bullish"))
    if p1["up"] and p2["body"] <= 0.4 * p2["rng"] and (not p3["up"]) and p3["c"] < (p1["o"] + p1["c"]) / 2:
        out.append(("Evening Star (نجمة المساء)", "bearish"))
    # ثلاثة جنود بيض / غربان سود
    if p1["up"] and p2["up"] and p3["up"] and p3["c"] > p2["c"] > p1["c"]:
        out.append(("Three White Soldiers (ثلاثة جنود بيض)", "bullish"))
    if (not p1["up"]) and (not p2["up"]) and (not p3["up"]) and p3["c"] < p2["c"] < p1["c"]:
        out.append(("Three Black Crows (ثلاثة غربان سود)", "bearish"))
    # خط الاختراق / الغيمة الداكنة
    if (not p1["up"]) and p3["up"] and p3["c"] > (p1["o"] + p1["c"]) / 2 and p3["c"] < p1["o"]:
        out.append(("Piercing Line (خط الاختراق)", "bullish"))
    if p1["up"] and (not p3["up"]) and p3["c"] < (p1["o"] + p1["c"]) / 2 and p3["c"] > p1["o"]:
        out.append(("Dark Cloud Cover (غطاء سحابي داكن)", "bearish"))
    # دوجي
    if p3["body"] <= 0.1 * p3["rng"]:
        out.append(("Doji (دوجي — حيرة)", "neutral"))
    return out


def detect_last(df):
    if df is None or len(df) < 4:
        return {"pattern": None, "type": "neutral", "desc": ""}
    rows = [{k: r[k] for k in ("Open", "High", "Low", "Close")} for _, r in df.tail(5).iterrows()]
    found = _patterns_at(rows, len(rows) - 1)
    if not found:
        return {"pattern": None, "type": "neutral", "desc": ""}
    name, typ = found[0]
    return {"pattern": name, "type": typ, "all": found}


def pattern_series(df):
    """يضيف عمودي pat_bull / pat_bear (منطقي) لكل شمعة."""
    df = df.copy()
    df["pat_bull"] = False
    df["pat_bear"] = False
    if df is None or len(df) < 5:
        return df
    rows = [{k: r[k] for k in ("Open", "High", "Low", "Close")} for _, r in df.iterrows()]
    bull = [False] * len(rows)
    bear = [False] * len(rows)
    for i in range(3, len(rows)):
        for name, typ in _patterns_at(rows, i):
            if typ == "bullish":
                bull[i] = True
            elif typ == "bearish":
                bear[i] = True
    df["pat_bull"] = bull
    df["pat_bear"] = bear
    return df

def recent_patterns(df, lookback: int = 60, limit: int = 10) -> list:
    """أحدث الأنماط المكتشفة (مرتبة من الأحدث) — [{date, pattern, type}]."""
    if df is None or len(df) < 5:
        return []
    d = df.tail(lookback)
    rows = [{k: r[k] for k in ("Open", "High", "Low", "Close")} for _, r in d.iterrows()]
    idxs = list(d.index)
    out = []
    for i in range(3, len(rows)):
        for name, typ in _patterns_at(rows, i):
            out.append({"date": str(idxs[i])[:10], "pattern": name, "type": typ})
    return out[-limit:][::-1]
