"""محرك التوصيات الذكية للبورصة المصرية (EGX Advisor Pro).

يحلل الأسهم باستخدام نماذج السوينغ المعتمدة في البورصة المصرية:
- ارتداد تشبع بيعي (Oversold Bounce)
- اختراق قمة وسيولة (Volume Breakout)
- تصحيح في مسار صاعد (Trend Pullback)
مع حساب نسبة العائد إلى المخاطرة (Risk-to-Reward Ratio) بدقة.
"""
import numpy as np
import pandas as pd
from modules.technical import add_indicators, get_last_signals
from modules.signals import generate_signal, calculate_technical_score, calculate_price_targets
from modules.expert_advisor import analyze_wyckoff_phase, INSTITUTIONAL_STOCKS, HIGH_SPECULATIVE_STOCKS


def analyze_stock_for_advisor(df: pd.DataFrame) -> dict:
    """تحليل سهم واحد وترجيع ملف كامل للتوصية (يُستخدم في الفحص الجماعي)."""
    if df is None or df.empty or len(df) < 40:
        return {}

    try:
        df_ind = add_indicators(df)
        sig = get_last_signals(df_ind)
        if not sig or "Close" not in sig:
            return {}

        close = sig["Close"]
        swing = generate_signal(sig, df_ind)
        tscore = calculate_technical_score(sig, df_ind)
        targets = calculate_price_targets(sig, df_ind)

        last = float(df["Close"].iloc[-1])
        prev = float(df["Close"].iloc[-2]) if len(df) > 1 else last
        ch_day = (last - prev) / prev * 100 if prev else 0

        # عائد آخر 20 يوم (شهر تداول) و 60 يوم
        def ret(n):
            if len(df) > n:
                p = float(df["Close"].iloc[-n - 1])
                return (last - p) / p * 100 if p else 0
            return 0
        ch_month = ret(21)
        ch_3month = ret(63)

        # بيانات الأهداف ونسبة العائد للمخاطرة R:R
        summary = targets.get("summary", {})
        stop_price = summary.get("stop_loss", close * 0.95)
        stop_pct = summary.get("stop_loss_pct", 5.0)
        t1_price = summary.get("T1", close * 1.06)
        t1_pct = summary.get("T1_pct", 6.0)
        t2_price = summary.get("T2", close * 1.12)
        t2_pct = summary.get("T2_pct", 12.0)
        rr_str = summary.get("risk_reward_str", "1:1.5")
        rr_num = summary.get("risk_reward_1", 1.5)

        # ثقة الإشارة
        confidence = int(swing["confidence"] * 100)

        # تحليل وايكوف وطبيعة السهم
        wyckoff = analyze_wyckoff_phase(df_ind, sig)
        wyckoff_tag = wyckoff.get("tag", "عرضي")
        sym_code = sig.get("symbol", "")
        # تصنيف آلي حسب القيمة السوقية الحقيقية (TradingView) — القوائم الثابتة احتياط فقط
        try:
            from modules.tv_data import stock_tier
            cat_tag = stock_tier(sym_code)
        except Exception:
            if sym_code in INSTITUTIONAL_STOCKS:
                cat_tag = "مؤسسي قيادي 🏛️"
            elif sym_code in HIGH_SPECULATIVE_STOCKS:
                cat_tag = "مضاربي حذر ⚠️"
            else:
                cat_tag = "متوسط السيولة"

        # تقييم السيولة والنشاط
        vol_ratio = sig.get("Vol_Ratio", 1.0)
        turnover_m = sig.get("Turnover_M", 0.0)
        liquidity = sig.get("Liquidity_Status", "سيولة مقبولة")

        return {
            "الرمز": sym_code,
            "السعر": round(last, 2),
            "التغير اليوم%": round(ch_day, 2),
            "شهر%": round(ch_month, 1),
            "3 شهور%": round(ch_3month, 1),
            "RSI": round(sig.get("RSI", 50), 1),
            "الاتجاه": tscore["verdict"],
            "درجة فنية": tscore["score"],
            "إشارة": swing["action"],
            "النموذج": swing.get("setup", "تداول عرضي"),
            "وايكوف": wyckoff_tag,
            "تصنيف": cat_tag,
            "ثقة%": confidence,
            "وقف خسارة": round(stop_price, 2),
            "وقف%": round(stop_pct, 1),
            "هدف1": round(t1_price, 2),
            "هدف1%": round(t1_pct, 1),
            "هدف2": round(t2_price, 2),
            "هدف2%": round(t2_pct, 1),
            "العائد/المخاطرة": rr_str,
            "rr_num": rr_num,
            "السيولة": liquidity,
            "قيمة التداول م.ج": round(turnover_m, 1),
            "حجم/متوسط": round(vol_ratio, 1) if vol_ratio else 1.0,
            "_score_sort": swing["score"] * 10 + tscore["score"] + (10 if rr_num >= 2.0 else 0) + (15 if "تجميع" in wyckoff_tag or "انطلاق" in wyckoff_tag else 0),
            "_ts_color": tscore["color"],
        }
    except Exception:
        return {}


