from langchain_core.tools import tool
from pytrends.request import TrendReq
import time
import json

@tool
def fetch_google_trends(input_str: str) -> str:
    """
    Fetches top 10 trending searches for a given region and summarizes interest.
    input_str is a JSON string like: {"region": "united_states"}
    """
    data = json.loads(input_str)
    region = data.get("region", "united_states")

    pytrends = TrendReq(hl='en-US', tz=360)
    time.sleep(2)

    try:
        trending_searches = pytrends.trending_searches(pn=region)
    except Exception as e:
        return f"Failed to fetch trending searches: {e}"

    top_trends = trending_searches.head(10)[0].tolist()
    return "Top 10 trending searches:\n" + "\n".join(f"{i+1}. {trend}" for i, trend in enumerate(top_trends))
