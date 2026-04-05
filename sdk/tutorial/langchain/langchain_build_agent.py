import getpass
import os

from langchain.chat_models import init_chat_model
from langchain_tavily import TavilySearch

if not os.environ.get("OPENAI_API_KEY"):
    os.environ["OPENAI_API_KEY"] = getpass.getpass("Enter API key for OpenAI: ")

model = init_chat_model("gpt-4.1", model_provider="openai")

if not os.environ.get("OPENAI_API_KEY"):
    os.environ["TAVILY_API_KEY"] = getpass.getpass("Enter API key for Tavily: ")

search = TavilySearch(max_results=2)
tools = [search]





