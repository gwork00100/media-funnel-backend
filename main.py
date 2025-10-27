# main.py
from dotenv import load_dotenv
import os
import logging
from fastapi import FastAPI, Request, HTTPException, Body, Query
from fastapi.middleware.cors import CORSMiddleware
from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.interval import IntervalTrigger
from pytrends.request import TrendReq
from cachetools import TTLCache
import httpx
from pydantic import BaseModel
from supabase import create_client, Client

# Load environment variables
load_dotenv()

# Logging
logging.basicConfig(level=logging.INFO)

# Initialize FastAPI app
app = FastAPI(title="Google Trends + Supabase API + Ollama Chat")

# CORS setup
app.add_middleware(
    CORSMiddleware,
    allow_origins=["https://gwork00100.github.io"],  # frontend URL
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Cache setup (24 hours)
cache = TTLCache(maxsize=1, ttl=86400)
CACHE_KEY = "trends_data"

# Environment variables
API_KEY = os.getenv("API_KEY")
OLLAMA_URL = os.getenv("OLLAMA_URL", "http://127.0.0.1:11434/v1/chat")
GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY")
CUSTOM_SEARCH_ENGINE_ID = os.getenv("CUSTOM_SEARCH_ENGINE_ID")
SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")

# Validate required env variables
required_env = {
    "SUPABASE_URL": SUPABASE_URL,
    "SUPABASE_KEY": SUPABASE_KEY,
    "GOOGLE_API_KEY": GOOGLE_API_KEY,
    "CUSTOM_SEARCH_ENGINE_ID": CUSTOM_SEARCH_ENGINE_ID,
    "API_KEY": API_KEY,
}
missing = [k for k, v in required_env.items() if not v]
if missing:
    raise RuntimeError(f"Missing required environment variables: {', '.join(missing)}")

# Supabase client
supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

# Scheduler
scheduler = BackgroundScheduler()

# Fetch Google Trends function
def fetch_trends():
    logging.info("Starting fetch_trends job...")
    try:
        pytrends = TrendReq(hl="en-US", tz=360)
        keywords = ["python"]
        pytrends.build_payload(kw_list=keywords, timeframe="now 7-d", geo="US")
        df = pytrends.interest_over_time()

        if df.empty:
            logging.warning("No trend data received.")
            return

        data = df.reset_index().to_dict(orient="records")
        cache[CACHE_KEY] = data
        logging.info("Trends data cached successfully.")

        # Insert into Supabase
        for record in data:
            supabase.table("trends").insert({
                "keyword": "python",
                "interest": record.get("python", 0),
                "fetched_at": record.get("date")
            }).execute()
        logging.info("Trends inserted into Supabase successfully.")

    except Exception as e:
        logging.error(f"Error in fetch_trends: {e}")

# Schedule fetch_trends every 3 hours
scheduler.add_job(fetch_trends, IntervalTrigger(hours=3))
scheduler.start()

# Pydantic model for chat/trend requests
class TrendRequest(BaseModel):
    topic: str

# Routes
@app.get("/")
def home():
    return {"message": "API running successfully"}

@app.get("/health")
def health():
    return {"status": "ok"}

@app.get("/daily-trends")
def daily_trends():
    try:
        result = supabase.table("trends").select("*").order("fetched_at", desc=True).limit(10).execute()
        return {"trends": result.data or []}
    except Exception as e:
        logging.error(e)
        raise HTTPException(status_code=500, detail="Failed to fetch trends.")

@app.get("/refresh-trends")
def refresh_trends():
    fetch_trends()
    return {"message": "Trends refreshed manually"}

@app.post("/score-trend")
async def score_trend(request: Request, trend_request: TrendRequest):
    if request.headers.get("Authorization") != f"Bearer {API_KEY}":
        raise HTTPException(status_code=401, detail="Unauthorized")
    # Placeholder logic for scoring
    return {"topic": trend_request.topic, "score": 42}

@app.get("/google-search")
async def google_search(q: str = Query(..., description="Search query")):
    url = "https://www.googleapis.com/customsearch/v1"
    params = {"key": GOOGLE_API_KEY, "cx": CUSTOM_SEARCH_ENGINE_ID, "q": q}
    async with httpx.AsyncClient() as client:
        resp = await client.get(url, params=params, timeout=10.0)
    if resp.status_code != 200:
        raise HTTPException(status_code=resp.status_code, detail="Google API error")
    data = resp.json()
    items = data.get("items", [])
    return {"query": q, "results": [{"title": i.get("title"), "link": i.get("link"), "snippet": i.get("snippet")} for i in items]}

@app.post("/chat")
async def chat(request: Request, body: dict = Body(...)):
    if request.headers.get("Authorization") != f"Bearer {API_KEY}":
        raise HTTPException(status_code=401, detail="Unauthorized")
    
    prompt = body.get("prompt")
    if not prompt:
        raise HTTPException(status_code=400, detail="Prompt required")

    async with httpx.AsyncClient() as client:
        try:
            resp = await client.post(
                OLLAMA_URL,
                json={
                    "model": "llama2",
                    "messages": [{"role": "user", "content": prompt}],
                    "stream": False
                },
                timeout=30.0,
            )
            resp.raise_for_status()
        except httpx.RequestError as e:
            raise HTTPException(status_code=503, detail=f"Ollama service unavailable: {e}")
        except httpx.HTTPStatusError as e:
            raise HTTPException(status_code=e.response.status_code, detail=f"Ollama API error: {e.response.text}")

    return resp.json()
