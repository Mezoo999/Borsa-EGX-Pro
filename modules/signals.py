"""وحدة إشارات البيع والشراء ونماذج السوينغ الاحترافية للبورصة المصرية."""
import numpy as np
import pandas as pd


def generate_signal(signals: dict, df: pd.DataFrame) -> dict:
    """
    توليد إشارة سوينغ احترافية للبورصة المصرية:
    - كشف النموذج الاستثماري (Setup Type)
    - حساب قوة الإشارة بدون ازدواجية
    - تقييم السيولة وملاءمة التداول عبر ثاندر
    """
    score = 0
    reasons = []
    setup = "محايد / تداول عرضي"

    close = signals.get("Close")
    rsi = signals.get("RSI")
    macd = signals.get("MACD")
    macd_sig = signals.get("MACD_Signal")
    sma20 = signals.get("SMA20")
    sma50 = signals.get("SMA50")
    sma200 = signals.get("SMA200")
    bb_u = signals.get("BB_Upper")
    bb_l = signals.get("BB_Lower")
    vol_ratio = signals.get("Vol_Ratio", 1.0)
    supertrend_dir = signals.get("ST_dir", 0)
    candle = signals.get("Candle_Pattern")
    divergence = signals.get("Divergence")
    turnover_m = signals.get("Turnover_M", 0)

    # 1. كشف النماذج الفنية القوية (Setups)
    # نموذج 1: ارتداد من تشبع بيعي (Oversold Bounce)
    if (rsi and rsi < 36) or (close and bb_l and close <= bb_l * 1.01) or (divergence and "Bullish" in divergence):
        setup = "ارتداد من قاع (تشبع بيعي)"
        score += 3
        reasons.append("السهم في منطقة قاع وتشبع بيعي — فرصة ارتداد صاعد")
        if divergence and "Bullish" in divergence:
            score += 2
            reasons.append("تأكيد قوي: انفراج إيجابي (Bullish Divergence) بين السعر وعزم RSI")
        if candle and "Hammer" in candle:
            score += 1
            reasons.append("شمعة مطرقة ارتدادية إيجابية (Hammer) على الدعم")

    # نموذج 2: اختراق قمة وسيولة (Breakout & Volume Surge)
    elif close and sma20 and close > sma20 and vol_ratio and vol_ratio >= 1.35 and (macd and macd_sig and macd > macd_sig):
        setup = "اختراق سيولة وزخم (Breakout)"
        score += 4
        reasons.append(f"اختراق مصحوب بسيولة شرائية قوية ({vol_ratio:.1f}x ضعف متوسط 20 يوم)")
        if supertrend_dir > 0:
            score += 1
            reasons.append("مؤشر الاتجاه Supertrend يدعم استمرار الصعود")

    # نموذج 3: تصحيح في مسار صاعد (Trend Pullback)
    elif close and sma20 and sma50 and close > sma50 and (sma200 is None or sma50 > sma200):
        if rsi and 42 <= rsi <= 58 and abs(close - sma20) / sma20 < 0.035:
            setup = "تصحيح في مسار صاعد (Pullback)"
            score += 3
            reasons.append("السهم في مسار صاعد مؤسسي ويعيد اختبار متوسط 20 يوماً بهدوء (نقطة دخول منخفضة المخاطر)")
        elif close > sma20 > sma50:
            setup = "مسار صاعد مستمر (Uptrend)"
            score += 2
            reasons.append("السعر فوق متوسطات 20 و 50 يوم — الاتجاه العام صاعد")

    # نموذج 4: هبوط وكسر دعوم (Breakdown & Weakness)
    elif close and sma20 and sma50 and close < sma20 < sma50:
        setup = "مسار هابط / كسر دعوم"
        score -= 3
        reasons.append("السعر كسر متوسطات 20 و 50 يوماً لأسفل — اتجاه هابط واضح")

    # مؤشرات إضافية وتأكيدات
    if rsi is not None:
        if rsi > 72:
            score -= 2
            reasons.append(f"RSI مرتفع ({rsi:.0f}) في منطقة تشبع شرائي — تجنب الشراء عند القمم")
        elif 50 <= rsi <= 65:
            score += 1

    if macd is not None and macd_sig is not None:
        if macd > macd_sig:
            score += 1
        else:
            score -= 1

    # كشف التحذيرات البيعية
    if candle and "Bearish" in candle:
        score -= 1
        reasons.append(f"شمعة انعكاسية بيعية ({candle}) تضغط على السعر")

    # فحص السيولة المصرية
    if turnover_m and turnover_m < 2.0:
        reasons.append("⚠️ تنبيه سيولة: تداول السهم اليومي أقل من 2 مليون ج.م (قد يصعب التنفيذ السريع في ثاندر)")

    # القرار النهائي
    if score >= 4:
        action = "شراء مؤكد"
        confidence = min(0.92, 0.60 + (score / 12.0) * 0.32)
        color = "#00c853"
    elif score >= 2:
        action = "شراء تدريجي"
        confidence = 0.65
        color = "#66bb6a"
    elif score <= -4:
        action = "بيع / خروج"
        confidence = min(0.90, 0.60 + (abs(score) / 12.0) * 0.30)
        color = "#e53935"
    elif score <= -2:
        action = "تخفيف / حذر"
        confidence = 0.60
        color = "#ef5350"
    else:
        action = "انتظار / مراقبة"
        confidence = 0.40
        color = "#90a4ae"

    return {
        "action": action,
        "setup": setup,
        "score": score,
        "confidence": round(confidence, 2),
        "color": color,
        "reasons": reasons,
    }


