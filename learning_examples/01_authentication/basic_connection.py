#!/usr/bin/env python3
"""
Basic Hyperliquid Connection

Demonstrates how to:
- Create wallet from private key using eth-account
- Initialize Hyperliquid Info and Exchange SDK objects
- Test basic connection to testnet/mainnet

TRADING MODES:
- SPOT: Cash trading (buy/sell actual assets) 
- PERPS: Perpetual futures (leveraged derivatives trading)
- This example works for both modes - same authentication process
"""

import os
import asyncio
from dotenv import load_dotenv

load_dotenv()


async def main():
    """Connect to Hyperliquid using the Python SDK"""
    
    # Get private key from environment
    private_key = os.getenv("HYPERLIQUID_TESTNET_PRIVATE_KEY")
    if not private_key:
        print("❌ Set HYPERLIQUID_TESTNET_PRIVATE_KEY environment variable")
        return
    
    print("🔐 Connecting to Hyperliquid Testnet...")
    
    try:
        from hyperliquid.info import Info
        from hyperliquid.exchange import Exchange  
        from eth_account import Account
        
        # Create wallet from private key
        wallet = Account.from_key(private_key)
        print(f"🔑 Wallet address: {wallet.address}")
        
        # Initialize SDK objects
        # For testnet: use api.hyperliquid-testnet.xyz
        # For mainnet: use api.hyperliquid.xyz
        base_url = "https://api.hyperliquid-testnet.xyz"
        
        info = Info(base_url, skip_ws=True)
        exchange = Exchange(wallet, base_url)
        
        # Test connection by getting account state
        user_state = info.user_state(wallet.address)
        print("✅ Successfully connected to Hyperliquid!")
        print(f"📊 Account value: ${float(user_state.get('accountValue', 0)):,.2f}")
        
        # Show balances if any
        balances = user_state.get('balances', [])
        if balances:
            print("💰 Asset balances:")
            for balance in balances:
                coin = balance.get('coin', '')
                total = float(balance.get('total', 0))
                if total > 0:
                    print(f"   {coin}: {total}")
        else:
            print("💸 No asset balances (new testnet account)")
            
    except ImportError:
        print("❌ Install hyperliquid SDK: uv add hyperliquid-python-sdk")
    except Exception as e:
        print(f"❌ Connection failed: {e}")


if __name__ == "__main__":
    asyncio.run(main())