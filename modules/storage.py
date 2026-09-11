"""تخزين دائم للمتابعة والتنبيهات والمحفظة في JSON - لا تُفقد عند إغلاق المنصة."""
import json
import os
from datetime import datetime

STORE_PATH = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "user_store.json")

DEFAULT_STORE = {
    "watchlist": ["COMI.CA", "TMGH.CA", "SWDY.CA", "FWRY.CA", "EFIH.CA"],
    "portfolio": {},          # symbol -> {shares, avg_cost, date}
    "alerts": {},             # symbol -> {"above": price, "below": price}
    "ideas": [],              # صفقات مراقَبة: {id, symbol, entry, stop, t1, t2, added}
    "rec_log": [],            # سجل التوصيات الموثق: {id, symbol, name, entry, stop, t1, score, date, note}
    "last_seen": {},
    "settings": {"capital": 100000, "risk_pct": 2.0, "max_pct": 10.0},
}


def load_store() -> dict:
    try:
        with open(STORE_PATH, "r", encoding="utf-8") as f:
            data = json.load(f)
        # دمج المفاتيح الناقصة
        for k, v in DEFAULT_STORE.items():
            data.setdefault(k, v)
        return data
    except (FileNotFoundError, json.JSONDecodeError):
        return json.loads(json.dumps(DEFAULT_STORE))


def save_store(store: dict):
    try:
        store["last_seen"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        with open(STORE_PATH, "w", encoding="utf-8") as f:
            json.dump(store, f, ensure_ascii=False, indent=2)
    except Exception:
        pass


def add_watch(store, symbol):
    if symbol not in store["watchlist"]:
        store["watchlist"].append(symbol)
        save_store(store)

def remove_watch(store, symbol):
    if symbol in store["watchlist"]:
        store["watchlist"].remove(symbol)
        save_store(store)

def set_alert(store, symbol, above=None, below=None):
    if symbol not in store["alerts"]:
        store["alerts"][symbol] = {}
    if above is not None:
        store["alerts"][symbol]["above"] = float(above)
    if below is not None:
        store["alerts"][symbol]["below"] = float(below)
    save_store(store)

def remove_alert(store, symbol):
    if symbol in store["alerts"]:
        del store["alerts"][symbol]
        save_store(store)

def add_idea(store, symbol, entry, stop, t1, t2=None):
    """تسجيل صفقة مراقَبة: نقطة دخول + وقف + أهداف — تُتابع لحظياً."""
    store.setdefault("ideas", []).append({
        "id": datetime.now().strftime("%Y%m%d%H%M%S%f"),
        "symbol": symbol,
        "entry": float(entry),
        "stop": float(stop),
        "t1": float(t1),
        "t2": float(t2) if t2 else None,
        "added": datetime.now().strftime("%Y-%m-%d %H:%M"),
    })
    save_store(store)

def remove_idea(store, idea_id):
    store["ideas"] = [i for i in store.get("ideas", []) if i.get("id") != idea_id]
    save_store(store)

def add_rec(store, symbol, name, entry, stop, t1, score, note=""):
    """تسجيل توصية في السجل الموثق — لا يُحذف أبداً (ملف إنجاز دائم)."""
    store.setdefault("rec_log", []).append({
        "id": datetime.now().strftime("%Y%m%d%H%M%S%f"),
        "symbol": symbol,
        "name": name,
        "entry": float(entry),
        "stop": float(stop),
        "t1": float(t1),
        "score": int(score),
        "date": datetime.now().strftime("%Y-%m-%d"),
        "note": note,
    })
    save_store(store)

def has_recent_rec(store, symbol, days: int = 7) -> bool:
    """منع تكرار تسجيل نفس السهم خلال فترة قصيرة."""
    from datetime import timedelta
    cutoff = (datetime.now() - timedelta(days=days)).strftime("%Y-%m-%d")
    return any(r.get("symbol") == symbol and r.get("date", "") >= cutoff
               for r in store.get("rec_log", []))

def buy_position(store, symbol, shares, price):
    """إضافة/دمج مركز شراء في المحفظة."""
    p = store["portfolio"].get(symbol, {"shares": 0, "avg_cost": 0, "date": datetime.now().strftime("%Y-%m-%d")})
    old_sh = float(p["shares"])
    old_cost = float(p["avg_cost"])
    new_sh = old_sh + float(shares)
    if new_sh > 0:
        p["avg_cost"] = (old_sh * old_cost + float(shares) * float(price)) / new_sh
        p["shares"] = new_sh
        store["portfolio"][symbol] = p
        save_store(store)

def sell_position(store, symbol, shares):
    p = store["portfolio"].get(symbol)
    if not p:
        return False
    p["shares"] = max(0, float(p["shares"]) - float(shares))
    if p["shares"] == 0:
        del store["portfolio"][symbol]
    save_store(store)
    return True
