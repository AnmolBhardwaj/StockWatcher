import yfinance as yf
import json
import os
import logging
from datetime import datetime

# Configure High-Density Logger
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("StockWatcher_API")
formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - [BLUNT_COEFF: HIGH] - %(message)s')
handler = logging.StreamHandler()
handler.setFormatter(formatter)
if not logger.handlers:
    logger.addHandler(handler)

class StockService:
    TICKERS = ["BHEL.NS", "MTARTECH.NS", "WALCHANNAG.NS", "LT.NS", "NTPC.NS"]
    DATA_FILE = "price_list.json"

    @classmethod
    def update_prices(cls):
        """Main execution loop for the 30-min price fetch."""
        logger.info("🚀 Initiating Stock Price Update Routine...")
        
        current_data = cls._load_storage()
        today_str = datetime.now().strftime('%Y-%m-%d')
        
        # 1. State Audit: Check if we need to reset for a new day
        if current_data and current_data[-1].get('date') != today_str:
            logger.info(f"📅 Date Change Detected (Last: {current_data[-1].get('date')} | Now: {today_str}). Resetting JSON.")
            current_data = []
        elif not current_data:
            logger.info("📁 JSON is empty or missing. Starting fresh for today.")
        else:
            logger.debug(f"🔄 Date match confirmed ({today_str}). Appending to existing records.")

        # 2. Fetch Logic
        timestamp = datetime.now().strftime('%H:%M:%S')
        new_entries = {"date": today_str, "time": timestamp, "prices": {}}

        for ticker in cls.TICKERS:
            try:
                logger.debug(f"📡 Calling yfinance for {ticker}...")
                stock = yf.Ticker(ticker)
                # Using fast_info for minimal latency in 30-min intervals
                price = round(stock.fast_info.last_price, 2)
                
                new_entries["prices"][ticker] = price
                logger.info(f"✅ {ticker}: {price} INR")
            except Exception as e:
                logger.error(f"❌ Failed to fetch {ticker}: {str(e)}")
                new_entries["prices"][ticker] = "N/A"

        # 3. Save Logic
        current_data.append(new_entries)
        cls._save_storage(current_data)
        logger.info(f"💾 Cycle complete. Total records for today: {len(current_data)}")

    @classmethod
    def _load_storage(cls):
        if not os.path.exists(cls.DATA_FILE):
            return []
        try:
            with open(cls.DATA_FILE, 'r') as f:
                return json.load(f)
        except Exception as e:
            logger.error(f"⚠️ Corruption in {cls.DATA_FILE}: {e}. Clearing file.")
            return []

    @classmethod
    def _save_storage(cls, data):
        try:
            with open(cls.DATA_FILE, 'w') as f:
                json.dump(data, f, indent=2)
            logger.debug(f"📝 Successfully wrote {len(data)} entries to {cls.DATA_FILE}")
        except Exception as e:
            logger.critical(f"🚫 Critical I/O Error: Could not save data: {e}")

if __name__ == "__main__":
    # Manual Trigger Test
    StockService.update_prices()