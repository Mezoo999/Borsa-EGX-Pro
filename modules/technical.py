"""وحدة التحليل الفني (Technical Analysis) باستخدام مكتبة ta."""
import warnings

import numpy as np
import pandas as pd
import ta

# تحذيرات FutureWarning من مكتبة ta الداخلية (تنفيذ PSAR) — ليست من كود المشروع
warnings.filterwarnings("ignore", category=FutureWarning, module="ta")


def add_indicators(df: pd.DataFrame) -> pd.DataFrame:
    """
    إضافة المؤشرات الفنية للبيانات:
    - المتوسطات المتحركة (SMA/EMA)
    - مؤشر القوة النسبية RSI
    - مؤشر MACD
    - نطاقات بولينجر Bollinger Bands
    - الحجم المتحرك
    - متوسط الاتجاه ATR
    """
    df = df.copy()
    close = df["Close"]
    high = df["High"]
    low = df["Low"]
    volume = df["Volume"]

    # لضمان التوافق مع pandas 3 / ta
    close_s = close.astype(float)

    # المتوسطات المتحركة (للمستثمر الأسبوعي)
    df["SMA20"] = close.rolling(20).mean()
    df["SMA50"] = close.rolling(50).mean()
    df["SMA200"] = close.rolling(200).mean()
    df["EMA12"] = close.ewm(span=12, adjust=False).mean()
    df["EMA26"] = close.ewm(span=26, adjust=False).mean()
    # متوسطات المضاربة السريعة
    df["EMA9"] = close.ewm(span=9, adjust=False).mean()
    df["EMA21"] = close.ewm(span=21, adjust=False).mean()

    # RSI (14) و RSI سريع (9) للمضاربة
    df["RSI"] = ta.momentum.RSIIndicator(close_s, window=14).rsi()
    try:
        df["RSI_9"] = ta.momentum.RSIIndicator(close_s, window=9).rsi()
    except:
        df["RSI_9"] = df["RSI"]

    # Stochastic (للمضاربة)
    try:
        stoch = ta.momentum.StochasticOscillator(high.astype(float), low.astype(float), close_s, window=14, smooth_window=3)
        df["Stoch_K"] = stoch.stoch()
        df["Stoch_D"] = stoch.stoch_signal()
    except:
        df["Stoch_K"] = np.nan
        df["Stoch_D"] = np.nan

    # StochRSI (عزم دقيق لتوقيت الدخول والخروج)
    try:
        srsi = ta.momentum.StochRSIIndicator(close_s, window=14, smooth1=3, smooth2=3)
        df["StochRSI_K"] = srsi.stochrsi_k() * 100
        df["StochRSI_D"] = srsi.stochrsi_d() * 100
    except:
        df["StochRSI_K"] = np.nan
        df["StochRSI_D"] = np.nan

    # MACD
    macd = ta.trend.MACD(close_s)
    df["MACD"] = macd.macd()
    df["MACD_Signal"] = macd.macd_signal()
    df["MACD_Hist"] = macd.macd_diff()

    # Bollinger Bands (20, 2)
    bb = ta.volatility.BollingerBands(close_s, window=20, window_dev=2)
    df["BB_Upper"] = bb.bollinger_hband()
    df["BB_Middle"] = bb.bollinger_mavg()
    df["BB_Lower"] = bb.bollinger_lband()
    df["BB_Width"] = bb.bollinger_wband()

    # ATR
    df["ATR"] = ta.volatility.AverageTrueRange(
        high.astype(float), low.astype(float), close_s, window=14
    ).average_true_range()

    # VWMA (Volume-Weighted Moving Average 20) - متوسط السعر المرجح بالسيولة المناسب للبيانات اليومية
    try:
        vol_price = close_s * volume
        df["VWMA20"] = vol_price.rolling(20).sum() / volume.rolling(20).sum().replace(0, np.nan)
        df["VWMA20"] = df["VWMA20"].fillna(df["SMA20"])
    except Exception:
        df["VWMA20"] = df["SMA20"]
    df["VWAP"] = df["VWMA20"]  # للمحافظة على التوافق البرمجي

    # حجم متحرك (متوسط 20)
    df["Vol_MA20"] = volume.rolling(20).mean()
    df["Vol_Ratio"] = volume / df["Vol_MA20"].replace(0, np.nan)

    # قيمة التداول بالجنيه (Turnover = السعر × الحجم)
    df["Turnover"] = close_s * volume
    df["Turnover_MA20"] = df["Turnover"].rolling(20).mean()

    # ADX - قوة الاتجاه (احترافي)
    try:
        adx = ta.trend.ADXIndicator(high.astype(float), low.astype(float), close_s, window=14)
        df["ADX"] = adx.adx()
        df["ADX_pos"] = adx.adx_pos()
        df["ADX_neg"] = adx.adx_neg()
    except:
        df["ADX"] = np.nan
        df["ADX_pos"] = np.nan
        df["ADX_neg"] = np.nan

    # CCI
    try:
        df["CCI"] = ta.trend.CCIIndicator(high.astype(float), low.astype(float), close_s, window=20).cci()
    except:
        df["CCI"] = np.nan

    # Williams %R
    try:
        df["WR"] = ta.momentum.WilliamsRIndicator(high.astype(float), low.astype(float), close_s, lbp=14).williams_r()
    except:
        df["WR"] = np.nan

    # OBV
    try:
        df["OBV"] = ta.volume.OnBalanceVolumeIndicator(close_s, volume).on_balance_volume()
        df["OBV_MA"] = df["OBV"].rolling(20).mean()
    except:
        df["OBV"] = np.nan
        df["OBV_MA"] = np.nan

    # MFI (سيولة)
    try:
        df["MFI"] = ta.volume.MFIIndicator(high.astype(float), low.astype(float), close_s, volume, window=14).money_flow_index()
    except:
        df["MFI"] = np.nan

    # ROC معدل التغير
    try:
        df["ROC"] = ta.momentum.ROCIndicator(close_s, window=12).roc()
    except:
        df["ROC"] = np.nan

    # Parabolic SAR (اتجاه + وقف ديناميكي)
    try:
        psar = ta.trend.PSARIndicator(high.astype(float), low.astype(float), close_s)
        df["PSAR"] = psar.psar()
        df["PSAR_up"] = psar.psar_up()
        df["PSAR_down"] = psar.psar_down()
    except:
        df["PSAR"] = np.nan

    # Supertrend (من أقوى مؤشرات الاتجاه)
    try:
        st_atr = ta.volatility.AverageTrueRange(high.astype(float), low.astype(float), close_s, window=10).average_true_range()
        hl2 = (high.astype(float) + low.astype(float)) / 2
        fband_ub = (hl2 + 3 * st_atr).ffill()
        fband_lb = (hl2 - 3 * st_atr).ffill()
        supertrend = pd.Series(index=df.index, dtype=float)
        direction = pd.Series(index=df.index, dtype=float)
        st, d = fband_lb.iloc[0], 1
        for i in range(len(df)):
            c = close_s.iloc[i]
            if d == 1:
                st = max(fband_lb.iloc[i], st)
                if c < st: st, d = fband_ub.iloc[i], -1
            else:
                st = min(fband_ub.iloc[i], st)
                if c > st: st, d = fband_lb.iloc[i], 1
            supertrend.iloc[i], direction.iloc[i] = st, d
        df["Supertrend"] = supertrend
        df["ST_dir"] = direction  # 1 = صاعد، -1 = هابط
    except:
        df["Supertrend"] = np.nan
        df["ST_dir"] = 0

    return df


