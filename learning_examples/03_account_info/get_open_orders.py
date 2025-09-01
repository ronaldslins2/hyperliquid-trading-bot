#!/usr/bin/env python3
"""
Get Open Orders

Demonstrates:
- info.open_orders(address) SDK method
- Raw HTTP call to /info with type: openOrders
- Understanding order structure and status

TRADING MODES:
- SPOT: Shows open orders for cash trading (immediate settlement)
- PERPS: Shows open orders for leveraged derivatives trading
- Same API returns both spot and perps orders together
"""

import os
import asyncio
import httpx
from dotenv import load_dotenv

load_dotenv()


async def method_1_sdk():
    """Method 1: Using Hyperliquid Python SDK"""
    
    print("🔧 Method 1: Hyperliquid SDK")
    print("-" * 30)
    
    private_key = os.getenv("HYPERLIQUID_TESTNET_PRIVATE_KEY")
    if not private_key:
        print("❌ Set HYPERLIQUID_TESTNET_PRIVATE_KEY")
        return None
    
    try:
        from hyperliquid.info import Info
        from eth_account import Account
        
        # Setup
        wallet = Account.from_key(private_key)
        info = Info("https://api.hyperliquid-testnet.xyz", skip_ws=True)
        
        # Get open orders
        open_orders = info.open_orders(wallet.address)
        
        print(f"📋 Found {len(open_orders)} open orders")
        
        if open_orders:
            for order in open_orders:
                oid = order.get('oid', '')
                coin = order.get('coin', '')
                side = "BUY" if order.get('side') == 'B' else "SELL"
                size = order.get('sz', '0')
                limit_px = order.get('limitPx', '0')
                timestamp = order.get('timestamp', 0)
                
                print(f"\n📄 Order {oid}:")
                print(f"   Asset: {coin}")
                print(f"   Side: {side}")
                print(f"   Size: {size}")
                print(f"   Price: ${float(limit_px):,.2f}")
                print(f"   Timestamp: {timestamp}")
                
                # Show order value
                order_value = float(size) * float(limit_px)
                print(f"   Total value: ${order_value:,.2f}")
        else:
            print("📭 No open orders")
            
        return open_orders
        
    except ImportError:
        print("❌ Install packages: uv add hyperliquid-python-sdk eth-account")
        return None
    except Exception as e:
        print(f"❌ SDK method failed: {e}")
        return None


async def method_2_http():
    """Method 2: Raw HTTP call"""
    
    print("\n🌐 Method 2: Raw HTTP")
    print("-" * 25)
    
    private_key = os.getenv("HYPERLIQUID_TESTNET_PRIVATE_KEY")
    if not private_key:
        print("❌ Set HYPERLIQUID_TESTNET_PRIVATE_KEY")
        return None
    
    try:
        from eth_account import Account
        
        wallet = Account.from_key(private_key)
        
        async with httpx.AsyncClient() as client:
            response = await client.post(
                "https://api.hyperliquid-testnet.xyz/info",
                json={
                    "type": "openOrders",
                    "user": wallet.address
                },
                headers={"Content-Type": "application/json"}
            )
            
            if response.status_code == 200:
                open_orders = response.json()
                
                print(f"📋 HTTP: Found {len(open_orders)} open orders")
                
                if open_orders:
                    for order in open_orders:
                        oid = order.get('oid', '')
                        coin = order.get('coin', '')
                        side = "BUY" if order.get('side') == 'B' else "SELL"
                        size = order.get('sz', '0')
                        limit_px = order.get('limitPx', '0')
                        
                        print(f"\n📄 HTTP Order {oid}:")
                        print(f"   {side} {size} {coin} @ ${float(limit_px):,.2f}")
                        
                        # Calculate how far from current market price
                        # (would need to fetch current price for comparison)
                        
                return open_orders
            else:
                print(f"❌ HTTP failed: {response.status_code}")
                return None
                
    except ImportError:
        print("❌ Install eth-account: uv add eth-account")
        return None
    except Exception as e:
        print("❌ HTTP method failed: {e}")
        return None


async def analyze_open_orders():
    """Analyze open orders for insights"""
    
    print("\n🔍 Order Analysis")
    print("-" * 20)
    
    private_key = os.getenv("HYPERLIQUID_TESTNET_PRIVATE_KEY")
    if not private_key:
        print("❌ Set HYPERLIQUID_TESTNET_PRIVATE_KEY")
        return
        
    try:
        from hyperliquid.info import Info
        from eth_account import Account
        
        wallet = Account.from_key(private_key)
        info = Info("https://api.hyperliquid-testnet.xyz", skip_ws=True)
        
        # Get both open orders and current prices
        open_orders = info.open_orders(wallet.address)
        all_prices = info.all_mids()
        
        if not open_orders:
            print("📭 No orders to analyze")
            return
            
        print("📊 Order Distance from Market:")
        
        buy_orders = []
        sell_orders = []
        
        for order in open_orders:
            coin = order.get('coin', '')
            side = order.get('side', '')
            limit_px = float(order.get('limitPx', 0))
            size = float(order.get('sz', 0))
            
            if coin in all_prices:
                market_price = float(all_prices[coin])
                distance_pct = ((limit_px - market_price) / market_price) * 100
                
                order_info = {
                    'coin': coin,
                    'side': side,
                    'price': limit_px,
                    'size': size,
                    'market_price': market_price,
                    'distance_pct': distance_pct
                }
                
                if side == 'B':
                    buy_orders.append(order_info)
                else:
                    sell_orders.append(order_info)
        
        # Show buy orders (should be below market)
        if buy_orders:
            print(f"\n🟢 Buy Orders ({len(buy_orders)}):")
            for order in buy_orders:
                print(f"   {order['coin']}: ${order['price']:,.2f} "
                      f"(Market: ${order['market_price']:,.2f}, "
                      f"{order['distance_pct']:+.1f}%)")
        
        # Show sell orders (should be above market) 
        if sell_orders:
            print(f"\n🔴 Sell Orders ({len(sell_orders)}):")
            for order in sell_orders:
                print(f"   {order['coin']}: ${order['price']:,.2f} "
                      f"(Market: ${order['market_price']:,.2f}, "
                      f"{order['distance_pct']:+.1f}%)")
        
        # Calculate total locked value
        total_buy_value = sum(o['price'] * o['size'] for o in buy_orders)
        total_sell_value = sum(o['price'] * o['size'] for o in sell_orders)
        
        print(f"\n💰 Locked Value:")
        print(f"   Buy orders: ${total_buy_value:,.2f}")
        print(f"   Sell orders: ${total_sell_value:,.2f}")
        print(f"   Total: ${total_buy_value + total_sell_value:,.2f}")
        
    except Exception as e:
        print(f"❌ Analysis failed: {e}")


async def main():
    """Demonstrate getting open orders"""
    
    print("📋 Hyperliquid Open Orders")
    print("=" * 40)
    
    # Compare both methods
    sdk_orders = await method_1_sdk()
    http_orders = await method_2_http()
    
    # Analyze orders
    await analyze_open_orders()
    
    print(f"\n📚 Key Points:")
    print("• oid: Unique order identifier for cancellation")
    print("• coin: Trading pair (BTC, ETH, etc.)")
    print("• side: 'B' for buy, 'S' for sell")
    print("• sz: Order size in base asset")
    print("• limitPx: Limit price for the order")
    print("• Orders remain open until filled or cancelled")


if __name__ == "__main__":
    asyncio.run(main())