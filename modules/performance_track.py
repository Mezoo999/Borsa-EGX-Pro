"""سجل الأداء — يقيس توصيات المنصة بالأرقام الحقيقية (لا كلام).

يحوّل سجل التوصيات (rec_log) إلى نتائج فعلية: ضرب الوقف / حققت الهدف / جارية،
ويحسب نسبة النجاح الفعلية ومتوسط العائد — دليل ملموس على أداء المنصة.
"""


def classify(rec: dict, price: float | None):
    entry = float(rec.get("entry", 0) or 0)
    stop = float(rec.get("stop", 0) or 0)
    t1 = float(rec.get("t1", 0) or 0)
    if price is None or entry <= 0:
        return "بلا بيانات", None
    ret = (price - entry) / entry * 100
    if stop and price <= stop:
        return "ضرب الوقف", ret
    if t1 and price >= t1:
        return "حققت الهدف", ret
    return "جارية", ret


def evaluate(recs: list, prices: dict) -> dict:
    rows = []
    for r in recs or []:
        sym = r.get("symbol", "")
        px = prices.get(sym) if prices else None
        status, ret = classify(r, px)
        rows.append({
            "date": r.get("date", ""), "symbol": sym.replace(".CA", ""),
            "entry": float(r.get("entry", 0) or 0),
            "now": round(px, 2) if px else None,
            "ret": round(ret, 2) if ret is not None else None,
            "status": status, "score": r.get("score"),
        })
    closed = [x for x in rows if x["status"] in ("ضرب الوقف", "حققت الهدف")]
    wins = [x for x in closed if x["status"] == "حققت الهدف"]
    rets = [x["ret"] for x in closed if x["ret"] is not None]
    summary = {
        "total": len(rows),
        "closed": len(closed),
        "wins": len(wins),
        "losses": len(closed) - len(wins),
        "running": sum(1 for x in rows if x["status"] == "جارية"),
        "win_rate": round(len(wins) / len(closed) * 100, 1) if closed else None,
        "avg_return": round(sum(rets) / len(rets), 2) if rets else None,
        "best": round(max(rets), 2) if rets else None,
        "worst": round(min(rets), 2) if rets else None,
    }
    return {"rows": rows, "summary": summary}
