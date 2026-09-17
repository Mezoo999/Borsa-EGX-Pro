# -*- coding: utf-8 -*-
"""اختبارات دخان لمحركات EGX Pro (بدون إنترنت).

التشغيل:
    python tests/smoke_test.py
"""
import os
import sys

import numpy as np
import pandas as pd

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)

passed, failed = [], []


def check(name, fn):
    try:
        fn()
        passed.append(name)
        print("[PASS] " + name)
    except Exception as e:  # noqa: BLE001
        failed.append((name, e))
        print("[FAIL] " + name + " -> " + type(e).__name__ + ": " + str(e))


def _synth(n=300, seed=42):
    rng = np.random.default_rng(seed)
    close = 50 + np.cumsum(rng.normal(0.05, 0.8, n))
    idx = pd.date_range("2025-01-01", periods=n, freq="B")
    return pd.DataFrame({
        "Open": close, "High": close * 1.01, "Low": close * 0.99,
        "Close": close, "Volume": np.abs(rng.normal(1e6, 2e5, n)),
    }, index=idx)


def t_technical():
    from modules.technical import add_indicators, get_last_signals
    d = add_indicators(_synth())
    sig = get_last_signals(d)
    assert "RSI" in sig and 0 <= sig["RSI"] <= 100
    assert "SMA20" in sig and "ATR" in sig


def t_indicator_bounds():
    from modules.technical import add_indicators, get_last_signals
    sig = get_last_signals(add_indicators(_synth(400)))
    for k in ("RSI", "RSI_9", "Stoch_K", "MFI", "ADX", "CCI"):
        v = sig.get(k)
        if v is not None:
            assert -200 <= v <= 200, f"{k} خارج النطاق: {v}"


def t_signals():
    from modules.technical import add_indicators, get_last_signals
    from modules.signals import generate_signal, calculate_technical_score
    d = add_indicators(_synth())
    sig = get_last_signals(d)
    sw = generate_signal(sig, d)
    sc = calculate_technical_score(sig, d)
    assert sw["action"] in ("شراء مؤكد", "شراء تدريجي", "بيع / خروج", "تخفيف / حذر", "انتظار / مراقبة")
    assert 0 <= sc["score"] <= 100


def t_targets_order():
    from modules.technical import add_indicators, get_last_signals
    from modules.signals import calculate_price_targets
    d = add_indicators(_synth())
    s = calculate_price_targets(get_last_signals(d), d)["summary"]
    assert s["stop_loss"] < s["entry"] < s["T1"] < s["T2"], f"ترتيب غلط: {s}"


def t_risk():
    from modules.risk import position_sizing
    r = position_sizing(100000, 2.0, 50.0, 45.0, 10.0)
    assert r["عدد_الأسهم"] > 0
    assert r["قيمة_المركز"] <= 100000 * 0.10 + 1


def t_storage_default():
    from modules.storage import DEFAULT_STORE
    for k in ("watchlist", "portfolio", "alerts", "ideas", "rec_log", "settings"):
        assert k in DEFAULT_STORE


def t_storage_buy_math():
    """متوسط التكلفة المدمج يُحسب صحيحاً (مع تعطيل الحفظ)."""
    import modules.storage as st
    st.save_store = lambda *a, **k: None  # تعطيل الكتابة على القرص
    store = {"portfolio": {"COMI.CA": {"shares": 100, "avg_cost": 50.0, "date": "2026-01-01"}}}
    st.buy_position(store, "COMI.CA", 100, 70.0)
    p = store["portfolio"]["COMI.CA"]
    assert p["shares"] == 200 and abs(p["avg_cost"] - 60.0) < 1e-6, p


def t_sectors_taxonomy():
    from modules.data import SECTORS
    bad = [k for k in SECTORS if not k.endswith(".CA")]
    assert not bad, "مفاتيح قطاعات غير صحيحة: " + str(bad[:5])


def t_backtest_threshold():
    from modules.backtest import backtest_signals
    r = backtest_signals(_synth(400), hold_days=5, threshold=4)
    assert "error" not in r or r.get("total") == 0


def t_notify_fallback():
    """بدون قنوات خارجية → fallback محلي (لا يرفع استثناء)."""
    from modules import notify
    for k in ("TELEGRAM_BOT_TOKEN", "TELEGRAM_CHAT_ID", "WEBHOOK_URL"):
        os.environ.pop(k, None)
    res = notify.send("test", "body")
    assert isinstance(res, list) and res, "يجب أن يعيد قائمة نتائج"
    assert res[0][0] == "log", f"متوقع fallback محلي، وجد {res}"


def t_notify_enabled_false():
    from modules import notify
    for k in ("TELEGRAM_BOT_TOKEN", "TELEGRAM_CHAT_ID", "WEBHOOK_URL"):
        os.environ.pop(k, None)
    assert notify.enabled() is False


