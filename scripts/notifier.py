import requests
import os
import logging
import html
import time

logger = logging.getLogger("Telegram_Notifier")

class TelegramNotifier:
    @classmethod
    def send_alpha(cls, text):
        token = os.getenv("TELEGRAM_TOKEN")
        chat_id = os.getenv("TELEGRAM_CHAT_ID")
        
        if not token or not chat_id:
            logger.error("🚫 Telegram Credentials Missing")
            return False

        # 1. ESCAPE THE BODY (Prevents 400 Errors from <, >, &)
        safe_body = html.escape(text)
        
        # 2. SMART CHUNKING (Limit characters, not lines)
        # We use 3500 to leave room for <b> and <pre> tags
        MAX_LEN = 3500 
        chunks = []
        current_chunk = ""

        # Split by lines to avoid cutting mid-sentence
        for line in safe_body.splitlines():
            # If adding this line exceeds limit, start new chunk
            if len(current_chunk) + len(line) + 1 > MAX_LEN:
                chunks.append(current_chunk.strip())
                current_chunk = line + "\n"
            else:
                current_chunk += line + "\n"
        
        # Add the final remaining piece
        if current_chunk:
            chunks.append(current_chunk.strip())

        # 3. DELIVERY
        success = True
        for i, chunk in enumerate(chunks):
            formatted_msg = (
                f"<b>🚀 STRATEGIC ALPHA REPORT [{i+1}/{len(chunks)}]</b>\n"
                f"<pre>{chunk}</pre>"
            )
            
            if not cls._execute_send(token, chat_id, formatted_msg):
                success = False
            time.sleep(1.5) # Slightly longer sleep to avoid Telegram Flood limits
            
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
            r = requests.post(url, json=payload, timeout=15)
            r.raise_for_status()
            logger.info(f"📡 Chunk delivered successfully.")
            return True
        except Exception as e:
            logger.error(f"❌ Telegram Error: {e}")
            # Final fallback: strip tags and send raw
            try:
                payload.pop("parse_mode")
                payload["text"] = f"⚠️ [RAW FALLBACK]\n{message_text.replace('<pre>','').replace('</pre>','').replace('<b>','').replace('</b>','')}"
                requests.post(url, json=payload)
            except:
                pass
            return False