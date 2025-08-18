#!/usr/bin/env python3
import asyncio
import logging
import os
from typing import Dict, List, Optional, Set

from eth_account import Account
from hyperliquid.exchange import Exchange
from hyperliquid.info import Info
from hyperliquid.utils import constants
from hyperliquid.utils.signing import OrderType

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class SpotSniper:
    def __init__(self, private_key: Optional[str], config: Dict):
        self.paper_trading = config.get('paper_trading', False)
        
        if self.paper_trading:
            self.wallet = None
            self.address = "PAPER_TRADING_MODE"
            self.exchange = None
            self.paper_balance = config.get('paper_balance', 10000)
            self.paper_trades = []
        else:
            self.wallet = Account.from_key(private_key)
            self.address = self.wallet.address
            self.exchange = Exchange(self.wallet, constants.MAINNET_API_URL)
        
        self.info = Info(constants.MAINNET_API_URL, skip_ws=True)
        self.config = config
        self.known_tokens: Set[str] = set()
        self.sniped_tokens: Set[str] = set()
        
    def get_spot_tokens(self) -> List[Dict]:
        try:
            spot_meta, _ = self.info.spot_meta_and_asset_ctxs()
            
            tokens = []
            for token in spot_meta['tokens']:
                if token['name'] != 'USDC':
                    tokens.append({
                        'name': token['name'],
                        'index': token['index'],
                        'szDecimals': token['szDecimals']
                    })
            
            return tokens
        except Exception as e:
            logger.error(f"Error fetching spot tokens: {e}")
            return []
    
    def get_token_price(self, token_name: str) -> Optional[float]:
        try:
            _, asset_ctxs = self.info.spot_meta_and_asset_ctxs()
            
            for asset in asset_ctxs:
                # Handle both formats: "TOKEN" and "TOKEN/USDC"
                coin = asset.get('coin', '')
                if coin == token_name or coin == f"{token_name}/USDC":
                    return float(asset['markPx']) if asset.get('markPx') else None
            
            return None
        except Exception as e:
            logger.error(f"Error getting token price for {token_name}: {e}")
            return None
    
    def place_market_buy(self, token_name: str, usdc_amount: float) -> bool:
        try:
            price = self.get_token_price(token_name)
            if not price:
                logger.warning(f"Could not get price for {token_name}")
                return False
            
            slippage = self.config.get('slippage', 0.05)
            limit_price = price * (1 + slippage)
            
            token_amount = usdc_amount / price
            
            if self.paper_trading:
                logger.info(f"[PAPER] Placing buy order for {token_amount:.4f} {token_name} at max price ${limit_price:.4f}")
                
                if self.paper_balance >= usdc_amount:
                    self.paper_balance -= usdc_amount
                    self.paper_trades.append({
                        'token': token_name,
                        'amount': token_amount,
                        'price': price,
                        'cost': usdc_amount
                    })
                    logger.info(f"[PAPER] Order filled! Remaining balance: ${self.paper_balance:.2f}")
                    return True
                else:
                    logger.warning(f"[PAPER] Insufficient balance. Need ${usdc_amount}, have ${self.paper_balance:.2f}")
                    return False
            else:
                logger.info(f"Placing buy order for {token_amount:.4f} {token_name} at max price ${limit_price:.4f}")
                
                result = self.exchange.order(
                    name=f"{token_name}:USDC",
                    is_buy=True,
                    sz=token_amount,
                    limit_px=limit_price,
                    order_type=OrderType.LIMIT,
                    reduce_only=False
                )
                
                if result and result.get('status') == 'ok':
                    logger.info(f"Successfully placed order for {token_name}: {result}")
                    return True
                else:
                    logger.error(f"Failed to place order for {token_name}: {result}")
                    return False
                
        except Exception as e:
            logger.error(f"Error placing order for {token_name}: {e}")
            return False
    
    def check_for_new_tokens(self) -> List[str]:
        current_tokens = self.get_spot_tokens()
        current_token_names = {token['name'] for token in current_tokens}
        
        new_tokens = current_token_names - self.known_tokens
        
        if self.known_tokens and new_tokens:
            logger.info(f"Found new tokens: {new_tokens}")
        
        self.known_tokens = current_token_names
        return list(new_tokens)
    
    async def monitor_and_snipe(self):
        mode = "[PAPER TRADING]" if self.paper_trading else "[LIVE TRADING]"
        logger.info(f"{mode} Starting sniper bot for address: {self.address}")
        logger.info(f"Config: Buy amount = ${self.config['buy_amount_usdc']}, Slippage = {self.config.get('slippage', 0.05)*100}%")
        if self.paper_trading:
            logger.info(f"Paper trading balance: ${self.paper_balance}")
        
        initial_tokens = self.get_spot_tokens()
        self.known_tokens = {token['name'] for token in initial_tokens}
        logger.info(f"Found {len(self.known_tokens)} existing tokens")
        
        while True:
            try:
                new_tokens = self.check_for_new_tokens()
                
                for token in new_tokens:
                    if token not in self.sniped_tokens:
                        logger.info(f"🎯 NEW TOKEN DETECTED: {token}")
                        
                        if self.place_market_buy(token, self.config['buy_amount_usdc']):
                            self.sniped_tokens.add(token)
                            logger.info(f"✅ Successfully sniped {token}")
                        else:
                            logger.warning(f"❌ Failed to snipe {token}")
                
                await asyncio.sleep(self.config.get('poll_interval', 1))
                
            except KeyboardInterrupt:
                logger.info("Shutting down bot...")
                if self.paper_trading and self.paper_trades:
                    logger.info("\n=== Paper Trading Summary ===")
                    logger.info(f"Total trades: {len(self.paper_trades)}")
                    total_spent = sum(t['cost'] for t in self.paper_trades)
                    logger.info(f"Total spent: ${total_spent:.2f}")
                    logger.info(f"Remaining balance: ${self.paper_balance:.2f}")
                    logger.info("Trades:")
                    for trade in self.paper_trades:
                        logger.info(f"  - {trade['token']}: {trade['amount']:.4f} @ ${trade['price']:.4f} = ${trade['cost']:.2f}")
                break
            except Exception as e:
                logger.error(f"Error in main loop: {e}")
                await asyncio.sleep(5)


async def main():
    config = {
        'buy_amount_usdc': float(os.getenv('BUY_AMOUNT_USDC', '100')),
        'slippage': float(os.getenv('SLIPPAGE', '0.05')),
        'poll_interval': float(os.getenv('POLL_INTERVAL', '0.5')),
        'paper_trading': os.getenv('PAPER_TRADING', 'false').lower() == 'true',
        'paper_balance': float(os.getenv('PAPER_BALANCE', '10000'))
    }
    
    private_key = os.getenv('HYPERLIQUID_PRIVATE_KEY')
    if not config['paper_trading'] and not private_key:
        logger.error("Please set HYPERLIQUID_PRIVATE_KEY environment variable or enable PAPER_TRADING")
        return
    
    sniper = SpotSniper(private_key, config)
    await sniper.monitor_and_snipe()


if __name__ == '__main__':
    asyncio.run(main())