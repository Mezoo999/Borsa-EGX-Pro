"""خادم EGX Pro — الواجهة الاحترافية الجديدة (FastAPI).

يخدم واجهة ويب حقيقية بأسلوب بورتالات الاستثمار العالمية، ويشغّل نفس محركات
المنصة (أسعار TradingView، تحليل فني، أخبار، سياق عالمي، محرك احتمالات مدرب).
التشغيل: uvicorn webapp.server:app --port 8000
"""
import os
import sys
import time
import threading
from contextlib import asynccontextmanager

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.gzip import GZipMiddleware
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel

from modules import tv_data as tvd, macro, ml_engine, notify
import modules.news as newsfeed
from modules.data import get_stock_data, get_company_name, get_bulk_data
from modules.technical import add_indicators, get_last_signals
from modules.signals import (get_support_resistance, calculate_technical_score,
                             generate_signal, calculate_price_targets)
from modules.advisor import rank_opportunities
from modules.storage import (load_store, add_watch, remove_watch,
                             buy_position, sell_position, set_alert, remove_alert)

BASE = os.path.dirname(os.path.abspath(__file__))
STATIC = os.path.join(BASE, "static")

@asynccontextmanager
async def lifespan(_app):
    # خيط خلفي: فحص التنبيهات السعرية وإرسال الإشعارات كل دقيقة
    threading.Thread(target=_alert_loop, daemon=True).start()
    yield


app = FastAPI(title="EGX Pro", lifespan=lifespan)
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


# ---------- تنبيهات الأسعار + إشعارات ----------
_alert_fired = set()  # مفاتيح "YYYY-MM-DD|رمز|اتجاه" — تمنع تكرار الإشعار في اليوم نفسه


def _norm_symbol(symbol: str) -> str:
    """توحيد الرمز إلى صيغة XXXX.CA."""
    symbol = (symbol or "").strip().upper()
    if not symbol:
        return ""
    return symbol if symbol.endswith(".CA") else symbol + ".CA"


def _check_alerts():
    try:
        st_ = load_store()
        alerts = st_.get("alerts") or {}
        if not alerts:
            return
        snap = _snapshot()
        if not snap:
            return
        today = time.strftime("%Y-%m-%d")
        for sym, a in alerts.items():
            row = snap.get(sym.replace(".CA", ""))
            if not row:
                continue
            price = row["close"]
            msgs = []
            above = a.get("above")
            below = a.get("below")
            if above and price >= above and f"{today}|{sym}|above" not in _alert_fired:
                _alert_fired.add(f"{today}|{sym}|above")
                msgs.append(f"⬆️ {sym.replace('.CA', '')} صعد فوق {above:,.2f} ج.م — الآن {price:,.2f}")
            if below and price <= below and f"{today}|{sym}|below" not in _alert_fired:
                _alert_fired.add(f"{today}|{sym}|below")
                msgs.append(f"⬇️ {sym.replace('.CA', '')} هبط تحت {below:,.2f} ج.م — الآن {price:,.2f}")
            for m in msgs:
                notify.send("🔔 تنبيه سعر — EGX Pro", m)
    except Exception:
        pass


def _alert_loop():
    while True:
        try:
            _check_alerts()
        except Exception:
            pass
        time.sleep(60)


# نماذج طلبات الكتابة
class PositionIn(BaseModel):
    symbol: str
    shares: float
    avg_cost: float


class SellIn(BaseModel):
    symbol: str
    shares: float


class WatchIn(BaseModel):
    symbol: str


class AlertIn(BaseModel):
    symbol: str
    above: float | None = None
    below: float | None = None


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


@app.get("/opportunities")
def opportunities_page():
    return FileResponse(os.path.join(STATIC, "opportunities.html"))


@app.get("/portfolio")
def portfolio_page():
    return FileResponse(os.path.join(STATIC, "portfolio.html"))


@app.get("/watchlist")
def watchlist_page():
    return FileResponse(os.path.join(STATIC, "watchlist.html"))


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


# ---------- الفرص (ترتيب آلي) ----------
@app.get("/api/opportunities")
def api_opportunities(universe: int = Query(30, ge=10, le=120)):
    def build():
        reg = _registry()
        syms = sorted(reg.keys(),
                      key=lambda s: (reg[s].get("tv") or {}).get("market_cap") or 0,
                      reverse=True)[:universe]
        bulk = get_bulk_data(syms, "6mo")
        df = rank_opportunities(bulk, "الكل")
        if df is None or df.empty:
            return []
        snap = _snapshot()
        out = []
        for _, r in df.iterrows():
            sym = r.get("الرمز", "")
            tv = snap.get(sym.replace(".CA", ""))
            out.append({
                "symbol": sym, "short": sym.replace(".CA", ""),
                "name": get_company_name(sym),
                "price": round(tv["close"], 2) if tv else round(r.get("السعر", 0), 2),
                "chg": round(tv["change_pct"], 2) if tv else round(r.get("التغير اليوم%", 0), 2),
                "score": int(r.get("درجة فنية", 0)),
                "signal": r.get("إشارة", ""),
                "setup": r.get("النموذج", ""),
                "tier": r.get("تصنيف", ""),
                "wyckoff": r.get("وايكوف", ""),
                "rr": r.get("العائد/المخاطرة", ""),
                "target1": round(float(r.get("هدف1", 0)), 2),
                "stop": round(float(r.get("وقف خسارة", 0)), 2),
                "liquidity": r.get("السيولة", ""),
            })
        return out
    return cached(f"opportunities_{universe}", 300, build)


