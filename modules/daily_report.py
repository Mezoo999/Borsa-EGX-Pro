"""التقرير الصباحي الآلي — يومية المتداول قبل الافتتاح.

يُنشأ تلقائياً 9:30 صباحاً أيام التداول (الأحد-الخميس) أو عند الطلب من المنصة.
كل الأرقام حقيقية لحظة الإنشاء: TradingView للأسعار والمؤشرات، Yahoo للشموع، Google News للأخبار.
"""
from datetime import datetime
from pathlib import Path

REPORTS_DIR = Path(__file__).resolve().parent.parent / "reports"


def _section_indices() -> list:
    from .tv_data import indices, snapshot
    lines = []
    idx = indices()
    snap = snapshot()
    ups = sum(1 for r in snap.values() if r["change_pct"] > 0)
    downs = sum(1 for r in snap.values() if r["change_pct"] < 0)
    flats = len(snap) - ups - downs
    lines.append("## 🏛️ حالة السوق")
    for k in ["EGX30", "EGX70EWI"]:
        if k in idx:
            r = idx[k]
            lines.append(f"- **{k}**: {r['value']:,.2f} ({r['change_pct']:+.2f}%)")
    lines.append(f"- **الاتساع**: ▲ {ups} صاعد • = {flats} ثابت • ▼ {downs} هابط")
    return lines


def _section_movers() -> list:
    from .tv_data import snapshot
    snap = snapshot()
    rows = sorted(snap.values(), key=lambda r: r["change_pct"], reverse=True)
    lines = ["## 🔥 أهم التحركات"]
    lines.append("**الأكثر صعوداً:**")
    for r in rows[:5]:
        lines.append(f"- {r['symbol']} ({r['name_tv'][:20]}): {r['close']:,.2f} ({r['change_pct']:+.2f}%)")
    lines.append("**الأكثر هبوطاً:**")
    for r in rows[-5:][::-1]:
        lines.append(f"- {r['symbol']} ({r['name_tv'][:20]}): {r['close']:,.2f} ({r['change_pct']:+.2f}%)")
    lines.append("*⚠️ تحركات بعض الأسهم قد تعكس زيادة/خفض رأس مال وليست مكسباً حقيقياً — تحقق من الإفصاح قبل التصرف*")
    return lines


def _section_sectors() -> list:
    from .tv_data import snapshot
    from .data import AR_NAMES, SECTORS
    from .tv_data import SECTOR_AR
    snap = snapshot()
    acc = {}
    for sym, r in snap.items():
        key = f"{sym}.CA"
        sector = SECTORS.get(key) or SECTOR_AR.get(r["sector"], "")
        if sector:
            acc.setdefault(sector, []).append(r["change_pct"])
    rows = sorted(((s, sum(v) / len(v), len(v)) for s, v in acc.items() if len(v) >= 3),
                  key=lambda x: x[1], reverse=True)
    lines = ["## 🏙️ أداء القطاعات"]
    for s, ch, n in rows[:3]:
        lines.append(f"- **{s}** ({n} سهم): {ch:+.2f}%")
    for s, ch, n in rows[-3:]:
        lines.append(f"- {s} ({n} سهم): {ch:+.2f}%")
    return lines


def _section_opportunities() -> list:
    from .tv_data import get_registry
    from .data import get_bulk_data
    from .technical import add_indicators, get_last_signals
    from .signals import generate_signal, calculate_technical_score, calculate_price_targets
    from .advisor import analyze_stock_for_advisor
    reg = get_registry()
    top30 = sorted(reg.keys(),
                   key=lambda s: (reg[s].get("tv") or {}).get("market_cap") or 0,
                   reverse=True)[:30]
    bulk = get_bulk_data(top30, "6mo")
    rows = []
    for sym, df in (bulk or {}).items():
        try:
            info = analyze_stock_for_advisor(df)
            if not info:
                continue
            info["الرمز"] = sym.replace(".CA", "")  # الوحدة لا تملك الرمز — نمرره يدوياً
            is_buy = "شراء" in str(info.get("إشارة", ""))
            high_score = info.get("درجة فنية", 0) >= 65
            high_conf = info.get("ثقة%", 0) >= 70
            if is_buy and high_score and high_conf:
                rows.append(info)
        except Exception:
            continue
    rows.sort(key=lambda x: x.get("درجة فنية", 0), reverse=True)
    lines = ["## 🎖️ فرص عالية الثقة اليوم (أوامر تنفيذية)"]
    if not rows:
        lines.append("- لا توجد فرص تستوفي الشروط الصارمة اليوم — عدم الدخول أفضل من دخول ضعيف")
        return lines
    for r in rows[:3]:
        name = r.get("الرمز", "")
        lines.append(
            f"- **{name}** — {r.get('النموذج','')}: "
            f"دخول حوالي {r.get('السعر', 0):,.2f} • وقف {r.get('وقف خسارة', 0):,.2f} • "
            f"هدف {r.get('هدف1', 0):,.2f} • درجة {r.get('درجة فنية', 0)}/100 • {r.get('السيولة','')}"
        )
    return lines


def _section_news() -> list:
    from .news import fetch_news
    from .storage import load_store
    import os, json
    store_path = Path(__file__).resolve().parent.parent / "user_store.json"
    syms = []
    try:
        st_ = json.loads(store_path.read_text(encoding="utf-8"))
        syms = list(st_.get("watchlist", []))[:4] + list(st_.get("portfolio", {}).keys())[:3]
    except Exception:
        pass
    from .data import AR_NAMES
    seen, lines = set(), ["## 📰 أخبار قائمتك ومحفظتك"]
    found_any = False
    for sym in syms:
        if sym in seen:
            continue
        seen.add(sym)
        name = AR_NAMES.get(sym, sym.replace(".CA", ""))
        items = fetch_news(f'"{name}" OR {sym.replace(".CA","")} البورصة المصرية', limit=2)
        if items:
            found_any = True
            lines.append(f"**{sym.replace('.CA','')} — {name[:24]}:**")
            for it in items:
                lines.append(f"- [{it['pub']}] {it['title']} ({it.get('source','')})")
    if not found_any:
        lines.append("- لا توجد أخبار جديدة الآن")
    return lines


def generate_report() -> str:
    parts = [f"# 🌅 التقرير الصباحي — {datetime.now().strftime('%Y-%m-%d %H:%M')} بتوقيت القاهرة\n"]
    for fn in (_section_indices, _section_movers, _section_sectors,
               _section_opportunities, _section_news):
        try:
            parts.append("\n".join(fn()))
        except Exception as e:
            parts.append(f"\n*(قسم {fn.__name__} تعذر: {type(e).__name__})*")
    parts.append("\n---\n*التقرير آلي من بيانات حقيقية لحظة الإنشاء — استرشادي وليس نصيحة استثمارية.*")
    return "\n\n".join(parts)


def save_report(md: str) -> Path:
    REPORTS_DIR.mkdir(exist_ok=True)
    d = datetime.now().strftime("%Y-%m-%d")
    (REPORTS_DIR / f"report_{d}.md").write_text(md, encoding="utf-8")
    latest = REPORTS_DIR / "latest.md"
    latest.write_text(md, encoding="utf-8")
    return latest


if __name__ == "__main__":
    md = generate_report()
    p = save_report(md)
    print(f"REPORT_SAVED: {p}")
    print(md[:1200])
