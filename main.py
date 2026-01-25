# main.py
import os
import logging
from groq import Groq
from scripts.brain import BrainService
from scripts.notifier import TelegramNotifier
from scripts.stock_api import StockService # Added direct import for safety

# High-Density Logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("StrategicWatcher_Main")

def run_strategic_audit():
    logger.info("🎬 [SYSTEM START] 3-Layer Strategic Audit...")
    
    api_key = os.getenv("GROQ_API_KEY")
    if not api_key:
        logger.critical("🚫 MISSING API KEY.")
        return

    try:
        client = Groq(api_key=api_key)
        
        # 1. GENERATE PAYLOAD
        payload_content = BrainService.prepare_payload()
        
        # 2. CALL LLaMA 3.3 70B
        logger.info("📡 Analyzing with LLaMA 3.3 70B...")
        completion = client.chat.completions.create(
            messages=[{"role": "user", "content": payload_content}],
            model="llama-3.3-70b-versatile",
            temperature=0.1, # Lowest temp for math/logic adherence
            max_tokens=1024
        )
        
        response_text = completion.choices[0].message.content
        
        # 3. NOTIFY
        if response_text:
            print("\n" + "="*40 + "\n" + response_text + "\n" + "="*40)
            TelegramNotifier.send_alpha(response_text)
            logger.info("✅ Cycle Complete.")
            
    except Exception as e:
        logger.error(f"💥 Failure: {e}", exc_info=True)

if __name__ == "__main__":
    run_strategic_audit()