#!/usr/bin/env python3
"""
Place Limit Orders

Demonstrates:
- exchange.order() SDK method (correct method name)
- Raw HTTP call to /exchange with limit order action
- Order validation and response handling

TRADING MODES:
- SPOT: Places limit orders for immediate asset ownership (no leverage)
- PERPS: Places leveraged limit orders for derivatives trading
- Same API method works for both - leverage determined by position sizing
"""

import os
import asyncio
import json
import time
import sys
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
        from hyperliquid.exchange import Exchange
        from hyperliquid.info import Info
        from eth_account import Account
        
        # Setup
        wallet = Account.from_key(private_key)
        exchange = Exchange(wallet, "https://api.hyperliquid-testnet.xyz")
        info = Info("https://api.hyperliquid-testnet.xyz", skip_ws=True)
        
        # Get current BTC price to place order below market
        all_prices = info.all_mids()
        btc_price = float(all_prices.get('BTC', 0))
        
        if btc_price == 0:
            print("❌ Could not get BTC price")
            return None
            
        # Place buy order 5% below market
        order_price = btc_price * 0.95
        # Round to whole dollars (BTC appears to trade in $1 increments)
        order_price = round(order_price, 0)
        
        order_size = 0.001  # Small test size
        # Round to BTC size decimals (5 decimal places)
        order_size = round(order_size, 5)
        
        print(f"📊 Current BTC price: ${btc_price:,.2f}")
        print(f"🎯 Placing buy order: {order_size} BTC @ ${order_price:,.2f}")
        
        # Place limit order (correct SDK method is 'order', not 'limit_order')
        from hyperliquid.utils.signing import OrderType as HLOrderType
        
        result = exchange.order(
            name="BTC",  # SDK uses 'name' parameter, not 'coin'
            is_buy=True,
            sz=order_size,
            limit_px=order_price,
            order_type=HLOrderType({"limit": {"tif": "Gtc"}}),
            reduce_only=False
        )
        
        print(f"📄 Order result:")
        print(json.dumps(result, indent=2))
        
        # Extract order ID if successful
        if result and result.get("status") == "ok":
            response_data = result.get("response", {}).get("data", {})
            statuses = response_data.get("statuses", [])
            
            if statuses:
                status_info = statuses[0]
                if "resting" in status_info:
                    order_id = status_info["resting"]["oid"]
                    print(f"✅ Order placed successfully! ID: {order_id}")
                    return order_id
                elif "filled" in status_info:
                    print(f"🎯 Order filled immediately!")
                    return "filled"
        
        print(f"❌ Order placement unclear")
        return None
        
    except ImportError:
        print("❌ Install packages: uv add hyperliquid-python-sdk eth-account")
        return None
    except Exception as e:
        print(f"❌ SDK method failed: {e}")
        return None
        
    except ImportError:
        print("❌ Install eth-account: uv add eth-account")
        return None
    except Exception as e:
        print(f"❌ HTTP method failed: {e}")
        return None


async def verify_order_placement(order_id):
    """Verify order was placed by checking open orders"""
    
    if not order_id or order_id in ["filled", "http_demo"]:
        return
        
    print(f"\n🔍 Verifying Order Placement")
    print("-" * 30)
    
    private_key = os.getenv("HYPERLIQUID_TESTNET_PRIVATE_KEY")
    if not private_key:
        return
        
    try:
        from hyperliquid.info import Info
        from eth_account import Account
        
        wallet = Account.from_key(private_key)
        info = Info("https://api.hyperliquid-testnet.xyz", skip_ws=True)
        
        # Wait a moment for order to appear
        await asyncio.sleep(2)
        
        # Check open orders
        open_orders = info.open_orders(wallet.address)
        
        order_found = False
        for order in open_orders:
            if str(order.get('oid', '')) == str(order_id):
                order_found = True
                print(f"✅ Order confirmed in system:")
                print(f"   ID: {order.get('oid')}")
                print(f"   Asset: {order.get('coin')}")
                print(f"   Side: {'BUY' if order.get('side') == 'B' else 'SELL'}")
                print(f"   Size: {order.get('sz')}")
                print(f"   Price: ${float(order.get('limitPx', 0)):,.2f}")
                break
                
        if not order_found:
            print(f"⚠️ Order {order_id} not found in open orders")
            print("   (May have been filled immediately)")
            
    except Exception as e:
        print(f"❌ Verification failed: {e}")


async def main():
    """Demonstrate placing limit orders"""
    
    print("📝 Hyperliquid Limit Orders")
    print("=" * 40)
    print("⚠️ This will place REAL orders on testnet!")
    
    # Confirm with user
    proceed = input("\nProceed with order placement? (y/N): ").lower().strip()
    if proceed != 'y':
        print("👋 Order examples cancelled")
        return
    
    # Try SDK method
    order_id = await method_1_sdk()
    
    # Verify order placement
    await verify_order_placement(order_id)
    
    print(f"\n📚 Key Points:")
    print("• exchange.order() places orders at specific prices (NOT limit_order)")
    print("• is_buy: True for buy orders, False for sell orders")
    print("• sz: Order size in base asset (BTC, ETH, etc.)")
    print("• limit_px: Exact price for order execution")
    print("• reduce_only: True to only reduce positions")
    print("• BTC prices must be rounded to whole dollars ($1 increments)")
    print("• Orders stay open until filled or cancelled")
    print("• SDK handles all signing complexity for you")


if __name__ == "__main__":
    asyncio.run(main())