def detect_candlestick_patterns(df: pd.DataFrame) -> dict:
    """كشف نماذج الشموع اليابانية الرئيسية (Hammer, Engulfing, Doji) في آخر شمعتين."""
    if df.empty or len(df) < 2:
        return {"pattern": None, "type": "neutral", "desc": ""}

    last = df.iloc[-1]
    prev = df.iloc[-2]

    o1, c1, h1, l1 = float(prev["Open"]), float(prev["Close"]), float(prev["High"]), float(prev["Low"])
    o2, c2, h2, l2 = float(last["Open"]), float(last["Close"]), float(last["High"]), float(last["Low"])

    body = abs(c2 - o2)
    upper_shadow = h2 - max(o2, c2)
    lower_shadow = min(o2, c2) - l2
    total_range = h2 - l2 if h2 > l2 else 0.001

    # Bullish Hammer (مطرقة إيجابية بعد هبوط)
    if lower_shadow >= 1.8 * body and upper_shadow <= 0.25 * total_range and c1 <= o1:
        return {"pattern": "Hammer (مطرقة ارتدادية)", "type": "bullish", "desc": "إشارة ارتداد إيجابية من قاع"}

    # Bullish Engulfing (ابتلاع شرائي)
    if c1 < o1 and c2 > o2 and c2 >= o1 and o2 <= c1:
        return {"pattern": "Bullish Engulfing (ابتلاع شرائي)", "type": "bullish", "desc": "سيولة شرائية ابتلعت الشمعة البيعية السابقة بالكامل"}

    # Bearish Engulfing (ابتلاع بيعي)
    if c1 > o1 and c2 < o2 and c2 <= o1 and o2 >= c1:
        return {"pattern": "Bearish Engulfing (ابتلاع بيعي)", "type": "bearish", "desc": "ضغط بيعي ابتلع الشمعة الصاعدة السابقة"}

    # Doji (حيرة وتوازن)
    if body <= 0.12 * total_range:
        return {"pattern": "Doji (شمعة حيرة)", "type": "neutral", "desc": "تردد وتوازن بين المشتري والبائع بانتظار تأكيد"}

    return {"pattern": None, "type": "neutral", "desc": ""}


