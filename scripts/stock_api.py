# scripts/stock_api.py
import yfinance as yf
import json
import os
import logging
import pandas as pd
from datetime import datetime

# High-Density Logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("StockWatcher_API")
formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - [BLUNT_COEFF: HIGH] - %(message)s')
handler = logging.StreamHandler()
handler.setFormatter(formatter)
if not logger.handlers:
    logger.addHandler(handler)

class StockService:
    # Added NTPC as requested
    TICKERS = ["BHEL.NS", "MTARTECH.NS", "WALCHANNAG.NS", "LT.NS", "NTPC.NS"]
    # Saved in 'data' folder to be clean
    DATA_FILE = os.path.join(os.path.dirname(__file__), "..", "data", "price_list.json")

    @classmethod
    def fetch_strategic_data(cls, ticker_symbol):
        """Calculates 3-Layer Metrics: EMA(20/50), Drift, and Fundamentals."""
        try:
            ticker = yf.Ticker(ticker_symbol)
            # Fetch 60 days to calculate accurate EMA(50)
            df = ticker.history(period="60d")
            
            if df.empty:
                logger.warning(f"⚠️ No history found for {ticker_symbol}")
                return None

            # 1. Technicals (Pandas Native)
            current_price = df['Close'].iloc[-1]
            ema_20 = df['Close'].ewm(span=20, adjust=False).mean().iloc[-1]
            ema_50 = df['Close'].ewm(span=50, adjust=False).mean().iloc[-1]
            
            # Linear Drift (Slope of last 5 days)
            # Positive = UP Trend, Negative = DOWN Trend
            drift_val = df['Close'].tail(5).diff().mean()
            drift_signal = "UP" if drift_val > 0 else "DOWN"

            # 2. Fundamentals (For Layer 3 Score)
            info = ticker.info
            debt_ratio = info.get('debtToEquity', 0)
            margins = info.get('profitMargins', 0)

            return {
                "symbol": ticker_symbol,
                "price": round(current_price, 2),
                "ema_20": round(ema_20, 2),
                "ema_50": round(ema_50, 2),
                "drift": drift_signal,
                "is_bullish": current_price > ema_20,
                "is_structural": current_price > ema_50, # Mid-term check
                "debt_ratio": debt_ratio,
                "margins": margins
            }
        except Exception as e:
            logger.error(f"❌ Math Error on {ticker_symbol}: {e}")
            return None

    @classmethod
    def update_prices(cls):
        """Main Loop: Fetches metrics and saves to JSON."""
        logger.info("🚀 Initiating Strategic Metric Update...")
        
        today_str = datetime.now().strftime('%Y-%m-%d')
        timestamp = datetime.now().strftime('%H:%M:%S')
        
        # Load existing or start fresh
        current_data = cls._load_storage()
        
        # Daily Reset Logic
        if current_data and current_data[-1].get('date') != today_str:
            logger.info("📅 New Trading Day Detected. Resetting JSON.")
            current_data = []

        new_entry = {
            "date": today_str,
            "time": timestamp,
            "metrics": {}
        }

        for t in cls.TICKERS:
            data = cls.fetch_strategic_data(t)
            if data:
                new_entry["metrics"][t] = data
                logger.info(f"✅ {t}: {data['price']} | EMA20: {data['ema_20']} | Drift: {data['drift']}")
            else:
                new_entry["metrics"][t] = "N/A"

        current_data.append(new_entry)
        cls._save_storage(current_data)

    @classmethod
    def _load_storage(cls):
        if not os.path.exists(cls.DATA_FILE):
            return []
        try:
            with open(cls.DATA_FILE, 'r') as f:
                return json.load(f)
        except Exception:
            return []

    @classmethod
    def _save_storage(cls, data):
        os.makedirs(os.path.dirname(cls.DATA_FILE), exist_ok=True)
        with open(cls.DATA_FILE, 'w') as f:
            json.dump(data, f, indent=2)

if __name__ == "__main__":
    StockService.update_prices()