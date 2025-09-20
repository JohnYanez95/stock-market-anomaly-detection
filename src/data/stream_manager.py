#!/usr/bin/env python3
"""
Unified Stream Manager for Multi-Asset Real-Time Data

This module provides a centralized manager for orchestrating multiple
WebSocket streams across different asset classes (stocks, crypto, forex, etc).

Key Features:
- Manages multiple concurrent WebSocket connections (one per asset class)
- Unified anomaly detection and alerting
- Centralized data persistence and monitoring
- Graceful shutdown and error handling
- Easy to add/remove asset types

Usage:
    # Stream all available assets
    python src/data/stream_manager.py
    
    # Stream specific assets
    python src/data/stream_manager.py --assets stocks crypto
    
    # Stream with custom symbols
    python src/data/stream_manager.py --stocks AAPL,MSFT --crypto BTC,ETH
"""

import argparse
import asyncio
import logging
import signal
import sys
import threading
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Set

# Add parent directory to path for imports
sys.path.append(str(Path(__file__).parent.parent.parent))

from src.data.stream_stocks import PolygonWebSocketClient as StockClient
from src.data.stream_crypto import CryptoWebSocketClient
from configs.websocket_config import AssetType, get_websocket_config

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class AssetStream:
    """Base class for asset-specific streams"""
    
    def __init__(self, asset_type: AssetType, symbols: Optional[List[str]] = None):
        self.asset_type = asset_type
        self.symbols = symbols
        self.client = None
        self.thread = None
        self.is_running = False
    
    def start(self):
        """Start streaming in a separate thread"""
        raise NotImplementedError
    
    def stop(self):
        """Stop streaming gracefully"""
        self.is_running = False
        if self.client:
            self.client.disconnect()
    
    def is_active(self):
        """Check if stream is active"""
        return self.is_running and self.thread and self.thread.is_alive()


class StockStream(AssetStream):
    """Stock market streaming implementation"""
    
    def __init__(self, symbols: Optional[List[str]] = None):
        super().__init__(AssetType.STOCKS, symbols)
        if not symbols:
            self.symbols = ['AAPL', 'GOOGL', 'MSFT', 'TSLA', 'VOO']
    
    def start(self):
        """Start stock streaming"""
        if self.is_running:
            logger.warning("Stock stream already running")
            return
            
        def run_stock_stream():
            try:
                logger.info(f"📈 Starting stock stream for {self.symbols}")
                self.client = StockClient()
                
                # Add unified anomaly handler
                from src.data.stream_stocks import RealTimeDataProcessor
                processor = RealTimeDataProcessor()
                self.client.add_data_handler(processor.process_data)
                
                self.is_running = True
                
                # The connect() method blocks until disconnected
                self.client.connect()
                self.client.subscribe(self.symbols, ['A'])
                    
            except Exception as e:
                logger.error(f"Stock stream error: {e}")
            finally:
                self.is_running = False
        
        self.thread = threading.Thread(target=run_stock_stream, name="StockStream")
        self.thread.daemon = True
        self.thread.start()


class CryptoStream(AssetStream):
    """Cryptocurrency streaming implementation"""
    
    def __init__(self, symbols: Optional[List[str]] = None):
        super().__init__(AssetType.CRYPTO, symbols)
        if not symbols:
            self.symbols = ['X:BTCUSD', 'X:ETHUSD', 'X:ADAUSD', 'X:SOLUSD', 'X:DOTUSD']
    
    def start(self):
        """Start crypto streaming"""
        if self.is_running:
            logger.warning("Crypto stream already running")
            return
            
        def run_crypto_stream():
            try:
                logger.info(f"💰 Starting crypto stream for {self.symbols}")
                self.client = CryptoWebSocketClient(self.symbols)
                
                # Add unified anomaly handler
                from src.data.stream_crypto import CryptoDataProcessor
                processor = CryptoDataProcessor()
                self.client.add_data_handler(processor.process_data)
                
                self.is_running = True
                
                # The connect() method blocks until disconnected
                self.client.connect()
                
            except Exception as e:
                logger.error(f"Crypto stream error: {e}")
            finally:
                self.is_running = False
        
        self.thread = threading.Thread(target=run_crypto_stream, name="CryptoStream")
        self.thread.daemon = True
        self.thread.start()


