"""محرك التقاء الإشارات (Confluence Engine).

الفكرة: توصية البيع/الشراء لا تُطلق من مؤشر واحد، بل فقط عندما تتوافق أبعاد
مستقلة متعددة (اتجاه يومي + أسبوعي، زخم، حجم، نموذج سعري، عائد/مخاطرة، سيولة، مالي).
كل بُعد يُقيَّم +1 (صاعد) / 0 (محايد) / -1 (هابط)، وتُحسب درجة توافق 0-100.
هذا يقلّل الإشارات الكاذبة ويجعل "الفرصة الحقيقية" شرطاً قابلاً للقياس.
"""
import pandas as pd

from modules.technical import add_indicators, get_last_signals
from modules.signals import generate_signal, calculate_price_targets
from modules.expert_advisor import analyze_wyckoff_phase, analyze_weekly_confluence
from modules.fundamental import analyze_fundamental


def _weekly_trend(df_weekly):
    """الاتجاه الأسبوعي الحقيقي (من شموع أسبوعية فعلية إن وُجدت)."""
    if df_weekly is None or len(df_weekly) < 20:
        return None
    try:
        w = add_indicators(df_weekly)
        last = w.iloc[-1]
        close = float(last["Close"])
        sma20 = float(last["SMA20"]) if "SMA20" in w.columns else close
        sma50 = float(last["SMA50"]) if "SMA50" in w.columns else close
        if close > sma20 > sma50:
            return {"status": 1, "note": "الأسبوعي صاعد (فوق SMA20/50)"}
        if close < sma20 < sma50:
            return {"status": -1, "note": "الأسبوعي هابط"}
        return {"status": 0, "note": "الأسبوعي متذبذب"}
    except Exception:
        return None


