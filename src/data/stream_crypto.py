#!/usr/bin/env python3
"""
Cryptocurrency Real-Time Streaming with Anomaly Detection

This module provides real-time cryptocurrency data streaming from Polygon.io
with built-in anomaly detection for crypto markets that operate 24/7.

Key Features:
- Real-time crypto data streaming (requires Starter tier)
- Volume anomaly detection optimized for crypto volatility
- 24/7 market operation (no market hours restrictions)
- Major cryptocurrency pairs monitoring
- Real-time alerts for significant market movements

Usage:
    python src/data/stream_crypto.py

Environment Requirements:
    POLYGON_TIER_CRYPTO=starter  # Required for WebSocket access
"""

import asyncio
import json
import logging
import os
import signal
import sys
from collections import defaultdict, deque
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Callable

import websocket
from websocket import WebSocketApp
from dotenv import load_dotenv

# Add parent directory to path for imports
sys.path.append(str(Path(__file__).parent.parent.parent))

from configs.websocket_config import get_websocket_config, WebSocketConfig, AssetType
from src.data.database import init_database, store_market_data, store_anomaly

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class CryptoWebSocketClient:
    """WebSocket client for cryptocurrency data streaming"""
    
    def __init__(self, symbols: Optional[List[str]] = None):
        """Initialize crypto WebSocket client
        
        Args:
            symbols: List of crypto symbols to stream. Defaults to major pairs.
        """
        self.asset_type = AssetType.CRYPTO
        self.config = get_websocket_config()
        
        # Default to major cryptocurrency pairs (including DOGE!)
        # Use the correct format that matches live data: hyphenated pairs
        if symbols is None:
            symbols = ['BTC-USD', 'ETH-USD', 'ADA-USD', 'SOL-USD', 'DOT-USD', 'DOGE-USD']
        self.symbols = symbols
        
        # WebSocket configuration
        self.ws_url = self.config.get_websocket_url(self.asset_type)
        self.api_key = self.config.api_key
        self.ws = None
        
        # Data handlers and callbacks
        self.data_handlers: List[Callable[[Dict], None]] = []
        self.anomaly_callbacks: List[Callable[[Dict], None]] = []
        
        # Connection state
        self.is_connected = False
        self.is_authenticated = False
        
        # Create output directory
        self.output_dir = Path("data/raw/streaming/crypto")
        self.output_dir.mkdir(parents=True, exist_ok=True)
        
        # Initialize database
        init_database()
        
        # Log configuration
        delay_info = f"({self.config.get_delay_minutes(self.asset_type)}-minute delayed)" if not self.config.is_realtime_available(self.asset_type) else "(real-time)"
        logger.info(f"Initialized crypto WebSocket client {delay_info}")
        logger.info(f"Using endpoint: {self.ws_url}")
    
    def add_data_handler(self, handler: Callable[[Dict], None]):
        """Add a callback function to handle incoming data"""
        self.data_handlers.append(handler)
    
    def add_anomaly_callback(self, callback: Callable[[Dict], None]):
        """Add a callback function to handle anomaly alerts"""
        self.anomaly_callbacks.append(callback)
    
    def on_open(self, ws):
        """Called when WebSocket connection is opened"""
        logger.info("WebSocket connection opened")
        self.is_connected = True
        
        # Send authentication
        auth_message = {
            "action": "auth",
            "params": self.api_key
        }
        logger.info("Sending authentication...")
        ws.send(json.dumps(auth_message))
    
    def on_close(self, ws, close_status_code, close_msg):
        """Called when WebSocket connection is closed"""
        logger.info(f"WebSocket connection closed: {close_status_code} - {close_msg}")
        self.is_connected = False
        self.is_authenticated = False
    
    def on_error(self, ws, error):
        """Called when WebSocket encounters an error"""
        logger.error(f"WebSocket error: {error}")
    
    def on_message(self, ws, message):
        """Called when a message is received from WebSocket"""
        try:
            data = json.loads(message)
            
            # Handle different message types
            for item in data:
                if item.get('ev') == 'status':
                    self.handle_status_message(item)
                elif item.get('ev') == 'XA':  # Crypto aggregate
                    self.handle_crypto_data(item)
                else:
                    logger.debug(f"Unhandled message type: {item}")
                    
        except json.JSONDecodeError as e:
            logger.error(f"Failed to decode JSON message: {e}")
        except Exception as e:
            logger.error(f"Error processing message: {e}")
    
    def handle_status_message(self, status_data: Dict):
        """Handle status messages from Polygon.io"""
        status = status_data.get('status', 'unknown')
        message = status_data.get('message', '')
        
        logger.info(f"Status: {status} - {message}")
        
        if status == 'auth_success':
            self.is_authenticated = True
            logger.info("✅ Authentication successful")
            self.subscribe_to_data()
        elif status == 'connected':
            logger.info("Connected to Polygon.io WebSocket")
        elif status.startswith('success') and 'subscribed' in message:
            logger.info(f"Status: {status} - {message}")
    
    def handle_crypto_data(self, crypto_data: Dict):
        """Handle incoming cryptocurrency data"""
        try:
            # Extract key information
            symbol = crypto_data.get('pair', 'UNKNOWN')
            timestamp = crypto_data.get('s', 0) / 1000  # Convert to seconds
            open_price = crypto_data.get('o', 0)
            high_price = crypto_data.get('h', 0)
            low_price = crypto_data.get('l', 0)
            close_price = crypto_data.get('c', 0)
            volume = crypto_data.get('v', 0)
            vwap = crypto_data.get('vw', 0)
            
            # Create readable timestamp
            dt = datetime.fromtimestamp(timestamp)
            time_str = dt.strftime("%H:%M:%S")
            
            # Store in database
            store_market_data('crypto', symbol, crypto_data)
            
            # Log data
            logger.info(f"💰 {symbol}: ${close_price:.4f}, Vol: {volume:,.0f} at {time_str}")
            
            # Call all data handlers
            for handler in self.data_handlers:
                try:
                    handler(crypto_data)
                except Exception as e:
                    logger.error(f"Error in data handler: {e}")
                    
        except Exception as e:
            logger.error(f"Error handling crypto data: {e}")
    
    def subscribe_to_data(self):
        """Subscribe to cryptocurrency data streams"""
        if not self.is_authenticated:
            logger.warning("Cannot subscribe - not authenticated")
            return
        
        try:
            # Get subscription channels
            channels = self.config.get_subscription_channels(
                asset_type=self.asset_type,
                symbols=self.symbols
            )
            
            logger.info("Subscribing to crypto data:")
            logger.info(f"  Symbols: {self.symbols}")
            logger.info(f"  Data types: ['aggregates']")
            logger.info(f"  Channels: {channels}")
            
            # Send subscription message
            subscription_message = {
                "action": "subscribe",
                "params": ",".join(channels)
            }
            
            self.ws.send(json.dumps(subscription_message))
            
        except Exception as e:
            logger.error(f"Error subscribing to data: {e}")
    
    def connect(self):
        """Establish WebSocket connection"""
        logger.info("Connecting to Polygon.io WebSocket...")
        
        self.ws = WebSocketApp(
            self.ws_url,
            on_open=self.on_open,
            on_message=self.on_message,
            on_error=self.on_error,
            on_close=self.on_close
        )
        
        # Start WebSocket in a separate thread
        self.ws.run_forever()
    
    def disconnect(self):
        """Close WebSocket connection"""
        if self.ws:
            self.ws.close()
            logger.info("WebSocket disconnected")


