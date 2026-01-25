import requests
import os
import logging
import time

logger = logging.getLogger("Telegram_Notifier")

class TelegramNotifier:
    @classmethod
    def send_alpha(cls, text):
        token = os.getenv("TELEGRAM_TOKEN")
        chat_id = os.getenv("TELEGRAM_CHAT_ID")
        
        if not token or not chat_id:
            logger.error("🚫 Credentials missing.")
            return False

        # Telegram limit is 4096. We use 3800 to be safe with HTML tags.
        MAX_LENGTH = 3800 
        
        # If text is short, send normally
        if len(text) <= MAX_LENGTH:
            return cls._execute_send(token, chat_id, text)

        # Split logic: Break by paragraphs to keep info readable
        logger.info(f"📏 Report too long ({len(text)} chars). Splitting into chunks...")
        chunks = []
        current_chunk = ""
        
        for paragraph in text.split('\n\n'):
            if len(current_chunk) + len(paragraph) < MAX_LENGTH:
                current_chunk += paragraph + "\n\n"
            else:
                chunks.append(current_chunk.strip())
                current_chunk = paragraph + "\n\n"
        chunks.append(current_chunk.strip())

        # Send each chunk
        success = True
        for i, chunk in enumerate(chunks):
            header = f"<b>[PART {i+1}/{len(chunks)}]</b>\n"
            if not cls._execute_send(token, chat_id, header + chunk):
                success = False
            time.sleep(1) # Prevent rate limiting
            
        return success

    @classmethod
    def _execute_send(cls, token, chat_id, message_text):
        url = f"https://api.telegram.org/bot{token}/sendMessage"
        payload = {
            "chat_id": chat_id,
            "text": message_text,
            "parse_mode": "HTML",
            "disable_web_page_preview": True
        }
        try:
            response = requests.post(url, json=payload)
            response.raise_for_status()
            return True
        except Exception as e:
            # Fallback: Try sending as plain text if HTML fails
            logger.error(f"❌ Chunk failed: {e}. Attempting plain text fallback.")
            payload.pop("parse_mode")
            requests.post(url, json=payload)
            return False