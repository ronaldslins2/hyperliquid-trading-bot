#!/usr/bin/env python3
import asyncio
import os

# Force paper trading mode for testing
os.environ['PAPER_TRADING'] = 'true'
os.environ['PAPER_BALANCE'] = '1000'
os.environ['BUY_AMOUNT_USDC'] = '250'
os.environ['POLL_INTERVAL'] = '1'

from sniper_bot import SpotSniper

async def test_paper_trading():
    config = {
        'buy_amount_usdc': 250,
        'slippage': 0.05,
        'poll_interval': 1,
        'paper_trading': True,
        'paper_balance': 1000
    }
    
    sniper = SpotSniper(None, config)
    
    print(f"Paper trading mode: {sniper.paper_trading}")
    print(f"Paper balance: ${sniper.paper_balance}")
    print(f"Address: {sniper.address}")
    
    # Test getting tokens
    tokens = sniper.get_spot_tokens()
    print(f"Found {len(tokens)} tokens")
    
    # Find a token with a price
    test_token = None
    for token in tokens[:10]:
        price = sniper.get_token_price(token['name'])
        if price:
            test_token = token['name']
            print(f"Found token with price: {test_token} at ${price:.4f}")
            break
    
    if test_token:
        print(f"\nSimulating buy of {test_token}...")
        success = sniper.place_market_buy(test_token, 250)
        print(f"Buy result: {'Success' if success else 'Failed'}")
        print(f"Remaining balance: ${sniper.paper_balance}")
        
        # Try to buy again with insufficient funds
        print(f"\nTrying to buy with insufficient funds...")
        success = sniper.place_market_buy(test_token, 1000)
        print(f"Buy result: {'Success' if success else 'Failed'}")

if __name__ == '__main__':
    asyncio.run(test_paper_trading())