class CryptoDataProcessor:
    """Process real-time crypto data and detect anomalies"""
    
    def __init__(self):
        """Initialize crypto data processor with crypto-specific parameters"""
        # Store recent data for anomaly detection (crypto is more volatile)
        self.recent_data = defaultdict(lambda: deque(maxlen=10))  # Shorter window for crypto
        self.volume_threshold = 2.0  # Lower threshold due to crypto volatility
        
        # Anomaly callbacks
        self.anomaly_callbacks: List[Callable[[Dict], None]] = []
        
        logger.info(f"Initialized crypto data processor (volume threshold: {self.volume_threshold}x)")
    
    def add_anomaly_callback(self, callback: Callable[[Dict], None]):
        """Add callback for anomaly notifications"""
        self.anomaly_callbacks.append(callback)
    
    def process_data(self, data: Dict):
        """Process incoming crypto data and detect anomalies"""
        try:
            # Extract symbol and volume
            symbol = data.get('pair', 'UNKNOWN')
            volume = data.get('v', 0)
            close_price = data.get('c', 0)
            timestamp = data.get('s', 0) / 1000
            
            if volume <= 0 or close_price <= 0:
                return
            
            # Store data for analysis
            self.recent_data[symbol].append({
                'volume': volume,
                'price': close_price,
                'timestamp': timestamp
            })
            
            # Check for volume anomalies
            self.check_volume_anomaly(symbol, volume)
            
        except Exception as e:
            logger.error(f"Error processing crypto data: {e}")
    
    def check_volume_anomaly(self, symbol: str, current_volume: float):
        """Check for volume anomalies in crypto data"""
        try:
            recent_volumes = [d['volume'] for d in self.recent_data[symbol]]
            
            if len(recent_volumes) < 5:  # Need some history
                return
            
            # Calculate average of recent volumes (excluding current)
            avg_volume = sum(recent_volumes[:-1]) / len(recent_volumes[:-1])
            
            if avg_volume > 0:
                multiplier = current_volume / avg_volume
                
                # Check if volume is significantly higher (crypto threshold)
                if multiplier >= self.volume_threshold:
                    anomaly = {
                        'type': 'volume_spike',
                        'symbol': symbol,
                        'current_volume': current_volume,
                        'average_volume': avg_volume,
                        'multiplier': multiplier,
                        'timestamp': datetime.now().isoformat(),
                        'market': 'crypto'
                    }
                    
                    # Store anomaly in database
                    store_anomaly('crypto', anomaly)
                    
                    logger.warning(f"🚨 CRYPTO ANOMALY: volume_spike in {symbol} - {multiplier:.2f}x normal")
                    
                    # Notify callbacks
                    for callback in self.anomaly_callbacks:
                        try:
                            callback(anomaly)
                        except Exception as e:
                            logger.error(f"Error in crypto anomaly callback: {e}")
                            
        except Exception as e:
            logger.error(f"Error checking crypto volume anomaly: {e}")