def generate_swing_strategy_signal(signals: dict, df: pd.DataFrame) -> dict:
    """فاحص نماذج السوينغ للبورصة المصرية."""
    res = generate_signal(signals, df)
    return {
        "action": res["action"],
        "setup": res["setup"],
        "score": res["score"],
        "confidence": res["confidence"],
        "reasons": res["reasons"],
    }


# للتوافق مع استدعاءات الكود السابقة
generate_scalp_signal = generate_swing_strategy_signal


def generate_combined_signal(signals: dict, df: pd.DataFrame, interval: str = "1d") -> dict:
    """إرجاع إشارة السوينغ الفنية المناسبة لبيانات EGX."""
    return generate_signal(signals, df)



def get_support_resistance(df: pd.DataFrame, lookback: int = 200) -> tuple:
    """حساب مستويات الدعم والمقاومة من القمم والقيعان السابقة."""
    if df.empty:
        return None, None
    recent = df.tail(lookback)
    high = recent["High"].max()
    low = recent["Low"].min()
    close = df["Close"].iloc[-1]
    # مقاومة قريبة: آخر قمة
    resistance = high
    support = low
    if close and high and low:
        # لو السعر قرب القمة ناخد مقاومة أبعد
        if close > high * 0.99:
            resistance = high * 1.03
        if close < low * 1.01:
            support = low * 0.97
    return support, resistance


