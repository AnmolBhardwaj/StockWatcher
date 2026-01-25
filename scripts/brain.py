# scripts/brain.py
import json
import os
import logging
from datetime import datetime

# High-Density Logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("PortfolioManager_Brain")
formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - [BLUNT_COEFF: HIGH] - %(message)s')
handler = logging.StreamHandler()
handler.setFormatter(formatter)
if not logger.handlers:
    logger.addHandler(handler)

class BrainService:
    PRICE_FILE = "price_list.json" # Relative path based on your setup
    NEWS_FILE = "data/news_list.json"
    
    @classmethod
    def prepare_payload(cls):
        logger.info("🧠 Brain: Preparing Strategic Payload...")
        
        prices = cls._read_json(cls.PRICE_FILE)
        news = cls._read_json(cls.NEWS_FILE)
        
        # Filter news for just the last 24-48 hours to avoid context bloat
        recent_news = news[-15:] if news else [] 
        
        # 1. System Persona (The Senior Portfolio Manager)
        system_prompt = (
            "You are a Senior Portfolio Manager specializing in Indian Strategic Industrials (Defence, Nuclear, Infra). "
            "Your tone is blunt, logical, and highly technical. You despise 'aesthetic' news and focus only on 'Direct Growth Catalysts'. "
            "Your goal: Identify if price movements in the portfolio align with nuclear/defence policy shifts (like the SHANTI Bill or AERB tenders)."
        )

        # 2. Contextual Data Injection
        payload = {
            "role": "system",
            "content": system_prompt,
            "context": {
                "market_data": prices,
                "strategic_news": recent_news,
                "watchlist_rules": [
                    "AERB licensing guidelines = Long-term growth",
                    "SMR tenders = Direct catalyst",
                    "New supplier contracts for MTAR/BHEL/LT = Earnings visibility"
                ]
            }
        }

        # 3. User Task
        user_message = (
            "Analyze the current Price List and Strategic News. "
            "Identify the 'Signal-to-Noise' ratio. Specifically: "
            "1. Is there a price spike in BHEL/MTAR/LT that correlates with Nuclear news? "
            "2. Flag any 'Technical Debt'—news that is purely aesthetic without commercial impact. "
            "3. Give a 3-sentence 'Strategic Alpha' summary for a Signal/Telegram alert."
        )

        full_prompt = f"{json.dumps(payload, indent=2)}\n\nUSER TASK:\n{user_message}"
        
        logger.info("✅ Payload Ready. Logic Density: 9/10.")
        return full_prompt

    @classmethod
    def _read_json(cls, path):
        if not os.path.exists(path):
            logger.warning(f"⚠️ Missing file: {path}")
            return []
        with open(path, 'r') as f:
            return json.load(f)

if __name__ == "__main__":
    prompt = BrainService.prepare_payload()
    print("\n--- GENERATED PAYLOAD ---\n")
    print(prompt)