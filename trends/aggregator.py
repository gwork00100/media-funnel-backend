import asyncio
import time
from typing import List, Dict, Any
from functools import lru_cache
import aiohttp

# ========== CONFIG ==========
CACHE_EXPIRY_SECONDS = 300  # 5 minutes
THROTTLE_DELAY = 1.5  # seconds between calls to prevent rate-limiting

# ========== CACHE ==========
_cache: Dict[str, Dict[str, Any]] = {}

def is_cache_valid(source: str) -> bool:
    return source in _cache and (time.time() - _cache[source]["timestamp"] < CACHE_EXPIRY_SECONDS)

def get_cached(source: str) -> Any:
    return _cache[source]["data"]

def set_cache(source: str, data: Any):
    _cache[source] = {"data": data, "timestamp": time.time()}

# ========== ADAPTERS ==========

# ✅ Google Custom Search
async def fetch_google_trends(session):
    # Placeholder – replace with actual API call using your credentials
    await asyncio.sleep(THROTTLE_DELAY)
    return {"source": "Google", "trends": ["Example Google Trend 1", "Example Google Trend 2"]}

# ✅ YouTube Trends
async def fetch_youtube_trends(session):
    await asyncio.sleep(THROTTLE_DELAY)
    return {"source": "YouTube", "trends": ["Trending Video 1", "Trending Video 2"]}

# ✅ Reddit Trends
async def fetch_reddit_trends(session):
    await asyncio.sleep(THROTTLE_DELAY)
    return {"source": "Reddit", "trends": ["r/AskReddit", "r/worldnews"]}

# ✅ Bing Trends
async def fetch_bing_trends(session):
    await asyncio.sleep(THROTTLE_DELAY)
    return {"source": "Bing", "trends": ["Bing Trend 1", "Bing Trend 2"]}

# ✅ Yahoo Trends
async def fetch_yahoo_trends(session):
    await asyncio.sleep(THROTTLE_DELAY)
    return {"source": "Yahoo", "trends": ["Yahoo Trend 1", "Yahoo Trend 2"]}

# ✅ Twitter (X) Trends
async def fetch_twitter_trends(session):
    await asyncio.sleep(THROTTLE_DELAY)
    return {"source": "Twitter", "trends": ["#TrendingOnX", "#News"]}

# ✅ Amazon Trends
async def fetch_amazon_trends(session):
    await asyncio.sleep(THROTTLE_DELAY)
    return {"source": "Amazon", "trends": ["Top Selling Product 1", "Top Product 2"]}

# ✅ PyTrends Fallback
async def fetch_pytrends(session):
    await asyncio.sleep(THROTTLE_DELAY)
    return {"source": "PyTrends", "trends": ["Fallback Trend A", "Fallback Trend B"]}

# ========== AGGREGATOR FUNCTION ==========

async def aggregate_trends() -> List[Dict[str, Any]]:
    sources = {
        "google": fetch_google_trends,
        "youtube": fetch_youtube_trends,
        "reddit": fetch_reddit_trends,
        "bing": fetch_bing_trends,
        "yahoo": fetch_yahoo_trends,
        "twitter": fetch_twitter_trends,
        "amazon": fetch_amazon_trends,
        "pytrends": fetch_pytrends,
    }

    results = []

    async with aiohttp.ClientSession() as session:
        tasks = []
        for name, fetch_func in sources.items():
            if is_cache_valid(name):
                results.append(get_cached(name))
            else:
                tasks.append((name, fetch_func(session)))

        fetched = await asyncio.gather(
            *[func for _, func in tasks],
            return_exceptions=True
        )

        for (name, _), data in zip(tasks, fetched):
            if isinstance(data, Exception):
                print(f"[ERROR] Failed to fetch from {name}: {data}")
            else:
                set_cache(name, data)
                results.append(data)

    return results
