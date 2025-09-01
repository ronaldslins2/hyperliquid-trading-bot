#!/usr/bin/env python3
"""
Real-Time Price Updates via WebSocket

Demonstrates:
- WebSocket connection to Hyperliquid
- Subscribing to allMids price updates
- Handling real-time price data
- Connection management and reconnection

TRADING MODES:
- SPOT: Receives real-time spot prices for immediate trading
- PERPS: Receives real-time perps prices (may include funding rate effects)
- WebSocket streams both spot and perps prices simultaneously
"""

import asyncio
import json
import signal
import websockets


class PriceMonitor:
    """Simple real-time price monitor using WebSocket"""
    
    def __init__(self, testnet=True):
        self.testnet = testnet
        self.ws_url = (
            "wss://api.hyperliquid-testnet.xyz/ws" if testnet 
            else "wss://api.hyperliquid.xyz/ws"
        )
        self.running = False
        self.websocket = None
        self.prices = {}
        
    def signal_handler(self, signum, frame):
        """Handle Ctrl+C gracefully"""
        print(f"\n📡 Received signal {signum}, shutting down...")
        self.running = False
        
    async def connect_and_monitor(self):
        """Connect to WebSocket and monitor prices"""
        
        print(f"📡 Connecting to Hyperliquid WebSocket...")
        print(f"🌐 URL: {self.ws_url}")
        
        # Setup signal handler
        signal.signal(signal.SIGINT, self.signal_handler)
        
        try:
            async with websockets.connect(self.ws_url) as websocket:
                self.websocket = websocket
                print("✅ WebSocket connected!")
                
                # Subscribe to all market prices
                subscribe_message = {
                    "method": "subscribe",
                    "subscription": {
                        "type": "allMids"
                    }
                }
                
                await websocket.send(json.dumps(subscribe_message))
                print("📊 Subscribed to allMids (all market prices)")
                print("💡 Price updates will appear below:")
                print("-" * 40)
                
                self.running = True
                message_count = 0
                
                # Listen for messages
                async for message in websocket:
                    if not self.running:
                        break
                        
                    try:
                        data = json.loads(message)
                        await self.handle_message(data)
                        message_count += 1
                        
                        # Show status every 50 messages
                        if message_count % 50 == 0:
                            print(f"📊 Received {message_count} price updates, "
                                  f"tracking {len(self.prices)} assets")
                        
                    except json.JSONDecodeError:
                        print("⚠️ Received non-JSON message")
                    except Exception as e:
                        print(f"❌ Error handling message: {e}")
                        
        except websockets.exceptions.ConnectionClosed:
            print("🔌 WebSocket connection closed")
        except Exception as e:
            print(f"❌ WebSocket error: {e}")
        finally:
            print("🔌 WebSocket disconnected")
            
    async def handle_message(self, data):
        """Process incoming WebSocket message"""
        
        # Check if this is a price update
        channel = data.get("channel")
        if channel == "allMids":
            price_data = data.get("data", {})
            
            # Update our price cache and show changes
            for asset, price_str in price_data.items():
                try:
                    new_price = float(price_str)
                    old_price = self.prices.get(asset)
                    
                    # Store new price
                    self.prices[asset] = new_price
                    
                    # Show popular assets with price changes
                    if asset in ["BTC", "ETH", "SOL", "DOGE", "AVAX"]:
                        if old_price is not None:
                            change = new_price - old_price
                            change_pct = (change / old_price) * 100 if old_price != 0 else 0
                            
                            if abs(change_pct) >= 0.01:  # Show changes >= 0.01%
                                direction = "📈" if change > 0 else "📉" if change < 0 else "➡️"
                                print(f"{direction} {asset}: ${new_price:,.2f} "
                                      f"({change:+.2f}, {change_pct:+.2f}%)")
                        else:
                            # First time seeing this asset
                            print(f"🆕 {asset}: ${new_price:,.2f}")
                            
                except (ValueError, TypeError):
                    continue
                    
        elif channel == "subscriptionUpdate":
            # Handle subscription confirmations
            subscription = data.get("subscription", {})
            print(f"✅ Subscription confirmed: {subscription}")
        else:
            # Other message types
            print(f"📨 Other message: {data}")


