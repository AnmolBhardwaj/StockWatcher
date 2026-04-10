# scripts/news_api.py
import feedparser
import json
import os
import logging
from datetime import datetime

# High-Density Logging Setup
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("NewsWatcher_API")
formatter = logging.Formatter('%(asctime)s - [BLUNT_COEFF: HIGH] - %(message)s')
handler = logging.StreamHandler()
handler.setFormatter(formatter)
if not logger.handlers:
    logger.addHandler(handler)

class NewsService:
    # Portfolio Manager's Curated Feeds (High-Signal Sources)
    FEEDS = {
        "PIB_Defence": "https://pib.gov.in/RssMain.aspx?ModId=6&Lang=1&Regid=3",
        "AERB_Regulatory": "https://www.aerb.gov.in/english/news1?format=feed&type=rss",
        "Nuclear_Strategic": "https://news.google.com/rss/search?q=Nuclear+Power+India+SMR+SHANTI+Act+NPCIL+BHEL+MTAR&hl=en-IN&gl=IN&ceid=IN:en",
        "Moneycontrol_Business": "https://www.moneycontrol.com/rss/business.xml"
    }
    
    TICKERS = ["BHEL", "MTARTECH", "WALCHANNAG", "LT", "NTPC", "JIOFINANCIALS", "MOTHERSUMI", "MSUMI"]
    
    # Keyword Weights for Relevance Scoring
    # Ticker Match: 5pts | High-Impact (Order/Contract): 4pts | Nuclear Context: 3pts
    IMPACT_KEYWORDS = ["ORDER", "CONTRACT", "TENDER", "L1", "MOU", "WIN"]
    NUCLEAR_KEYWORDS = ["SMR", "AERB", "NPCIL", "KUDANKULAM", "FAC", "CRITICALITY"]
    
    # NEW: Macro Event Keywords for Sniper Triggers
    MACRO_KEYWORDS = {
        "FEDERAL_RESERVE": ["FEDERAL RESERVE", "FED RATE", "INTEREST RATE DECISION", "FOMC"],
        "RBI_POLICY": ["RBI POLICY", "MONETARY POLICY", "REPO RATE", "RBI DECISION"],
        "GEOPOLITICAL": ["UKRAINE", "RUSSIA", "CHINA", "SANCTION", "GEOPOLITICAL", "TRADE WAR"],
        "INFLATION": ["INFLATION", "CPI", "DEFLATION", "PRICE SURGE"]
    }
    
    DATA_FILE = "data/news_list.json"

    @classmethod
    def _detect_macro_trigger(cls, title):
        """Detect if article contains macro event trigger. Returns trigger_type or None."""
        title_upper = title.upper()
        for trigger_type, keywords in cls.MACRO_KEYWORDS.items():
            if any(kw in title_upper for kw in keywords):
                return trigger_type
        return None

    @classmethod
    def fetch_and_filter(cls):
        logger.info("🔍 [TASK: NEWS AGGREGATION] Scanning for Order Wins, Macro Events, and Policy Shifts...")
        
        existing_news = cls._load_storage()
        seen_links = {item['link'] for item in existing_news}
        new_stories_count = 0

        for source_name, url in cls.FEEDS.items():
            try:
                feed = feedparser.parse(url)
                for entry in feed.entries:
                    title = entry.title.upper()
                    
                    # 1. Scoring Logic
                    score = 0
                    is_ticker_match = any(t in title for t in cls.TICKERS)
                    is_nuclear_match = any(nk in title for nk in cls.NUCLEAR_KEYWORDS)
                    is_impact_match = any(ik in title for ik in cls.IMPACT_KEYWORDS)
                    macro_trigger = cls._detect_macro_trigger(title)

                    if is_ticker_match: score += 5
                    if is_impact_match: score += 4
                    if is_nuclear_match: score += 4 # Upgraded from 3 to 4
                    if macro_trigger: score += 3  # Macro triggers get bonus points

                    # 2. Strategic Threshold
                    # ALLOW if: Direct Ticker news (>=5) OR high-impact Nuclear news (>=4) OR Macro event (>=3)
                    if (score >= 3) and entry.link not in seen_links:
                        # Determine category based on trigger type
                        if macro_trigger:
                            category = f"MACRO_TRIGGER_{macro_trigger}"
                        elif is_ticker_match and is_impact_match:
                            category = "ORDER_WIN"
                        else:
                            category = "STRATEGIC"
                        
                        news_item = {
                            "source": source_name,
                            "category": category,
                            "title": entry.title,
                            "link": entry.link,
                            "published": entry.get('published', datetime.now().strftime('%Y-%m-%d %H:%M')),
                            "relevance_score": score,
                            "is_critical": score >= 9, # Flag for immediate Brain attention
                            "macro_trigger_type": macro_trigger  # NEW: Track macro type for sniper
                        }
                        existing_news.append(news_item)
                        seen_links.add(entry.link)
                        new_stories_count += 1
                        logger.info(f"📰 [{category}] Score {score}: {entry.title[:60]}...")

            except Exception as e:
                logger.error("❌ Failed to parse %s: %s", source_name, type(e).__name__)

        # Technical Debt Pruning: Keep top 80, but SORT by relevance before slicing
        existing_news = sorted(existing_news, key=lambda x: x.get('relevance_score', 0), reverse=True)
        if len(existing_news) > 80:
            logger.info("🧹 Pruning: Retaining top 80 highest-relevance items.")
            existing_news = existing_news[:80]

        cls._save_storage(existing_news)
        logger.info(f"✅ News Cycle Complete. Added {new_stories_count} strategic stories.")

    @classmethod
    def _load_storage(cls):
        if not os.path.exists(cls.DATA_FILE):
            os.makedirs(os.path.dirname(cls.DATA_FILE), exist_ok=True)
            return []
        with open(cls.DATA_FILE, 'r') as f: return json.load(f)

    @classmethod
    def _save_storage(cls, data):
        with open(cls.DATA_FILE, 'w') as f: json.dump(data, f, indent=2)

if __name__ == "__main__":
    NewsService.fetch_and_filter()