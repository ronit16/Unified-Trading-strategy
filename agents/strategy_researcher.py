from google.adk.agents import LlmAgent
from google.adk.tools import FunctionTool
import requests
from bs4 import BeautifulSoup
from .db_tools import save_strategy_tool

# Tool definitions
def web_scraper(url: str) -> str:
    """Scrapes the text content from a given URL."""
    try:
        response = requests.get(url)
        # Use html.parser for resilience
        soup = BeautifulSoup(response.text, 'html.parser')
        # Simple text extraction
        return ' '.join(p.get_text() for p in soup.find_all('p'))
    except Exception as e:
        return f"Error scraping URL: {e}"

def google_search(query: str) -> str:
    """
    Performs a Google search and returns a list of relevant URLs.
    This is a functional placeholder that returns a fixed set of URLs
    to allow the research agent to work without a real search API key.
    """
    print(f"Performing placeholder search for: {query}")
    # Return a list of URLs known to contain trading strategy information
    return [
        "https://www.investopedia.com/terms/g/goldencross.asp",
        "https://corporatefinanceinstitute.com/resources/capital-markets/death-cross/",
        "https://www.babypips.com/learn/forex/crossover"
    ]


# Agent definition
strategy_researcher = LlmAgent(
    name="StrategyResearcher",
    instruction="""You are a quantitative researcher. Your goal is to find trading strategies for a given asset class.
    1.  Use your tools to search for and scrape information about trading strategies from the provided URLs.
    2.  Analyze the information to extract the strategy's logic, indicators, and parameters.
    3.  Format the extracted information into a structured JSON object.
    4.  **Crucially, you must save the final JSON object to the session state by setting `session.set('strategy_json', ...)`**.
    5.  You must also save the strategy to the database using the `save_strategy_tool`.""",
    tools=[
        FunctionTool(web_scraper),
        FunctionTool(google_search),
        save_strategy_tool
    ]
)
