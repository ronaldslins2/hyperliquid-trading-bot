## Extensible grid trading bot for [Hyperliquid DEX](https://hyperliquid.xyz)

> ⚠️ This software is for educational and research purposes. Trading cryptocurrencies involves substantial risk of loss. Never trade with funds you cannot afford to lose. Always thoroughly test strategies on testnet before live deployment.**

This project is under active development. Feel free to submit questions, suggestions, and issues through GitHub.

## 🚀 Quick start

### **Prerequisites**
- [UV Package Manager](https://github.com/astral-sh/uv)
- Hyperliquid testnet account with testnet funds (see [Chainstack Hyperliquid faucet](https://faucet.chainstack.com/hyperliquid-testnet-faucet))

### **Installation**

```bash
# Clone the repository
git clone https://github.com/yourusername/hyperliquid-examples.git
cd hyperliquid-examples

# Install dependencies using UV
uv sync

# Set up environment variables
cp .env.example .env
# Edit .env with your Hyperliquid testnet private key
```

### **Configuration**

Create your environment file:
```bash
# .env
HYPERLIQUID_TESTNET_PRIVATE_KEY=0xYOUR_PRIVATE_KEY_HERE
HYPERLIQUID_TESTNET=true
```

The bot comes with a pre-configured conservative BTC grid strategy in `bots/btc_conservative.yaml`. Review and adjust parameters as needed.

### **Running the bot**

```bash
# Auto-discover and run the first active configuration
uv run src/run_bot.py

# Validate configuration before running
uv run src/run_bot.py --validate

# Run specific configuration
uv run src/run_bot.py bots/btc_conservative.yaml
```

## 📚 Learning examples

Master the Hyperliquid API with standalone educational scripts:

```bash
# Authentication and connection
uv run learning_examples/01_authentication/basic_connection.py

# Market data and pricing
uv run learning_examples/02_market_data/get_all_prices.py
uv run learning_examples/02_market_data/get_market_metadata.py

# Account information
uv run learning_examples/03_account_info/get_user_state.py
uv run learning_examples/03_account_info/get_open_orders.py

# Trading operations
uv run learning_examples/04_trading/place_limit_order.py
uv run learning_examples/04_trading/cancel_orders.py

# Real-time data
uv run learning_examples/05_websockets/realtime_prices.py
```

## ⚙️ Configuration

Bot configurations use YAML format with comprehensive parameter documentation:

```yaml
# Conservative BTC Grid Strategy
name: "btc_conservative_clean"
active: true  # Enable/disable this strategy

account:
  max_allocation_pct: 10.0  # Use only 10% of account balance

grid:
  symbol: "BTC"
  levels: 10               # Number of grid levels
  price_range:
    mode: "auto"           # Auto-calculate from current price
    auto:
      range_pct: 5.0      # ±5% price range (conservative)

risk_management:
  rebalance:
    price_move_threshold_pct: 12.0  # Rebalance trigger

monitoring:
  log_level: "INFO"       # DEBUG/INFO/WARNING/ERROR
```

## 🔧 Development

### **Package management**
This project uses [UV](https://github.com/astral-sh/uv) for fast, reliable dependency management:

```bash
uv sync              # Install/sync dependencies
uv add <package>     # Add new dependencies
uv run <command>     # Run commands in virtual environment
```

### **Testing**
All components are tested against Hyperliquid testnet:

```bash
# Test learning examples
uv run learning_examples/04_trading/place_limit_order.py

# Validate bot configuration
uv run src/run_bot.py --validate

# Run bot in testnet mode (default)
uv run src/run_bot.py
```
