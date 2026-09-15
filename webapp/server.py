"""خادم EGX Pro — الواجهة الاحترافية الجديدة (FastAPI).

يخدم واجهة ويب حقيقية بأسلوب بورتالات الاستثمار العالمية، ويشغّل نفس محركات
المنصة (أسعار TradingView، تحليل فني، أخبار، سياق عالمي، محرك احتمالات مدرب).
التشغيل: uvicorn webapp.server:app --port 8000
"""
import os
import sys
import time
import threading

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.gzip import GZipMiddleware
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles

from modules import tv_data as tvd, macro, ml_engine
import modules.news as newsfeed
from modules.data import get_stock_data, get_company_name, get_bulk_data
from modules.technical import add_indicators, get_last_signals
from modules.signals import (get_support_resistance, calculate_technical_score,
                             generate_signal, calculate_price_targets)
from modules.storage import load_store

BASE = os.path.dirname(os.path.abspath(__file__))
STATIC = os.path.join(BASE, "static")

app = FastAPI(title="EGX Pro")
app.add_middleware(GZipMiddleware, minimum_size=1024)

# خدمة ملفات الواجهة (CSS/JS)
app.mount("/static", StaticFiles(directory=STATIC), name="static")

# ---------- كاش بسيط بمهلة ----------
_cache = {}
_cache_lock = threading.Lock()


def cached(key: str, ttl: int, fn):
    now = time.time()
    with _cache_lock:
        hit = _cache.get(key)
        if hit and now - hit[0] < ttl:
            return hit[1]
    val = fn()
    with _cache_lock:
        _cache[key] = (now, val)
    return val


def _snapshot():
    return tvd.snapshot()


def _registry():
    return tvd.get_registry()


@app.get("/api/health")
def api_health():
    """فحص صحة الخادم."""
    return {"status": "ok"}


@app.get("/api/quote/{symbol}")
def api_quote(symbol: str):
    """سعر لحظي خفيف (بدون تحليل) — لتحديث السعر بسرعة في صفحة السهم."""
    symbol = symbol.upper()
    if not symbol.endswith(".CA"):
        symbol += ".CA"
    row = tvd.one(symbol)
    if not row:
        return {"error": "لا توجد بيانات"}
    return {"symbol": symbol, "short": symbol.replace(".CA", ""),
            "price": row["close"], "chg": row["change_pct"]}


# ---------- الصفحات ----------
@app.get("/")
def index():
    return FileResponse(os.path.join(STATIC, "index.html"))


@app.get("/stock/{symbol}")
def stock_page(symbol: str):
    return FileResponse(os.path.join(STATIC, "stock.html"))


# ---------- APIs ----------
@app.get("/api/search")
def api_search(q: str = Query("")):
    q = q.strip().lower()
    reg = _registry()
    out = []
    for sym, meta in reg.items():
        name = meta.get("name") or ""
        if not q or q in sym.lower().replace(".ca", "") or q in name.lower():
            out.append({"symbol": sym, "short": sym.replace(".CA", ""), "name": name})
        if len(out) >= 12:
            break
    return out


