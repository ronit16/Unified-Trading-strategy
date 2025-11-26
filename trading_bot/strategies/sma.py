from .base import BaseStrategy

class SMAStrategy(BaseStrategy):
    """
    Your original Golden Cross Strategy.
    """
    def __init__(self, short_window=10, long_window=50):
        super().__init__()
        self.short_window = short_window
        self.long_window = long_window

    def process_candle(self, candle):
        self.prices.append(candle['close'])
        
        # Maintain history size
        if len(self.prices) > self.long_window:
            self.prices.pop(0)

        # Not enough data
        if len(self.prices) < self.long_window:
            return None

        # Calculate SMAs
        short_ma = sum(self.prices[-self.short_window:]) / self.short_window
        long_ma = sum(self.prices[-self.long_window:]) / self.long_window
        
        # Logic
        if short_ma > long_ma:
            return 'BUY'
        elif short_ma < long_ma:
            return 'SELL'
        
        return None