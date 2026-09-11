"""وحدة التحليل المالي والأساسي (Fundamental Analysis) المتكاملة لأسهم البورصة المصرية."""
from .data import get_ticker_info
from .egx_fundamentals import get_curated_fundamentals, calculate_fundamental_health_score


def analyze_fundamental(symbol: str) -> dict:
    """جمع وتحليل البيانات الأساسية للشركة مع دمج البيانات المرجعية المصرية."""
    info = get_ticker_info(symbol) or {}
    curated = get_curated_fundamentals(symbol)

    def val(key, default=None):
        v = info.get(key, default)
        return v

    metrics = {}
    metrics["اسم_الشركة"] = curated.get("name") or val("longName") or val("shortName") or symbol
    metrics["السوق"] = val("exchange", "EGX")
    metrics["العملة"] = val("currency", "EGP")
    metrics["طبيعة_التحوط"] = curated.get("theme", "سهم مدرج بالبورصة المصرية")
    metrics["الملاءة_والديون"] = curated.get("debt_health", "متوسطة")
    metrics["نبذة_عن_السهم"] = curated.get("description", "")

    # السعر والقيمة السوقية
    metrics["السعر_الحالي"] = val("currentPrice") or val("regularMarketPrice")
    metrics["القيمة_السوقية"] = val("marketCap")
    metrics["سعر_السنة_المنخفض"] = val("fiftyTwoWeekLow")
    metrics["سعر_السنة_المرتفع"] = val("fiftyTwoWeekHigh")

    # نسب الربحية والتقييم (مع fallback ذكي للبيانات المصرية المرجعية)
    pe_val = val("trailingPE")
    if pe_val is None or pe_val == 0:
        pe_val = curated.get("pe_ref")
    metrics["مكرر_الربحية_PE"] = pe_val
    metrics["مكرر_الربحية_المتوقع"] = val("forwardPE")

    pb_val = val("priceToBook")
    if pb_val is None or pb_val == 0:
        pb_val = curated.get("pb_ref")
    metrics["السعر_إلى_القيمة_الدفترية_PB"] = pb_val
    metrics["نسبة_السعر_للمبيعات_PS"] = val("priceToSalesTrailing12Months")

    # مؤشرات الأداء والربحية
    pm_val = val("profitMargins")
    if pm_val is None or pm_val == 0:
        pm_val = curated.get("profit_margin")
    metrics["هامش_الربح"] = pm_val
    metrics["هامش_التشغيل"] = val("operatingMargins")

    roe_val = val("returnOnEquity")
    if roe_val is None or roe_val == 0:
        roe_val = curated.get("roe")
    metrics["العائد_على_حقوق_الملكية_ROE"] = roe_val
    metrics["العائد_على_الأصول_ROA"] = val("returnOnAssets")

    # النمو
    metrics["نمو_الإيرادات"] = val("revenueGrowth")
    metrics["نمو_الأرباح"] = val("earningsGrowth")

    # الأرباح والتوزيعات (سد العيب الأكبر في ياهو فاينانس للبورصة المصرية)
    dy_val = val("dividendYield")
    if dy_val is None:
        dy_val = curated.get("dividend_yield")
    metrics["عائد_التوزيعات"] = dy_val
    metrics["نسبة_التوزيع"] = val("payoutRatio")

    # الميزانية
    metrics["إجمالي_الديون"] = val("totalDebt")
    metrics["النقدية"] = val("totalCash")
    metrics["الديون_إلى_حقوق_الملكية"] = val("debtToEquity")

    # حساب درجة الجدارة المالية والتقييم (0-100)
    health = calculate_fundamental_health_score(metrics)
    metrics["الجدارة_المالية"] = health

    return {k: v for k, v in metrics.items() if v is not None}


def calculate_valuation_summary(metrics: dict, current_price: float) -> dict:
    """
    تلخيص التقييم بناءً على المقاييس الأساسية للمستثمر في البورصة المصرية.
    """
    summaries = {}

    if metrics.get("مكرر_الربحية_PE") is not None:
        pe = metrics["مكرر_الربحية_PE"]
        if pe <= 0:
            summaries["مكرر الربحية (P/E)"] = ("تحذير", "الشركة تحقق خسائر حالياً")
        elif pe < 5.0:
            summaries["مكرر الربحية (P/E)"] = ("جيد", f"تقييم رخيص جداً واستثنائي ({pe:.1f})")
        elif pe < 9.0:
            summaries["مكرر الربحية (P/E)"] = ("جيد", f"تقييم ممتاز وأقل من متوسط السوق ({pe:.1f})")
        elif pe < 16.0:
            summaries["مكرر الربحية (P/E)"] = ("متوسط", f"تقييم في النطاق العادل والمقبول ({pe:.1f})")
        else:
            summaries["مكرر الربحية (P/E)"] = ("مرتفع", f"تقييم أعلى من المتوسط ({pe:.1f}) — تداول بعلاوة نمو")

    if metrics.get("عائد_التوزيعات") is not None:
        dy = metrics["عائد_التوزيعات"] * 100
        if dy >= 8.0:
            summaries["عائد التوزيعات النقدية"] = ("جيد", f"عائد كاش سخي استثنائي ({dy:.1f}%) — تحوط قوي من التضخم")
        elif dy >= 5.0:
            summaries["عائد التوزيعات النقدية"] = ("جيد", f"عائد توزيعات جيد جداً ({dy:.1f}%)")
        elif dy >= 1.0:
            summaries["عائد التوزيعات النقدية"] = ("متوسط", f"توزيعات نقدية مقبولة ({dy:.1f}%)")
        else:
            summaries["عائد التوزيعات النقدية"] = ("متوسط", "الشركة تعيد استثمار كامل أرباحها للتوسع الرأسمالي (سهم نمو)")

    if metrics.get("السعر_إلى_القيمة_الدفترية_PB") is not None:
        pb = metrics["السعر_إلى_القيمة_الدفترية_PB"]
        if pb < 1.0:
            summaries["مضاعف القيمة الدفترية (P/B)"] = ("جيد", f"السهم يباع بأقل من أصوله الصافية ({pb:.2f}x)")
        elif pb < 2.0:
            summaries["مضاعف القيمة الدفترية (P/B)"] = ("جيد", f"مضاعف قيمة دفترية معتدل وجذاب ({pb:.2f}x)")
        else:
            summaries["مضاعف القيمة الدفترية (P/B)"] = ("متوسط", f"مضاعف قيمة دفترية أعلى من المتوسط ({pb:.2f}x)")

    if metrics.get("العائد_على_حقوق_الملكية_ROE") is not None:
        roe = metrics["العائد_على_حقوق_الملكية_ROE"] * 100
        if roe >= 30:
            summaries["العائد على حقوق الملكية (ROE)"] = ("جيد", f"كفاءة تشغيلية فائقة ({roe:.0f}%)")
        elif roe >= 18:
            summaries["العائد على حقوق الملكية (ROE)"] = ("جيد", f"معدل ربحية تشغيلية ممتاز ({roe:.0f}%)")
        else:
            summaries["العائد على حقوق الملكية (ROE)"] = ("متوسط", f"معدل ربحية معتدل ({roe:.0f}%)")

    if metrics.get("الملاءة_والديون"):
        summaries["الملاءة المالية والديون"] = ("جيد" if "ممتازة" in metrics["الملاءة_والديون"] or "جيدة" in metrics["الملاءة_والديون"] else "متوسط", metrics["الملاءة_والديون"])

    return summaries

