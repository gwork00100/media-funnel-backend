from fastapi import FastAPI
from pytrends.request import TrendReq
from agents.agent_runner import run_agent
import schedule
import threading
import time
import uvicorn
import os
import requests  # ← Add this if it wasn't already

app = FastAPI()

# ========== 🌐 ROUTES ==========

@app.get("/")
async def home():
    return {"message": "Media Funnel Agent is live!"}

@app.get("/health")
async def health_check():
    return {"status": "healthy"}

@app.get("/top-trending-products")
async def get_trending_searches():
    try:
        pytrends = TrendReq(hl='en-US', tz=360)
        try:
            trending_searches_df = pytrends.trending_searches(pn='united_states')
        except Exception:
            trending_searches_df = pytrends.trending_searches(pn='global')
        top_10 = trending_searches_df[0].head(10).tolist()
        return {"top_trending_searches": top_10}
    except Exception as e:
        return {"error": str(e)}

@app.get("/run")
async def run_now():
    output = run_agent()
    return {"agent_output": output}

# 👇 NEW ROUTE — send data to your n8n webhook
@app.get("/ping-n8n")
async def ping_n8n():
    data = {
        "source": "Fly.io",
        "message": "Webhook triggered!"
    }
    url = "https://313f39f3e215.ngrok-free.app/webhook-test/d18c086b-7a55-417d-81d3-fb08eb64610d"
    try:
        response = requests.post(url, json=data)
        return {
            "status_code": response.status_code,
            "response": response.text
        }
    except Exception as e:
        return {"error": str(e)}

# ========== 🕒 SCHEDULER ==========

def schedule_runner():
    schedule.every().day.at("09:00").do(run_agent)
    while True:
        schedule.run_pending()
        time.sleep(60)

# Start the scheduler in a daemon thread
scheduler_thread = threading.Thread(target=schedule_runner, daemon=True)
scheduler_thread.start()


# ========== 🚀 SERVER START ==========
# This is the new code that starts the server correctly on Replit.
if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=int(os.environ.get("PORT", 8000)))
