"""
Data collection script for stock market data from Polygon.io API.
"""

import os
import json
import pandas as pd
from datetime import datetime, timedelta
from pathlib import Path
from polygon import RESTClient
from dotenv import load_dotenv
import logging

# Load environment variables
load_dotenv()

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class StockDataCollector:
    def __init__(self):
        self.api_key = os.getenv('POLYGON_API_KEY')
        if not self.api_key:
            raise ValueError("POLYGON_API_KEY not found in environment variables")
        
        self.client = RESTClient(self.api_key)
        
        # Set up data directories
        self.raw_data_dir = Path("data/raw")
        self.raw_data_dir.mkdir(parents=True, exist_ok=True)
    
    def get_stock_aggregates(self, symbol: str, timespan: str = "minute", 
                           multiplier: int = 1, from_date: str = None, 
                           to_date: str = None, limit: int = 5000):
        """
        Get aggregated stock data for a given symbol.
        
        Args:
            symbol: Stock symbol (e.g., 'AAPL')
            timespan: Timespan ('minute', 'hour', 'day', 'week', 'month', 'quarter', 'year')
            multiplier: Size of timespan multiplier
            from_date: Start date (YYYY-MM-DD)
            to_date: End date (YYYY-MM-DD)
            limit: Number of results to return (max 50000)
        """
        try:
            logger.info(f"Fetching {timespan} data for {symbol} from {from_date} to {to_date}")
            
            aggs = self.client.get_aggs(
                ticker=symbol,
                multiplier=multiplier,
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
                    'vwap': agg.vwap if hasattr(agg, 'vwap') else None,
                    'transactions': agg.transactions if hasattr(agg, 'transactions') else None
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
    
    def get_market_status(self):
        """Get current market status."""
        try:
            status = self.client.get_market_status()
            logger.info(f"Market status: {status}")
            return status
        except Exception as e:
            logger.error(f"Error getting market status: {e}")
            return None
    
    def get_ticker_details(self, symbol: str):
        """Get detailed information about a ticker."""
        try:
            details = self.client.get_ticker_details(symbol)
            logger.info(f"Retrieved details for {symbol}")
            return details
        except Exception as e:
            logger.error(f"Error getting ticker details for {symbol}: {e}")
            return None
    
    def save_data(self, df: pd.DataFrame, symbol: str, timespan: str, 
                  from_date: str, to_date: str):
        """Save DataFrame to CSV file."""
        if df.empty:
            logger.warning(f"No data to save for {symbol}")
            return None
        
        filename = f"{symbol}_{timespan}_{from_date}_{to_date}.csv"
        filepath = self.raw_data_dir / filename
        
        df.to_csv(filepath)
        logger.info(f"Saved {len(df)} records to {filepath}")
        return filepath
    
    def collect_sample_data(self):
        """Collect sample data for testing and exploration."""
        # Get data for a few popular stocks
        symbols = ['AAPL', 'GOOGL', 'MSFT', 'TSLA', 'VOO']
        
        # Get last 5 trading days of minute data
        end_date = datetime.now().date()
        start_date = end_date - timedelta(days=7)  # Get a week to ensure we have 5 trading days
        
        from_date = start_date.strftime('%Y-%m-%d')
        to_date = end_date.strftime('%Y-%m-%d')
        
        results = {}
        
        for symbol in symbols:
            logger.info(f"Collecting data for {symbol}")
            
            # Get minute-level data
            df = self.get_stock_aggregates(
                symbol=symbol,
                timespan='minute',
                from_date=from_date,
                to_date=to_date,
                limit=5000
            )
            
            if not df.empty:
                # Save the data
                filepath = self.save_data(df, symbol, 'minute', from_date, to_date)
                results[symbol] = {
                    'records': len(df),
                    'filepath': str(filepath),
                    'date_range': f"{df.index.min()} to {df.index.max()}"
                }
                
                # Display sample data
                print(f"\n{symbol} Sample Data:")
                print(f"Records: {len(df)}")
                print(f"Date range: {df.index.min()} to {df.index.max()}")
                print(df.head())
                print(f"Columns: {list(df.columns)}")
            else:
                results[symbol] = {'error': 'No data retrieved'}
        
        return results

def main():
    """Main function to test data collection."""
    try:
        collector = StockDataCollector()
        
        # Check market status
        print("=== Market Status ===")
        status = collector.get_market_status()
        if status:
            print(f"Market: {status.market}")
            print(f"Server time: {status.server_time}")
        
        # Collect sample data
        print("\n=== Collecting Sample Data ===")
        results = collector.collect_sample_data()
        
        # Summary
        print("\n=== Collection Summary ===")
        for symbol, result in results.items():
            if 'error' in result:
                print(f"{symbol}: {result['error']}")
            else:
                print(f"{symbol}: {result['records']} records, {result['date_range']}")
        
        print(f"\nData saved to: {collector.raw_data_dir}")
        
    except Exception as e:
        logger.error(f"Error in main: {e}")
        raise

if __name__ == "__main__":
    main()