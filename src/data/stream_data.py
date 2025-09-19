"""
Real-time data streaming from Polygon.io WebSocket API.
"""

import os
import json
import asyncio
import logging
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Callable, Optional
import websocket
import threading
import pandas as pd
from dotenv import load_dotenv

# Import configuration system
import sys
sys.path.append(str(Path(__file__).parent.parent.parent))
from configs.websocket_config import get_websocket_config, AssetType, get_ws_url, get_subscription_channels

# Load environment variables
load_dotenv()

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class PolygonWebSocketClient:
    """WebSocket client for real-time market data from Polygon.io"""
    
    def __init__(self, asset_type: AssetType = AssetType.STOCKS, api_key: str = None):
        # Initialize configuration
        self.config = get_websocket_config()
        self.asset_type = asset_type
        
        # API key setup
        self.api_key = api_key or self.config.api_key
        if not self.api_key:
            raise ValueError("POLYGON_API_KEY not found in environment variables")
        
        # Get WebSocket URL from configuration
        self.ws_url = get_ws_url(asset_type)
        self.ws = None
        self.subscribed_symbols = set()
        
        # Data handlers
        self.data_handlers = []
        self.data_buffer = []
        
        # Connection state
        self.is_connected = False
        self.is_authenticated = False
        
        # Create output directory
        self.output_dir = Path("data/raw/streaming")
        self.output_dir.mkdir(parents=True, exist_ok=True)
        
        # Log configuration
        delay_info = f"({self.config.get_delay_minutes()}-minute delayed)" if not self.config.is_realtime_available() else "(real-time)"
        logger.info(f"Initialized WebSocket client for {asset_type.value} {delay_info}")
        logger.info(f"Using endpoint: {self.ws_url}")
    
    def add_data_handler(self, handler: Callable[[Dict], None]):
        """Add a callback function to handle incoming data"""
        self.data_handlers.append(handler)
    
    def on_message(self, ws, message):
        """Handle incoming WebSocket messages"""
        try:
            data = json.loads(message)
            
            # Handle different message types
            if isinstance(data, list):
                for item in data:
                    self._process_message(item)
            else:
                self._process_message(data)
                
        except json.JSONDecodeError as e:
            logger.error(f"Failed to decode message: {e}")
        except Exception as e:
            logger.error(f"Error processing message: {e}")
    
    def _process_message(self, message: Dict):
        """Process individual message"""
        msg_type = message.get('ev', 'unknown')
        
        if msg_type == 'status':
            self._handle_status_message(message)
        elif msg_type == 'A':  # Aggregate (minute bar)
            self._handle_aggregate_message(message)
        elif msg_type == 'T':  # Trade
            self._handle_trade_message(message)
        elif msg_type == 'Q':  # Quote
            self._handle_quote_message(message)
        else:
            logger.debug(f"Unhandled message type: {msg_type}")
    
    def _handle_status_message(self, message: Dict):
        """Handle connection status messages"""
        status = message.get('status', '')
        msg = message.get('message', '')
        logger.info(f"Status: {status}" + (f" - {msg}" if msg else ""))
        
        if status == 'connected':
            self.is_connected = True
            self._authenticate()
        elif status == 'auth_success':
            self.is_authenticated = True
            logger.info("✅ Authentication successful")
        elif status == 'auth_failed':
            logger.error(f"❌ Authentication failed: {msg}")
            self.disconnect()
    
    def _handle_aggregate_message(self, message: Dict):
        """Handle aggregate (minute bar) data"""
        # Transform to match historical data format
        processed_data = {
            'timestamp': datetime.fromtimestamp(message.get('t', 0) / 1000) if message.get('t', 0) > 0 else datetime.now(),
            'symbol': message.get('sym', ''),
            'open': message.get('o', 0),
            'high': message.get('h', 0),
            'low': message.get('l', 0),
            'close': message.get('c', 0),
            'volume': message.get('v', 0),
            'vwap': message.get('vw', 0),
            'transactions': message.get('n', 0),
            'message_type': 'aggregate'
        }
        
        self._dispatch_data(processed_data)
    
    def _handle_trade_message(self, message: Dict):
        """Handle individual trade data"""
        processed_data = {
            'timestamp': datetime.fromtimestamp(message.get('t', 0) / 1000000),
            'symbol': message.get('sym', ''),
            'price': message.get('p', 0),
            'size': message.get('s', 0),
            'exchange': message.get('x', ''),
            'conditions': message.get('c', []),
            'message_type': 'trade'
        }
        
        self._dispatch_data(processed_data)
    
    def _handle_quote_message(self, message: Dict):
        """Handle quote (bid/ask) data"""
        processed_data = {
            'timestamp': datetime.fromtimestamp(message.get('t', 0) / 1000000),
            'symbol': message.get('sym', ''),
            'bid_price': message.get('bp', 0),
            'bid_size': message.get('bs', 0),
            'ask_price': message.get('ap', 0),
            'ask_size': message.get('as', 0),
            'message_type': 'quote'
        }
        
        self._dispatch_data(processed_data)
    
    def _dispatch_data(self, data: Dict):
        """Send data to all registered handlers"""
        # Add to buffer
        self.data_buffer.append(data)
        
        # Call all handlers
        for handler in self.data_handlers:
            try:
                handler(data)
            except Exception as e:
                logger.error(f"Error in data handler: {e}")
    
    def on_error(self, ws, error):
        """Handle WebSocket errors"""
        logger.error(f"WebSocket error: {error}")
    
    def on_close(self, ws, close_status_code, close_msg):
        """Handle WebSocket close"""
        logger.info(f"WebSocket closed: {close_status_code} - {close_msg}")
        self.is_connected = False
        self.is_authenticated = False
    
    def on_open(self, ws):
        """Handle WebSocket open"""
        logger.info("WebSocket connection opened")
    
    def _authenticate(self):
        """Send authentication message"""
        auth_message = {
            "action": "auth",
            "params": self.api_key
        }
        logger.info("Sending authentication...")
        self.ws.send(json.dumps(auth_message))
    
    def subscribe(self, symbols: List[str], data_types: List[str] = None):
        """
        Subscribe to real-time data for symbols
        
        Args:
            symbols: List of symbols (e.g., ['AAPL', 'GOOGL'] for stocks, ['X:BTCUSD'] for crypto)
            data_types: List of data types (None uses defaults for asset type)
        """
        # Use configuration system to build subscription channels
        subscriptions = get_subscription_channels(self.asset_type, symbols, data_types)
        
        subscribe_message = {
            "action": "subscribe",
            "params": ",".join(subscriptions)
        }
        
        available_types = self.config.get_available_data_types(self.asset_type)
        used_types = data_types or list(available_types.keys())[:1]  # Default to first available type
        type_descriptions = [available_types.get(dt, dt) for dt in used_types]
        
        logger.info(f"Subscribing to {self.asset_type.value} data:")
        logger.info(f"  Symbols: {symbols}")
        logger.info(f"  Data types: {type_descriptions}")
        logger.info(f"  Channels: {subscriptions}")
        
        self.ws.send(json.dumps(subscribe_message))
        self.subscribed_symbols.update(symbols)
    
    def unsubscribe(self, symbols: List[str], data_types: List[str] = None):
        """Unsubscribe from symbols"""
        if data_types is None:
            data_types = ['A']
        
        subscriptions = []
        for data_type in data_types:
            for symbol in symbols:
                subscriptions.append(f"{data_type}.{symbol}")
        
        unsubscribe_message = {
            "action": "unsubscribe",
            "params": ",".join(subscriptions)
        }
        
        logger.info(f"Unsubscribing from: {subscriptions}")
        self.ws.send(json.dumps(unsubscribe_message))
        self.subscribed_symbols.difference_update(symbols)
    
    def connect(self):
        """Establish WebSocket connection"""
        logger.info("Connecting to Polygon.io WebSocket...")
        
        websocket.enableTrace(False)
        self.ws = websocket.WebSocketApp(
            self.ws_url,
            on_open=self.on_open,
            on_message=self.on_message,
            on_error=self.on_error,
            on_close=self.on_close
        )
        
        # Run in a separate thread
        self.ws_thread = threading.Thread(target=self.ws.run_forever)
        self.ws_thread.daemon = True
        self.ws_thread.start()
        
        # Wait for connection and authentication
        max_wait = 10  # seconds
        wait_count = 0
        while not self.is_authenticated and wait_count < max_wait:
            import time
            time.sleep(1)
            wait_count += 1
        
        if not self.is_authenticated:
            raise ConnectionError("Failed to authenticate with Polygon.io WebSocket")
        
        logger.info("Successfully connected and authenticated")
    
    def disconnect(self):
        """Close WebSocket connection"""
        if self.ws:
            self.ws.close()
        self.is_connected = False
        self.is_authenticated = False
        logger.info("WebSocket disconnected")
    
    def get_buffered_data(self, clear_buffer: bool = True) -> List[Dict]:
        """Get data from buffer and optionally clear it"""
        data = self.data_buffer.copy()
        if clear_buffer:
            self.data_buffer.clear()
        return data
    
    def save_buffer_to_csv(self, filename: str = None):
        """Save buffered data to CSV file"""
        if not self.data_buffer:
            logger.warning("No data in buffer to save")
            return
        
        if filename is None:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"streaming_data_{timestamp}.csv"
        
        filepath = self.output_dir / filename
        df = pd.DataFrame(self.data_buffer)
        df.to_csv(filepath, index=False)
        logger.info(f"Saved {len(self.data_buffer)} records to {filepath}")


