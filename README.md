# Stock Market Anomaly Detection Pipeline

Real-time anomaly detection system for stock market data with production-grade MLOps infrastructure.

## Project Overview

This project implements a complete anomaly detection pipeline for stock market data, featuring:

- Real-time data ingestion from Polygon.io API
- Feature store implementation with Feast
- ML models: Isolation Forest and LSTM Autoencoder
- MLflow for experiment tracking and model registry
- FastAPI serving with Redis caching
- SHAP-based interpretability
- Real-time monitoring dashboard

## Tech Stack

- **Data Source**: Polygon.io API (WebSocket + REST)
- **Feature Store**: Feast
- **ML Framework**: scikit-learn, TensorFlow/Keras
- **MLOps**: MLflow
- **API**: FastAPI
- **Caching**: Redis
- **Monitoring**: Streamlit
- **Interpretability**: SHAP

## Project Structure

```
├── data/
│   ├── raw/          # Raw market data
│   ├── processed/    # Cleaned and preprocessed data
│   └── features/     # Feature store data
├── src/
│   ├── data/         # Data ingestion and processing
│   ├── features/     # Feature engineering
│   ├── models/       # ML models and training
│   └── api/          # FastAPI application
├── notebooks/
│   └── exploration/  # Data exploration and analysis
├── configs/          # Configuration files
├── tests/           # Unit and integration tests
├── deployment/      # Docker and Kubernetes configs
│   ├── docker/
│   └── kubernetes/
├── monitoring/      # Monitoring and alerting
└── docs/           # Documentation
    ├── daily-reviews/  # Daily progress reviews
    └── time-invested/  # Time tracking and productivity metrics
```

## Getting Started

### Prerequisites

- **Python 3.10+** (tested with 3.10.12)
- **Polygon.io API key** (free tier: 10,000 calls/month)
- **Git** for version control
- Redis server (for future caching implementation)
- Docker (optional, for containerized deployment)

### Installation

1. Clone the repository:
```bash
git clone https://github.com/JohnYanez95/stock-market-anomaly-detection.git
cd stock-market-anomaly-detection
```

2. Create virtual environment and install dependencies:
```bash
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install -r requirements.txt

# Install MLOps packages separately (due to dependency conflicts)
pip install mlflow feast
```

3. Set up environment variables:
```bash
cp .env.example .env
# Edit .env with your Polygon.io API key and subscription tiers
```

**Environment Configuration**:
```bash
# Required: Your Polygon.io API key
POLYGON_API_KEY=your_api_key_here

# Per-asset subscription tiers (basic, starter, developer, advanced)
# WebSocket requires at least 'starter' tier for each asset type
POLYGON_TIER_STOCKS=starter     # Enable for WebSocket access
POLYGON_TIER_CRYPTO=starter     # Real-time WebSocket (24/7)
POLYGON_TIER_INDICES=basic      # Basic = no WebSocket
POLYGON_TIER_FOREX=basic        # Basic = no WebSocket
POLYGON_TIER_OPTIONS=basic      # Basic = no WebSocket
```

### Quick Start

1. **Data Collection**:
```bash
# Activate virtual environment
source venv/bin/activate

# Collect sample data (AAPL, GOOGL, MSFT, TSLA, VOO)
python src/data/collect_data.py
```

2. **Data Schema Analysis**:
```bash
# Comprehensive analysis of collected data
python notebooks/exploration/data_schema_analysis.py
```

3. **Real-Time Streaming** (requires Polygon.io Starter plans):
```bash
# Test WebSocket configuration
python configs/websocket_config.py

# Stream stocks (market hours, 15-min delayed)
python src/data/stream_stocks.py

# Stream crypto (24/7, real-time)
python src/data/stream_crypto.py

# Or run both simultaneously in separate terminals
python src/data/stream_orchestrator.py
```

4. **Real-Time Dashboard** (launch during market hours for live data):
```bash
# Launch interactive dashboard with live streaming data
streamlit run monitoring/dashboard.py
```

5. **Feature Engineering**:
```bash
python src/features/build_features.py
```

6. **Model Training**:
```bash
python src/models/train_model.py
```

7. **Start API Server**:
```bash
uvicorn src.api.main:app --reload
```

## Real-Time Streaming

### WebSocket Configuration

