import requests
import os
import logging
import html
import time

logger = logging.getLogger("Telegram_Notifier")

class TelegramNotifier:
    @classmethod
    def send_alpha(cls, text):
        # Retrieve tokens from Environment (Local .env or GitHub Secrets)
        token = os.getenv("TELEGRAM_TOKEN")
        chat_id = os.getenv("TELEGRAM_CHAT_ID")
        
        if not token or not chat_id:
            logger.error("🚫 TELEGRAM_TOKEN or CHAT_ID missing from Environment.")
            return False

        # 1. ESCAPE THE RAW AI CONTENT
        # Converts '<' to '&lt;' so they don't interfere with our HTML tags
        safe_body = html.escape(text)
        
        # 2. CHUNKING LOGIC (Telegram limit is 4096 chars)
        # We use 3500 to leave a margin for our <b> and <pre> tags
        MAX_LEN = 3500
        chunks = []
        current_chunk = ""

        for line in safe_body.splitlines():
            if len(current_chunk) + len(line) + 1 > MAX_LEN:
                chunks.append(current_chunk.strip())
                current_chunk = line + "\n"
            else:
                current_chunk += line + "\n"
        
        if current_chunk:
            chunks.append(current_chunk.strip())

        # 3. SEQUENTIAL DELIVERY
        success = True
        for i, chunk in enumerate(chunks):
            # Using your verified HTML structure
            formatted_msg = (
                f"<b>📊 STRATEGIC ALPHA REPORT [{i+1}/{len(chunks)}]</b>\n\n"
                f"<pre>{chunk}</pre>\n\n"
                f"<code>Generated at: {time.strftime('%H:%M:%S IST')}</code>"
            )
            
            if not cls._execute_send(token, chat_id, formatted_msg):
                success = False
            
            # Delay to prevent Telegram Flood Error
            time.sleep(1.5) 
            
        return success

    @classmethod
    def _execute_send(cls, token, chat_id, message_text):
        url = f"https://api.telegram.org/bot{token}/sendMessage"
        
        # Using 'data' payload as verified in your test script
        payload = {
            "chat_id": chat_id,
            "text": message_text,
            "parse_mode": "HTML",
            "disable_web_page_preview": "True"
        }
        
        try:
            # 15s timeout for GitHub Actions stability
            response = requests.post(url, data=payload, timeout=15)
            response.raise_for_status()
            logger.info("📡 Chunk delivered successfully.")
            return True
        except Exception as e:
            logger.error(f"❌ Telegram Delivery Error: {e}")
            # Final emergency fallback: Send as plain text if HTML tags are broken
            try:
                payload.pop("parse_mode")
                payload["text"] = f"⚠️ [FORMAT ERROR - RAW TEXT]:\n{message_text}"
                requests.post(url, data=payload)
            except:
                pass
            return False