class RealTimeDataProcessor:
    """Process streaming data in real-time"""
    
    def __init__(self):
        self.data_store = {}
        self.anomaly_callbacks = []
    
    def add_anomaly_callback(self, callback: Callable[[Dict], None]):
        """Add callback for anomaly detection"""
        self.anomaly_callbacks.append(callback)
    
    def process_data(self, data: Dict):
        """Process incoming streaming data"""
        symbol = data.get('symbol', '')
        message_type = data.get('message_type', '')
        
        if message_type == 'aggregate':
            self._process_aggregate(data)
        elif message_type == 'trade':
            self._process_trade(data)
    
    def _process_aggregate(self, data: Dict):
        """Process minute aggregate data"""
        symbol = data['symbol']
        
        # Initialize symbol data if not exists
        if symbol not in self.data_store:
            self.data_store[symbol] = {
                'recent_prices': [],
                'recent_volumes': [],
                'last_price': 0,
                'last_volume': 0
            }
        
        store = self.data_store[symbol]
        
        # Update data store
        current_price = data['close']
        current_volume = data['volume']
        
        store['recent_prices'].append(current_price)
        store['recent_volumes'].append(current_volume)
        
        # Keep only last 20 data points
        store['recent_prices'] = store['recent_prices'][-20:]
        store['recent_volumes'] = store['recent_volumes'][-20:]
        
        # Simple anomaly detection
        self._check_for_anomalies(symbol, data)
        
        store['last_price'] = current_price
        store['last_volume'] = current_volume
    
    def _check_for_anomalies(self, symbol: str, data: Dict):
        """Basic anomaly detection on streaming data"""
        store = self.data_store[symbol]
        
        if len(store['recent_volumes']) < 5:
            return  # Need minimum data
        
        current_volume = data['volume']
        avg_volume = sum(store['recent_volumes'][:-1]) / len(store['recent_volumes'][:-1])
        
        # Volume spike detection (3x average)
        if current_volume > avg_volume * 3:
            anomaly = {
                'type': 'volume_spike',
                'symbol': symbol,
                'timestamp': data['timestamp'],
                'current_volume': current_volume,
                'average_volume': avg_volume,
                'multiplier': current_volume / avg_volume,
                'data': data
            }
            
            logger.warning(f"Volume anomaly detected: {symbol} - {anomaly['multiplier']:.2f}x average")
            
            # Notify callbacks
            for callback in self.anomaly_callbacks:
                try:
                    callback(anomaly)
                except Exception as e:
                    logger.error(f"Error in anomaly callback: {e}")


