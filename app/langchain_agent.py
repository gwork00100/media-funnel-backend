# app/langchain_agent.py

from langchain.tools import tool, Tool
from langchain.agents import initialize_agent, AgentType
# from langchain.chat_models import ChatOpenAI  # <-- Removed this import
from langchain_community.llms import Ollama  # <-- Added this import
import os
import sys

# Allow importing from sibling modules like scorer.py, matcher.py, etc.
sys.path.append(os.path.dirname(__file__))

# Import your existing logic
from scorer import score_trend
from matcher import match_product
from generator import generate_content

# --- LangChain Tool Wrappers --- #

@tool
def score_trend_tool(trend: str) -> str:
    """Score how hot a trend is for product-market fit."""
    score = score_trend(trend)
    return f"The score for '{trend}' is {score}"

@tool
def match_product_tool(trend: str) -> str:
    """Suggest a product for a given trend."""
    return match_product(trend)

@tool
def generate_content_tool(trend_and_product: str) -> str:
    """Generate marketing content from trend and product. Format: 'trend|product'"""
    if "|" not in trend_and_product:
        return "Invalid input. Use 'trend|product'"
    trend, product = trend_and_product.split("|", 1)
    return generate_content(trend.strip(), product.strip())


# --- Initialize LangChain Agent --- #

def get_agent():
    tools = [
        Tool.from_function(score_trend_tool),
        Tool.from_function(match_product_tool),
        Tool.from_function(generate_content_tool),
    ]

    llm = Ollama(model="llama2", temperature=0)  # Changed here

    agent = initialize_agent(
        tools=tools,
        llm=llm,
        agent=AgentType.ZERO_SHOT_REACT_DESCRIPTION,
        verbose=True,
    )

    return agent


# --- Run the Agent on a Trend or List of Trends --- #

if __name__ == "__main__":
    import dotenv
    dotenv.load_dotenv()  # Load your .env file if you're storing OPENAI_API_KEY there

    agent = get_agent()

    # 👇 Test with multiple trends
    trends = [
        "AI for pets",
        "Climate-conscious fashion",
        "Space tourism"
    ]

    for trend in trends:
        print("\n", "="*40)
        print(f"Running agent on trend: {trend}\n")
        response = agent.run(f"""
            Analyze the trend "{trend}".
            Score it, match a product, and generate content.
            Return a complete summary.
        """)
        print(response)
