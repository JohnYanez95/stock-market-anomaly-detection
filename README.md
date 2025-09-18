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
# Edit .env with your Polygon.io API key
```

### Quick Start

1. **Data Collection**:
```bash
# Activate virtual environment
source venv/bin/activate

# Collect sample data (AAPL, GOOGL, MSFT, TSLA, VOO)
python src/data/collect_data.py
```

2. **Feature Engineering**:
```bash
python src/features/build_features.py
```

3. **Model Training**:
```bash
python src/models/train_model.py
```

4. **Start API Server**:
```bash
uvicorn src.api.main:app --reload
```

5. **Launch Dashboard**:
```bash
streamlit run monitoring/dashboard.py
```

## Current Status

**✅ Completed (Week 1)**
- Environment setup with Python 3.10 virtual environment
- All dependencies installed (TensorFlow, scikit-learn, FastAPI, MLflow, Feast)
- Polygon.io API integration working
- Historical data collection implemented
- Sample dataset collected: 5 symbols, ~19,000 total records
- Data schema identified: OHLC prices, volume, VWAP, transaction counts

**📊 Available Data**
- **AAPL**: 3,762 minute-level records (Sep 11-17, 2025)
- **GOOGL**: 3,522 records
- **MSFT**: 3,120 records  
- **TSLA**: 4,700 records (highest volume)
- **VOO**: 2,574 records (ETF, lower frequency)

**🚧 Next Steps**
- Real-time WebSocket data streaming
- Feature engineering pipeline
- Anomaly detection model development

## Development Roadmap

### Week 1-2: Data Pipeline Foundation
- [x] Project setup and structure
- [x] Environment setup with virtual environment
- [x] Dependencies installed (ML, MLOps, API frameworks)
- [x] Polygon.io API integration
- [x] Historical data collection for AAPL, GOOGL, MSFT, TSLA, VOO
- [x] Data schema exploration (OHLC, volume, VWAP, transactions)
- [ ] WebSocket real-time connection
- [ ] Basic feature engineering

### Week 3-4: ML Pipeline
- [ ] Feast feature store setup
- [ ] Isolation Forest implementation
- [ ] LSTM Autoencoder development
- [ ] Backtesting framework

### Week 5-6: Production Systems
- [ ] MLflow experiment tracking
- [ ] Model registry and promotion
- [ ] FastAPI endpoint development
- [ ] Real-time dashboard

### Week 7-8: Polish & Interpretability
- [ ] SHAP implementation
- [ ] Historical validation
- [ ] Performance optimization
- [ ] Documentation and blog post

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