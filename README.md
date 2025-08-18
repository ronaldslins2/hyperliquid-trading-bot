# Hyperliquid Spot Token Sniper Bot

A simple bot that monitors Hyperliquid for new spot token listings and automatically buys them when detected.

## Features

- Monitors Hyperliquid spot market for new token listings
- Automatically places market buy orders for new tokens
- Paper trading mode for testing without real funds
- Configurable buy amount and slippage tolerance
- Simple logging for tracking operations

## Setup

1. Install dependencies:
```bash
uv sync
```

2. Configure environment variables:
```bash
cp .env.example .env
# Edit .env with your private key and settings
```

3. Run the bot:
```bash
uv run python sniper_bot.py
```

## Configuration

- `HYPERLIQUID_PRIVATE_KEY`: Your wallet private key (required for live trading)
- `PAPER_TRADING`: Enable paper trading mode - no real trades (default: false)
- `PAPER_BALANCE`: Starting balance for paper trading in USDC (default: 10000)
- `BUY_AMOUNT_USDC`: Amount in USDC to spend on each new token (default: 100)
- `SLIPPAGE`: Maximum slippage tolerance (default: 0.05 = 5%)
- `POLL_INTERVAL`: How often to check for new tokens in seconds (default: 0.5)

## Paper Trading

To test the bot without real funds:
```bash
PAPER_TRADING=true uv run python sniper_bot.py
```

Or set in your `.env` file:
```
PAPER_TRADING=true
PAPER_BALANCE=10000
```

## Warning

This bot will automatically buy tokens as soon as they are listed. Use at your own risk and only with funds you can afford to lose.