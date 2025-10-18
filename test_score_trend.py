from dotenv import load_dotenv
import os

load_dotenv()  # Load variables from .env

openai_api_key = os.getenv("OPENAI_API_KEY")
print(f"Using OpenAI key: {openai_api_key[:5]}...")  # Only shows first 5 chars for safety



from agents.scorer import score_trend

# Sample trend input (customize if needed)
trend_data = {
    "title": "AI in video editing is growing fast",
    "summary": "AI tools are revolutionizing how creators produce and edit videos.",
    "source": "Reddit"
}

# Call your scoring function
result = score_trend(trend_data)

# Output the result
print(result)
