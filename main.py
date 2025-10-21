import os
import logging
from fastapi import FastAPI, Request, HTTPException, Body
from fastapi.middleware.cors import CORSMiddleware
from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.interval import IntervalTrigger
from pytrends.request import TrendReq
from cachetools import TTLCache
import httpx
from pydantic import BaseModel

# Initialize FastAPI app
app = FastAPI()

# CORS setup — adjust origin as needed
app.add_middleware(
    CORSMiddleware,
    allow_origins=["https://gwork00100.github.io"],  # Change to your frontend URL
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Configure logging
logging.basicConfig(level=logging.INFO)

# Cache setup: max 1 item, TTL 24 hours
cache = TTLCache(maxsize=1, ttl=86400)
CACHE_KEY = "trends_data"

# API Keys and URLs from env or defaults
API_KEY = os.getenv("API_KEY", "supersecretkey")
OLLAMA_URL = os.getenv("OLLAMA_URL", "http://localhost:11434/api/generate")

# Scheduler setup
scheduler = BackgroundScheduler()

def fetch_trends():
    logging.info("Starting fetch_trends function.")
    try:
        pytrends = TrendReq(hl='en-US', tz=360, retries=3, backoff_factor=0.5, timeout=(10, 25))
        keywords = ['python']
        logging.info(f"Building payload for keywords: {keywords}")

        pytrends.build_payload(kw_list=keywords, timeframe='now 7-d', geo='US')
        df = pytrends.interest_over_time()

        if df is None or df.empty:
            logging.error("No interest_over_time data received from pytrends")
            return

        data = df.reset_index().to_dict(orient='records')
        cache[CACHE_KEY] = data
        logging.info("Trends interest_over_time data cached successfully.")

    except Exception as e:
        logging.error(f"Exception in fetch_trends: {e}")

# Schedule the job every 3 hours
scheduler.add_job(fetch_trends, IntervalTrigger(hours=3))
scheduler.start()

# Pydantic model for /score-trend POST body
class TrendRequest(BaseModel):
    topic: str

# --- API endpoints ---

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
    fetch_trends()  # Run synchronously on demand
    logging.info(">>> fetch_trends finished")
    return {"message": "Trends refresh executed synchronously"}

@app.get("/aggregate-trends")
async def aggregate_trends_endpoint(q: str = "Python"):
    keywords = [k.strip() for k in q.split(",")] if "," in q else [q]
    # Dummy aggregator response
    results = {"dummy": "aggregated data for " + ", ".join(keywords)}
    return {"query": keywords, "results": results}

@app.post("/score-trend")
async def score_trend_endpoint(request: Request, trend_request: TrendRequest):
    auth_header = request.headers.get("Authorization")
    if auth_header != f"Bearer {API_KEY}":
        raise HTTPException(status_code=401, detail="Unauthorized")

    if not trend_request.topic or not trend_request.topic.strip():
        raise HTTPException(status_code=400, detail="Topic is required")

    # Dummy scoring logic (replace with your real logic)
    result = {"score": 42}
    return {
        "topic": trend_request.topic,
        "scores": result
    }

@app.get("/health")
async def health_check():
    return {"status": "ok"}

@app.post("/chat")
async def chat(request: Request, body: dict = Body(...)):
    # Authorization check
    auth_header = request.headers.get("Authorization")
    if auth_header != f"Bearer {API_KEY}":
        raise HTTPException(status_code=401, detail="Unauthorized")

    prompt = body.get("prompt")
    if not prompt:
        raise HTTPException(status_code=400, detail="Prompt is required")

    try:
        async with httpx.AsyncClient() as client:
            resp = await client.post(
                OLLAMA_URL,
                json={
                    "model": "llama2",  # Use llama2 since mistral is not available
                    "prompt": prompt,
                    "stream": False,
                },
                timeout=15.0,
            )
        if resp.status_code != 200:
            logging.error(f"Ollama request failed with status {resp.status_code}: {resp.text}")
            raise HTTPException(status_code=resp.status_code, detail="Ollama request failed")

        return resp.json()

    except httpx.RequestError as e:
        logging.error(f"Ollama service unavailable: {str(e)}")
        raise HTTPException(status_code=503, detail=f"Ollama service unavailable: {str(e)}")
