"""
Data Schema Analysis and Exploration
====================================

This script analyzes the collected stock market data to understand:
- Data structure and schema
- Data quality and completeness
- Statistical properties
- Temporal patterns
- Cross-asset relationships
- Potential anomaly patterns
"""

import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
from pathlib import Path
import warnings
from datetime import datetime, timedelta
import os

warnings.filterwarnings('ignore')

# Set up plotting style
plt.style.use('seaborn-v0_8')
sns.set_palette("husl")

class DataSchemaAnalyzer:
    def __init__(self, data_dir: str = "data/raw"):
        self.data_dir = Path(data_dir)
        self.symbols = ['AAPL', 'GOOGL', 'MSFT', 'TSLA', 'VOO']
        self.data = {}
        self.load_data()
    
    def load_data(self):
        """Load all CSV files and store in dictionary."""
        print("Loading data files...")
        for symbol in self.symbols:
            files = list(self.data_dir.glob(f"{symbol}_*.csv"))
            if files:
                # Get the most recent file for each symbol
                latest_file = max(files, key=lambda x: x.stat().st_mtime)
                df = pd.read_csv(latest_file, index_col=0, parse_dates=True)
                self.data[symbol] = df
                print(f"✅ {symbol}: {len(df)} records from {latest_file.name}")
            else:
                print(f"❌ No data found for {symbol}")
    
    def analyze_schema(self):
        """Analyze the data schema and structure."""
        print("\n" + "="*60)
        print("DATA SCHEMA ANALYSIS")
        print("="*60)
        
        for symbol, df in self.data.items():
            print(f"\n📊 {symbol} Schema:")
            print(f"Shape: {df.shape}")
            print(f"Index: {df.index.name} ({type(df.index).__name__})")
            print(f"Columns: {list(df.columns)}")
            print(f"Data types:\n{df.dtypes}")
            print(f"Memory usage: {df.memory_usage(deep=True).sum() / 1024**2:.2f} MB")
            
            # Check for missing values
            missing = df.isnull().sum()
            if missing.any():
                print(f"Missing values:\n{missing[missing > 0]}")
            else:
                print("✅ No missing values")
            
            # Time range analysis
            print(f"Time range: {df.index.min()} to {df.index.max()}")
            print(f"Duration: {df.index.max() - df.index.min()}")
            
            # Sample data
            print(f"\nSample data:")
            print(df.head(3))
            print("-" * 50)
    
    def analyze_data_quality(self):
        """Analyze data quality issues."""
        print("\n" + "="*60)
        print("DATA QUALITY ANALYSIS")
        print("="*60)
        
        quality_report = {}
        
        for symbol, df in self.data.items():
            print(f"\n🔍 {symbol} Quality Check:")
            
            # Basic statistics
            print("Basic Statistics:")
            print(df.describe())
            
            # Check for anomalies in data
            issues = []
            
            # 1. Negative values (shouldn't exist for prices/volume)
            negative_cols = []
            for col in ['open', 'high', 'low', 'close', 'volume']:
                if col in df.columns and (df[col] < 0).any():
                    negative_cols.append(col)
            if negative_cols:
                issues.append(f"Negative values in: {negative_cols}")
            
            # 2. High > Low check
            if 'high' in df.columns and 'low' in df.columns:
                invalid_hl = (df['high'] < df['low']).sum()
                if invalid_hl > 0:
                    issues.append(f"High < Low in {invalid_hl} records")
            
            # 3. OHLC relationship checks
            ohlc_cols = ['open', 'high', 'low', 'close']
            if all(col in df.columns for col in ohlc_cols):
                # Check if OHLC values are within high-low range
                ohlc_issues = 0
                ohlc_issues += (df['open'] > df['high']).sum()
                ohlc_issues += (df['open'] < df['low']).sum()
                ohlc_issues += (df['close'] > df['high']).sum()
                ohlc_issues += (df['close'] < df['low']).sum()
                if ohlc_issues > 0:
                    issues.append(f"OHLC consistency issues: {ohlc_issues} records")
            
            # 4. Zero volume
            if 'volume' in df.columns:
                zero_volume = (df['volume'] == 0).sum()
                if zero_volume > 0:
                    issues.append(f"Zero volume in {zero_volume} records")
            
            # 5. Duplicate timestamps
            duplicate_times = df.index.duplicated().sum()
            if duplicate_times > 0:
                issues.append(f"Duplicate timestamps: {duplicate_times}")
            
            # 6. Time gaps analysis
            time_diffs = df.index.to_series().diff()
            expected_freq = pd.Timedelta('1 minute')
            large_gaps = (time_diffs > expected_freq * 10).sum()  # > 10 minutes
            if large_gaps > 0:
                issues.append(f"Large time gaps (>10min): {large_gaps}")
            
            if issues:
                print("⚠️  Issues found:")
                for issue in issues:
                    print(f"   - {issue}")
            else:
                print("✅ No quality issues detected")
            
            quality_report[symbol] = issues
            print("-" * 50)
        
        return quality_report
    
    def analyze_trading_patterns(self):
        """Analyze trading patterns and market hours."""
        print("\n" + "="*60)
        print("TRADING PATTERNS ANALYSIS")
        print("="*60)
        
        for symbol, df in self.data.items():
            print(f"\n📈 {symbol} Trading Patterns:")
            
            # Extract time components
            df_analysis = df.copy()
            df_analysis['hour'] = df_analysis.index.hour
            df_analysis['day_of_week'] = df_analysis.index.day_name()
            df_analysis['date'] = df_analysis.index.date
            
            # Trading hours analysis
            trading_hours = df_analysis['hour'].value_counts().sort_index()
            print(f"Trading hours distribution:")
            print(f"   Pre-market (3-9 AM): {trading_hours[3:10].sum()} records")
            print(f"   Regular hours (9:30 AM - 4 PM): {trading_hours[9:16].sum()} records")
            print(f"   After hours (4-8 PM): {trading_hours[16:21].sum()} records")
            
            # Volume patterns
            if 'volume' in df.columns:
                hourly_volume = df_analysis.groupby('hour')['volume'].mean()
                peak_hour = hourly_volume.idxmax()
                print(f"   Peak volume hour: {peak_hour}:00 (avg: {hourly_volume[peak_hour]:,.0f})")
            
            # Daily patterns
            daily_counts = df_analysis['date'].value_counts().sort_index()
            print(f"Records per day: {daily_counts.describe()}")
            
            print("-" * 50)
    
    def analyze_price_movements(self):
        """Analyze price movements and volatility."""
        print("\n" + "="*60)
        print("PRICE MOVEMENT ANALYSIS")
        print("="*60)
        
        movement_stats = {}
        
        for symbol, df in self.data.items():
            if 'close' not in df.columns:
                continue
                
            print(f"\n💰 {symbol} Price Analysis:")
            
            # Calculate returns
            df_analysis = df.copy()
            df_analysis['returns'] = df_analysis['close'].pct_change()
            df_analysis['log_returns'] = np.log(df_analysis['close'] / df_analysis['close'].shift(1))
            
            # Price range analysis
            if all(col in df.columns for col in ['high', 'low']):
                df_analysis['price_range'] = df_analysis['high'] - df_analysis['low']
                df_analysis['price_range_pct'] = df_analysis['price_range'] / df_analysis['close'] * 100
            
            # Basic price statistics
            print(f"Price range: ${df_analysis['close'].min():.2f} - ${df_analysis['close'].max():.2f}")
            print(f"Average price: ${df_analysis['close'].mean():.2f}")
            
            # Returns analysis
            returns_stats = df_analysis['returns'].describe()
            print(f"Returns statistics:")
            print(f"   Mean: {returns_stats['mean']*100:.4f}%")
            print(f"   Std: {returns_stats['std']*100:.4f}%")
            print(f"   Min: {returns_stats['min']*100:.4f}%")
            print(f"   Max: {returns_stats['max']*100:.4f}%")
            
            # Volatility (annualized)
            minute_vol = df_analysis['returns'].std()
            daily_vol = minute_vol * np.sqrt(390)  # 390 trading minutes per day
            annual_vol = daily_vol * np.sqrt(252)  # 252 trading days per year
            print(f"Annualized volatility: {annual_vol*100:.2f}%")
            
            # Large movements (potential anomalies)
            large_moves = df_analysis[abs(df_analysis['returns']) > 0.05]  # >5% moves
            print(f"Large movements (>5%): {len(large_moves)} occurrences")
            
            movement_stats[symbol] = {
                'volatility': annual_vol,
                'large_moves': len(large_moves),
                'price_range': (df_analysis['close'].min(), df_analysis['close'].max())
            }
            
            print("-" * 50)
        
        return movement_stats
    
    def analyze_volume_patterns(self):
        """Analyze volume patterns."""
        print("\n" + "="*60)
        print("VOLUME PATTERN ANALYSIS")
        print("="*60)
        
        for symbol, df in self.data.items():
            if 'volume' not in df.columns:
                continue
                
            print(f"\n📊 {symbol} Volume Analysis:")
            
            volume_stats = df['volume'].describe()
            print(f"Volume statistics:")
            print(f"   Mean: {volume_stats['mean']:,.0f}")
            print(f"   Median: {volume_stats['50%']:,.0f}")
            print(f"   Max: {volume_stats['max']:,.0f}")
            print(f"   Min: {volume_stats['min']:,.0f}")
            
            # Volume spikes (potential anomalies)
            volume_threshold = volume_stats['mean'] + 3 * volume_stats['std']
            volume_spikes = df[df['volume'] > volume_threshold]
            print(f"Volume spikes (>3σ): {len(volume_spikes)} occurrences")
            
            if len(volume_spikes) > 0:
                print("Recent volume spikes:")
                spike_sample = volume_spikes.tail(3)[['volume', 'close']]
                for idx, row in spike_sample.iterrows():
                    print(f"   {idx}: {row['volume']:,.0f} shares at ${row['close']:.2f}")
            
            print("-" * 50)
    
    def cross_asset_analysis(self):
        """Analyze relationships between different assets."""
        print("\n" + "="*60)
        print("CROSS-ASSET ANALYSIS")
        print("="*60)
        
        # Create a combined dataframe with close prices
        close_prices = pd.DataFrame()
        for symbol, df in self.data.items():
            if 'close' in df.columns:
                close_prices[symbol] = df['close']
        
        # Calculate correlations
        correlations = close_prices.corr()
        print("Price correlations:")
        print(correlations.round(3))
        
        # Calculate returns correlations
        returns = close_prices.pct_change().dropna()
        returns_corr = returns.corr()
        print("\nReturns correlations:")
        print(returns_corr.round(3))
        
        # Find pairs with high/low correlations
        print("\nCorrelation insights:")
        for i in range(len(correlations.columns)):
            for j in range(i+1, len(correlations.columns)):
                asset1, asset2 = correlations.columns[i], correlations.columns[j]
                corr_val = correlations.iloc[i, j]
                if corr_val > 0.8:
                    print(f"   High correlation: {asset1}-{asset2}: {corr_val:.3f}")
                elif corr_val < 0.2:
                    print(f"   Low correlation: {asset1}-{asset2}: {corr_val:.3f}")
    
    def generate_summary_report(self):
        """Generate a comprehensive summary report."""
        print("\n" + "="*60)
        print("SUMMARY REPORT")
        print("="*60)
        
        total_records = sum(len(df) for df in self.data.values())
        print(f"\n📋 Dataset Summary:")
        print(f"   Total symbols: {len(self.data)}")
        print(f"   Total records: {total_records:,}")
        print(f"   Average records per symbol: {total_records/len(self.data):,.0f}")
        
        # Time coverage
        all_times = []
        for df in self.data.values():
            all_times.extend(df.index.tolist())
        
        if all_times:
            min_time = min(all_times)
            max_time = max(all_times)
            print(f"   Time coverage: {min_time} to {max_time}")
            print(f"   Duration: {max_time - min_time}")
        
        # Data characteristics
        print(f"\n🔍 Data Characteristics:")
        print(f"   Frequency: Minute-level data")
        print(f"   Fields: OHLC prices, volume, VWAP, transaction count")
        print(f"   Market coverage: Pre-market, regular hours, after-hours")
        
        # Asset types
        individual_stocks = ['AAPL', 'GOOGL', 'MSFT', 'TSLA']
        etfs = ['VOO']
        
        print(f"\n📈 Asset Composition:")
        print(f"   Individual stocks: {[s for s in individual_stocks if s in self.data]}")
        print(f"   ETFs: {[s for s in etfs if s in self.data]}")
        
        print(f"\n✅ Data is ready for:")
        print(f"   - Feature engineering")
        print(f"   - Anomaly detection model training")
        print(f"   - Real-time streaming integration")
        print(f"   - Cross-asset pattern analysis")

def main():
    """Run the complete data schema analysis."""
    analyzer = DataSchemaAnalyzer()
    
    if not analyzer.data:
        print("❌ No data files found. Please run data collection first.")
        return
    
    # Run all analyses
    analyzer.analyze_schema()
    quality_report = analyzer.analyze_data_quality()
    analyzer.analyze_trading_patterns()
    movement_stats = analyzer.analyze_price_movements()
    analyzer.analyze_volume_patterns()
    analyzer.cross_asset_analysis()
    analyzer.generate_summary_report()
    
    print(f"\n🎉 Analysis complete! Data schema is well understood.")
    print(f"💡 Ready to proceed with feature engineering and streaming implementation.")

if __name__ == "__main__":
    main()