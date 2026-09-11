"""تشغيل التقرير الصباحي — يُستدعى من الجدولة الآلية (9:30 أيام التداول) أو يدوياً."""
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from modules.daily_report import generate_report, save_report

if __name__ == "__main__":
    md = generate_report()
    p = save_report(md)
    print(f"REPORT_SAVED: {p}")
    print("---")
    print(md)
