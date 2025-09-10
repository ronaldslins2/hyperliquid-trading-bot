"""
Trading Strategies

Business logic for different trading strategies.
Add new strategies by implementing the TradingStrategy interface.

Available strategies:
- BasicGridStrategy: Grid trading with geometric spacing and rebalancing
"""

from .grid import BasicGridStrategy

# Strategy registry - makes it easy to add new strategies
STRATEGY_REGISTRY = {
    "basic_grid": BasicGridStrategy,
    "grid": BasicGridStrategy,  # Alias
}


def create_strategy(strategy_type: str, config: dict):
    """
    Factory function to create strategies.

    Makes it easy for newbies to add new strategies:
    1. Implement TradingStrategy interface
    2. Add to STRATEGY_REGISTRY
    3. Done!
    """
    if strategy_type not in STRATEGY_REGISTRY:
        available = ", ".join(STRATEGY_REGISTRY.keys())
        raise ValueError(
            f"Unknown strategy type: {strategy_type}. Available: {available}"
        )

    strategy_class = STRATEGY_REGISTRY[strategy_type]
    return strategy_class(config)


__all__ = ["BasicGridStrategy", "STRATEGY_REGISTRY", "create_strategy"]
