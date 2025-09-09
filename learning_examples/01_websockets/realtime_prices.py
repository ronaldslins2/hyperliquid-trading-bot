#!/usr/bin/env python3
"""
Real-time price monitoring using WebSocket connections.
Demonstrates subscribing to live market data and handling price updates.
"""

import asyncio
import json
import os
import signal
from dotenv import load_dotenv
import websockets

load_dotenv()

WS_URL = os.getenv("HYPERLIQUID_TESTNET_PUBLIC_WS_URL")
ASSETS_TO_TRACK = ["BTC", "ETH", "SOL", "DOGE", "AVAX"]

# Global state for demo
prices = {}
running = False

def signal_handler(signum, frame):
    """Handle Ctrl+C gracefully"""
    global running
    print(f"\nShutting down...")
    running = False

async def handle_price_message(data):
    """Process price update messages"""
    global prices
    
    channel = data.get("channel")
    if channel == "allMids":
        price_data = data.get("data", {})
        
        # Update prices and show changes for tracked assets
        for asset, price_str in price_data.items():
            if asset in ASSETS_TO_TRACK:
                try:
                    new_price = float(price_str)
                    old_price = prices.get(asset)
                    
                    # Store new price
                    prices[asset] = new_price
                    
                    if old_price is not None:
                        change = new_price - old_price
                        change_pct = (change / old_price) * 100 if old_price != 0 else 0
                        
                        # Show significant changes (>= 0.01%)
                        if abs(change_pct) >= 0.01:
                            direction = "📈" if change > 0 else "📉" if change < 0 else "➡️"
                            print(f"{direction} {asset}: ${new_price:,.2f} ({change_pct:+.2f}%)")
                    else:
                        # First price update
                        print(f"🔄 {asset}: ${new_price:,.2f}")
                        
                except (ValueError, TypeError):
                    continue
                    
    elif channel == "subscriptionUpdate":
        subscription = data.get("subscription", {})
        print(f"✅ Subscription confirmed: {subscription}")


async def monitor_prices():
    """Connect to WebSocket and monitor real-time prices"""
    global running
    
    print(f"🔗 Connecting to {WS_URL}")
    
    # Set up signal handler
    signal.signal(signal.SIGINT, signal_handler)
    
    try:
        async with websockets.connect(WS_URL) as websocket:
            print("✅ WebSocket connected!")
            
            # Subscribe to all market prices
            subscribe_message = {
                "method": "subscribe",
                "subscription": {"type": "allMids"}
            }
            
            await websocket.send(json.dumps(subscribe_message))
            print(f"📊 Monitoring {', '.join(ASSETS_TO_TRACK)}")
            print("=" * 40)
            
            running = True
            message_count = 0
            
            # Listen for messages
            async for message in websocket:
                if not running:
                    break
                    
                try:
                    data = json.loads(message)
                    await handle_price_message(data)
                    message_count += 1
                    
                    # Show status every 100 messages
                    if message_count % 100 == 0:
                        print(f"📈 Received {message_count} updates, tracking {len(prices)} assets")
                    
                except json.JSONDecodeError:
                    print("⚠️ Received invalid JSON")
                except Exception as e:
                    print(f"❌ Error: {e}")
                    
    except websockets.exceptions.ConnectionClosed:
        print("🔌 WebSocket connection closed")
    except Exception as e:
        print(f"❌ WebSocket error: {e}")
    finally:
        print("👋 Disconnected")


async def main():
    print("Hyperliquid Real-time Price Monitor")
    print("=" * 40)
    print("This demo shows live price updates via WebSocket")
    print("Press Ctrl+C to stop")
    print()
    
    if not WS_URL:
        print("❌ Missing HYPERLIQUID_TESTNET_PUBLIC_WS_URL environment variable")
        print("Set it in your .env file")
        return
    
    await monitor_prices()


if __name__ == "__main__":
    print("Starting WebSocket demo...")
    asyncio.run(main())