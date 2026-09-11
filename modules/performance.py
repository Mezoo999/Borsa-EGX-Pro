"""وحدة حساب الأداء عبر الفترات - يومي/أسبوعي/شهري/سنوي/منذ الإنشاء"""
import pandas as pd
import yfinance as yf

def calculate_performance(symbol: str) -> dict:
    """
    حساب نسبة التغير عبر فترات متعددة لنفس السهم:
    يوم، أسبوع، شهر، 3 شهور، 6 شهور، سنة، منذ بداية السنة، منذ الإنشاء
    ترجع dict مع كل فترة ونسبة الربح
    """
    try:
        t = yf.Ticker(symbol)
        # نحتاج history max للحصول على أول سعر
        hist_max = t.history(period="max", auto_adjust=True)
        if hist_max is None or hist_max.empty:
            return {}
        hist_max = hist_max[["Close"]].dropna()
        current = float(hist_max["Close"].iloc[-1])
        last_date = hist_max.index[-1]

        def pct(days_ago):
            try:
                # ابحث عن سعر قبل days_ago يوم تداول (تقريبي عبر index)
                if len(hist_max) <= days_ago:
                    return None
                past = float(hist_max["Close"].iloc[-days_ago-1])
                return (current - past) / past * 100 if past else None
            except:
                return None

        # حساب عبر فترات تقريبية بأيام تداول
        perf = {}
        # يوم واحد (آخر يوم تداول)
        perf["يوم"] = pct(1)
        # أسبوع (5 أيام تداول)
        perf["أسبوع"] = pct(5)
        # شهر (21 يوم)
        perf["شهر"] = pct(21)
        # 3 شهور (63)
        perf["3 شهور"] = pct(63)
        # 6 شهور (126)
        perf["6 شهور"] = pct(126)
        # سنة (252)
        perf["سنة"] = pct(252)
        # منذ بداية السنة
        try:
            year_start = hist_max[hist_max.index.year == last_date.year].iloc[0]
            ys_price = float(year_start["Close"])
            perf["منذ بداية السنة"] = (current - ys_price) / ys_price * 100 if ys_price else None
        except:
            perf["منذ بداية السنة"] = None
        # منذ الإنشاء (أول سعر)
        try:
            first = float(hist_max["Close"].iloc[0])
            perf["منذ الإنشاء"] = (current - first) / first * 100 if first else None
            perf["سعر البداية"] = first
            perf["تاريخ البداية"] = hist_max.index[0].strftime("%Y-%m-%d")
        except:
            perf["منذ الإنشاء"] = None

        # تنظيف None
        for k in list(perf.keys()):
            if perf[k] is not None:
                try:
                    perf[k] = round(float(perf[k]), 2)
                except:
                    pass
        perf["السعر الحالي"] = round(current,2)
        perf["آخر تحديث"] = last_date.strftime("%Y-%m-%d")
        return perf
    except Exception as e:
        return {"error": str(e)[:100]}

def get_performance_table(symbol: str):
    """جدول أداء جاهز للعرض — يرجع (DataFrame, dict) دائماً حتى عند الفشل"""
    perf = calculate_performance(symbol)
    if not perf or "error" in perf:
        return pd.DataFrame(), {}
    rows = []
    for label in ["يوم","أسبوع","شهر","3 شهور","6 شهور","سنة","منذ بداية السنة","منذ الإنشاء"]:
        val = perf.get(label)
        if val is not None:
            rows.append({"الفترة": label, "العائد %": val, "الحالة": "📈 رابح" if val>0 else ("📉 خاسر" if val<0 else "➖ ثابت")})
    df = pd.DataFrame(rows)
    return df, perf