The project supports real-time data streaming from multiple asset types with individual subscription management:

**Supported Asset Types**:
- **Stocks** (NYSE, NASDAQ)
- **Crypto** (Bitcoin, Ethereum, etc.)
- **Forex** (Currency pairs)
- **Indices** (S&P 500, NASDAQ, etc.)
- **Options** (Equity options)
- **Futures** (Commodity and financial futures)

**Subscription Requirements**:
- **Basic Tier** (Free): REST API only, no WebSocket access
- **Starter Tier** (Stocks: $29/month, Currencies: $49/month): WebSocket streaming (stocks=15min delayed, currencies=real-time)
- **Developer Tier** ($79/month per asset): Real-time WebSocket streaming
- **Advanced Tier** ($199/month per asset): Real-time + additional features

### Configuration Examples

**Current Setup** (Stocks + Crypto):
```bash
POLYGON_TIER_STOCKS=starter     # $29/month - 15-min delayed streaming
POLYGON_TIER_CRYPTO=starter     # $49/month - real-time crypto streaming
POLYGON_TIER_INDICES=basic      # REST API only
POLYGON_TIER_FOREX=basic        # REST API only
```

**Future Multi-Asset Setup**:
```bash
POLYGON_TIER_STOCKS=starter     # $29/month - 15-min delayed streaming
POLYGON_TIER_CRYPTO=starter     # $49/month - real-time crypto streaming
POLYGON_TIER_FOREX=starter      # $49/month - real-time forex (included with crypto)
POLYGON_TIER_OPTIONS=developer  # $79/month - real-time options
```

**Testing Your Configuration**:
```bash
# Check what's available with your current subscriptions
python configs/websocket_config.py

# Test individual streams
python src/data/stream_stocks.py  # Stocks only
python src/data/stream_crypto.py  # Crypto only

# Test multi-stream orchestration
python src/data/stream_orchestrator.py --assets stocks crypto
```

### Live Anomaly Detection

Currently implemented anomaly detection:
- **Volume Spikes**: Detects when trading volume exceeds 3x the recent average
- **Real-time Alerts**: Immediate notification when anomalies are detected
- **Multi-symbol Monitoring**: Simultaneously track multiple assets

Example output during market hours:
```
📊 AAPL: $245.09, Vol: 1,097 at 14:32:15
🚨 ANOMALY: volume_spike in AAPL - 9.46x normal
📊 TSLA: $425.30, Vol: 4,441 at 14:32:30
🚨 ANOMALY: volume_spike in TSLA - 3.78x normal
```

### Multi-Stream Architecture

The system supports concurrent streaming from multiple asset classes using Polygon's cluster architecture:

**Key Features**:
- **One connection per asset type** - Stocks, crypto, forex, etc. on separate WebSocket connections
- **Process isolation** - Each stream runs independently for maximum reliability
- **Unified monitoring** - All streams can be viewed in a single dashboard
- **24/7 crypto + Market hours stocks** - Different schedules handled automatically

**Running Multiple Streams**:
```bash
# Option 1: Manual (separate terminals)
Terminal 1: python src/data/stream_stocks.py
Terminal 2: python src/data/stream_crypto.py

# Option 2: Orchestrated (single command)
python src/data/stream_orchestrator.py

# Option 3: Future Docker approach (coming soon)
docker run -p 8501:8501 stock-crypto-dashboard
```

## Current Status

**✅ Phase 1: Foundation COMPLETE** (11.5 hours across 4 sessions)
- Environment setup with Python 3.10 virtual environment
- All dependencies installed (TensorFlow, scikit-learn, FastAPI, MLflow, Feast, Streamlit)
- Polygon.io API integration working with Starter tier subscriptions
- **Real-time WebSocket streaming implemented** with modular configuration
- **SQLite database integration** with thread-safe operations and time-series optimization
- **Multi-asset streaming support**: Concurrent streams for stocks and crypto
- **Live anomaly detection**: Volume spike detection working in real-time

**✅ Phase 2: Real-Time Dashboard COMPLETE** (September 22, 2025)
- **Streamlit Dashboard**: Interactive real-time crypto market dashboard
- **Live Price Charts**: Real-time visualization for all 6 crypto symbols
- **Volume Analysis**: Anomaly detection with visual highlighting
- **Auto-Refresh**: 60-second automatic updates with live database queries
- **Multi-Asset Layout**: Professional dashboard showing all symbols simultaneously
- **Historical Data Integration**: Rich time-series charts with 9 days of data

