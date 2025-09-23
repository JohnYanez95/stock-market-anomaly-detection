#!/usr/bin/env python3
"""
SQLite Database Management for Real-Time Market Data

This module handles database initialization, schema management, and
data persistence for the multi-asset streaming pipeline.

Key Features:
- Time-series optimized schema for market data
- Anomaly event tracking with start/end times
- Performance indexes for fast queries
- Data retention management
- Thread-safe operations for concurrent streams

Usage:
    from src.data.database import init_database, store_market_data
    
    # Initialize database
    init_database()
    
    # Store market data
    store_market_data('stocks', 'AAPL', market_data_dict)
"""

import sqlite3
import json
import logging
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Optional, Any
from contextlib import contextmanager
import threading

# Configure logging
logger = logging.getLogger(__name__)

# Database configuration
DB_PATH = Path("data/streaming_data.db")
DB_TIMEOUT = 30.0  # seconds

# Thread-local storage for connections
_local = threading.local()

def get_db_connection() -> sqlite3.Connection:
    """Get thread-local database connection"""
    if not hasattr(_local, 'connection'):
        DB_PATH.parent.mkdir(parents=True, exist_ok=True)
        _local.connection = sqlite3.connect(
            str(DB_PATH), 
            timeout=DB_TIMEOUT,
            check_same_thread=False
        )
        _local.connection.row_factory = sqlite3.Row
    return _local.connection

@contextmanager
def get_db_cursor():
    """Context manager for database operations"""
    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        yield cursor
        conn.commit()
    except Exception as e:
        conn.rollback()
        logger.error(f"Database error: {e}")
        raise
    finally:
        cursor.close()

def init_database():
    """Initialize SQLite database with schema and indexes"""
    logger.info("Initializing SQLite database...")
    
    with get_db_cursor() as cursor:
        # Market data table (main time-series data)
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS market_data (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp DATETIME NOT NULL,
                symbol TEXT NOT NULL,
                asset_type TEXT NOT NULL,
                price REAL NOT NULL,
                volume REAL NOT NULL,
                high REAL,
                low REAL,
                open REAL,
                vwap REAL,
                raw_data TEXT,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        # Anomalies table (detected events)
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS anomalies (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                start_time DATETIME NOT NULL,
                end_time DATETIME,
                symbol TEXT NOT NULL,
                asset_type TEXT NOT NULL,
                anomaly_type TEXT NOT NULL,
                multiplier REAL,
                current_value REAL,
                average_value REAL,
                status TEXT DEFAULT 'detected',
                details TEXT,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        # Performance indexes
        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_market_data_symbol_time 
            ON market_data(symbol, timestamp)
        """)
        
        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_market_data_asset_time 
            ON market_data(asset_type, timestamp)
        """)
        
        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_anomalies_time 
            ON anomalies(start_time)
        """)
        
        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_anomalies_symbol 
            ON anomalies(symbol, start_time)
        """)
    
    logger.info(f"Database initialized at: {DB_PATH}")

def store_market_data(asset_type: str, symbol: str, data: Dict) -> bool:
    """
    Store market data in the database
    
    Args:
        asset_type: 'stocks' or 'crypto'
        symbol: Trading symbol (e.g., 'AAPL', 'X:BTCUSD')
        data: Market data dictionary from WebSocket
        
    Returns:
        bool: True if stored successfully
    """
    try:
        # Extract fields from data (handles both stock and crypto formats)
        # Use provided timestamp if available, otherwise use current time
        if 'timestamp' in data:
            if isinstance(data['timestamp'], str):
                timestamp = datetime.fromisoformat(data['timestamp'])
            else:
                timestamp = data['timestamp']
        else:
            timestamp = datetime.now()
        
        price = data.get('c', data.get('close', 0))  # Close price
        volume = data.get('v', data.get('volume', 0))
        high = data.get('h', data.get('high'))
        low = data.get('l', data.get('low'))  
        open_price = data.get('o', data.get('open'))
        vwap = data.get('vw', data.get('vwap'))
        
        with get_db_cursor() as cursor:
            # Prepare raw_data for JSON serialization (convert datetime objects to strings)
            raw_data_copy = data.copy()
            if 'timestamp' in raw_data_copy and hasattr(raw_data_copy['timestamp'], 'isoformat'):
                raw_data_copy['timestamp'] = raw_data_copy['timestamp'].isoformat()
            
            cursor.execute("""
                INSERT INTO market_data 
                (timestamp, symbol, asset_type, price, volume, high, low, open, vwap, raw_data)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                timestamp, symbol, asset_type, price, volume, 
                high, low, open_price, vwap, json.dumps(raw_data_copy)
            ))
        
        logger.debug(f"Stored {asset_type} data for {symbol}: ${price:.4f}, Vol: {volume:,.0f}")
        return True
        
    except Exception as e:
        logger.error(f"Error storing market data for {symbol}: {e}")
        return False

def store_anomaly(asset_type: str, anomaly: Dict) -> bool:
    """
    Store anomaly detection result
    
    Args:
        asset_type: 'stocks' or 'crypto'
        anomaly: Anomaly dictionary with detection details
        
    Returns:
        bool: True if stored successfully
    """
    try:
        with get_db_cursor() as cursor:
            cursor.execute("""
                INSERT INTO anomalies 
                (start_time, symbol, asset_type, anomaly_type, multiplier, 
                 current_value, average_value, details)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                datetime.now(),
                anomaly.get('symbol', ''),
                asset_type,
                anomaly.get('type', ''),
                anomaly.get('multiplier', 0),
                anomaly.get('current_volume', anomaly.get('current_value', 0)),
                anomaly.get('average_volume', anomaly.get('average_value', 0)),
                json.dumps(anomaly)
            ))
        
        logger.warning(f"🚨 STORED ANOMALY: {anomaly.get('type')} in {anomaly.get('symbol')} - {anomaly.get('multiplier', 0):.2f}x")
        return True
        
    except Exception as e:
        logger.error(f"Error storing anomaly: {e}")
        return False

