from .base import BaseStrategy

class Sma(BaseStrategy):
    """
    Golden Cross Strategy with Short Selling.
    """
    def __init__(self, short_window=10, long_window=50, stop_loss_pct=0.02, take_profit_pct=0.05):
        super().__init__()
        self.short_window = short_window
        self.long_window = long_window
        self.stop_loss_pct = stop_loss_pct
        self.take_profit_pct = take_profit_pct

    def process_candle(self, candle, position):
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
        
        # Logic for long positions
        if position == 'long':
            if short_ma < long_ma:
                return 'SELL'
        # Logic for short positions
        elif position == 'short':
            if short_ma > long_ma:
                return 'COVER_SHORT'
        # No position open
        else:
            if short_ma > long_ma:
                return 'BUY'
            elif short_ma < long_ma:
                return 'SELL_SHORT'
        
        return None