**📊 Current Database & Data Status**
- **Total Records**: 64,900 minute-level records
- **Crypto Assets**: 6 symbols (BTC-USD, ETH-USD, ADA-USD, SOL-USD, DOT-USD, DOGE-USD)
- **Data Coverage**: September 14-22, 2025 (9 days of historical data)
- **Granularity**: Minute-level OHLC data with volume and VWAP
- **Data Quality**: No duplicates, comprehensive coverage, validated timestamps

**Symbol-Level Coverage**:
- **ADA-USD**: 11,518 records | **BTC-USD**: 10,917 records | **DOGE-USD**: 10,532 records
- **DOT-USD**: 10,213 records | **ETH-USD**: 11,123 records | **SOL-USD**: 10,597 records

**🔄 Historical Data Backfill System**
- **Modular Backfill Script**: Automatic tier detection and rate limiting
- **Subscription-Aware**: Adjusts behavior based on Polygon.io subscription tier
- **Duplicate Prevention**: Robust UPSERT logic prevents data duplication
- **Progress Tracking**: Real-time progress monitoring for long-running backfills
- **Smart Defaults**: Automatic date range selection based on subscription limits

**🎯 Active Features**
- **Dashboard Access**: `streamlit run monitoring/dashboard.py` → http://localhost:8501
- **Live Streaming**: Real-time crypto data (24/7) with volume anomaly detection
- **Historical Backfill**: `python src/data/backfill_historical.py` for data collection
- **Database Persistence**: All market data and anomalies stored in SQLite
- **Multi-Stream Architecture**: Concurrent WebSocket connections with unified storage

**🚧 Next Steps (Phase 3)**
- Enhanced anomaly detection algorithms (price movements, correlation breaks)
- Docker containerization for single-command deployment
- TimescaleDB migration for production-scale time-series operations
- Feature engineering pipeline for ML model development

## Development Philosophy

This project follows an **interconnected CI/CD approach** where each component builds upon and enhances the others, with anomaly detection serving as our foundation for market behavior profiling and trading signal generation:

```mermaid
graph TB
    subgraph "Data Ingestion Layer"
        A[Historical Data Collection] --> B[Real-time WebSocket Stream]
        B --> C[Data Quality Validation]
    end
    
    subgraph "Market Anomaly Detection System"
        C --> D[Volume Anomaly Detection]
        C --> E[Price Movement Detection]
        C --> F[Volatility Spike Detection]
        C --> G[Cross-Asset Correlation Breaks]
        
        D --> H[Anomaly Pattern Database]
        E --> H
        F --> H
        G --> H
    end
    
    subgraph "Real-time Analytics Pipeline"
        H --> I[Pattern Recognition Engine]
        I --> J[Market Regime Classification]
        J --> K[Risk Assessment Model]
        K --> L[Signal Generation]
    end
    
    subgraph "Visualization & Feedback Loop"
        L --> M[Real-time Dashboard]
        M --> N[Anomaly Alerts & Flags]
        N --> O[Performance Metrics]
        O --> P[Strategy Validation]
    end
    
    subgraph "Decision Making System"
        P --> Q[Paper Trading Simulation]
        Q --> R[Strategy Performance Analysis]
        R --> S[Risk-Adjusted Position Sizing]
        S --> T[Automated Trading Decisions]
    end
    
    subgraph "Continuous Improvement Loop"
        T --> U[Trade Outcome Analysis]
        U --> V[Model Retraining]
        V --> W[Algorithm Enhancement]
        W --> I
        
        N --> X[Manual Pattern Verification]
        X --> Y[Supervised Learning Labels]
        Y --> V
    end
    
    style D fill:#ff9999
    style E fill:#ff9999
    style F fill:#ff9999
    style G fill:#ff9999
    style H fill:#ffcc99
    style I fill:#99ccff
    style M fill:#99ff99
    style Q fill:#ffff99
```

**🔄 The Interconnected CI/CD Flow:**

