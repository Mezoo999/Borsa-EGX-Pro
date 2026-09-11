"""وحدة إدارة المخاطر (Risk Management) - منصة متقدمة كأفضل متداول محترف."""
import numpy as np
import pandas as pd


def calculate_atr_based_stops(
    signals: dict, action: str, atr_mult: float = 2.0
) -> dict:
    """
    حساب مستويات إيقاف الخسارة وجني الأرباح بناءً على ATR (متوسط المدى الحقيقي).
    هذه الطريقة يستخدمها المحترفون لأنها تتكيف مع تقلبات السهم.
    """
    close = signals.get("Close")
    atr = signals.get("ATR")
    if not close or not atr:
        return {}

    price = float(close)
    atr_v = float(atr)
    stop = None
    targets = {}

    if action in ("شراء", "شراء جزئي"):
        stop = price - (atr_mult * atr_v)
        # أهداف ربحيّة متدرجة (كتاب قواعد المحترفين)
        targets["الهدف الأول (1:1)"] = price + (1.0 * atr_v)
        targets["الهدف الثاني (1.5:1)"] = price + (1.5 * atr_v)
        targets["الهدف الثالث (2:1)"] = price + (2.0 * atr_v)
    else:
        stop = price + (atr_mult * atr_v)
        targets["الهدف الأول (1:1)"] = price - (1.0 * atr_v)
        targets["الهدف الثاني (1.5:1)"] = price - (1.5 * atr_v)
        targets["الهدف الثالث (2:1)"] = price - (2.0 * atr_v)

    return {"price": price, "atr": atr_v, "stop": stop, "targets": targets}


def position_sizing(
    capital: float,
    risk_percent: float,
    entry_price: float,
    stop_price: float,
    max_portfolio_pct: float = 10.0,
) -> dict:
    """
    حساب حجم المركز (Position Sizing) وفق منهجية إدارة المخاطر الاحترافية.
    المخاطرة = نسبة من رأس المال لكل صفقة، ويتم حساب عدد الأسهم.
    """
    if not capital or capital <= 0 or not entry_price or entry_price <= 0 or not stop_price:
        return {"error": "بيانات غير كافية لحساب حجم المركز"}

    risk_amount = capital * (risk_percent / 100.0)
    per_share_risk = abs(entry_price - stop_price)
    if per_share_risk <= 0:
        return {"error": "المسافة بين الدخول والإيقاف غير صالحة"}

    shares = int(risk_amount / per_share_risk)
    position_value = shares * entry_price

    # حد أقصى لنسبة محفظتك في سهم واحد
    max_position_value = capital * (max_portfolio_pct / 100.0)
    if position_value > max_position_value:
        shares = int(max_position_value / entry_price)
        position_value = shares * entry_price

    return {
        "رأس_المال": capital,
        "نسبة_المخاطرة": risk_percent,
        "مبلغ_المخاطرة": risk_amount,
        "عدد_الأسهم": shares,
        "قيمة_المركز": position_value,
        "نسبة_المركز_من_المحفظة": (position_value / capital * 100.0) if capital else 0,
        "المخاطرة_لكل_سهم": per_share_risk,
        "الدخول": entry_price,
        "الإيقاف": stop_price,
    }


def risk_score(signals: dict, df: pd.DataFrame) -> dict:
    """
    تقييم المخاطر العام للسهم (0-100): كلما زاد الرقم زادت الخطورة.
    يُحسب من التقلب (ATR%)، وضع السعر من القمة، والاتجاه.
    """
    risk = 0
    notes = []

    close = signals.get("Close")
    atr = signals.get("ATR")
    if close and atr:
        atr_pct = (atr / close) * 100.0
        if atr_pct > 5:
            risk += 40
            notes.append(f"تقلب مرتفع جداً (ATR {atr_pct:.1f}% من السعر)")
        elif atr_pct > 3:
            risk += 25
            notes.append(f"تقلب مرتفع (ATR {atr_pct:.1f}%)")
        elif atr_pct > 1.5:
            risk += 10
            notes.append(f"تقلب متوسط (ATR {atr_pct:.1f}%)")
        else:
            notes.append(f"تقلب منخفض (ATR {atr_pct:.1f}%)")

    rsi = signals.get("RSI")
    if rsi is not None:
        if rsi > 80:
            risk += 25
            notes.append("سهم في ذروة شراء شديدة (خطر ارتداد)")
        elif rsi > 70:
            risk += 15
            notes.append("سهم في منطقة شراء مفرط")
        elif rsi < 20:
            risk += 20
            notes.append("سهم في ذروة بيع شديدة (خطر استمرار الهبوط)")

    # بعد السعر عن قمته (تراجع)
    if not df.empty:
        recent = df.tail(120)
        high = recent["High"].max()
        if close and high:
            drawdown = (high - close) / high * 100.0
            if drawdown > 20:
                risk += 20
                notes.append(f"السهم تراجع {drawdown:.0f}% عن قمته خلال 6 شهور")
            elif drawdown > 10:
                risk += 10
                notes.append(f"السهم تراجع {drawdown:.0f}% عن قمته")

    return {
        "risk_score": min(risk, 100),
        "level": "مرتفع" if risk >= 60 else ("متوسط" if risk >= 35 else "منخفض"),
        "notes": notes,
    }