def analyze_confluence(symbol: str, df_daily: pd.DataFrame,
                       df_weekly: pd.DataFrame | None = None,
                       info: dict | None = None) -> dict:
    """تحليل التوافق الكامل لسهم وإصدار توصية شرطية.

    يعيد dict: conviction (0-100)، verdict، color، pos/neg/total، factors (قائمة).
    """
    if df_daily is None or len(df_daily) < 40:
        return {"error": "بيانات غير كافية"}

    df_ind = add_indicators(df_daily)
    sig = get_last_signals(df_ind)
    close = float(sig.get("Close", df_daily["Close"].iloc[-1]))
    swing = generate_signal(sig, df_ind)
    targets = calculate_price_targets(sig, df_ind)
    summary = targets.get("summary", {})
    wyckoff = analyze_wyckoff_phase(df_ind, sig)

    factors = []

    # 1) الاتجاه اليومي
    sma20, sma50 = sig.get("SMA20"), sig.get("SMA50")
    if close and sma20 and sma50:
        if close > sma20 > sma50:
            factors.append({"group": "الاتجاه", "name": "اليومي", "status": 1, "note": "فوق SMA20 وSMA50"})
        elif close < sma20 < sma50:
            factors.append({"group": "الاتجاه", "name": "اليومي", "status": -1, "note": "تحت SMA20 وSMA50"})
        else:
            factors.append({"group": "الاتجاه", "name": "اليومي", "status": 0, "note": "متذبذب"})

    # 2) الاتجاه الأسبوعي (MTF حقيقي)
    wt = _weekly_trend(df_weekly)
    if wt is not None:
        factors.append({"group": "الاتجاه", "name": "الأسبوعي (MTF)", "status": wt["status"], "note": wt["note"]})
    else:
        mtf = analyze_weekly_confluence(df_ind)
        bias = mtf.get("bias", "neutral")
        s = 1 if bias == "bullish" else (-1 if bias == "bearish" else 0)
        factors.append({"group": "الاتجاه", "name": "الأسبوعي", "status": s, "note": mtf.get("weekly_trend", "محايد")})

    # 3) الزخم MACD
    macd, macd_sig = sig.get("MACD"), sig.get("MACD_Signal")
    if macd is not None and macd_sig is not None:
        if macd > macd_sig:
            factors.append({"group": "الزخم", "name": "MACD", "status": 1, "note": "فوق الإشارة (صاعد)"})
        else:
            factors.append({"group": "الزخم", "name": "MACD", "status": -1, "note": "تحت الإشارة"})

    # 4) RSI
    rsi = sig.get("RSI")
    if rsi is not None:
        if 45 <= rsi <= 65:
            factors.append({"group": "الزخم", "name": "RSI", "status": 1, "note": f"{rsi:.0f} منطقة صحية"})
        elif rsi > 72:
            factors.append({"group": "الزخم", "name": "RSI", "status": -1, "note": f"{rsi:.0f} تشبع شرائي"})
        elif rsi < 32:
            factors.append({"group": "الزخم", "name": "RSI", "status": 0, "note": f"{rsi:.0f} تشبع بيعي"})
        else:
            factors.append({"group": "الزخم", "name": "RSI", "status": 0, "note": f"{rsi:.0f} محايد"})

    # 5) حجم التداول
    vol_ratio = sig.get("Vol_Ratio", 1.0)
    if vol_ratio and vol_ratio >= 1.3:
        factors.append({"group": "الحجم", "name": "حجم التداول", "status": 1, "note": f"{vol_ratio:.1f}x المتوسط (تأكيد)"})
    elif vol_ratio and vol_ratio <= 0.5:
        factors.append({"group": "الحجم", "name": "حجم التداول", "status": -1, "note": "حجم ضعيف جداً"})
    else:
        factors.append({"group": "الحجم", "name": "حجم التداول", "status": 0, "note": "حجم عادي"})

    # 6) تدفق الأموال OBV
    obv, obv_ma = sig.get("OBV"), sig.get("OBV_MA")
    if obv is not None and obv_ma is not None:
        s = 1 if obv > obv_ma else -1
        factors.append({"group": "الحجم", "name": "تدفق الأموال", "status": s, "note": "تراكم صاعد" if s == 1 else "توزيع هابط"})

    # 7) النموذج السعري + وايكوف
    setup = swing.get("setup", "")
    wy_tag = wyckoff.get("tag", "عرضي")
    if "اختراق" in setup or "انطلاق" in wy_tag or "تجميع" in wy_tag:
        factors.append({"group": "النموذج", "name": "النموذج/وايكوف", "status": 1, "note": f"{setup} • {wy_tag}"})
    elif "هابط" in setup or "تصريف" in wy_tag or "مسار هابط" in wy_tag:
        factors.append({"group": "النموذج", "name": "النموذج/وايكوف", "status": -1, "note": f"{setup} • {wy_tag}"})
    else:
        factors.append({"group": "النموذج", "name": "النموذج/وايكوف", "status": 0, "note": f"{setup} • {wy_tag}"})

    # 8) العائد/مخاطرة
    rr = summary.get("risk_reward_1", 1.0)
    if rr and rr >= 2.0:
        factors.append({"group": "العائد/مخاطرة", "name": "R:R", "status": 1, "note": f"1:{rr} ممتاز"})
    elif rr and rr >= 1.5:
        factors.append({"group": "العائد/مخاطرة", "name": "R:R", "status": 0, "note": f"1:{rr} مقبول"})
    else:
        factors.append({"group": "العائد/مخاطرة", "name": "R:R", "status": -1, "note": f"1:{rr} ضعيف"})

    # 9) السيولة
    turnover = sig.get("Turnover_M", 0) or 0
    if turnover >= 5:
        factors.append({"group": "السيولة", "name": "السيولة", "status": 1, "note": f"{turnover:.1f} م.ج ممتازة"})
    elif turnover < 2:
        factors.append({"group": "السيولة", "name": "السيولة", "status": -1, "note": f"{turnover:.1f} م.ج ضعيفة"})
    else:
        factors.append({"group": "السيولة", "name": "السيولة", "status": 0, "note": f"{turnover:.1f} م.ج"})

    # 10) الجدارة المالية
    try:
        fund = analyze_fundamental(symbol, info=info)
        health = fund.get("الجدارة_المالية", {})
        hs = health.get("health_score", 50) or 50
        if hs >= 70:
            factors.append({"group": "المالي", "name": "الجدارة المالية", "status": 1, "note": f"{hs}/100 قوية"})
        elif hs <= 40:
            factors.append({"group": "المالي", "name": "الجدارة المالية", "status": -1, "note": f"{hs}/100 ضعيفة"})
        else:
            factors.append({"group": "المالي", "name": "الجدارة المالية", "status": 0, "note": f"{hs}/100 متوسطة"})
    except Exception:
        factors.append({"group": "المالي", "name": "الجدارة المالية", "status": 0, "note": "غير متاحة"})

    total = len(factors)
    pos = sum(1 for f in factors if f["status"] == 1)
    neg = sum(1 for f in factors if f["status"] == -1)
    conviction = max(0, min(100, round(50 + (pos - neg) / total * 50)))

    if pos >= 5 and neg <= 1 and conviction >= 70:
        verdict, color = "شراء قوي — توافق عالٍ", "#00c853"
    elif pos >= 4 and (pos - neg) >= 3 and conviction >= 58:
        verdict, color = "شراء — توافق جيد", "#66bb6a"
    elif neg >= 4 and (neg - pos) >= 2:
        verdict, color = "بيع / تجنّب — توافق هابط", "#e53935"
    elif neg >= 3:
        verdict, color = "حذر — ضعف التوافق", "#ffab00"
    else:
        verdict, color = "محايد — لا توافق كافٍ (انتظار)", "#90a4ae"

    return {
        "symbol": symbol,
        "conviction": conviction,
        "verdict": verdict,
        "color": color,
        "pos": pos,
        "neg": neg,
        "total": total,
        "setup": setup,
        "swing_action": swing["action"],
        "factors": factors,
    }
