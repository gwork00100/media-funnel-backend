from langchain.agents import tool

@tool
def fetch_trends():
    """Fetch top trends from multiple sources."""
    return ["AI Music", "Eco Fashion", "Space Tourism"]

@tool
def score_trends(trends: list):
    """Score and prioritize trends."""
    return sorted(trends)

@tool
def generate_content(trend: str):
    """Generate social media content."""
    return f"🔥 Trending Now: {trend}! Don't miss what's next in {trend.lower()}."
