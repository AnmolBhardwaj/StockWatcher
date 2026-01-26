# scripts/test_telegram.py
import os
import requests
import logging
from dotenv import load_dotenv

load_dotenv() # Load local .env file

TOKEN = "8487210336:AAH0M21i4SwqF4F1O88fuCwRsPybyFqDwAg"
# Note: For private chats, Chat ID is a positive integer. 
# For Channels/Groups, it usually starts with -100.
CHAT_ID = "6665325033"

def verify_connection():
    # 1. First, check if the Token is even valid
    print(f"📡 Testing Token: {TOKEN[:10]}...")
    url_me = f"https://api.telegram.org/bot{TOKEN}/getMe"
    try:
        res = requests.get(url_me).json()
        if not res.get("ok"):
            print("❌ TOKEN INVALID: BotFather token is wrong.")
            return
        print(f"✅ TOKEN VALID: Bot Name is @{res['result']['username']}")

        # 2. Check for recent updates to find your ACTUAL Chat ID
        print("📡 Fetching latest updates to find Chat ID...")
        url_updates = f"https://api.telegram.org/bot{TOKEN}/getUpdates"
        updates = requests.get(url_updates).json()
        
        if not updates.get("result"):
            print("⚠️ NO UPDATES FOUND: Send a message to your bot on Telegram FIRST, then run this again.")
            return

        # Extract the last Chat ID that interacted with the bot
        latest_chat = updates["result"][-1]["message"]["chat"]
        print(f"🎯 FOUND CHAT ID: {latest_chat['id']} ({latest_chat.get('username', 'Private Group')})")
        print(f"👉 Use this ID in your .env and GitHub Secrets!")

        # 3. Try sending a test message
        print(f"📡 Sending test message to {CHAT_ID}...")
        url_send = f"https://api.telegram.org/bot{TOKEN}/sendMessage"
        payload = {"chat_id": CHAT_ID, "text": """
                   <b>📊 Strategic Sector Audit</b>

<b>Market Status:</b> <i>OPEN</i>

<b>Top Sectors</b>
• <b>IT</b> — +1.24%
• <b>Banking</b> — +0.87%
• <b>Energy</b> — -0.42%

<b>Key News</b>
<a href="https://example.com">RBI policy update impacts banks</a>

<b>Signal:</b>
🟢 <b>ACCUMULATE</b>

<code>Updated at: 09:45 IST</code>

                   """,
                   "parse_mode":"HTML"}
        
        send_res = requests.post(url_send, data=payload)
        send_res.raise_for_status()
        print("🎉 SUCCESS: Message delivered!")

    except Exception as e:
        print(f"💥 FAILED: {e}")

if __name__ == "__main__":
    verify_connection()