"""تحليل معنويات الأخبار — قائمة كلمات مالية (عربي + إنجليزي).

تقدير تقريبي (lexicon-based) وصريح: لا يُعدّ تحليلاً لغوياً عميقاً، لكنه يعطي انطباعاً
سريعاً عن نبرة عناوين الأخبار (إيجابي/سلبي/محايد).
"""

POS = ["ارتفاع", "صعود", "نمو", "أرباح", "قفزة", "تحسن", "توزيعات", "توسع", "زيادة",
       "ربح", "إيجابي", "قوي", "استحواذ", "عقود", "تفوق", "قفز", "يرتفع", "تجاوز",
       "surge", "rise", "growth", "profit", "gain", "beat", "record", "dividend",
       "bullish", "upgrade", "strong", "wins", "expansion", "jump", "soar"]
NEG = ["انخفاض", "هبوط", "خسارة", "تراجع", "أزمة", "ديون", "انكماش", "ضعف", "سلبي",
       "تخفيض", "تحذير", "خسائر", "توقف", "ينخفض", "تفشل", "تضرر",
       "decline", "fall", "drop", "loss", "debt", "crisis", "weak", "downgrade",
       "bearish", "cut", "warning", "miss", "slump", "plunge", "fraud"]


def score_text(text: str):
    t = (text or "").lower()
    pos = sum(1 for w in POS if w.lower() in t)
    neg = sum(1 for w in NEG if w.lower() in t)
    if pos > neg:
        return "إيجابي", 1
    if neg > pos:
        return "سلبي", -1
    return "محايد", 0


def analyze_news(items: list) -> dict:
    rows = []
    total = 0
    for it in items or []:
        label, s = score_text(it.get("title", ""))
        total += s
        rows.append({"title": it.get("title", ""), "pub": it.get("pub", ""),
                     "source": it.get("source", ""), "link": it.get("link", ""),
                     "sentiment": label, "score": s})
    overall = "إيجابية" if total > 0 else ("سلبية" if total < 0 else "محايدة")
    return {"overall": overall, "score": total, "count": len(rows), "rows": rows}
