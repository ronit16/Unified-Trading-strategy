import logging
from datetime import datetime
from trading_bot.config import cfg

logger = logging.getLogger(__name__)

class ExecutionEngine:
    def __init__(self, kraken_rest, database):
        self.mode = cfg.TRADING_MODE
        self.rest = kraken_rest
        self.db = database
        self.balance = cfg.CAPITAL
        self.position = 0

    async def execute_order(self, signal, current_price, timestamp):
        """
        Executes order based on mode and saves to Postgres.
        """
        amount = 0
        executed_price = current_price
        
        if signal == 'BUY' and self.balance > 0:
            amount = (self.balance / current_price) * 0.99 # Simple fee buffer
            if self.mode == 'LIVE':
                # Real Kraken Order
                try:
                    resp = await self.rest.add_order(cfg.SYMBOL, 'buy', 'market', amount)
                    logger.warning(f"LIVE BUY EXECUTED: {resp}")
                    # In a real scenario, you'd fetch the actual fill price here
                except Exception as e:
                    logger.error(f"LIVE ORDER FAILED: {e}")
                    return
            
            self.position = amount
            self.balance = 0
            await self._finalize_trade('buy', executed_price, amount)

        elif signal == 'SELL' and self.position > 0:
            amount = self.position
            if self.mode == 'LIVE':
                try:
                    resp = await self.rest.add_order(cfg.SYMBOL, 'sell', 'market', amount)
                    logger.warning(f"LIVE SELL EXECUTED: {resp}")
                except Exception as e:
                    logger.error(f"LIVE ORDER FAILED: {e}")
                    return

            revenue = self.position * current_price
            self.balance = revenue
            self.position = 0
            await self._finalize_trade('sell', executed_price, amount)

    async def _finalize_trade(self, side, price, amount):
        logger.info(f"[{self.mode}] {side.upper()} @ {price} | Vol: {amount}")
        
        # Save to Postgres
        if self.db:
            await self.db.save_trade(
                symbol=cfg.SYMBOL,
                side=side,
                price=price,
                amount=amount,
                mode=self.mode,
                strategy=cfg.STRATEGY_NAME
            )

    def get_portfolio_value(self, current_price):
        return self.balance + (self.position * current_price)