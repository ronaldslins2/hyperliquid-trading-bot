#!/usr/bin/env python3
"""
Cancel Orders

Demonstrates:
- exchange.cancel_order() SDK method
- Raw HTTP call to /exchange with cancel action
- Bulk order cancellation strategies

TRADING MODES:
- SPOT: Cancels open spot orders (no leverage impact)
- PERPS: Cancels open perps orders (may affect margin requirements)
- Same cancellation methods work for both spot and perps orders
"""

import os
import asyncio
import json
import time
from dotenv import load_dotenv

load_dotenv()


async def method_1_sdk():
    """Method 1: Using Hyperliquid Python SDK"""
    
    print("🔧 Method 1: Hyperliquid SDK")
    print("-" * 30)
    
    private_key = os.getenv("HYPERLIQUID_TESTNET_PRIVATE_KEY")
    if not private_key:
        print("❌ Set HYPERLIQUID_TESTNET_PRIVATE_KEY")
        return
    
    try:
        from hyperliquid.exchange import Exchange
        from hyperliquid.info import Info
        from eth_account import Account
        
        # Setup
        wallet = Account.from_key(private_key)
        exchange = Exchange(wallet, "https://api.hyperliquid-testnet.xyz")
        info = Info("https://api.hyperliquid-testnet.xyz", skip_ws=True)
        
        # Get current open orders
        open_orders = info.open_orders(wallet.address)
        
        if not open_orders:
            print("📭 No open orders to cancel")
            return
            
        print(f"📋 Found {len(open_orders)} open orders")
        
        # Show orders
        for i, order in enumerate(open_orders, 1):
            oid = order.get('oid', '')
            coin = order.get('coin', '')
            side = "BUY" if order.get('side') == 'B' else "SELL"
            size = order.get('sz', '0')
            price = float(order.get('limitPx', 0))
            
            print(f"   {i}. Order {oid}: {side} {size} {coin} @ ${price:,.2f}")
        
        # Cancel first order as example
        if open_orders:
            first_order = open_orders[0]
            order_id = first_order.get('oid')
            
            print(f"\n🗑️ Cancelling order {order_id}...")
            
            # Cancel order
            result = exchange.cancel_order(
                coin=first_order.get('coin', ''),
                oid=order_id
            )
            
            print(f"📄 Cancel result:")
            print(json.dumps(result, indent=2))
            
            # Check if successful
            if result and result.get("status") == "ok":
                print(f"✅ Order {order_id} cancelled successfully!")
                
                # Verify cancellation
                await asyncio.sleep(2)
                new_orders = info.open_orders(wallet.address)
                
                still_exists = any(o.get('oid') == order_id for o in new_orders)
                if not still_exists:
                    print(f"✅ Cancellation confirmed - order removed")
                else:
                    print(f"⚠️ Order still appears (may take time)")
            else:
                print(f"❌ Cancellation failed")
        
    except ImportError:
        print("❌ Install packages: uv add hyperliquid-python-sdk eth-account")
    except Exception as e:
        print(f"❌ SDK method failed: {e}")


async def method_2_bulk_cancel():
    """Method 2: Bulk cancel multiple orders"""
    
    print("\n🗂️ Method 2: Bulk Cancellation")
    print("-" * 35)
    
    private_key = os.getenv("HYPERLIQUID_TESTNET_PRIVATE_KEY")
    if not private_key:
        print("❌ Set HYPERLIQUID_TESTNET_PRIVATE_KEY")
        return
    
    try:
        from hyperliquid.exchange import Exchange
        from hyperliquid.info import Info
        from eth_account import Account
        
        wallet = Account.from_key(private_key)
        exchange = Exchange(wallet, "https://api.hyperliquid-testnet.xyz")
        info = Info("https://api.hyperliquid-testnet.xyz", skip_ws=True)
        
        # Get current open orders
        open_orders = info.open_orders(wallet.address)
        
        if len(open_orders) <= 1:
            print("📭 Need at least 2 orders for bulk cancel demo")
            return
            
        # Cancel multiple orders (limit to 3 for safety)
        orders_to_cancel = open_orders[:min(3, len(open_orders))]
        
        print(f"🗑️ Bulk cancelling {len(orders_to_cancel)} orders...")
        
        cancelled_count = 0
        for order in orders_to_cancel:
            try:
                oid = order.get('oid')
                coin = order.get('coin', '')
                
                result = exchange.cancel_order(coin=coin, oid=oid)
                
                if result and result.get("status") == "ok":
                    cancelled_count += 1
                    print(f"   ✅ Cancelled order {oid}")
                else:
                    print(f"   ❌ Failed to cancel {oid}")
                    
                # Small delay between cancellations
                await asyncio.sleep(0.5)
                
            except Exception as e:
                print(f"   ❌ Error cancelling {oid}: {e}")
        
        print(f"\n📊 Bulk cancel summary: {cancelled_count}/{len(orders_to_cancel)} successful")
        
    except Exception as e:
        print(f"❌ Bulk cancel failed: {e}")


