from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from agents.scorer import score_trend

app = FastAPI()

class TrendRequest(BaseModel):
    topic: str

@app.post("/score-trend")
async def score_trend_endpoint(request: TrendRequest):
    if not request.topic or not request.topic.strip():
        raise HTTPException(status_code=400, detail="Topic is required")
    result = score_trend(request.topic.strip())
    return {
        "topic": request.topic,
        "scores": result
    }
