# Data Aggregation Strategies for Crypto Market Microstructure

## Overview
This document analyzes different approaches to aggregating high-frequency crypto trade and quote data into meaningful analytical units. Based on our test results showing 845+ messages in 30 seconds, we need efficient aggregation strategies for both real-time analysis and historical storage.

## Current Data Volume Analysis

### Observed Message Rates
**Test Results** (30-second sample):
- **Total messages**: 845
- **Rate**: ~28 messages/second
- **Types**: Trades (XT), Quotes (XQ), Aggregates (XA)
- **Peak periods**: Higher during active trading

**Extrapolated Daily Volume**:
- **Per hour**: ~100,800 messages
- **Per day**: ~2.4 million messages  
- **Storage implications**: Significant for raw storage

### Message Type Distribution (Estimated)
- **Quotes (XQ)**: ~80% of messages (frequent bid/ask updates)
- **Trades (XT)**: ~15% of messages (actual transactions)
- **Aggregates (XA)**: ~5% of messages (minute summaries)

## Aggregation Strategies

### Strategy 1: Second-Level Aggregation
**Time Window**: 1-second buckets

#### **Advantages**:
- **High resolution** for scalping and high-frequency analysis
- **Preserves rapid market movements** and volatility spikes
- **Detailed order flow analysis** possible
- **Real-time responsiveness** for algorithmic trading

#### **Disadvantages**:
- **Massive data volume** (~2.4M records/day)
- **Storage overhead** significant
- **Processing complexity** higher
- **May be noisy** for longer-term analysis

#### **Use Cases**:
- High-frequency trading algorithms
- Scalping strategies (seconds to minutes)
- Market microstructure research
- Real-time anomaly detection

#### **Sample Aggregated Data**:
```json
{
  "timestamp": "2025-09-23T19:15:01.000Z",
  "symbol": "BTC-USD",
  "period": "1s",
  "trades": {
    "count": 3,
    "volume": 0.0021,
    "buy_volume": 0.0016,  // Condition [1] total
    "sell_volume": 0.0005, // Condition [2] total  
    "vwap": 112244.39,
    "price_range": [112244.38, 112256.10]
  },
  "quotes": {
    "updates": 12,
    "final_bid": 112237.90,
    "final_ask": 112238.70,
    "avg_spread": 1.15,
    "min_spread": 0.80,
    "max_spread": 2.10
  }
}
```

### Strategy 2: Minute-Level Aggregation (Recommended)
**Time Window**: 1-minute buckets

#### **Advantages**:
- **Manageable data volume** (~1,440 records/day/symbol)
- **Industry standard** for most trading analysis
- **Good balance** of detail vs performance
- **Compatible** with existing OHLC data structure
- **Efficient storage** and querying

#### **Disadvantages**:
- **Less granular** than second-level
- **May miss short-term patterns**
- **Smooths out rapid movements**

#### **Use Cases**:
- Day trading strategies (minutes to hours)
- Swing trading analysis  
- Technical indicator calculations
- Anomaly detection for sustained movements
- Integration with existing minute-bar systems

#### **Sample Aggregated Data**:
```json
{
  "timestamp": "2025-09-23T19:15:00.000Z",
  "symbol": "BTC-USD", 
  "period": "1m",
  "ohlc": {
    "open": 112240.00,
    "high": 112260.85,
    "low": 112235.50,
    "close": 112244.39
  },
  "volume": {
    "total": 0.0847,
    "buy_volume": 0.0521,     // Total Condition [1] volume
    "sell_volume": 0.0326,    // Total Condition [2] volume  
    "buy_sell_ratio": 1.60,   // Buy/sell pressure indicator
    "trade_count": 89,
    "buy_trade_count": 54,
    "sell_trade_count": 35
  },
  "spread_analysis": {
    "avg_spread": 1.85,
    "min_spread": 0.80,
    "max_spread": 13.00,
    "spread_volatility": 2.34
  },
  "liquidity_indicators": {
    "quote_updates": 342,
    "spread_stability": 0.73,  // 0-1, higher = more stable
    "price_impact": 0.0012     // Avg price change per trade
  }
}
```

### Strategy 3: Multi-Timeframe Aggregation
**Approach**: Calculate multiple timeframes simultaneously

