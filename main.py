import logging
from fastapi import FastAPI, BackgroundTasks, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.interval import IntervalTrigger
from pytrends.request import TrendReq
from cachetools import TTLCache
from trends.aggregator import aggregate_trends  # Your aggregator import
from pydantic import BaseModel
from agents.scorer import score_trend

# Create the FastAPI app
app = FastAPI()

# Setup CORS middleware to allow your frontend origin
app.add_middleware(
    CORSMiddleware,
    allow_origins=["https://gwork00100.github.io"],  # change if needed
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Configure logging
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

# Schedule fetch_trends to run every 3 hours
scheduler = BackgroundScheduler()
scheduler.add_job(fetch_trends, IntervalTrigger(hours=3))
scheduler.start()

# Pydantic model for POST /score-trend request body
class TrendRequest(BaseModel):
    topic: str

# API endpoints

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

@app.get("/aggregate-trends")
async def aggregate_trends_endpoint(q: str = "Python"):
    keywords = [k.strip() for k in q.split(",")] if "," in q else [q]
    try:
        results = await aggregate_trends()  # assuming aggregate_trends is async and returns dummy data
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error fetching aggregated trends: {e}")

    if not results:
        raise HTTPException(status_code=503, detail="No data returned from any source")

    return {"query": keywords, "results": results}

@app.post("/score-trend")
async def score_trend_endpoint(request: TrendRequest):
    if not request.topic or not request.topic.strip():
        raise HTTPException(status_code=400, detail="Topic is required")
    result = score_trend(request.topic.strip())
    return {
        "topic": request.topic,
        "scores": result
    }
