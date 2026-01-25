# scripts/notifier.py
import os
import requests
import logging

logger = logging.getLogger("Telegram_Notifier")

class TelegramNotifier:
    TOKEN = os.getenv("TELEGRAM_TOKEN")
    CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")

    @classmethod
    def send_alpha(cls, message):
        """Sends the Strategic Alpha report to the user."""
        if not cls.TOKEN or not cls.CHAT_ID:
            logger.error("🚫 NOTIFIER ERROR: Telegram credentials missing in environment.")
            return False

        url = f"https://api.telegram.org/bot{cls.TOKEN}/sendMessage"
        
        # Payload optimized for Telegram MarkdownV2 or HTML
        # Using HTML here as it handles special characters in LLM output better
        payload = {
            "chat_id": cls.CHAT_ID,
            "text": f"🚀 <b>STRATEGIC ALPHA REPORT</b>\n\n{message}",
            "parse_mode": "HTML"
        }

        try:
            logger.info("📡 Dispatching alert to Telegram...")
            response = requests.post(url, data=payload, timeout=10)
            response.raise_for_status()
            logger.info("✅ Telegram notification delivered.")
            return True
        except Exception as e:
            logger.error(f"❌ Telegram delivery failed: {e}")
            return False