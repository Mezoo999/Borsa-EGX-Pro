"""محرك الفحص الشامل للسوق (Screener Engine) - احترافي."""
import pandas as pd
import numpy as np
from .technical import add_indicators, get_last_signals
from .signals import generate_signal
from .data import get_company_name


def build_screener(bulk_data: dict) -> pd.DataFrame:
    """
    بناء جدول الفحص الشامل من البيانات المجمعة.
    كل سهم -> صف يحتوي السعر + المؤشرات + الإشارة.
    """
    rows = []
    for sym, df in bulk_data.items():
        if df is None or df.empty or len(df) < 30:
            continue
        try:
            df_ind = add_indicators(df)
            sig = get_last_signals(df_ind)
            signal = generate_signal(sig, df_ind)

            last = df.iloc[-1]
            prev = df.iloc[-2] if len(df) > 1 else last
            change = ((last["Close"] - prev["Close"]) / prev["Close"] * 100) if prev["Close"] else 0

            # اتجاه SMA
            sma_trend = "محايد"
            if sig.get("Close") and sig.get("SMA20") and sig.get("SMA50"):
                if sig["Close"] > sig["SMA20"] > sig["SMA50"]:
                    sma_trend = "صاعد قوي"
                elif sig["Close"] > sig["SMA20"]:
                    sma_trend = "صاعد"
                elif sig["Close"] < sig["SMA20"] < sig["SMA50"]:
                    sma_trend = "هابط قوي"
                elif sig["Close"] < sig["SMA20"]:
                    sma_trend = "هابط"

            rows.append({
                "الرمز": sym,
                "الشركة": get_company_name(sym),
                "السعر": round(float(last["Close"]), 2),
                "التغير%": round(float(change), 2),
                "الحجم": int(last["Volume"]),
                "قيمة_التداول_م": sig.get("Turnover_M", round(float(last["Close"] * last["Volume"]) / 1e6, 2)),
                "السيولة": sig.get("Liquidity_Status", "سيولة مقبولة"),
                "RSI": round(float(sig.get("RSI", np.nan)), 1) if sig.get("RSI") is not None else np.nan,
                "SMA_trend": sma_trend,
                "النموذج": signal.get("setup", "تداول عرضي"),
                "الإشارة": signal["action"],
                "الثقة%": int(signal["confidence"]*100),
                "score": signal["score"],
                "_df": df_ind,  # للاستخدام الداخلي
            })
        except Exception as e:
            continue

    if not rows:
        return pd.DataFrame()

    df_out = pd.DataFrame(rows)
    # ترتيب افتراضي حسب القيمة السوقية الضمنية (السعر*الحجم تقريباً) أو حسب التغير
    return df_out


def market_summary(screener_df: pd.DataFrame) -> dict:
    """ملخص السوق من جدول الفحص."""
    if screener_df.empty:
        return {}
    gainers = len(screener_df[screener_df["التغير%"] > 0])
    losers = len(screener_df[screener_df["التغير%"] < 0])
    flat = len(screener_df[screener_df["التغير%"] == 0])
    avg_change = screener_df["التغير%"].mean()
    total_vol = screener_df["الحجم"].sum()
    buy_signals = len(screener_df[screener_df["الإشارة"].str.contains("شراء", na=False)])
    sell_signals = len(screener_df[screener_df["الإشارة"].str.contains("بيع", na=False)])
    return {
        "gainers": gainers,
        "losers": losers,
        "flat": flat,
        "avg_change": round(float(avg_change), 2),
        "total_volume": int(total_vol),
        "buy_signals": buy_signals,
        "sell_signals": sell_signals,
        "total": len(screener_df),
    }
