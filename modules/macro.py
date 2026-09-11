"""طبقة الترابط العالمي (Intermarket) — السياق الذي تحكم به الأسواق العالمية قرارك المصري.

كل البيانات حقيقية ومجانية من Yahoo Finance بلا أي تأخير عملي:
- الدولار/الجنيه (EGP=X) — القوة الشرائية والتحوط
- نفط برنت (BZ=F) — قطاع البترول وتكاليف النقل
- الذهب (GC=F) — مقياس طلب الملاذ الآمن
- S&P 500 (^GSPC) — الشهية العالمية للمخاطرة
- عائد أمريكي 10 سنوات (^TNX) — جاذبية السندات مقابل الأسهم الناشئة
- MSCI أسواق ناشئة (EEM) — نبض تدفقات الأجانب نحو أسواق مثل مصر

الدور: قبل أي قرار شراء — هل البيئة العالمية والنقدية تدعم السوق المصري أم تعانده؟
"""
import threading
import time as _time

import pandas as pd
import yfinance as yf

_lock = threading.Lock()
_cache = {"ts": 0.0, "data": {}}
TTL = 600  # 10 دقائق

INSTRUMENTS = [
    ("EGP=X", "الدولار/الجنيه"),
    ("BZ=F", "نفط برنت"),
    ("GC=F", "الذهب"),
    ("^GSPC", "S&P 500"),
    ("^TNX", "عائد أمريكي 10س"),
    ("EEM", "أسواق ناشئة"),
]


def fetch_macro(force: bool = False) -> dict:
    """{ticker: {label, value, day_pct, wk_pct}} — كاش 10 دقائق."""
    now = _time.time()
    if not force and _cache["data"] and now - _cache["ts"] < TTL:
        return _cache["data"]
    with _lock:
        now = _time.time()
        if not force and _cache["data"] and now - _cache["ts"] < TTL:
            return _cache["data"]
        data = {}
        try:
            tickers = [t for t, _ in INSTRUMENTS]
            df = yf.download(tickers, period="1mo", interval="1d",
                             group_by="ticker", auto_adjust=True, progress=False)
            for ticker, label in INSTRUMENTS:
                try:
                    sub = df[ticker]["Close"].dropna()
                    if len(sub) < 6:
                        continue
                    last = float(sub.iloc[-1])
                    prev = float(sub.iloc[-2])
                    wk = float(sub.iloc[-6])
                    data[ticker] = {
                        "label": label, "value": last,
                        "day_pct": (last - prev) / prev * 100 if prev else 0.0,
                        "wk_pct": (last - wk) / wk * 100 if wk else 0.0,
                    }
                except Exception:
                    continue
        except Exception:
            pass
        if data:
            _cache.update(ts=now, data=data)
        return data


def _yield_display(v: float) -> float:
    """^TNX قد يُسعّر كنسبة أو 10×النسبة حسب المصدر — نوحّد العرض."""
    return v / 10 if v > 20 else v


def regime(data: dict) -> dict:
    """تصنيف البيئة العامة: داعمة للمخاطرة / محايدة / ضاغطة — من 3 أدلة مستقلة."""
    score = 0
    sp, eem, yld = data.get("^GSPC"), data.get("EEM"), data.get("^TNX")
    if sp:
        score += 1 if sp["day_pct"] > 0 else -1
    if eem:
        score += 1 if eem["wk_pct"] > 0 else -1
    if yld:
        score += -1 if yld["wk_pct"] > 1 else (1 if yld["wk_pct"] < -1 else 0)
    if score >= 2:
        return {"label": "🌍 بيئة داعمة للمخاطرة", "color": "#00c853",
                "desc": "المؤشرات العالمية تساند تدفقات إيجابية نحو الأسواق الناشئة ومنها مصر — مناسب لتفعيل خطط الشراء"}
    if score <= -2:
        return {"label": "🔴 بيئة ضاغطة على المخاطرة", "color": "#ff5c76",
                "desc": "توتر عالمي يضغط على الأسواق الناشئة — خفّف الأحمال الجديدة وفعّل الأوامر بحذر فقط"}
    return {"label": "⚪ بيئة محايدة", "color": "#90a4ae",
            "desc": "لا دعم ولا ضغط عالمي واضح — اعتمد على تحليل السهم نفسه ومعاييره الخاصة"}


