import json
import os
import logging
import yfinance as yf
from datetime import datetime
from groq import Groq

# Custom Instruction: Always add lots of logs
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("PortfolioManager_Brain")

class BrainService:
    # Hard constraint: Monthly SIP Budget
    TOTAL_BUDGET = int(os.getenv("TOTAL_BUDGET", 30000))
    DUMB_MONEY_PCT = 0.70  # 70% to index (reduced for cyclical)
    SNIPER_PCT = 0.20  # 20% to sniper
    CYCLICAL_PCT = 0.10  # 10% to cyclical/swing trades
    
    PRICE_FILE = os.path.join(os.path.dirname(__file__), "..", "data", "price_list.json")
    NEWS_FILE = os.path.join(os.path.dirname(__file__), "..", "data", "news_list.json")
    TRIGGERS_FILE = os.path.join(os.path.dirname(__file__), "..", "data", "triggers.json")
    CYCLICAL_FILE = os.path.join(os.path.dirname(__file__), "..", "data", "cyclical_positions.json")
    
    SNIPER_STOCKS = ["JIOFINANCIALS.NS", "MOTHERSUMI.NS", "MSUMI.NS", "LT.NS", "MTARTECH.NS"]
    CYCLICAL_STOCKS = ["TATASTEEL.NS", "NATIONALUM.NS", "BALUFORGE.NS", "PNB.NS"]

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
        """
        Prepares tri-playbook payload:
        Part A: Nifty Index Allocation (70% of budget, weekly)
        Part B: Sniper Trigger Detection (20% of budget, daily)
        Part C: Cyclical Swing Trades (10% of budget, intraday 3x daily)
        """
        logger.info("🧠 Initializing Tri-Playbook Allocation Engine...")
        
        prices = cls._read_json(cls.PRICE_FILE)
        news = cls._read_json(cls.NEWS_FILE)
        triggers = cls._read_json(cls.TRIGGERS_FILE)
        cyclical = cls._read_json(cls.CYCLICAL_FILE)
        
        # Fetch Nifty index data inline for Part A
        nifty_data = cls._fetch_nifty_indices()
        
        # Extract sniper stock data from prices
        sniper_data = cls._extract_sniper_data(prices)
        
        # Extract cyclical stock data from prices
        cyclical_data = cls._extract_cyclical_data(prices)
        
        # Determine execution mode based on environment variable
        # MONTHLY: runs weekly for Part A (index allocation)
        # DAILY: runs daily for Part B (sniper checks)
        # CYCLICAL: runs intraday 3x for Part C (swing trades)
        execution_mode = os.getenv("EXECUTION_MODE", "DAILY").upper()
        is_monthly = execution_mode == "MONTHLY"
        is_cyclical = execution_mode == "CYCLICAL"
        
        # Validate Environment
        api_key = os.getenv("GROQ_API_KEY")
        if not api_key:
            logger.error("❌ GROQ_API_KEY missing from environment.")
            return "ERROR: Missing API Key"

        client = Groq(api_key=api_key)
        
        # Build execution-mode-specific prompt
        system_prompt = cls._build_system_prompt(is_monthly, is_cyclical)
        
        # Build user content with all required data
        user_content = cls._build_user_content(prices, news, triggers, cyclical, nifty_data, sniper_data, cyclical_data, is_monthly, is_cyclical)
        
        try:
            logger.info("📡 Sending playbook data to LLaMA 3.3 for decision mapping...")
            response = client.chat.completions.create(
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_content}
                ],
                model="llama-3.3-70b-versatile",
                temperature=0.1  # Disciplined, deterministic output for trigger detection
            )
            
            logger.info("✅ Playbook decision layer output received.")
            return response.choices[0].message.content

        except Exception as e:
            logger.error(f"❌ Groq Inference Failed: {str(e)}")
            return f"CRITICAL: Playbook Engine Failure - {str(e)}"

    @classmethod
    def _fetch_nifty_indices(cls):
        """Fetch Nifty 50 and Nifty Next 50 data for Part A."""
        try:
            logger.info("📊 Fetching Nifty indices...")
            nifty_50 = yf.Ticker("^NSEI")
            nifty_next_50 = yf.Ticker("^NSENXT50")
            
            df_50 = nifty_50.history(period="1y")
            df_next = nifty_next_50.history(period="1y")
            
            result = {}
            
            # Nifty 50
            if len(df_50) > 0:
                result["NIFTY_50"] = {
                    "price": float(df_50['Close'].iloc[-1]),
                    "ema_50": float(df_50['Close'].ewm(span=50).mean().iloc[-1]),
                    "dma_200": float(df_50['Close'].iloc[-200:].mean()) if len(df_50) >= 200 else None
                }
            
            # Nifty Next 50
            if len(df_next) > 0:
                result["NIFTY_NEXT_50"] = {
                    "price": float(df_next['Close'].iloc[-1]),
                    "ema_50": float(df_next['Close'].ewm(span=50).mean().iloc[-1]),
                    "dma_200": float(df_next['Close'].iloc[-200:].mean()) if len(df_next) >= 200 else None
                }
            
            logger.info(f"✅ Nifty indices fetched: {json.dumps(result)}")
            return result
        except Exception as e:
            logger.warning(f"⚠️ Failed to fetch Nifty indices: {e}")
            return {}

    @classmethod
    def _extract_sniper_data(cls, prices):
        """Extract sniper stock metrics from price data."""
        sniper_data = {}
        metrics = prices.get("metrics", {})
        
        for stock in cls.SNIPER_STOCKS:
            if stock in metrics:
                data = metrics[stock]
                sniper_data[stock] = {
                    "price": data.get("price"),
                    "dma_200": data.get("dma_200"),
                    "rsi_14": data.get("rsi_14"),
                    "market_structure": data.get("market_structure"),
                    "margins": data.get("margins")
                }
        
        return sniper_data

    @classmethod
    def _extract_cyclical_data(cls, prices):
        """Extract cyclical stock metrics for swing trading."""
        cyclical_data = {}
        metrics = prices.get("metrics", {})
        
        for stock in cls.CYCLICAL_STOCKS:
            if stock in metrics:
                data = metrics[stock]
                cyclical_data[stock] = {
                    "price": data.get("price"),
                    "rsi_14": data.get("rsi_14"),
                    "ema_50": data.get("ema_50"),
                    "market_structure": data.get("market_structure"),
                    "volume_signal": "N/A"  # Would need intraday data for actual volume
                }
        
        return cyclical_data

    @classmethod
    def _build_system_prompt(cls, is_monthly, is_cyclical):
        """Build system prompt based on execution mode."""
        
        if is_monthly:
            return """
You are the "Dumb Money + Sniper + Cyclical" Tri-Playbook Engine.

## PLAYBOOK PART A: Dumb Money Core (Weekly)

The 'Dumb Money' strategy allocates 70% of monthly budget to Nifty 50 + Nifty Next 50 index funds.

DECISION LOGIC:
- Evaluate overall market conditions
- If market in structural downtrend (price < 200-DMA AND price < EMA50): Reduce to 50%
- Otherwise (bullish or range-bound): Allocate full 70%

OUTPUT:
```
🚀 DUMB MONEY ALLOCATION (Weekly)
━━━━━━━━━━━━━━━━━━━━━━
📊 INDEX ALLOCATION: ₹21,000 (70% of ₹30,000)
   - NIFTYBEES: ₹10,500
   - NIFTYNXT: ₹10,500

💰 SNIPER HOLD: ₹6,000 (20%)
💎 CYCLICAL HOLD: ₹3,000 (10%)
```
"""
        elif is_cyclical:
            return """
You are the "Dumb Money + Sniper + Cyclical" Tri-Playbook Engine.

## PLAYBOOK PART C: Cyclical Swing Trades (Intraday, 3x Daily)

Cyclical strategy allocates 10% of budget to momentum/swing trades (1-3 day holds).
Stocks: TATASTEEL, NATIONALUM, BALUFORGE, PNB

TRIGGER CONDITIONS (Check all):

**Trigger 1: Momentum Break (RSI > 50 from below)**
- If RSI crosses above 50 (entering uptrend): FLAG 🟢 (MOMENTUM_UP)
- Entry: Market open at crossover
- Target: +3% profit
- Stop: -1%

**Trigger 2: Oversold Bounce (RSI < 20 + rebound 1%)**
- If RSI < 20 AND price rebounds 1%: FLAG 🔵 (OVERSOLD_BOUNCE)
- Quick scalp entry
- Target: +2% profit
- Stop: -1%

**Trigger 3: Sector Strength (Intraday breakout)**
- If sector (metals/banks) breaks intraday highs: FLAG 🟡 (SECTOR_STRENGTH)
- Entry: Jump on momentum
- Target: +4% or EOD exit

OUTPUT:
```
📊 CYCLICAL MOMENTUM CHECK (Intraday)
━━━━━━━━━━━━━━━━━━━━━━━
💵 Available Cash: ₹3,000

🔍 MOMENTUM WATCH:
  ✅ TATASTEEL | Price: ₹XXX | RSI: XX
     🟢 MOMENTUM_UP | Target: +3% | Entry: NOW ⚡
  
  ⭕ NATIONALUM | Price: ₹XXX | RSI: XX
     No triggers - WAIT

💡 Trades to Exit:
  [If any open positions near targets]
```

STRICT: Take profit at targets. Do not hold overnight unless confirmed next day trend.
"""
        else:
            return """
You are the "Dumb Money + Sniper + Cyclical" Tri-Playbook Engine.

## PLAYBOOK PART B: Sniper Trigger Detection (Daily, After Market Close)

Sniper allocates 20% of budget to quality tactical entries when specific triggers fire.
Stocks: JIOFINANCIALS, MOTHERSON, MSUMI, NTPC, MTARTECH

TRIGGER CONDITIONS (Check all three):

**Trigger 1: 200-DMA Touch** → Deploy 40% of sniper cash
- If price <= 200-DMA: FLAG 🔴 (200-DMA_BREACH)

**Trigger 2: Oversold (RSI < 30)** → Deploy 30% of sniper cash
- If RSI < 30: FLAG 🟠 (OVERSOLD)

**Trigger 3: Macro Event** → Deploy 30% of sniper cash
- If macro event + stock not in downtrend: FLAG 🟡 (MACRO_FEAR)

OUTPUT:
```
📊 SNIPER TRIGGER CHECK
━━━━━━━━━━━━━━━━━━━━━━━
💵 Available Cash: ₹6,000

🔍 TRIGGERS:
  ✅ JIOFINANCIALS | RSI: 28 | 200-DMA: ₹260
     🟠 OVERSOLD → Deploy: ₹1,800 ⚠️
  
  ⭕ MOTHERSON | RSI: 45
     No triggers - WAIT

💰 Remaining: ₹4,200
```
"""

