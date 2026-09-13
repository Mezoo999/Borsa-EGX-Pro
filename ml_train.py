"""تدريب محرك الاحتمالات على تاريخ البورصة المصرية — يعمل يدوياً أو دورياً."""
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from modules.ml_engine import train

if __name__ == "__main__":
    top_n = int(sys.argv[1]) if len(sys.argv) > 1 else 60
    print(f"🤖 تدريب محرك الاحتمالات على أكبر {top_n} سهم مصري...")
    m = train(top_n=top_n)
    if "error" in m:
        print("❌", m["error"])
        sys.exit(1)
    print("\n=== ملخص النموذج (أرقام صادقة من اختبار زمني) ===")
    for k, v in m.items():
        print(f"  {k}: {v}")