def rank_opportunities(bulk: dict, filter_mode: str = "شراء قوي") -> pd.DataFrame:
    """
    ترتيب كل الأسهم وتوليد قائمة الفرص بناءً على قوة النموذج الفني والعائد للمخاطرة.
    filter_mode: "الكل" | "شراء قوي" | "شراء" | "بيع"
    """
    rows = []
    for sym, df in bulk.items():
        r = analyze_stock_for_advisor(df)
        if not r:
            continue
        r["الرمز"] = sym
        rows.append(r)

    if not rows:
        return pd.DataFrame()

    df_all = pd.DataFrame(rows).sort_values("_score_sort", ascending=False).reset_index(drop=True)

    if filter_mode == "شراء قوي":
        mask = (df_all["درجة فنية"] >= 60) & (df_all["ثقة%"] >= 60)
        df_out = df_all[mask]
    elif filter_mode == "شراء":
        mask = df_all["درجة فنية"] >= 55
        df_out = df_all[mask]
    elif filter_mode == "بيع":
        mask = df_all["درجة فنية"] <= 40
        df_out = df_all[mask].sort_values("_score_sort")
    else:
        df_out = df_all

    return df_out


def beginner_summary(row: dict) -> str:
    """شرح مبسط ومباشر لمستخدم تطبيق ثاندر عن فرصة السهم ونموذج الصفقة."""
    parts = []
    score = row.get("درجة فنية", 50)
    sig = row.get("إشارة", "")
    setup = row.get("النموذج", "")
    rr = row.get("العائد/المخاطرة", "1:1.5")
    t1 = row.get("هدف1", 0)
    t1_pct = row.get("هدف1%", 0)
    stop = row.get("وقف خسارة", 0)
    stop_pct = row.get("وقف%", 0)
    liq = row.get("السيولة", "")
    rsi = row.get("RSI", 50)

    parts.append(f"📌 **النموذج الفني:** {setup} (الدرجة الفنية {score}/100).")

    if "شراء" in str(sig):
        parts.append(f"🟢 **قرار ثاندر:** فرصة شراء للدخول سوينغ بنسبة عائد إلى مخاطرة **{rr}**.")
        parts.append(f"🎯 **الهدف الأول:** عند {t1:,.2f} ج.م (صعود متوقع **+{t1_pct:.1f}%**).")
        parts.append(f"🛡️ **وقف الخسارة الصارم:** عند {stop:,.2f} ج.م (مخاطرة **-{stop_pct:.1f}%**). لو كسر السعر هذا المستوى لأسفل، اخرج من الصفقة فوراً لحماية رأس مالك.")
    elif "بيع" in str(sig):
        parts.append("🔴 **قرار ثاندر:** السهم في اتجاه هابط أو تصحيحي. لا تشتري الآن واحتفظ بسيولتك.")
    else:
        parts.append("⚪ **قرار ثاندر:** السهم في مرحلة تذبذب وحيرة. الأفضل الانتظار حتى ظهور اختراق واضح.")

    # نصيحة السيولة في ثاندر
    if "ضعيفة" in str(liq):
        parts.append("⚠️ **تحذير سيولة:** السهم سيولته اليومية منخفضة في البورصة المصرية، ادخل بجزء صغير جداً من محفظتك حتى لا تصعب عليك عملية البيع.")
    elif "ممتازة" in str(liq):
        parts.append("💎 **ميزة أمان:** السهم ذو سيولة مؤسسية عالية، والدخول والخروج فيه سهل وسلس في ثاندر.")

    if rsi and rsi >= 70:
        parts.append("⚠️ السهم قريب من ذروة الشراء، لا تشترِ دفعة واحدة بل انتظر تهدئة طفيفة.")
    elif rsi and rsi <= 35:
        parts.append("✅ السهم في منطقة تشبع بيعي وقاع سعري يتيح نقطة شراء ممتازة وقريبة من الوقف.")

    return " ".join(parts)

