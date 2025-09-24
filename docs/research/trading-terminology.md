# Trading Terminology & Market Microstructure

## Overview
This document provides comprehensive definitions and analysis of key trading concepts observed in our crypto data streams from Polygon.io. Understanding these fundamentals is crucial for building effective buy/sell pressure analysis and aggregation strategies.

## Core Trading Concepts

### 1. **Trade**
**Definition**: A completed transaction where a buyer and seller agree on price and quantity.

**From Our Data**:
```
💰 TRADE BTC-USD: $112244.3900 x 0.0005 | Conditions: [1]
```

**Components**:
- **Symbol**: BTC-USD (Bitcoin to US Dollar)
- **Price**: $112,244.39 (execution price)
- **Size/Quantity**: 0.0005 BTC (amount traded)
- **Conditions**: [1] (trade type/direction indicator)
- **Timestamp**: When the trade occurred

**Key Insights**:
- Trades represent **actual money changing hands**
- **Price discovery mechanism** - shows where market participants actually transact
- **Volume impact** - larger trades have more market influence
- **Direction matters** - who initiated the trade (buyer vs seller)

### 2. **Quote**
**Definition**: Current best bid and ask prices available in the market (order book top level).

**From Our Data**:
```
📊 Quote BTC-USD: Bid $112237.9000 | Ask $112238.7000 | Spread: $0.8000
```

**Components**:
- **Bid**: $112,237.90 (highest price buyers are willing to pay)
- **Ask**: $112,238.70 (lowest price sellers are willing to accept)
- **Spread**: $0.80 (difference between ask and bid)

**Key Insights**:
- Quotes show **market intention**, trades show **market action**
- **Order book snapshot** - represents current supply/demand balance
- **Changes rapidly** - reflects real-time market sentiment
- **Liquidity indicator** - tight spreads = high liquidity

### 3. **Bid**
**Definition**: The highest price that buyers are currently willing to pay for an asset.

**Market Psychology**:
- Represents **demand side** of the market
- **Aggressive bids** (high prices) indicate buying pressure
- **Bid size** indicates depth of demand
- **Rising bids** suggest increasing buying interest

**Analysis Opportunities**:
- **Bid pressure**: How fast bids are increasing
- **Bid-trade relationship**: When trades occur at/near bid prices
- **Bid size analysis**: Large bids = institutional interest

### 4. **Ask**
**Definition**: The lowest price that sellers are currently willing to accept for an asset.

**Market Psychology**:
- Represents **supply side** of the market
- **Aggressive asks** (low prices) indicate selling pressure
- **Ask size** indicates depth of supply
- **Falling asks** suggest increasing selling interest

**Analysis Opportunities**:
- **Ask pressure**: How fast asks are decreasing
- **Ask-trade relationship**: When trades occur at/near ask prices
- **Ask size analysis**: Large asks = institutional selling

### 5. **Spread**
**Definition**: The difference between the best ask price and the best bid price.

**Formula**: `Spread = Ask Price - Bid Price`

**From Our Data Examples**:
- **Tight spread**: $0.8 (high liquidity, active market)
- **Wide spread**: $10+ (low liquidity, volatile conditions)

**Market Implications**:
- **Narrow spreads** (< $1): High liquidity, efficient price discovery
- **Wide spreads** (> $10): Low liquidity, high volatility, or market uncertainty
- **Changing spreads**: Market stress indicator

**Analysis Value**:
- **Liquidity measurement**
- **Transaction cost estimation**
- **Market stress detection**
- **Volatility prediction**

### 6. **Trade Conditions**
**Definition**: Codes indicating the nature, type, or circumstances of a trade.

**From Our Observations**:
- **Condition [1]**: Appears frequently, likely "market buy" orders
- **Condition [2]**: Less frequent, likely "market sell" orders

**Hypothesis Based on Patterns**:

