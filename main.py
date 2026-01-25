# main.py
import os
import logging
from groq import Groq
from scripts.brain import BrainService
from scripts.notifier import TelegramNotifier # NEW IMPORT

# High-Density Logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("StrategicWatcher_Groq")
formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - [BLUNT_COEFF: HIGH] - %(message)s')
handler = logging.StreamHandler()
handler.setFormatter(formatter)
if not logger.handlers:
    logger.addHandler(handler)

def run_strategic_audit():
    logger.info("🎬 [SYSTEM START] Starting Groq-Powered Strategic Audit Cycle...")
    
    # 1. API Authentication Audit
    api_key = os.getenv("GROQ_API_KEY")
    if not api_key:
        logger.critical("🚫 MISSING API KEY: Ensure GROQ_API_KEY is set in environment variables.")
        return

    try:
        # 2. Initialize Groq Client
        client = Groq(api_key=api_key)
        
        # 3. Data Aggregation (From Brain Service)
        logger.info("🧠 Fetching compiled context from BrainService...")
        payload_content = BrainService.prepare_payload()
        
        # 4. Transmit to LLaMA 3.3 70B (Groq Production Model)
        logger.info("📡 Transmitting payload to Groq (llama-3.3-70b-versatile)...")
        
        chat_completion = client.chat.completions.create(
            messages=[
                {
                    "role": "user",
                    "content": payload_content,
                }
            ],
            model="llama-3.3-70b-versatile", # Latest stable 70B model on Groq
            temperature=0.2, # Low temperature for logical consistency in finance
            max_tokens=1024,
            stream=False
        )
        
        # 5. Result Extraction & Output
        response_text = chat_completion.choices[0].message.content
        
        if response_text:
            logger.info("📥 Audit Response Received Successfully from Groq.")
            print("\n" + "="*50)
            print("🚀 GROQ STRATEGIC ALPHA REPORT (LLaMA 3.3 70B)")
            print("="*50)
            print(response_text)
            print("="*50 + "\n")

            # SEND TO TELEGRAM
            notified = TelegramNotifier.send_alpha(response_text)
            if notified:
                print("✨ Report delivered to phone.")
            else:
                print("⚠️ Report generated but delivery failed.")
                
            print("\n--- REPORT PREVIEW ---\n", response_text)
        else:
            logger.warning("⚠️ Groq returned an empty response. Verify JSON formatting in BrainService.")

    except Exception as e:
        logger.error(f"💥 CRITICAL FAILURE in Groq Audit Cycle: {str(e)}", exc_info=True)

if __name__ == "__main__":
    run_strategic_audit()