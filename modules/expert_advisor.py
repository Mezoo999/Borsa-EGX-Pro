"""المستشار الاستثماري المتقدم وخبير البورصة المصرية (EGX Master Expert Advisor).

محرك استشاري يحاكي تفكير أكبر مديري الصناديق والمحافظ في البورصة المصرية:
1. دراسة دورة حركة السعر وسلوك صناع السوق (Wyckoff Market Phase: تجميع، انطلاق، تصريف، هبوط)
2. توافق الاتجاه على الفواصل الزمنية (Daily + Weekly Confluence)
3. كشف تدفقات السيولة المؤسسية الحقيقية (Institutional Inflows)
4. فحص الأمان المالي والتقييم (P/E, P/B, Div Yield, ROE)
5. كشف فخاخ المضاربة والتلاعبات السعرية في السوق المصري (Speculation vs Value)
6. خطة الدخول الرقمية والأهداف (Buy Zone, Invalidation Stop, Target 1, Target 2, R:R)
7. التقرير الاستشاري التنفيذي الحاسم (Executive Investment Brief)
"""
import numpy as np
import pandas as pd
from modules.technical import add_indicators, get_last_signals, detect_candlestick_patterns, detect_divergence
from modules.signals import calculate_price_targets, calculate_technical_score
from modules.fundamental import analyze_fundamental
from modules.egx_fundamentals import get_curated_fundamentals

# تصنيف طبيعة الأسهم في البورصة المصرية (مؤسسي استثماري vs مضاربي عالي المخاطر)
INSTITUTIONAL_STOCKS = {
    "COMI.CA", "TMGH.CA", "SWDY.CA", "MFPC.CA", "ABUK.CA", "ALCN.CA",
    "EAST.CA", "ETEL.CA", "EGAL.CA", "EFIH.CA", "HRHO.CA", "CIEB.CA",
    "HDBK.CA", "ADIB.CA", "ORWE.CA", "JUFO.CA", "EFID.CA", "SKPC.CA"
}

HIGH_SPECULATIVE_STOCKS = {
    "BTFH.CA", "CCAP.CA", "DSCW.CA", "OIH.CA", "ACAMD.CA", "ORAS.CA",
    "EGTS.CA", "AJWA.CA", "RTVC.CA", "ASCM.CA", "PRDC.CA", "ISPH.CA"
}