1. **Anomaly Detection as Foundation** → Unusual market patterns become labeled data for behavior profiling
2. **Real-time Dashboard** → Immediate visual feedback drives algorithm enhancement  
3. **Advanced Analytics** → Pattern recognition engine learns from observed anomalies
4. **Paper Trading** → Decision system validates strategies based on anomaly patterns
5. **Continuous Learning** → Trade outcomes and manual verification improve anomaly detection

**Why This Approach Works:**
- **Anomaly-Driven Learning**: Each detected anomaly becomes training data for trading signal generation
- **Visual Debugging**: Dashboard provides immediate feedback for algorithm refinement
- **Risk-First Development**: Test with paper trading before real capital deployment
- **Continuous Model Improvement**: Performance feedback loops enhance anomaly detection
- **Market Behavior Profiling**: Build a database of market anomalies and their trading contexts

This mirrors how trading firms build robust systems - starting with anomaly detection, adding visualization for human oversight, then gradually automating decision-making based on validated trading signals.

## Development Roadmap

### Phase 1: Foundation (Week 1-2) ✅
- [x] Project setup and structure
- [x] Environment setup with virtual environment
- [x] Dependencies installed (ML, MLOps, API frameworks)
- [x] Polygon.io API integration
- [x] Historical data collection for AAPL, GOOGL, MSFT, TSLA, VOO
- [x] **Data schema comprehensive analysis**
  - [x] Field definitions (OHLC, volume, VWAP, transactions)
  - [x] Volatility analysis and calculation methodology
  - [x] Volume spike detection and patterns
  - [x] Cross-asset correlation analysis
  - [x] Data quality validation
  - [x] API limits and streaming capabilities assessment
- [x] **WebSocket real-time connection**
  - [x] Modular configuration system for per-asset subscriptions
  - [x] Multi-asset support (stocks, crypto, forex, indices, options, futures)
  - [x] Real-time data streaming with 15-minute delay (stocks)
  - [x] Live volume anomaly detection (3x threshold)
- [x] **Multi-stream architecture**
  - [x] Separate streaming scripts for stocks and crypto
  - [x] Process-based orchestration for concurrent streams
  - [x] Crypto subscription with real-time 24/7 data
- [x] **Database integration (SQLite)**
  - [x] Thread-safe operations for concurrent streams
  - [x] Time-series optimized schema
  - [x] Market data and anomaly persistence
### Phase 2: Real-Time Dashboard (Week 2) 🚧 Current Focus
- [ ] **Basic Streamlit dashboard**
  - [ ] Live price charts and volume visualization
  - [ ] Anomaly detection alerts and flags  
  - [ ] Multi-asset monitoring (stocks + crypto)
  - [ ] Simple file/SQLite storage
- [ ] **Enhanced anomaly detection**
  - [ ] Price movement anomalies
  - [ ] Volatility spike detection
  - [ ] Cross-asset correlation breaks

### Phase 3: Containerization (Week 3)
- [ ] **Docker containerization**
  - [ ] Multi-process management with supervisor
  - [ ] Unified container for stocks + crypto + dashboard
  - [ ] Single command deployment: `docker run -p 8501:8501`
  - [ ] Environment variable configuration
- [ ] **Process orchestration**
  - [ ] Health monitoring and auto-restart
  - [ ] Shared volume for data persistence
  - [ ] Logging aggregation

### Phase 4: Enhanced Dashboard + Real-Time Labeling (Week 4-5)
- [ ] **Migrate to TimescaleDB**
  - [ ] Time-series optimized storage
  - [ ] Fast aggregations for dashboard queries
  - [ ] Historical data retention policies
- [ ] **Real-time event labeling**
  - [ ] Click-to-mark event boundaries on charts
  - [ ] Dropdown menus for event classification
  - [ ] Store labeled events for ML training
  - [ ] Export training datasets
  - [ ] **Edge detection auto-refinement**: Auto-refine user-selected boundaries using volume/price edge detection
  - [ ] **Enterprise batch workflow**: Local Docker labeling → cloud storage sync for team collaboration
- [ ] **Advanced analytics**
  - [ ] Rolling correlations and cross-asset analysis
  - [ ] Technical indicators (RSI, MACD, Bollinger Bands)
  - [ ] Market regime detection

