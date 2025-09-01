"""
Hyperliquid Exchange Adapter

Clean implementation of Hyperliquid integration using the exchange interface.
Technical implementation separated from business logic.
"""

from typing import Dict, List, Optional, Any
import time

from interfaces.exchange import (
    ExchangeAdapter, Order, OrderSide, OrderType, OrderStatus, 
    Balance, MarketInfo
)
from core.endpoint_router import get_endpoint_router


class HyperliquidAdapter(ExchangeAdapter):
    """
    Hyperliquid DEX adapter implementation
    
    Handles all Hyperliquid-specific technical details while implementing
    the clean exchange interface that strategies can use.
    """
    
    def __init__(self, private_key: str, testnet: bool = True):
        super().__init__("Hyperliquid")
        self.private_key = private_key
        self.testnet = testnet
        self.paper_trading = False
        
        # Hyperliquid SDK components (will be initialized on connect)
        self.info = None
        self.exchange = None
        
        # Endpoint router for smart routing
        self.endpoint_router = get_endpoint_router(testnet)
        
    async def connect(self) -> bool:
        """Connect to Hyperliquid with smart endpoint routing"""
        try:
            # Import here to avoid dependency issues
            from hyperliquid.info import Info
            from hyperliquid.exchange import Exchange
            from eth_account import Account
            
            # Get the info endpoint from router
            info_url = self.endpoint_router.get_endpoint_for_method("user_state")
            if not info_url:
                raise RuntimeError("No healthy info endpoint available")
            
            # Remove /info suffix if present (SDK adds it automatically)
            base_url = info_url.replace('/info', '') if info_url.endswith('/info') else info_url
            
            # Create wallet from private key
            wallet = Account.from_key(self.private_key)
            
            # Initialize SDK components with smart endpoint routing
            self.info = Info(base_url, skip_ws=True)
            self.exchange = Exchange(wallet, base_url)
            
            # Test connection
            user_state = self.info.user_state(self.exchange.wallet.address)
            
            self.is_connected = True
            print(f"✅ Connected to Hyperliquid ({'testnet' if self.testnet else 'mainnet'})")
            print(f"📡 Using endpoint: {info_url}")
            print(f"🔑 Wallet address: {self.exchange.wallet.address}")
            return True
            
        except Exception as e:
            print(f"❌ Failed to connect to Hyperliquid: {e}")
            self.is_connected = False
            return False
    
    async def disconnect(self) -> None:
        """Disconnect from Hyperliquid"""
        self.is_connected = False
        self.info = None
        self.exchange = None
        print("🔌 Disconnected from Hyperliquid")
    
    async def get_balance(self, asset: str) -> Balance:
        """Get account balance for an asset"""
        if not self.is_connected:
            raise RuntimeError("Not connected to exchange")
            
        try:
            user_state = self.info.user_state(self.exchange.wallet.address)
            
            # Find asset balance
            for balance_info in user_state.get("balances", []):
                coin = balance_info.get("coin", "")
                if coin == asset:
                    total = float(balance_info.get("total", 0))
                    hold = float(balance_info.get("hold", 0))
                    available = total - hold
                    
                    return Balance(
                        asset=asset,
                        available=available,
                        locked=hold,
                        total=total
                    )
            
            # Asset not found, return zero balance
            return Balance(asset=asset, available=0.0, locked=0.0, total=0.0)
            
        except Exception as e:
            raise RuntimeError(f"Failed to get {asset} balance: {e}")
    
    async def get_market_price(self, asset: str) -> float:
        """Get current market price"""
        if not self.is_connected:
            raise RuntimeError("Not connected to exchange")
            
        try:
            # Get all mids (market prices)
            all_mids = self.info.all_mids()
            
            # Find asset price
            if asset in all_mids:
                return float(all_mids[asset])
            else:
                raise ValueError(f"Asset {asset} not found in market data")
                
        except Exception as e:
            raise RuntimeError(f"Failed to get {asset} price: {e}")
    
    async def place_order(self, order: Order) -> str:
        """Place an order on Hyperliquid"""
        if not self.is_connected:
            raise RuntimeError("Not connected to exchange")
            
        try:
            # Convert to Hyperliquid format
            is_buy = order.side == OrderSide.BUY
            
            # Import the OrderType from the SDK
            from hyperliquid.utils.signing import OrderType as HLOrderType
            
            # Round values to proper precision for Hyperliquid
            def round_price(price):
                """Round price to proper tick size for BTC (whole dollars)"""
                if order.asset == "BTC":
                    # BTC appears to require whole dollar prices
                    return float(int(price))
                else:
                    # For other assets, use 2 decimal places
                    return round(float(price), 2)
            
            def round_size(size):
                """Round size to proper precision based on szDecimals (5 for BTC)"""
                return round(float(size), 5)  # BTC has szDecimals=5
            
            # Ensure minimum size requirements
            min_size = 0.0001  # Minimum BTC size
            rounded_size = max(round_size(order.size), min_size)
            
            if order.order_type == OrderType.MARKET:
                # Market order - use limit order with current market price
                market_price = await self.get_market_price(order.asset)
                # Adjust price slightly to ensure fill for market orders  
                adjusted_price = round_price(market_price * (1.01 if is_buy else 0.99))
                result = self.exchange.order(
                    name=order.asset,
                    is_buy=is_buy,
                    sz=rounded_size,
                    limit_px=adjusted_price,
                    order_type=HLOrderType({"limit": {"tif": "Ioc"}}),  # Immediate or Cancel for market-like behavior
                    reduce_only=False
                )
            else:
                # Limit order
                rounded_price = round_price(order.price)
                result = self.exchange.order(
                    name=order.asset,
                    is_buy=is_buy,
                    sz=rounded_size,
                    limit_px=rounded_price,
                    order_type=HLOrderType({"limit": {"tif": "Gtc"}}),  # Good Till Cancel
                    reduce_only=False
                )
            
            # Extract order ID from result
            if result and "status" in result and result["status"] == "ok":
                if "response" in result and "data" in result["response"]:
                    response_data = result["response"]["data"]
                    if "statuses" in response_data and response_data["statuses"]:
                        status_info = response_data["statuses"][0]
                        if "resting" in status_info:
                            order_id = str(status_info["resting"]["oid"])
                            return order_id
            
            raise RuntimeError(f"Failed to place order: {result}")
            
        except Exception as e:
            raise RuntimeError(f"Failed to place {order.side.value} order: {e}")
    
    async def cancel_order(self, exchange_order_id: str) -> bool:
        """Cancel an order"""
        if not self.is_connected:
            raise RuntimeError("Not connected to exchange")
            
        try:
            # Convert to int (Hyperliquid uses integer order IDs)
            oid = int(exchange_order_id)
            
            result = self.exchange.cancel_order(oid)
            
            # Check if cancellation was successful
            if result and "status" in result:
                return result["status"] == "ok"
            
            return False
            
        except Exception as e:
            print(f"❌ Error cancelling order {exchange_order_id}: {e}")
            return False
    
    async def get_order_status(self, exchange_order_id: str) -> Order:
        """Get order status (simplified implementation)"""
        if not self.is_connected:
            raise RuntimeError("Not connected to exchange")
            
        # This would require maintaining order state or querying open orders
        # For now, return a basic order object
        return Order(
            id=exchange_order_id,
            asset="BTC",  # Would need to track this
            side=OrderSide.BUY,  # Would need to track this
            size=0.0,  # Would need to track this
            order_type=OrderType.LIMIT,  # Would need to track this
            status=OrderStatus.SUBMITTED,  # Would need to query actual status
            exchange_order_id=exchange_order_id
        )
    
    async def get_market_info(self, asset: str) -> MarketInfo:
        """Get market information"""
        if not self.is_connected:
            raise RuntimeError("Not connected to exchange")
            
        try:
            # Get market metadata
            meta = self.info.meta()
            universe = meta.get("universe", [])
            
            # Find asset info
            for asset_info in universe:
                if asset_info.get("name") == asset:
                    return MarketInfo(
                        symbol=asset,
                        base_asset=asset,
                        quote_asset="USD",  # Hyperliquid uses USD
                        min_order_size=float(asset_info.get("szDecimals", 4)) / 10000,
                        price_precision=int(asset_info.get("priceDecimals", 2)),
                        size_precision=int(asset_info.get("szDecimals", 4)),
                        is_active=True
                    )
            
            raise ValueError(f"Asset {asset} not found")
            
        except Exception as e:
            raise RuntimeError(f"Failed to get market info for {asset}: {e}")
    
    async def get_open_orders(self) -> List[Order]:
        """Get all open orders"""
        if not self.is_connected:
            return []
            
        try:
            open_orders = self.info.open_orders(self.exchange.wallet.address)
            orders = []
            
            for order_info in open_orders:
                order = Order(
                    id=str(order_info.get("oid", "")),
                    asset=order_info.get("coin", ""),
                    side=OrderSide.BUY if order_info.get("side") == "B" else OrderSide.SELL,
                    size=float(order_info.get("sz", 0)),
                    order_type=OrderType.LIMIT,  # Hyperliquid default
                    price=float(order_info.get("limitPx", 0)),
                    status=OrderStatus.SUBMITTED,
                    exchange_order_id=str(order_info.get("oid", ""))
                )
                orders.append(order)
            
            return orders
            
        except Exception as e:
            print(f"❌ Error getting open orders: {e}")
            return []
    
    async def health_check(self) -> bool:
        """Check connection health"""
        if not self.is_connected:
            return False
            
        try:
            # Simple health check - get account state
            self.info.user_state(self.exchange.wallet.address)
            return True
        except:
            return False