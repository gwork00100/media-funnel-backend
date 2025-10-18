from agents.google_trends_agent import fetch_google_trends as fetch_trends
from langchain_core.tools import tool
import json

@tool
def score_trends(input_str: str) -> str:
    """Scores the top 3 trends from a list of trend strings passed as JSON."""
    trends = json.loads(input_str)
    scored = [(trend, 0.9) for trend in trends[:3]]
    return json.dumps(scored)

@tool
def generate_content(input_str: str) -> str:
    """Generates content/posts based on scored trends in JSON format."""
    scored = json.loads(input_str)
    posts = [f"Post about {trend} (score: {score})" for trend, score in scored]
    return "\n".join(posts)

__all__ = ["fetch_trends", "score_trends", "generate_content"]
