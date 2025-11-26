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
        self.position_type = None  # 'long' or 'short'
        self.entry_price = 0
        self.stop_loss_price = 0
        self.take_profit_price = 0
        self.short_proceeds = 0
        self.trades = []
        self.portfolio_history = []

    async def execute_order(self, signal, current_price, timestamp):
        """
        Executes order based on mode and saves to Postgres.
        """
        amount = 0
        executed_price = current_price
        strategy_params = cfg.STRATEGY_CONFIG.get(cfg.STRATEGY_NAME, {})
        stop_loss_pct = strategy_params.get('stop_loss_pct', 0)
        take_profit_pct = strategy_params.get('take_profit_pct', 0)

        # --- LONG ENTRY ---
        if signal == 'BUY' and self.balance > 0:
            amount = (self.balance / current_price) * 0.99
            if self.mode == 'LIVE':
                try:
                    resp = await self.rest.add_order(cfg.SYMBOL, 'buy', 'market', amount)
                    logger.warning(f"LIVE BUY EXECUTED: {resp}")
                except Exception as e:
                    logger.error(f"LIVE ORDER FAILED: {e}")
                    return

            self.position = amount
            self.position_type = 'long'
            self.entry_price = executed_price
            self.stop_loss_price = executed_price * (1 - stop_loss_pct)
            self.take_profit_price = executed_price * (1 + take_profit_pct)
            
            # LOCK CAPITAL
            self.balance = 0 
            await self._finalize_trade('buy', executed_price, amount)

        # --- LONG EXIT ---
        elif signal == 'SELL' and self.position_type == 'long':
            amount = self.position
            if self.mode == 'LIVE':
                try:
                    resp = await self.rest.add_order(cfg.SYMBOL, 'sell', 'market', amount)
                    logger.warning(f"LIVE SELL EXECUTED: {resp}")
                except Exception as e:
                    logger.error(f"LIVE ORDER FAILED: {e}")
                    return

            revenue = self.position * current_price
            cost = self.position * self.entry_price
            pnl = revenue - cost
            
            # UNLOCK CAPITAL + REVENUE
            self.balance = revenue
            
            self.position = 0
            self.position_type = None
            self.entry_price = 0
            self.trades.append({'side': 'sell', 'price': executed_price, 'amount': amount, 'timestamp': timestamp, 'pnl': pnl})
            await self._finalize_trade('sell', executed_price, amount)

        # --- SHORT ENTRY ---
        elif signal == 'SELL_SHORT' and self.balance > 0:
            amount = (self.balance / current_price) * 0.99
            if self.mode == 'LIVE':
                try:
                    resp = await self.rest.add_order(cfg.SYMBOL, 'sell', 'market', amount)
                    logger.warning(f"LIVE SELL SHORT EXECUTED: {resp}")
                except Exception as e:
                    logger.error(f"LIVE ORDER FAILED: {e}")
                    return
            
            self.position = amount
            self.position_type = 'short'
            self.entry_price = executed_price
            self.stop_loss_price = executed_price * (1 + stop_loss_pct)
            self.take_profit_price = executed_price * (1 - take_profit_pct)
            self.short_proceeds = amount * executed_price # "Cash" obtained from selling borrowed assets
            
            # LOCK CAPITAL (This was missing!)
            self.balance = 0 
            
            await self._finalize_trade('sell_short', executed_price, amount)
            
        # --- SHORT EXIT ---
        elif signal == 'COVER_SHORT' and self.position_type == 'short':
            amount = self.position
            if self.mode == 'LIVE':
                try:
                    resp = await self.rest.add_order(cfg.SYMBOL, 'buy', 'market', amount)
                    logger.warning(f"LIVE COVER SHORT EXECUTED: {resp}")
                except Exception as e:
                    logger.error(f"LIVE ORDER FAILED: {e}")
                    return

            buy_back_cost = self.position * current_price
            # PnL = Initial Proceeds - Cost to Buy Back
            pnl = self.short_proceeds - buy_back_cost
            
            # UNLOCK CAPITAL: The initial proceeds + PnL (or - Loss)
            self.balance = self.short_proceeds + pnl
            
            self.position = 0
            self.position_type = None
            self.entry_price = 0
            self.short_proceeds = 0
            self.trades.append({'side': 'cover_short', 'price': executed_price, 'amount': amount, 'timestamp': timestamp, 'pnl': pnl})
            await self._finalize_trade('cover_short', executed_price, amount)

    async def check_exit_conditions(self, current_price, timestamp):
        if self.position_type == 'long':
            if current_price <= self.stop_loss_price or current_price >= self.take_profit_price:
                await self.execute_order('SELL', current_price, timestamp)
        elif self.position_type == 'short':
            if current_price >= self.stop_loss_price or current_price <= self.take_profit_price:
                await self.execute_order('COVER_SHORT', current_price, timestamp)

    async def _finalize_trade(self, side, price, amount):
        logger.info(f"[{self.mode}] {side.upper()} @ {price} | Vol: {amount}")
        if self.db:
            await self.db.save_trade(
                symbol=cfg.SYMBOL,
                side=side,
                price=price,
                amount=amount,
                mode=self.mode,
                strategy=cfg.STRATEGY_NAME
            )

    def get_portfolio_value(self, current_price, timestamp):
        value = self.balance
        if self.position_type == 'long':
            value += self.position * current_price
        elif self.position_type == 'short':
            # Value = Cash + (Proceeds - Cost to Cover)
            # Since self.balance is 0 during short, value is purely the remaining equity
            value += self.short_proceeds + (self.short_proceeds - (self.position * current_price))

        self.portfolio_history.append({'timestamp': timestamp, 'portfolio_value': value})
        return value