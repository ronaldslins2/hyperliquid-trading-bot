#!/usr/bin/env python3
"""
Get Market Metadata  

Demonstrates:
- info.meta() SDK method
- Raw HTTP call to /info with type: meta
- Understanding trading pair information (decimals, leverage, etc.)

TRADING MODES:
- SPOT: No leverage constraints (leverage = 1x), actual asset ownership
- PERPS: Uses maxLeverage field for derivatives trading (up to 40x for BTC)
- szDecimals and price constraints apply to both spot and perps
"""

import asyncio
import httpx


async def method_1_sdk():
    """Method 1: Using Hyperliquid Python SDK"""
    
    print("🔧 Method 1: Hyperliquid SDK")
    print("-" * 30)
    
    try:
        from hyperliquid.info import Info
        
        info = Info("https://api.hyperliquid-testnet.xyz", skip_ws=True)
        
        # Get market metadata
        meta = info.meta()
        universe = meta.get("universe", [])
        
        print(f"📊 Found {len(universe)} trading pairs")
        
        # Show details for popular assets
        popular_assets = ["BTC", "ETH", "SOL"]
        
        for asset_info in universe:
            asset_name = asset_info.get("name", "")
            if asset_name in popular_assets:
                print(f"\n🔍 {asset_name} Details:")
                print(f"   Size decimals: {asset_info.get('szDecimals')}")
                print(f"   Price decimals: {asset_info.get('priceDecimals')}")  
                print(f"   Max leverage: {asset_info.get('maxLeverage')}x")
                print(f"   Only isolated: {asset_info.get('onlyIsolated', False)}")
                
        return meta
        
    except ImportError:
        print("❌ Install SDK: uv add hyperliquid-python-sdk")
        return None
    except Exception as e:
        print(f"❌ SDK method failed: {e}")
        return None


async def method_2_http():
    """Method 2: Raw HTTP call"""
    
    print("\n🌐 Method 2: Raw HTTP")
    print("-" * 25)
    
    try:
        async with httpx.AsyncClient() as client:
            response = await client.post(
                "https://api.hyperliquid-testnet.xyz/info",
                json={"type": "meta"},
                headers={"Content-Type": "application/json"}
            )
            
            if response.status_code == 200:
                meta = response.json()
                universe = meta.get("universe", [])
                
                print(f"📊 HTTP: Found {len(universe)} trading pairs")
                
                # Show same details  
                popular_assets = ["BTC", "ETH", "SOL"]
                
                for asset_info in universe:
                    asset_name = asset_info.get("name", "")
                    if asset_name in popular_assets:
                        print(f"\n🔍 {asset_name} Details:")
                        print(f"   Size decimals: {asset_info.get('szDecimals')}")
                        print(f"   Price decimals: {asset_info.get('priceDecimals')}")  
                        print(f"   Max leverage: {asset_info.get('maxLeverage')}x")
                        print(f"   Only isolated: {asset_info.get('onlyIsolated', False)}")
                
                return meta
            else:
                print(f"❌ HTTP failed: {response.status_code}")
                return None
                
    except Exception as e:
        print(f"❌ HTTP method failed: {e}")
        return None


async def analyze_trading_constraints():
    """Analyze trading constraints from metadata"""
    
    print("\n📋 Trading Constraints Analysis")
    print("-" * 35)
    
    try:
        async with httpx.AsyncClient() as client:
            response = await client.post(
                "https://api.hyperliquid-testnet.xyz/info",
                json={"type": "meta"},
                headers={"Content-Type": "application/json"}
            )
            
            if response.status_code == 200:
                meta = response.json()
                universe = meta.get("universe", [])
                
                print("🎯 Key Trading Information:")
                
                for asset_info in universe[:5]:  # Show first 5 assets
                    name = asset_info.get("name", "")
                    sz_decimals = asset_info.get("szDecimals", 4)
                    price_decimals = asset_info.get("priceDecimals", 2)
                    
                    # Calculate minimum order size
                    min_size = 1 / (10 ** sz_decimals)
                    price_tick = 1 / (10 ** price_decimals)
                    
                    print(f"\n📊 {name}:")
                    print(f"   Min order size: {min_size:.{sz_decimals}f} {name}")
                    print(f"   Price tick size: ${price_tick:.{price_decimals}f}")
                    print(f"   Max leverage: {asset_info.get('maxLeverage')}x")
                    
    except Exception as e:
        print(f"❌ Analysis failed: {e}")


async def main():
    """Demonstrate getting market metadata"""
    
    print("📊 Hyperliquid Market Metadata")
    print("=" * 40)
    
    # Compare both methods
    sdk_meta = await method_1_sdk()
    http_meta = await method_2_http()
    
    # Analyze constraints
    await analyze_trading_constraints()
    
    print(f"\n📚 Key Points:")
    print("• szDecimals: Size precision (affects minimum order size)")
    print("• priceDecimals: Price precision (affects price ticks)")
    print("• maxLeverage: Maximum allowed leverage for the asset")
    print("• onlyIsolated: If true, only isolated margin allowed")
    print("• Use this data to validate orders before placement")


if __name__ == "__main__":
    asyncio.run(main())