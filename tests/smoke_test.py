# -*- coding: utf-8 -*-
"""اختبارات دخان سريعة لمحركات EGX Pro (بدون إنترنت).

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
    sig = get_last_signals(add_indicators(_synth()))
    assert "RSI" in sig and 0 <= sig["RSI"] <= 100


def t_signals():
    from modules.technical import add_indicators, get_last_signals
    from modules.signals import generate_signal, calculate_technical_score, calculate_price_targets
    d = add_indicators(_synth())
    sig = get_last_signals(d)
    assert generate_signal(sig, d)["action"]
    assert 0 <= calculate_technical_score(sig, d)["score"] <= 100
    assert "summary" in calculate_price_targets(sig, d)


def t_risk():
    from modules.risk import position_sizing
    r = position_sizing(100000, 2.0, 50.0, 45.0, 10.0)
    assert r["عدد_الأسهم"] > 0


def t_storage():
    from modules.storage import DEFAULT_STORE
    for k in ("watchlist", "portfolio", "alerts", "ideas", "rec_log", "settings"):
        assert k in DEFAULT_STORE


def t_sectors_taxonomy():
    from modules.data import SECTORS
    bad = [k for k in SECTORS if not k.endswith(".CA")]
    assert not bad, "مفاتيح قطاعات غير صحيحة: " + str(bad[:5])


def t_backtest_threshold():
    from modules.backtest import backtest_signals
    r = backtest_signals(_synth(400), hold_days=5, threshold=4)
    assert "error" not in r or r.get("total") == 0


check("technical", t_technical)
check("signals", t_signals)
check("risk", t_risk)
check("storage", t_storage)
check("sectors taxonomy", t_sectors_taxonomy)
check("backtest threshold", t_backtest_threshold)

print("")
print("=" * 50)
print("نتيجة: " + str(len(passed)) + " ناجح / " + str(len(failed)) + " فاشل")
sys.exit(1 if failed else 0)