def analyze_wyckoff_phase(df: pd.DataFrame, signals: dict) -> dict:
    """
    تحليل مرحلة السهم وفق نظرية وايكوف (Wyckoff Market Structure):
    - تجميع مؤسسي (Accumulation)
    - انطلاق صاعد (Markup)
    - تصريف وجني أرباح صناع السوق (Distribution)
    - هبوط وتفريغ (Markdown)
    """
    if len(df) < 50:
        return {"phase": "غير محدد", "desc": "بيانات غير كافية"}

    close = float(signals.get("Close", df["Close"].iloc[-1]))
    sma20 = float(signals.get("SMA20", close))
    sma50 = float(signals.get("SMA50", close))
    sma200 = float(signals.get("SMA200", close))
    rsi = float(signals.get("RSI", 50))
    vol_ratio = float(signals.get("Vol_Ratio", 1.0))
    st_dir = signals.get("ST_dir", 0)
    divergence = signals.get("Divergence")

    recent_60 = df.tail(60)
    high_60 = float(recent_60["High"].max())
    low_60 = float(recent_60["Low"].min())
    pos_in_range = (close - low_60) / (high_60 - low_60) * 100 if (high_60 - low_60) > 0 else 50

    # 1. مرحلة التجميع (Accumulation)
    # السعر في النصف السفلي من النطاق (pos < 40%)، قريب من القاع، مع أحجام تداول تتزايد عند الصعود، أو وجود دايفرجنس إيجابي
    if pos_in_range <= 35 and (rsi < 45 or (divergence and "Bullish" in divergence)):
        if vol_ratio >= 1.2 and close >= sma20 * 0.98:
            return {
                "phase": "تجميع مؤسسي صامت (Accumulation Phase)",
                "status": "bullish_early",
                "tag": "تجميع",
                "desc": "المؤسسات وصناع السوق يجمعون كميات في السهم عند القاع بهدوء بدون إحداث فورة سعرية.",
                "action_advice": "منطقة شراء وتجميع مثالية على دفعات قرب الدعم."
            }
        else:
            return {
                "phase": "بناء قاع واختبار دعوم (Base Building)",
                "status": "neutral_bottom",
                "tag": "بناء قاع",
                "desc": "السهم يبني قاعدة سعرية قرب القاع بانتظار ظهور مشترٍ حقيقي ودخول سيولة.",
                "action_advice": "مراقبة واقتراب من نقطة الدخول، بانتظار إشارة اختراق بحجم تداول."
            }

    # 2. مرحلة الانطلاق الصاعد (Markup)
    # السعر فوق متوسطات 20 و 50 و 200، واتجاه صاعد قوي
    if close > sma20 > sma50 and (close > sma200 if sma200 else True) and st_dir > 0:
        if rsi >= 72:
            return {
                "phase": "قمة صاعدة وتشبع شرائي (Markup Climax)",
                "status": "caution_high",
                "tag": "تشبع صاعد",
                "desc": "السهم في مسار صاعد قوي لكنه وصل لمرحلة ذروة الشراء، وتزداد احتمالية التهدئة وجني الأرباح.",
                "action_advice": "لا تشترِ عند هذه القمة؛ احتفظ إذا كنت شارياً وارفع وقف الخسارة لحجز أرباحك."
            }
        return {
            "phase": "مسار صاعد نشط (Markup Phase)",
            "status": "bullish_strong",
            "tag": "انطلاق صاعد",
            "desc": "السهم تحت سيطرة كاملة للمشترين المؤسسيين، المتوسطات تدعم الصعود والاتجاه قوي.",
            "action_advice": "فرصة شراء ممتازة مع الاتجاه، أو ركوب الموجة حتى ظهور إشارات ضعف."
        }

    # 3. مرحلة التصريف (Distribution)
    # السعر قرب القمة (pos > 75%) مع دايفرجنس سلبي أو أحجام تداول شاذة بدون تقدم في السعر، أو كسر SMA20
    if pos_in_range >= 70 and (rsi > 60 or (divergence and "Bearish" in divergence)):
        if close < sma20 or (divergence and "Bearish" in divergence):
            return {
                "phase": "تصريف وجني أرباح صناع السوق (Distribution Phase)",
                "status": "bearish_distribution",
                "tag": "تصريف",
                "desc": "صناع السوق يبيعون تدريجياً ويفرغون حمولتهم للأفراد بعد موجة صعود سابقة.",
                "action_advice": "خطر جداً! لا تشترِ إطلاقاً، ومن يمتلك السهم يجب عليه البيع وتأمين أرباحه."
            }

    # 4. مرحلة الهبوط والتفريغ (Markdown)
    # السعر تحت المتوسطات، قيعان وقمم هابطة
    if close < sma20 < sma50:
        return {
            "phase": "مسار هابط وضغط بيعي (Markdown Phase)",
            "status": "bearish_markdown",
            "tag": "مسار هابط",
            "desc": "سيطرة واضحة للبائعين، والسيولة تهرب من السهم بحثاً عن فرص أخرى.",
            "action_advice": "تجنب الشراء تماماً، والاحتفاظ بالسيولة كاش في ثاندر."
        }

    # افتراضي: نطاق عرضي وحيرة
    return {
        "phase": "تداول عرضي متذبذب (Consolidation)",
        "status": "neutral",
        "tag": "عرضي",
        "desc": "توازن مؤقت بين قوى الشراء والبيع داخل نطاق ضيق بدون اتجاه محدد.",
        "action_advice": "انتظر حتى يخترق السهم المقاومة أو يرتد من الدعم بوضوح."
    }


def analyze_weekly_confluence(df: pd.DataFrame) -> dict:
    """
    تحليل الاتجاه العام على الفاصل الأكبر (الأسبوعي):
    توافق اليومي مع الأسبوعي هو سر نجاح الصفقات الكبرى في البورصة المصرية.
    """
    if len(df) < 50:
        return {"weekly_trend": "صاعد", "confluence": True}

    # شمعة أسبوعية تقريبية (كل 5 جلسات)
    close_now = float(df["Close"].iloc[-1])
    sma50_daily = float(df["Close"].rolling(50).mean().iloc[-1])
    sma200_daily = float(df["Close"].rolling(200).mean().iloc[-1]) if len(df) >= 200 else sma50_daily

    if close_now > sma50_daily >= sma200_daily:
        return {
            "weekly_trend": "صاعد قوي (مؤسسي)",
            "bias": "bullish",
            "desc": "الاتجاه العام طويل الأجل صاعد ويدعم الصفقات الشرائية بقوة."
        }
    elif close_now > sma50_daily:
        return {
            "weekly_trend": "صاعد متوسط",
            "bias": "bullish",
            "desc": "الاتجاه العام إيجابي مع بعض التذبذب."
        }
    elif close_now < sma50_daily < sma200_daily:
        return {
            "weekly_trend": "هابط رئيسي",
            "bias": "bearish",
            "desc": "الاتجاه العام طويل الأجل سلبي، وأي صعود هو مجرد ارتداد تصحيحي مؤقت."
        }
    else:
        return {
            "weekly_trend": "محايد / تصحيحي",
            "bias": "neutral",
            "desc": "الاتجاه طويل الأجل غير واضح ويتحرك عرضياً."
        }