def t_signal_series():
    from modules.technical import add_indicators
    from modules.signals import signal_series
    d = signal_series(add_indicators(_synth(300)))
    assert "sig_buy" in d.columns and "sig_sell" in d.columns
    assert not (d["sig_buy"] & d["sig_sell"]).any()


def t_sentiment():
    from modules.sentiment import score_text, analyze_news
    assert score_text("أرباح ونمو وارتفاع")[0] == "إيجابي"
    assert score_text("خسائر وتراجع")[0] == "سلبي"
    assert analyze_news([{"title": "أرباح قوية"}])["overall"] == "إيجابية"


def t_patterns():
    from modules.patterns import pattern_series, recent_patterns
    d = pattern_series(_synth(120))
    assert "pat_bull" in d.columns and "pat_bear" in d.columns
    assert isinstance(recent_patterns(_synth(120)), list)


def t_peer_compare():
    from modules.peer_compare import compare
    db = {"A.CA": {"pe_ref": 5, "roe": 0.2}, "B.CA": {"pe_ref": 9, "roe": 0.1}}
    r = compare("A.CA", lambda s: "بنوك", db)
    assert not r.get("error") and len(r["rows"]) == 5
    assert compare("Z.CA", lambda s: "x", db).get("error")


def t_events():
    import pandas as pd
    from modules.events import get_events
    class FakeT:
        dividends = pd.Series([0.5, 0.7], index=pd.to_datetime(["2025-01-01", "2025-06-01"]))
        splits = pd.Series([], dtype=float)
        info = {"exDividendDate": 1780000000}
    r = get_events("X.CA", ticker=FakeT())
    assert len(r["dividends"]) == 2 and len(r["upcoming"]) >= 1


def t_performance_track():
    from modules.performance_track import evaluate
    recs = [{"symbol": "A.CA", "entry": 100, "stop": 95, "t1": 110, "date": "2026-01-01"},
            {"symbol": "B.CA", "entry": 50, "stop": 45, "t1": 60, "date": "2026-01-02"}]
    s = evaluate(recs, {"A.CA": 112, "B.CA": 44})["summary"]
    assert s["closed"] == 2 and s["wins"] == 1 and s["losses"] == 1
    assert s["win_rate"] == 50.0


def t_risk_dashboard():
    from modules.risk_dashboard import analyze
    r = analyze({"A.CA": {"shares": 100, "avg_cost": 10}}, {"A.CA": 12}, {"A.CA": "بنوك"})
    assert r["count"] == 1 and r["top_weight"] == 100.0
    assert analyze({}, {}, {}).get("empty")


def t_report_export():
    from modules.report_export import render
    h = render("COMI.CA", "CIB", [{"title": "السعر", "items": [("الآن", 120)]},
                                  {"title": "ملاحظات", "lines": ["نقطة"]}])
    assert "COMI" in h and "<!DOCTYPE html>" in h


def t_theories():
    from modules.theories import dow_analysis, elliott_analysis, fibonacci_levels
    d = _synth(200)
    assert "trend" in dow_analysis(d) or "error" in dow_analysis(d)
    assert "label" in elliott_analysis(d)
    assert "levels" in fibonacci_levels(d)


def t_time_analysis():
    from modules.time_analysis import day_of_week_stats, monthly_stats, summary
    d = _synth(400)
    assert not day_of_week_stats(d).empty
    assert not monthly_stats(d).empty
    assert "نسبة الأيام الرابحة %" in summary(d)


def t_confluence():
    from modules.confluence import analyze_confluence
    r = analyze_confluence("TEST.CA", _synth(200), info={})
    assert "conviction" in r and 0 <= r["conviction"] <= 100
    assert "verdict" in r and "color" in r
    assert "factors" in r and len(r["factors"]) >= 8
    assert r["pos"] + r["neg"] <= r["total"]


check("technical", t_technical)
check("indicator bounds", t_indicator_bounds)
check("signals", t_signals)
check("targets order", t_targets_order)
check("risk sizing", t_risk)
check("storage default", t_storage_default)
check("storage buy math", t_storage_buy_math)
check("sectors taxonomy", t_sectors_taxonomy)
check("backtest threshold", t_backtest_threshold)
check("notify fallback", t_notify_fallback)
check("notify enabled", t_notify_enabled_false)
check("signal series", t_signal_series)
check("confluence", t_confluence)
check("theories", t_theories)
check("time analysis", t_time_analysis)
check("performance track", t_performance_track)
check("risk dashboard", t_risk_dashboard)
check("report export", t_report_export)
check("sentiment", t_sentiment)
check("patterns", t_patterns)
check("peer compare", t_peer_compare)
check("events", t_events)

print("")
print("=" * 50)
print("نتيجة: " + str(len(passed)) + " ناجح / " + str(len(failed)) + " فاشل")
for n, e in failed:
    print("  ✗ " + n + ": " + str(e))
sys.exit(1 if failed else 0)
