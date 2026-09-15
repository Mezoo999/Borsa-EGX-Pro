"""محرك اختبار الاستراتيجية (Backtesting) - يثبت مصداقية التوصيات مجاناً."""
import pandas as pd
import numpy as np
from .technical import add_indicators, get_last_signals
from .signals import generate_signal


def backtest_signals(df: pd.DataFrame, hold_days: int = 5, threshold: int = 4,
                     round_trip_fee_pct: float = 0.55) -> dict:
    """
    اختبار الاستراتيجية على البيانات التاريخية — صافي بعد العمولات.
    round_trip_fee_pct: مصاريف الدورة الكاملة (عمولة وسيط + رسوم بورصة وقيد) —
    قيمة محافظة 0.55% تُخصم من كل صفقة حتى لا تكون نسب النجاح متفائلة زوراً.
    """
    if df is None or df.empty or len(df) < 100:
        return {"error": "بيانات غير كافية للاختبار (يحتاج 100 يوم على الأقل)"}

    df_ind = add_indicators(df.copy())
    # نحسب الإشارة لكل يوم تاريخياً (باستخدام نافذة متحركة)
    trades = []
    for i in range(60, len(df_ind) - hold_days):
        window = df_ind.iloc[:i+1]
        last_row = window.iloc[-1]
        # نحتاج إشارات ذلك اليوم
        # نبني dict مبسط
        sig = {}
        try:
            sig["RSI"] = float(window["RSI"].iloc[-1])
            sig["SMA20"] = float(window["SMA20"].iloc[-1])
            sig["SMA50"] = float(window["SMA50"].iloc[-1])
            sig["SMA200"] = float(window["SMA200"].iloc[-1]) if "SMA200" in window.columns else np.nan
            sig["Close"] = float(window["Close"].iloc[-1])
            sig["MACD"] = float(window["MACD"].iloc[-1])
            sig["MACD_Signal"] = float(window["MACD_Signal"].iloc[-1])
            sig["BB_Upper"] = float(window["BB_Upper"].iloc[-1])
            sig["BB_Lower"] = float(window["BB_Lower"].iloc[-1])
            sig["ATR"] = float(window["ATR"].iloc[-1])
            sig["Volume"] = float(window["Volume"].iloc[-1])
            sig["Vol_MA20"] = float(window["Vol_MA20"].iloc[-1])
            sig["Vol_Ratio"] = float(window["Vol_Ratio"].iloc[-1]) if "Vol_Ratio" in window.columns else 1.0
            sig["Turnover_M"] = (float(window["Turnover"].iloc[-1]) / 1e6) if "Turnover" in window.columns else 0.0
            sig["ST_dir"] = float(window["ST_dir"].iloc[-1]) if "ST_dir" in window.columns else 0.0
            if np.isnan(sig["RSI"]) or np.isnan(sig["SMA20"]):
                continue
        except:
            continue

        # إشارة ذلك اليوم
        signal = generate_signal(sig, window)
        action = signal["action"]
        strength = signal.get("score", 0)  # قوة الإشارة (score) لتفعيل حد threshold
        price_entry = float(window["Close"].iloc[-1])
        price_exit = float(df_ind["Close"].iloc[i+hold_days])
        # العائد صافي بعد عمولات الدورة الكاملة
        ret = (price_exit - price_entry) / price_entry * 100 - round_trip_fee_pct

        # نختبر فقط الإشارات التي تتجاوز حد القوة المطلوب (threshold)
        if "شراء" in action and strength >= threshold:
            trades.append({"action": "شراء", "entry": price_entry, "exit": price_exit, "return": ret, "win": ret > 0})
        elif "بيع" in action and strength <= -threshold:
            # للبيع: الربح عندما ينخفض السعر (إغلاق مركز قائم)
            ret_short = (price_entry - price_exit) / price_entry * 100 - round_trip_fee_pct
            trades.append({"action": "بيع", "entry": price_entry, "exit": price_exit, "return": ret_short, "win": ret_short > 0})

    if not trades:
        return {"total": 0, "win_rate": 0, "avg_return": 0, "message": "لا توجد إشارات كافية في الفترة"}

    df_tr = pd.DataFrame(trades)
    total = len(df_tr)
    wins = len(df_tr[df_tr["win"]])
    win_rate = wins / total * 100 if total else 0
    avg_ret = df_tr["return"].mean()
    avg_win = df_tr[df_tr["win"]]["return"].mean() if wins else 0
    avg_loss = df_tr[~df_tr["win"]]["return"].mean() if (total-wins) else 0
    best = df_tr["return"].max()
    worst = df_tr["return"].min()

    # فصل شراء/بيع
    buy_tr = df_tr[df_tr["action"]=="شراء"]
    sell_tr = df_tr[df_tr["action"]=="بيع"]

    return {
        "total": int(total),
        "wins": int(wins),
        "losses": int(total-wins),
        "win_rate": round(float(win_rate), 1),
        "avg_return": round(float(avg_ret), 2),
        "avg_win": round(float(avg_win), 2) if not np.isnan(avg_win) else 0,
        "avg_loss": round(float(avg_loss), 2) if not np.isnan(avg_loss) else 0,
        "best": round(float(best), 2),
        "worst": round(float(worst), 2),
        "hold_days": hold_days,
        "fee_pct": round_trip_fee_pct,
        "buy_count": len(buy_tr),
        "sell_count": len(sell_tr),
        "buy_win_rate": round(len(buy_tr[buy_tr["win"]])/len(buy_tr)*100,1) if len(buy_tr) else 0,
        "sell_win_rate": round(len(sell_tr[sell_tr["win"]])/len(sell_tr)*100,1) if len(sell_tr) else 0,
        "trades": df_tr.tail(20).to_dict(orient="records"),
    }