async def method_3_cancel_by_asset():
    """Method 3: Cancel all orders for specific asset"""
    
    print("\n🎯 Method 3: Cancel by Asset")
    print("-" * 30)
    
    private_key = os.getenv("HYPERLIQUID_TESTNET_PRIVATE_KEY")
    if not private_key:
        print("❌ Set HYPERLIQUID_TESTNET_PRIVATE_KEY")
        return
    
    try:
        from hyperliquid.exchange import Exchange
        from hyperliquid.info import Info
        from eth_account import Account
        
        wallet = Account.from_key(private_key)
        exchange = Exchange(wallet, "https://api.hyperliquid-testnet.xyz")
        info = Info("https://api.hyperliquid-testnet.xyz", skip_ws=True)
        
        # Get open orders
        open_orders = info.open_orders(wallet.address)
        
        if not open_orders:
            print("📭 No orders to cancel")
            return
        
        # Group by asset
        orders_by_asset = {}
        for order in open_orders:
            coin = order.get('coin', '')
            if coin not in orders_by_asset:
                orders_by_asset[coin] = []
            orders_by_asset[coin].append(order)
        
        print(f"📊 Orders by asset:")
        for asset, orders in orders_by_asset.items():
            print(f"   {asset}: {len(orders)} orders")
        
        # Cancel all BTC orders as example
        if 'BTC' in orders_by_asset:
            btc_orders = orders_by_asset['BTC']
            print(f"\n🗑️ Cancelling all {len(btc_orders)} BTC orders...")
            
            cancelled = 0
            for order in btc_orders:
                try:
                    result = exchange.cancel_order(
                        coin='BTC',
                        oid=order.get('oid')
                    )
                    
                    if result and result.get("status") == "ok":
                        cancelled += 1
                        
                    await asyncio.sleep(0.3)
                    
                except Exception as e:
                    print(f"   ❌ Error: {e}")
            
            print(f"✅ Cancelled {cancelled}/{len(btc_orders)} BTC orders")
        else:
            print("💡 No BTC orders to cancel")
        
    except Exception as e:
        print(f"❌ Asset cancel failed: {e}")


async def demonstrate_cancel_strategies():
    """Show different cancellation strategies"""
    
    print("\n📚 Cancellation Strategies")
    print("-" * 30)
    
    print("1️⃣ SINGLE ORDER:")
    print("   • Cancel specific order by ID")
    print("   • Good for precise control")
    print("   • Use when you know exact order to cancel")
    
    print("\n2️⃣ BULK CANCEL:")
    print("   • Cancel multiple orders at once")
    print("   • Good for portfolio rebalancing") 
    print("   • Add delays between cancellations")
    
    print("\n3️⃣ CANCEL BY ASSET:")
    print("   • Cancel all orders for specific trading pair")
    print("   • Good for risk management")
    print("   • Useful before major market events")
    
    print("\n4️⃣ CANCEL ALL:")
    print("   • Emergency cancellation of all orders")
    print("   • Good for stopping all trading activity")
    print("   • Use in high volatility or system issues")
    
    print("\n⚠️ BEST PRACTICES:")
    print("• Add delays between bulk cancellations")
    print("• Always verify cancellation success")
    print("• Handle partial failures gracefully")
    print("• Consider rate limits for large batches")


async def main():
    """Demonstrate order cancellation methods"""
    
    print("🗑️ Hyperliquid Order Cancellation")
    print("=" * 40)
    
    # Check if user has orders to cancel
    private_key = os.getenv("HYPERLIQUID_TESTNET_PRIVATE_KEY")
    if private_key:
        try:
            from hyperliquid.info import Info
            from eth_account import Account
            
            wallet = Account.from_key(private_key)
            info = Info("https://api.hyperliquid-testnet.xyz", skip_ws=True)
            orders = info.open_orders(wallet.address)
            
            if not orders:
                print("📭 No open orders found")
                print("💡 Place some orders first using place_limit_order.py")
                print("\n⚠️ Showing methods for educational purposes...")
            else:
                print("⚠️ This will cancel REAL orders on testnet!")
                proceed = input("\nProceed with cancellation examples? (y/N): ").lower().strip()
                if proceed != 'y':
                    print("👋 Cancellation examples skipped")
                    await demonstrate_cancel_strategies()
                    return
        except:
            pass
    
    # Demonstrate methods
    await method_1_sdk()
    await method_2_bulk_cancel()
    await method_3_cancel_by_asset()
    await demonstrate_cancel_strategies()
    
    print(f"\n📚 Key Points:")
    print("• cancel_order() requires coin and order ID (oid)")
    print("• Always check cancellation result status")
    print("• Orders may take time to disappear from open_orders")
    print("• Use bulk cancellation with delays for large batches")
    print("• SDK handles all authentication and signing")


if __name__ == "__main__":
    asyncio.run(main())