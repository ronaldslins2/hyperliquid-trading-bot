#!/usr/bin/env python3
import os
from hyperliquid.info import Info
from hyperliquid.utils import constants

def test_connection():
    print("Testing Hyperliquid connection...")
    
    info = Info(constants.MAINNET_API_URL, skip_ws=True)
    
    try:
        spot_meta, asset_ctxs = info.spot_meta_and_asset_ctxs()
        
        print(f"✅ Connection successful!")
        print(f"Found {len(spot_meta['tokens'])} tokens")
        
        print("\nFirst 5 spot tokens:")
        for i, token in enumerate(spot_meta['tokens'][:5]):
            if token['name'] != 'USDC':
                print(f"  - {token['name']}")
        
        print("\nCurrent prices for first 5 tokens:")
        for asset in asset_ctxs[:5]:
            if asset['coin'] != 'USDC' and asset['markPx']:
                print(f"  - {asset['coin']}: ${asset['markPx']}")
                
    except Exception as e:
        print(f"❌ Error: {e}")

if __name__ == '__main__':
    test_connection()