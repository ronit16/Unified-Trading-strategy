import pandas as pd
from .base import BaseStrategy

class RSIStrategy(BaseStrategy):
    """
    An example RSI Mean Reversion Strategy.
    Buy if RSI < 30 (Oversold), Sell if RSI > 70 (Overbought).
    """
    def __init__(self, period=14):
        super().__init__()
        self.period = period
        # We need slightly more data for RSI calculation to stabilize
        self.buffer_size = period * 2 

    def process_candle(self, candle):
        self.prices.append(candle['close'])
        
        if len(self.prices) > self.buffer_size:
            self.prices.pop(0)
            
        if len(self.prices) < self.period:
            return None
            
        # Calculate RSI using Pandas for convenience
        series = pd.Series(self.prices)
        delta = series.diff()
        gain = (delta.where(delta > 0, 0)).rolling(window=self.period).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(window=self.period).mean()
        
        rs = gain / loss
        rsi = 100 - (100 / (1 + rs))
        current_rsi = rsi.iloc[-1]
        
        if current_rsi < 30:
            return 'BUY'
        elif current_rsi > 70:
            return 'SELL'
            
        return None