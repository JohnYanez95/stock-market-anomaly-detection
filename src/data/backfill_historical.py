#!/usr/bin/env python3
"""
Historical data backfill script for cryptocurrency market data.

This script uses the Polygon.io REST API to collect historical data
for the past year and stores it in the SQLite database.

Usage:
    python src/data/backfill_historical.py [--days DAYS]
    
    Options:
    --days: Number of days to backfill (default: 365)
    --symbols: Comma-separated list of symbols (default: all crypto)
"""

import os
import sys
import argparse
import pandas as pd
from datetime import datetime, timedelta
from pathlib import Path
from polygon import RESTClient
from dotenv import load_dotenv
import logging
import time
from typing import List, Dict, Any
import sqlite3
import json

# Add src to path for imports
sys.path.append('src')
from data.database import get_db_connection, store_market_data

# Load environment variables
load_dotenv()

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Crypto symbols to backfill
CRYPTO_SYMBOLS = ['BTC-USD', 'ETH-USD', 'ADA-USD', 'SOL-USD', 'DOT-USD', 'DOGE-USD']

class HistoricalDataBackfiller:
    def __init__(self):
        self.api_key = os.getenv('POLYGON_API_KEY')
        if not self.api_key:
            raise ValueError("POLYGON_API_KEY not found in environment variables")
        
        self.client = RESTClient(self.api_key)
        
        # Detect subscription tiers from environment
        self.tier_stocks = os.getenv('POLYGON_TIER_STOCKS', 'basic').lower()
        self.tier_crypto = os.getenv('POLYGON_TIER_CRYPTO', 'basic').lower()
        
        # Configure rate limiting based on tier
        self.configure_rate_limits()
        
        self.api_calls = 0
        self.last_api_call = datetime.now()
        
    def configure_rate_limits(self):
        """Configure rate limits and data access based on subscription tiers."""
        # Rate limit configuration
        if self.tier_crypto in ['starter', 'developer', 'advanced']:
            self.rate_limit_calls = None  # Unlimited API calls
            self.rate_limit_delay = 0.1    # 100ms courtesy delay
            self.historical_years = 10 if self.tier_crypto == 'starter' else 15
            self.has_realtime = True
            logger.info(f"Crypto tier: {self.tier_crypto.title()} - Unlimited API calls, {self.historical_years}+ years data")
        else:
            self.rate_limit_calls = 5      # Basic tier: 5 calls/minute
            self.rate_limit_delay = 12     # 12 seconds between calls
            self.historical_years = 2      # 2 years historical
            self.has_realtime = False
            logger.info(f"Crypto tier: Basic - 5 calls/minute, 2 years historical data")
            
    def _rate_limit(self):
        """Apply rate limiting based on subscription tier."""
        if self.rate_limit_calls is None:
            # Starter/Developer/Advanced tier - unlimited calls
            time.sleep(self.rate_limit_delay)  # Small courtesy delay
        else:
            # Basic tier - strict rate limiting
            self.api_calls += 1
            
            if self.api_calls >= self.rate_limit_calls:
                elapsed = (datetime.now() - self.last_api_call).total_seconds()
                if elapsed < 60:
                    wait_time = 60 - elapsed + 1
                    logger.info(f"Rate limit reached. Waiting {wait_time:.0f} seconds...")
                    time.sleep(wait_time)
                self.api_calls = 0
                self.last_api_call = datetime.now()
            else:
                time.sleep(self.rate_limit_delay)
    
    def get_crypto_aggregates(self, symbol: str, timespan: str = "minute", 
                            from_date: str = None, to_date: str = None, 
                            limit: int = 50000) -> pd.DataFrame:
        """
        Get aggregated crypto data for a given symbol.
        
        Args:
            symbol: Crypto symbol (e.g., 'BTC-USD')
            timespan: Timespan ('minute', 'hour', 'day')
            from_date: Start date (YYYY-MM-DD)
            to_date: End date (YYYY-MM-DD)
            limit: Number of results to return (max 50000)
        """
        try:
            # Apply rate limiting
            self._rate_limit()
            
            # Convert symbol format for API (BTC-USD -> X:BTCUSD)
            ticker = f"X:{symbol.replace('-', '')}"
            
            logger.info(f"Fetching {timespan} data for {symbol} from {from_date} to {to_date}")
            
            aggs = self.client.get_aggs(
                ticker=ticker,
                multiplier=1,
                timespan=timespan,
                from_=from_date,
                to=to_date,
                limit=limit
            )
            
            # Convert to DataFrame
            data = []
            for agg in aggs:
                data.append({
                    'timestamp': datetime.fromtimestamp(agg.timestamp / 1000),
                    'open': agg.open,
                    'high': agg.high,
                    'low': agg.low,
                    'close': agg.close,
                    'volume': agg.volume,
                    'vwap': agg.vwap if hasattr(agg, 'vwap') else None
                })
            
            df = pd.DataFrame(data)
            if not df.empty:
                df.set_index('timestamp', inplace=True)
                df.sort_index(inplace=True)
            
            logger.info(f"Retrieved {len(df)} records for {symbol}")
            return df
            
        except Exception as e:
            logger.error(f"Error fetching data for {symbol}: {e}")
            return pd.DataFrame()
    
    def store_to_database(self, df: pd.DataFrame, symbol: str) -> int:
        """Store DataFrame to database using efficient UPSERT logic."""
        if df.empty:
            return 0
        
        stored_count = 0
        
        try:
            conn = sqlite3.connect('data/streaming_data.db')
            cursor = conn.cursor()
            
            # Use SQLite's INSERT OR REPLACE for efficient UPSERT
            # First, we need to ensure we have the record ID for updates
            for timestamp, row in df.iterrows():
                timestamp_str = timestamp.strftime('%Y-%m-%d %H:%M:%S')
                
                # Check if record exists to decide if it's new
                cursor.execute("""
                    SELECT COUNT(*) FROM market_data 
                    WHERE timestamp = ? AND symbol = ?
                """, (timestamp_str, symbol))
                
                exists = cursor.fetchone()[0] > 0
                
                if not exists:
                    # Insert new record
                    cursor.execute("""
                        INSERT INTO market_data 
                        (timestamp, symbol, asset_type, price, volume, high, low, open, vwap, raw_data)
                        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """, (
                        timestamp_str,  # Use string format for consistency
                        symbol,
                        'crypto',
                        float(row['close']),
                        float(row['volume']),
                        float(row['high']),
                        float(row['low']),
                        float(row['open']),
                        float(row['vwap'] if pd.notna(row['vwap']) else row['close']),
                        json.dumps({
                            'timestamp': timestamp.isoformat(),
                            'open': float(row['open']),
                            'high': float(row['high']),
                            'low': float(row['low']),
                            'close': float(row['close']),
                            'volume': float(row['volume']),
                            'vwap': float(row['vwap'] if pd.notna(row['vwap']) else row['close'])
                        })
                    ))
                    stored_count += 1
            
            conn.commit()
            conn.close()
            
            logger.info(f"Stored {stored_count} new records for {symbol}")
            
        except Exception as e:
            logger.error(f"Error storing data: {e}")
            import traceback
            traceback.print_exc()
        
        return stored_count
    
    def backfill_symbol(self, symbol: str, days: int = 365, timespan: str = 'minute') -> Dict[str, Any]:
        """Backfill historical data for a single symbol."""
        logger.info(f"Starting backfill for {symbol} ({days} days, {timespan} granularity)")
        
        end_date = datetime.now().date()
        start_date = end_date - timedelta(days=days)
        
        total_records = 0
        total_stored = 0
        
        # Adjust chunk size based on timespan
        if timespan == 'minute':
            chunk_days = 30  # ~43k minutes in 30 days
        elif timespan == 'hour':
            chunk_days = 365  # ~8.7k hours in a year
        else:  # day
            chunk_days = 3650  # 10 years of daily data
        
        current_start = start_date
        while current_start < end_date:
            current_end = min(current_start + timedelta(days=chunk_days), end_date)
            
            # Fetch data for this chunk
            df = self.get_crypto_aggregates(
                symbol=symbol,
                timespan=timespan,
                from_date=current_start.strftime('%Y-%m-%d'),
                to_date=current_end.strftime('%Y-%m-%d')
            )
            
            if not df.empty:
                total_records += len(df)
                stored = self.store_to_database(df, symbol)
                total_stored += stored
                
                logger.info(f"{symbol}: Processed {current_start} to {current_end} "
                          f"({len(df)} records, {stored} new)")
            
            current_start = current_end + timedelta(days=1)
        
        return {
            'symbol': symbol,
            'total_records': total_records,
            'new_records': total_stored,
            'date_range': f"{start_date} to {end_date}"
        }
    
    def backfill_all(self, symbols: List[str], days: int = 365, timespan: str = 'minute'):
        """Backfill historical data for all symbols."""
        results = []
        
        logger.info(f"Starting backfill for {len(symbols)} symbols ({days} days each, {timespan} granularity)")
        logger.info(f"Symbols: {', '.join(symbols)}")
        
        for i, symbol in enumerate(symbols, 1):
            logger.info(f"\nProcessing {i}/{len(symbols)}: {symbol}")
            result = self.backfill_symbol(symbol, days, timespan)
            results.append(result)
            
            # Show progress
            total_new = sum(r['new_records'] for r in results)
            logger.info(f"Progress: {i}/{len(symbols)} symbols, {total_new} new records total")
        
        return results