@app.get("/api/overview")
def api_overview():
    def build():
        snap = _snapshot()
        idx = tvd.indices()
        reg = _registry()
        # المؤشرات
        indices = [{"key": k, "value": v["value"], "chg": v["change_pct"]}
                   for k, v in idx.items()]
        # الشريط المتحرك: أكبر 14 سهماً
        top = sorted(reg.keys(),
                     key=lambda s: (reg[s].get("tv") or {}).get("market_cap") or 0,
                     reverse=True)[:14]
        tape = []
        for s in top:
            r = snap.get(s.replace(".CA", ""))
            if r:
                tape.append({"symbol": s.replace(".CA", ""), "price": r["close"], "chg": r["change_pct"]})
        # الماكرو
        mdata = macro.fetch_macro()
        regime_ = macro.regime(mdata) if mdata else {"label": "—", "color": "#90a4ae", "desc": ""}
        macro_cards = [{"ticker": t, "label": m_["label"], "value": m_["value"],
                        "day": m_["day_pct"], "week": m_["wk_pct"]} for t, m_ in (mdata or {}).items()]
        macro_sigs = macro.macro_signals(mdata) if mdata else []
        # التحركات
        rows = sorted(snap.values(), key=lambda r: r["change_pct"], reverse=True)
        movers = {
            "up": [{"symbol": r["symbol"], "name": r["name_tv"][:22], "price": r["close"], "chg": r["change_pct"]} for r in rows[:8]],
            "down": [{"symbol": r["symbol"], "name": r["name_tv"][:22], "price": r["close"], "chg": r["change_pct"]} for r in rows[-8:][::-1]],
        }
        breadth = {
            "up": sum(1 for r in snap.values() if r["change_pct"] > 0),
            "down": sum(1 for r in snap.values() if r["change_pct"] < 0),
            "flat": sum(1 for r in snap.values() if r["change_pct"] == 0),
        }
        # القطاعات
        acc = {}
        for sym, meta in reg.items():
            tv_r = meta.get("tv") or snap.get(sym.replace(".CA", ""))
            if tv_r and meta.get("sector"):
                acc.setdefault(meta["sector"], []).append(tv_r["change_pct"])
        sectors = sorted(({"name": s_, "chg": round(sum(v_) / len(v_), 2), "count": len(v_)}
                          for s_, v_ in acc.items() if len(v_) >= 3),
                         key=lambda x: x["chg"], reverse=True)
        # الأخبار (قائمة المتابعة + المحفظة)
        st_ = load_store()
        news_syms = (list(st_.get("watchlist", []))[:4] + list(st_.get("portfolio", {}).keys())[:2])
        news_items = []
        for sym in dict.fromkeys(news_syms):
            from modules.data import AR_NAMES
            name = AR_NAMES.get(sym, sym.replace(".CA", ""))
            for it in newsfeed.fetch_news(f'"{name}" OR {sym.replace(".CA","")} البورصة المصرية', limit=2):
                news_items.append({"symbol": sym.replace(".CA", ""), "title": it["title"],
                                   "pub": it["pub"], "source": it.get("source", ""), "link": it["link"]})
        return {"indices": indices, "tape": tape, "regime": regime_,
                "macro": macro_cards, "macro_signals": [{"tone": t, "text": x} for t, x in macro_sigs],
                "movers": movers, "breadth": breadth, "sectors": sectors, "news": news_items[:10]}
    return cached("overview", 45, build)