class StreamManager:
    """Centralized manager for multi-asset streaming"""
    
    def __init__(self):
        self.config = get_websocket_config()
        self.streams: Dict[str, AssetStream] = {}
        self.is_running = False
        
        # Check available subscriptions
        self.available_assets = self._check_available_assets()
        
    def _check_available_assets(self) -> Set[str]:
        """Check which assets have WebSocket access"""
        available = set()
        
        for asset_type in AssetType:
            try:
                # Check if WebSocket is available for this asset
                self.config.get_websocket_url(asset_type)
                available.add(asset_type.value)
                logger.info(f"✅ {asset_type.value}: WebSocket available")
            except ValueError as e:
                logger.info(f"❌ {asset_type.value}: {e}")
                
        return available
    
    def add_stream(self, asset_type: str, symbols: Optional[List[str]] = None):
        """Add an asset stream"""
        if asset_type not in self.available_assets:
            logger.warning(f"Cannot add {asset_type} - no WebSocket access")
            return
        
        if asset_type == 'stocks':
            self.streams['stocks'] = StockStream(symbols)
        elif asset_type == 'crypto':
            self.streams['crypto'] = CryptoStream(symbols)
        # Add more asset types here as needed
        else:
            logger.warning(f"Unsupported asset type: {asset_type}")
    
    def start_all(self):
        """Start all configured streams"""
        logger.info("🚀 Starting Stream Manager")
        logger.info(f"📊 Available assets: {', '.join(self.available_assets)}")
        
        # Add all available streams
        for asset in self.available_assets:
            if asset in ['stocks', 'crypto']:  # Currently implemented
                self.add_stream(asset)
        
        self._start_streams()
    
    def start_selected(self, asset_types: List[str], 
                      stock_symbols: Optional[List[str]] = None,
                      crypto_symbols: Optional[List[str]] = None):
        """Start only selected asset streams"""
        logger.info(f"🚀 Starting selected streams: {asset_types}")
        
        for asset_type in asset_types:
            if asset_type == 'stocks':
                self.add_stream('stocks', stock_symbols)
            elif asset_type == 'crypto':
                self.add_stream('crypto', crypto_symbols)
        
        self._start_streams()
    
    def _start_streams(self):
        """Start all configured streams"""
        self.is_running = True
        
        # Start each stream
        for name, stream in self.streams.items():
            logger.info(f"Starting {name} stream...")
            stream.start()
        
        # Monitor streams
        try:
            while self.is_running:
                # Check stream health
                for name, stream in self.streams.items():
                    if not stream.is_active() and self.is_running:
                        logger.warning(f"{name} stream died, restarting...")
                        stream.start()
                
                import time
                time.sleep(5)  # Health check every 5 seconds
                
        except KeyboardInterrupt:
            logger.info("Received interrupt signal")
        finally:
            self.stop_all()
    
    def stop_all(self):
        """Stop all streams gracefully"""
        logger.info("Stopping all streams...")
        self.is_running = False
        
        for name, stream in self.streams.items():
            logger.info(f"Stopping {name} stream...")
            stream.stop()
        
        # Wait for threads to finish
        for name, stream in self.streams.items():
            if stream.thread:
                stream.thread.join(timeout=5)
        
        logger.info("All streams stopped")
    
    def get_status(self) -> Dict:
        """Get status of all streams"""
        status = {
            'manager_running': self.is_running,
            'available_assets': list(self.available_assets),
            'active_streams': {}
        }
        
        for name, stream in self.streams.items():
            status['active_streams'][name] = {
                'active': stream.is_active(),
                'symbols': stream.symbols
            }
        
        return status


def main():
    """Main entry point for the stream manager"""
    parser = argparse.ArgumentParser(description='Multi-asset streaming manager')
    parser.add_argument(
        '--assets', 
        nargs='+', 
        choices=['stocks', 'crypto', 'forex', 'options'],
        help='Asset types to stream (default: all available)'
    )
    parser.add_argument(
        '--stocks',
        type=lambda s: s.split(','),
        help='Comma-separated list of stock symbols (e.g., AAPL,MSFT,GOOGL)'
    )
    parser.add_argument(
        '--crypto',
        type=lambda s: s.split(','),
        help='Comma-separated list of crypto pairs (e.g., X:BTCUSD,X:ETHUSD)'
    )
    
    args = parser.parse_args()
    
    # Initialize manager
    manager = StreamManager()
    
    # Setup signal handlers
    def signal_handler(sig, frame):
        logger.info("Shutting down Stream Manager...")
        manager.stop_all()
        sys.exit(0)
    
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)
    
    # Start streaming
    try:
        if args.assets:
            manager.start_selected(
                args.assets,
                stock_symbols=args.stocks,
                crypto_symbols=args.crypto
            )
        else:
            manager.start_all()
    except Exception as e:
        logger.error(f"Stream manager error: {e}")
        manager.stop_all()


if __name__ == "__main__":
    main()