"""المقارنة الأساسية المتقدمة — نِسب السهم مقابل قطاعه والسوق.

تعتمد على قاعدة المؤشرات المرجعية المحلية (egx_fundamentals). صريحة: تغطية القاعدة
محدودة لأهم الأسهم، والمتوسطات تُحسب من المتاح.
"""

METRICS = [
    ("مكرر الربحية (P/E)", "pe_ref", "lower"),
    ("مضاعف القيمة الدفترية (P/B)", "pb_ref", "lower"),
    ("العائد على حقوق الملكية (ROE)", "roe", "higher"),
    ("عائد التوزيعات", "dividend_yield", "higher"),
    ("هامش صافي الربح", "profit_margin", "higher"),
]


def _avg(keys, db, field):
    vals = [db[k].get(field) for k in keys if db.get(k, {}).get(field) is not None]
    return round(sum(vals) / len(vals), 3) if vals else None


def compare(symbol: str, sector_fn, db: dict) -> dict:
    stock = db.get(symbol)
    if not stock:
        return {"error": "لا تتوفر بيانات مرجعية لهذا السهم في القاعدة المحلية."}
    sector = sector_fn(symbol) if sector_fn else "—"
    peer_keys = [k for k in db if db[k] and (sector_fn(k) if sector_fn else None) == sector]
    all_keys = list(db.keys())

    rows = []
    for label, field, direction in METRICS:
        sv = stock.get(field)
        sa = _avg(peer_keys, db, field)
        ma = _avg(all_keys, db, field)
        rel = "—"
        if sv is not None and sa:
            if direction == "lower":
                rel = "أرخص من القطاع" if sv < sa * 0.95 else ("أغلى من القطاع" if sv > sa * 1.05 else "قريب من القطاع")
            else:
                rel = "أفضل من القطاع" if sv > sa * 1.05 else ("أضعف من القطاع" if sv < sa * 0.95 else "قريب من القطاع")
        rows.append({"المؤشر": label, "السهم": sv, "متوسط القطاع": sa, "متوسط السوق": ma, "الحكم": rel})

    return {"symbol": symbol, "sector": sector, "peers_count": len(peer_keys), "rows": rows}
