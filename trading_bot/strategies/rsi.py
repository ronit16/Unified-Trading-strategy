import pandas as pd
from .base import BaseStrategy

class Rsi(BaseStrategy):
    """
    RSI Mean Reversion Strategy with Short Selling.
    """
    def __init__(self, period=14, overbought=70, oversold=30, stop_loss_pct=0.03, take_profit_pct=0.06):
        super().__init__()
        self.period = period
        self.overbought = overbought
        self.oversold = oversold
        self.stop_loss_pct = stop_loss_pct
        self.take_profit_pct = take_profit_pct
        self.avg_gain = 0
        self.avg_loss = 0

    def process_candle(self, candle, position):
        self.prices.append(candle['close'])
        
        if len(self.prices) < 2:
            return None
        
        if len(self.prices) > self.period + 1:
            self.prices.pop(0)

        if len(self.prices) < self.period + 1:
            return None

        # Incremental RSI calculation
        if len(self.prices) == self.period + 1:
            # Initial SMA
            changes = [self.prices[i] - self.prices[i-1] for i in range(1, len(self.prices))]
            gains = [c for c in changes if c > 0]
            losses = [-c for c in changes if c < 0]
            self.avg_gain = sum(gains) / self.period
            self.avg_loss = sum(losses) / self.period
        else:
            # Smoothed Moving Average (SMMA)
            change = self.prices[-1] - self.prices[-2]
            gain = change if change > 0 else 0
            loss = -change if change < 0 else 0
            self.avg_gain = (self.avg_gain * (self.period - 1) + gain) / self.period
            self.avg_loss = (self.avg_loss * (self.period - 1) + loss) / self.period
            
        if self.avg_loss == 0:
            current_rsi = 100
        else:
            rs = self.avg_gain / self.avg_loss
            current_rsi = 100 - (100 / (1 + rs))

        # Logic for long positions
        if position == 'long':
            if current_rsi > self.overbought:
                return 'SELL'
        # Logic for short positions
        elif position == 'short':
            if current_rsi < self.oversold:
                return 'COVER_SHORT'
        # No position open
        else:
            if current_rsi < self.oversold:
                return 'BUY'
            elif current_rsi > self.overbought:
                return 'SELL_SHORT'
            
        return None
