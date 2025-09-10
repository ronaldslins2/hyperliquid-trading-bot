"""
Interfaces for extending the trading system.

These interfaces define clear contracts for adding:
- New trading strategies (implement TradingStrategy)
- New exchanges/DEXes (implement ExchangeAdapter)
"""

from .strategy import TradingStrategy, TradingSignal, SignalType, MarketData, Position
from .exchange import (
    ExchangeAdapter,
    Order,
    OrderSide,
    OrderType,
    OrderStatus,
    Balance,
    MarketInfo,
)

__all__ = [
    # Strategy interface
    "TradingStrategy",
    "TradingSignal",
    "SignalType",
    "MarketData",
    "Position",
    # Exchange interface
    "ExchangeAdapter",
    "Order",
    "OrderSide",
    "OrderType",
    "OrderStatus",
    "Balance",
    "MarketInfo",
]
