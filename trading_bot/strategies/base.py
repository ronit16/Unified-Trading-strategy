from abc import ABC, abstractmethod

class BaseStrategy(ABC):
    """
    Abstract Base Class for all trading strategies.
    Enforces that every strategy has a process_candle method.
    """
    def __init__(self):
        self.prices = []

    @abstractmethod
    def process_candle(self, candle, position):
        """
        Input: candle dict {'timestamp': int, 'close': float, ...}, position string ('long', 'short', or None)
        Output: 'BUY', 'SELL', 'SELL_SHORT', 'COVER_SHORT', or None
        """
        pass
