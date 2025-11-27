import asyncio
import logging
import argparse
import json
from decouple import config
from adk.api import Session
from agents.alpha_factory import alpha_factory
from agents.monitoring_agent import monitoring_agent
from agents.db_tools import db
from trading_bot.core.bot import Bot

def setup_logging():
    """Configures the logging for the application."""
    log_formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    file_handler = logging.FileHandler('trading_bot.log')
    file_handler.setFormatter(log_formatter)
    console_handler = logging.StreamHandler()
    console_handler.setFormatter(log_formatter)
    root_logger = logging.getLogger()
    root_logger.setLevel(logging.INFO)
    root_logger.addHandler(file_handler)
    root_logger.addHandler(console_handler)

async def run_alpha_factory():
    """Wrapper coroutine to run the Alpha Factory task."""
    logging.info("--- Starting Alpha Factory ---")
    session = Session()
    try:
        initial_input = "Find me a Bitcoin scalping strategy"
        # Provide a path to sample data for the backtesting phase
        session['csv_datapath'] = 'trading_bot/data/historical_btc_data.csv'
        await alpha_factory.run(session, initial_input)
        logging.info("--- Alpha Factory Run Complete ---")
    except Exception as e:
        logging.error(f"Alpha Factory failed: {e}", exc_info=True)

async def run_monitoring_agent():
    """Wrapper coroutine to run the Monitoring Agent service."""
    logging.info("--- Starting Monitoring Agent ---")
    session = Session()
    try:
        await monitoring_agent.run(session)
    except Exception as e:
        logging.error(f"Monitoring Agent failed: {e}", exc_info=True)

async def run_backtest_from_cli(args):
    """
    Runs a backtest using the provided command-line arguments and prints the results as JSON.
    """
    bot = Bot(
        strategy_filepath=args.strategy_filepath,
        config_filepath=args.config_filepath,
        csv_datapath=args.csv_datapath
    )
    await db.connect()
    results = await bot.run_backtest()
    await db.close()

    print(json.dumps(results))

async def main():
    """
    Main entry point for the application.
    Parses command-line arguments to decide whether to run the agent system or a backtest.
    """
    setup_logging()

    parser = argparse.ArgumentParser()
    parser.add_argument("--mode", default="AGENT", choices=["AGENT", "BACKTEST"])
    parser.add_argument("--strategy_filepath")
    parser.add_argument("--config_filepath")
    parser.add_argument("--csv_datapath")
    args = parser.parse_args()

    if args.mode == "BACKTEST":
        await run_backtest_from_cli(args)
    else:
        await db.connect()
        try:
            await asyncio.gather(
                run_monitoring_agent(),
                run_alpha_factory()
            )
        finally:
            await db.close()
            logging.info("Database connection closed.")

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\nSystem stopped by user.")
    except Exception as e:
        logging.error(f"Critical System Error: {e}", exc_info=True)
