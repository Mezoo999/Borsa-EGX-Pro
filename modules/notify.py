"""وحدة إشعارات التنبيهات السعرية — قنوات قابلة للتكوين عبر متغيرات البيئة.

الترتيب:
1. Telegram  (يحتاج TELEGRAM_BOT_TOKEN + TELEGRAM_CHAT_ID)
2. Webhook   (يحتاج WEBHOOK_URL — أي خدمة HTTP تستقبل JSON)
3. تسجيل محلي (fallback افتراضي — يكتب في السجل، لا يفشل أبداً)

طريقة الضبط (Windows PowerShell):
    $env:TELEGRAM_BOT_TOKEN="123:ABC"
    $env:TELEGRAM_CHAT_ID="123456789"
    $env:WEBHOOK_URL="https://example.com/hook"

لا توجد أي اعتمادية خارجية إضافية — كل شيء عبر مكتبة requests الموجودة.
"""
import logging
import os

import requests

logger = logging.getLogger("egx.notify")


def _telegram():
    return (os.environ.get("TELEGRAM_BOT_TOKEN", "").strip(),
            os.environ.get("TELEGRAM_CHAT_ID", "").strip())


def _webhook():
    return os.environ.get("WEBHOOK_URL", "").strip()


def enabled() -> bool:
    """هل توجد قناة خارجية مفعّلة (تليجرام أو ويبهوك)؟"""
    token, chat = _telegram()
    return bool(token and chat) or bool(_webhook())


def _send_telegram(token, chat, text):
    try:
        r = requests.post(
            f"https://api.telegram.org/bot{token}/sendMessage",
            json={"chat_id": chat, "text": text, "parse_mode": "HTML"},
            timeout=10)
        return r.status_code == 200
    except Exception as e:  # noqa: BLE001
        logger.warning("telegram failed: %s", e)
        return False


def _send_webhook(url, payload):
    try:
        r = requests.post(url, json=payload, timeout=10)
        return 200 <= r.status_code < 300
    except Exception as e:  # noqa: BLE001
        logger.warning("webhook failed: %s", e)
        return False


def send(subject: str, body: str):
    """إرسال إشعار عبر كل القنوات المفعلة. يعيد قائمة نتائج (لا يرفع استثناء أبداً)."""
    results = []
    token, chat = _telegram()
    if token and chat:
        ok = _send_telegram(token, chat, f"<b>{subject}</b>\n{body}")
        results.append(("telegram", ok))
    wh = _webhook()
    if wh:
        ok = _send_webhook(wh, {"subject": subject, "body": body})
        results.append(("webhook", ok))
    if not results:
        # fallback: سجل محلي — لا يعتمد على أي حساب خارجي
        logger.info("ALERT | %s | %s", subject, body)
        results.append(("log", True))
    return results