**Trigger 1: 200-Day Moving Average Touch**
- If current_price <= 200-DMA (exact touch, 0% tolerance):
  - Flag as TRIGGERED
  - Deploy 40% of sniper cash
  - Reasoning: Institutional support line, high-probability entry

**Trigger 2: Oversold Panic (RSI < 30)**
- If RSI(14) < 30:
  - Flag as TRIGGERED
  - Deploy 30% of sniper cash
  - Reasoning: Extreme selling exhaustion, reversal likely

**Trigger 3: Macro Overreaction**
- If recent macro event exists (Fed rate, RBI policy, geopolitical) AND stock is NOT in structural downtrend:
  - Flag as TRIGGERED
  - Deploy 30% of sniper cash
  - Reasoning: Market panic on event unrelated to company fundamentals

OUTPUT FORMAT for Part B:
```
PART B: SNIPER TRIGGER ALERTS
Total Sniper Cash: ₹X,XXX (25% of budget)

Active Triggers:
- [STOCK]: [TRIGGER_TYPE] | Recommended Deploy: ₹X,XXX
- [STOCK]: [TRIGGER_TYPE] | Recommended Deploy: ₹X,XXX
  (if any)

If NO triggers fired: "NO TRIGGERS FIRED TODAY - Hold sniper cash at ₹X,XXX"
```

