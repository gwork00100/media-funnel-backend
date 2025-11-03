#!/usr/bin/env python3
"""
Blood API: Central Data Store & Async Prompt Queue
Stores and exposes data from bones, nerves, and mind.
Supports /ask endpoint for asynchronous AI processing via Mind agent.
"""

import os
import asyncio
import logging
import json
from datetime import datetime
from fastapi import FastAPI, Request, HTTPException, Body, Query
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.interval import IntervalTrigger
from cachetools import TTLCache
from pytrends.request import TrendReq
from dotenv import load_dotenv

from utils.supabase_client import supabase
from utils.affiliate_links import get_affiliate_link
from queue_manager import enqueue_prompt, start_workers  # <- Async queue system

import httpx

# ---------------- Environment & Logging ----------------
load_dotenv()
logging.basicConfig(level=logging.INFO)

API_KEY = os.getenv("API_KEY")
OLLAMA_HOST = os.getenv("OLLAMA_HOST", "http://127.0.0.1:52683")
OLLAMA_URL = f"{OLLAMA_HOST}/v1/chat"
GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY")
CUSTOM_SEARCH_ENGINE_ID = os.getenv("CUSTOM_SEARCH_ENGINE_ID")

required_env = {
    "SUPABASE_URL": os.getenv("SUPABASE_URL"),
    "SUPABASE_KEY": os.getenv("SUPABASE_KEY"),
    "GOOGLE_API_KEY": GOOGLE_API_KEY,
    "CUSTOM_SEARCH_ENGINE_ID": CUSTOM_SEARCH_ENGINE_ID,
    "API_KEY": API_KEY,
}
missing = [k for k, v in required_env.items() if not v]
if missing:
    raise RuntimeError(f"Missing required environment variables: {', '.join(missing)}")

# ---------------- FastAPI app & CORS ----------------
app = FastAPI(title="Blood: Autonomous Trend Storage + API")
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Adjust to frontend URL if needed
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ---------------- Cache & Scheduler ----------------
cache = TTLCache(maxsize=1, ttl=86400)
CACHE_KEY = "trends_data"
scheduler = BackgroundScheduler()
scheduler.start()

# ---------------- Pydantic Models ----------------
class TrendRequest(BaseModel):
    topic: str

# ---------------- Trend Fetching ----------------
def fetch_trends():
    """Fetch Google Trends and store in Supabase & cache"""
    logging.info("📈 Fetching Google Trends...")
    try:
        pytrends = TrendReq(hl="en-US", tz=360)
        keywords = ["python", "fastapi", "AI", "trending"]  # Can be dynamic
        pytrends.build_payload(kw_list=keywords, timeframe="now 7-d", geo="US")
        df = pytrends.interest_over_time()
        if df.empty:
            logging.warning("No trend data received")
            return

        data = df.reset_index().to_dict(orient="records")
        cache[CACHE_KEY] = data
        logging.info("✅ Trends cached successfully")

        # Insert into Supabase
        for record in data:
            for keyword in keywords:
                supabase.table("trends").insert({
                    "keyword": keyword,
                    "interest": record.get(keyword, 0),
                    "fetched_at": record.get("date")
                }).execute()
        logging.info("✅ Trends inserted into Supabase")

    except Exception as e:
        logging.error(f"❌ Error in fetch_trends: {e}")

# Schedule every 3 hours
scheduler.add_job(fetch_trends, IntervalTrigger(hours=3))

# ---------------- Startup Event ----------------
@app.on_event("startup")
async def startup_event():
    loop = asyncio.get_event_loop()
    start_workers(loop=loop)
    logging.info("🩸 Blood API workers started.")

# ---------------- Routes ----------------
@app.get("/")
def home():
    return {"message": "Blood API running successfully"}

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
        raise HTTPException(status_code=500, detail="Failed to fetch trends")

@app.get("/refresh-trends")
def refresh_trends():
    fetch_trends()
    return {"message": "Trends refreshed manually"}

@app.post("/score-trend")
async def score_trend(request: Request, trend_request: TrendRequest):
    if request.headers.get("Authorization") != f"Bearer {API_KEY}":
        raise HTTPException(status_code=401, detail="Unauthorized")
    score = len(trend_request.topic) % 100  # Placeholder scoring
    return {"topic": trend_request.topic, "score": score}

@app.get("/google-search")
async def google_search(q: str = Query(...)):
    url = "https://www.googleapis.com/customsearch/v1"
    params = {"key": GOOGLE_API_KEY, "cx": CUSTOM_SEARCH_ENGINE_ID, "q": q}
    async with httpx.AsyncClient() as client:
        resp = await client.get(url, params=params, timeout=10)
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
        resp = await client.post(
            OLLAMA_URL,
            json={"model": "llama2:latest", "messages": [{"role": "user", "content": prompt}], "stream": False},
            timeout=30.0
        )
        resp.raise_for_status()
        return resp.json()

@app.post("/generate-link")
async def generate_link(request: Request):
    data = await request.json()
    link_id = data.get("link_id")
    source = data.get("source", "autoloop")
    medium = data.get("medium", "affiliate")
    campaign = data.get("campaign", "default")
    default_url = "https://your-default-affiliate.com"

    redirect_url = get_affiliate_link(link_id, default_url)
    if not redirect_url:
        raise HTTPException(status_code=404, detail="Affiliate link not found")

    if "?" in redirect_url:
        utm_link = f"{redirect_url}&utm_source={source}&utm_medium={medium}&utm_campaign={campaign}"
    else:
        utm_link = f"{redirect_url}?utm_source={source}&utm_medium={medium}&utm_campaign={campaign}"

    try:
        supabase.table("affiliate_clicks").insert({
            "link_id": link_id,
            "clicked_at": datetime.utcnow().isoformat(),
            "utm_source": source,
            "utm_medium": medium,
            "utm_campaign": campaign
        }).execute()
    except Exception as e:
        logging.error(f"❌ Error logging click: {e}")

    return {"redirectUrl": utm_link}

# ---------------- Local JSON storage ----------------
DATA_FILE = "trends_output.json"

@app.post("/api/update")
async def update_results(request: Request):
    body = await request.json()
    data = []
    if os.path.exists(DATA_FILE):
        with open(DATA_FILE, "r") as f:
            data = json.load(f)
    data.append(body)
    with open(DATA_FILE, "w") as f:
        json.dump(data, f, indent=2)
    return {"status": "✅ Stored successfully", "item": body}

@app.get("/api/results")
def get_results():
    if os.path.exists(DATA_FILE):
        with open(DATA_FILE) as f:
            return json.load(f)
    return {"message": "No data yet."}

# ---------------- Async /ask endpoint ----------------
@app.post("/ask")
async def ask(request: Request):
    data = await request.json()
    prompt = data.get("prompt")
    conversation_id = data.get("conversation_id", "default")
    
    if not prompt:
        raise HTTPException(status_code=400, detail="Prompt is required")
    
    try:
        answer = await enqueue_prompt(prompt, conversation_id)
        return {"answer": answer}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
