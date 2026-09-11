"""
منصة البورصة المصرية — Trading Terminal V5
==========================================
- أسعار لحظية حقيقية من TradingView (نفس مصدر الموقع الرسمي)
- كل أسهم البورصة المصرية الحقيقية + محرك توصيات ذكي
- تحليل فني 18 مؤشر + مالي + إدارة مخاطر
- محفظة وتنبيهات ومتابعة محفوظة دائماً
"""
import sys, os, warnings, json, time
from datetime import datetime
warnings.filterwarnings("ignore")
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import streamlit as st
import streamlit.components.v1 as components
import pandas as pd
import numpy as np
import plotly.graph_objects as go
from plotly.subplots import make_subplots

from modules.data import (EGX_STOCKS, PERIOD_MAP, INTERVAL_MAP,
                          get_stock_data, get_bulk_data, get_ticker_info, get_company_name,
                          get_sector)
from modules.technical import add_indicators, get_last_signals, calculate_vwap_signals
from modules.fundamental import analyze_fundamental, calculate_valuation_summary
from modules.signals import (generate_signal, generate_scalp_signal, generate_combined_signal,
                             get_support_resistance, get_intraday_levels,
                             calculate_technical_score, calculate_price_targets)
from modules.risk import calculate_atr_based_stops, position_sizing, risk_score
from modules.screener import build_screener, market_summary
from modules.backtest import backtest_signals
from modules.live_verify import egx_market_status
from modules.performance import get_performance_table
from modules.advisor import rank_opportunities, beginner_summary
from modules.expert_advisor import (generate_expert_verdict, analyze_wyckoff_phase,
                                    analyze_weekly_confluence, INSTITUTIONAL_STOCKS,
                                    HIGH_SPECULATIVE_STOCKS)
import modules.storage as store
import modules.tv_data as tvd
import modules.tv_widgets as tv
import modules.news as newsfeed
import modules.macro as macro