def main():
    """Main function for cryptocurrency streaming"""
    
    # Initialize crypto client with default symbols (including DOGE!)
    crypto_symbols = ['BTC-USD', 'ETH-USD', 'ADA-USD', 'SOL-USD', 'DOT-USD', 'DOGE-USD']
    client = CryptoWebSocketClient(symbols=crypto_symbols)
    processor = CryptoDataProcessor()
    
    # Add data handler
    client.add_data_handler(processor.process_data)
    
    # Add anomaly callback
    def log_crypto_anomaly(anomaly: Dict):
        symbol = anomaly['symbol']
        anomaly_type = anomaly['type']
        multiplier = anomaly['multiplier']
        logger.warning(f"🚨 CRYPTO ALERT: {anomaly_type} detected in {symbol} ({multiplier:.2f}x normal)")
    
    processor.add_anomaly_callback(log_crypto_anomaly)
    
    # Setup graceful shutdown
    def signal_handler(sig, frame):
        logger.info("Shutting down crypto streaming...")
        client.disconnect()
        sys.exit(0)
    
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)
    
    try:
        logger.info("🚀 Starting cryptocurrency streaming...")
        logger.info("💡 Crypto markets operate 24/7 - data should flow continuously")
        logger.info("Streaming started. Press Ctrl+C to stop.")
        
        # Connect and start streaming
        client.connect()
        
    except KeyboardInterrupt:
        logger.info("Crypto streaming stopped by user")
    except Exception as e:
        logger.error(f"Error in crypto streaming: {e}")
    finally:
        client.disconnect()


if __name__ == "__main__":
    main()