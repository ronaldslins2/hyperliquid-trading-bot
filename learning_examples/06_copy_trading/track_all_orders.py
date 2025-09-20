"""
Monitor all order activity from a leader wallet using WebSocket.
Shows real-time order placements, cancellations, and fills.
"""

import asyncio
import json
import os
import signal
from dotenv import load_dotenv
import websockets

load_dotenv()

WS_URL = os.getenv("HYPERLIQUID_TESTNET_PUBLIC_WS_URL")
LEADER_ADDRESS = "0x..."  # Replace with leader's wallet address

running = False


def signal_handler(signum, frame):
    """Handle Ctrl+C gracefully"""
    global running
    print("\nShutting down...")
    running = False


def detect_market_type(coin_field):
    """Detect market type from coin field"""
    if coin_field.startswith("@"):
        # @{index} format = SPOT trading
        result = "SPOT"
        print(f"DEBUG: {coin_field} -> SPOT (@index format)")
        return result
    elif "/" in coin_field:
        # Pairs like PURR/USDC = SPOT trading
        result = "SPOT"
        print(f"DEBUG: {coin_field} -> SPOT (pair format)")
        return result
    else:
        # Direct symbols like SOL, BTC, ETH = PERP trading
        result = "PERP"
        print(f"DEBUG: {coin_field} -> PERP (direct symbol)")
        return result


def format_order(order_data):
    """Format order data for display"""
    order = order_data.get("order", {})
    status = order_data.get("status", "unknown")

    coin_field = order.get("coin", "N/A")
    market_type = detect_market_type(coin_field)

    return {
        "asset": coin_field,
        "market_type": market_type,
        "side": "BUY" if order.get("side") == "B" else "SELL",
        "size": order.get("sz", "N/A"),
        "price": order.get("limitPx", "N/A"),
        "order_id": order.get("oid", "N/A"),
        "status": status
    }


async def handle_order_events(data):
    """Process order-related WebSocket events"""
    channel = data.get("channel")

    if channel == "orderUpdates":
        orders = data.get("data", [])
        for order_update in orders:
            order_info = format_order(order_update)
            status_emoji = {"open": "🟢", "canceled": "❌", "filled": "✅"}.get(order_info['status'], "📋")

            print(f"{status_emoji} {order_info['status'].upper()}: {order_info['side']} {order_info['size']} {order_info['asset']} @ {order_info['price']} [{order_info['market_type']}] (ID: {order_info['order_id']})")

    elif channel == "userEvents":
        events = data.get("data", [])
        for event in events:
            if event.get("fills"):
                for fill in event["fills"]:
                    coin_field = fill.get("coin", "N/A")
                    market_type = detect_market_type(coin_field)
                    side = "BUY" if fill.get("side") == "B" else "SELL"

                    pnl_text = f" | PnL: {fill.get('closedPnl', '0')}" if float(fill.get('closedPnl', '0')) != 0 else ""
                    print(f"💰 FILL: {side} {fill.get('sz', 'N/A')} {coin_field} @ {fill.get('px', 'N/A')} [{market_type}] (Fee: {fill.get('fee', 'N/A')}){pnl_text}")

    elif channel == "subscriptionResponse":
        print("✅ Subscription confirmed")


async def ping_websocket(websocket):
    """Send ping every 30 seconds to keep connection alive"""
    try:
        while True:
            await asyncio.sleep(30)
            await websocket.ping()
    except asyncio.CancelledError:
        pass
    except Exception as e:
        print(f"⚠️ Ping failed: {e}")


async def monitor_leader_orders():
    """Connect to WebSocket and monitor leader's order activity"""
    global running

    if not LEADER_ADDRESS or LEADER_ADDRESS == "0x...":
        print("❌ Please set LEADER_ADDRESS in the script")
        return

    print(f"🔗 Connecting to {WS_URL}")
    signal.signal(signal.SIGINT, signal_handler)

    try:
        async with websockets.connect(WS_URL) as websocket:
            print("✅ WebSocket connected!")

            # Subscribe to order updates
            order_subscription = {
                "method": "subscribe",
                "subscription": {
                    "type": "orderUpdates",
                    "user": LEADER_ADDRESS
                }
            }

            # Subscribe to user events (fills)
            events_subscription = {
                "method": "subscribe",
                "subscription": {
                    "type": "userEvents",
                    "user": LEADER_ADDRESS
                }
            }

            await websocket.send(json.dumps(order_subscription))
            await websocket.send(json.dumps(events_subscription))

            print(f"📊 Monitoring orders for: {LEADER_ADDRESS}")
            print("=" * 80)

            running = True

            # Start ping task
            ping_task = asyncio.create_task(ping_websocket(websocket))

            try:
                async for message in websocket:
                    if not running:
                        break

                    try:
                        data = json.loads(message)

                        # Print raw WebSocket messages for debugging
                        if data.get("channel") in ["orderUpdates", "userEvents"]:
                            print(f"RAW MESSAGE: {json.dumps(data, indent=2)}")

                        await handle_order_events(data)
                    except json.JSONDecodeError:
                        print("⚠️ Received invalid JSON")
                    except Exception as e:
                        print(f"❌ Error: {e}")
            finally:
                ping_task.cancel()

    except websockets.exceptions.ConnectionClosed:
        print("🔌 WebSocket connection closed")
    except Exception as e:
        print(f"❌ WebSocket error: {e}")
    finally:
        print("👋 Disconnected")


async def main():
    print("Hyperliquid Order Monitor")
    print("=" * 40)

    if not WS_URL:
        print("❌ Missing HYPERLIQUID_TESTNET_PUBLIC_WS_URL in .env file")
        return

    await monitor_leader_orders()


if __name__ == "__main__":
    asyncio.run(main())