# ============================================================
# إعداد الصفحة
# ============================================================
st.set_page_config(
    page_title="منصة البورصة المصرية — Trading Terminal",
    page_icon="📈",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ============================================================
# CSS احترافي — مستوى منصات التداول
# ============================================================
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Tajawal:wght@400;500;700;800&display=swap');
html, body, [class*="css"] { font-family: 'Tajawal', sans-serif; }
.stApp { background-color: #0b0e14; }
.main { direction: rtl; }

/* ===== الهيدر ===== */
.pro-header {
    background: linear-gradient(135deg, #101828 0%, #0d1b2e 100%);
    border: 1px solid #1f2d45; border-radius: 14px;
    padding: 0.9rem 1.4rem; color: white; margin-bottom: 0.7rem;
}
.pro-header h1 { color: white !important; margin: 0; font-size: 1.35rem; font-weight: 800; }
.pro-header p { color: #7d8db1; margin: 0.25rem 0 0 0; font-size: 0.82rem; }
.live-badge { background: rgba(0,200,83,0.12); border: 1px solid rgba(0,200,83,0.4);
    color: #00e676; padding: 0.35rem 0.8rem; border-radius: 8px; font-size: 0.78rem; font-weight: 700;
    display: inline-flex; align-items: center; gap: 0.35rem; }
.closed-badge { background: rgba(255,61,87,0.12); border: 1px solid rgba(255,61,87,0.4);
    color: #ff5c76; padding: 0.35rem 0.8rem; border-radius: 8px; font-size: 0.78rem; font-weight: 700; }
.market-live-dot { width: 8px; height: 8px; background: #00e676; border-radius: 50%;
    animation: pulse-dot 1.5s infinite; display: inline-block; }
@keyframes pulse-dot { 0%,100% { opacity:1; } 50% { opacity:0.3; } }

/* ===== الكروت ===== */
div[data-testid="stMetric"] {
    background: linear-gradient(135deg, #10141d 0%, #0d1119 100%);
    border: 1px solid #1f2d45; border-radius: 12px; padding: 0.7rem 0.9rem;
    transition: border-color 0.2s, transform 0.2s;
}
div[data-testid="stMetric"]:hover { border-color: #2962ff; transform: translateY(-2px); }
div[data-testid="stMetric"] label { color: #7d8db1 !important; font-size: 0.78rem !important; }
div[data-testid="stMetric"] div[data-testid="stMetricValue"] { color: white; font-size: 1.35rem !important; font-weight: 700 !important; }

.metric-card {
    background: #10141d; border: 1px solid #1f2d45; border-radius: 12px;
    padding: 1rem; text-align: center;
}
.metric-card .label { color: #7d8db1; font-size: 0.8rem; margin-bottom: 0.2rem; }
.metric-card .value { color: white; font-size: 1.3rem; font-weight: 700; }

/* ===== لوحة القرار ===== */
.decision-hero {
    border-radius: 16px; padding: 1.3rem; margin: 0.8rem 0;
    border: 1px solid; position: relative; overflow: hidden;
    animation: fadeInUp 0.4s ease-out;
}
.decision-hero-buy { background: linear-gradient(135deg, #0a2a14 0%, #10341a 100%); border-color: #00c853; }
.decision-hero-sell { background: linear-gradient(135deg, #2d0a0a 0%, #3d1414 100%); border-color: #ff3d57; }
.decision-hero-hold { background: linear-gradient(135deg, #12161f 0%, #1a1f2c 100%); border-color: #546e7a; }
.decision-action { font-size: 1.7rem; font-weight: 800; margin: 0; }
.decision-sub { font-size: 0.9rem; opacity: 0.92; margin-top: 0.3rem; }
@keyframes fadeInUp { from { opacity:0; transform:translateY(12px); } to { opacity:1; transform:translateY(0); } }

.action-plan { background: #10141d; border: 1px solid #1f2d45; border-radius: 12px; padding: 1rem; }
.action-plan h4 { color: white; font-size: 0.95rem; margin: 0 0 0.6rem 0; }
.step-num { background: #2962ff; color: white; width: 26px; height: 26px; border-radius: 50%;
    display: inline-flex; align-items: center; justify-content: center; font-size: 0.8rem; font-weight: 700; margin-left: 0.5rem; }
.scenario-buy { background: rgba(0,200,83,0.08); border: 1px solid rgba(0,200,83,0.3); border-radius: 10px; padding: 0.8rem; }
.scenario-sell { background: rgba(255,61,87,0.08); border: 1px solid rgba(255,61,87,0.3); border-radius: 10px; padding: 0.8rem; }

/* ===== درجة فنية ===== */
.tech-score-card {
    background: linear-gradient(135deg, #10141d 0%, #0d1119 100%);
    border: 1px solid #1f2d45; border-radius: 16px;
    padding: 1.2rem; text-align: center;
    animation: fadeInUp 0.5s ease-out;
}
.tech-score-num { font-size: 3rem; font-weight: 900; line-height: 1; }
.tech-score-label { font-size: 1rem; font-weight: 700; margin-top: 0.3rem; }
.tech-score-sub { font-size: 0.72rem; color: #7d8db1; margin-top: 0.2rem; }

/* ===== كروت التوصيات ===== */
.pick-card {
    background: linear-gradient(135deg, #10141d 0%, #0d1119 100%);
    border: 2px solid #1f2d45; border-radius: 16px; padding: 1.1rem;
    transition: transform 0.2s, border-color 0.2s;
}
.pick-card:hover { transform: translateY(-3px); }

/* ===== الخريطة الحرارية ===== */
.heatmap-cell { border-radius: 6px; text-align: center; display:inline-flex;
    flex-direction:column; justify-content:center; align-items:center;
    border:1px solid rgba(255,255,255,0.08); }

/* ===== شريط التيرمنال العلوي ===== */
.terminal-bar { display:flex; gap:0.4rem; background:#0d1119; border:1px solid #1f2d45; border-radius:12px; padding:0.55rem 0.9rem; margin-bottom:0.7rem; flex-wrap:wrap; align-items:center; }
.tb-cell { display:flex; align-items:center; gap:0.45rem; padding:0 0.8rem; border-left:1px solid #1f2d45; font-size:0.82rem; }
.tb-cell:last-child { border-left:none; }
.tb-label { color:#7d8db1; font-size:0.68rem; font-weight:700; }

/* ===== تبويبات ===== */
.stTabs [data-baseweb="tab-list"] { gap: 0.4rem; background: #0d1119; border-radius: 12px; padding: 0.3rem; }
.stTabs [data-baseweb="tab"] { background: transparent; border-radius: 9px; color: #7d8db1;
    font-weight: 700; padding: 0.45rem 1rem; }
.stTabs [aria-selected="true"] { background: #2962ff !important; color: white !important; }

/* ===== عناصر عامة ===== */
.stButton button { border-radius: 10px; transition: all 0.2s ease; font-weight: 600; }
.stButton button:hover { transform: translateY(-1px); box-shadow: 0 4px 14px rgba(41,98,255,0.35); }
div[data-testid="stExpander"] { background: #10141d; border: 1px solid #1f2d45; border-radius: 12px; }
div[data-testid="stDataFrame"] { border-radius: 12px; overflow: hidden; }
section[data-testid="stSidebar"] { background-color: #0d1119; border-left: 1px solid #1f2d45; }

::-webkit-scrollbar { width: 8px; height: 8px; }
::-webkit-scrollbar-track { background: #0b0e14; }
::-webkit-scrollbar-thumb { background: #1f2d45; border-radius: 4px; }
::-webkit-scrollbar-thumb:hover { background: #2962ff; }
</style>
""", unsafe_allow_html=True)

# ============================================================
# Session State + التخزين الدائم
# ============================================================
USER_STORE = store.load_store()

if "watchlist" not in st.session_state:
    st.session_state.watchlist = USER_STORE["watchlist"]
if "portfolio" not in st.session_state:
    st.session_state.portfolio = USER_STORE["portfolio"]
if "last_refresh" not in st.session_state:
    st.session_state.last_refresh = datetime.now()

def persist_watch():
    USER_STORE["watchlist"] = st.session_state.watchlist
    store.save_store(USER_STORE)

# ============================================================
# Cache
# ============================================================
@st.cache_data(ttl=90, show_spinner=False)
def cached_bulk(symbols_tuple, period, interval="1d"):
    return get_bulk_data(list(symbols_tuple), period=period, interval=interval)

@st.cache_data(ttl=60, show_spinner=False)
def cached_single(symbol, period, interval="1d"):
    return get_stock_data(symbol, period, interval=interval)

@st.cache_data(ttl=600, show_spinner=False)
def cached_info(symbol):
    return get_ticker_info(symbol)

@st.cache_data(ttl=1800, show_spinner=False)
def cached_performance(symbol):
    return get_performance_table(symbol)

# ============================================================
# سجل الأسهم الحقيقي من TradingView + أدوات العرض الموحد
# ============================================================
@st.cache_data(ttl=900, show_spinner=False)
def symbol_registry():
    """{symbol.CA: {"name":.., "sector":.., "tv": row}} — قائمة البورصة الحقيقية."""
    reg = tvd.get_registry()
    if reg:
        return reg
    return {s: {"name": get_company_name(s), "sector": get_sector(s), "tv": None}
            for s in EGX_STOCKS}

def cname(symbol) -> str:
    return symbol_registry().get(symbol, {}).get("name") or get_company_name(symbol)

def sector_of(symbol) -> str:
    return symbol_registry().get(symbol, {}).get("sector") or get_sector(symbol)

def all_symbols_list() -> list:
    return sorted(symbol_registry().keys())

def sector_list_dyn() -> list:
    return sorted({m["sector"] for m in symbol_registry().values() if m.get("sector")})

def symbols_by_mcap(n=None) -> list:
    """أكبر الأسهم حسب القيمة السوقية الحقيقية من TradingView (بدون أسهم ميتة)."""
    reg = symbol_registry()
    ordered = sorted(reg.keys(),
                     key=lambda s: (reg[s].get("tv") or {}).get("market_cap") or 0,
                     reverse=True)
    return ordered[:n] if n else ordered

def smart_search(query: str):
    q = query.strip().lower()
    if not q:
        return []
    out = []
    for sym, meta in symbol_registry().items():
        name = meta.get("name") or ""
        if q in sym.lower().replace(".ca", "") or q in name.lower():
            out.append((sym, name))
    return out[:15]

def tv_overlay(df, sym_col="الرمز", price_col="السعر", chg_col="التغير%"):
    """تركيب السعر والتغير اللحظي من TradingView فوق نتائج تحليل الإغلاق."""
    if df is None or df.empty:
        return df
    snap = tvd.snapshot()
    if not snap:
        return df
    df = df.copy()
    prices, chgs = [], []
    for sym in df[sym_col]:
        row = snap.get(str(sym).replace(".CA", ""))
        prices.append(round(row["close"], 2) if row else None)
        chgs.append(round(row["change_pct"], 2) if row else None)
    if price_col in df.columns:
        df[price_col] = [p if p is not None else o for p, o in zip(prices, df[price_col])]
    if chg_col in df.columns:
        df[chg_col] = [c if c is not None else o for c, o in zip(chgs, df[chg_col])]
    return df

def indices_row():
    """بطاقات مؤشرات البورصة الرسمية (EGX30 / EGX70) من TradingView."""
    idx = tvd.indices()
    if not idx:
        st.caption("جاري تحميل المؤشرات الرسمية من TradingView...")
        return
    labels = {"EGX30": "EGX30 الرئيسي", "EGX70EWI": "EGX70", "EGX30TR": "EGX30 العائد الكلي", "EGX100": "EGX100"}
    keys = [k for k in ["EGX30", "EGX70EWI", "EGX30TR", "EGX100"] if k in idx]
    cols = st.columns(len(keys))
    for col, k in zip(cols, keys):
        r = idx[k]
        ch = r["change_pct"]
        cc = "#00e676" if ch > 0 else ("#ff5c76" if ch < 0 else "#90a4ae")
        arrow = "▲" if ch > 0 else ("▼" if ch < 0 else "—")
        col.markdown(f"""
        <div class="metric-card" style="padding:0.8rem 0.9rem;">
            <div style="color:#7d8db1; font-size:0.72rem; font-weight:700;">🏛️ {labels.get(k, k)}</div>
            <div style="color:white; font-size:1.35rem; font-weight:800;">{r['value']:,.2f}</div>
            <div style="color:{cc}; font-size:0.8rem; font-weight:700;">{arrow} {ch:+.2f}% ({r['change_abs']:+,.1f})</div>
        </div>
        """, unsafe_allow_html=True)
    st.caption("المؤشرات الرسمية — المصدر: TradingView")

AR_MONTHS = ["يناير", "فبراير", "مارس", "أبريل", "مايو", "يونيو",
             "يوليو", "أغسطس", "سبتمبر", "أكتوبر", "نوفمبر", "ديسمبر"]

def short_dates(idx):
    """تواريخ مختصرة بالعربية لمحور الرسم (بدون أوقات وطوابع زمنية مزعجة)."""
    out = []
    for d in idx:
        try:
            out.append(f"{d.day:02d} {AR_MONTHS[d.month - 1]}")
        except Exception:
            out.append(str(d)[:10])
    return out

# ============================================================
# الهيدر + حالة السوق
# ============================================================
status = egx_market_status()
if status["open"]:
    status_html = f'<span class="live-badge"><span class="market-live-dot"></span> السوق مفتوح الآن — {status["reason"]}</span>'
else:
    status_html = f'<span class="closed-badge">● السوق مغلق — {status["reason"]}</span>'

st.markdown(f"""
<div class="pro-header">
    <div style="display:flex; justify-content:space-between; align-items:center; flex-wrap:wrap; gap:0.6rem;">
        <div>
            <h1>📈 منصة البورصة المصرية — Trading Terminal</h1>
            <p>أسعار لحظية من TradingView • {len(symbol_registry())} سهم حقيقي • توصيات ذكية • تحليل احترافي مجاني 100%</p>
        </div>
    </div>
</div>
""", unsafe_allow_html=True)

# ===== شريط الأسعار اللحظي — نفس مصدر TradingView =====
@st.fragment(run_every=30)
def live_prices_strip():
    """أكبر 10 أسهم بأسعار TradingView الحقيقية — يتحدث كل 30 ثانية."""
    try:
        snap = tvd.snapshot()
        if not snap:
            st.caption("جاري تحميل الأسعار اللحظية من TradingView...")
            return
        syms = [s.replace(".CA", "") for s in symbols_by_mcap(10)]
        cols = st.columns(len(syms))
        for col, short in zip(cols, syms):
            row = snap.get(short)
            if not row:
                continue
            ch = row["change_pct"]
            cc = "#00e676" if ch > 0 else ("#ff5c76" if ch < 0 else "#90a4ae")
            col.markdown(f'<div class="metric-card" style="padding:0.45rem;"><div style="color:#7d8db1; font-size:0.62rem;">{short}</div><div style="color:white; font-weight:700; font-size:0.85rem;">{row["close"]:,.2f}</div><div style="color:{cc}; font-size:0.68rem;">{ch:+.2f}%</div></div>', unsafe_allow_html=True)
        st.caption("🔁 يتحدث كل 30 ثانية — أسعار TradingView (نفس الأرقام التي تراها على الموقع الرسمي)")
    except Exception:
        st.caption("جاري تحميل الأسعار...")

live_prices_strip()

# ============================================================
# شريط التيرمنال + مراقبة الصفقات (تحديث لحظي كل 30 ثانية)
# ============================================================
@st.fragment(run_every=30)
def terminal_topbar():
    """EGX30 + الصاعدون/الهابطون + حالة السوق — مثل الشريط العلوي في منصات التداول."""
    try:
        idx = tvd.indices()
        snap = tvd.snapshot()
        cells = []
        egx30 = idx.get("EGX30")
        if egx30:
            cc = "#00e676" if egx30["change_pct"] > 0 else ("#ff5c76" if egx30["change_pct"] < 0 else "#90a4ae")
            cells.append(f'<div class="tb-cell"><span class="tb-label">EGX30</span><b style="color:white;">{egx30["value"]:,.2f}</b><span style="color:{cc}; font-weight:800;">{egx30["change_pct"]:+.2f}%</span></div>')
        ups = sum(1 for r in snap.values() if r["change_pct"] > 0)
        downs = sum(1 for r in snap.values() if r["change_pct"] < 0)
        flats = len(snap) - ups - downs
        cells.append(f'<div class="tb-cell"><span style="color:#00e676; font-weight:800;">▲ {ups}</span><span style="color:#90a4ae; font-weight:800;">= {flats}</span><span style="color:#ff5c76; font-weight:800;">▼ {downs}</span><span class="tb-label">الصاعدون / الهابطون</span></div>')
        mstat = egx_market_status()
        cells.append(f'<div class="tb-cell"><span class="tb-label">{"🟢 السوق مفتوح" if mstat["open"] else "🔴 السوق مغلق"}</span><span style="color:#7d8db1; font-size:0.68rem;">{mstat["reason"]}</span></div>')
        cells.append(f'<div class="tb-cell"><span class="tb-label">⏰ القاهرة</span><b style="color:white;">{datetime.now().strftime("%H:%M:%S")}</b></div>')
        st.markdown('<div class="terminal-bar">' + "".join(cells) + '</div>', unsafe_allow_html=True)
    except Exception:
        st.caption("جاري تحميل شريط السوق...")

def add_trade_idea(symbol, entry, stop, t1, t2=None):
    store.add_idea(USER_STORE, symbol, entry, stop, t1, t2)

@st.fragment(run_every=30)
def watch_panel():
    """جدول المتابعة اليومية — أسعار لحظية من TradingView كل 30 ثانية."""
    st.markdown("#### 📌 متابعة الأسهم اليومية")
    if not st.session_state.watchlist:
        st.info("قائمتك فارغة — أضف أسهم من السايدبار أو من أسفل الجدول")
        return
    with st.spinner("تحديث المتابعة..."):
        snap_w = tvd.snapshot()
        w_bulk = cached_bulk(tuple(st.session_state.watchlist), "3mo") or {}
        rows_w = []
        for w in st.session_state.watchlist:
            row_w = {"الرمز": w.replace(".CA", ""), "الشركة": cname(w)[:30]}
            tv_r = snap_w.get(w.replace(".CA", ""))
            if tv_r:
                row_w["السعر الحالي"] = round(tv_r["close"], 2)
                row_w["التغير%"] = round(tv_r["change_pct"], 2)
            wdf = w_bulk.get(w)
            row_w["إشارة اليوم"] = "—"
            if wdf is not None and not wdf.empty and len(wdf) > 30:
                try:
                    wdf_i = add_indicators(wdf)
                    w_sig = get_last_signals(wdf_i)
                    row_w["إشارة اليوم"] = generate_signal(w_sig, wdf_i)["action"]
                except Exception:
                    pass
            rows_w.append(row_w)
    st.dataframe(pd.DataFrame(rows_w), use_container_width=True, hide_index=True, height=300,
        column_config={
            "السعر الحالي": st.column_config.NumberColumn(format="%.2f"),
            "التغير%": st.column_config.NumberColumn(format="%.2f%%"),
        })
    st.caption("🔄 يتحدث كل 30 ثانية — الأسعار من TradingView • الإشارة من آخر جلسة")
    pick_w = st.selectbox("إدارة سهم", options=st.session_state.watchlist,
                          format_func=lambda w: f"{w.replace('.CA','')} — {cname(w)[:30]}", key="pick_w")
    wm1, wm2 = st.columns(2)
    if wm1.button("🎯 افتح التحليل الكامل", use_container_width=True, key="open_w"):
        st.session_state["selected_symbol"] = pick_w
        st.rerun()
    if wm2.button("🗑️ حذف من المتابعة", use_container_width=True, key="del_w"):
        st.session_state.watchlist.remove(pick_w)
        USER_STORE["watchlist"] = st.session_state.watchlist
        store.save_store(USER_STORE)
        st.rerun()

@st.fragment(run_every=30)
def trade_ideas_panel():
    """مراقبة الصفقات النشطة لحظياً: السعر الحالي مقابل الدخول + الوقف والأهداف."""
    ideas = USER_STORE.get("ideas", [])
    st.markdown("#### 🎯 مراقبة الصفقات — لحظية")
    if not ideas:
        st.caption("لا توجد صفقات مراقبة — أضف واحدة من 🎖️ فرص عالية الثقة أو من خطة خبير البورصة")
        return
    snap_i = tvd.snapshot()
    n_cols = min(3, len(ideas))
    for start in range(0, len(ideas), n_cols):
        cols = st.columns(n_cols)
        for col, idea in zip(cols, ideas[start:start + n_cols]):
            sym = idea["symbol"]
            tv_r = snap_i.get(sym.replace(".CA", ""))
            now_p = tv_r["close"] if tv_r else None
            entry = float(idea["entry"])
            pl = (now_p - entry) / entry * 100 if now_p else 0
            if now_p is not None and now_p <= float(idea["stop"]):
                status, sc = "🚨 ضرب الوقف — أخرج فوراً", "#ff5c76"
            elif now_p is not None and idea.get("t2") and now_p >= float(idea["t2"]):
                status, sc = "🚀 الهدف الثاني تحقق", "#ce93d8"
            elif now_p is not None and now_p >= float(idea["t1"]):
                status, sc = "🎯 الهدف الأول تحقق — احجز ربحاً جزئياً", "#00e676"
            else:
                status, sc = "⏳ جارية — التزم بالخطة", "#64b5f6"
            pl_c = "#00e676" if pl >= 0 else "#ff5c76"
            t2_html = f'<span style="color:#ce93d8;">🚀 {float(idea["t2"]):,.2f}</span>' if idea.get("t2") else ""
            col.markdown(f"""
            <div class="pick-card" style="border-color:{sc}; padding:0.8rem;">
                <div style="display:flex; justify-content:space-between; align-items:center;">
                    <b style="color:white;">{sym.replace('.CA','')}</b>
                    <span style="color:{pl_c}; font-weight:800;">{pl:+.2f}%</span>
                </div>
                <div style="color:#7d8db1; font-size:0.7rem; margin:0.2rem 0;">{cname(sym)[:26]}</div>
                <div style="font-size:0.78rem; color:#e0e0e0;">دخول <b>{entry:,.2f}</b> → الآن <b style="color:white;">{now_p:,.2f}</b></div>
                <div style="display:flex; justify-content:space-between; font-size:0.72rem; margin-top:0.3rem;">
                    <span style="color:#ff5c76;">🛡️ {float(idea['stop']):,.2f}</span>
                    <span style="color:#00e676;">🎯 {float(idea['t1']):,.2f}</span>
                    {t2_html}
                </div>
                <div style="background:rgba(255,255,255,0.05); border-radius:8px; padding:0.3rem 0.5rem; margin-top:0.4rem; color:{sc}; font-size:0.75rem; font-weight:700;">{status}</div>
                <div style="color:#7d8db1; font-size:0.62rem; margin-top:0.2rem;">أُضيفت {idea.get('added', '')}</div>
            </div>
            """, unsafe_allow_html=True)
            if col.button("✕ إنهاء المراقبة", key=f"del_idea_{idea['id']}", use_container_width=True):
                store.remove_idea(USER_STORE, idea["id"])
                st.rerun()

@st.fragment(run_every=30)
def portfolio_panel():
    """محفظتك الفعلية — ربح وخسارة لحظي بأسعار TradingView."""
    positions = USER_STORE.get("portfolio", {})
    if not positions:
        st.info("لا توجد صفقات مسجلة — سجّل أول صفقة من نموذج التسجيل بالأعلى")
        return
    snap_p = tvd.snapshot()
    rows_p = []
    tot_val = tot_cost = 0.0
    for sym, p in positions.items():
        sh = float(p["shares"]); cost = float(p["avg_cost"])
        tv_r = snap_p.get(sym.replace(".CA", ""))
        now_p = tv_r["close"] if tv_r else cost
        val = sh * now_p; basis = sh * cost
        pl = val - basis
        pl_pct = (now_p - cost) / cost * 100 if cost else 0
        day_ch = tv_r["change_pct"] if tv_r else 0
        tot_val += val; tot_cost += basis
        rows_p.append({
            "الرمز": sym.replace(".CA", ""), "الشركة": cname(sym)[:24],
            "العدد": int(sh), "متوسط الشراء": round(cost, 2),
            "السعر الآن": round(now_p, 2), "اليوم%": round(day_ch, 2),
            "القيمة": round(val, 0), "التكلفة": round(basis, 0),
            "الربح/الخسارة": round(pl, 0), "العائد%": round(pl_pct, 2),
        })
    total_pl = tot_val - tot_cost
    total_pct = total_pl / tot_cost * 100 if tot_cost else 0
    m1, m2, m3, m4 = st.columns(4)
    m1.metric("💼 القيمة السوقية", f"{tot_val:,.0f} ج.م")
    m2.metric("💵 التكلفة", f"{tot_cost:,.0f} ج.م")
    m3.metric("📈 الربح/الخسارة", f"{total_pl:+,.0f} ج.م", f"{total_pct:+.2f}%")
    m4.metric("🗂️ عدد المراكز", len(positions))

    st.dataframe(pd.DataFrame(rows_p), use_container_width=True, hide_index=True, height=min(320, 60 + 35 * len(rows_p)),
        column_config={
            "متوسط الشراء": st.column_config.NumberColumn(format="%.2f"),
            "السعر الآن": st.column_config.NumberColumn(format="%.2f"),
            "اليوم%": st.column_config.NumberColumn(format="%+.2f%%"),
            "القيمة": st.column_config.NumberColumn(format="%,.0f"),
            "التكلفة": st.column_config.NumberColumn(format="%,.0f"),
            "الربح/الخسارة": st.column_config.NumberColumn(format="%+.0f"),
            "العائد%": st.column_config.NumberColumn(format="%+.2f%%"),
        })

    # رسم عائد كل مركز
    fig_pf = go.Figure(go.Bar(
        x=[r["العائد%"] for r in rows_p][::-1],
        y=[r["الرمز"] for r in rows_p][::-1],
        orientation="h",
        marker_color=["#00c853" if r["العائد%"] >= 0 else "#ff5c76" for r in rows_p][::-1],
        text=[f"{r['العائد%']:+.2f}%" for r in rows_p][::-1],
        textposition="auto",
    ))
    fig_pf.update_layout(height=max(220, 50 * len(rows_p)), template="plotly_dark",
                         paper_bgcolor="#0d1119", margin=dict(l=10, r=30, t=10, b=10),
                         xaxis_title="العائد %")
    st.plotly_chart(fig_pf, use_container_width=True)
    st.caption("🔄 القيم الحية من TradingView — تتحدث كل 30 ثانية")

    # إدارة مراكز المحفظة
    pick_p = st.selectbox("إدارة مركز", options=list(positions.keys()),
                          format_func=lambda s: f"{s.replace('.CA','')} — {cname(s)[:26]} — {positions[s]['shares']} سهم", key="pf_manage")
    pcol_a, pcol_b = st.columns(2)
    max_sh = int(float(positions[pick_p]["shares"]))
    sell_n = pcol_a.number_input("عدد الأسهم", 1, max_sh, 1, key="pf_sell_n")
    if pcol_a.button("💸 بيع من المركز", use_container_width=True, key="pf_sell"):
        store.sell_position(USER_STORE, pick_p, sell_n)
        st.rerun()
    if pcol_b.button("🗑️ حذف المركز بالكامل", use_container_width=True, key="pf_del"):
        USER_STORE["portfolio"].pop(pick_p, None)
        store.save_store(USER_STORE)
        st.rerun()

# شريط التيرمنال: EGX30 + الصاعدون/الهابطون + حالة السوق + الساعة
terminal_topbar()

# ============================================================
# السايدبار — نظيف ومباشر
# ============================================================
with st.sidebar:
    st.markdown("### 📈 EGX Terminal")

    search_q = st.text_input("🔍 بحث", placeholder="اسم أو رمز السهم...", key="sym_search")

    ordered = symbols_by_mcap()
    if search_q:
        ql = search_q.strip().lower()
        ordered = [s for s in ordered
                   if ql in s.lower().replace(".ca", "") or ql in (cname(s) or "").lower()]

    default_sym = st.session_state.get("selected_symbol", "COMI.CA")
    ordered = [default_sym] + [s for s in ordered if s != default_sym]

    symbol = st.selectbox(
        "السهم الحالي",
        options=ordered,
        index=0,
        format_func=lambda s: f"{s.replace('.CA','')} — {cname(s)[:26]}",
        label_visibility="collapsed",
    )
    st.session_state["selected_symbol"] = symbol

    period_label = st.selectbox("فترة التحليل", list(PERIOD_MAP.keys()), index=4)
    period = PERIOD_MAP[period_label]

    st.markdown("---")

    with st.expander("⚙️ إعدادات المخاطر"):
        saved = USER_STORE["settings"]
        capital = st.number_input("رأس المال (ج.م)", 0.0, 1e9, float(saved.get("capital", 100000.0)), 1000.0, format="%.0f")
        risk_pct = st.slider("مخاطرة/صفقة %", 0.5, 5.0, float(saved.get("risk_pct", 2.0)), 0.1)
        max_pct = st.slider("أقصى نسبة للسهم %", 5.0, 50.0, float(saved.get("max_pct", 10.0)), 1.0)
        if st.button("💾 حفظ", use_container_width=True):
            USER_STORE["settings"].update({"capital": capital, "risk_pct": risk_pct, "max_pct": max_pct})
            store.save_store(USER_STORE)
            st.success("حُفظ ✓")

    if st.button("🔄 تحديث البيانات", use_container_width=True):
        tvd.clear_cache()
        st.cache_data.clear()
        st.session_state.last_refresh = datetime.now()
        st.rerun()

# ============================================================
# التبويبات
# ============================================================
tab_market, tab_portfolio, tab_advisor, tab_detail, tab_watch, tab_tools = st.tabs(
    ["🏠 السوق", "💼 محفظتي", "💡 الفرص", "🎯 التداول والقرار", "⭐ المتابعة والصفقات", "🧪 أدوات"]
)

# ============================================================
# TAB 1: السوق اللحظي
# ============================================================
with tab_market:
    # ===== مؤشرات البورصة الرسمية =====
    st.markdown("#### 🏛️ مؤشرات البورصة المصرية")
    indices_row()
    st.markdown("---")

    # ===== السياق العالمي وأثره على قراراتك =====
    with st.expander("🌍 السياق العالمي وأثره على قراراتك — الدولار، برنت، الفائدة الأمريكية", expanded=False):
        macro_data = macro.fetch_macro()
        if not macro_data:
            st.caption("جاري تحميل البيانات العالمية...")
        else:
            reg_ = macro.regime(macro_data)
            st.markdown(f"""
            <div style="background:#10141d; border:1px solid {reg_['color']}; border-radius:12px; padding:0.7rem 1rem; margin-bottom:0.7rem;">
                <b style="color:{reg_['color']}; font-size:1rem;">{reg_['label']}</b>
                <div style="color:#7d8db1; font-size:0.78rem; margin-top:0.2rem;">{reg_['desc']}</div>
            </div>
            """, unsafe_allow_html=True)
            mcols = st.columns(len(macro_data))
            for mcol, (tk_, m_) in zip(mcols, macro_data.items()):
                cc_ = "#00e676" if m_["day_pct"] > 0 else ("#ff5c76" if m_["day_pct"] < 0 else "#90a4ae")
                mcol.markdown(f'<div class="metric-card" style="padding:0.5rem;"><div style="color:#7d8db1; font-size:0.62rem;">{m_["label"]}</div><div style="color:white; font-weight:700; font-size:0.85rem;">{m_["value"]:,.2f}</div><div style="color:{cc_}; font-size:0.66rem;">{m_["day_pct"]:+.2f}% اليوم • {m_["wk_pct"]:+.2f}% أسبوع</div></div>', unsafe_allow_html=True)
            sigs_ = macro.macro_signals(macro_data)
            if sigs_:
                st.markdown("##### 🔍 قراءة السياق للسوق المصري")
                for tone_, text_ in sigs_:
                    icon_ = "🟢" if tone_ == "pos" else ("🟠" if tone_ == "neg_mixed" else "🔴")
                    st.markdown(f"- {icon_} {text_}")
            pos_ = USER_STORE.get("portfolio", {})
            if pos_:
                st.markdown("##### 💼 أثر هذا السياق على محفظتك")
                for sym_ in pos_:
                    st.markdown(f"- **{sym_.replace('.CA','')}** — {macro.holding_impact(sector_of(sym_))}")
            st.caption("بيانات عالمية حقيقية من Yahoo Finance بلا تأخير عملي — تُحدَّث كل 10 دقائق")

    st.markdown("---")

    # ===== التقرير الصباحي الآلي =====
    with st.expander("🌅 التقرير الصباحي الآلي — خلاصة اليوم قبل الافتتاح", expanded=False):
        base_dir = os.path.dirname(os.path.abspath(__file__))
        today_rep = os.path.join(base_dir, "reports", f"report_{datetime.now().strftime('%Y-%m-%d')}.md")
        latest_rep = os.path.join(base_dir, "reports", "latest.md")
        if os.path.exists(today_rep):
            st.markdown(open(today_rep, encoding="utf-8").read())
        else:
            st.caption("لا يوجد تقرير لليوم بعد — يُنشأ تلقائياً 9:30 صباحاً أيام التداول (الأحد-الخميس)")
            if st.button("⚙️ أنشئ تقرير اليوم الآن (30-60 ثانية)", use_container_width=True, key="gen_report"):
                with st.spinner("جمع بيانات السوق وتحليل الفرص وجمع الأخبار..."):
                    from modules.daily_report import generate_report, save_report
                    md_rep = generate_report()
                    save_report(md_rep)
                st.markdown(md_rep)
        if os.path.exists(latest_rep):
            st.download_button("⬇️ تحميل التقرير", open(latest_rep, encoding="utf-8").read().encode("utf-8-sig"),
                               "egx_daily_report.md", "text/markdown", use_container_width=True, key="dl_report")

    st.markdown("---")

    mcol1, mcol2 = st.columns([2.1, 1])
    with mcol1:
        with st.spinner(f"تحميل رسم {symbol}..."):
            df_m = cached_single(symbol, "6mo")
        if df_m is not None and not df_m.empty and len(df_m) > 5:
            tv_live_m = tvd.one(symbol)
            if tv_live_m:  # حدّث شمعة اليوم بالسعر اللحظي الحقيقي
                df_m = df_m.copy()
                df_m.iloc[-1, df_m.columns.get_loc("Close")] = tv_live_m["close"]
                if tv_live_m["close"] > float(df_m["High"].iloc[-1]):
                    df_m.iloc[-1, df_m.columns.get_loc("High")] = tv_live_m["close"]
                if tv_live_m["close"] < float(df_m["Low"].iloc[-1]):
                    df_m.iloc[-1, df_m.columns.get_loc("Low")] = tv_live_m["close"]
            dfm = add_indicators(df_m)
            xm = short_dates(dfm.index)
            figm = go.Figure()
            figm.add_trace(go.Candlestick(x=xm, open=dfm["Open"], high=dfm["High"], low=dfm["Low"], close=dfm["Close"], name="الشموع",
                                          increasing_line_color="#00e676", decreasing_line_color="#ff5c76"))
            figm.add_trace(go.Scatter(x=xm, y=dfm["SMA20"], name="SMA20", line=dict(color="#ffab00", width=1)))
            figm.add_trace(go.Scatter(x=xm, y=dfm["SMA50"], name="SMA50", line=dict(color="#29b6f6", width=1)))
            figm.update_layout(height=560, template="plotly_dark", xaxis_rangeslider_visible=False,
                               margin=dict(l=10, r=10, t=30, b=10), hovermode="x unified",
                               paper_bgcolor="#0d1119", legend=dict(orientation="h", y=1.05, x=0.5, xanchor="center"))
            figm.update_xaxes(type="category")
            st.plotly_chart(figm, use_container_width=True)
            st.caption(f"📊 {symbol.replace('.CA','')} — آخر 6 أشهر (شموع + متوسطات) — مرر بالماوس لرؤية الأسعار")
        else:
            st.error("تعذر تحميل بيانات هذا السهم")

    with mcol2:
        st.markdown("#### 🔥 أهم التحركات الآن")
        if "screener_df" not in st.session_state or st.session_state.screener_df is None or st.session_state.screener_df.empty:
            with st.spinner("تحليل EGX30..."):
                bulk0 = cached_bulk(tuple(symbols_by_mcap(30)), "3mo")
                st.session_state.screener_df = tv_overlay(build_screener(bulk0)) if bulk0 else pd.DataFrame()
        s0 = st.session_state.screener_df
        if s0 is not None and not s0.empty:
            st.markdown("**🟢 الأكثر صعوداً**")
            top_g = s0.sort_values("التغير%", ascending=False).head(5)
            for _, r in top_g.iterrows():
                ch = r["التغير%"]
                cc = "#00e676" if ch > 0 else ("#ff5c76" if ch < 0 else "#90a4ae")
                sym_short = r["الرمز"].replace(".CA", "")
                comp = str(r["الشركة"])[:16]
                prc = r["السعر"]
                st.markdown(f'<div class="metric-card" style="padding:0.5rem; margin-bottom:0.35rem; display:flex; justify-content:space-between; align-items:center;"><span><b style="color:white;">{sym_short}</b> <span style="color:#7d8db1; font-size:0.7rem;">{comp}</span></span><span><b style="color:white;">{prc:,.2f}</b> <b style="color:{cc};">{ch:+.2f}%</b></span></div>', unsafe_allow_html=True)
            st.markdown("**🔴 الأكثر هبوطاً**")
            top_l = s0.sort_values("التغير%").head(5)
            for _, r in top_l.iterrows():
                ch = r["التغير%"]
                cc = "#00e676" if ch > 0 else ("#ff5c76" if ch < 0 else "#90a4ae")
                sym_short = r["الرمز"].replace(".CA", "")
                prc = r["السعر"]
                st.markdown(f'<div class="metric-card" style="padding:0.5rem; margin-bottom:0.35rem; display:flex; justify-content:space-between; align-items:center;"><span><b style="color:white;">{sym_short}</b></span><span><b style="color:white;">{prc:,.2f}</b> <b style="color:{cc};">{ch:+.2f}%</b></span></div>', unsafe_allow_html=True)
        else:
            st.caption("جاري التحليل...")

    st.markdown("---")

    # ===== أداء القطاعات اليوم (من أسعار TradingView الحقيقية) =====
    st.markdown("#### 🏙️ أداء القطاعات اليوم")
    try:
        reg_s = symbol_registry()
        snap_s = tvd.snapshot()
        sec_acc = {}
        for sym_m, meta_m in reg_s.items():
            tv_mm = meta_m.get("tv") or snap_s.get(sym_m.replace(".CA", ""))
            if tv_mm and meta_m.get("sector"):
                sec_acc.setdefault(meta_m["sector"], []).append(tv_mm["change_pct"])
        sec_rows = sorted(((s_, sum(v_) / len(v_), len(v_)) for s_, v_ in sec_acc.items() if len(v_) >= 3),
                          key=lambda x_: x_[1], reverse=True)
        if sec_rows:
            fig_sec = go.Figure(go.Bar(
                x=[r_[1] for r_ in sec_rows][::-1],
                y=[f"{r_[0]} ({r_[2]} سهم)" for r_ in sec_rows][::-1],
                orientation="h",
                marker_color=["#00c853" if v_ > 0 else ("#ff5c76" if v_ < 0 else "#546e7a") for v_ in [r_[1] for r_ in sec_rows][::-1]],
                text=[f"{v_:+.2f}%" for v_ in [r_[1] for r_ in sec_rows][::-1]],
                textposition="auto",
            ))
            fig_sec.update_layout(height=max(300, 36 * len(sec_rows)), template="plotly_dark",
                                  paper_bgcolor="#0d1119", margin=dict(l=10, r=30, t=10, b=10))
            st.plotly_chart(fig_sec, use_container_width=True)
            st.caption("متوسط تغير أسهم كل قطاع اليوم — محسوب من أسعار TradingView لكل أسهم البورصة")
        else:
            st.caption("جاري حساب أداء القطاعات...")
    except Exception:
        st.caption("جاري حساب أداء القطاعات...")

    st.markdown("---")

    # الفاحص الشامل
    st.markdown("#### 🌍 فحص السوق الشامل")
    sc1, sc2, sc3 = st.columns([1.2, 1, 1])
    with sc1:
        universe = st.selectbox("النطاق", ["EGX30 (الأكبر 30)", "أكبر 70", "أكبر 100", f"كل السوق ({len(all_symbols_list())}) ⚠️ بطيء"], index=0, key="scr_uni")
    with sc2:
        screener_period = st.selectbox("الفترة", ["3mo", "6mo", "1y"], index=0, key="scr_per")
    with sc3:
        filter_sig = st.selectbox("الإشارة", ["الكل", "شراء فقط", "بيع فقط", "محايد فقط"], index=0, key="scr_sig")

    if universe.startswith("EGX30"):
        scr_symbols = symbols_by_mcap(30)
    elif universe.startswith("أكبر 70"):
        scr_symbols = symbols_by_mcap(70)
    elif universe.startswith("أكبر 100"):
        scr_symbols = symbols_by_mcap(100)
    else:
        scr_symbols = all_symbols_list()

    if st.button("🚀 شغّل الفحص", type="primary", use_container_width=True, key="run_scr"):
        with st.spinner(f"تحليل {len(scr_symbols)} سهم..."):
            bulk = cached_bulk(tuple(scr_symbols), screener_period)
            st.session_state.screener_df = tv_overlay(build_screener(bulk)) if bulk else pd.DataFrame()

    if "screener_df" in st.session_state and not st.session_state.screener_df.empty:
        df_scr = st.session_state.screener_df.copy()

        summary = market_summary(st.session_state.screener_df)
        s1, s2, s3, s4, s5, s6 = st.columns(6)
        s1.metric("📈 رابحون", summary["gainers"])
        s2.metric("📉 خاسرون", summary["losers"])
        s3.metric("➖ ثابت", summary["flat"])
        s4.metric("متوسط التغير", f"{summary['avg_change']:+.2f}%")
        s5.metric("🟢 شراء", summary["buy_signals"])
        s6.metric("🔴 بيع", summary["sell_signals"])

        # خريطة حرارية
        st.markdown("##### 🗺️ الخريطة الحرارية — أخضر رابح / أحمر خاسر")
        sorted_scr = st.session_state.screener_df.sort_values("التغير%", ascending=False)
        heatmap_html = '<div style="display:flex; flex-wrap:wrap; gap:5px; padding:10px; background:#0d1119; border-radius:12px; border:1px solid #1f2d45;">'
        for _, row in sorted_scr.iterrows():
            ch = row["التغير%"]
            sym_short = row["الرمز"].replace('.CA','')
            if ch > 2: bg = "#00c853"
            elif ch > 0.5: bg = "#388e3c"
            elif ch > -0.5: bg = "#546e7a"
            elif ch > -2: bg = "#c62828"
            else: bg = "#b71c1c"
            company = str(row["الشركة"])[:30]
            price = row["السعر"]
            rsi_v = row["RSI"]
            heatmap_html += f'<div class="heatmap-cell" style="background:{bg}; width:62px; height:44px;" title="{company} | {price:.2f} | RSI {rsi_v:.0f}"><b style="font-size:0.65rem; color:white;">{sym_short}</b><span style="font-size:0.55rem; color:rgba(255,255,255,0.85);">{ch:+.1f}%</span></div>'
        heatmap_html += '</div>'
        st.markdown(heatmap_html, unsafe_allow_html=True)

        # فلترة وعرض
        if filter_sig == "شراء فقط":
            df_scr = df_scr[df_scr["الإشارة"].str.contains("شراء")]
        elif filter_sig == "بيع فقط":
            df_scr = df_scr[df_scr["الإشارة"].str.contains("بيع")]
        elif filter_sig == "محايد فقط":
            df_scr = df_scr[df_scr["الإشارة"] == "انتظار / محايد"]

        display = df_scr[["الرمز","الشركة","السعر","التغير%","الحجم","RSI","SMA_trend","الإشارة","الثقة%"]].copy()
        st.dataframe(display, use_container_width=True, hide_index=True, height=380,
            column_config={
                "التغير%": st.column_config.NumberColumn(format="%.2f%%"),
                "السعر": st.column_config.NumberColumn(format="%.2f"),
                "RSI": st.column_config.ProgressColumn(min_value=0, max_value=100, format="%.1f"),
                "الثقة%": st.column_config.ProgressColumn(min_value=0, max_value=100),
            })

        pick = st.selectbox("افتح تحليل سهم من النتائج", options=df_scr["الرمز"].tolist(),
                            format_func=lambda s: f"{s} — {get_company_name(s)}", key="pick_scr")
        if st.button("➡️ افتح التحليل المفصل", key="open_scr", use_container_width=True):
            st.session_state["selected_symbol"] = pick
            st.rerun()

        csv = display.to_csv(index=False).encode('utf-8-sig')
        st.download_button("⬇️ تصدير CSV", csv, "egx_market.csv", "text/csv", use_container_width=True)

    else:
        st.info("اضغط **شغّل الفحص** لعرض تحليل السوق الكامل.")

# ============================================================
# TAB 2: محفظتي — تسجيل ومتابعة صفقاتك الفعلية من ثاندر
# ============================================================
with tab_portfolio:
    st.subheader("💼 محفظتي — متابعة الصفقات الفعلية")
    st.caption("سجّل صفقاتك كما هي في ثاندر (السهم + عدد الأسهم + متوسط سعر الشراء) وتابع ربحك لحظياً بأسعار TradingView — بياناتك محفوظة على جهازك فقط")

    with st.expander("➕ تسجيل صفقة جديدة", expanded=not USER_STORE.get("portfolio")):
        fcol1, fcol2, fcol3, fcol4 = st.columns([2, 1.1, 1.2, 1])
        with fcol1:
            new_sym = st.selectbox("السهم", options=all_symbols_list(),
                                   format_func=lambda s: f"{s.replace('.CA','')} — {cname(s)[:24]}", key="pf_new_sym")
        with fcol2:
            new_sh = st.number_input("عدد الأسهم", min_value=1, step=1, value=100, key="pf_new_sh")
        with fcol3:
            prefill = tvd.one(new_sym)
            prefill_v = round(prefill["close"], 2) if prefill else 10.0
            new_cost = st.number_input("متوسط الشراء (ج.م)", min_value=0.01, step=0.01, value=prefill_v, key="pf_new_cost")
        with fcol4:
            st.write("")
            if st.button("💾 تسجيل الصفقة", type="primary", use_container_width=True, key="pf_add"):
                store.buy_position(USER_STORE, new_sym, int(new_sh), float(new_cost))
                st.success(f"✓ سُجلت: {int(new_sh)} سهم {new_sym.replace('.CA','')} بمتوسط {new_cost:,.2f}")
                st.rerun()
        st.caption(f"💡 السعر المقترح للمتوسط هو سعر {new_sym.replace('.CA','')} الحالي من TradingView — عدّله لمتوسط شرائك الفعلي من ثاندر")

    portfolio_panel()

# ============================================================
# TAB 3: التوصيات الذكية
# ============================================================
with tab_advisor:
    st.subheader("💡 التوصيات الذكية — أفضل فرص السوق الآن")
    st.caption("المحرك يحلل كل سهم بـ 18 مؤشر فني ثم يرشح الأقوى للشراء مع درجة الربح المتوقعة")

    a1, a2 = st.columns([1.3, 1])
    with a1:
        advisor_universe = st.selectbox("النطاق", ["EGX30 (الأكثر أماناً)", "أكبر 70 سهم", "كل السوق (شامل لكن بطيء)"], index=0, key="adv_uni")
    with a2:
        adv_filter = st.selectbox("نوع الفرص", ["شراء قوي", "شراء", "بيع", "الكل"], index=0, key="adv_filt")
    beginner_mode = st.checkbox("🎓 وضع المبتدئ (شرح مبسط بالعامية)", value=True, key="beg_mode")

    if advisor_universe.startswith("EGX30"):
        adv_symbols = symbols_by_mcap(30)
    elif advisor_universe.startswith("أكبر 70"):
        adv_symbols = symbols_by_mcap(70)
    else:
        adv_symbols = all_symbols_list()

    adv_key = f"adv_{adv_filter}_{len(adv_symbols)}"
    if st.button("🚀 حلل السوق واعرض التوصيات", type="primary", use_container_width=True, key="run_adv") or adv_key not in st.session_state:
        with st.spinner(f"🧠 تحليل {len(adv_symbols)} سهم بمحرك المؤشرات... (10-30 ثانية)"):
            bulk_adv = cached_bulk(tuple(adv_symbols), "6mo")
            st.session_state[adv_key] = tv_overlay(rank_opportunities(bulk_adv, adv_filter), chg_col="التغير اليوم%") if bulk_adv else pd.DataFrame()

    df_adv = st.session_state.get(adv_key, pd.DataFrame())

    # ===== الوضع الاحترافي: فرص عالية الثقة مُثبَتة بالاختبار التاريخي =====
    st.markdown("#### 🎖️ فرص عالية الثقة (مفلترة بمعايير المؤسسات)")
    st.caption("شروط الفرصة: درجة فنية ≥ 65 + ثقة ≥ 70% + سيولة قوية + إشارة شراء — مع نسبة نجاح تاريخية حقيقية من الاختبار الرجعي لكل فرصة")
    if not df_adv.empty:
        df_hc = df_adv[
            (df_adv["درجة فنية"] >= 65)
            & (df_adv["إشارة"].astype(str).str.contains("شراء"))
            & (df_adv["ثقة%"] >= 70)
            & (df_adv["السيولة"].astype(str).str.contains("ممتازة|جيدة", na=False)
               if "السيولة" in df_adv.columns else True)
        ].head(3)
    else:
        df_hc = pd.DataFrame()

    if not df_hc.empty:
        # تسجيل آلي في السجل الموثق — مرة كل 7 أيام لكل سهم (ملف إنجاز دائم)
        for _, r in df_hc.iterrows():
            if not store.has_recent_rec(USER_STORE, r["الرمز"]):
                store.add_rec(USER_STORE, r["الرمز"], cname(r["الرمز"])[:40],
                              float(r["السعر"]), float(r.get("وقف خسارة", 0) or 0),
                              float(r.get("هدف1", 0) or 0), int(r["درجة فنية"]))
        hc_cols = st.columns(len(df_hc))
        for col, (_, r) in zip(hc_cols, df_hc.iterrows()):
            sym = r["الرمز"]
            with col:
                # الاختبار الرجعي الحقيقي لهذه الفرصة على سنتين
                ticket = None
                bt_df = None
                try:
                    bt_df = cached_single(sym, "2y")
                    bt = backtest_signals(bt_df, hold_days=5, threshold=4)
                    bt_line = (f"✅ نجاح تاريخي: **{bt['win_rate']:.0f}%** من {bt['total']} صفقة "
                               f"(متوسط {bt['avg_return']:+.1f}%)") if bt.get("total") else "لا توجد صفقات مشابهة تاريخياً"
                except Exception:
                    bt_line = "اختبار تاريخي غير متاح الآن"
                # ===== بطاقة الأمر التنفيذي: سعر تفعيل محدد + صلاحية + شرط إلغاء =====
                try:
                    tdf = add_indicators(bt_df)
                    tsig = get_last_signals(tdf)
                    sup_, res_ = get_support_resistance(tdf)
                    close_ = float(tsig.get("Close", float(r["السعر"])))
                    atr_ = float(tsig.get("ATR", close_ * 0.02)) or close_ * 0.02
                    stop_ = float(r.get("وقف خسارة", 0) or close_ * 0.95)
                    t1_ = float(r.get("هدف1", 0) or close_ * 1.05)
                    t2_ = round(close_ + 2 * (t1_ - close_), 2)
                    setup_ = str(r.get("النموذج", ""))
                    if "اختراق" in setup_ and res_:
                        etype_ = "⏱️ أمر شراء عند الكسر (Stop-Buy)"
                        trig_ = round(res_ + 0.25 * atr_, 2)
                        zone_ = f"{res_:,.2f} ← {trig_:,.2f}"
                        cond_ = f"لا تفعّل الأمر إلا بكسر {res_:,.2f} بحجم تداول أعلى من المتوسط"
                    elif "ارتداد" in setup_ or "تشبع" in setup_:
                        etype_ = "📥 أمر شراء معلق (Limit-Buy)"
                        trig_ = round(max(sup_ or close_ - 1.2 * atr_, close_ - 1.5 * atr_), 2)
                        zone_ = f"{trig_:,.2f} ← {close_:,.2f}"
                        cond_ = "اشترِ بالتدرج داخل المنطقة — لا تطارد السعر للأعلى"
                    else:
                        ema21_ = float(tsig.get("EMA21", close_ * 0.98))
                        etype_ = "📥 أمر شراء معلق (Limit-Buy)"
                        trig_ = round(ema21_, 2)
                        zone_ = f"{min(trig_, close_):,.2f} ← {close_:,.2f}"
                        cond_ = "الشراء عند عودة السعر لمنطقة المتوسط القصير مع بقاء الاتجاه صاعداً"
                    sizing_ = position_sizing(capital, risk_pct, trig_, stop_, max_pct)
                    shares_ = int(sizing_.get("عدد_الأسهم", 0))
                    rr_ = (t1_ - trig_) / max(trig_ - stop_, 1e-9)
                    ticket = {"etype": etype_, "trig": trig_, "zone": zone_, "stop": stop_,
                              "t1": t1_, "t2": t2_, "shares": shares_, "rr": rr_,
                              "cond": cond_, "value": shares_ * trig_}
                except Exception:
                    ticket = None
                st.markdown(f"""
                <div class="pick-card" style="border-color:#00c853;">
                    <div style="display:flex; justify-content:space-between; align-items:center;">
                        <b style="color:white; font-size:1.1rem;">{sym.replace('.CA','')} — {cname(sym)[:20]}</b>
                        <span style="background:#00c853; color:white; padding:3px 10px; border-radius:12px; font-size:0.7rem; font-weight:700;">{r['إشارة']}</span>
                    </div>
                    <div style="color:#7d8db1; font-size:0.75rem; margin-top:0.3rem;">📌 {r.get('النموذج','')} • درجة {int(r['درجة فنية'])}/100</div>
                    <div style="color:white; font-size:1.1rem; font-weight:700; margin-top:0.3rem;">{r['السعر']:,.2f} <span style="font-size:0.75rem; color:{'#00e676' if r['التغير اليوم%']>=0 else '#ff5c76'};">{r['التغير اليوم%']:+.2f}%</span></div>
                    <div style="display:flex; justify-content:space-between; font-size:0.75rem; margin-top:0.3rem;">
                        <span style="color:#00e676;">🎯 {r.get('هدف1',0):,.2f}</span>
                        <span style="color:#ff5c76;">🛡️ {r.get('وقف خسارة',0):,.2f}</span>
                    </div>
                </div>
                """, unsafe_allow_html=True)
                st.markdown(f'<div style="background:rgba(41,98,255,0.08); border-radius:8px; padding:0.4rem 0.6rem; font-size:0.78rem;">📊 {bt_line}</div>', unsafe_allow_html=True)
                if ticket:
                    st.markdown(f"""
                    <div style="background:rgba(0,200,83,0.05); border:1px dashed rgba(0,200,83,0.45); border-radius:10px; padding:0.7rem; margin-top:0.4rem;">
                        <div style="color:#00e676; font-size:0.8rem; font-weight:800; margin-bottom:0.3rem;">📋 {ticket['etype']} — صلاحية 5 جلسات تداول</div>
                        <div style="display:flex; justify-content:space-between; font-size:0.78rem; color:#e0e0e0;">
                            <span>سعر التفعيل: <b style="color:white;">{ticket['trig']:,.2f}</b></span>
                            <span>R:R <b style="color:#00e676;">1:{ticket['rr']:.1f}</b></span>
                        </div>
                        <div style="font-size:0.72rem; color:#7d8db1; margin-top:0.15rem;">منطقة الدخول: {ticket['zone']}</div>
                        <div style="display:flex; justify-content:space-between; font-size:0.75rem; margin-top:0.35rem;">
                            <span style="color:#ff5c76;">🛡️ وقف {ticket['stop']:,.2f}</span>
                            <span style="color:#00e676;">🎯 {ticket['t1']:,.2f}</span>
                            <span style="color:#ce93d8;">🚀 {ticket['t2']:,.2f}</span>
                        </div>
                        <div style="background:rgba(255,255,255,0.05); border-radius:6px; padding:0.3rem 0.5rem; margin-top:0.35rem; font-size:0.72rem; color:#90caf9;">
                            📐 الحجم المقترح: <b>{ticket['shares']:,} سهم</b> ({ticket['value']:,.0f} ج.م) — بحد {max_pct:.0f}% من رأس المال ومخاطرة {risk_pct:.1f}%
                        </div>
                        <div style="font-size:0.7rem; color:#ffab00; margin-top:0.3rem;">⛔ شرط الإلغاء: {ticket['cond']}</div>
                    </div>
                    """, unsafe_allow_html=True)
                hc1, hc2 = st.columns(2)
                if hc1.button("🔬 تحليل كامل", key=f"hc_{sym}", use_container_width=True):
                    st.session_state["selected_symbol"] = sym
                    st.rerun()
                if hc2.button("🎯 راقب الصفقة", key=f"hcid_{sym}", use_container_width=True):
                    add_trade_idea(sym, float(r["السعر"]),
                                   float(r.get("وقف خسارة", 0) or 0),
                                   float(r.get("هدف1", 0) or 0), None)
                    st.success("✓ أُضيفت لمراقبة الصفقات — تبويب ⭐ المتابعة والصفقات")
        st.info("""
        ⚖️ **كلام صريح عن الدقة:** لا يوجد على وجه الأرض نظام توصيات بنسبة نجاح 95% — أي جهة تدّعي ذلك تكذب عليك.
        صناديق التحوط العالمية الكبرى تحقق 55–65% نجاح، وربحها الحقيقي يأتي من نسبة العائد إلى المخاطرة (1:2) وإيقاف الخسارة المنضبط.
        هذه الفرص أعلى ما ينتجه المحرك الآن، وكل واحدة مذكور نجاحها التاريخي الحقيقي — قرارك النهائي ومعك إدارة المخاطر.
        """)
    else:
        st.caption("لا توجد الآن فرص تستوفي كل الشروط الصارمة — وهذا بحد ذاته إشارة: عدم الدخول أفضل من دخول ضعيف.")

    if not df_adv.empty:
        buys = df_adv[df_adv["درجة فنية"] >= 60]
        b1, b2, b3, b4 = st.columns(4)
        b1.metric("🟢 فرص شراء سوينغ", len(buys))
        b2.metric("📊 متوسط درجة السوق", f"{df_adv['درجة فنية'].mean():.0f}/100")
        best_sym = df_adv.iloc[0]["الرمز"].replace(".CA","")
        best_setup = str(df_adv.iloc[0].get("النموذج", ""))[:18]
        b3.metric("🎯 أفضل فرصة", best_sym, f"نموذج: {best_setup}")
        b4.metric("⚖️ أعلى عائد/مخاطرة", f"{df_adv['العائد/المخاطرة'].iloc[0]}")

        st.markdown("#### 🏆 أفضل 3 فرص سوينغ الآن")
        cols = st.columns(3)
        for col, (_, r) in zip(cols, df_adv.head(3).iterrows()):
            sym = r["الرمز"]
            score = int(r["درجة فنية"])
            card_color = "#00c853" if "شراء" in str(r["إشارة"]) else ("#ff3d57" if "بيع" in str(r["إشارة"]) else "#78909c")
            with col:
                st.markdown(f"""
                <div class="pick-card" style="border-color:{card_color};">
                    <div style="display:flex; justify-content:space-between; align-items:center;">
                        <b style="color:white; font-size:1.15rem;">{sym.replace('.CA','')}</b>
                        <span style="background:{card_color}; color:white; padding:3px 10px; border-radius:12px; font-size:0.72rem; font-weight:700;">{r['إشارة']}</span>
                    </div>
                    <div style="color:#7d8db1; font-size:0.72rem; margin:0.25rem 0;">{get_company_name(sym)[:35]}</div>
                    <div style="background:rgba(255,255,255,0.04); border-radius:8px; padding:0.3rem 0.5rem; margin:0.3rem 0; font-size:0.75rem; color:#90caf9;">
                        📌 {r.get('النموذج', 'نموذج فني')}
                    </div>
                    <div style="display:flex; justify-content:space-between; margin-top:0.4rem;">
                        <div>
                            <div style="color:{card_color}; font-size:1.5rem; font-weight:800;">{score}<span style="font-size:0.7rem; color:#7d8db1;">/100</span></div>
                            <div style="color:#7d8db1; font-size:0.65rem;">الدرجة الفنية</div>
                        </div>
                        <div style="text-align:left;">
                            <div style="color:white; font-size:1.2rem; font-weight:700;">{r['السعر']:,.2f}</div>
                            <div style="color:{'#00c853' if r['التغير اليوم%']>=0 else '#ff3d57'}; font-size:0.75rem;">{r['التغير اليوم%']:+.2f}%</div>
                        </div>
                    </div>
                    <div style="display:flex; justify-content:space-between; margin-top:0.5rem; padding-top:0.4rem; border-top:1px solid #1f2d45;">
                        <span style="color:#00e676; font-size:0.75rem;">🎯 هدف1: <b>{r['هدف1']:,.2f}</b> ({r['هدف1%']:+.1f}%)</span>
                        <span style="color:#ffab00; font-size:0.75rem;">⚖️ R:R <b>{r['العائد/المخاطرة']}</b></span>
                    </div>
                    <div style="display:flex; justify-content:space-between; margin-top:0.3rem;">
                        <span style="color:#ff5c76; font-size:0.75rem;">🛡️ وقف: <b>{r['وقف خسارة']:,.2f}</b> (-{r['وقف%']:.1f}%)</span>
                        <span style="color:#7d8db1; font-size:0.72rem;">{r.get('السيولة', '')}</span>
                    </div>
                </div>
                """, unsafe_allow_html=True)
                bc1, bc2 = st.columns(2)
                if bc1.button("📊 حلّل", key=f"an_{sym}", use_container_width=True):
                    st.session_state["selected_symbol"] = sym
                    st.rerun()
                if bc2.button("⭐ تابع", key=f"wt_{sym}", use_container_width=True):
                    if sym not in st.session_state.watchlist:
                        st.session_state.watchlist.append(sym)
                        persist_watch()
                    st.success("أُضيف ✓")

        if beginner_mode:
            st.markdown("#### 🎓 شرح الفرصة لمستخدم ثاندر")
            st.info(beginner_summary(df_adv.iloc[0].to_dict()))

        st.markdown("#### 📋 التوصيات الكاملة (مرتبة بالقوة والعائد إلى المخاطرة)")
        cols_to_show = ["الرمز","السعر","التغير اليوم%","درجة فنية","تصنيف","وايكوف","النموذج","إشارة","العائد/المخاطرة","هدف1","هدف1%","وقف خسارة","وقف%","السيولة","RSI"]
        cols_avail = [c for c in cols_to_show if c in df_adv.columns]
        adv_display = df_adv[cols_avail].copy()
        adv_display.insert(1, "الشركة", [get_company_name(s)[:25] for s in adv_display["الرمز"]])
        st.dataframe(adv_display, use_container_width=True, hide_index=True, height=400,
            column_config={
                "درجة فنية": st.column_config.ProgressColumn(min_value=0, max_value=100, format="%.0f"),
                "التغير اليوم%": st.column_config.NumberColumn(format="%.2f%%"),
                "هدف1%": st.column_config.NumberColumn(format="+%.1f%%"),
                "وقف%": st.column_config.NumberColumn(format="-%.1f%%"),
                "السعر": st.column_config.NumberColumn(format="%.2f"),
                "هدف1": st.column_config.NumberColumn(format="%.2f"),
                "وقف خسارة": st.column_config.NumberColumn(format="%.2f"),
                "RSI": st.column_config.NumberColumn(format="%.0f"),
            })

        pick_adv = st.selectbox("افتح تحليل سهم من التوصيات", options=df_adv["الرمز"].tolist(),
                                format_func=lambda s: f"{s.replace('.CA','')} — {get_company_name(s)[:30]}", key="pick_adv")
        pv1, pv2 = st.columns(2)
        if pv1.button("🎯 افتح تحليل خبير البورصة", key="open_adv", use_container_width=True):
            st.session_state["selected_symbol"] = pick_adv
            st.rerun()
        if pv2.button("⭐ أضف للمتابعة السريعة", key="watch_adv", use_container_width=True):
            if pick_adv not in st.session_state.watchlist:
                st.session_state.watchlist.append(pick_adv)
                persist_watch()
            st.success("أُضيف ✓")

        csv_adv = adv_display.to_csv(index=False).encode('utf-8-sig')
        st.download_button("⬇️ تصدير التوصيات CSV", csv_adv, "egx_recommendations.csv", "text/csv", use_container_width=True)
    else:
        st.info("المحرك يعمل تلقائياً — سيظهر الكروت بعد لحظات")

    # ===== سجل التوصيات — ملف الإنجاز الموثق =====
    st.markdown("---")
    st.markdown("#### 📜 سجل التوصيات — ملف الإنجاز الموثق")
    st.caption("كل توصية عالية الثقة تُسجَّل آلياً بتاريخها وسعرها ولا تُحذف أبداً — المنصة تقيس نفسها بالأرقام لا بالوعود")
    recs = USER_STORE.get("rec_log", [])
    if not recs:
        st.caption("السجل فارغ — سيُملأ تلقائياً مع أول فحص يظهر فرصاً عالية الثقة")
    else:
        snap_r = tvd.snapshot()
        rows_r = []
        for rec in recs:
            tv_rr = snap_r.get(rec["symbol"].replace(".CA", ""))
            now_p = tv_rr["close"] if tv_rr else None
            entry_r = float(rec["entry"]); stop_r = float(rec["stop"]); t1_r = float(rec["t1"])
            pl_r = (now_p - entry_r) / entry_r * 100 if now_p else None
            if now_p is None:
                status_r = "— بلا بيانات"
            elif now_p <= stop_r:
                status_r = "🚨 ضرب الوقف"
            elif now_p >= t1_r:
                status_r = "🎯 حققت الهدف"
            else:
                status_r = "⏳ جارية"
            rows_r.append({"التاريخ": rec["date"], "الرمز": rec["symbol"].replace(".CA", ""),
                           "دخول": round(entry_r, 2),
                           "الآن": round(now_p, 2) if now_p else None,
                           "العائد%": round(pl_r, 2) if pl_r is not None else None,
                           "هدف1": round(t1_r, 2), "وقف": round(stop_r, 2),
                           "الدرجة": rec.get("score"), "الحالة": status_r})
        df_rec = pd.DataFrame(rows_r)
        closed_r = df_rec[df_rec["الحالة"].isin(["🚨 ضرب الوقف", "🎯 حققت الهدف"])]
        if not closed_r.empty:
            wins_r = int((closed_r["الحالة"] == "🎯 حققت الهدف").sum())
            tr1, tr2, tr3 = st.columns(3)
            tr1.metric("توصيات مُغلقة", len(closed_r))
            tr2.metric("حققت الهدف", wins_r)
            tr3.metric("نسبة النجاح الفعلية", f"{wins_r / len(closed_r) * 100:.0f}%")
        st.dataframe(df_rec.sort_values("التاريخ", ascending=False), use_container_width=True,
                     hide_index=True, height=260,
                     column_config={
                         "العائد%": st.column_config.NumberColumn(format="%.2f%%"),
                         "دخول": st.column_config.NumberColumn(format="%.2f"),
                         "الآن": st.column_config.NumberColumn(format="%.2f"),
                         "هدف1": st.column_config.NumberColumn(format="%.2f"),
                         "وقف": st.column_config.NumberColumn(format="%.2f"),
                     })
    st.caption("⚠️ استرشادية مبنية على التحليل الفني — لا تخاطر بأكثر من 2% من رأس مالك في صفقة واحدة")

# ============================================================
# TAB 3: التحليل المفصل
# ============================================================
with tab_detail:
    company_name = get_company_name(symbol)

    with st.spinner(f"تحميل {symbol}..."):
        # فترات العرض القصير (أسبوع/أسبوعين): نجلب 6 أشهر كاملة لتحليل سليم ونعرض آخر شموع فقط
        if period in ("5d", "10d"):
            df = cached_single(symbol, "6mo")
        else:
            df = cached_single(symbol, period)
        info = cached_info(symbol)

    # السعر اللحظي من TradingView (يُجلب قبل التحليل لنتمكن من تحديث شمعة اليوم)
    tv_row = tvd.one(symbol)
    live_price = tv_row["close"] if tv_row else None
    live_ch = tv_row["change_pct"] if tv_row else None
    market_open_now = egx_market_status()["open"]

    if df.empty:
        st.error(f"تعذر تحميل بيانات {symbol}. جرّب سهم آخر.")
    else:
        # ⚡ التحليل اللحظي: حدّث شمعة اليوم بالسعر الحالي من TradingView
        use_live = live_price is not None
        if live_price is not None:
            use_live = st.toggle(
                "⚡ التحليل اللحظي — حدّث شمعة اليوم بالسعر الحالي من TradingView",
                value=market_open_now,
                help="عند التفعيل تُحسب كل المؤشرات والقرار الفني على سعر اللحظي لجلسة اليوم، وليس إغلاق الأمس فقط",
            )
        if use_live and live_price is not None:
            df = df.copy()
            i_last = len(df) - 1
            df.iloc[i_last, df.columns.get_loc("Close")] = live_price
            if live_price > float(df["High"].iloc[i_last]):
                df.iloc[i_last, df.columns.get_loc("High")] = live_price
            if live_price < float(df["Low"].iloc[i_last]):
                df.iloc[i_last, df.columns.get_loc("Low")] = live_price

        df_ind = add_indicators(df)
        last_signals = get_last_signals(df_ind)
        signal = generate_combined_signal(last_signals, df_ind, "1d")
        support, resistance = get_support_resistance(df_ind)
        vwap_info = calculate_vwap_signals(df_ind)
        rinfo = risk_score(last_signals, df_ind)
        atr_stops = calculate_atr_based_stops(last_signals, signal["action"])
        tech_score = calculate_technical_score(last_signals, df_ind)
        price_targets = calculate_price_targets(last_signals, df_ind)

        # المستشار الاستثماري وخبير البورصة المصرية
        expert = generate_expert_verdict(symbol, df)
        v_action = expert.get("verdict", signal["action"])
        v_color = expert.get("verdict_color", "#00c853")
        v_summary = expert.get("verdict_summary", "")
        v_memo = expert.get("executive_memo", "")
        wyckoff = expert.get("wyckoff", {})
        mtf = expert.get("mtf", {})
        plan = expert.get("plan", {})
        bulls = expert.get("bullish_signals", [])
        bears = expert.get("bearish_warnings", [])
        nature = expert.get("stock_nature", "سهم مدرج بالبورصة")
        nature_adv = expert.get("nature_advice", "")
        is_spec = expert.get("is_speculative", False)
        theme = expert.get("theme", "سهم مصري")
        div_yield_pct = expert.get("div_yield_pct", 0.0)
        fund_pe = expert.get("pe")

        last_close = float(df["Close"].iloc[-1])
        prev_close = float(df["Close"].iloc[-2]) if len(df) > 1 else last_close
        daily_ch = (last_close - prev_close) / prev_close * 100 if prev_close else 0
        cur = info.get("currency", "EGP")
        is_buy = "شراء" in v_action
        is_sell = "بيع" in v_action or "تخفيف" in v_action

        # ===== رأس الصفحة: السعر + بيانات لحظية =====
        hcol1, hcol2 = st.columns([1.4, 1])
        with hcol1:
            st.markdown(f"### {company_name} — `{symbol}`")
            m1, m2, m3, m4, m5 = st.columns(5)
            if live_price is not None:
                m1.metric("السعر الحالي — TradingView", f"{live_price:,.2f}", f"{live_ch:+.2f}%")
            else:
                m1.metric("آخر إغلاق", f"{last_close:,.2f}", f"{daily_ch:+.2f}%")
            turnover_val = plan.get("turnover_m", 0)
            m2.metric("السيولة اليومية", f"{turnover_val:.1f}M ج.م" if turnover_val else f"{int(df['Volume'].iloc[-1]):,}")
            mcap = info.get("marketCap") or (tv_row or {}).get("market_cap")
            m3.metric("القيمة السوقية", f"{mcap/1e9:,.1f}B" if mcap else "—")
            pe_disp = info.get("trailingPE") or fund_pe  # البيانات اللحظية أولاً، المرجعية احتياط
            m4.metric("مكرر الربحية P/E", f"{pe_disp:.1f}" if pe_disp else "—")
            if div_yield_pct and div_yield_pct > 0:
                m5.metric("عائد التوزيعات", f"{div_yield_pct:.1f}%")
            else:
                wk_hi = info.get("fiftyTwoWeekHigh")
                wk_lo = info.get("fiftyTwoWeekLow")
                m5.metric("52 أسبوع", f"{wk_lo:,.0f}-{wk_hi:,.0f}" if wk_hi else "—")
            try:
                last_str = pd.to_datetime(df.index[-1]).strftime("%Y-%m-%d")
            except:
                last_str = str(df.index[-1])
            src_note = " • ⚡ التحليل محدّث بالسعر اللحظي" if (use_live and live_price is not None) else " • التحليل على إغلاق الجلسة"
            st.caption(f"📅 رسوم التحليل حتى جلسة: {last_str}{src_note}")
        with hcol2:
            wk_hi = info.get("fiftyTwoWeekHigh")
            wk_lo = info.get("fiftyTwoWeekLow")
            st.markdown(f"""
            <div class="tech-score-card" style="padding:0.9rem;">
                <div style="color:#7d8db1; font-size:0.75rem;">نطاق 52 أسبوع</div>
                <div style="color:white; font-size:1.25rem; font-weight:800;">{f'{wk_lo:,.1f} — {wk_hi:,.1f}' if wk_hi else '—'}</div>
                <div style="margin-top:0.6rem; color:#7d8db1; font-size:0.75rem;">موقع السعر من النطاق</div>
            """, unsafe_allow_html=True)
            if wk_hi and wk_lo and wk_hi > wk_lo:
                pos52 = (last_close - wk_lo) / (wk_hi - wk_lo) * 100
                pos52 = min(max(pos52, 0), 100)
                st.markdown(f"""
                <div style="height:8px; border-radius:4px; background:linear-gradient(90deg, #ff3d57, #ffab00, #00e676); position:relative;">
                    <div style="position:absolute; left:{pos52:.0f}%; top:-4px; width:14px; height:16px; background:white; border-radius:3px; transform:translateX(-50%);"></div>
                </div>
                <div style="display:flex; justify-content:space-between; font-size:0.65rem; color:#7d8db1; margin-top:0.3rem;">
                    <span>أدنى {wk_lo:,.1f}</span><span style="color:white; font-weight:700;">الآن {pos52:.0f}%</span><span>أعلى {wk_hi:,.1f}</span>
                </div>
                </div>
                """, unsafe_allow_html=True)
            else:
                st.markdown("</div>", unsafe_allow_html=True)
            st.caption("📊 نطاق التذبذب السنوي")

        st.markdown("---")

        # ===== بطاقة القرار الاستشاري الحاسم =====
        st.markdown(f"""
        <div style="background:linear-gradient(135deg, #0d1624 0%, #101d32 100%); border: 2px solid {v_color}; border-radius: 16px; padding: 1.3rem 1.5rem; margin: 0.8rem 0; box-shadow: 0 8px 24px rgba(0,0,0,0.4);">
            <div style="display:flex; justify-content:space-between; align-items:flex-start; flex-wrap:wrap; gap:1rem;">
                <div style="flex: 1; min-width: 280px;">
                    <div style="font-size:0.8rem; color:#90caf9; font-weight:800; text-transform:uppercase; letter-spacing:0.5px;">🎯 قرار خبير البورصة المصرية ومستشار الصناديق:</div>
                    <div style="font-size:2.1rem; font-weight:900; color:{v_color}; margin:0.3rem 0; line-height:1.2;">{v_action}</div>
                    <div style="color:white; font-size:1.05rem; font-weight:600; margin-top:0.3rem;">{v_summary}</div>
                    <div style="display:flex; gap:0.5rem; flex-wrap:wrap; margin-top:0.9rem;">
                        <span style="background:rgba(255,255,255,0.07); border:1px solid #2a3b5c; border-radius:8px; padding:4px 10px; font-size:0.75rem; color:#e0e0e0;">🏛️ {nature}</span>
                        <span style="background:rgba(255,255,255,0.07); border:1px solid #2a3b5c; border-radius:8px; padding:4px 10px; font-size:0.75rem; color:#e0e0e0;">🔄 مرحلة وايكوف: {wyckoff.get('tag', 'عرضي')}</span>
                        <span style="background:rgba(255,255,255,0.07); border:1px solid #2a3b5c; border-radius:8px; padding:4px 10px; font-size:0.75rem; color:#90caf9;">🌐 {theme}</span>
                        <span style="background:rgba(255,255,255,0.07); border:1px solid #2a3b5c; border-radius:8px; padding:4px 10px; font-size:0.75rem; color:#ffd54f;">📈 الأسبوعي: {mtf.get('weekly_trend', 'محايد')}</span>
                    </div>
                </div>
                <div style="text-align:center; background:rgba(255,255,255,0.06); border:1px solid rgba(255,255,255,0.12); padding:0.9rem 1.4rem; border-radius:14px; min-width:140px;">
                    <div style="color:{v_color}; font-size:1.8rem; font-weight:900;">{tech_score['score']}<span style="font-size:0.8rem; color:#7d8db1;">/100</span></div>
                    <div style="color:#cfd8dc; font-size:0.75rem; font-weight:700;">الدرجة الفنية</div>
                    <div style="color:#7d8db1; font-size:0.65rem; margin-top:0.2rem;">18 مؤشر فني</div>
                </div>
            </div>
        </div>
        """, unsafe_allow_html=True)

        # ===== الرسم المباشر الاحترافي — محرك TradingView (نفس محرك ثاندر والمنصات العالمية) =====
        st.markdown("#### 📊 الرسم المباشر التفاعلي")
        tv.render_tv(tv.tradingview_advanced_chart(f"EGX:{symbol.replace('.CA','')}", height=700), height=740)
        st.caption("🎨 شموع كاملة بارتفاع كبير + أدوات الرسم على اليسار • غيّر الفترة من الشريط العلوي (دقائق/ساعات/أيام/سنوات) • أضف أي مؤشر من زر Ⲷ مؤشرات • اسحب الزاوية أو استخدم وضع ملء الشاشة من القائمة")

        # ===== صندوق التنفيذ الرقمي (Digital Execution Box) =====
        st.markdown(f"""
        <div style="background:#10141d; border:1px solid #1f2d45; border-radius:14px; padding:1.2rem; margin-bottom:1rem;">
            <div style="display:flex; justify-content:space-between; align-items:center; margin-bottom:0.9rem; border-bottom:1px solid #1f2d45; padding-bottom:0.6rem;">
                <span style="font-size:1rem; font-weight:800; color:white;">📋 خطة التنفيذ الرقمية (بالقرش والجنيه)</span>
                <span style="font-size:0.8rem; color:#90caf9;">⚖️ نسبة العائد إلى المخاطرة (R:R): <b style="color:#00e676; font-size:0.95rem;">{plan.get('rr_ratio', '1:1.5')}</b></span>
            </div>
            <div style="display:grid; grid-template-columns: repeat(auto-fit, minmax(180px, 1fr)); gap:0.8rem;">
                <div style="background:rgba(0,200,83,0.06); border:1px solid rgba(0,200,83,0.3); border-radius:10px; padding:0.8rem; text-align:center;">
                    <div style="color:#7d8db1; font-size:0.75rem; font-weight:700;">🟢 منطقة الشراء المفضلة</div>
                    <div style="color:#00e676; font-size:1.2rem; font-weight:900; margin-top:0.2rem;">{plan.get('buy_zone', f'{last_close:,.2f}')}</div>
                    <div style="color:#a5d6a7; font-size:0.68rem; margin-top:0.2rem;">أفضل نطاق للدخول الآمن</div>
                </div>
                <div style="background:rgba(255,61,87,0.06); border:1px solid rgba(255,61,87,0.3); border-radius:10px; padding:0.8rem; text-align:center;">
                    <div style="color:#7d8db1; font-size:0.75rem; font-weight:700;">🛡️ وقف الخسارة الحاسم</div>
                    <div style="color:#ff5c76; font-size:1.2rem; font-weight:900; margin-top:0.2rem;">{plan.get('stop_loss', 0):,.2f} ج.م</div>
                    <div style="color:#ef9a9a; font-size:0.68rem; margin-top:0.2rem;">خسارة محتملة: -{plan.get('stop_pct', 0):.1f}%</div>
                </div>
                <div style="background:rgba(41,98,255,0.06); border:1px solid rgba(41,98,255,0.3); border-radius:10px; padding:0.8rem; text-align:center;">
                    <div style="color:#7d8db1; font-size:0.75rem; font-weight:700;">🎯 الهدف الأول (جني ربح جزئي)</div>
                    <div style="color:#64b5f6; font-size:1.2rem; font-weight:900; margin-top:0.2rem;">{plan.get('target_1', 0):,.2f} ج.م</div>
                    <div style="color:#90caf9; font-size:0.68rem; margin-top:0.2rem;">ربح متوقع: +{plan.get('target_1_pct', 0):.1f}%</div>
                </div>
                <div style="background:rgba(171,71,188,0.06); border:1px solid rgba(171,71,188,0.3); border-radius:10px; padding:0.8rem; text-align:center;">
                    <div style="color:#7d8db1; font-size:0.75rem; font-weight:700;">🚀 الهدف الثاني (امتداد الموجة)</div>
                    <div style="color:#ce93d8; font-size:1.2rem; font-weight:900; margin-top:0.2rem;">{plan.get('target_2', 0):,.2f} ج.م</div>
                    <div style="color:#e1bee7; font-size:0.68rem; margin-top:0.2rem;">ربح متوقع: +{plan.get('target_2_pct', 0):.1f}%</div>
                </div>
            </div>
            <div style="margin-top:0.9rem; padding-top:0.7rem; border-top:1px solid #1f2d45; display:flex; justify-content:space-between; align-items:center; flex-wrap:wrap; gap:0.6rem; font-size:0.8rem;">
                <span style="color:#e0e0e0;">💡 <b>توجيه صانع السوق ووايكوف:</b> {wyckoff.get('action_advice', '')}</span>
                <span style="color:#7d8db1;">💧 <b>السيولة الحالية:</b> {plan.get('liquidity', 'سيولة مقبولة')}</span>
            </div>
        </div>
        """, unsafe_allow_html=True)

        # تسجيل الصفقة في المراقبة اللحظية
        idea_entry = live_price if live_price is not None else last_close
        if st.button("🎯 راقب هذه الصفقة لحظياً (الدخول الحالي + الوقف + الأهداف)", type="primary", use_container_width=True, key=f"idea_{symbol}"):
            add_trade_idea(symbol, idea_entry,
                           plan.get("stop_loss", last_close * 0.95),
                           plan.get("target_1", last_close * 1.05),
                           plan.get("target_2"))
            st.success("✓ أُضيفت إلى مراقبة الصفقات — تابعها لحظياً في تبويب ⭐ المتابعة والصفقات")

        # ===== المذكرة الاستشارية التنفيذية =====
        st.markdown(f"""
        <div style="background:rgba(41,98,255,0.05); border-right:4px solid #2962ff; border-radius:10px; padding:1rem 1.2rem; margin-bottom:1.2rem;">
            <div style="color:#64b5f6; font-weight:800; font-size:0.95rem; margin-bottom:0.4rem;">🏛️ مذكرة مدير الاستثمار لمستثمري البورصة المصرية:</div>
            <div style="color:#e0e0e0; font-size:0.92rem; line-height:1.7;">
                {v_memo.replace(chr(10), '<br>')}
            </div>
        </div>
        """, unsafe_allow_html=True)

        # ===== أسباب القرار وعوامل التأكيد والتحذير =====
        rcol1, rcol2 = st.columns(2)
        with rcol1:
            st.markdown("#### 🟢 عوامل القوة والتأكيد الشرائي")
            if bulls:
                for b in bulls:
                    st.markdown(f'<div style="background:rgba(0,200,83,0.06); border:1px solid rgba(0,200,83,0.25); border-radius:8px; padding:0.5rem 0.8rem; margin-bottom:0.4rem; font-size:0.85rem; color:#e0e0e0;">✓ {b}</div>', unsafe_allow_html=True)
            else:
                st.caption("لا توجد إشارات قوة مؤكدة حالياً تدعم الشراء المباشر.")

        with rcol2:
            st.markdown("#### 🔴 التحذيرات ومصائد صناع السوق")
            if bears:
                for w in bears:
                    st.markdown(f'<div style="background:rgba(255,61,87,0.06); border:1px solid rgba(255,61,87,0.25); border-radius:8px; padding:0.5rem 0.8rem; margin-bottom:0.4rem; font-size:0.85rem; color:#e0e0e0;">⚠️ {w}</div>', unsafe_allow_html=True)
            else:
                st.markdown('<div style="background:rgba(0,200,83,0.05); border-radius:8px; padding:0.5rem 0.8rem; font-size:0.85rem; color:#81c784;">✓ لا توجد تحذيرات سلبية حرجة على السهم حالياً.</div>', unsafe_allow_html=True)

        # ===== الأخبار والإفصاحات الحقيقية (Google News) =====
        with st.expander("📰 آخر أخبار وإفصاحات السهم — حقيقية ومحدّثة", expanded=False):
            news_items = newsfeed.fetch_news(f'"{company_name}" OR {symbol.replace(".CA","")} البورصة المصرية')
            if not news_items:
                st.caption("لا توجد أخبار حديثة متاحة لهذا السهم الآن")
            else:
                for it in news_items:
                    src_html = f' — <span style="color:#7d8db1;">{it["source"]}</span>' if it.get("source") else ""
                    st.markdown(f'<div style="border-right:3px solid #2962ff; padding:0.4rem 0.7rem; margin-bottom:0.35rem; background:rgba(41,98,255,0.04); border-radius:6px;"><a href="{it["link"]}" target="_blank" style="color:#90caf9; text-decoration:none; font-size:0.85rem;">{it["title"]}</a><div style="color:#7d8db1; font-size:0.68rem; margin-top:0.15rem;">📅 {it["pub"]}{src_html}</div></div>', unsafe_allow_html=True)
            st.caption("⚠️ عناوين حقيقية من مصادر إخبارية عامة — راجع الإفصاح الرسمي للبورصة قبل أي قرار")

        st.markdown("---")

        # ===== حاسبة سيناريو الربح والمخاطرة (استرشادية بدون حفظ بيانات) =====
        st.markdown("#### 💰 حاسبة سيناريو الصفقة (أداة حسابية بحتة دون حفظ بياناتك)")
        sc_col1, sc_col2 = st.columns([1, 1.8])
        with sc_col1:
            amount = st.number_input("مبلغ الدخول الافتراضي (ج.م)", 1000.0, 10_000_000.0, 10000.0, 1000.0, key=f"scen_{symbol}")
            st.caption("🛡️ أداة حسابية استرشادية لمساعدتك في حساب المخاطرة قبل تنفيذ الصفقة في ثاندر.")
        with sc_col2:
            stop_p = float(plan.get("stop_loss", last_close * 0.95))
            tgt1_p = float(plan.get("target_1", last_close * 1.05))
            tgt2_p = float(plan.get("target_2", last_close * 1.10))
            sh_count = int(amount // last_close) if last_close else 0
            if sh_count > 0:
                cost_actual = sh_count * last_close
                p_loss = sh_count * (last_close - stop_p)
                p_prof1 = sh_count * (tgt1_p - last_close)
                p_prof2 = sh_count * (tgt2_p - last_close)
                loss_pct = (p_loss / cost_actual * 100) if cost_actual else 0
                prof1_pct = (p_prof1 / cost_actual * 100) if cost_actual else 0
                prof2_pct = (p_prof2 / cost_actual * 100) if cost_actual else 0

                st.markdown(f"""
                <div style="background:#10141d; border:1px solid #1f2d45; border-radius:12px; padding:0.9rem;">
                    <div style="color:white; font-size:0.9rem; font-weight:700; margin-bottom:0.5rem;">
                        📊 سيناريو شراء <b>{sh_count:,} سهم</b> (قيمة فعلية: {cost_actual:,.0f} ج.م):
                    </div>
                    <div style="display:flex; justify-content:space-between; flex-wrap:wrap; gap:0.5rem;">
                        <div style="background:rgba(255,61,87,0.08); border-radius:8px; padding:0.5rem 0.8rem; flex:1; min-width:130px;">
                            <div style="color:#ff5c76; font-size:0.75rem; font-weight:700;">🔴 عند وقف الخسارة</div>
                            <div style="color:white; font-size:1.05rem; font-weight:800;">-{p_loss:,.0f} ج.م</div>
                            <div style="color:#ef9a9a; font-size:0.68rem;">-{loss_pct:.1f}% من القيمة</div>
                        </div>
                        <div style="background:rgba(0,200,83,0.08); border-radius:8px; padding:0.5rem 0.8rem; flex:1; min-width:130px;">
                            <div style="color:#00e676; font-size:0.75rem; font-weight:700;">🟢 عند الهدف الأول</div>
                            <div style="color:white; font-size:1.05rem; font-weight:800;">+{p_prof1:,.0f} ج.م</div>
                            <div style="color:#a5d6a7; font-size:0.68rem;">+{prof1_pct:.1f}% ربح</div>
                        </div>
                        <div style="background:rgba(41,98,255,0.08); border-radius:8px; padding:0.5rem 0.8rem; flex:1; min-width:130px;">
                            <div style="color:#64b5f6; font-size:0.75rem; font-weight:700;">🚀 عند الهدف الثاني</div>
                            <div style="color:white; font-size:1.05rem; font-weight:800;">+{p_prof2:,.0f} ج.م</div>
                            <div style="color:#90caf9; font-size:0.68rem;">+{prof2_pct:.1f}% ربح</div>
                        </div>
                    </div>
                </div>
                """, unsafe_allow_html=True)
            else:
                st.caption("المبلغ أقل من سعر سهم واحد.")

        with st.container():
            # مرحلة وايكوف والاتجاه الكلي
            wyckoff_tag = wyckoff.get("tag", "عرضي")
            phase_colors = {
                "تجميع": "#29b6f6", "بناء قاع": "#ffb300", "انطلاق صاعد": "#00e676",
                "تشبع صاعد": "#ff9800", "تصريف": "#ff5c76", "مسار هابط": "#d32f2f", "عرضي": "#90a4ae"
            }
            pc = next((v for k, v in phase_colors.items() if k in wyckoff_tag), "#90a4ae")
            mtf_bias = mtf.get("bias", "neutral")
            mtf_color = "#00e676" if mtf_bias == "bullish" else ("#ff5c76" if mtf_bias == "bearish" else "#90a4ae")
            st.markdown(f"""
            <div style="background:#10141d; border:1px solid #1f2d45; border-radius:14px; padding:1rem;">
                <div style="color:#7d8db1; font-size:0.72rem; font-weight:700; text-transform:uppercase; letter-spacing:0.5px;">مرحلة وايكوف (Wyckoff Phase)</div>
                <div style="font-size:1.35rem; font-weight:900; color:{pc}; margin:0.3rem 0; line-height:1.2;">{wyckoff_tag}</div>
                <div style="color:#cfd8dc; font-size:0.78rem; line-height:1.5;">{wyckoff.get('desc', '')[:120]}</div>
                <div style="margin-top:0.8rem; border-top:1px solid #1f2d45; padding-top:0.7rem;">
                    <div style="color:#7d8db1; font-size:0.72rem; font-weight:700;">الاتجاه طويل المدى (MTF)</div>
                    <div style="color:{mtf_color}; font-size:1rem; font-weight:800; margin-top:0.2rem;">{mtf.get('weekly_trend', '—')}</div>
                    <div style="color:#90a4ae; font-size:0.75rem; margin-top:0.2rem;">{mtf.get('desc', '')[:90]}</div>
                </div>
            </div>
            """, unsafe_allow_html=True)

            st.markdown("")

            # تقييم مخاطر سريع
            st.markdown("##### 🛡️ المخاطر والجدارة المالية")
            st.metric("مستوى المخاطر", rinfo["level"], f"{rinfo['risk_score']}/100")
            st.progress(min(rinfo["risk_score"]/100, 1.0))
            for n in rinfo["notes"][:2]:
                st.caption(f"• {n}")

            # حجم المركز
            sizing = position_sizing(capital, risk_pct, last_close, plan.get("stop_loss", last_close*0.95), max_pct)
            if "error" not in sizing:
                st.markdown("##### 📐 حجم المركز المقترح (إدارة رأس المال)")
                st.metric("عدد الأسهم الأمثل", f"{sizing['عدد_الأسهم']:,}")
                st.metric("قيمة المركز", f"{sizing['قيمة_المركز']:,.0f} ج.م")
                st.caption(f"بحد أقصى {max_pct:.0f}% من رأس المال ومخاطرة {risk_pct:.1f}%/صفقة")

        st.markdown("---")

        # ===== الارتفاع المتوقع + الأداء + الأهداف =====
        tcol1, tcol2, tcol3 = st.columns(3)
        with tcol1:
            st.markdown("#### 📈 الارتفاع المتوقع")
            if is_buy and atr_stops and "targets" in atr_stops:
                t1 = atr_stops["targets"]["الهدف الأول (1:1)"]
                t2 = atr_stops["targets"]["الهدف الثاني (1.5:1)"]
                t3 = atr_stops["targets"]["الهدف الثالث (2:1)"]
                exp1 = (t1 - last_close)/last_close*100
                exp2 = (t2 - last_close)/last_close*100
                exp3 = (t3 - last_close)/last_close*100
                if resistance:
                    exp_res = (resistance - last_close)/last_close*100
                    st.metric("إلى المقاومة", f"{exp_res:+.1f}%", f"{resistance:,.2f}")
                e1, e2, e3 = st.columns(3)
                e1.metric("هدف1", f"{exp1:+.1f}%")
                e2.metric("هدف2", f"{exp2:+.1f}%")
                e3.metric("هدف3", f"{exp3:+.1f}%")
                st.caption("تقديرية بناءً على ATR والمقاومة — ليست ضماناً")
            else:
                if resistance and support:
                    up = (resistance - last_close)/last_close*100
                    down = (support - last_close)/last_close*100
                    st.metric("مسافة المقاومة", f"{up:+.1f}%", f"{resistance:,.1f}")
                    st.metric("مسافة الدعم", f"{down:+.1f}%", f"{support:,.1f}")
                st.caption("لا ارتفاع متوقع حتى ظهور إشارة شراء")

        with tcol2:
            st.markdown("#### 📊 الأداء التاريخي")
            perf_df, perf_raw = cached_performance(symbol)
            if not perf_df.empty:
                st.dataframe(perf_df, hide_index=True, use_container_width=True, height=210,
                    column_config={"العائد %": st.column_config.NumberColumn(format="%.2f%%")})
                if perf_raw.get("منذ الإنشاء") is not None:
                    st.caption(f"🏛️ منذ {perf_raw.get('تاريخ البداية','')}: **{perf_raw['منذ الإنشاء']:+.0f}%**")
            else:
                st.caption("غير متاح")

        with tcol3:
            st.markdown("#### 🎯 أهداف متقدمة")
            if price_targets:
                if "summary" in price_targets:
                    s = price_targets["summary"]
                    st.metric("الربح المتوقع", f"+{s['expected_rise_pct']}%", f"أقصى +{s['max_rise_pct']}%")
                    st.caption(f"مخاطرة/عائد 1:{s['risk_reward_1']} • وقف -{s['stop_loss_pct']}%")
                if "Pivot" in price_targets:
                    pv = price_targets["Pivot"]
                    st.caption(f"Pivot {pv['pivot']:,.2f} • R1 {pv['R1']:,.2f} • S1 {pv['S1']:,.2f}")
                if "Fibonacci" in price_targets:
                    fb = price_targets["Fibonacci"]
                    fib_618 = fb["levels"].get("61.8%", 0)
                    fib_382 = fb["levels"].get("38.2%", 0)
                    st.caption(f"Fib 61.8%: {fib_618:,.2f} • Fib 38.2%: {fib_382:,.2f}")

        st.markdown("---")

        # ===== الأسباب + الرسم + تبويبات متقدمة =====
        with st.expander("🔍 أسباب القرار (لماذا؟)", expanded=True):
            for r in signal["reasons"]:
                st.markdown(f"• {r}")
            if support and resistance:
                st.markdown(f"**الدعم:** {support:,.2f} — **المقاومة:** {resistance:,.2f}")
            if vwap_info:
                vcol = "#00e676" if vwap_info["above_vwap"] else "#ff5c76"
                st.markdown(f'<span style="color:{vcol}">VWMA20 (متوسط السعر الموزون بالسيولة): {vwap_info["vwma"]:.2f} — السعر {"فوق" if vwap_info["above_vwap"] else "تحت"}ه بـ {vwap_info["distance_pct"]:+.1f}%</span>', unsafe_allow_html=True)
            with st.expander("تفصيل درجة التحليل الفني"):
                for name, pts, desc in tech_score["breakdown"]:
                    pcol = "#00e676" if pts.startswith("+") else ("#ff5c76" if pts.startswith("-") else "#7d8db1")
                    st.markdown(f'<div style="display:flex; justify-content:space-between; padding:0.25rem 0; border-bottom:1px solid #1f2d45;"><span style="color:white;">{name}</span><span style="color:{pcol}; font-weight:700;">{pts}</span><span style="color:#7d8db1; font-size:0.8rem;">{desc}</span></div>', unsafe_allow_html=True)

        # الرسم
        st.markdown("#### 📈 الرسم الفني مع المؤشرات")
        # العرض القصير (أسبوع/أسبوعين): التحليل كله على التاريخ الكامل، والرسم يعرض آخر شموع فقط
        SHORT_VIEWS = {"5d": 7, "10d": 12}
        df_plot = df_ind.tail(SHORT_VIEWS[period]) if period in SHORT_VIEWS else df_ind
        xd = short_dates(df_plot.index)
        fig = make_subplots(rows=4, cols=1, shared_xaxes=True, vertical_spacing=0.02,
                            row_heights=[0.50, 0.15, 0.18, 0.17],
                            subplot_titles=("السعر والمتوسطات", "الحجم", "RSI", "MACD"))
        fig.add_trace(go.Candlestick(x=xd, open=df_plot["Open"], high=df_plot["High"], low=df_plot["Low"], close=df_plot["Close"], name="الشموع"), row=1, col=1)
        fig.add_trace(go.Scatter(x=xd, y=df_plot["SMA20"], name="SMA20", line=dict(color="orange", width=1)), row=1, col=1)
        fig.add_trace(go.Scatter(x=xd, y=df_plot["SMA50"], name="SMA50", line=dict(color="#00c853", width=1.2)), row=1, col=1)
        if "SMA200" in df_plot.columns:
            fig.add_trace(go.Scatter(x=xd, y=df_plot["SMA200"], name="SMA200", line=dict(color="#ab47bc", width=1.2)), row=1, col=1)
        if "Supertrend" in df_plot.columns and df_plot["Supertrend"].notna().any():
            fig.add_trace(go.Scatter(x=xd, y=df_plot["Supertrend"], name="Supertrend", line=dict(width=1.6)), row=1, col=1)
        if support and resistance:
            fig.add_hline(y=resistance, line_dash="dash", line_color="#ff3d57", annotation_text=f"مقاومة {resistance:.1f}", row=1, col=1)
            fig.add_hline(y=support, line_dash="dash", line_color="#00c853", annotation_text=f"دعم {support:.1f}", row=1, col=1)
        colors = ["#00c853" if c >= o else "#ff3d57" for c, o in zip(df_plot["Close"], df_plot["Open"])]
        fig.add_trace(go.Bar(x=xd, y=df_plot["Volume"], name="الحجم", marker_color=colors, opacity=0.6), row=2, col=1)
        fig.add_trace(go.Scatter(x=xd, y=df_plot["RSI"], name="RSI", line=dict(color="#ffab00", width=1.8)), row=3, col=1)
        fig.add_hline(y=70, line_dash="dash", line_color="#ff3d57", row=3, col=1)
        fig.add_hline(y=30, line_dash="dash", line_color="#00c853", row=3, col=1)
        fig.add_hrect(y0=70, y1=100, fillcolor="#ff3d57", opacity=0.08, row=3, col=1)
        fig.add_hrect(y0=0, y1=30, fillcolor="#00c853", opacity=0.08, row=3, col=1)
        fig.add_trace(go.Bar(x=xd, y=df_plot["MACD_Hist"], name="Hist", marker_color=["#00c853" if v >= 0 else "#ff3d57" for v in df_plot["MACD_Hist"]], opacity=0.7), row=4, col=1)
        fig.add_trace(go.Scatter(x=xd, y=df_plot["MACD"], name="MACD", line=dict(color="#2962ff", width=1.5)), row=4, col=1)
        fig.add_trace(go.Scatter(x=xd, y=df_plot["MACD_Signal"], name="Signal", line=dict(color="#ff6d00", width=1.2)), row=4, col=1)
        fig.update_layout(height=780, template="plotly_dark", xaxis_rangeslider_visible=False,
                          legend=dict(orientation="h", y=1.02, x=0.5, xanchor="center", font=dict(size=10)),
                          margin=dict(l=10, r=10, t=40, b=10), hovermode="x unified")
        fig.update_xaxes(type="category")
        st.plotly_chart(fig, use_container_width=True, config={"displayModeBar": True})

        # تبويبات متقدمة
        t_tech, t_fund, t_data = st.tabs(["🔧 المؤشرات الكاملة", "🏦 المالي", "📋 البيانات"])

        with t_tech:
            g_rsi, g_macd, g_adx, g_stoch = st.columns(4)

            def make_gauge(val, title, color, low=0, high=100, suffix=""):
                figg = go.Figure()
                figg.add_trace(go.Indicator(
                    mode="gauge+number", value=val,
                    number={"suffix": suffix, "font": {"size": 22}},
                    title={"text": title, "font": {"size": 13}},
                    gauge={
                        "axis": {"range": [low, high], "tickwidth": 1, "tickcolor": "#333"},
                        "bar": {"color": color},
                        "bgcolor": "rgba(0,0,0,0)",
                        "borderwidth": 0,
                        "steps": [
                            {"range": [low, low + (high-low)*0.3], "color": "rgba(0,200,83,0.12)"},
                            {"range": [low + (high-low)*0.7, high], "color": "rgba(255,61,87,0.12)"}
                        ],
                        "threshold": {"line": {"color": "white", "width": 3}, "thickness": 0.85, "value": val}
                    }
                ))
                figg.update_layout(height=185, margin=dict(l=25, r=25, t=45, b=5),
                                   template="plotly_dark", paper_bgcolor="rgba(0,0,0,0)", font=dict(size=11))
                return figg

            rsi_v = last_signals.get("RSI", 50)
            with g_rsi:
                st.plotly_chart(make_gauge(rsi_v, "RSI", "#ffab00"), use_container_width=True)
            with g_macd:
                macd_v = last_signals.get("MACD", 0)
                sig_v = last_signals.get("MACD_Signal", 0)
                macd_ratio = (macd_v - sig_v) / abs(sig_v) * 100 if sig_v and sig_v != 0 else 0
                st.plotly_chart(make_gauge(max(-100, min(100, macd_ratio)), "MACD vs Signal", "#2962ff", -100, 100, "%"), use_container_width=True)
            with g_adx:
                st.plotly_chart(make_gauge(last_signals.get("ADX", 0), "ADX", "#ab47bc", 0, 80), use_container_width=True)
            with g_stoch:
                st.plotly_chart(make_gauge(last_signals.get("Stoch_K", 50), "Stochastic", "#29b6f6"), use_container_width=True)

            ind_tbl = pd.DataFrame([
                ["RSI (14)", f"{last_signals.get('RSI',0):.1f}", "30 بيع مفرط | 70 شراء مفرط"],
                ["RSI (9)", f"{last_signals.get('RSI_9',0):.1f}", "مضاربة سريعة"],
                ["Stoch K/D", f"{last_signals.get('Stoch_K',0):.0f}/{last_signals.get('Stoch_D',0):.0f}", "<20 بيع | >80 شراء"],
                ["MACD", f"{last_signals.get('MACD',0):.4f}", "فوق الإشارة = صاعد"],
                ["ADX", f"{last_signals.get('ADX',0):.1f}", ">25 اتجاه قوي"],
                ["CCI", f"{last_signals.get('CCI',0):.1f}", ">100 شراء مفرط"],
                ["Williams %R", f"{last_signals.get('WR',0):.1f}", "<-80 بيع مفرط"],
                ["ROC", f"{last_signals.get('ROC',0):.1f}%", "زخم 12 يوم"],
                ["Supertrend", f"{last_signals.get('Supertrend',0):,.2f}", "صاعد" if last_signals.get('ST_dir',0) >= 0 else "هابط"],
                ["SMA 20/50/200", f"{last_signals.get('SMA20',0):,.1f} / {last_signals.get('SMA50',0):,.1f} / {last_signals.get('SMA200',0):,.1f}", "اتجاه عام"],
                ["EMA 9/21", f"{last_signals.get('EMA9',0):,.2f} / {last_signals.get('EMA21',0):,.2f}", "زخم قصير"],
                ["VWAP", f"{last_signals.get('VWAP',0):,.2f}", "فوقه = صاعد"],
                ["MFI", f"{last_signals.get('MFI',0):.1f}", "سيولة — <20 بيع | >80 شراء"],
                ["StochRSI K/D", f"{last_signals.get('StochRSI_K',0):.0f}/{last_signals.get('StochRSI_D',0):.0f}", "<20 تشبع بيعي | >80 تشبع شرائي"],
                ["OBV (تدفق الأموال)", "صاعد ✓" if last_signals.get('OBV', 0) > last_signals.get('OBV_MA', 0) else "هابط ✗", "هل السيولة تدعم الاتجاه؟"],
                ["حجم/متوسط", f"{last_signals.get('Vol_Ratio',0):.1f}x", ">1.5 حجم مرتفع"],
                ["ATR", f"{last_signals.get('ATR',0):,.2f}", f"تقلب {(last_signals.get('ATR',0)/last_close*100):.1f}%" if last_close else ""],
            ], columns=["المؤشر", "القيمة", "الملاحظة"])
            st.dataframe(ind_tbl, use_container_width=True, hide_index=True)

        with t_fund:
            metrics = analyze_fundamental(symbol)
            if "error" in metrics:
                st.warning(metrics["error"])
            else:
                health = metrics.get("الجدارة_المالية", {})
                h_score = health.get("health_score", 50)
                h_verdict = health.get("verdict", "تقييم معتدل")
                h_color = health.get("color", "#ffb300")
                theme = metrics.get("طبيعة_التحوط", "سهم مدرج بالبورصة المصرية")
                desc = metrics.get("نبذة_عن_السهم", "")

                st.markdown(f"""
                <div style="background:linear-gradient(135deg, #101828 0%, #0d1b2e 100%); border:1px solid #1f2d45; border-radius:12px; padding:1rem; margin-bottom:1rem; display:flex; justify-content:space-between; align-items:center; flex-wrap:wrap; gap:0.8rem;">
                    <div>
                        <div style="color:#64b5f6; font-size:0.8rem; font-weight:700;">🏛️ تصنيف السهم في الاقتصاد المصري:</div>
                        <div style="color:white; font-size:1.15rem; font-weight:800; margin-top:0.2rem;">{theme}</div>
                        {f'<div style="color:#90a4ae; font-size:0.78rem; margin-top:0.35rem;">{desc}</div>' if desc else ''}
                    </div>
                    <div style="text-align:center; background:rgba(255,255,255,0.06); padding:0.6rem 1.2rem; border-radius:10px; border:1px solid {h_color};">
                        <div style="color:{h_color}; font-size:1.6rem; font-weight:900;">{h_score}<span style="font-size:0.8rem; color:#7d8db1;">/100</span></div>
                        <div style="color:white; font-size:0.75rem; font-weight:700;">{h_verdict}</div>
                    </div>
                </div>
                """, unsafe_allow_html=True)

                f1, f2, f3, f4, f5, f6 = st.columns(6)
                f1.metric("P/E (مكرر الربحية)", f"{metrics.get('مكرر_الربحية_PE',0):.1f}" if metrics.get("مكرر_الربحية_PE") else "—")
                f2.metric("P/B (مضاعف الدفترية)", f"{metrics.get('السعر_إلى_القيمة_الدفترية_PB',0):.2f}" if metrics.get("السعر_إلى_القيمة_الدفترية_PB") else "—")
                f3.metric("عائد التوزيعات النقدية", f"{metrics.get('عائد_التوزيعات',0)*100:.1f}%" if metrics.get("عائد_التوزيعات") is not None else "—")
                f4.metric("العائد على الملكية ROE", f"{metrics.get('العائد_على_حقوق_الملكية_ROE',0)*100:.0f}%" if metrics.get("العائد_على_حقوق_الملكية_ROE") is not None else "—")
                f5.metric("هامش صافي الربح", f"{metrics.get('هامش_الربح',0)*100:.0f}%" if metrics.get("هامش_الربح") is not None else "—")
                f6.metric("القيمة السوقية", f"{metrics.get('القيمة_السوقية',0)/1e9:.1f}B ج.م" if metrics.get("القيمة_السوقية") else "—")

                st.caption("⚠️ الشفافية: مكرر الربحية من بيانات Yahoo اللحظية • التوزيعات وROE والجدارة من قاعدة مرجعية محلية مدققة يدوياً (قد لا تعكس آخر إفصاح) — قارن دائماً مع آخر إفصاح رسمي للشركة قبل القرار")

                st.markdown("---")

                col_fund_1, col_fund_2 = st.columns(2)
                with col_fund_1:
                    st.markdown("##### 🔍 نقاط القوة والتقييم المالي")
                    if health.get("reasons"):
                        for rsn in health["reasons"]:
                            st.markdown(f"• {rsn}")
                    else:
                        st.caption("جاري جمع بيانات التقييم...")

                with col_fund_2:
                    st.markdown("##### 🛡️ ملخص سلامة الاستثمار للمستثمر")
                    summary_f = calculate_valuation_summary(metrics, last_close)
                    for label, (lvl, text) in summary_f.items():
                        if lvl == "جيد": st.success(f"**{label}:** {text}")
                        elif lvl == "متوسط": st.info(f"**{label}:** {text}")
                        else: st.warning(f"**{label}:** {text}")

        with t_data:
            show = df_ind.tail(100).copy()
            show.index = pd.to_datetime(show.index).strftime("%Y-%m-%d")
            st.dataframe(show.round(2), use_container_width=True, height=380)
            csv2 = df_ind.to_csv().encode('utf-8-sig')
            st.download_button("⬇️ تحميل البيانات CSV", csv2, f"{symbol}_{period}.csv", "text/csv")

# ============================================================
# TAB 4: قائمة المتابعة والتنبيهات (بدون تتبع محفظة شخصية)
# ============================================================
with tab_watch:
    st.markdown("""
    <div style="background:linear-gradient(135deg, #0d1624 0%, #101d32 100%); border:1px solid #1f2d45; border-radius:14px; padding:1rem 1.4rem; margin-bottom:1rem; display:flex; align-items:center; gap:1rem;">
        <div style="font-size:2rem;">⭐</div>
        <div>
            <div style="color:white; font-size:1.15rem; font-weight:800;">قائمة المتابعة السريعة والتنبيهات السعرية</div>
            <div style="color:#7d8db1; font-size:0.82rem; margin-top:0.2rem;">
                🔒 خصوصية تامة — لا يتم تسجيل أي بيانات محفظة أو صفقات شخصية. فقط متابعة أسعار وتنبيهات.
            </div>
        </div>
    </div>
    """, unsafe_allow_html=True)

    # ===== مراقبة الصفقات النشطة (لحظية) =====
    trade_ideas_panel()

    st.markdown("---")

    wcol1, wcol2 = st.columns([1.3, 1])

    with wcol1:
        watch_panel()

        st.markdown("---")
        st.markdown("#### ➕ إضافة سهم للمتابعة")
        add_sym = st.selectbox("اختر سهم لإضافته", options=[s for s in all_symbols_list() if s not in st.session_state.watchlist],
                               format_func=lambda s: f"{s.replace('.CA','')} — {cname(s)[:30]}", key="add_watch_sym")
        if st.button("➕ أضف للمتابعة", type="primary", use_container_width=True, key="btn_add_watch"):
            st.session_state.watchlist.append(add_sym)
            USER_STORE["watchlist"] = st.session_state.watchlist
            store.save_store(USER_STORE)
            st.success(f"تمت إضافة {add_sym.replace('.CA','')} ✓")
            st.rerun()

    with wcol2:
        st.markdown("#### 🔔 التنبيهات السعرية الذكية")
        st.caption("حدد مستوى سعري وستظهر لك إشارة تنبيه فور وصول السهم إليه")

        al1, al2, al3 = st.columns(3)
        with al1:
            alert_sym = st.selectbox("السهم", options=all_symbols_list(),
                                     format_func=lambda s: s.replace('.CA',''), key="alert_sym")
        with al2:
            alert_above = st.number_input("⬆️ يصعد فوق", 0.0, step=0.01, key="alert_ab", format="%.2f")
        with al3:
            alert_below = st.number_input("⬇️ ينزل تحت", 0.0, step=0.01, key="alert_bl", format="%.2f")

        if st.button("🔔 حفظ التنبيه", type="primary", key="alert_save", use_container_width=True):
            store.set_alert(USER_STORE, alert_sym,
                            above=alert_above if alert_above > 0 else None,
                            below=alert_below if alert_below > 0 else None)
            st.success(f"تنبيه على {alert_sym.replace('.CA','')} تم حفظه ✓")

        st.markdown("##### حالة التنبيهات المفعّلة:")
        if USER_STORE["alerts"]:
            alert_bulk = cached_bulk(tuple(USER_STORE["alerts"].keys()), "5d") or {}
            for asym, a in list(USER_STORE["alerts"].items()):
                acol1, acol2 = st.columns([5, 1])
                aprice_series = alert_bulk.get(asym)
                aprice = float(aprice_series["Close"].iloc[-1]) if aprice_series is not None and len(aprice_series) else None
                parts = []
                triggered = False
                if aprice:
                    if a.get("above"):
                        if aprice >= a["above"]:
                            parts.append(f"🚨 وصل فوق {a['above']:,.2f} (الحالي {aprice:,.2f})")
                            triggered = True
                        else:
                            parts.append(f"⏳ ينتظر {a['above']:,.2f} (الحالي {aprice:,.2f})")
                    if a.get("below"):
                        if aprice <= a["below"]:
                            parts.append(f"🚨 نزل تحت {a['below']:,.2f} (الحالي {aprice:,.2f})")
                            triggered = True
                        else:
                            parts.append(f"⏳ ينتظر {a['below']:,.2f}")
                else:
                    parts.append("⏳ لا بيانات متاحة")
                with acol1:
                    if triggered:
                        st.error(f"**{asym.replace('.CA','')}** — {' • '.join(parts)}")
                    else:
                        st.caption(f"**{asym.replace('.CA','')}** — {' • '.join(parts)}")
                if acol2.button("🗑️", key=f"da_{asym}", help="حذف التنبيه"):
                    store.remove_alert(USER_STORE, asym)
                    st.rerun()
        else:
            st.info("لا توجد تنبيهات مضافة. أضف تنبيهاً من الأعلى.")



# ============================================================
# TAB 5: أدوات متقدمة
# ============================================================
with tab_tools:
    st.subheader("🧪 أدوات متقدمة")
    tool_tab1, tool_tab2, tool_tab3 = st.tabs(["🎯 فاحص نماذج السوينغ", "⚖️ مقارنة أسهم", "🧪 اختبار الاستراتيجية"])

    with tool_tab1:
        st.caption("فاحص نماذج التداول السوينغ للبورصة المصرية: ارتداد تشبع بيعي • اختراق سيولة • تصحيح صاعد")
        st1, st2 = st.columns(2)
        with st1:
            scalp_universe = st.selectbox("النطاق", ["EGX30", "EGX70", "أكبر 100"], index=0, key="sc_uni")
        with st2:
            scalp_filter = st.selectbox("الفلتر الفني", ["الكل", "ارتداد من قاع (تشبع بيعي)", "اختراق سيولة وزخم", "تصحيح في مسار صاعد", "أسهم السيولة العالية"], index=0, key="sc_filt")

        if scalp_universe == "EGX30":
            scalp_syms = symbols_by_mcap(30)
        elif scalp_universe == "EGX70":
            scalp_syms = symbols_by_mcap(70)
        else:
            scalp_syms = symbols_by_mcap(100)

        if st.button("🚀 افحص نماذج السوينغ", type="primary", use_container_width=True, key="run_scalp"):
            with st.spinner(f"فحص {len(scalp_syms)} سهم بنماذج السوينغ..."):
                bulk_s = cached_bulk(tuple(scalp_syms), "3mo")
                rows = []
                for sym, sdf in (bulk_s or {}).items():
                    if sdf is None or sdf.empty or len(sdf) < 30:
                        continue
                    sdf_ind = add_indicators(sdf)
                    sig = get_last_signals(sdf_ind)
                    swing_sig = generate_signal(sig, sdf_ind)
                    targets = calculate_price_targets(sig, sdf_ind)
                    t_sum = targets.get("summary", {})
                    last = float(sdf["Close"].iloc[-1])
                    prev = float(sdf["Close"].iloc[-2]) if len(sdf) > 1 else last
                    ch = (last - prev) / prev * 100 if prev else 0
                    rows.append({
                        "الرمز": sym, "الشركة": get_company_name(sym)[:22],
                        "السعر": round(last, 2), "التغير%": round(ch, 2),
                        "النموذج": swing_sig.get("setup", "تداول عرضي"),
                        "الإشارة": swing_sig["action"],
                        "العائد/المخاطرة": t_sum.get("risk_reward_str", "1:1.5"),
                        "هدف1": t_sum.get("T1", round(last * 1.06, 2)),
                        "وقف خسارة": t_sum.get("stop_loss", round(last * 0.95, 2)),
                        "السيولة": sig.get("Liquidity_Status", "سيولة مقبولة"),
                        "RSI": round(sig.get("RSI", 0), 1),
                        "ثقة%": int(swing_sig["confidence"] * 100),
                        "_s": swing_sig["score"],
                    })
                if rows:
                    df_scalp = pd.DataFrame(rows).sort_values("_s", ascending=False)
                    if scalp_filter == "ارتداد من قاع (تشبع بيعي)":
                        df_scalp = df_scalp[df_scalp["النموذج"].str.contains("ارتداد|تشبع", na=False)]
                    elif scalp_filter == "اختراق سيولة وزخم":
                        df_scalp = df_scalp[df_scalp["النموذج"].str.contains("اختراق", na=False)]
                    elif scalp_filter == "تصحيح في مسار صاعد":
                        df_scalp = df_scalp[df_scalp["النموذج"].str.contains("تصحيح|صاعد", na=False)]
                    elif scalp_filter == "أسهم السيولة العالية":
                        df_scalp = df_scalp[df_scalp["السيولة"].str.contains("ممتازة|جيدة", na=False)]
                    st.session_state["scalp_df"] = df_scalp

        if "scalp_df" in st.session_state and not st.session_state["scalp_df"].empty:
            df_scalp = st.session_state["scalp_df"]
            st.dataframe(df_scalp[["الرمز","الشركة","السعر","التغير%","النموذج","الإشارة","العائد/المخاطرة","هدف1","وقف خسارة","السيولة","RSI","ثقة%"]],
                         use_container_width=True, hide_index=True, height=380,
                         column_config={
                             "التغير%": st.column_config.NumberColumn(format="%.2f%%"),
                             "السعر": st.column_config.NumberColumn(format="%.2f"),
                             "هدف1": st.column_config.NumberColumn(format="%.2f"),
                             "وقف خسارة": st.column_config.NumberColumn(format="%.2f"),
                             "RSI": st.column_config.ProgressColumn(min_value=0, max_value=100, format="%.0f"),
                             "ثقة%": st.column_config.ProgressColumn(min_value=0, max_value=100),
                         })
            pick_s = st.selectbox("افتح تحليل", options=df_scalp["الرمز"].tolist(),
                                  format_func=lambda s: f"{s} — {get_company_name(s)}", key="pick_scalp")
            if st.button("➡️ افتح التحليل المفصل", key="open_scalp", use_container_width=True):
                st.session_state["selected_symbol"] = pick_s
                st.rerun()
        else:
            st.info("اضغط زر فحص نماذج السوينغ لعرض أفضل الترتيبات الفنية في السوق المصري")

    with tool_tab2:
        cmp_defaults = [s for s in ["COMI.CA", "TMGH.CA", "SWDY.CA"] if s in symbol_registry()]
        picks = st.multiselect("اختر أسهم للمقارنة (حتى 4)",
                               options=all_symbols_list(),
                               format_func=lambda s: f"{s.replace('.CA','')} — {cname(s)}",
                               default=cmp_defaults,
                               max_selections=4, key="cmp_picks")
        if len(picks) >= 2:
            bulk_c = cached_bulk(tuple(picks), period)
            if bulk_c:
                figc = go.Figure()
                for sym in picks:
                    dfc = bulk_c.get(sym)
                    if dfc is None or dfc.empty:
                        continue
                    norm = dfc["Close"] / dfc["Close"].iloc[0] * 100
                    figc.add_trace(go.Scatter(x=short_dates(dfc.index), y=norm, name=sym.replace(".CA",""), mode="lines"))
                figc.update_layout(height=420, template="plotly_dark", title="الأداء النسبي (البداية = 100)",
                                   hovermode="x unified")
                st.plotly_chart(figc, use_container_width=True)
        else:
            st.info("اختر سهمين على الأقل")

    with tool_tab3:
        st.caption("اختبر استراتيجية المنصة على التاريخ — هل توصياتها تنجح فعلاً؟")
        bt_hold = st.slider("مدة الاحتفاظ (أيام)", 3, 20, 5, 1)
        bt_threshold = st.slider("قوة الإشارة", 2, 6, 4, 1)
        if st.button("🧪 شغّل الاختبار على السهم الحالي", type="primary", use_container_width=True):
            with st.spinner("اختبار تاريخي..."):
                df_bt = cached_single(symbol, "2y", "1d")
                res = backtest_signals(df_bt, hold_days=bt_hold, threshold=bt_threshold)
                if "error" in res:
                    st.error(res["error"])
                elif res["total"] == 0:
                    st.warning("لا توجد إشارات كافية في هذه الفترة")
                else:
                    c1, c2, c3, c4 = st.columns(4)
                    c1.metric("الصفقات", res["total"])
                    c2.metric("نسبة النجاح", f"{res['win_rate']:.1f}%", delta=f"{res['wins']} رابحة")
                    c3.metric("متوسط العائد", f"{res['avg_return']:+.2f}%")
                    c4.metric("أفضل/أسوأ", f"{res['best']:+.1f}% / {res['worst']:+.1f}%")
                    if res["win_rate"] >= 58 and res["avg_return"] > 0:
                        st.success(f"✅ الاستراتيجية ناجحة على {symbol}")
                    elif res["win_rate"] >= 52:
                        st.info("⚠️ متوسطة — تحتاج إدارة مخاطر صارمة")
                    else:
                        st.warning("🔴 ضعيفة على هذا السهم — لا تعتمد عليها وحدها")
                    if res.get("trades"):
                        trd = pd.DataFrame(res["trades"])
                        fig_bt = go.Figure()
                        fig_bt.add_trace(go.Histogram(x=trd["return"], nbinsx=20, marker_color="#2962ff", opacity=0.7))
                        fig_bt.add_vline(x=0, line_dash="dash", line_color="#ff3d57")
                        fig_bt.update_layout(height=280, template="plotly_dark", title="توزيع العوائد %")
                        st.plotly_chart(fig_bt, use_container_width=True)

    # ===== لوحة الصناديق المصرية =====
    with st.expander("🏦 الصناديق المصرية (بلتون وأمثالها) — الشرح الكامل", expanded=False):
        st.markdown("""
#### لماذا لا تجد صناديق بلتون داخل شاشة الأسعار؟

**صناديق الاستثمار المصرية (صناديق بلتون، أزيموت، سي كابيتال، صناديق البنوك...) ليست أسهماً تُتداول في البورصة.**
هي صناديق "اكتتاب واسترداد": تشتريها وتبيعها مباشرة عبر شركة إدارة الصندوق أو المنصة/البنك، بسعر **قيمة الأصول الصافية (NAV)**
الذي يُعلن يومياً — لذلك لا تظهر على شاشات التداول أصلاً (بيانات TradingView للبورصة المصرية تعرض الأسهم المدرجة فقط، لا الصناديق).

**كيف تتابع صندوقك إذن؟**
- سعر الوحدة (NAV) اليومي يُنشر في موقع **الهيئة العامة للرقابة المالية (FRA)** وموقع شركة إدارة الصندوق نفسها
- الشراء/البيع من خلال مدير الصندوق (مثل بلتون لصناديقها) أو المنصات المرخصة (ثاندر، بنوك...)
- عمولاتها أقل من أسهم البورصة عادة، لكن سيولتها أبطأ (التسوية قد تستغرق أياماً)

**البديل المتاح داخل هذه المنصة** — تداول أسهم **شركات إدارة الأصول نفسها** المدرجة في البورصة:
""")
        fund_house_syms = [s for s in ["BTFH.CA", "HRHO.CA", "CCAP.CA", "EFIH.CA"] if s in symbol_registry()]
        if fund_house_syms:
            fh1, fh2 = st.columns([1.2, 1])
            with fh2:
                st.caption("اضغط لتحليل السهم في خبير البورصة:")
                for s in fund_house_syms:
                    row_tv = tvd.one(s)
                    price_txt = f"— {row_tv['close']:,.2f} ({row_tv['change_pct']:+.2f}%)" if row_tv else ""
                    if st.button(f"📊 {s.replace('.CA','')} — {cname(s)[:30]} {price_txt}", key=f"fh_{s}", use_container_width=True):
                        st.session_state["selected_symbol"] = s
                        st.rerun()
            with fh1:
                st.markdown("""
| السهم | ماذا يمثل |
|---|---|
| **BTFH** | بلتون القابضة — أكبر مدير أصول مستقل في مصر |
| **HRHO** | إي إف جي هيرميس — استثمار مصرفي وإدارة أصول |
| **CCAP** | القلعة للاستثمار — صناديق خاصة وأصول بديلة |
| **EFIH** | إي فاينانس — بنية تحتية للمدفوعات والحكومة الرقمية |

ملاحظة مهنية: أسهم هذه الشركات تتأثر بأداء قطاع إدارة الأصول ككل، لكنها **ليست** بديلاً مباشراً لأداء الصناديق نفسها.
                """)
        st.caption("🔒 لا تقدم هذه المنصة توصيات بشأن صناديق الاكتتاب — راجع نشرة الصندوق وموقع الهيئة العامة للرقابة المالية قبل أي استثمار")

# ============================================================
# Footer
# ============================================================
st.markdown("---")
st.caption("⚠️ هذه المنصة لأغراض التحليل والتعليم — ليست نصيحة استثمارية. الأسعار والمؤشرات من TradingView (متأخرة ~15 دقيقة وفق قواعد البورصة المصرية)، والتحليل الفني على بيانات الإغلاق. لا تخاطر بأكثر من 2% في صفقة واحدة.")