def calculate_technical_score(signals: dict, df: pd.DataFrame) -> dict:
    """
    درجة التحليل الفني الموحدة (0-100):
    تجمع كل المؤشرات في درجة واحدة سهلة الفهم.
    0-20 = بيع قوي | 20-40 = بيع | 40-60 = محايد | 60-80 = شراء | 80-100 = شراء قوي
    """
    score = 50  # نقطة البداية محايد
    breakdown = []

    # RSI (وزن 20)
    rsi = signals.get("RSI")
    if rsi is not None:
        if rsi < 30:
            score += 18
            breakdown.append(("RSI", "+18", "بيع مفرط — فرصة شراء"))
        elif rsi < 40:
            score += 10
            breakdown.append(("RSI", "+10", "منطقة ضعف — احتمال ارتداد"))
        elif rsi < 50:
            score += 2
            breakdown.append(("RSI", "+2", "محايد"))
        elif rsi < 60:
            score += 5
            breakdown.append(("RSI", "+5", "منطقة قوة"))
        elif rsi < 70:
            score -= 2
            breakdown.append(("RSI", "-2", "قريب من التشبع"))
        else:
            score -= 15
            breakdown.append(("RSI", "-15", "شراء مفرط — خطر انكشاف"))

    # MACD (وزن 15)
    macd = signals.get("MACD")
    macd_sig = signals.get("MACD_Signal")
    if macd is not None and macd_sig is not None:
        diff = macd - macd_sig
        if diff > 0:
            pts = min(12, int(diff / abs(macd_sig) * 100)) if macd_sig else 5
            score += pts
            breakdown.append(("MACD", f"+{pts}", "زخم صاعد"))
        else:
            pts = min(12, int(abs(diff) / abs(macd_sig) * 100)) if macd_sig else 5
            score -= pts
            breakdown.append(("MACD", f"-{pts}", "زخم هابط"))

    # المتوسطات (وزن 20)
    close = signals.get("Close")
    sma20 = signals.get("SMA20")
    sma50 = signals.get("SMA50")
    sma200 = signals.get("SMA200")
    if close and sma20 and sma50:
        if sma200 and close > sma20 > sma50 > sma200:
            score += 15
            breakdown.append(("المتوسطات", "+15", "صاعد قوي فوق كل المتوسطات"))
        elif close > sma20 > sma50:
            score += 10
            breakdown.append(("المتوسطات", "+10", "صاعد فوق SMA20 و SMA50"))
        elif close > sma20:
            score += 5
            breakdown.append(("المتوسطات", "+5", "فوق SMA20"))
        elif close < sma20 < sma50:
            score -= 10
            breakdown.append(("المتوسطات", "-10", "هابط تحت SMA20 و SMA50"))
        elif close < sma20:
            score -= 5
            breakdown.append(("المتوسطات", "-5", "تحت SMA20"))

    # Bollinger (وزن 10)
    bb_u = signals.get("BB_Upper")
    bb_l = signals.get("BB_Lower")
    if close and bb_u and bb_l:
        if close <= bb_l:
            score += 8
            breakdown.append(("Bollinger", "+8", "قرب الحافة السفلية — ارتداد محتمل"))
        elif close >= bb_u:
            score -= 8
            breakdown.append(("Bollinger", "-8", "قرب الحافة العلوية — ضغط بيعي"))

    # Stochastic (وزن 10)
    stoch_k = signals.get("Stoch_K")
    stoch_d = signals.get("Stoch_D")
    if stoch_k is not None and stoch_d is not None:
        if stoch_k < 20:
            score += 8
            breakdown.append(("Stochastic", "+8", "تشبع بيعي"))
        elif stoch_k > 80:
            score -= 8
            breakdown.append(("Stochastic", "-8", "تشبع شرائي"))
        elif stoch_k > stoch_d and stoch_k < 50:
            score += 4
            breakdown.append(("Stochastic", "+4", "تقاطع صاعد"))

    # ADX (وزن 10)
    adx = signals.get("ADX")
    if adx is not None:
        if adx > 25:
            # اتجاه قوي — يدعم الإشارة الحالية
            breakdown.append(("ADX", "0", f"اتجاه قوي ({adx:.0f}) — يدعم الإشارة"))
        else:
            score -= 3
            breakdown.append(("ADX", "-3", f"اتجاه ضعيف ({adx:.0f}) — تذبذب"))

    # OBV (وزن 5)
    obv = signals.get("OBV")
    obv_ma = signals.get("OBV_MA")
    if obv is not None and obv_ma is not None:
        if obv > obv_ma:
            score += 5
            breakdown.append(("OBV", "+5", "حجم يتراكم صاعد"))
        else:
            score -= 3
            breakdown.append(("OBV", "-3", "حجم يتراكم هابط"))

    # MFI (وزن 5)
    mfi = signals.get("MFI")
    if mfi is not None:
        if mfi < 20:
            score += 5
            breakdown.append(("MFI", "+5", "سيولة بيعية مفرطة"))
        elif mfi > 80:
            score -= 5
            breakdown.append(("MFI", "-5", "سيولة شرائية مفرطة"))

    # CCI (وزن 5)
    cci = signals.get("CCI")
    if cci is not None:
        if cci < -100:
            score += 5
            breakdown.append(("CCI", "+5", "بيع مفرط"))
        elif cci > 100:
            score -= 5
            breakdown.append(("CCI", "-5", "شراء مفرط"))

    # الحجم (وزن 5)
    vol_ratio = signals.get("Vol_Ratio")
    if vol_ratio is not None:
        if vol_ratio > 2.0:
            breakdown.append(("الحجم", "0", f"حجم شاذ ({vol_ratio:.1f}x) — تأكيد للحركة"))
        elif vol_ratio > 1.3:
            breakdown.append(("الحجم", "0", f"حجم مرتفع ({vol_ratio:.1f}x)"))

    # تقييم نهائي
    score = max(0, min(100, score))
    if score >= 75:
        verdict = "شراء قوي"
        verdict_en = "STRONG BUY"
        color = "#00c853"
    elif score >= 60:
        verdict = "شراء"
        verdict_en = "BUY"
        color = "#66bb6a"
    elif score >= 55:
        verdict = "شراء جزئي"
        verdict_en = "LEAN BUY"
        color = "#81c784"
    elif score >= 45:
        verdict = "محايد"
        verdict_en = "NEUTRAL"
        color = "#90a4ae"
    elif score >= 40:
        verdict = "بيع جزئي"
        verdict_en = "LEAN SELL"
        color = "#ef5350"
    elif score >= 25:
        verdict = "بيع"
        verdict_en = "SELL"
        color = "#e53935"
    else:
        verdict = "بيع قوي"
        verdict_en = "STRONG SELL"
        color = "#c62828"

    return {
        "score": score,
        "verdict": verdict,
        "verdict_en": verdict_en,
        "color": color,
        "breakdown": breakdown,
    }


