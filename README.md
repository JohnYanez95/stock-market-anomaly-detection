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

- Python 3.9+
- Polygon.io API key (free tier)
- Redis server
- Docker (optional)

### Installation

1. Clone the repository:
```bash
git clone https://github.com/YOUR_USERNAME/stock-market-anomaly-detection.git
cd stock-market-anomaly-detection
```

2. Install dependencies:
```bash
pip install -r requirements.txt
```

3. Set up environment variables:
```bash
cp .env.example .env
# Edit .env with your API keys
```

### Quick Start

1. **Data Collection**:
```bash
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

## Development Roadmap

### Week 1-2: Data Pipeline Foundation
- [x] Project setup and structure
- [ ] Polygon.io API integration
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