STRICT RULE: Deploy funds ONLY if trigger conditions are met. Do not invent reasons.
"""

    @classmethod
    def _build_user_content(cls, prices, news, triggers, cyclical, nifty_data, sniper_data, cyclical_data, is_monthly, is_cyclical):
        """Build user message with execution-mode-specific data."""
        
        content = f"""
=== TRI-PLAYBOOK DATA INPUT ===
Execution Mode: {"WEEKLY (Dumb Money)" if is_monthly else "INTRADAY (Cyclical)" if is_cyclical else "DAILY (Sniper)"}
Current Date/Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')} IST
Budget Allocation: 70% Dumb Money + 20% Sniper + 10% Cyclical

"""

        if is_monthly:
            content += f"""
PART A DATA: NIFTY INDICES (Weekly Allocation Check)
{json.dumps(nifty_data, indent=2)}

Sniper Stock Health (for reference):
{json.dumps(sniper_data, indent=2)}

Cyclical Stocks (for reference):
{json.dumps(cyclical_data, indent=2)}

Macro Context:
{json.dumps([n for n in (news if isinstance(news, list) else []) if 'macro_trigger_type' in n][:5], indent=2)}
"""
        elif is_cyclical:
            content += f"""
PART C DATA: CYCLICAL SWING TRADES (Intraday Momentum Check)

Current Cyclical Positions:
{json.dumps(cyclical.get('active_positions', []) if isinstance(cyclical, dict) else [], indent=2)}

Cyclical Stock Metrics:
{json.dumps(cyclical_data, indent=2)}

Available Cash for Cyclical: ₹{cyclical.get('current_cyclical_cash', cls.TOTAL_BUDGET * cls.CYCLICAL_PCT) if isinstance(cyclical, dict) else cls.TOTAL_BUDGET * cls.CYCLICAL_PCT}
"""
        else:
            content += f"""
PART B DATA: SNIPER TACTICAL ENTRIES (Daily After Market Close)

Sniper Stock Metrics:
{json.dumps(sniper_data, indent=2)}

Available Sniper Cash: ₹{triggers.get('current_sniper_cash', cls.TOTAL_BUDGET * cls.SNIPER_PCT) if isinstance(triggers, dict) else cls.TOTAL_BUDGET * cls.SNIPER_PCT}

Recent Macro Events (May trigger Macro Fear):
{json.dumps([n for n in (news if isinstance(news, list) else []) if 'macro_trigger_type' in n][:3], indent=2)}

Recent Order Wins (May trigger Sniper):
{json.dumps([n for n in (news if isinstance(news, list) else []) if 'ORDER_WIN' in n.get('category', '')][:3], indent=2)}
"""

        return content