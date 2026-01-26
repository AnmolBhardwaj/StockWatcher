import json
import os
import logging
from groq import Groq


# Custom Instruction: Always add lots of logs
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("PortfolioManager_Brain")

class BrainService:
    # Hard constraint: Monthly SIP Budget
    TOTAL_BUDGET = 20000 
    PRICE_FILE = os.path.join(os.path.dirname(__file__), "..", "data", "price_list.json")
    NEWS_FILE = os.path.join(os.path.dirname(__file__), "..", "data", "news_list.json")
    
    @classmethod
    def _read_json(cls, file_path):
        """Helper method to safely read JSON data."""
        logger.info(f"📂 Reading data from: {file_path}")
        if not os.path.exists(file_path):
            logger.warning(f"⚠️ File not found: {file_path}")
            return {}
        try:
            with open(file_path, 'r') as f:
                data = json.load(f)
                # If it's the price_list (a list of snapshots), take the last one
                if isinstance(data, list) and len(data) > 0:
                    return data[-1]
                return data
        except Exception as e:
            logger.error(f"❌ Failed to parse JSON at {file_path}: {e}")
            return {}

    @classmethod
    def prepare_payload(cls):
        logger.info("🧠 Initializing SIP Alpha Deployment Engine...")
        
        prices = cls._read_json(cls.PRICE_FILE)
        news = cls._read_json(cls.NEWS_FILE)
        
        
        # Validate Environment
        api_key = os.getenv("GROQ_API_KEY")
        if not api_key:
            logger.error("❌ GROQ_API_KEY missing from environment.")
            return "ERROR: Missing API Key"

        client = Groq(api_key=api_key)
        
        # The System Prompt is the 'Decision Layer'
        system_prompt = """
        You are the 'SIP Alpha Allocation Engine'. You manage a ₹{cls.TOTAL_BUDGET} monthly deployment.
        Your role is to convert raw market data into capital deployment actions.
        
        
        ### 1. SCORING MODEL (Strict Weighting: 30/20/50)
        
        - TREND (30% weight):
            +1.0: 'is_structural_bull' is True AND 'market_structure' is 'BULLISH (HH/HL)'.
            +0.5: 'market_structure' is 'RANGE_BOUND / FLATTENING' (regardless of price vs EMA50).
            +0.0: 'market_structure' is 'BEARISH (LH/LL)' (The Falling Knife).

        - NEWS (20% weight):
            +1.0: Policy tailwind + EXECUTION evidence (Orders, Tenders, JV).
            +0.5: Policy/Sector tailwind ONLY (Headlines).
            +0.0: No relevant catalysts or negative execution.

        - FUNDAMENTALS (50% weight):
            +1.0: Margins > 8% (Stable or Improving).
            +0.7: Margins 5–8% OR clear QoQ improvement.
            +0.4: Turnaround narrative (Low margins but improving visibility).
            +0.0: Structurally weak / Negative margins.

        ### 2. ACTION BANDS (Capital Allocation)
        - Score >= 0.7: 🟢 SIP AGGRESSIVE (Increase allocation)
        - 0.5 - 0.69: 🟡 SIP NORMAL (Continue monthly)
        - 0.3 - 0.49: 🟠 SIP PAUSE / WATCH (Maintain current, no new capital)
        - < 0.3: 🔴 NO SIP (Discipline over emotion)
        MATH: Individual Allocation = (Ticker Units / Total Units across all tickers) * ₹{cls.TOTAL_BUDGET}.
        If all tickers are PAUSE/NO SIP, Allocation is ₹0 (Save cash).

        ### 3. OUTPUT STRUCTURE (Telegram HTML)
        - <b>🚀 SIP ALLOCATION SUMMARY</b>: Total deployment amount for the month.
        - <b>Ticker Audit Table</b>: Wrapped in <pre> tags. Include Score, Action, and specific ₹ Allocation.
        - <b>Re-entry Triggers</b>: What specifically moves a 'PAUSE' to 'NORMAL'.
        - Reasoning: (Explain using the 3 Layers: Trend, EMA50, and Policy)
        - SIP Advice:** (Allocate ₹X,XXX today based on ₹20k monthly limit)
        """

        # Dynamic Audit: Ensuring input data is focused on 'Trusted Decisions'
        user_content = f"""
        INPUT DATA:
        Tickers (1Y Structural Audit): {json.dumps(prices[-1:] if prices else [], indent=2)}
        News (Strategic Feed): {json.dumps(news, indent=2)}
        
        Apply the SIP Alpha Framework.
        Determine the Buy/Sell/Hold action and specific fractional quantities for TODAY.
        """

        try:
            logger.info("📡 Sending data to LLaMA 3.3 for decision mapping...")
            response = client.chat.completions.create(
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_content}
                ],
                model="llama-3.3-70b-versatile",
                temperature=0.1 # Disciplined, non-creative output
            )
            
            logger.info("✅ Decision Layer output received.")
            return response.choices[0].message.content

        except Exception as e:
            logger.error(f"❌ Groq Inference Failed: {str(e)}")
            return f"CRITICAL: SIP Engine Logic Failure - {str(e)}"