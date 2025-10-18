import logging
from fastapi import FastAPI, BackgroundTasks, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.interval import IntervalTrigger
from pytrends.request import TrendReq
from cachetools import TTLCache
from trends.aggregator import aggregate_trends  # Your aggregator import

# Create the app
app = FastAPI()

# Set up CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["https://gwork00100.github.io"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Logging
logging.basicConfig(level=logging.INFO)

# In-memory cache with TTL (24 hours = 86400 seconds)
cache = TTLCache(maxsize=1, ttl=86400)
CACHE_KEY = 'trends_data'

def fetch_trends():
    logging.info("Starting fetch_trends function.")
    pytrends = TrendReq(hl='en-US', tz=360)
    
    try:
        keywords = ['Python']
        logging.info("Building payload for keywords.")
        pytrends.build_payload(kw_list=keywords, timeframe='today 1-d', geo='US')

        logging.info("Fetching related topics.")
        trends = pytrends.related_topics()

        if trends is None:
            raise ValueError("Received None instead of trends data")

        json_trends = {}
        for key, value in trends.items():
            if value is not None:
                json_trends[key] = {k: v.to_dict(orient='records') for k, v in value.items()}
            else:
                json_trends[key] = None
        
        cache[CACHE_KEY] = json_trends
        logging.info("Trends data fetched and cached successfully.")

    except Exception as e:
        logging.error(f"Exception in fetch_trends: {e}")

# Schedule background job
scheduler = BackgroundScheduler()
scheduler.add_job(fetch_trends, IntervalTrigger(hours=3))
scheduler.start()

# Routes

@app.get("/")
def home():
    return {"message": "Welcome to Google Trends API (FastAPI version)"}

@app.get("/daily-trends")
def daily_trends():
    data = cache.get(CACHE_KEY)
    if not data:
        return {"error": "No trends data available yet."}
    return data

@app.get("/refresh-trends")
def refresh_trends(background_tasks: BackgroundTasks):
    background_tasks.add_task(fetch_trends)
    return {"message": "Trends refresh triggered in background"}

# New aggregator endpoint
@app.get("/aggregate-trends")
async def aggregate_trends_endpoint(q: str = "Python"):
    keywords = [k.strip() for k in q.split(",")] if "," in q else [q]
    try:
        results = await aggregate_trends()  # currently no keywords param; dummy data
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error fetching aggregated trends: {e}")

    if not results:
        raise HTTPException(status_code=503, detail="No data returned from any source")

    return {"query": keywords, "results": results}
