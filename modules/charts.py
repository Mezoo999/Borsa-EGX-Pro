"""محرك الرسوم الحية — ECharts المتحركة + Lightweight Charts (محرك TradingView المفتوح).

الاثنتان تُضمَّنان مباشرة عبر CDN بدون أي تبعيات بايثون إضافية، بنفس نمط ويدجت TradingView.
- echarts_sectors: أعمدة القطاعات بحركة انسيابية (تنطلق مرتدة عند كل تحديث)
- lightweight_candles: شموع بمحرك TradingView المفتوح — كروس هير لحظي وحجم ومتوسطات، إحساس تيرمنال كامل
"""
import json

import pandas as pd
import streamlit.components.v1 as components

def _render(html: str, height: int):
    """عرض HTML تفاعلي (شموع/أعمدة) داخل Streamlit.

    ملاحظة مهمة: نستخدم components.html (iframe معزول) عن قصد — البديل الجديد
    st.html يدرج الكود في الصفحة الرئيسية بدون عزل، ما يمنع تحميل مكتبات CDN
    (Lightweight Charts / ECharts) بترتيب صحيح ويفسد إعدادات ويدجت TradingView.
    الـ iframe المعزول هو الطريقة الصحيحة والمضمونة لعرض سكربتات طرف ثالث.
    """
    components.html(html, height=height, scrolling=False)


DARK_BG = "#0d1119"
GRID_COLOR = "rgba(31,45,69,0.45)"
TEXT_COLOR = "#cfd8dc"


def echarts_sectors(rows: list, height: int = 420):
    """rows: [(اسم القطاع, متوسط التغير%, عدد الأسهم)] — أعمدة أفقية متحركة."""
    if not rows:
        return
    ordered = rows[::-1]  # ECharts يرسم من الأسفل للأعلى
    names = [f"{s} ({n} سهم)" for s, _, n in ordered]
    data = []
    for s, ch, n in ordered:
        color = "#00c853" if ch > 0 else ("#ff5c76" if ch < 0 else "#546e7a")
        data.append({"value": round(ch, 2), "itemStyle": {"color": color}})
    options = json.dumps({
        "backgroundColor": "transparent",
        "tooltip": {"trigger": "axis", "axisPointer": {"type": "shadow"},
                    "backgroundColor": "#10141d", "borderColor": "#1f2d45",
                    "textStyle": {"color": TEXT_COLOR}},
        "grid": {"left": 10, "right": 70, "top": 10, "bottom": 10, "containLabel": True},
        "xAxis": {"type": "value", "axisLabel": {"color": "#7d8db1", "formatter": "{value}%"},
                  "splitLine": {"lineStyle": {"color": GRID_COLOR}}},
        "yAxis": {"type": "category", "data": names,
                  "axisLabel": {"color": TEXT_COLOR, "fontSize": 12},
                  "axisLine": {"lineStyle": {"color": GRID_COLOR}}},
        "series": [{
            "type": "bar",
            "data": data,
            "barMaxWidth": 26,
            "label": {"show": True, "position": "right",
                      "color": TEXT_COLOR, "formatter": "{c}%"},
            "animationDuration": 1600,
            "animationEasing": "elasticOut",
            "animationDelay": 150,
        }],
    }, ensure_ascii=False)
    html = f"""
    <div id="sec_chart" style="width:100%;height:{height}px;"></div>
    <script src="https://cdn.jsdelivr.net/npm/echarts@5.5.0/dist/echarts.min.js"></script>
    <script>
      var chart = echarts.init(document.getElementById('sec_chart'), null, {{renderer: 'canvas'}});
      chart.setOption({options});
      window.addEventListener('resize', function() {{ chart.resize(); }});
    </script>
    """
    components.html(html, height=height + 10, scrolling=False)


def lightweight_candles(df: pd.DataFrame, height: int = 560, title: str = ""):
    """شموع احترافية بمحرك TradingView المفتوح: شموع + حجم + SMA20/50 + كروس هير لحظي."""
    if df is None or df.empty or len(df) < 5:
        return
    d = df.tail(180).copy()
    candles, volumes, sma20, sma50 = [], [], [], []
    sma20_s = d["Close"].rolling(20).mean()
    sma50_s = d["Close"].rolling(50).mean()
    for i, (idx, r) in enumerate(d.iterrows()):
        t = str(idx)[:10]
        o, h, l, c = float(r["Open"]), float(r["High"]), float(r["Low"]), float(r["Close"])
        candles.append({"time": t, "open": round(o, 2), "high": round(h, 2),
                        "low": round(l, 2), "close": round(c, 2)})
        vol_color = "rgba(0,200,83,0.45)" if c >= o else "rgba(255,61,87,0.45)"
        volumes.append({"time": t, "value": float(r["Volume"]), "color": vol_color})
        v20, v50 = sma20_s.iloc[i], sma50_s.iloc[i]
        if pd.notna(v20):
            sma20.append({"time": t, "value": round(float(v20), 2)})
        if pd.notna(v50):
            sma50.append({"time": t, "value": round(float(v50), 2)})
    j_candles = json.dumps(candles)
    j_volumes = json.dumps(volumes)
    j_sma20 = json.dumps(sma20)
    j_sma50 = json.dumps(sma50)
    html = f"""
    <div id="lw_chart" style="width:100%;height:{height}px;"></div>
    <script src="https://unpkg.com/lightweight-charts@4.1.3/dist/lightweight-charts.standalone.production.js"></script>
    <script>
      var el = document.getElementById('lw_chart');
      var chart = LightweightCharts.createChart(el, {{
        width: el.clientWidth,
        height: {height},
        layout: {{ background: {{ type: 'solid', color: '{DARK_BG}' }}, textColor: '{TEXT_COLOR}' }},
        grid: {{ vertLines: {{ color: '{GRID_COLOR}' }}, horzLines: {{ color: '{GRID_COLOR}' }} }},
        crosshair: {{ mode: 0,
          vertLine: {{ color: '#2962ff', labelBackgroundColor: '#2962ff' }},
          horzLine: {{ color: '#2962ff', labelBackgroundColor: '#2962ff' }} }},
        rightPriceScale: {{ borderColor: '#1f2d45' }},
        timeScale: {{ borderColor: '#1f2d45', timeVisible: false }},
      }});
      var candles = chart.addCandlestickSeries({{
        upColor: '#00c853', downColor: '#ff5c76', borderVisible: false,
        wickUpColor: '#00c853', wickDownColor: '#ff5c76',
        priceLineColor: '#2962ff',
      }});
      candles.setData(__CANDLES__);
      var vol = chart.addHistogramSeries({{ priceFormat: {{ type: 'volume' }}, priceScaleId: '' }});
      vol.priceScale().applyOptions({{ scaleMargins: {{ top: 0.82, bottom: 0 }} }});
      vol.setData(__VOLUMES__);
      var s20 = chart.addLineSeries({{ color: '#ffab00', lineWidth: 1, priceLineVisible: false, lastValueVisible: false }});
      s20.setData(__SMA20__);
      var s50 = chart.addLineSeries({{ color: '#29b6f6', lineWidth: 1, priceLineVisible: false, lastValueVisible: false }});
      s50.setData(__SMA50__);
      chart.timeScale().fitContent();
      window.addEventListener('resize', function() {{
        chart.applyOptions({{ width: el.clientWidth }});
      }});
    </script>
    """
    html = (html.replace("__CANDLES__", j_candles)
                .replace("__VOLUMES__", j_volumes)
                .replace("__SMA20__", j_sma20)
                .replace("__SMA50__", j_sma50))
    components.html(html, height=height + 10, scrolling=False)