def detect_divergence(df: pd.DataFrame) -> dict:
    """كشف الدايفرجنس (التباعد) بين السعر ومؤشر RSI خلال آخر 25 جلسة."""
    if df.empty or len(df) < 25 or "RSI" not in df.columns:
        return {"divergence": None, "type": "none", "desc": ""}

    recent = df.tail(25)
    p_low_recent = float(recent.iloc[-8:]["Low"].min())
    p_low_prev = float(recent.iloc[:15]["Low"].min())
    r_low_recent = float(recent.iloc[-8:]["RSI"].min())
    r_low_prev = float(recent.iloc[:15]["RSI"].min())

    # Bullish Divergence (انفراج إيجابي)
    if p_low_recent < p_low_prev and r_low_recent > r_low_prev and r_low_recent < 48:
        return {
            "divergence": "Bullish Divergence (انفراج إيجابي)",
            "type": "bullish",
            "desc": "السعر يسجل قاعاً أدنى بينما عزم الشراء RSI يسجل قاعاً أعلى (تجهيز لانعكاس صاعد)"
        }

    p_hi_recent = float(recent.iloc[-8:]["High"].max())
    p_hi_prev = float(recent.iloc[:15]["High"].max())
    r_hi_recent = float(recent.iloc[-8:]["RSI"].max())
    r_hi_prev = float(recent.iloc[:15]["RSI"].max())

    # Bearish Divergence (انفراج سلبي)
    if p_hi_recent > p_hi_prev and r_hi_recent < r_hi_prev and r_hi_recent > 55:
        return {
            "divergence": "Bearish Divergence (انفراج سلبي)",
            "type": "bearish",
            "desc": "السعر يسجل قمة أعلى بينما عزم الصعود RSI يضعف (خطر جني أرباح وهبوط)"
        }

    return {"divergence": None, "type": "none", "desc": ""}