def generate_expert_verdict(symbol: str, df: pd.DataFrame) -> dict:
    """
    توليد التقرير الاستشاري الشامل والقرار القاطع كأفضل خبير في البورصة المصرية.
    """
    if df is None or df.empty or len(df) < 30:
        return {"error": "بيانات غير كافية لتحليل هذا السهم"}

    df_ind = add_indicators(df)
    sig = get_last_signals(df_ind)
    price = float(sig.get("Close", df["Close"].iloc[-1]))

    # 1. تحليل الهيكل ومرحلة وايكوف
    wyckoff = analyze_wyckoff_phase(df_ind, sig)

    # 2. تحليل الاتجاه طويل المدى
    mtf = analyze_weekly_confluence(df_ind)

    # 3. التحليل المالي والتقييم
    fund = analyze_fundamental(symbol)
    health = fund.get("الجدارة_المالية", {})
    health_score = health.get("health_score", 50)
    pe = fund.get("مكرر_الربحية_PE")
    div_yield = fund.get("عائد_التوزيعات")
    div_yield_pct = (div_yield * 100) if div_yield else 0
    theme = fund.get("طبيعة_التحوط", "سهم مدرج بالبورصة")

    # 4. طبيعة السهم وتصنيف المخاطر
    is_institutional = symbol in INSTITUTIONAL_STOCKS
    is_speculative = symbol in HIGH_SPECULATIVE_STOCKS
    if is_institutional:
        stock_nature = "سهم قيادي ومؤسسي (Tier-1 Institutional)"
        nature_advice = "تحركات السهم منضبطة وصعبة التلاعب، وتعتمد على النتائج المالية والمؤسسات."
    elif is_speculative:
        stock_nature = "سهم مضاربي عالي التذبذب والمخاطر ⚠️"
        nature_advice = "السهم يتحكم فيه مضاربون وأفراد، التقلب حاد ويتطلب وقف خسارة صارم جداً."
    else:
        stock_nature = "سهم متوسط السيولة (Mid-Cap)"
        nature_advice = "سهم استثماري معتدل يعتمد على سيولة السوق والقطاع."

    # 5. الأهداف الرقمية ونسبة العائد إلى المخاطرة
    targets_data = calculate_price_targets(sig, df_ind)
    summary_tgt = targets_data.get("summary", {})

    atr = float(sig.get("ATR", price * 0.025))
    stop_loss = float(summary_tgt.get("stop_loss", price - 1.0 * atr))
    stop_pct = float(summary_tgt.get("stop_loss_pct", 3.5))
    t1 = float(summary_tgt.get("T1", price + 1.5 * atr))
    t1_pct = float(summary_tgt.get("T1_pct", 5.5))
    t2 = float(summary_tgt.get("T2", price + 2.5 * atr))
    t2_pct = float(summary_tgt.get("T2_pct", 9.5))
    rr_str = summary_tgt.get("risk_reward_str", "1:1.6")

    # Buy zone (منطقة الشراء المفضلة)
    buy_zone_min = round(min(price * 0.99, stop_loss + (price - stop_loss) * 0.3), 2)
    buy_zone_max = round(max(price * 1.005, price), 2)

    # 6. القرار النهائي القاطع والحاسم (The Master Decision)
    phase_status = wyckoff.get("status", "")
    tscore = calculate_technical_score(sig, df_ind)
    tech_score = tscore["score"]

    # تجميع النقاط والوزن المؤسسي
    conviction_points = 0
    bullish_signals = []
    bearish_warnings = []

    if "bullish" in phase_status:
        conviction_points += 3
        bullish_signals.append(f"مرحلة السهم: {wyckoff['phase']}")
    elif "bearish" in phase_status:
        conviction_points -= 4
        bearish_warnings.append(f"مرحلة السهم: {wyckoff['phase']}")

    if mtf["bias"] == "bullish":
        conviction_points += 2
        bullish_signals.append(f"الاتجاه طويل الأجل: {mtf['weekly_trend']}")
    elif mtf["bias"] == "bearish":
        conviction_points -= 2
        bearish_warnings.append(f"الاتجاه العام: {mtf['weekly_trend']}")

    if health_score >= 70:
        conviction_points += 2
        bullish_signals.append(f"جدارة مالية قوية ({health_score}/100) — مضاعف ربحية وتوزيعات تحمي السهم")
    elif health_score <= 40:
        conviction_points -= 1
        bearish_warnings.append("التقييم المالي متضخم أو توجد مخاطر مالية")

    rsi_val = sig.get("RSI", 50)
    if rsi_val and rsi_val < 35:
        conviction_points += 2
        bullish_signals.append(f"مؤشر RSI في منطقة قاع وتشبع بيعي ({rsi_val:.0f})")
    elif rsi_val and rsi_val > 72:
        conviction_points -= 3
        bearish_warnings.append(f"مؤشر RSI في ذروة شراء شديدة ({rsi_val:.0f}) — خطر ارتداد هابط")

    vol_ratio = sig.get("Vol_Ratio", 1.0)
    if vol_ratio and vol_ratio >= 1.4:
        bullish_signals.append(f"حجم تداول غير معتاد ({vol_ratio:.1f}x ضعف المتوسط)")

    turnover_m = sig.get("Turnover_M", 0)
    if turnover_m and turnover_m < 2.0:
        bearish_warnings.append(f"سيولة السهم ضعيفة ({turnover_m:.1f} مليون ج.م يومياً) — تداول بحذر")

    # صياغة الحكم النهائي
    if conviction_points >= 4 and tech_score >= 60:
        verdict = "شراء مؤكد وقوي 🟢"
        verdict_code = "STRONG_BUY"
        verdict_color = "#00c853"
        verdict_summary = "تضافرت المؤشرات الفنية والمالية على الصعود، والسهم في منطقة دخول ممتازة."
    elif conviction_points >= 2 and tech_score >= 52:
        verdict = "شراء تدريجي على دفعات 🟢"
        verdict_code = "BUY"
        verdict_color = "#66bb6a"
        verdict_summary = "الاتجاه إيجابي والفرصة جيدة، ويُفضل الدخول على دفعتين داخل منطقة الشراء."
    elif conviction_points <= -4 or tech_score <= 35:
        verdict = "بيع وتخارج فوري 🔴"
        verdict_code = "STRONG_SELL"
        verdict_color = "#d32f2f"
        verdict_summary = "السهم تحت ضغط بيعي أو تصريف واضح، والاحتفاظ بالكاش هو الخيار الصحيح."
    elif conviction_points <= -2 or tech_score <= 44:
        verdict = "تخفيف ومراقبة حذرة 🔴"
        verdict_code = "SELL"
        verdict_color = "#ef5350"
        verdict_summary = "المؤشرات تشير إلى ضعف عزم الصعود، ولا يُنصح بفتح أي مراكز شراء جديدة."
    else:
        verdict = "انتظار ومراقبة (كاش) ⚪"
        verdict_code = "HOLD"
        verdict_color = "#90a4ae"
        verdict_summary = "السهم في منطقة حيرة وتذبذب عرضي، ولا توجد إشارة واضحة للدخول الآن."

    # تقرير تنفيذي مكتوب بلغة خبير البورصة المصرية
    executive_memo = f"""
السهم حالياً في **{wyckoff['phase']}**. {wyckoff['desc']}
من الناحية الأساسية والتحوط: السهم يصنف كـ **{theme}**، بجدارة مالية **{health_score}/100**، ومكرر ربحية يبلغ **{pe if pe else '—'}**.
الاتجاه العام طويل الأجل هو **{mtf['weekly_trend']}**.
{('⚠️ تنبيه صناع السوق: ' + nature_advice) if is_speculative else ('💎 ميزة أمان: ' + nature_advice)}
    """.strip()

    return {
        "symbol": symbol,
        "price": price,
        "verdict": verdict,
        "verdict_code": verdict_code,
        "verdict_color": verdict_color,
        "verdict_summary": verdict_summary,
        "executive_memo": executive_memo,
        "wyckoff": wyckoff,
        "mtf": mtf,
        "stock_nature": stock_nature,
        "nature_advice": nature_advice,
        "is_institutional": is_institutional,
        "is_speculative": is_speculative,
        "health_score": health_score,
        "theme": theme,
        "pe": pe,
        "div_yield_pct": div_yield_pct,
        "tech_score": tech_score,
        "bullish_signals": bullish_signals,
        "bearish_warnings": bearish_warnings,
        "plan": {
            "buy_zone": f"{buy_zone_min:,.2f} — {buy_zone_max:,.2f} ج.م",
            "current_price": price,
            "stop_loss": stop_loss,
            "stop_pct": stop_pct,
            "target_1": t1,
            "target_1_pct": t1_pct,
            "target_2": t2,
            "target_2_pct": t2_pct,
            "rr_ratio": rr_str,
            "liquidity": sig.get("Liquidity_Status", "سيولة مقبولة"),
            "turnover_m": turnover_m
        }
    }
