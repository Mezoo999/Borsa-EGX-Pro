"""محرك الاحتمالات المدرب (Quant ML) — يتعلم من تاريخ البورصة المصرية فعلياً.

صدق المنهجية (أهم من أي شيء):
- المزايا تُحسب من المؤشرات عند كل يوم تاريخي فقط (لا تسرب مستقبلي)
- التدريب على أول 80% من الخط الزمني، والاختبار على آخر 20% التي لم يرها النموذج
- المخرجات: دقة الاختبار + AUC + المعدل الأساسي — أرقام صادقة تُعرض للمستخدم
- الاحتمال الناتج = تقدير إحصائي لنجاح إشارة الشراء على مدى 5 جلسات، وليس ضماناً
"""
import os
from datetime import datetime

import joblib
import numpy as np
import pandas as pd

MODEL_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "models")
MODEL_PATH = os.path.join(MODEL_DIR, "egx_ml.joblib")

HORIZON_DAYS = 5  # أفق التوقع: 5 جلسات تداول — مناسب للتداول القصير

FEATURES = [
    "rsi", "rsi9", "macd_hist_pct", "vol_ratio", "dist_sma20", "dist_sma50",
    "dist_sma200", "roc12", "atr_pct", "stoch_k", "mfi", "bb_pos",
]


def _features_from_row(row: pd.Series) -> dict:
    close = float(row["Close"])
    up_bb = float(row.get("BB_Upper", np.nan))
    lo_bb = float(row.get("BB_Lower", np.nan))
    bb_pos = (close - lo_bb) / (up_bb - lo_bb) if up_bb and lo_bb and up_bb > lo_bb else 0.5
    macd_h = float(row.get("MACD_Hist", 0) or 0)
    atr = float(row.get("ATR", np.nan))
    sma200 = float(row.get("SMA200", np.nan))
    return {
        "rsi": float(row.get("RSI", 50)),
        "rsi9": float(row.get("RSI_9", 50)),
        "macd_hist_pct": macd_h / close * 10000,
        "vol_ratio": float(row.get("Vol_Ratio", 1)),
        "dist_sma20": close / float(row["SMA20"]) - 1 if row.get("SMA20") else 0,
        "dist_sma50": close / float(row["SMA50"]) - 1 if row.get("SMA50") else 0,
        "dist_sma200": close / sma200 - 1 if sma200 and not np.isnan(sma200) else 0,
        "roc12": float(row.get("ROC", 0) or 0),
        "atr_pct": atr / close * 100 if atr and not np.isnan(atr) else 2.0,
        "stoch_k": float(row.get("Stoch_K", 50)),
        "mfi": float(row.get("MFI", 50)),
        "bb_pos": bb_pos,
    }


def build_dataset(top_n: int = 60, period: str = "2y", verbose: bool = True) -> pd.DataFrame:
    from .tv_data import get_registry
    from .data import get_stock_data
    from .technical import add_indicators

    reg = get_registry()
    syms = sorted(reg.keys(),
                  key=lambda s: (reg[s].get("tv") or {}).get("market_cap") or 0,
                  reverse=True)[:top_n]
    rows = []
    for i, sym in enumerate(syms):
        try:
            df = get_stock_data(sym, period)
            if df is None or len(df) < 120:
                continue
            df = add_indicators(df)
            closes = df["Close"].values
            for j in range(60, len(df) - HORIZON_DAYS):
                row = df.iloc[j]
                f = _features_from_row(row)
                fwd = closes[j + HORIZON_DAYS] / closes[j] - 1
                f["date"] = df.index[j]
                f["symbol"] = sym
                f["fwd_ret"] = fwd
                f["target"] = 1 if fwd > 0 else 0
                rows.append(f)
        except Exception:
            continue
        if verbose and (i + 1) % 10 == 0:
            print(f"  ... {i + 1}/{len(syms)} سهم")
    return pd.DataFrame(rows)


def train(top_n: int = 60, verbose: bool = True) -> dict:
    """تدريب كامل مع اختبار زمني صادق — يعيد الم metrics ويحفظ النموذج."""
    from sklearn.ensemble import GradientBoostingClassifier
    from sklearn.metrics import accuracy_score, roc_auc_score

    if verbose:
        print(f"📥 بناء قاعدة البيانات من أكبر {top_n} سهم (سنتان يومياً)...")
    ds = build_dataset(top_n=top_n, verbose=verbose)
    if len(ds) < 2000:
        return {"error": f"بيانات غير كافية للتدريب ({len(ds)} صف)"}

    ds = ds.sort_values("date")
    # تنظيف صارم: صفوف بمزايا ناقصة أو لانهائية تُحذف (أغلبها بدايات سلاسل المؤشرات)
    ds = ds.replace([np.inf, -np.inf], np.nan).dropna(subset=FEATURES)
    if len(ds) < 2000:
        return {"error": f"بيانات غير كافية للتدريب ({len(ds)} صف)"}
    cutoff = ds["date"].quantile(0.8)
    train, test = ds[ds["date"] < cutoff], ds[ds["date"] >= cutoff]

    model = GradientBoostingClassifier(n_estimators=200, max_depth=3, learning_rate=0.06,
                                       subsample=0.9, random_state=42)
    model.fit(train[FEATURES], train["target"])

    prob = model.predict_proba(test[FEATURES])[:, 1]
    pred = (prob >= 0.5).astype(int)
    acc = accuracy_score(test["target"], pred)
    auc = roc_auc_score(test["target"], prob)
    base_rate = test["target"].mean() * 100

    # أداء عملي: ماذا لو اشترينا فقط عندما النموذج واثق (>60%)؟
    conf = prob >= 0.60
    conf_acc = accuracy_score(test["target"][conf], pred[conf]) * 100 if conf.sum() > 30 else None
    conf_n = int(conf.sum())

    metrics = {
        "trained_at": datetime.now().strftime("%Y-%m-%d %H:%M"),
        "samples_train": int(len(train)),
        "samples_test": int(len(test)),
        "accuracy_test": round(acc * 100, 1),
        "auc_test": round(auc, 3),
        "base_rate_up": round(base_rate, 1),
        "confident_trades": conf_n,
        "confident_win_rate": round(conf_acc, 1) if conf_acc else None,
        "horizon_days": HORIZON_DAYS,
    }

    os.makedirs(MODEL_DIR, exist_ok=True)
    joblib.dump({"model": model, "features": FEATURES, "metrics": metrics}, MODEL_PATH)
    if verbose:
        print("✅ النموذج محفوظ:", MODEL_PATH)
        print(f"   دقة الاختبار: {metrics['accuracy_test']}% | AUC: {metrics['auc_test']} | المعدل الأساسي: {metrics['base_rate_up']}%")
        if conf_acc:
            print(f"   عندما واثق (>60%): {conf_n} صفقة بنجاح {metrics['confident_win_rate']}%")
    return metrics


def load_model():
    if not os.path.exists(MODEL_PATH):
        return None
    try:
        return joblib.load(MODEL_PATH)
    except Exception:
        return None


def predict_probability(df_with_indicators: pd.DataFrame):
    """احتمال نجاح شراء الآن (أفق 5 جلسات) — من أحدث شمعة. يعيد (احتمال, metrics)."""
    bundle = load_model()
    if not bundle or df_with_indicators is None or df_with_indicators.empty:
        return None, None
    row = df_with_indicators.iloc[-1]
    try:
        f = _features_from_row(row)
        x = pd.DataFrame([f])[bundle["features"]]
        prob = float(bundle["model"].predict_proba(x)[0, 1])
        return prob, bundle.get("metrics")
    except Exception:
        return None, bundle.get("metrics")
