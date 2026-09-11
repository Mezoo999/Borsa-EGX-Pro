"""وحدة التحقق الموثوق للبيانات الحية - مجانية"""
import requests
from bs4 import BeautifulSoup
import re

# خريطة EGX -> Investing.com slug (للمقارنة)
INVESTING_MAP = {
    "COMI.CA": "com-intl-bk",
    "TMGH.CA": "talaat-moustafa-group",
    "SWDY.CA": "elsewedy-cable",
    "ETEL.CA": "telecom-egypt",
    "EFIH.CA": "e-finance-for-digital",
    "FWRY.CA": "fawry-banking-and-payment",
    "ABUK.CA": "abou-kir-fertilizers",
    "EAST.CA": "eastern-co",
    "HRHO.CA": "efg-hermes",
    "ORHD.CA": "orascom-devt",
}

def fetch_investing_price(symbol: str, timeout=8):
    """محاولة جلب السعر من Investing.com للمقارنة (مجاني، بدون اشتراك)"""
    slug = INVESTING_MAP.get(symbol)
    if not slug:
        return None
    url = f"https://www.investing.com/equities/{slug}"
    try:
        headers = {"User-Agent": "Mozilla/5.0"}
        r = requests.get(url, headers=headers, timeout=timeout)
        if r.status_code != 200:
            return None
        # بحث بسيط عن السعر
        m = re.search(r'"price"\s*:\s*"?([\d,.]+)"?', r.text)
        if m:
            return float(m.group(1).replace(",",""))
        # fallback: ابحث عن 141.00 في النص
        soup = BeautifulSoup(r.text, "html.parser")
        text = soup.get_text()
        # ابحث عن نمط سعر
        return None
    except:
        return None

def egx_market_status():
    """حالة السوق المصري (الأحد-الخميس 10:00-14:30 بتوقيت القاهرة)"""
    from datetime import datetime, timezone, timedelta
    # توقيت القاهرة UTC+3
    now_cairo = datetime.now(timezone(timedelta(hours=3)))
    weekday = now_cairo.weekday()  # 0=Mon ... 6=Sun
    # EGX: الأحد=6, الإثنين=0 ... الخميس=3
    # مفتوح الأحد (6) إلى الخميس (3)
    is_weekend = weekday in [4,5]  # الجمعة والسبت
    hour = now_cairo.hour + now_cairo.minute/60
    is_trading_hours = 10 <= hour <= 14.5
    if is_weekend:
        return {"open": False, "reason": "عطلة نهاية الأسبوع (الجمعة-السبت)", "next": "الأحد 10:00"}
    if not is_trading_hours:
        if hour < 10:
            return {"open": False, "reason": f"قبل الافتتاح (يفتح 10:00)", "next": "اليوم 10:00"}
        else:
            return {"open": False, "reason": "بعد الإغلاق (أغلق 14:30)", "next": "غداً 10:00"}
    return {"open": True, "reason": "السوق مفتوح الآن (10:00-14:30)", "next": "يغلق 14:30"}