@app.get("/api/stock/{symbol}")
def api_stock(symbol: str):
    symbol = symbol.upper()
    if not symbol.endswith(".CA"):
        symbol += ".CA"

    def build():
        snap = _snapshot()
        reg = _registry()
        meta = reg.get(symbol, {})
        tv_r = snap.get(symbol.replace(".CA", ""))
        df = get_stock_data(symbol, "6mo")
        if df is None or df.empty:
            raise HTTPException(status_code=404, detail="لا توجد بيانات تاريخية لهذا الرمز")
        # تحديث شمعة اليوم بالسعر اللحظي
        if tv_r:
            df = df.copy()
            df.iloc[-1, df.columns.get_loc("Close")] = tv_r["close"]
            if tv_r["close"] > float(df["High"].iloc[-1]):
                df.iloc[-1, df.columns.get_loc("High")] = tv_r["close"]
            if tv_r["close"] < float(df["Low"].iloc[-1]):
                df.iloc[-1, df.columns.get_loc("Low")] = tv_r["close"]
        df_ind = add_indicators(df)
        sig = get_last_signals(df_ind)
        close = float(sig.get("Close", df["Close"].iloc[-1]))
        score = calculate_technical_score(sig, df_ind)
        swing = generate_signal(sig, df_ind)
        targets = calculate_price_targets(sig, df_ind)
        support, resistance = get_support_resistance(df_ind)
        # احتمال الذكاء الاصطناعي
        prob, ml_metrics = ml_engine.predict_probability(df_ind)
        # بطاقة الأمر — الوقف يجب أن يكون تحت سعر التفعيل دائماً
        atr = float(sig.get("ATR", close * 0.02)) or close * 0.02
        summary = targets.get("summary", {})
        stop = float(summary.get("stop_loss", close - 1.5 * atr))
        t1 = float(summary.get("T1", close + 1.5 * atr))
        t2 = float(summary.get("T2", close + 3 * atr))
        setup = swing.get("setup", "")
        if "اختراق" in setup and resistance:
            etype, trig = "أمر شراء عند الكسر", round(resistance + 0.25 * atr, 2)
        elif "ارتداد" in setup or "تشبع" in setup:
            etype, trig = "أمر شراء معلق", round(max(support or close - 1.2 * atr, close - 1.5 * atr), 2)
        else:
            etype, trig = "أمر شراء معلق", round(float(sig.get("EMA21", close * 0.98)), 2)
        # صحّح الوقف إن صار فوق/قريب جداً من سعر التفعيل: وقف صحيح = تحت التفعيل بمسافة ATR محسوبة
        if stop >= trig - 0.8 * atr:
            stop = trig - 1.5 * atr
        # والأهداف فوق التفعيل بمضاعفات المخاطرة السليمة
        risk = max(trig - stop, 0.5 * atr)
        t1 = max(t1, trig + 1.2 * risk)
        t2 = max(t2, trig + 2.0 * risk)
        rr = (t1 - trig) / risk
        # الأخبار
        name = meta.get("name") or get_company_name(symbol)
        news = newsfeed.fetch_news(f'"{name}" OR {symbol.replace(".CA","")} البورصة المصرية', limit=5)
        return {
            "symbol": symbol, "short": symbol.replace(".CA", ""), "name": name,
            "sector": meta.get("sector", ""), "live": tv_r["close"] if tv_r else close,
            "live_chg": tv_r["change_pct"] if tv_r else 0.0,
            "close": close, "high52": None, "support": support, "resistance": resistance,
            "tech_score": score.get("score"), "tech_verdict": score.get("verdict"),
            "signal": swing.get("action"), "setup": setup,
            "ml": ({"prob": round(prob * 100, 1), "metrics": ml_metrics} if prob is not None else None),
            "ticket": {"type": etype, "entry": trig, "stop": round(stop, 2),
                       "t1": round(t1, 2), "t2": round(t2, 2), "rr": f"1:{rr:.1f}"},
            "indicators": {
                "RSI": round(float(sig.get("RSI", 0)), 1),
                "MACD": "صاعد" if sig.get("MACD", 0) > sig.get("MACD_Signal", 0) else "هابط",
                "ADX": round(float(sig.get("ADX", 0)), 1),
                "MFI": round(float(sig.get("MFI", 0)), 1),
                "سيولة": sig.get("Liquidity_Status", ""),
                "وايكوف": swing.get("setup", ""),
            },
            "news": [{"title": n["title"], "pub": n["pub"], "source": n.get("source", ""), "link": n["link"]} for n in news],
        }
    return cached(f"stock_{symbol}", 120, build)


@app.get("/api/stock/{symbol}/candles")
def api_candles(symbol: str):
    symbol = symbol.upper()
    if not symbol.endswith(".CA"):
        symbol += ".CA"

    def build():
        df = get_stock_data(symbol, "6mo")
        if df is None or df.empty:
            return {"candles": []}
        tv_r = tvd.one(symbol)
        if tv_r:
            df = df.copy()
            df.iloc[-1, df.columns.get_loc("Close")] = tv_r["close"]
            if tv_r["close"] > float(df["High"].iloc[-1]):
                df.iloc[-1, df.columns.get_loc("High")] = tv_r["close"]
            if tv_r["close"] < float(df["Low"].iloc[-1]):
                df.iloc[-1, df.columns.get_loc("Low")] = tv_r["close"]
        # مهم: نحسب المتوسطات على نفس النافذة المعروضة (آخر 180 شمعة) لتفادي انزياح الخطوط
        d = df.tail(180)
        sma20 = d["Close"].rolling(20).mean()
        sma50 = d["Close"].rolling(50).mean()
        candles, volumes, l20, l50 = [], [], [], []
        for i, (idx, r) in enumerate(d.iterrows()):
            t = str(idx)[:10]
            o, h, l, c = float(r["Open"]), float(r["High"]), float(r["Low"]), float(r["Close"])
            candles.append({"time": t, "open": round(o, 2), "high": round(h, 2), "low": round(l, 2), "close": round(c, 2)})
            volumes.append({"time": t, "value": float(r["Volume"]),
                            "color": "rgba(0,200,83,0.45)" if c >= o else "rgba(255,61,87,0.45)"})
            v20, v50 = sma20.iloc[i], sma50.iloc[i]
            if v20 == v20:
                l20.append({"time": t, "value": round(float(v20), 2)})
            if v50 == v50:
                l50.append({"time": t, "value": round(float(v50), 2)})
        return {"candles": candles, "volumes": volumes, "sma20": l20, "sma50": l50}
    return cached(f"candles_{symbol}", 120, build)