def main():
    """Example usage of the WebSocket client"""
    
    # Initialize client
    client = PolygonWebSocketClient()
    processor = RealTimeDataProcessor()
    
    # Add data handler
    client.add_data_handler(processor.process_data)
    
    # Add simple logging handler
    def log_data(data):
        if data['message_type'] == 'aggregate':
            logger.info(f"{data['symbol']}: ${data['close']:.2f}, Vol: {data['volume']:,}")
    
    client.add_data_handler(log_data)
    
    # Add anomaly handler
    def log_anomaly(anomaly):
        logger.warning(f"ANOMALY: {anomaly['type']} in {anomaly['symbol']} - {anomaly['multiplier']:.2f}x")
    
    processor.add_anomaly_callback(log_anomaly)
    
    try:
        # Connect and subscribe
        client.connect()
        client.subscribe(['AAPL', 'GOOGL', 'MSFT', 'TSLA', 'VOO'], ['A'])  # Minute aggregates
        
        logger.info("Streaming started. Press Ctrl+C to stop.")
        
        # Keep running
        while True:
            import time
            time.sleep(60)  # Save data every minute
            client.save_buffer_to_csv()
            
    except KeyboardInterrupt:
        logger.info("Stopping stream...")
    finally:
        client.disconnect()


if __name__ == "__main__":
    main()