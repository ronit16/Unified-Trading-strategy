import asyncio
import json
import logging
import nats
import pandas as pd
import os
import importlib.util
from trading_bot.core.database import Database
from trading_bot.core.kraken_api import KrakenREST
from trading_bot.core.execution import ExecutionEngine
from trading_bot.core.results import Results
from agents.db_tools import db # Use the shared DB instance

logger = logging.getLogger(__name__)

def load_strategy_from_file(filepath: str):
    """Dynamically loads a strategy class from a Python file."""
    spec = importlib.util.spec_from_file_location("strategy_module", filepath)
    strategy_module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(strategy_module)
    # Assumes the class name is the same as the file name, capitalized
    class_name = os.path.basename(filepath).replace(".py", "").capitalize()
    return getattr(strategy_module, class_name)

class Bot:
    def __init__(self, strategy_filepath, config_filepath, csv_datapath):
        self.strategy_filepath = strategy_filepath
        self.config_filepath = config_filepath
        self.csv_datapath = csv_datapath
        
        # Load config and strategy dynamically
        self.config = self._load_config()
        StrategyClass = load_strategy_from_file(strategy_filepath)
        self.strategy = StrategyClass(self.config['indicators'])

        self.db = db
        self.rest = KrakenREST(self.config['api_key'], self.config['api_secret'], self.config['rest_url'])
        self.execution = ExecutionEngine(self.rest, self.db)
        self.nc = None

    def _load_config(self) -> dict:
        """Loads the configuration from the specified file."""
        # This is a simplified config loader. A real implementation would be more robust.
        config = {}
        with open(self.config_filepath, 'r') as f:
            exec(f.read(), config)
        return config

    async def run_backtest(self) -> dict:
        """Runs the backtest and returns the performance metrics as a dictionary."""
        logger.info(f"Starting Backtest for {self.strategy_filepath}...")
        if not os.path.exists(self.csv_datapath):
            logger.error("CSV file not found.")
            return {"error": "CSV file not found"}

        df = pd.read_csv(self.csv_datapath, header=None,
                         names=['timestamp', 'open', 'high', 'low', 'close', 'volume', 'vwap'])

        for index, row in df.iterrows():
            candle = {'timestamp': row['timestamp'], 'close': row['close']}
            
            await self.execution.check_exit_conditions(candle['close'], candle['timestamp'])
            
            signal = self.strategy.process_candle(candle, self.execution.position_type)
            
            if signal:
                await self.execution.execute_order(signal, row['close'], row['timestamp'])
            
            self.execution.get_portfolio_value(row['close'], row['timestamp'])
        
        results = Results(self.execution.trades, self.execution.portfolio_history, self.config.get('capital', 10000))
        metrics = results.calculate_metrics()
        
        logger.info(f"Backtest Finished. Final Value: ${metrics['final_equity']:.2f}")
        return metrics

    # Note: The live trading methods (run_live_system, on_market_data, etc.) are omitted
    # as they are not used in the agent-based backtesting workflow. They would be part of
    # the containerized strategy that the DeploymentManager launches.