# ---------- المحفظة ----------
@app.get("/api/portfolio")
def api_portfolio():
    def build():
        st_ = load_store()
        snap = _snapshot()
        reg = _registry()
        positions = []
        tot_val = tot_cost = 0.0
        for sym, p in (st_.get("portfolio") or {}).items():
            sh = float(p["shares"]); cost = float(p["avg_cost"])
            tv = snap.get(sym.replace(".CA", ""))
            now = tv["close"] if tv else cost
            val = sh * now; basis = sh * cost; pl = val - basis
            plp = (now - cost) / cost * 100 if cost else 0
            tot_val += val; tot_cost += basis
            positions.append({
                "symbol": sym, "short": sym.replace(".CA", ""),
                "name": (reg.get(sym) or {}).get("name") or get_company_name(sym),
                "shares": int(sh), "avg_cost": round(cost, 2),
                "price": round(now, 2), "chg": round(tv["change_pct"], 2) if tv else 0,
                "value": round(val, 0), "cost": round(basis, 0),
                "pl": round(pl, 0), "pl_pct": round(plp, 2),
            })
        total_pl = tot_val - tot_cost
        return {"positions": positions,
                "summary": {"value": round(tot_val, 0), "cost": round(tot_cost, 0),
                            "pl": round(total_pl, 0),
                            "pl_pct": round(total_pl / tot_cost * 100, 2) if tot_cost else 0,
                            "count": len(positions)}}
    return cached("portfolio", 30, build)


@app.post("/api/portfolio")
def add_position(body: PositionIn):
    sym = _norm_symbol(body.symbol)
    if not sym:
        raise HTTPException(status_code=400, detail="رمز غير صالح")
    st_ = load_store()
    buy_position(st_, sym, body.shares, body.avg_cost)
    return {"ok": True}


@app.post("/api/portfolio/sell")
def sell_position_api(body: SellIn):
    sym = _norm_symbol(body.symbol)
    st_ = load_store()
    if not sell_position(st_, sym, body.shares):
        raise HTTPException(status_code=404, detail="المركز غير موجود")
    return {"ok": True}


@app.delete("/api/portfolio/{symbol}")
def del_position(symbol: str):
    sym = _norm_symbol(symbol)
    st_ = load_store()
    st_["portfolio"].pop(sym, None)
    import modules.storage as _store
    _store.save_store(st_)
    return {"ok": True}


# ---------- المتابعة ----------
@app.get("/api/watchlist")
def api_watchlist():
    def build():
        st_ = load_store()
        syms = list(st_.get("watchlist") or [])
        snap = _snapshot()
        reg = _registry()
        bulk = get_bulk_data(syms, "3mo") if syms else {}
        out = []
        for sym in syms:
            tv = snap.get(sym.replace(".CA", ""))
            signal = "—"
            df = bulk.get(sym)
            if df is not None and len(df) > 30:
                try:
                    d = add_indicators(df)
                    s = get_last_signals(d)
                    signal = generate_signal(s, d)["action"]
                except Exception:
                    signal = "—"
            out.append({"symbol": sym, "short": sym.replace(".CA", ""),
                        "name": (reg.get(sym) or {}).get("name") or get_company_name(sym),
                        "price": tv["close"] if tv else None,
                        "chg": tv["change_pct"] if tv else None,
                        "signal": signal})
        return out
    return cached("watchlist", 60, build)


@app.post("/api/watchlist")
def add_w(body: WatchIn):
    sym = _norm_symbol(body.symbol)
    if not sym:
        raise HTTPException(status_code=400, detail="رمز غير صالح")
    st_ = load_store()
    add_watch(st_, sym)
    return {"ok": True}


@app.delete("/api/watchlist/{symbol}")
def del_w(symbol: str):
    sym = _norm_symbol(symbol)
    st_ = load_store()
    remove_watch(st_, sym)
    return {"ok": True}


# ---------- التنبيهات ----------
@app.get("/api/alerts")
def api_alerts():
    st_ = load_store()
    snap = _snapshot()
    out = []
    for sym, a in (st_.get("alerts") or {}).items():
        row = snap.get(sym.replace(".CA", ""))
        out.append({"symbol": sym, "short": sym.replace(".CA", ""),
                    "name": get_company_name(sym),
                    "above": a.get("above"), "below": a.get("below"),
                    "price": row["close"] if row else None})
    return out


@app.post("/api/alerts")
def add_alert(body: AlertIn):
    sym = _norm_symbol(body.symbol)
    if not sym:
        raise HTTPException(status_code=400, detail="رمز غير صالح")
    st_ = load_store()
    set_alert(st_, sym,
              above=body.above if body.above and body.above > 0 else None,
              below=body.below if body.below and body.below > 0 else None)
    return {"ok": True}


@app.delete("/api/alerts/{symbol}")
def del_alert(symbol: str):
    sym = _norm_symbol(symbol)
    st_ = load_store()
    remove_alert(st_, sym)
    return {"ok": True}