def macro_signals(data: dict) -> list:
    """قراءة السياق: [(tone, نص)] — tone: pos / neg / neg_mixed."""
    sig = []
    fx = data.get("EGP=X")
    if fx:
        w = fx["wk_pct"]
        if w >= 0.5:
            sig.append(("neg_mixed", f"الجنيه يفقد {w:.2f}% أمام الدولار خلال أسبوع ({fx['value']:,.2f}) — ضغط على المستوردين والمديونين بالدولار، بينما العقاري والتصدير يتحوطان بالأصول الدولارية"))
        elif w <= -0.5:
            sig.append(("pos", f"الجنيه يتعزز {abs(w):.2f}% ({fx['value']:,.2f}) — إيجابي للقوة الشرائية والشركات ذات التكاليف المستوردة"))
    oil = data.get("BZ=F")
    if oil and oil["wk_pct"] >= 3:
        sig.append(("neg_mixed", f"برنت صاعد {oil['wk_pct']:+.2f}% أسبوعياً — إيجابي لقطاع البترول المصري، وضغط على تكاليف النقل والكيمائيات"))
    elif oil and oil["wk_pct"] <= -3:
        sig.append(("neg_mixed", f"برنت يهبط {oil['wk_pct']:+.2f}% أسبوعياً — ضغط على أسهم البترول، وتخفيف لتكاليف المستوردين"))
    sp, eem = data.get("^GSPC"), data.get("EEM")
    if sp and eem:
        if sp["day_pct"] < -1 or eem["wk_pct"] < -2:
            sig.append(("neg", f"Risk-off عالمي: S&P {sp['day_pct']:+.2f}% اليوم والناشئة {eem['wk_pct']:+.2f}% أسبوعياً — تراجع التدفقات الأجنبية يضغط على EGX"))
        elif sp["day_pct"] > 0.5 and eem["wk_pct"] > 0:
            sig.append(("pos", f"Risk-on: S&P {sp['day_pct']:+.2f}% والناشئة {eem['wk_pct']:+.2f}% — بيئة تدعم تدفقات أجنبية نحو أسواق مثل مصر"))
    yld = data.get("^TNX")
    if yld and yld["wk_pct"] >= 3:
        sig.append(("neg", f"عائد السندات الأمريكية 10 سنوات يرتفع ({_yield_display(yld['value']):.2f}%) — أموال تهاجر من الأسواق الناشئة نحو السندات وضغط على تقييمات الأسهم"))
    gold, eem2 = data.get("GC=F"), data.get("EEM")
    if gold and eem2 and gold["wk_pct"] > 1.5 and eem2["wk_pct"] < 0:
        sig.append(("neg_mixed", f"الذهب يرتفع {gold['wk_pct']:+.2f}% مع تراجع الناشئة ({eem2['wk_pct']:+.2f}%) — طلب ملاذ آمن، إشارة حذر عام"))
    return sig


_SECTOR_IMPACT = [
    ("عقاري|ملاذ عقاري", "الأصول العقارية تحوط طبيعي ضد ضعف الجنيه — قوي عندما يهبط الجنيه"),
    ("بنوك|مالية", "مستفيد من ارتفاع الفائدة، وأرباحه بالجنيه تتكيف مع التضخم"),
    ("بترول|نفط|طاقة", "يتأثر مباشرة بأسعار برنت العالمية — راقب حركة النفط"),
    ("أسمدة|كيماويات|أسمنت|تعدين|ألومنيوم", "مصدّر بإيرادات دولارية — يستفيد من ضعف الجنيه"),
    ("أدوية|صحة|استهلاك|تجارة", "مكونات مستوردة — ضعف الجنيه يرفع تكاليفه ويضغط بالهوامش"),
    ("اتصالات|تكنولوجيا", "تقييماته حساسة لعائد السندات الأمريكية — ارتفاع العائد يضغط عليها"),
    ("فنادق|سياحة", "تدفقات سياحية دولارية — يستفيد مع تعزيز جاذبية مصر للسائح"),
]


def holding_impact(sector: str) -> str:
    """أثر السياق العالمي على قطاع سهم بعينه."""
    for pat, note in _SECTOR_IMPACT:
        for p in pat.split("|"):
            if p in sector:
                return note
    return "تأثر غير مباشر — راقب الدولار والفائدة العالمية"
