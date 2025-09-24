#!/usr/bin/env python3
"""
Test crypto trades WebSocket access with current subscription
This script tests if we can access individual crypto trades (XT channel) for buy/sell analysis
"""

import os
import sys
import json
import time
import websocket
from pathlib import Path
from dotenv import load_dotenv

# Add parent directory to path
sys.path.append(str(Path(__file__).parent.parent))
from configs.websocket_config import get_websocket_config, AssetType

load_dotenv()

class CryptoTradesTest:
    def __init__(self):
        self.api_key = os.getenv("POLYGON_API_KEY")
        self.ws_config = get_websocket_config()
        self.asset_type = AssetType.CRYPTO
        self.messages_received = 0
        self.max_test_duration = 30  # 30 seconds
        self.start_time = None
        
    def on_open(self, ws):
        """WebSocket opened"""
        ws_url = self.ws_config.get_websocket_url(self.asset_type)
        print(f"🔗 Connected to {ws_url}")
        
        # Authenticate
        auth_msg = {"action": "auth", "params": self.api_key}
        ws.send(json.dumps(auth_msg))
        print(f"🔐 Authentication sent")
        
        self.start_time = time.time()
        
        # Test different crypto data types
        test_channels = [
            "XA.BTC-USD",   # Aggregates (should work with Starter)
            "XT.BTC-USD",   # Trades (may need Developer+)
            "XQ.BTC-USD"    # Quotes (may need Developer+)
        ]
        
        for channel in test_channels:
            subscribe_msg = {"action": "subscribe", "params": channel}
            ws.send(json.dumps(subscribe_msg))
            print(f"📊 Subscribed to: {channel}")
        
    def on_message(self, ws, message):
        """Handle WebSocket messages"""
        try:
            data = json.loads(message)
            self.messages_received += 1
            
            # Check message type
            for msg in data:
                msg_type = msg.get('ev', 'unknown')
                
                if msg_type == 'status':
                    status = msg.get('status', '')
                    message_text = msg.get('message', '')
                    print(f"📢 Status: {status} - {message_text}")
                    
                elif msg_type == 'XA':  # Crypto aggregates
                    symbol = msg.get('pair', 'Unknown')
                    price = msg.get('c', 0)
                    volume = msg.get('v', 0)
                    print(f"📈 Aggregate {symbol}: ${price:.4f}, Vol: {volume:,.0f}")
                    
                elif msg_type == 'XT':  # Crypto trades - THIS IS WHAT WE WANT!
                    symbol = msg.get('pair', 'Unknown')
                    price = msg.get('p', 0)
                    size = msg.get('s', 0)
                    timestamp = msg.get('t', 0)
                    conditions = msg.get('c', [])
                    
                    print(f"💰 TRADE {symbol}: ${price:.4f} x {size:.4f} | Conditions: {conditions}")
                    print(f"    📅 Timestamp: {timestamp}")
                    
                    # Check for buy/sell indicators in conditions
                    if conditions:
                        print(f"    🔍 Trade conditions suggest market dynamics")
                    
                elif msg_type == 'XQ':  # Crypto quotes
                    symbol = msg.get('pair', 'Unknown')
                    bid = msg.get('bp', 0)
                    ask = msg.get('ap', 0)
                    print(f"📊 Quote {symbol}: Bid ${bid:.4f} | Ask ${ask:.4f} | Spread: ${ask-bid:.4f}")
                    
                else:
                    print(f"❓ Unknown message type: {msg_type}")
                    
        except json.JSONDecodeError:
            print(f"⚠️  Non-JSON message: {message}")
            
        # Check if test duration exceeded
        if self.start_time and time.time() - self.start_time > self.max_test_duration:
            print(f"\n⏰ Test duration reached ({self.max_test_duration}s)")
            ws.close()
    
    def on_error(self, ws, error):
        """Handle WebSocket errors"""
        print(f"❌ WebSocket Error: {error}")
    
    def on_close(self, ws, close_status_code, close_msg):
        """WebSocket closed"""
        print(f"\n🔌 WebSocket closed")
        print(f"📊 Test Results:")
        print(f"   Messages received: {self.messages_received}")
        print(f"   Duration: {time.time() - self.start_time:.1f}s" if self.start_time else "Duration: Unknown")
        
        # Analyze results
        if self.messages_received > 0:
            print(f"✅ WebSocket connection working!")
        else:
            print(f"❌ No messages received - check subscription tier")
    
    def run_test(self):
        """Run the crypto trades test"""
        if not self.api_key:
            print("❌ POLYGON_API_KEY not found in environment")
            return
            
        if not self.ws_config.has_websocket_access(self.asset_type):
            tier = self.ws_config.get_subscription_tier(self.asset_type)
            print(f"❌ WebSocket not enabled for crypto tier: {tier}")
            return
            
        ws_url = self.ws_config.get_websocket_url(self.asset_type)
        tier = self.ws_config.get_subscription_tier(self.asset_type)
            
        print(f"🚀 Testing Crypto Trades Access")
        print(f"   Subscription tier: {tier}")
        print(f"   WebSocket URL: {ws_url}")
        print(f"   Test duration: {self.max_test_duration} seconds")
        print(f"   Testing channels: XA (aggregates), XT (trades), XQ (quotes)")
        print("")
        
        # Create WebSocket app
        ws = websocket.WebSocketApp(
            ws_url,
            on_open=self.on_open,
            on_message=self.on_message,
            on_error=self.on_error,
            on_close=self.on_close
        )
        
        # Run WebSocket
        ws.run_forever()

def main():
    """Main function"""
    test = CryptoTradesTest()
    test.run_test()

if __name__ == "__main__":
    main()