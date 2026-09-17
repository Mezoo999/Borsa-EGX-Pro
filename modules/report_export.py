"""تصدير تقرير تحليل السهم كملف HTML قابل للفتح والطباعة كـ PDF."""
from datetime import datetime


def _esc(s) -> str:
    return (str(s).replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;"))


def render(symbol: str, name: str, sections: list, generated_at: str | None = None) -> str:
    """sections: [{"title": str, "items": [(k, v)]}] أو [{"title": str, "lines": [str]}]"""
    when = generated_at or datetime.now().strftime("%Y-%m-%d %H:%M")
    body = []
    for sec in sections or []:
        body.append(f'<div class="card"><h2>{_esc(sec.get("title", ""))}</h2>')
        if "items" in sec:
            body.append("<table>")
            for k, v in sec["items"]:
                body.append(f"<tr><td class='k'>{_esc(k)}</td><td class='v'>{_esc(v)}</td></tr>")
            body.append("</table>")
        if "lines" in sec:
            body.append("<ul>" + "".join(f"<li>{_esc(x)}</li>" for x in sec["lines"]) + "</ul>")
        body.append("</div>")
    return f"""<!DOCTYPE html><html lang="ar" dir="rtl"><head><meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>تقرير {_esc(symbol)}</title>
<style>
body{{background:#0b0e14;color:#e8edf4;font-family:'Segoe UI',Tahoma,sans-serif;padding:2rem;max-width:900px;margin:auto;}}
h1{{color:#64b5f6;font-size:1.4rem;}} .card{{background:#10141d;border:1px solid #1f2d45;border-radius:12px;padding:1rem 1.2rem;margin:0.8rem 0;}}
h2{{color:#fff;font-size:1rem;border-bottom:1px solid #1f2d45;padding-bottom:0.4rem;}}
table{{width:100%;border-collapse:collapse;}} td{{padding:0.35rem 0.5rem;border-bottom:1px solid rgba(31,45,69,.45);font-size:0.9rem;}}
td.k{{color:#7d8db1;width:42%;}} td.v{{color:#fff;font-weight:600;}}
ul{{margin:0.3rem 0;padding-inline-start:1.2rem;}} li{{font-size:0.88rem;margin-bottom:0.2rem;}}
.foot{{color:#7d8db1;font-size:0.75rem;margin-top:0.6rem;}}
@media print{{body{{background:#fff;color:#000;}} .card{{border-color:#ccc;}} h1{{color:#000;}} h2{{color:#000;border-color:#ccc;}} td.v{{color:#000;}} .foot{{color:#666;}}}}
</style></head><body>
<h1>📈 تقرير تحليل — {_esc(name)} ({_esc(symbol)})</h1>
<p class="foot">أُنشئ في {_esc(when)} — منصة EGX Pro • استرشادي وليس نصيحة استثمارية</p>
{"".join(body)}
<p class="foot">الأسعار من TradingView (متأخرة ~15 دقيقة وفق قواعد البورصة المصرية).</p>
</body></html>"""