def print_configuration_summary():
    """Print configuration summary based on environment settings."""
    tier_crypto = os.getenv('POLYGON_TIER_CRYPTO', 'basic').lower()
    tier_stocks = os.getenv('POLYGON_TIER_STOCKS', 'basic').lower()
    
    print("\n=== Polygon.io Subscription Configuration ===")
    print(f"Crypto Tier: {tier_crypto.title()}")
    print(f"Stocks Tier: {tier_stocks.title()}")
    
    if tier_crypto in ['starter', 'developer', 'advanced']:
        print("\n✅ Crypto Capabilities:")
        print("  - Unlimited API calls")
        print("  - 10+ years historical data")
        print("  - Real-time data access")
        print("  - Fast backfill (100ms between calls)")
        
        # Time estimates for unlimited tier
        print("\n⏱️ Estimated Backfill Time:")
        print("  - 1 symbol, 1 year: ~5-7 minutes")
        print("  - 6 symbols, 1 year: ~30-40 minutes")
        print("  - 6 symbols, YTD: ~25-30 minutes")
    else:
        print("\n⚠️ Basic Tier Limitations:")
        print("  - 5 API calls per minute")
        print("  - 2 years historical data")
        print("  - 15-minute delayed data")
        print("  - Slow backfill (12s between calls)")
        
        # Time estimates for basic tier
        print("\n⏱️ Estimated Backfill Time:")
        print("  - 1 symbol, 1 year: ~15-20 minutes")
        print("  - 6 symbols, 1 year: ~90-120 minutes")
        print("  - 6 symbols, YTD: ~75-90 minutes")
    
    print("\n" + "="*40)

