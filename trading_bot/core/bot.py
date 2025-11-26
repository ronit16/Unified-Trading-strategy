import asyncio
import json
import logging
import nats
import pandas as pd
import os
from trading_bot.config import cfg
from trading_bot.core.database import Database
from trading_bot.core.kraken_api import KrakenREST, KrakenWS
from trading_bot.core.execution import ExecutionEngine
from trading_bot.strategies import get_strategy

logger = logging.getLogger(__name__)

class Bot:
    def __init__(self):
        cfg.parse_args() # Parse CLI args
        self.strategy = get_strategy(cfg.STRATEGY_NAME)
        self.db = Database(cfg.DB_URL)
        self.rest = KrakenREST(cfg.API_KEY, cfg.API_SECRET, cfg.KRAKEN_REST_URL)
        self.execution = ExecutionEngine(self.rest, self.db)
        self.nc = None # NATS connection

    async def run(self):
        logger.info(f"Starting Bot | Mode: {cfg.TRADING_MODE} | Strategy: {cfg.STRATEGY_NAME}")
        
        # 1. Connect to Infrastructure
        await self.db.connect()
        
        if cfg.TRADING_MODE in ['LIVE', 'PAPER']:
            await self.run_live_system()
        else:
            await self.run_backtest()

    async def run_live_system(self):
        """
        Sets up NATS:
        1. Producer (KrakenWS) -> NATS 'market.data'
        2. Consumer (Bot) <- NATS 'market.data'
        """
        # Connect to NATS
        try:
            self.nc = await nats.connect(cfg.NATS_URL)
            logger.info(f"Connected to NATS at {cfg.NATS_URL}")
        except Exception as e:
            logger.error(f"NATS Connection failed: {e}")
            return

        # Start Consumer (The Strategy Engine)
        await self.nc.subscribe(f"market.{cfg.SYMBOL}", cb=self.on_market_data)

        # Start Producer (The Data Feed)
        # In a microservice architecture, this would be a separate process.
        # Here we run it as a background task.
        kraken_ws = KrakenWS(cfg.KRAKEN_WS_URL, self.publish_to_nats)
        
        # Kraken uses symbols like BTC/USD, NATS prefers clean strings (BTC_USD)
        clean_symbol = [cfg.SYMBOL] # API expects list
        
        await kraken_ws.connect_and_stream(clean_symbol)

    async def publish_to_nats(self, raw_data):
        """Callback for KrakenWS to publish to NATS"""
        # Filter for 'ohlc' channel update
        if raw_data.get('channel') == 'ohlc' and raw_data.get('type') == 'update':
            # Extract candle data
            # Kraken format: {'channel': 'ohlc', 'data': [{'close': ..., 'timestamp': ...}]}
            for candle in raw_data['data']:
                payload = json.dumps(candle).encode()
                # Publish to NATS
                await self.nc.publish(f"market.{cfg.SYMBOL}", payload)

    async def on_market_data(self, msg):
        """NATS Consumer Callback: Runs Strategy"""
        data = json.loads(msg.data.decode())
        
        # Convert Kraken candle to our format
        # Kraken v2 OHLC: { 'close': 100.0, 'time': 123456789.0, ... }
        candle = {
            'timestamp': data.get('end', time.time()), # V2 uses 'end' for close time
            'close': float(data.get('close', 0))
        }

        signal = self.strategy.process_candle(candle)
        if signal:
            await self.execution.execute_order(signal, candle['close'], candle['timestamp'])

    async def run_backtest(self):
        logger.info("Starting Backtest...")
        if not os.path.exists(cfg.CSV_PATH):
            logger.error("CSV file not found.")
            return

        # Load CSV
        try:
            df = pd.read_csv(cfg.CSV_PATH, header=None, 
                           names=['timestamp', 'open', 'high', 'low', 'close', 'volume', 'vwap'])
        except Exception as e:
            logger.error(f"CSV Error: {e}")
            return

        for index, row in df.iterrows():
            candle = {'timestamp': row['timestamp'], 'close': row['close']}
            
            # Direct calls (Simulating the NATS pipeline speed is unnecessary for backtest logic)
            signal = self.strategy.process_candle(candle)
            
            if signal:
                # We use the async execution engine, so we must await
                await self.execution.execute_order(signal, row['close'], row['timestamp'])
        
        final = self.execution.get_portfolio_value(df.iloc[-1]['close'])
        logger.info(f"Backtest Finished. Final Value: ${final:.2f}")

    async def shutdown(self):
        await self.db.close()
        if self.nc:
            await self.nc.close()