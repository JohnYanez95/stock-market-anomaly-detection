# Polygon.io Condition Codes Research

## Overview
This document consolidates research on Polygon.io trade condition codes, focusing on crypto markets. Understanding these codes is crucial for accurate buy/sell pressure analysis.

## Observed Condition Codes

### From Our Live Data Collection

#### **Condition [1] - Frequent Pattern**
**Observed Behavior**:
```
💰 TRADE BTC-USD: $112244.3900 x 0.0005 | Conditions: [1]
💰 TRADE BTC-USD: $112244.3900 x 0.0007 | Conditions: [1]  
💰 TRADE BTC-USD: $112244.3900 x 0.0009 | Conditions: [1]
```

**Characteristics**:
- **Same price** across consecutive trades
- **Incremental sizes** (position building)
- **Most common** condition in our sample

**Hypothesis**: **Market Buy Order** (buyer initiated)
- Buyer "hits the ask"
- Aggressive buying behavior
- Positive price pressure indicator

#### **Condition [2] - Less Frequent Pattern**
**Observed Behavior**:
```
💰 TRADE BTC-USD: $112256.1000 x 0.0008 | Conditions: [2]
💰 TRADE BTC-USD: $112244.3800 x 0.0003 | Conditions: [2]
```

**Characteristics**:
- **Varying prices** across trades
- **Different sizing patterns**
- **Less frequent** than condition [1]

**Hypothesis**: **Market Sell Order** (seller initiated)
- Seller "hits the bid"
- Aggressive selling behavior
- Negative price pressure indicator

## Research Tasks

### Immediate Research Needed
- [ ] **Polygon.io official documentation** on crypto condition codes
- [ ] **Cross-reference with equity** condition codes for consistency
- [ ] **Statistical analysis** of condition frequency vs market direction
- [ ] **Price impact study** of different condition types

### Validation Experiments
- [ ] **Correlate conditions with price movements** over various timeframes
- [ ] **Compare condition ratios** during known buying/selling periods
- [ ] **Analyze condition patterns** around significant price moves
- [ ] **Test hypothesis** against multiple crypto symbols

## Industry Standard Condition Codes

### Typical Trade Condition Meanings
Based on general market data standards:

#### **Common Conditions**:
- **Regular Sale**: Normal market transaction
- **Market Buy**: Trade initiated by buyer (hits ask)
- **Market Sell**: Trade initiated by seller (hits bid)
- **Opening Trade**: First trade of trading session
- **Closing Trade**: Last trade of trading session
- **Block Trade**: Large institutional transaction
- **Odd Lot**: Trade size less than standard unit

#### **Crypto-Specific Considerations**:
- **24/7 trading**: No opening/closing concepts
- **Exchange routing**: Condition may indicate source exchange
- **Aggregation method**: How Polygon combines multi-exchange data
- **Settlement type**: Spot vs derivative instruments

## Working Hypotheses

### Primary Hypothesis
**Condition [1] = Buyer Initiated (Market Buy)**
**Condition [2] = Seller Initiated (Market Sell)**

**Supporting Evidence**:
1. **Price clustering**: [1] shows same-price clustering (hitting ask)
2. **Size progression**: [1] shows incremental position building
3. **Frequency difference**: [1] more common (typical in bull markets)
4. **Price variance**: [2] shows more price variation (hitting different bids)

**Validation Needed**:
- Correlation with price movements (expect [1] → up, [2] → down)
- Relationship to bid/ask spreads
- Behavior during volatile vs stable periods

### Alternative Hypotheses

#### **Hypothesis A: Exchange Source Indicator**
- **Condition [1]**: Coinbase trades
- **Condition [2]**: Binance trades  
- **Test**: Check if pattern holds across different symbols

#### **Hypothesis B: Trade Size Classification**
- **Condition [1]**: Standard trades
- **Condition [2]**: Large block trades
- **Test**: Analyze size distribution by condition

#### **Hypothesis C: Settlement Method**
- **Condition [1]**: Spot settlement
- **Condition [2]**: Derivative settlement  
- **Test**: Compare with known spot-only pairs

## Research Methodology

### Data Collection Strategy
1. **Extended sampling**: Collect 24-hour data samples
2. **Multi-symbol analysis**: Test across BTC, ETH, ADA, etc.
3. **Volatile period focus**: Capture data during known market movements
4. **Statistical significance**: Ensure adequate sample sizes

### Analysis Framework
1. **Condition frequency analysis**: Track [1] vs [2] ratios over time
2. **Price impact correlation**: Measure price changes following each condition
3. **Volume pattern analysis**: Compare trade sizes by condition
4. **Temporal clustering**: Look for condition timing patterns

### Validation Experiments
1. **Bull market test**: Higher [1] frequency expected
2. **Bear market test**: Higher [2] frequency expected  
3. **News event correlation**: Condition patterns around major announcements
4. **Cross-exchange validation**: Compare with other data providers

## Implementation Notes

### Interim Approach
Until official confirmation, implement configurable logic:
```python
def interpret_trade_condition(conditions):
    """Interpret trade conditions with fallback logic"""
    if 1 in conditions:
        return 'buy'  # Working hypothesis: buyer initiated
    elif 2 in conditions:
        return 'sell'  # Working hypothesis: seller initiated
    else:
        # Fallback: use price vs midpoint
        midpoint = (bid + ask) / 2
        return 'buy' if trade_price >= midpoint else 'sell'
```

### Validation Metrics
```python
def validate_condition_hypothesis(trades, price_movements):
    """Test condition interpretation accuracy"""
    buy_trades = [t for t in trades if 1 in t['conditions']]
    sell_trades = [t for t in trades if 2 in t['conditions']]
    
    # Measure price impact correlation
    buy_impact = correlate(buy_trades, subsequent_price_increases)
    sell_impact = correlate(sell_trades, subsequent_price_decreases)
    
    return {
        'buy_accuracy': buy_impact,
        'sell_accuracy': sell_impact,
        'confidence': (buy_impact + sell_impact) / 2
    }
```

## Contact Points for Research

### Official Sources
1. **Polygon.io Support**: Direct inquiry about condition codes
2. **Polygon.io Documentation**: API reference updates
3. **Developer Forum**: Community discussions on interpretations

### Industry Contacts  
1. **Crypto trading firms**: Validation of interpretation
2. **Market data vendors**: Cross-reference with other providers
3. **Academic researchers**: Market microstructure expertise

### Alternative Data Sources
1. **Direct exchange APIs**: Compare with Coinbase, Binance native data
2. **Other aggregators**: Cross-validate with CoinAPI, CryptoCompare
3. **Traditional finance**: Compare with equity market conditions

## Timeline for Resolution

### Week 1: Information Gathering
- [ ] Contact Polygon.io support
- [ ] Research online documentation
- [ ] Collect extended data samples
- [ ] Statistical analysis of patterns

### Week 2: Validation Testing
- [ ] Implement validation experiments  
- [ ] Cross-reference with market movements
- [ ] Test alternative hypotheses
- [ ] Document findings and confidence levels

### Implementation Decision
- **High confidence** (>80%): Proceed with hypothesis
- **Medium confidence** (60-80%): Implement with monitoring
- **Low confidence** (<60%): Use fallback price-based logic

---

*Condition Code Research - Created September 23, 2025*
*Status: Hypothesis phase, validation in progress*