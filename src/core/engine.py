"""
Trading Engine

Main orchestration component that connects strategies, exchanges, and infrastructure.
Clean, focused responsibility - no confusing naming like "enhanced" or "advanced".
"""

import asyncio
import time
from typing import Dict, List, Optional, Any
import logging

from interfaces.strategy import TradingStrategy, TradingSignal, SignalType, MarketData, Position
from interfaces.exchange import ExchangeAdapter, Order, OrderSide, OrderType, OrderStatus
from exchanges.hyperliquid import HyperliquidAdapter, HyperliquidMarketData
from core.key_manager import key_manager


class TradingEngine:
    """
    Main trading engine that orchestrates everything
    
    Responsibilities:
    - Connect strategies to market data
    - Execute trading signals via exchange adapters
    - Manage order lifecycle
    - Coordinate between all components
    
    This is the main "bot" - clean and focused.
    """
    
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.running = False
        
        # Core components
        self.strategy: Optional[TradingStrategy] = None
        self.exchange: Optional[ExchangeAdapter] = None 
        self.market_data: Optional[HyperliquidMarketData] = None
        
        # State tracking
        self.current_positions: List[Position] = []
        self.pending_orders: Dict[str, Order] = {}
        self.executed_trades = 0
        self.total_pnl = 0.0
        
        # Setup logging
        self.logger = logging.getLogger(__name__)
        logging.basicConfig(
            level=getattr(logging, config.get("log_level", "INFO")),
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
        
    async def initialize(self) -> bool:
        """Initialize all components"""
        
        try:
            self.logger.info("🚀 Initializing trading engine")
            
            # Initialize exchange adapter
            if not await self._initialize_exchange():
                return False
                
            # Initialize market data
            if not await self._initialize_market_data():
                return False
                
            # Initialize strategy
            if not self._initialize_strategy():
                return False
            
            self.logger.info("✅ Trading engine initialized successfully")
            return True
            
        except Exception as e:
            self.logger.error(f"❌ Failed to initialize trading engine: {e}")
            return False
    
    async def _initialize_exchange(self) -> bool:
        """Initialize exchange adapter"""
        
        exchange_config = self.config.get("exchange", {})
        
        # For now, only Hyperliquid is supported
        # Easy to extend by checking exchange_config["type"] and creating different adapters
        testnet = exchange_config.get("testnet", True)
        
        try:
            # Get private key using KeyManager
            bot_config = self.config.get("bot_config")  # Optional bot-specific config
            private_key = key_manager.get_private_key(testnet, bot_config)
        except ValueError as e:
            self.logger.error(f"❌ {e}")
            return False
        
        self.exchange = HyperliquidAdapter(private_key, testnet)
        
        if await self.exchange.connect():
            self.logger.info("✅ Exchange adapter connected")
            return True
        else:
            self.logger.error("❌ Failed to connect to exchange")
            return False
    
    async def _initialize_market_data(self) -> bool:
        """Initialize market data provider"""
        
        testnet = self.config.get("exchange", {}).get("testnet", True)
        self.market_data = HyperliquidMarketData(testnet)
        
        if await self.market_data.connect():
            self.logger.info("✅ Market data provider connected")
            return True
        else:
            self.logger.error("❌ Failed to connect to market data")
            return False
    
    def _initialize_strategy(self) -> bool:
        """Initialize trading strategy"""
        
        strategy_config = self.config.get("strategy", {})
        strategy_type = strategy_config.get("type", "basic_grid")
        
        try:
            from strategies import create_strategy
            self.strategy = create_strategy(strategy_type, strategy_config)
            
            self.strategy.start()
            self.logger.info(f"✅ Strategy initialized: {strategy_type}")
            return True
            
        except Exception as e:
            self.logger.error(f"❌ Failed to initialize strategy: {e}")
            return False
    
    async def start(self) -> None:
        """Start the trading engine"""
        
        if not self.strategy or not self.exchange or not self.market_data:
            raise RuntimeError("Engine not initialized")
        
        self.running = True
        self.logger.info("🎬 Trading engine started")
        
        # Subscribe to market data for strategy asset
        asset = self.config.get("strategy", {}).get("symbol", "BTC")
        await self.market_data.subscribe_price_updates(asset, self._handle_price_update)
        
        # Main trading loop
        await self._trading_loop()
    
    async def stop(self) -> None:
        """Stop the trading engine gracefully"""
        
        self.running = False
        self.logger.info("🛑 Stopping trading engine")
        
        # Stop strategy
        if self.strategy:
            self.strategy.stop()
        
        # Cancel pending orders
        if self.exchange:
            await self.exchange.cancel_all_orders()
        
        # Disconnect components
        if self.market_data:
            await self.market_data.disconnect()
        if self.exchange:
            await self.exchange.disconnect()
        
        self.logger.info("✅ Trading engine stopped")
    
    async def _handle_price_update(self, market_data: MarketData) -> None:
        """Handle incoming price updates"""
        
        if not self.running or not self.strategy:
            return
        
        try:
            # Get current balance
            balance_info = await self.exchange.get_balance("USD")  # Assuming USD balance
            balance = balance_info.available
            
            # Generate trading signals from strategy
            signals = self.strategy.generate_signals(market_data, self.current_positions, balance)
            
            # Execute signals
            for signal in signals:
                await self._execute_signal(signal)
                
        except Exception as e:
            self.logger.error(f"❌ Error handling price update: {e}")
    
    async def _execute_signal(self, signal: TradingSignal) -> None:
        """Execute a trading signal"""
        
        try:
            if signal.signal_type in [SignalType.BUY, SignalType.SELL]:
                await self._place_order(signal)
            elif signal.signal_type == SignalType.CLOSE:
                await self._close_positions(signal)
                
        except Exception as e:
            self.logger.error(f"❌ Error executing signal: {e}")
            # Notify strategy of error
            if self.strategy:
                self.strategy.on_error(e, {"signal": signal})
    
    async def _place_order(self, signal: TradingSignal) -> None:
        """Place an order based on trading signal"""
        
        # Create order
        current_time = time.time()
        order = Order(
            id=f"order_{int(current_time * 1000)}",  # Simple ID generation
            asset=signal.asset,
            side=OrderSide.BUY if signal.signal_type == SignalType.BUY else OrderSide.SELL,
            size=signal.size,
            order_type=OrderType.LIMIT if signal.price else OrderType.MARKET,
            price=signal.price,
            created_at=current_time
        )
        
        # Place order with exchange
        exchange_order_id = await self.exchange.place_order(order)
        order.exchange_order_id = exchange_order_id
        order.status = OrderStatus.SUBMITTED
        
        # Track pending order
        self.pending_orders[order.id] = order
        
        self.logger.info(f"📝 Placed {order.side.value} order: {order.size} {order.asset} @ ${order.price}")
        
        # Notify strategy
        if self.strategy:
            # Simulate immediate execution for now (real implementation would track fills)
            executed_price = order.price or 0.0
            self.strategy.on_trade_executed(signal, executed_price, order.size)
            self.executed_trades += 1
    
    async def _close_positions(self, signal: TradingSignal) -> None:
        """Close positions (e.g., cancel all orders for rebalancing)"""
        
        if signal.metadata.get("action") == "cancel_all":
            cancelled = await self.exchange.cancel_all_orders()
            self.logger.info(f"🗑️ Cancelled {cancelled} orders for rebalancing")
    
    async def _trading_loop(self) -> None:
        """Main trading loop for periodic tasks"""
        
        while self.running:
            try:
                # Periodic health checks, order status updates, etc.
                await asyncio.sleep(60)  # Check every minute
                
                # Update order statuses (simplified)
                await self._update_order_statuses()
                
                # Log status
                if self.executed_trades > 0:
                    self.logger.info(f"📊 Total trades: {self.executed_trades}")
                
            except Exception as e:
                self.logger.error(f"❌ Error in trading loop: {e}")
                await asyncio.sleep(60)
    
    async def _update_order_statuses(self) -> None:
        """Update status of pending orders"""
        
        # This would query the exchange for order statuses
        # For now, we'll just clean up old orders
        current_time = time.time()
        
        for order_id in list(self.pending_orders.keys()):
            order = self.pending_orders[order_id]
            
            # Remove orders older than 1 hour (they're probably filled or cancelled)
            if current_time - order.created_at > 3600:
                del self.pending_orders[order_id]
    
    def get_status(self) -> Dict[str, Any]:
        """Get engine status"""
        
        return {
            "running": self.running,
            "strategy": self.strategy.get_status() if self.strategy else None,
            "exchange": self.exchange.get_status() if self.exchange else None,
            "market_data": self.market_data.get_status() if self.market_data else None,
            "executed_trades": self.executed_trades,
            "pending_orders": len(self.pending_orders),
            "total_pnl": self.total_pnl
        }