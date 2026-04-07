# main.py
import os
import logging
from datetime import datetime
from groq import Groq
from scripts.brain import BrainService
from scripts.notifier import TelegramNotifier
from scripts.stock_api import StockService # Added direct import for safety

# High-Density Logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("StrategicWatcher_Main")

def determine_execution_mode():
    """Determine execution mode based on current date and time."""
    current_day = datetime.now().day
    current_hour = datetime.now().hour  # UTC
    # IST = UTC + 5:30, so 11 AM IST = 5:30 AM UTC, 1 PM IST = 7:30 AM UTC, 3:45 PM IST = 10:15 AM UTC
    
    # Override via environment variable for testing
    if "EXECUTION_MODE" in os.environ:
        return os.environ["EXECUTION_MODE"]
    
    # Determine mode by date/time
    if current_day == 1 or (current_day == 2 and current_hour < 6):  # Monday on 1st or early 2nd
        return "MONTHLY"
    elif current_hour in [5, 7, 10]:  # 11 AM, 1 PM, 3:45 PM IST (approx)
        return "CYCLICAL"
    else:
        return "DAILY"

def run_strategic_audit():
    logger.info("🎬 [SYSTEM START] Playbook-Based Investment Engine...")
    
    # Determine execution mode based on current date
    execution_mode = determine_execution_mode()
    os.environ["EXECUTION_MODE"] = execution_mode
    logger.info(f"📅 Execution Mode: {execution_mode}")
    
    api_key = os.getenv("GROQ_API_KEY")
    if not api_key:
        logger.critical("🚫 MISSING API KEY.")
        return

    try:
        payload_content = BrainService.prepare_payload()
        response_text = payload_content
        
        # 3. NOTIFY
        if response_text:
            output_header = f"\n{'='*50}\n[{execution_mode} EXECUTION - {datetime.now().isoformat()}]\n{'='*50}\n"
            output_footer = f"\n{'='*50}\n"
            print(output_header + response_text + output_footer)
            
            TelegramNotifier.send_alpha(response_text)
            logger.info(f"✅ {execution_mode} Cycle Complete.")
            
    except Exception as e:
        logger.error(f"💥 Failure: {e}", exc_info=True)

if __name__ == "__main__":
    run_strategic_audit()