#### **Implementation**:
- **Real-time**: 1-second for immediate analysis
- **Short-term**: 5-second for rapid pattern detection  
- **Standard**: 1-minute for regular analysis
- **Storage**: Only store 1-minute+ for historical data

#### **Advantages**:
- **Flexibility** for different analysis needs
- **Real-time responsiveness** with efficient storage
- **Multi-scale analysis** possible

#### **Disadvantages**:  
- **Complex implementation**
- **Higher computational overhead**
- **Memory requirements** for multiple buffers

## Recommended Architecture

### Phase 1: Minute-Level Foundation
**Rationale**: Start with proven, manageable approach

```
Raw Messages (28/sec) → 1-Minute Aggregation → Database Storage
                     ↓
              Real-time Dashboard Updates
```

**Benefits**:
- **Immediate implementation** possible
- **Manageable complexity**
- **Industry-standard approach**
- **Easy integration** with existing minute-bar system

### Phase 2: Enhanced Analysis (Future)
**Add second-level analysis for specific use cases**

```
Raw Messages → 1-Second Buffer → 1-Minute Aggregation → Storage
             ↓
          Real-time Alerts (Sub-minute anomalies)
```

## Aggregation Metrics Design

### Core Metrics (Must Have)
1. **OHLC prices** (standard candle data)
2. **Volume breakdown** (buy vs sell volume)
3. **Trade counts** (buy vs sell initiated)
4. **Spread analysis** (liquidity indicators)

### Advanced Metrics (Nice to Have)
1. **Price impact analysis** (trade size vs price movement)
2. **Order flow imbalance** (buy pressure - sell pressure)  
3. **Liquidity stability** (spread consistency)
4. **Trade size distribution** (retail vs institutional patterns)

### Derived Indicators
1. **Buy/Sell Pressure Ratio**: `buy_volume / sell_volume`
2. **Aggressor Ratio**: `buy_trades / total_trades`
3. **Spread Volatility**: Standard deviation of spreads
4. **Liquidity Score**: Function of spread and update frequency

## Implementation Considerations

### Database Schema Extension
```sql
-- Extend existing market_data table
ALTER TABLE market_data ADD COLUMN buy_volume REAL;
ALTER TABLE market_data ADD COLUMN sell_volume REAL;
ALTER TABLE market_data ADD COLUMN buy_trade_count INTEGER;
ALTER TABLE market_data ADD COLUMN sell_trade_count INTEGER;
ALTER TABLE market_data ADD COLUMN avg_spread REAL;
ALTER TABLE market_data ADD COLUMN spread_volatility REAL;
ALTER TABLE market_data ADD COLUMN quote_updates INTEGER;
```

### Real-time Processing Pipeline
1. **Message Router**: Separate trades, quotes, aggregates
2. **Time Window Manager**: Group messages by minute
3. **Aggregation Calculator**: Compute metrics for each window
4. **Database Writer**: Store aggregated results
5. **Dashboard Updater**: Push real-time updates

### Performance Considerations
- **Memory buffers** for current minute data
- **Batch inserts** for database efficiency
- **Async processing** to handle message rate
- **Data compression** for historical storage

## Migration Strategy

### Phase 1: Add Buy/Sell to Current System
- **Extend database schema** with buy/sell fields  
- **Update aggregation logic** in existing minute bars
- **Add buy/sell indicators** to dashboard charts
- **Test with current XA (aggregate) data**

### Phase 2: Implement Full Microstructure Collection  
- **Build trade/quote collection system**
- **Implement minute-level aggregation**
- **Replace XA data** with our calculated aggregates
- **Add advanced buy/sell pressure indicators**

### Phase 3: Real-time Analysis Enhancement
- **Add second-level analysis** for specific alerts
- **Implement order flow anomaly detection**  
- **Build liquidity-based trading signals**
- **Advanced market microstructure analytics**

## Success Metrics

### Data Quality Metrics
- **Message capture rate** > 99%
- **Aggregation accuracy** vs known patterns
- **Storage efficiency** (compression ratio)
- **Query performance** (sub-second response)

### Analysis Quality Metrics  
- **Buy/sell pressure accuracy** vs price movements
- **Liquidity indicators** correlation with volatility
- **Anomaly detection** precision and recall
- **Trading signal** performance metrics

---

*Data Aggregation Strategy Document - Created September 23, 2025*