from .sma import SMAStrategy
from .rsi import RSIStrategy
from trading_bot.config import cfg

# Registry mapping names to classes
STRATEGY_MAP = {
    'SMA': SMAStrategy,
    'RSI': RSIStrategy
}

def get_strategy(strategy_name):
    """Factory function to load strategy by name."""
    if strategy_name not in STRATEGY_MAP:
        raise ValueError(f"Strategy '{strategy_name}' not found. Available: {list(STRATEGY_MAP.keys())}")
    
    strategy_params = cfg.STRATEGY_CONFIG.get(strategy_name, {})
    return STRATEGY_MAP[strategy_name](**strategy_params)
