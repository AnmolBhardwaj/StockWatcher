import json
import os
import logging

# High-Density Logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("PortfolioManager_Brain")

class BrainService:
    PRICE_FILE = os.path.join(os.path.dirname(__file__), "..", "data", "price_list.json")
    NEWS_FILE = os.path.join(os.path.dirname(__file__), "..", "data", "news_list.json")
    
    @classmethod
    def prepare_payload(cls):
        logger.info("🧠 Brain: Compiling 3-Layer Logic Payload...")
        
        prices = cls._read_json(cls.PRICE_FILE)
        news = cls._read_json(cls.NEWS_FILE)
        # Focus on last 15 news items to avoid noise
        recent_news = news[-15:] if news else [] 

        # --- THE 3-LAYER STRATEGIC PROMPT ---
        system_prompt = (
            "You are a Strategic SIP Advisor for Indian Energy/Defense. "
            "Your mandate is to evaluate: BHEL, MTAR, LT, NTPC, and WALCHANNAG.\n\n"
            
            "### THE SCORING FORMULA\n"
            "Every ticker must receive a 'Confidence Score' based on:\n"
            "Score = 0.4(Trend) + 0.3(News) + 0.3(Fundamentals)\n"
            "- Trend: +1.0 if Price > EMA(20) AND Drift is 'UP'. Else 0.\n"
            "- News: +1.0 if high-impact policy (SHANTI Bill, SMR Tenders). Else 0.\n"
            "- Fundamentals: +1.0 if clear earnings visibility (Margins > 8%). Else 0.\n\n"
            
            "### THE 3-LAYER FILTER (STRICT)\n"
            "1. Short-term: Use Trend/Drift to pick the specific day to buy.\n"
            "2. Mid-term: Use Price vs EMA(50) to decide to Hold or Buy More. (Below EMA50 = Caution/Value).\n"
            "3. Long-term: Use Policy (Nuclear/Defense) to stay in the stock for 10 years.\n\n"
            
            "### RESPONSE FORMAT (STRICT)\n"
            "**[TICKER] | Score: [X.X/1.0] | ACTION: [BUY/WAIT/HOLD]**\n"
            "**Reasoning:** (Explain using the 3 Layers: Trend, EMA50, and Policy)\n"
            "**SIP Advice:** (Allocate ₹X,XXX today based on ₹20k monthly limit)\n"
            "**Signal vs Debt:** (Signal: [Policy Win] | Debt: [Noise to Ignore])\n"
            "---"
        )

        # Context Injection
        user_message = (
            f"Here is the Computed Strategic Data (EMA/Drift included):\n{json.dumps(prices[-1:] if prices else [], indent=2)}\n\n"
            f"Recent Strategic News:\n{json.dumps(recent_news, indent=2)}\n\n"
            "Generate the Strategic Alpha Report. Be blunt. Calculate the scores."
        )

        payload = {
            "role": "system",
            "content": system_prompt,
        }
        
        full_prompt = f"{json.dumps(payload)}\n\nUSER TASK:\n{user_message}"
        return full_prompt

    @classmethod
    def _read_json(cls, path):
        if not os.path.exists(path):
            return []
        with open(path, 'r') as f:
            return json.load(f)

if __name__ == "__main__":
    print(BrainService.prepare_payload())