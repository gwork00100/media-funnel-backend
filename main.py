import logging
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.interval import IntervalTrigger
from pytrends.request import TrendReq
from cachetools import TTLCache
from pydantic import BaseModel

# Initialize FastAPI app
app = FastAPI()

# CORS setup
app.add_middleware(
    CORSMiddleware,
    allow_origins=["https://gwork00100.github.io"],  # Adjust as needed
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Configure logging
logging.basicConfig(level=logging.INFO)

# Cache with TTL of 24 hours
cache = TTLCache(maxsize=1, ttl=86400)
CACHE_KEY = "trends_data"


def fetch_trends():
    logging.info("Starting fetch_trends function.")
    try:
        pytrends = TrendReq(hl='en-US', tz=360, retries=3, backoff_factor=0.5, timeout=(10, 25))
        keywords = ['python']
        logging.info(f"Building payload for keywords: {keywords}")

        # Use interest_over_time() for simpler data fetch test
        pytrends.build_payload(kw_list=keywords, timeframe='now 7-d', geo='US')
        df = pytrends.interest_over_time()

        if df is None or df.empty:
            logging.error("No interest_over_time data received from pytrends")
            return

        # Convert DataFrame to list of dicts for JSON serialization
        data = df.reset_index().to_dict(orient='records')
        cache[CACHE_KEY] = data
        logging.info("Trends interest_over_time data cached successfully.")

    except Exception as e:
        logging.error(f"Exception in fetch_trends: {e}")


# Schedule fetch_trends every 3 hours
scheduler = BackgroundScheduler()
scheduler.add_job(fetch_trends, IntervalTrigger(hours=3))
scheduler.start()


# Pydantic model for POST /score-trend
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
def refresh_trends():
    logging.info(">>> /refresh-trends called")
    fetch_trends()  # run synchronously
    logging.info(">>> fetch_trends finished")
    return {"message": "Trends refresh executed synchronously"}


@app.get("/aggregate-trends")
async def aggregate_trends_endpoint(q: str = "Python"):
    keywords = [k.strip() for k in q.split(",")] if "," in q else [q]
    # Dummy aggregator response
    results = {"dummy": "aggregated data for " + ", ".join(keywords)}
    return {"query": keywords, "results": results}


@app.post("/score-trend")
async def score_trend_endpoint(request: TrendRequest):
    if not request.topic or not request.topic.strip():
        raise HTTPException(status_code=400, detail="Topic is required")
    # Dummy scoring logic
    result = {"score": 42}
    return {
        "topic": request.topic,
        "scores": result
    }