def get_recent_data(symbol: Optional[str] = None, 
                   asset_type: Optional[str] = None,
                   hours: int = 1) -> List[Dict]:
    """
    Get recent market data from database
    
    Args:
        symbol: Specific symbol to filter (optional)
        asset_type: 'stocks' or 'crypto' (optional)
        hours: Number of hours to look back
        
    Returns:
        List of market data records
    """
    try:
        since = datetime.now() - timedelta(hours=hours)
        
        query = """
            SELECT timestamp, symbol, asset_type, price, volume, high, low, open, vwap
            FROM market_data 
            WHERE timestamp > ?
        """
        params = [since]
        
        if symbol:
            query += " AND symbol = ?"
            params.append(symbol)
            
        if asset_type:
            query += " AND asset_type = ?"
            params.append(asset_type)
            
        query += " ORDER BY timestamp DESC"
        
        with get_db_cursor() as cursor:
            cursor.execute(query, params)
            rows = cursor.fetchall()
            
            return [dict(row) for row in rows]
            
    except Exception as e:
        logger.error(f"Error getting recent data: {e}")
        return []

def get_recent_anomalies(hours: int = 24) -> List[Dict]:
    """
    Get recent anomalies from database
    
    Args:
        hours: Number of hours to look back
        
    Returns:
        List of anomaly records
    """
    try:
        since = datetime.now() - timedelta(hours=hours)
        
        with get_db_cursor() as cursor:
            cursor.execute("""
                SELECT start_time, end_time, symbol, asset_type, anomaly_type, 
                       multiplier, current_value, average_value, status
                FROM anomalies 
                WHERE start_time > ?
                ORDER BY start_time DESC
            """, (since,))
            
            rows = cursor.fetchall()
            return [dict(row) for row in rows]
            
    except Exception as e:
        logger.error(f"Error getting recent anomalies: {e}")
        return []

def get_symbols_by_asset_type() -> Dict[str, List[str]]:
    """Get all symbols grouped by asset type"""
    try:
        with get_db_cursor() as cursor:
            cursor.execute("""
                SELECT DISTINCT asset_type, symbol 
                FROM market_data 
                ORDER BY asset_type, symbol
            """)
            
            rows = cursor.fetchall()
            
            result = {}
            for row in rows:
                asset_type = row['asset_type']
                symbol = row['symbol']
                if asset_type not in result:
                    result[asset_type] = []
                result[asset_type].append(symbol)
                
            return result
            
    except Exception as e:
        logger.error(f"Error getting symbols: {e}")
        return {}

def cleanup_old_data(days: int = 7):
    """
    Clean up old data to manage storage
    
    Args:
        days: Keep data newer than this many days
    """
    try:
        cutoff = datetime.now() - timedelta(days=days)
        
        with get_db_cursor() as cursor:
            # Clean old market data
            cursor.execute("DELETE FROM market_data WHERE timestamp < ?", (cutoff,))
            market_deleted = cursor.rowcount
            
            # Clean old anomalies
            cursor.execute("DELETE FROM anomalies WHERE start_time < ?", (cutoff,))
            anomaly_deleted = cursor.rowcount
            
            # Vacuum to reclaim space
            cursor.execute("VACUUM")
            
        logger.info(f"Cleaned up {market_deleted} market records and {anomaly_deleted} anomaly records older than {days} days")
        
    except Exception as e:
        logger.error(f"Error cleaning up old data: {e}")

def get_database_stats() -> Dict:
    """Get database statistics"""
    try:
        with get_db_cursor() as cursor:
            # Market data count
            cursor.execute("SELECT COUNT(*) as count FROM market_data")
            market_count = cursor.fetchone()['count']
            
            # Anomaly count
            cursor.execute("SELECT COUNT(*) as count FROM anomalies")
            anomaly_count = cursor.fetchone()['count']
            
            # Database size
            db_size = DB_PATH.stat().st_size if DB_PATH.exists() else 0
            
            # Latest data timestamp
            cursor.execute("SELECT MAX(timestamp) as latest FROM market_data")
            latest_data = cursor.fetchone()['latest']
            
            return {
                'market_data_count': market_count,
                'anomaly_count': anomaly_count,
                'database_size_mb': db_size / (1024 * 1024),
                'latest_data': latest_data,
                'database_path': str(DB_PATH)
            }
            
    except Exception as e:
        logger.error(f"Error getting database stats: {e}")
        return {}

if __name__ == "__main__":
    # Demo/test mode
    logging.basicConfig(level=logging.INFO)
    
    # Initialize database
    init_database()
    
    # Test storing some data
    test_data = {
        'c': 245.50,  # close price
        'v': 1500,    # volume
        'h': 246.00,  # high
        'l': 244.50,  # low
        'o': 245.00,  # open
        'vw': 245.25  # vwap
    }
    
    store_market_data('stocks', 'AAPL', test_data)
    
    # Test anomaly
    test_anomaly = {
        'symbol': 'AAPL',
        'type': 'volume_spike',
        'multiplier': 3.5,
        'current_volume': 5250,
        'average_volume': 1500
    }
    
    store_anomaly('stocks', test_anomaly)
    
    # Show stats
    stats = get_database_stats()
    print("\n=== Database Stats ===")
    for key, value in stats.items():
        print(f"{key}: {value}")