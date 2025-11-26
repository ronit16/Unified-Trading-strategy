import os
import argparse
import json
from dotenv import load_dotenv

load_dotenv(dotenv_path='.env')

class Config:
    def __init__(self):
        # 1. Load defaults from Environment
        self.TRADING_MODE = os.getenv('TRADING_MODE', 'BACKTEST').upper()
        self.STRATEGY_NAME = os.getenv('STRATEGY_NAME', 'SMA').upper()
        self.SYMBOL = os.getenv('SYMBOL', 'BTC/USD').upper()
        self.TIMEFRAME = int(os.getenv('TIMEFRAME_MINUTES', '1'))
        
        # Infrastructure
        self.NATS_URL = os.getenv('NATS_URL', 'nats://localhost:4222')
        postgres_password = os.getenv('POSTGRES_PASSWORD', 'password')
        self.DB_URL = f'postgresql://admin:{postgres_password}@localhost:5432/trading_bot'
        
        # Kraken Auth
        self.API_KEY = os.getenv('KRAKEN_API_KEY', '')
        self.API_SECRET = os.getenv('KRAKEN_SECRET', '')
        self.KRAKEN_REST_URL = "https://api.kraken.com"
        self.KRAKEN_WS_URL = "wss://ws-auth.kraken.com/v2"
        
        # Backtest
        self.CSV_PATH = os.getenv('CSV_PATH', 'BTCUSD_1.csv')
        self.CAPITAL = float(os.getenv('INITIAL_CAPITAL', '10000'))
        
        # Strategy Config
        self.STRATEGY_CONFIG = self.load_strategy_config()

    def load_strategy_config(self):
        """Load strategy configurations from strategies.json"""
        try:
            with open('trading_bot/strategies.json', 'r') as f:
                return json.load(f)
        except FileNotFoundError:
            print("Error: strategies.json not found.")
            return {}
        except json.JSONDecodeError:
            print("Error: Could not decode strategies.json.")
            return {}

    def parse_args(self):
        """Override config with command line arguments"""
        parser = argparse.ArgumentParser(description="Kraken Trading Bot (NATS + Postgres)")
        
        parser.add_argument('--mode', type=str, choices=['BACKTEST', 'PAPER', 'LIVE'], 
                           help='Trading Mode')
        parser.add_argument('--strategy', type=str, help='Strategy Name (e.g., SMA, RSI)')
        parser.add_argument('--symbol', type=str, help='Trading Pair (e.g., BTC/USD)')
        
        args = parser.parse_args()
        
        if args.mode: self.TRADING_MODE = args.mode.upper()
        if args.strategy: self.STRATEGY_NAME = args.strategy.upper()
        if args.symbol: self.SYMBOL = args.symbol.upper()

# Global Instance
cfg = Config()