def calculate_price_targets(signals: dict, df: pd.DataFrame) -> dict:
    """
    أهداف سعرية من مصادر متعددة:
    - ATR-based (1x, 1.5x, 2x, 3x)
    - Fibonacci Retracement (23.6%, 38.2%, 50%, 61.8%, 78.6%)
    - Pivot Points (S1,S2,S3, R1,R2,R3)
    - إجمالي الهدف المتوقع (تقدير)
    """
    close = signals.get("Close")
    high = signals.get("High")
    low = signals.get("Low")
    atr = signals.get("ATR")

    targets = {}

    # ATR Targets
    if close and atr:
        targets["ATR"] = {
            "entry": close,
            "stop_loss": close - 1.0 * atr,
            "T1": close + 1.5 * atr,
            "T2": close + 2.5 * atr,
            "T3": close + 3.5 * atr,
        }

    # Fibonacci Retracement (من آخر swing high/low)
    if df is not None and len(df) > 20:
        recent = df.tail(60)
        swing_high = float(recent["High"].max())
        swing_low = float(recent["Low"].min())
        diff = swing_high - swing_low
        if diff > 0 and close:
            fib_levels = [0.236, 0.382, 0.5, 0.618, 0.786]
            fib_retracement = {}
            for level in fib_levels:
                price = swing_high - diff * level
                fib_retracement[f"{level*100:.1f}%"] = round(price, 2)
            targets["Fibonacci"] = {
                "swing_high": round(swing_high, 2),
                "swing_low": round(swing_low, 2),
                "levels": fib_retracement,
                "note": "مستويات ارتداد فيبوناتشي من آخر حركة"
            }

    # Pivot Points
    if high and low and close:
        pivot = (high + low + close) / 3
        r1 = 2 * pivot - low
        r2 = pivot + (high - low)
        r3 = high + 2 * (pivot - low)
        s1 = 2 * pivot - high
        s2 = pivot - (high - low)
        s3 = low - 2 * (high - pivot)
        targets["Pivot"] = {
            "pivot": round(pivot, 2),
            "R1": round(r1, 2),
            "R2": round(r2, 2),
            "R3": round(r3, 2),
            "S1": round(s1, 2),
            "S2": round(s2, 2),
            "S3": round(s3, 2),
        }

    # حساب أهداف السوينغ ونسبة العائد إلى المخاطرة (Risk-to-Reward)
    if close:
        price = float(close)
        atr_v = float(atr) if atr and atr > 0 else price * 0.025
        if not targets.get("ATR"):
            targets["ATR"] = {
                "entry": round(price, 2),
                "stop_loss": round(price - 1.5 * atr_v, 2),
                "T1": round(price + 1.2 * atr_v, 2),
                "T2": round(price + 2.0 * atr_v, 2),
                "T3": round(price + 3.0 * atr_v, 2),
            }
        t1 = float(targets["ATR"]["T1"])
        t2 = float(targets["ATR"]["T2"])
        t3 = float(targets["ATR"].get("T3", price + 3.0 * atr_v))
        stop = float(targets["ATR"]["stop_loss"])

        expected_up = max(0.5, (t1 - price) / price * 100)
        max_up = max(1.0, (t2 - price) / price * 100)
        stop_pct = max(0.5, (price - stop) / price * 100)
        rr = round(expected_up / stop_pct, 1) if stop_pct > 0 else 1.5

        targets["summary"] = {
            "entry": round(price, 2),
            "stop_loss": round(stop, 2),
            "stop_loss_pct": round(stop_pct, 1),
            "T1": round(t1, 2),
            "T1_pct": round(expected_up, 1),
            "T2": round(t2, 2),
            "T2_pct": round(max_up, 1),
            "expected_rise_pct": round(expected_up, 1),
            "max_rise_pct": round(max_up, 1),
            "risk_reward_1": rr,
            "risk_reward_str": f"1:{rr}",
        }

    return targets


def get_intraday_levels(df: pd.DataFrame) -> dict:
    """مستويات اليوم للمضاربة (High/Low اليوم، أمس، Pivot)."""
    if df.empty or len(df) < 2:
        return {}
    last = df.iloc[-1]
    # إذا البيانات يومية، استخدم آخر يوم
    # إذا لحظية، احسب مستويات اليوم
    try:
        # حاول تحديد اليوم الحالي من الـ index
        today = df.tail(20)  # آخر 20 شمعة تقريباً
        day_high = today["High"].max()
        day_low = today["Low"].min()
        day_open = today["Open"].iloc[0] if len(today) else last["Open"]
        # Pivot تقليدي
        pivot = (day_high + day_low + float(last["Close"])) / 3
        r1 = 2*pivot - day_low
        s1 = 2*pivot - day_high
        return {
            "day_high": float(day_high),
            "day_low": float(day_low),
            "day_open": float(day_open),
            "pivot": float(pivot),
            "R1": float(r1),
            "S1": float(s1),
        }
    except:
        return {}