#### **Condition [1] - Market Buy (Buyer Initiated)**
```
💰 TRADE BTC-USD: $112244.3900 x 0.0005 | Conditions: [1]
💰 TRADE BTC-USD: $112244.3900 x 0.0007 | Conditions: [1]  
💰 TRADE BTC-USD: $112244.3900 x 0.0009 | Conditions: [1]
```
**Characteristics**:
- **Same price across multiple trades** (hitting the same ask level)
- **Increasing sizes** (building position)
- **Likely interpretation**: Buyers "hitting the ask" (aggressive buying)

#### **Condition [2] - Market Sell (Seller Initiated)**  
```
💰 TRADE BTC-USD: $112256.1000 x 0.0008 | Conditions: [2]
💰 TRADE BTC-USD: $112244.3800 x 0.0003 | Conditions: [2]
```
**Characteristics**:
- **Varying prices** (hitting different bid levels)
- **Different behavior pattern**
- **Likely interpretation**: Sellers "hitting the bid" (aggressive selling)

**Research Needed**:
- **Polygon.io documentation** on specific condition codes
- **Cross-reference with price movements** to validate hypotheses
- **Statistical analysis** of condition patterns vs market direction

## Market Microstructure Concepts

### Order Flow Analysis
**Definition**: Study of how orders move through the market and impact prices.

**Components**:
1. **Trade direction** (buy vs sell initiated)
2. **Trade size distribution** (retail vs institutional)
3. **Trade timing patterns** (frequency, clustering)
4. **Price impact analysis** (how trades move prices)

### Buy/Sell Pressure Indicators

#### **Buy Pressure Signals**:
- High frequency of **Condition [1]** trades
- Trades executing **at or above ask prices**
- **Rising bid prices** in quotes
- **Decreasing spreads** with upward price movement
- **Large size trades** with condition [1]

#### **Sell Pressure Signals**:
- High frequency of **Condition [2]** trades  
- Trades executing **at or below bid prices**
- **Falling ask prices** in quotes
- **Increasing spreads** with downward price movement
- **Large size trades** with condition [2]

### Market Liquidity Indicators

#### **High Liquidity**:
- **Tight spreads** ($0.10 - $2.00 for BTC)
- **Frequent quotes updates**
- **Consistent bid/ask sizes**
- **Small price impact** from trades

#### **Low Liquidity**:
- **Wide spreads** ($5.00+ for BTC)
- **Infrequent quote updates**
- **Volatile bid/ask prices**
- **Large price impact** from trades

## Data Quality Observations

### Trade Data Characteristics
- **High frequency**: Multiple trades per second during active periods
- **Variable sizes**: From 0.0001 BTC (retail) to larger amounts
- **Consistent conditions**: Primarily [1] and [2] observed
- **Price precision**: 4 decimal places standard

### Quote Data Characteristics  
- **Ultra high frequency**: Quote updates multiple times per second
- **Tight spreads common**: $0.80 - $2.00 typical for BTC
- **Wide spreads during volatility**: Up to $13+ observed
- **Rapid changes**: Reflects active order book management

## Research Questions

### Immediate Research Needs
1. **What do Polygon.io condition codes [1], [2], etc. specifically mean?**
2. **How do other conditions (if any) affect our analysis?**
3. **What's the relationship between quote spreads and trade conditions?**
4. **How do trade sizes correlate with market impact?**

### Analysis Development Questions  
1. **Should we aggregate at 1-second, 5-second, or 1-minute intervals?**
2. **Which metrics are most predictive of price movements?**
3. **How do we weight different types of market data?**
4. **What's the optimal lookback window for buy/sell pressure calculation?**

### Implementation Considerations
1. **How do we handle data rate (800+ messages in 30 seconds)?**
2. **What aggregation strategy balances detail vs performance?**
3. **How do we store and query time-series microstructure data efficiently?**
4. **What real-time indicators provide actionable trading insights?**

## Next Steps

1. **Research Polygon.io condition codes** documentation
2. **Implement data collection** for quotes and trades
3. **Build aggregation pipeline** for minute-level summaries
4. **Create buy/sell pressure indicators** based on findings
5. **Validate indicators** against known market movements

---

*Research Foundation Document - Created September 23, 2025*