from adk.agents import LlmAgent
from adk.tools import FunctionTool
import requests
from bs4 import BeautifulSoup
from .db_tools import save_strategy_tool

# Tool definitions
def web_scraper(url: str) -> str:
    """Scrapes the text content from a given URL."""
    try:
        response = requests.get(url)
        soup = BeautifulSoup(response.text, 'html.parser')
        return soup.get_text()
    except Exception as e:
        return f"Error scraping URL: {e}"

def google_search(query: str) -> str:
    """Performs a Google search and returns the top results."""
    # This is a placeholder for a real Google Search API call.
    return f"Performing Google search for: {query}"


# Agent definition
strategy_researcher = LlmAgent(
    name="StrategyResearcher",
    system_instructions="""You are a quantitative researcher. Your goal is to find trading strategies for a given asset class.
    1.  Use your tools to search for and scrape information about trading strategies.
    2.  Analyze the information to extract the strategy's logic, indicators, and parameters.
    3.  Format the extracted information into a structured JSON object.
    4.  **Crucially, you must save the final JSON object to the session state by setting `session['strategy_json']`**.
    5.  You must also save the strategy to the database using the `save_strategy_tool`.""",
    tools=[
        FunctionTool(web_scraper),
        FunctionTool(google_search),
        save_strategy_tool
    ]
)
