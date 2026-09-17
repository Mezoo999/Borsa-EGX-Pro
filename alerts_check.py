"""فحص التنبيهات السعرية وإرسال الإشعارات — يُنفَّذ مرة واحدة (صالح للجدولة).

التشغيل اليدوي:
    python alerts_check.py

الجدولة (مثال كل 5 دقائق):
    schtasks /Create /TN "EGX Alerts" /TR "\"<python.exe>\" \"<المسار>\\alerts_check.py\"" /SC MINUTE /MO 5 /F
"""
import os
import sys
from datetime import datetime

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from modules import tv_data as tvd, notify
import modules.storage as store


def run_once():
    st_ = store.load_store()
    alerts = st_.get("alerts") or {}
    if not alerts:
        print("لا توجد تنبيهات مفعلة حالياً")
        return
    snap = tvd.snapshot(force=True)
    if not snap:
        print("تعذّر جلب الأسعار اللحظية من TradingView")
        return
    today = datetime.now().strftime("%Y-%m-%d")
    sent = 0
    for sym, a in alerts.items():
        row = snap.get(sym.replace(".CA", ""))
        if not row:
            continue
        price = row["close"]
        msgs = []
        above, below = a.get("above"), a.get("below")
        if above and price >= above and not store.alert_fired_today(st_, sym, "above", today):
            msgs.append(f"⬆️ {sym.replace('.CA', '')} صعد فوق {above:,.2f} ج.م — الآن {price:,.2f}")
            store.mark_alert_fired(st_, sym, "above", today)
        if below and price <= below and not store.alert_fired_today(st_, sym, "below", today):
            msgs.append(f"⬇️ {sym.replace('.CA', '')} هبط تحت {below:,.2f} ج.م — الآن {price:,.2f}")
            store.mark_alert_fired(st_, sym, "below", today)
        for m in msgs:
            notify.send("🔔 تنبيه سعر — EGX Pro", m)
            sent += 1
    print(f"فحص التنبيهات اكتمل — أُرسل {sent} إشعار جديد")


if __name__ == "__main__":
    run_once()
