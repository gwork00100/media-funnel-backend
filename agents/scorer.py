# agents/scorer.py

from langchain.chat_models import ChatOpenAI
from langchain.schema import SystemMessage, HumanMessage
from dotenv import load_dotenv
import os
import json

load_dotenv()

USE_MOCK = True  # Set to False to use real LLM scoring

def mock_score_trend(topic: str) -> dict:
    print(f"[MOCK] Scoring trend for topic: {topic}")
    return {
        "virality": 7,
        "monetization": 5,
        "content": 6
    }

def real_score_trend(topic: str) -> dict:
    openai_api_key = os.getenv("OPENAI_API_KEY")
    print(f"Loaded OpenAI key: {openai_api_key[:5]}...")

    llm = ChatOpenAI(model="gpt-3.5-turbo", temperature=0.7)

    system_prompt = """You are a trend analyst bot. 
    For each topic, return scores (0-10) for:
    - Virality potential
    - Monetization potential
    - Content potential

    Respond in JSON format like this:
    {
        "virality": 8,
        "monetization": 6,
        "content": 7
    }
    """

    user_prompt = f"Evaluate the trend: {topic}"

    messages = [
        SystemMessage(content=system_prompt),
        HumanMessage(content=user_prompt)
    ]

    response = llm.predict_messages(messages)

    try:
        return json.loads(response.content)
    except json.JSONDecodeError:
        return {"raw_response": response.content}

def score_trend(topic: str) -> dict:
    if USE_MOCK:
        return mock_score_trend(topic)
    else:
        return real_score_trend(topic)
