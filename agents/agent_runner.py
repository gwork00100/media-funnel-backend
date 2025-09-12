from langchain.agents import initialize_agent, AgentType
from langchain_community.chat_models import ChatOpenAI
from langchain.memory import ConversationBufferMemory
from tools import fetch_trends, score_trends, generate_content
import os
from dotenv import load_dotenv

load_dotenv()

llm = ChatOpenAI(
    temperature=0.7,
    model_name="gpt-4",
    openai_api_key=os.getenv("OPENAI_API_KEY")
)

tools = [fetch_trends, score_trends, generate_content]

memory = ConversationBufferMemory(memory_key="chat_history")

agent = initialize_agent(
    tools,
    llm,
    agent=AgentType.ZERO_SHOT_REACT_DESCRIPTION,
    memory=memory,
    verbose=True
)

def run_agent():
    result = agent.run("Fetch top 3 trends, score them, and create a post for each.")
    print("Agent Output:\n", result)
    return result