async def method_1_simple_websocket():
    """Method 1: Simple WebSocket connection"""
    
    print("🔧 Method 1: Simple WebSocket")
    print("-" * 30)
    
    monitor = PriceMonitor(testnet=True)
    await monitor.connect_and_monitor()


async def method_2_manual_websocket():
    """Method 2: Manual WebSocket handling"""
    
    print("\n🛠️ Method 2: Manual WebSocket")
    print("-" * 30)
    
    ws_url = "wss://api.hyperliquid-testnet.xyz/ws"
    
    try:
        async with websockets.connect(ws_url) as websocket:
            print("✅ Manual WebSocket connected")
            
            # Subscribe to allMids
            subscribe_msg = json.dumps({
                "method": "subscribe",
                "subscription": {"type": "allMids"}
            })
            
            await websocket.send(subscribe_msg)
            print("📊 Manual subscription sent")
            
            # Receive a few messages
            for i in range(5):
                try:
                    message = await asyncio.wait_for(websocket.recv(), timeout=10)
                    data = json.loads(message)
                    
                    print(f"📨 Message {i+1}:")
                    if data.get("channel") == "allMids":
                        price_data = data.get("data", {})
                        btc_price = price_data.get("BTC")
                        eth_price = price_data.get("ETH")
                        
                        print(f"   BTC: ${float(btc_price):,.2f} | ETH: ${float(eth_price):,.2f}")
                    else:
                        print(f"   {data}")
                        
                except asyncio.TimeoutError:
                    print("⏰ Timeout waiting for message")
                    break
                except Exception as e:
                    print(f"❌ Error: {e}")
                    break
                    
    except Exception as e:
        print(f"❌ Manual WebSocket failed: {e}")


async def demonstrate_websocket_concepts():
    """Explain WebSocket concepts"""
    
    print("\n📚 WebSocket Concepts")
    print("-" * 25)
    
    print("🔗 CONNECTION:")
    print("   • Persistent bidirectional connection")
    print("   • Lower latency than HTTP polling")
    print("   • Automatic reconnection handling needed")
    
    print("\n📡 SUBSCRIPTION:")
    print("   • Send subscribe message with subscription type")
    print("   • Server streams updates until unsubscribe")
    print("   • Multiple subscriptions per connection possible")
    
    print("\n📊 MESSAGE TYPES:")
    print("   • allMids: All asset prices")
    print("   • trades: Recent trade data")
    print("   • l2Book: Order book updates")
    print("   • user: User-specific updates (fills, orders)")
    
    print("\n⚠️ BEST PRACTICES:")
    print("   • Handle connection drops gracefully")
    print("   • Implement exponential backoff for reconnection")
    print("   • Buffer messages during processing")
    print("   • Validate all incoming data")


async def main():
    """Demonstrate WebSocket price monitoring"""
    
    print("📡 Hyperliquid WebSocket Price Monitor")
    print("=" * 45)
    print("Press Ctrl+C to stop monitoring")
    print("⚠️ This creates a live connection to Hyperliquid!")
    
    proceed = input("\nStart real-time monitoring? (y/N): ").lower().strip()
    if proceed != 'y':
        print("👋 WebSocket demo cancelled")
        await demonstrate_websocket_concepts()
        return
    
    # Choose monitoring method
    print("\nChoose monitoring method:")
    print("1. Simple monitor (recommended)")
    print("2. Manual WebSocket handling")
    
    choice = input("Enter choice (1/2): ").strip()
    
    try:
        if choice == "2":
            await method_2_manual_websocket()
        else:
            await method_1_simple_websocket()
            
    except KeyboardInterrupt:
        print("\n📡 Monitoring stopped by user")
    
    await demonstrate_websocket_concepts()
    
    print(f"\n📚 Key Points:")
    print("• WebSocket provides real-time price updates")
    print("• allMids subscription gives all asset prices")
    print("• Handle connection drops and reconnection")
    print("• Process messages efficiently to avoid lag")
    print("• Use for live trading and monitoring applications")


if __name__ == "__main__":
    asyncio.run(main())