### Phase 5: ML Pipeline + Production Systems (Week 6-7)
- [ ] **ML model development**
  - [ ] Isolation Forest implementation
  - [ ] LSTM Autoencoder development
  - [ ] Training on labeled anomaly data
  - [ ] Backtesting framework
- [ ] **Production infrastructure**
  - [ ] MLflow experiment tracking
  - [ ] Model registry and versioning
  - [ ] FastAPI serving endpoints
  - [ ] Feast feature store
- [ ] **Paper trading simulation**
  - [ ] Strategy based on ML predictions
  - [ ] Portfolio management and risk controls
  - [ ] Performance tracking

### Phase 6: Advanced Strategies + Polish (Week 8)
- [ ] **Strategy enhancement**
  - [ ] Multi-asset arbitrage detection
  - [ ] Cross-market correlation trading
  - [ ] Risk-adjusted position sizing
- [ ] **Production polish**
  - [ ] SHAP implementation for interpretability
  - [ ] Performance optimization
  - [ ] Comprehensive documentation
  - [ ] Live demonstrations

## 🏗️ Future Architecture

### Containerized Multi-Stream Dashboard
The project will evolve into a Docker-based system with:
- **Single Container**: Runs stocks + crypto streams + dashboard
- **Process Management**: Supervisor manages all processes
- **One Command**: `docker run -p 8501:8501 stock-crypto-dashboard`
- **Web Access**: Dashboard available at `http://localhost:8501`

### TimescaleDB + Real-Time Labeling
- **Time-Series Optimization**: Fast queries across millions of data points
- **Event Labeling UI**: Click-to-mark anomalies for supervised learning
- **Training Data Generation**: Human-in-the-loop ML pipeline
- **PostgreSQL Compatible**: Full relational features for complex queries

### Enterprise Anomaly Labeling System
**Concept**: Hybrid local/cloud architecture for team-based anomaly labeling
- **Local Docker Processing**: Interactive labeling on powerful workstations
- **Edge Detection Auto-Refinement**: Algorithm tightens user-selected time boundaries
- **Batch Cloud Sync**: `docker run` → label locally → batch upsert to cloud storage
- **Cost Optimization**: No cloud compute costs during labeling sessions
- **Security**: Sensitive data stays local during human review process
- **Team Workflow**: SMEs label locally, results sync to shared cloud datasets

**Use Cases**: Financial anomaly detection, IoT sensor analysis, manufacturing quality control

```bash
# Enterprise workflow example
docker run your-labeler:latest --pull-from-cloud s3://data-bucket
docker run -p 8501:8501 your-labeler:latest --mode interactive  
docker run your-labeler:latest --push-to-cloud s3://labeled-data --upsert
```

## 📚 Documentation

**Daily Reviews**: Detailed session summaries in `docs/daily-reviews/`
- **[2025-09-18 Review](docs/daily-reviews/2025-09-18-review.md)**: Data schema exploration and analysis
- **[2025-09-19 Review](docs/daily-reviews/2025-09-19-review.md)**: WebSocket implementation and multi-stream architecture
- Key insights: Real-time streaming, per-asset subscriptions, concurrent WebSocket connections

**Time Investment**: Productivity tracking in `docs/time-invested/`
- **[Time Tracking Overview](docs/time-invested/README.md)**: Project timeline and efficiency metrics
- **[2025-09-18 Session](docs/time-invested/2025-09-18.md)**: 2.5 hours, data analysis focus
- **[2025-09-19 Session](docs/time-invested/2025-09-19.md)**: 3.0 hours, WebSocket implementation
- **Total Time**: 9.0+ hours across 4 sessions (September 21st session ongoing)

**Analysis Scripts**: 
- `notebooks/exploration/data_schema_analysis.py`: Comprehensive data analysis tool
- `src/data/collect_data.py`: Historical data collection from Polygon.io
- `src/data/stream_stocks.py`: Stock market WebSocket streaming (15-min delayed)
- `src/data/stream_crypto.py`: Cryptocurrency WebSocket streaming (real-time 24/7)
- `src/data/stream_orchestrator.py`: Multi-stream process orchestration
- `configs/websocket_config.py`: Multi-asset subscription configuration system

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests
5. Submit a pull request

## License

MIT License - see LICENSE file for details

## Contact

For questions or suggestions, please open an issue.