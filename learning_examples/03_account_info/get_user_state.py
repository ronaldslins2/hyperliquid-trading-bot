#!/usr/bin/env python3
"""
Get User Account State

Demonstrates:
- info.user_state(address) SDK method
- Raw HTTP call to /info with type: clearinghouseState
- Understanding account balances, positions, and margin

TRADING MODES:
- SPOT: Shows balances for owned assets (cash positions)
- PERPS: Shows leveraged positions, margin requirements, and funding
- API returns both spot balances and perps positions in same call
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
        
        # Create wallet and get address
        wallet = Account.from_key(private_key)
        address = wallet.address
        
        # Create Info object
        info = Info("https://api.hyperliquid-testnet.xyz", skip_ws=True)
        
        # Get user state
        user_state = info.user_state(address)
        
        print(f"📊 Account: {address}")
        print(f"💰 Account value: ${float(user_state.get('accountValue', 0)):,.2f}")
        
        # Show balances
        balances = user_state.get('balances', [])
        if balances:
            print("\n💳 Asset Balances:")
            for balance in balances:
                coin = balance.get('coin', '')
                total = float(balance.get('total', 0))
                hold = float(balance.get('hold', 0))
                available = total - hold
                
                if total > 0:
                    print(f"   {coin}:")
                    print(f"     Total: {total:.6f}")
                    print(f"     Available: {available:.6f}")
                    print(f"     Held: {hold:.6f}")
        else:
            print("\n💸 No asset balances")
            
        # Show positions
        positions = user_state.get('assetPositions', [])
        if positions:
            print(f"\n📈 Open Positions:")
            for pos in positions:
                position = pos.get('position', {})
                coin = position.get('coin', '')
                size = position.get('szi', '0')
                entry_px = position.get('entryPx')
                
                print(f"   {coin}: {size} @ ${entry_px}")
        else:
            print(f"\n📈 No open positions")
            
        return user_state
        
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
        
        # Get wallet address
        wallet = Account.from_key(private_key)
        address = wallet.address
        
        async with httpx.AsyncClient() as client:
            response = await client.post(
                "https://api.hyperliquid-testnet.xyz/info",
                json={
                    "type": "clearinghouseState",
                    "user": address
                },
                headers={"Content-Type": "application/json"}
            )
            
            if response.status_code == 200:
                user_state = response.json()
                
                print(f"📊 HTTP Account: {address}")
                print(f"💰 Account value: ${float(user_state.get('accountValue', 0)):,.2f}")
                
                # Show withdrawable amounts (useful info)
                withdrawable = user_state.get('withdrawable', {})
                if withdrawable and isinstance(withdrawable, dict):
                    print(f"\n💸 Withdrawable:")
                    for asset, amount in withdrawable.items():
                        if float(amount) > 0:
                            print(f"   {asset}: {float(amount):.6f}")
                else:
                    print(f"\n💸 No withdrawable amounts")
                
                return user_state
            else:
                print(f"❌ HTTP failed: {response.status_code}")
                return None
                
    except ImportError:
        print("❌ Install eth-account: uv add eth-account")
        return None  
    except Exception as e:
        print(f"❌ HTTP method failed: {e}")
        return None


async def analyze_account_health():
    """Analyze account health metrics"""
    
    print("\n🏥 Account Health Analysis")
    print("-" * 30)
    
    private_key = os.getenv("HYPERLIQUID_TESTNET_PRIVATE_KEY")
    if not private_key:
        print("❌ Set HYPERLIQUID_TESTNET_PRIVATE_KEY")
        return
    
    try:
        from hyperliquid.info import Info
        from eth_account import Account
        
        wallet = Account.from_key(private_key)
        info = Info("https://api.hyperliquid-testnet.xyz", skip_ws=True)
        user_state = info.user_state(wallet.address)
        
        # Key health metrics
        account_value = float(user_state.get('accountValue', 0))
        maintenance_margin = float(user_state.get('crossMaintenanceMarginUsed', 0))
        
        print(f"💰 Total account value: ${account_value:,.2f}")
        print(f"🛡️ Maintenance margin used: ${maintenance_margin:,.2f}")
        
        if account_value > 0:
            margin_ratio = (maintenance_margin / account_value) * 100
            print(f"📊 Margin utilization: {margin_ratio:.1f}%")
            
            if margin_ratio > 80:
                print("⚠️ HIGH RISK: Margin utilization above 80%")
            elif margin_ratio > 50:
                print("🟡 MEDIUM RISK: Margin utilization above 50%") 
            else:
                print("✅ LOW RISK: Healthy margin levels")
        
        # Check for liquidation risk
        liquidation_px = user_state.get('crossMarginSummary', {}).get('liquidationPx')
        if liquidation_px:
            print(f"💀 Liquidation price: ${liquidation_px}")
            
    except Exception as e:
        print(f"❌ Health analysis failed: {e}")


async def main():
    """Demonstrate getting user account state"""
    
    print("👤 Hyperliquid User Account State")
    print("=" * 40)
    
    # Compare both methods
    sdk_state = await method_1_sdk()
    http_state = await method_2_http()
    
    # Analyze account health
    await analyze_account_health()
    
    print(f"\n📚 Key Points:")
    print("• user_state requires wallet address parameter")
    print("• balances: Available and held amounts per asset")
    print("• assetPositions: Open trading positions")
    print("• accountValue: Total account value in USD")  
    print("• withdrawable: Assets available for withdrawal")
    print("• Use margin metrics to assess liquidation risk")


if __name__ == "__main__":
    asyncio.run(main())