def get_last_signals(df: pd.DataFrame):
    """استخراج إشارات ومؤشرات آخر جلسة مع السيولة ونماذج الشموع والدايفرجنس."""
    if df.empty or len(df) < 30:
        return {}
    last = df.iloc[-1]
    prev = df.iloc[-2]

    # حساب قيمة التداول بالمليون جنيه
    turnover_val = float(last.get("Turnover", last["Close"] * last["Volume"]))
    turnover_m = turnover_val / 1e6
    turnover_ma20_val = float(last.get("Turnover_MA20", turnover_val))
    turnover_ma20_m = turnover_ma20_val / 1e6

    # تقييم سيولة السهم في البورصة المصرية
    if turnover_m >= 15:
        liquidity_status = "سيولة ممتازة (مؤسسية)"
    elif turnover_m >= 5:
        liquidity_status = "سيولة جيدة"
    elif turnover_m >= 2:
        liquidity_status = "سيولة متوسطة"
    else:
        liquidity_status = "سيولة ضعيفة ⚠️"

    candle_pat = detect_candlestick_patterns(df)
    div_info = detect_divergence(df)

    out = {
        "RSI": float(last["RSI"]) if "RSI" in df.columns else np.nan,
        "RSI_9": float(last["RSI_9"]) if "RSI_9" in df.columns else np.nan,
        "SMA20": float(last["SMA20"]),
        "SMA50": float(last["SMA50"]),
        "SMA200": float(last["SMA200"]),
        "EMA9": float(last["EMA9"]) if "EMA9" in df.columns else np.nan,
        "EMA21": float(last["EMA21"]) if "EMA21" in df.columns else np.nan,
        "Close": float(last["Close"]),
        "MACD": float(last["MACD"]),
        "MACD_Signal": float(last["MACD_Signal"]),
        "BB_Upper": float(last["BB_Upper"]),
        "BB_Lower": float(last["BB_Lower"]),
        "BB_Middle": float(last["BB_Middle"]) if "BB_Middle" in df.columns else np.nan,
        "ATR": float(last["ATR"]),
        "VWAP": float(last["VWAP"]) if "VWAP" in df.columns else np.nan,
        "VWMA20": float(last["VWMA20"]) if "VWMA20" in df.columns else np.nan,
        "Stoch_K": float(last["Stoch_K"]) if "Stoch_K" in df.columns else np.nan,
        "Stoch_D": float(last["Stoch_D"]) if "Stoch_D" in df.columns else np.nan,
        "StochRSI_K": float(last["StochRSI_K"]) if "StochRSI_K" in df.columns else np.nan,
        "StochRSI_D": float(last["StochRSI_D"]) if "StochRSI_D" in df.columns else np.nan,
        "Vol_Ratio": float(last["Vol_Ratio"]) if "Vol_Ratio" in df.columns else np.nan,
        "Turnover_M": round(turnover_m, 2),
        "Turnover_MA20_M": round(turnover_ma20_m, 2),
        "Liquidity_Status": liquidity_status,
        "Candle_Pattern": candle_pat.get("pattern"),
        "Candle_Type": candle_pat.get("type"),
        "Divergence": div_info.get("divergence"),
        "Divergence_Type": div_info.get("type"),
        "ADX": float(last["ADX"]) if "ADX" in df.columns else np.nan,
        "ADX_pos": float(last["ADX_pos"]) if "ADX_pos" in df.columns else np.nan,
        "ADX_neg": float(last["ADX_neg"]) if "ADX_neg" in df.columns else np.nan,
        "CCI": float(last["CCI"]) if "CCI" in df.columns else np.nan,
        "WR": float(last["WR"]) if "WR" in df.columns else np.nan,
        "OBV": float(last["OBV"]) if "OBV" in df.columns else np.nan,
        "OBV_MA": float(last["OBV_MA"]) if "OBV_MA" in df.columns else np.nan,
        "MFI": float(last["MFI"]) if "MFI" in df.columns else np.nan,
        "ROC": float(last["ROC"]) if "ROC" in df.columns else np.nan,
        "PSAR": float(last["PSAR"]) if "PSAR" in df.columns else np.nan,
        "Supertrend": float(last["Supertrend"]) if "Supertrend" in df.columns else np.nan,
        "ST_dir": float(last["ST_dir"]) if "ST_dir" in df.columns else 0,
        "pre_RSI": float(prev["RSI"]) if "RSI" in df.columns else np.nan,
        "pre_MACD": float(prev["MACD"]),
        "pre_MACD_Signal": float(prev["MACD_Signal"]),
        "Volume": float(last["Volume"]),
        "Vol_MA20": float(last["Vol_MA20"]),
        "High": float(last["High"]),
        "Low": float(last["Low"]),
        "Open": float(last["Open"]),
    }
    # تجاهل القيم غير المحددة
    out = {k: v for k, v in out.items() if not (isinstance(v, float) and np.isnan(v))}
    return out


def calculate_vwap_signals(df: pd.DataFrame) -> dict:
    """تحليل متوسط السعر الموزون بالسيولة (VWMA20) لبيانات البورصة المصرية."""
    if df.empty or "VWMA20" not in df.columns:
        return {}
    last = df.iloc[-1]
    close = float(last["Close"])
    vwma = float(last["VWMA20"])
    dist = (close - vwma) / vwma * 100 if vwma else 0
    above = close > vwma
    return {"vwap": vwma, "vwma": vwma, "close": close, "distance_pct": dist, "above_vwap": above}