def main():
    """Main function to run historical backfill."""
    parser = argparse.ArgumentParser(description='Backfill historical crypto data')
    parser.add_argument('--days', type=int, default=None, 
                       help='Number of days to backfill (default: 365 or max available)')
    parser.add_argument('--symbols', type=str, default=None,
                       help='Comma-separated list of symbols (default: all crypto)')
    parser.add_argument('--timespan', type=str, default='minute',
                       choices=['minute', 'hour', 'day'],
                       help='Data granularity (default: minute)')
    
    args = parser.parse_args()
    
    # Print configuration summary
    print_configuration_summary()
    
    # Determine symbols to process
    if args.symbols:
        symbols = [s.strip() for s in args.symbols.split(',')]
    else:
        symbols = CRYPTO_SYMBOLS
    
    try:
        # Initialize backfiller to get tier information
        backfiller = HistoricalDataBackfiller()
        
        # Determine days to backfill based on tier and user input
        if args.days:
            days = args.days
        else:
            # Smart defaults based on tier
            if backfiller.tier_crypto in ['starter', 'developer', 'advanced']:
                days = 365  # Default to 1 year for paid tiers
                logger.info(f"Using default: 365 days (1 year) for {backfiller.tier_crypto} tier")
            else:
                days = 90   # Default to 90 days for basic tier
                logger.info(f"Using default: 90 days for basic tier (to stay within limits)")
        
        # Validate days against tier limits
        max_days = backfiller.historical_years * 365
        if days > max_days:
            logger.warning(f"Requested {days} days exceeds tier limit of {max_days} days")
            days = max_days
        # Check current database status
        conn = sqlite3.connect('data/streaming_data.db')
        cursor = conn.cursor()
        cursor.execute("SELECT COUNT(*) FROM market_data")
        initial_count = cursor.fetchone()[0]
        conn.close()
        
        logger.info(f"Current database has {initial_count} records")
        
        # Run backfill
        results = backfiller.backfill_all(symbols, days, args.timespan)
        
        # Summary
        print("\n=== Backfill Summary ===")
        total_records = 0
        total_new = 0
        
        for result in results:
            print(f"{result['symbol']}: {result['new_records']} new records "
                  f"(out of {result['total_records']} fetched)")
            total_records += result['total_records']
            total_new += result['new_records']
        
        print(f"\nTotal: {total_new} new records added "
              f"(out of {total_records} fetched)")
        
        # Check final database status
        conn = sqlite3.connect('data/streaming_data.db')
        cursor = conn.cursor()
        cursor.execute("SELECT COUNT(*) FROM market_data")
        final_count = cursor.fetchone()[0]
        conn.close()
        
        print(f"\nDatabase now has {final_count} records "
              f"(increased by {final_count - initial_count})")
        
    except Exception as e:
        logger.error(f"Error in backfill: {e}")
        raise

if __name__ == "__main__":
    main()