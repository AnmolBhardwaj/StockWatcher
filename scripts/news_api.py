# scripts/news_api.py
import feedparser
import json
import os
import logging
from datetime import datetime

# High-Density Logging Setup
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("NewsWatcher_API")
formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - [BLUNT_COEFF: HIGH] - %(message)s')
handler = logging.StreamHandler()
handler.setFormatter(formatter)
if not logger.handlers:
    logger.addHandler(handler)

class NewsService:
    # Portfolio Manager's Curated Feeds
    FEEDS = {
        "Moneycontrol_Business": "https://www.moneycontrol.com/rss/business.xml",
        "ET_Defence": "https://b2b.economictimes.indiatimes.com/rss/defence",
        "ET_Energy": "https://energy.economictimes.indiatimes.com/rss/power",
        # Synthetic Feed for Nuclear Regulatory tracking (AERB, NPCIL, SMR)
        "Nuclear_Strategic": "https://news.google.com/rss/search?q=Nuclear+Power+India+SMR+AERB+SHANTI+Bill&hl=en-IN&gl=IN&ceid=IN:en"
    }
    
    TICKERS = ["BHEL", "MTARTECH", "WALCHANNAG", "LT", "NTPC"]
    
    # Nuclear specific keywords based on your Watchlist Category
    NUCLEAR_KEYWORDS = [
        "NUCLEAR", "SMR", "SMALL MODULAR REACTOR", "AERB", "NPCIL", 
        "SHANTI BILL", "ATOMIC ENERGY", "TENDER", "KUDANKULAM", "KAIGA"
    ]
    
    DATA_FILE = "data/news_list.json"

    @classmethod
    def fetch_and_filter(cls):
        logger.info("🔍 [TASK: NEWS AGGREGATION] Initiating scan for Portfolio Tickers and Nuclear updates...")
        
        existing_news = cls._load_storage()
        # Track links to prevent duplicates
        seen_links = {item['link'] for item in existing_news}
        new_stories_count = 0

        for source_name, url in cls.FEEDS.items():
            logger.info(f"📡 Polling {source_name}...")
            try:
                feed = feedparser.parse(url)
                if not feed.entries:
                    logger.warning(f"⚠️ Feed {source_name} returned 0 entries. Check URL connectivity.")
                
                for entry in feed.entries:
                    title = entry.title.upper()
                    summary = entry.get('summary', '').upper()
                    
                    # Logic: Match specific tickers OR nuclear keywords OR high-impact sector words
                    is_ticker_match = any(t in title for t in cls.TICKERS)
                    is_nuclear_match = any(nk in title for nk in cls.NUCLEAR_KEYWORDS)
                    is_sector_impact = any(kw in title for kw in ["DEFENCE", "INFRA", "POWER", "ORDER", "CONTRACT"])

                    if (is_ticker_match or is_nuclear_match or is_sector_impact) and entry.link not in seen_links:
                        # Determine category for LLM prioritization
                        category = "NUCLEAR" if is_nuclear_match else "CORPORATE"
                        
                        news_item = {
                            "source": source_name,
                            "category": category,
                            "title": entry.title,
                            "link": entry.link,
                            "published": entry.get('published', datetime.now().strftime('%Y-%m-%d %H:%M')),
                            "timestamp_fetched": datetime.now().isoformat(),
                            "relevance": "High" if (is_ticker_match or is_nuclear_match) else "Sector"
                        }
                        existing_news.append(news_item)
                        seen_links.add(entry.link)
                        new_stories_count += 1
                        logger.info(f"📰 [{category}] Match Found: {entry.title[:60]}...")

            except Exception as e:
                logger.error(f"❌ Failed to parse {source_name}: {str(e)}", exc_info=True)

        # Technical Debt Pruning: Maintain a rolling buffer to keep JSON manageable for LLM context window
        if len(existing_news) > 80:
            logger.info("🧹 Pruning news_list.json (Keeping last 80 high-relevance items).")
            existing_news = existing_news[-80:]

        cls._save_storage(existing_news)
        logger.info(f"✅ News Cycle Complete. Added {new_stories_count} new strategic stories.")

    @classmethod
    def _load_storage(cls):
        if not os.path.exists(cls.DATA_FILE):
            logger.info(f"📁 Creating new storage at {cls.DATA_FILE}")
            os.makedirs(os.path.dirname(cls.DATA_FILE), exist_ok=True)
            return []
        try:
            with open(cls.DATA_FILE, 'r') as f:
                return json.load(f)
        except Exception as e:
            logger.error(f"⚠️ Corruption detected in News JSON: {e}")
            return []

    @classmethod
    def _save_storage(cls, data):
        try:
            with open(cls.DATA_FILE, 'w') as f:
                json.dump(data, f, indent=2)
            logger.debug(f"💾 Storage synced: {len(data)} items currently tracked.")
        except Exception as e:
            logger.critical(f"🚫 IO ERROR: Failed to write to {cls.DATA_FILE}: {e}")

if __name__ == "__main__":
    NewsService.fetch_and_filter()