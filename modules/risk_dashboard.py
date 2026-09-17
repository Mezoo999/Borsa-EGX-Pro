"""لوحة المخاطر — تحليل مخاطر المحفظة: التركّز، الأوزان، التنويع، التعرض القطاعي."""


def analyze(positions: dict, prices: dict, sectors: dict) -> dict:
    """positions: {sym: {"shares":n, "avg_cost":c}} • prices: {sym: price} • sectors: {sym: sector}"""
    items = []
    total = 0.0
    for sym, p in (positions or {}).items():
        sh = float(p.get("shares", 0) or 0)
        px = prices.get(sym)
        if px is None:
            px = float(p.get("avg_cost", 0) or 0)
        val = sh * px
        total += val
        items.append({"symbol": sym.replace(".CA", ""), "shares": int(sh),
                      "value": val, "sector": sectors.get(sym, "أخرى")})
    if total <= 0:
        return {"empty": True}

    for it in items:
        it["weight"] = round(it["value"] / total * 100, 1)

    sec = {}
    for it in items:
        sec[it["sector"]] = sec.get(it["sector"], 0) + it["value"]
    sectors_list = sorted(
        ({"sector": s, "value": v, "weight": round(v / total * 100, 1)} for s, v in sec.items()),
        key=lambda x: x["weight"], reverse=True)

    hhi = sum((it["weight"] / 100) ** 2 for it in items)
    div_score = round((1 - hhi) * 100, 1) if len(items) > 1 else 0.0
    top = max(items, key=lambda x: x["weight"])

    warnings = []
    if len(items) == 1:
        warnings.append("كل رأس المال في مركز واحد — تنويع صفري.")
    if top["weight"] > 35:
        warnings.append(f"مركز {top['symbol']} يشكّل {top['weight']}% من المحفظة (أكثر من 35%) — تركّز مرتفع.")
    if sectors_list and sectors_list[0]["weight"] > 50:
        warnings.append(f"قطاع «{sectors_list[0]['sector']}» يشكّل {sectors_list[0]['weight']}% — تركّز قطاعي.")

    return {
        "items": sorted(items, key=lambda x: x["weight"], reverse=True),
        "total": round(total, 0),
        "count": len(items),
        "sectors": sectors_list,
        "diversification": div_score,
        "top_weight": top["weight"],
        "warnings": warnings,
    }
