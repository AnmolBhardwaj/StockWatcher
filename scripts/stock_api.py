# scripts/stock_api.py
import yfinance as yf
import json
import os
import logging
import pandas as pd
from datetime import datetime

# Custom Instruction: Always add lots of logs
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("SIP_Stock_API")

class StockService:
    # Original PSU/Defense stocks + 5 Sniper stocks for playbook
    TICKERS_PSU = ["BHEL.NS", "MTARTECH.NS", "WALCHANNAG.NS", "LT.NS", "NTPC.NS"]
    TICKERS_SNIPER = ["JIOFINANCIALS.NS", "MOTHERSUMI.NS", "MSUMI.NS", "LT.NS", "MTARTECH.NS"]
    # NEW: Cyclical/Swing trade stocks (intraday/short-term momentum)
    TICKERS_CYCLICAL = ["TATASTEEL.NS", "NATIONALUM.NS", "BALUFORGE.NS", "PNB.NS"]
    TICKERS = TICKERS_PSU + [t for t in TICKERS_SNIPER if t not in TICKERS_PSU] + [t for t in TICKERS_CYCLICAL if t not in TICKERS_PSU and t not in TICKERS_SNIPER]
    DATA_FILE = os.path.join(os.path.dirname(__file__), "..", "data", "price_list.json")

    @classmethod
    def _calculate_rsi(cls, series, period=14):
        """Calculate RSI(14) using standard formula: RSI = 100 - (100 / (1 + RS))"""
        try:
            delta = series.diff()
            gain = (delta.where(delta > 0, 0)).rolling(window=period).mean()
            loss = (-delta.where(delta < 0, 0)).rolling(window=period).mean()
            rs = gain / loss
            rsi = 100 - (100 / (1 + rs))
            return float(rsi.iloc[-1]) if not pd.isna(rsi.iloc[-1]) else None
        except Exception as e:
            logger.warning(f"RSI calculation failed: {e}")
            return None

    @classmethod
    def fetch_strategic_data(cls, ticker_symbol):
        """
        Calculates SIP-Grade Metrics:
        1. EMA50 (Durability Filter)
        2. 6-Month Structure (HH/HL vs LH/LL)
        3. 200-Day Moving Average (Institutional Support Line)
        4. RSI(14) (Oversold Detection for Sniper)
        5. Fundamentals (Margins/Debt)
        """
        try:
            logger.info(f"📡 Fetching 1Y history for {ticker_symbol} to audit structure...")
            ticker = yf.Ticker(ticker_symbol)
            # Fetch 1y to get clean 6mo structure + EMA50 lead-in + 200-DMA
            df = ticker.history(period="1y")
            
            if df.empty or len(df) < 130: # 130 days ~ 6 months
                logger.warning(f"⚠️ Insufficient history for {ticker_symbol}")
                return None

            # 1. PRICE & EMAs
            current_price = df['Close'].iloc[-1]
            ema_50 = df['Close'].ewm(span=50, adjust=False).mean().iloc[-1]
            
            # [TECHNICAL DEBT FLAG]: EMA20 is kept for legacy but ignored by Brain
            ema_20 = df['Close'].ewm(span=20, adjust=False).mean().iloc[-1]
            
            # NEW: 200-DMA for sniper trigger detection
            dma_200 = None
            if len(df) >= 200:
                dma_200 = df['Close'].iloc[-200:].mean()
                logger.info(f"  📊 200-DMA calculated: {round(dma_200, 2)}")
            else:
                logger.warning(f"  ⚠️ Insufficient data for 200-DMA ({len(df)} days available)")
            
            # NEW: RSI(14) for oversold detection
            rsi_14 = cls._calculate_rsi(df['Close'], period=14)
            if rsi_14:
                logger.info(f"  📈 RSI(14) calculated: {round(rsi_14, 2)}")

            # 2. 6-MONTH STRUCTURE ANALYSIS
            # Compare the last 3 months to the 3 months before that
            recent_3m = df.iloc[-63:] # Approx 3 months
            prior_3m = df.iloc[-126:-63] # Prior 3 months
            
            recent_high = recent_3m['High'].max()
            recent_low = recent_3m['Low'].min()
            prior_high = prior_3m['High'].max()
            prior_low = prior_3m['Low'].min()

            # Logic: Higher Highs (HH) + Higher Lows (HL) = Bullish Structure
            if recent_high > prior_high and recent_low > prior_low:
                structure = "BULLISH (HH/HL)"
            # Logic: Lower Highs (LH) + Lower Lows (LL) = Bearish Structure
            elif recent_high < prior_high and recent_low < prior_low:
                structure = "BEARISH (LH/LL)"
            else:
                structure = "RANGE_BOUND / FLATTENING"

            # 3. FUNDAMENTALS
            info = ticker.info
            debt_ratio = info.get('debtToEquity', 0.0)
            margins = info.get('profitMargins', 0.0)

            logger.info(f"✅ {ticker_symbol}: Structure={structure} | EMA50={round(ema_50, 2)}")

            return {
                "symbol": str(ticker_symbol),
                "price": float(round(current_price, 2)),
                "ema_50": float(round(ema_50, 2)),
                "dma_200": float(round(dma_200, 2)) if dma_200 else None,
                "rsi_14": float(round(rsi_14, 2)) if rsi_14 else None,
                "is_structural_bull": bool(current_price > ema_50),
                "market_structure": structure,
                "debt_ratio": float(debt_ratio) if debt_ratio else 0.0,
                "margins": float(margins) if margins else 0.0,
                "timestamp": datetime.now().isoformat()
            }
        except Exception as e:
            logger.error(f"❌ Structural Audit Error on {ticker_symbol}: {e}")
            return None

    @classmethod
    def update_prices(cls):
        """Updates the local JSON storage with the new SIP-grade metrics."""
        logger.info("🚀 Initiating Monthly SIP Metric Scan...")
        
        today_str = datetime.now().strftime('%Y-%m-%d')
        current_data = cls._load_storage()
        
        # We only keep the latest snapshot for the Brain to act on
        new_entry = {
            "date": today_str,
            "metrics": {}
        }

        for t in cls.TICKERS:
            data = cls.fetch_strategic_data(t)
            if data:
                new_entry["metrics"][t] = data
            else:
                new_entry["metrics"][t] = "N/A"

        # Update or Overwrite (For SIPs, we want the most recent structural state)
        cls._save_storage([new_entry]) 

    @classmethod
    def _load_storage(cls):
        if not os.path.exists(cls.DATA_FILE): return []
        try:
            with open(cls.DATA_FILE, 'r') as f: return json.load(f)
        except: return []

    @classmethod
    def _save_storage(cls, data):
        os.makedirs(os.path.dirname(cls.DATA_FILE), exist_ok=True)
        with open(cls.DATA_FILE, 'w') as f:
            json.dump(data, f, indent=2)

if __name__ == "__main__":
    StockService.update_prices()