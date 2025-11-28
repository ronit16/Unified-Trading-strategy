from google.adk.tools import FunctionTool
from trading_bot.core.database import Database
from decouple import config

# Create a single, shared instance of the Database
db = Database(config('DB_URL'))

async def save_strategy_to_db(source_url: str, raw_text: str, structured_json: dict) -> str:
    """Saves a strategy to the database."""
    return await db.save_strategy(source_url, raw_text, structured_json)

save_strategy_tool = FunctionTool(save_strategy_to_db)

async def save_backtest_results_to_db(strategy_id: str, iteration: int, params: dict, results: dict) -> str:
    """Saves the backtest results to the database."""
    return await db.save_backtest_run(strategy_id, iteration, params, results)

save_backtest_results_tool = FunctionTool(save_backtest_results_to_db)
