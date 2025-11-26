from abc import ABC, abstractmethod

class BaseStrategy(ABC):
    """
    Abstract Base Class for all trading strategies.
    Enforces that every strategy has a process_candle method.
    """
    def __init__(self):
        self.prices = []

    @abstractmethod
    def process_candle(self, candle):
        """
        Input: candle dict {'timestamp': int, 'close': float, ...}
        Output: 'BUY', 'SELL', or None
        """
        pass