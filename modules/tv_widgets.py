"""ويدجت TradingView لحظية — أسعار البورصة المصرية الحقيقية المباشرة (مجاني 100%)

ملاحظة تقنية: كل ويدجت يستخدم البنية الرسمية الموثقة:
<div class="tradingview-widget-container" style="height:..px">
  <div class="tradingview-widget-container__widget" style="height:100%"></div>
  <script ...>
بدون هذه البنية + ارتفاع صريح يظهر الويدجت فارغاً أو صغيراً.
"""
import streamlit.components.v1 as components

TV_DARK_BG = "rgba(11,14,20,1)"


def tradingview_ticker_tape(symbols: list):
    """شريط أسعار متحرك لحظي من TradingView."""
    tv_syms = [f"EGX:{s.replace('.CA','')}" for s in symbols]
    syms_json = str([{"proName": s, "title": s.replace("EGX:", "")} for s in tv_syms]).replace("'", '"')
    return f"""
    <div class="tradingview-widget-container">
      <div class="tradingview-widget-container__widget"></div>
      <script type="text/javascript" src="https://s3.tradingview.com/external-embedding/embed-widget-ticker-tape.js" async>
      {{
        "symbols": {syms_json},
        "showSymbolLogo": true,
        "isTransparent": true,
        "displayMode": "adaptive",
        "locale": "ar_AE",
        "colorTheme": "dark"
      }}
      </script>
    </div>
    """


def tradingview_advanced_chart(tv_symbol: str, height: int = 680, interval: str = "D"):
    """رسم احترافي لحظي كامل الأدوات من TradingView.

    مهم: نستخدم height ثابت في إعداد الويدجت نفسه (وليس autosize) —
    وضع autosize ينكسر داخل iframe الخاص بـ Streamlit فينضغط الرسم لشريط صغير.
    """
    return f"""
    <div class="tradingview-widget-container" style="height:{height}px;width:100%;">
      <div class="tradingview-widget-container__widget" style="height:100%;width:100%;"></div>
      <script type="text/javascript" src="https://s3.tradingview.com/external-embedding/embed-widget-advanced-chart.js" async>
      {{
        "width": "100%",
        "height": {height},
        "symbol": "{tv_symbol}",
        "interval": "{interval}",
        "timezone": "Africa/Cairo",
        "theme": "dark",
        "style": "1",
        "locale": "ar_AE",
        "backgroundColor": "{TV_DARK_BG}",
        "gridColor": "rgba(31,45,69,0.5)",
        "hide_side_toolbar": false,
        "allow_symbol_change": true,
        "save_image": true,
        "details": false,
        "calendar": false,
        "withdateranges": true,
        "hide_volume": false,
        "support_host": "https://www.tradingview.com"
      }}
      </script>
    </div>
    """


def tradingview_symbol_info(tv_symbol: str, height: int = 210):
    """بطاقة معلومات لحظية (سعر/تغير/أعلى/أدنى) من TradingView."""
    return f"""
    <div class="tradingview-widget-container" style="height:{height}px;width:100%;">
      <div class="tradingview-widget-container__widget" style="height:100%;width:100%;"></div>
      <script type="text/javascript" src="https://s3.tradingview.com/external-embedding/embed-widget-symbol-info.js" async>
      {{
        "symbol": "{tv_symbol}",
        "width": "100%",
        "locale": "ar_AE",
        "colorTheme": "dark",
        "isTransparent": true
      }}
      </script>
    </div>
    """


def tradingview_market_overview(height: int = 460):
    """لوحة مؤشرات السوق EGX30/70/100 والأسهم الكبرى لحظياً."""
    symbols = [
        {"proName": "EGX:EGX30", "title": "EGX 30"},
        {"proName": "EGX:EGX70", "title": "EGX 70"},
        {"proName": "EGX:EGX100", "title": "EGX 100"},
        {"proName": "EGX:COMI", "title": "CIB"},
        {"proName": "EGX:TMGH", "title": "TMG Holding"},
        {"proName": "EGX:SWDY", "title": "Elsewedy Electric"},
        {"proName": "EGX:ETEL", "title": "Telecom Egypt"},
        {"proName": "EGX:HRHO", "title": "EFG Holding"},
        {"proName": "EGX:FWRY", "title": "Fawry"},
    ]
    syms_json = str(symbols).replace("'", '"')
    return f"""
    <div class="tradingview-widget-container" style="height:{height}px;width:100%;border-radius:12px;overflow:hidden;border:1px solid #1f2d45;">
      <div class="tradingview-widget-container__widget" style="height:100%;width:100%;"></div>
      <script type="text/javascript" src="https://s3.tradingview.com/external-embedding/embed-widget-market-overview.js" async>
      {{
        "showChart": true,
        "locale": "ar_AE",
        "width": "100%",
        "height": {height},
        "isTransparent": true,
        "showSymbolLogo": true,
        "colorTheme": "dark",
        "tabs": [
          {{
            "title": "مؤشرات وأسهم مصر",
            "symbols": {syms_json}
          }}
        ]
      }}
      </script>
    </div>
    """


def tradingview_screener_widget(height: int = 560):
    """فاحص أسهم مصر لحظي من TradingView."""
    return f"""
    <div class="tradingview-widget-container" style="height:{height}px;width:100%;border-radius:12px;overflow:hidden;border:1px solid #1f2d45;">
      <div class="tradingview-widget-container__widget" style="height:100%;width:100%;"></div>
      <script type="text/javascript" src="https://s3.tradingview.com/external-embedding/embed-widget-screener.js" async>
      {{
        "width": "100%",
        "height": {height},
        "defaultColumn": "overview",
        "defaultScreen": "most_capitalized",
        "market": "egypt",
        "showToolbar": true,
        "colorTheme": "dark",
        "locale": "ar_AE",
        "isTransparent": true
      }}
      </script>
    </div>
    """


def render_tv(component_html: str, height: int):
    """عرض ويدجت داخل Streamlit."""
    components.html(component_html, height=height, scrolling=False)
