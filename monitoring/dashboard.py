#!/usr/bin/env python3
"""
Real-Time Crypto Market Dashboard

Interactive Streamlit dashboard showing live cryptocurrency market data
with anomaly detection visualization from SQLite database.

Features:
- 🔒 Secure authentication with session management
- Real-time price charts for 6 crypto symbols
- Auto-refresh every 60 seconds
- Anomaly highlighting and alerts
- Multi-asset overview with volume analysis

Usage:
    streamlit run monitoring/dashboard.py
    
Navigate to: http://localhost:8501
Default credentials: admin / admin123

Security Features:
- PBKDF2 password hashing
- Session timeout management
- API key masking
- Environment-based configuration
"""

import streamlit as st
import sqlite3
import pandas as pd
import plotly.graph_objects as go
import plotly.express as px
from datetime import datetime, timedelta
import time
from pathlib import Path
import sys
import logging
import os

# Add src to Python path for imports
sys.path.append('src')
from data.database import get_db_connection

# Import authentication module
from monitoring.auth import require_authentication, get_current_user, mask_api_key, validate_environment

# Configure page
st.set_page_config(
    page_title="Crypto Market Anomaly Detection",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Database path
DB_PATH = Path("data/streaming_data.db")

@st.cache_data(ttl=60)  # Cache for 60 seconds
def load_market_data(hours_back=24):
    """Load market data from SQLite database"""
    try:
        # Calculate time threshold
        time_threshold = datetime.now() - timedelta(hours=hours_back)
        
        conn = sqlite3.connect(str(DB_PATH))
        query = """
        SELECT timestamp, symbol, asset_type, price, volume, vwap, high, low, open
        FROM market_data 
        WHERE timestamp >= ?
        ORDER BY timestamp DESC
        """
        
        df = pd.read_sql_query(query, conn, params=[time_threshold.isoformat()])
        conn.close()
        
        if not df.empty:
            df['timestamp'] = pd.to_datetime(df['timestamp'])
            df = df.sort_values('timestamp')
        
        return df
    except Exception as e:
        logger.error(f"Error loading market data: {e}")
        return pd.DataFrame()

@st.cache_data(ttl=60)
def load_anomalies(hours_back=24):
    """Load anomaly data from SQLite database"""
    try:
        time_threshold = datetime.now() - timedelta(hours=hours_back)
        
        conn = sqlite3.connect(str(DB_PATH))
        query = """
        SELECT start_time, symbol, anomaly_type, multiplier, details
        FROM anomalies 
        WHERE start_time >= ?
        ORDER BY start_time DESC
        """
        
        df = pd.read_sql_query(query, conn, params=[time_threshold.isoformat()])
        conn.close()
        
        if not df.empty:
            df['start_time'] = pd.to_datetime(df['start_time'])
        
        return df
    except Exception as e:
        logger.error(f"Error loading anomaly data: {e}")
        return pd.DataFrame()

def create_price_chart(df, symbol):
    """Create price chart for a specific symbol"""
    symbol_data = df[df['symbol'] == symbol].copy()
    
    if symbol_data.empty:
        return None
    
    # Calculate recent stats
    if len(symbol_data) > 1:
        latest_price = symbol_data.iloc[-1]['price']
        price_change = latest_price - symbol_data.iloc[-2]['price']
        price_change_pct = (price_change / symbol_data.iloc[-2]['price']) * 100
    else:
        latest_price = symbol_data.iloc[0]['price']
        price_change = 0
        price_change_pct = 0
    
    # Create the chart
    fig = go.Figure()
    
    # Add price line
    fig.add_trace(go.Scatter(
        x=symbol_data['timestamp'],
        y=symbol_data['price'],
        mode='lines+markers',
        name=f'{symbol} Price',
        line=dict(color='#00d4aa', width=2),
        marker=dict(size=4)
    ))
    
    # Update layout
    fig.update_layout(
        title=f"{symbol} - ${latest_price:.6f} ({price_change_pct:+.2f}%)",
        xaxis_title="Time",
        yaxis_title="Price (USD)",
        height=300,
        showlegend=False,
        template="plotly_dark"
    )
    
    return fig

def create_volume_chart(df, symbol):
    """Create volume chart for a specific symbol"""
    symbol_data = df[df['symbol'] == symbol].copy()
    
    if symbol_data.empty:
        return None
    
    # Calculate volume anomalies (simple 3x threshold)
    if len(symbol_data) >= 20:
        symbol_data['volume_ma'] = symbol_data['volume'].rolling(window=20, min_periods=1).mean()
        symbol_data['volume_anomaly'] = symbol_data['volume'] > (symbol_data['volume_ma'] * 3)
        anomaly_color = ['red' if x else '#1f77b4' for x in symbol_data['volume_anomaly']]
    else:
        anomaly_color = '#1f77b4'
    
    fig = go.Figure()
    
    # Add volume bars
    fig.add_trace(go.Bar(
        x=symbol_data['timestamp'],
        y=symbol_data['volume'],
        name=f'{symbol} Volume',
        marker_color=anomaly_color
    ))
    
    fig.update_layout(
        title=f"{symbol} Volume",
        xaxis_title="Time",
        yaxis_title="Volume",
        height=200,
        showlegend=False,
        template="plotly_dark"
    )
    
    return fig

def main():
    """Main dashboard function"""
    # Authentication check
    if not require_authentication():
        st.stop()
    
    # Title and header with user info
    col1, col2 = st.columns([3, 1])
    with col1:
        st.title("📊 Real-Time Crypto Market Dashboard")
    with col2:
        current_user = get_current_user()
        if current_user:
            st.markdown(f"**Welcome, {current_user}** 👤")
    
    st.markdown("---")
    
    # Sidebar controls
    st.sidebar.header("Dashboard Controls")
    hours_back = st.sidebar.slider("Hours of Data", 1, 72, 48)
    auto_refresh = st.sidebar.checkbox("Auto Refresh (60s)", value=True)
    
    # Security information
    st.sidebar.markdown("---")
    st.sidebar.markdown("### 🔒 Security Status")
    
    # Validate environment and show warnings
    warnings = validate_environment()
    if warnings:
        for warning in warnings:
            st.sidebar.warning(warning)
    else:
        st.sidebar.success("✅ Security configuration OK")
    
    # Show masked API key
    api_key = os.getenv('POLYGON_API_KEY', '')
    if api_key:
        masked_key = mask_api_key(api_key)
        st.sidebar.markdown(f"**API Key:** `{masked_key}`")
    else:
        st.sidebar.error("⚠️ No API key configured")
    
    # Session info is already rendered by require_authentication()
    
    # Load data
    with st.spinner("Loading market data..."):
        market_df = load_market_data(hours_back)
        anomaly_df = load_anomalies(hours_back)
    
    if market_df.empty:
        st.error("No market data available. Check if streaming is running.")
        return
    
    # Display key metrics
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric("Total Records", len(market_df))
    
    with col2:
        symbols = market_df['symbol'].nunique()
        st.metric("Active Symbols", symbols)
    
    with col3:
        if not anomaly_df.empty:
            recent_anomalies = len(anomaly_df[anomaly_df['start_time'] > datetime.now() - timedelta(hours=1)])
        else:
            recent_anomalies = 0
        st.metric("Anomalies (1h)", recent_anomalies)
    
    with col4:
        latest_time = market_df['timestamp'].max()
        time_ago = datetime.now() - latest_time
        st.metric("Last Update", f"{int(time_ago.total_seconds())}s ago")
    
    st.markdown("---")
    
    # Get unique symbols
    symbols = sorted(market_df['symbol'].unique())
    
    # Create charts for each symbol
    st.header("Live Price Charts")
    
    # Display in 2 columns
    for i in range(0, len(symbols), 2):
        col1, col2 = st.columns(2)
        
        with col1:
            if i < len(symbols):
                symbol = symbols[i]
                fig = create_price_chart(market_df, symbol)
                if fig:
                    st.plotly_chart(fig, use_container_width=True)
        
        with col2:
            if i + 1 < len(symbols):
                symbol = symbols[i + 1]
                fig = create_price_chart(market_df, symbol)
                if fig:
                    st.plotly_chart(fig, use_container_width=True)
    
    # Volume analysis section
    st.header("Volume Analysis")
    
    for i in range(0, len(symbols), 3):
        cols = st.columns(3)
        
        for j in range(3):
            if i + j < len(symbols):
                symbol = symbols[i + j]
                with cols[j]:
                    fig = create_volume_chart(market_df, symbol)
                    if fig:
                        st.plotly_chart(fig, use_container_width=True)
    
    # Anomaly alerts
    if not anomaly_df.empty:
        st.header("🚨 Recent Anomalies")
        
        # Show recent anomalies
        recent_anomalies = anomaly_df.head(10)
        
        for _, anomaly in recent_anomalies.iterrows():
            with st.container():
                cols = st.columns([1, 2, 2, 1])
                
                with cols[0]:
                    st.write(f"**{anomaly['symbol']}**")
                
                with cols[1]:
                    st.write(f"{anomaly['anomaly_type']}")
                
                with cols[2]:
                    if anomaly['multiplier']:
                        st.write(f"{anomaly['multiplier']:.2f}x normal")
                
                with cols[3]:
                    time_ago = datetime.now() - anomaly['start_time']
                    st.write(f"{int(time_ago.total_seconds() / 60)}m ago")
        
        st.markdown("---")
    
    # Data table
    with st.expander("Raw Data (Latest 50 records)"):
        st.dataframe(
            market_df.head(50)[['timestamp', 'symbol', 'price', 'volume', 'vwap', 'high', 'low']],
            use_container_width=True
        )
    
    # Auto-refresh functionality
    if auto_refresh:
        time.sleep(60)
        st.rerun()

if __name__ == "__main__":
    main()