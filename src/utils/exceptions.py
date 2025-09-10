class TradingFrameworkError(Exception):
    """Base exception for the trading framework"""

    pass


class ConfigurationError(TradingFrameworkError):
    """Raised when configuration is invalid"""

    pass


class StrategyError(TradingFrameworkError):
    """Raised when strategy encounters an error"""

    pass


class ExchangeError(TradingFrameworkError):
    """Raised when exchange operations fail"""

    pass


class OrderError(TradingFrameworkError):
    """Raised when order operations fail"""

    pass


class PositionError(TradingFrameworkError):
    """Raised when position operations fail"""

    pass


class GridError(TradingFrameworkError):
    """Raised when grid trading operations fail"""

    pass


class TradingError(TradingFrameworkError):
    """Raised for general trading operations errors"""

    pass
