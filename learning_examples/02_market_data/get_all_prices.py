#!/usr/bin/env python3
"""
Get All Market Prices

Demonstrates:
- info.all_mids() SDK method  
- Raw HTTP call to /info with type: allMids
- Parsing price data for specific assets

TRADING MODES:
- SPOT: Returns spot prices for immediate settlement
- PERPS: Returns perpetual futures prices (may differ from spot due to funding rates)
- This API returns both spot and perps prices in the same call
"""

import asyncio
import httpx


async def method_1_sdk():
    """Method 1: Using Hyperliquid Python SDK"""
    
    print("🔧 Method 1: Hyperliquid SDK")
    print("-" * 30)
    
    try:
        from hyperliquid.info import Info
        
        # Create Info object (no authentication needed for market data)
        info = Info("https://api.hyperliquid-testnet.xyz", skip_ws=True)
        
        # Get all market prices  
        all_prices = info.all_mids()
        
        print(f"📊 Got prices for {len(all_prices)} assets")
        
        # Show popular assets
        popular_assets = ["BTC", "ETH", "SOL", "DOGE", "AVAX"]
        for asset in popular_assets:
            if asset in all_prices:
                price = float(all_prices[asset])
                print(f"   {asset}: ${price:,.2f}")
                
        return all_prices
        
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
                json={"type": "allMids"},
                headers={"Content-Type": "application/json"}
            )
            
            if response.status_code == 200:
                all_prices = response.json()
                print(f"📊 HTTP: Got prices for {len(all_prices)} assets")
                
                # Show same popular assets
                popular_assets = ["BTC", "ETH", "SOL", "DOGE", "AVAX"]
                for asset in popular_assets:
                    if asset in all_prices:
                        price = float(all_prices[asset])
                        print(f"   {asset}: ${price:,.2f}")
                        
                return all_prices
            else:
                print(f"❌ HTTP failed: {response.status_code}")
                return None
                
    except Exception as e:
        print(f"❌ HTTP method failed: {e}")
        return None


async def compare_methods():
    """Compare SDK vs HTTP methods"""
    
    print("\n🔍 Comparing Methods")
    print("-" * 25)
    
    # Get data from both methods
    sdk_prices = await method_1_sdk()
    http_prices = await method_2_http()
    
    if sdk_prices and http_prices:
        # Compare a few assets
        test_assets = ["BTC", "ETH", "SOL"]
        
        print("📊 Price comparison:")
        for asset in test_assets:
            if asset in sdk_prices and asset in http_prices:
                sdk_price = float(sdk_prices[asset])
                http_price = float(http_prices[asset])
                
                match = "✅" if sdk_price == http_price else "❌"
                print(f"   {asset}: SDK=${sdk_price:,.2f} | HTTP=${http_price:,.2f} {match}")


async def main():
    """Demonstrate getting all market prices"""
    
    print("📊 Hyperliquid Market Prices")
    print("=" * 40)
    
    await compare_methods()


if __name__ == "__main__":
    asyncio.run(main())