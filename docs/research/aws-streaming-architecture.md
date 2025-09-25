# AWS Streaming Architecture Setup Guide

## Overview

This guide provides a comprehensive walkthrough for establishing a production-grade AWS infrastructure for 24/7 crypto market data streaming, designed for data scientists building end-to-end systems similar to SentiLink's architecture.

## Table of Contents

1. [Architecture Overview](#architecture-overview)
2. [AWS Account Setup](#aws-account-setup)
3. [Core Infrastructure](#core-infrastructure)
4. [Database Configuration](#database-configuration)
5. [Security Setup](#security-setup)
6. [Deployment Process](#deployment-process)
7. [Monitoring & Alerts](#monitoring--alerts)
8. [Cost Management](#cost-management)
9. [Career Development Value](#career-development-value)
10. [Next Steps](#next-steps)

---

## Architecture Overview

### System Design
```
Development Machine (Local)
    ↓ Query via PostgreSQL connection
AWS Cloud Infrastructure
├── EC2 Instance (t3.medium)
│   ├── Docker Container
│   │   ├── Crypto WebSocket Streams
│   │   ├── Stock WebSocket Streams
│   │   └── Data Processing Pipeline
│   └── TimescaleDB (PostgreSQL)
├── S3 Bucket
│   ├── Raw data backup
│   └── Model artifacts
└── CloudWatch
    ├── Logs
    └── Metrics & Alarms
```

### Data Flow
```
Polygon.io WebSocket → EC2 Processing → TimescaleDB → Development Machine
                           ↓
                      S3 Backup (hourly)
```

---

## AWS Account Setup

### Initial Configuration
1. **Create AWS Account**
   ```bash
   # Sign up at aws.amazon.com
   # Enable MFA for root account immediately
   # Create IAM user for daily operations
   ```

2. **Install AWS CLI**
   ```bash
   # Windows/Mac/Linux
   pip install awscli
   
   # Configure credentials
   aws configure
   # Enter: Access Key ID, Secret Access Key, Region (us-east-1), Output (json)
   ```

3. **Set Budget Alerts**
   ```bash
   # Navigate to AWS Billing Console
   # Create budget: $75/month (50% above expected)
   # Set AGGRESSIVE alerts at: $30, $40, $50, $60, $75
   # This catches cost overruns early
   ```

### Free Tier Optimization
```
First 12 months includes:
├── 750 hours EC2 t2.micro (use for testing)
├── 5GB S3 storage
├── 1M Lambda requests
└── CloudWatch: 10 metrics, 1M API requests
```

---

## Core Infrastructure

### EC2 Instance Setup

#### 1. FREE TIER Testing Phase (Weeks 1-2)
```
EC2 Dashboard → Launch Instance
├── Name: "crypto-streaming-test"
├── AMI: Ubuntu Server 22.04 LTS
├── Instance Type: t2.micro (FREE TIER - 1 vCPU, 1GB RAM)
├── Key Pair: Create new → "crypto-streaming-key"
├── Network: Default VPC
├── Security Group: Create new (see Security Setup)
├── Storage: 30GB GP3 SSD (free tier)
└── Tags: Environment=Testing, Project=CryptoStreaming

Use this to:
- Test all configurations
- Verify database connections
- Validate streaming setup
- Save $15-20 in first month
```

#### 2. Production Instance (After Testing)
```
Upgrade to t3.medium when ready for 24/7 operation:
├── Stop t2.micro instance
├── Change instance type to t3.medium
├── Increase storage to 100GB
└── Update tags: Environment=Production
```

#### 2. Initial Server Configuration
```bash
# SSH into instance
ssh -i crypto-streaming-key.pem ubuntu@<public-ip>

# Update system
sudo apt update && sudo apt upgrade -y

# Install Docker
curl -fsSL https://get.docker.com -o get-docker.sh
sudo sh get-docker.sh
sudo usermod -aG docker ubuntu

# Install Docker Compose
sudo apt install docker-compose -y

# Setup project directory
mkdir -p /opt/crypto-streaming/{data,logs,config}
cd /opt/crypto-streaming
```

#### 3. Elastic IP (Static Address)
```
EC2 Console → Elastic IPs → Allocate
├── Associate with streaming instance
└── Note: Free while associated, $0.005/hour if not
```

### S3 Bucket Configuration

```bash
# Create bucket via CLI
aws s3 mb s3://crypto-streaming-data-<unique-suffix>

# Enable versioning (data protection)
aws s3api put-bucket-versioning \
  --bucket crypto-streaming-data-<unique-suffix> \
  --versioning-configuration Status=Enabled

# Setup lifecycle policy for cost optimization
cat > lifecycle.json << EOF
{
  "Rules": [{
    "Id": "ArchiveOldData",
    "Status": "Enabled",
    "Transitions": [{
      "Days": 30,
      "StorageClass": "GLACIER_IR"
    }]
  }]
}
EOF

aws s3api put-bucket-lifecycle-configuration \
  --bucket crypto-streaming-data-<unique-suffix> \
  --lifecycle-configuration file://lifecycle.json
```

---

## Database Configuration

### Option 1: Self-Managed TimescaleDB on EC2 (Recommended for Learning)

```bash
# Install PostgreSQL + TimescaleDB
sudo apt install postgresql postgresql-contrib -y
sudo sh -c "echo 'deb https://packagecloud.io/timescale/timescaledb/ubuntu/ $(lsb_release -c -s) main' > /etc/apt/sources.list.d/timescaledb.list"
wget --quiet -O - https://packagecloud.io/timescale/timescaledb/gpgkey | sudo apt-key add -
sudo apt update
sudo apt install timescaledb-2-postgresql-14 -y

# Configure PostgreSQL
sudo -u postgres psql << EOF
CREATE DATABASE crypto_streams;
CREATE USER streaming_user WITH ENCRYPTED PASSWORD 'your-secure-password';
GRANT ALL PRIVILEGES ON DATABASE crypto_streams TO streaming_user;
EOF

# Enable TimescaleDB
sudo -u postgres psql -d crypto_streams -c "CREATE EXTENSION IF NOT EXISTS timescaledb;"

# Create ML-focused schema for anomaly detection
sudo -u postgres psql -d crypto_streams << EOF
-- Enhanced schema for anomaly detection features
CREATE TABLE market_microstructure (
    timestamp TIMESTAMPTZ NOT NULL,
    symbol TEXT NOT NULL,
    price NUMERIC NOT NULL,
    volume NUMERIC NOT NULL,
    buy_volume NUMERIC,              -- For order flow analysis
    sell_volume NUMERIC,             -- For order flow analysis
    bid_price NUMERIC,               -- Best bid
    ask_price NUMERIC,               -- Best ask
    bid_ask_spread NUMERIC,          -- Liquidity metric
    order_imbalance NUMERIC,         -- (buy_vol - sell_vol) / total_vol
    volatility_1min NUMERIC,         -- Rolling volatility
    volume_spike_score NUMERIC,      -- Pre-calculated anomaly score
    price_change_pct NUMERIC,        -- % change from previous minute
    rsi_14 NUMERIC,                  -- Technical indicator
    PRIMARY KEY (timestamp, symbol)
);

-- Convert to TimescaleDB hypertable for performance
SELECT create_hypertable('market_microstructure', 'timestamp');

-- Create indexes for ML queries
CREATE INDEX idx_symbol_time ON market_microstructure (symbol, timestamp DESC);
CREATE INDEX idx_anomaly_scores ON market_microstructure (volume_spike_score) 
  WHERE volume_spike_score > 3;
EOF

# Configure remote access
sudo nano /etc/postgresql/14/main/postgresql.conf
# Set: listen_addresses = '*'

sudo nano /etc/postgresql/14/main/pg_hba.conf
# Add: host all all 0.0.0.0/0 md5 (temporary for testing)

sudo systemctl restart postgresql
```

### Option 2: AWS RDS (Managed Service)

```bash
# Create RDS instance via CLI
aws rds create-db-instance \
  --db-instance-identifier crypto-streaming-db \
  --db-instance-class db.t3.micro \
  --engine postgres \
  --engine-version 14.6 \
  --master-username dbadmin \
  --master-user-password your-secure-password \
  --allocated-storage 20 \
  --vpc-security-group-ids sg-your-security-group \
  --backup-retention-period 7 \
  --preferred-backup-window "03:00-04:00" \
  --preferred-maintenance-window "sun:04:00-sun:05:00"
```

---

## Security Setup

### Security Group Configuration

#### Progressive Security Approach

**Week 1: Development Setup**
```bash
# Create security group
aws ec2 create-security-group \
  --group-name crypto-streaming-sg \
  --description "Security group for crypto streaming server"

# SSH from your IP only (immediate)
aws ec2 authorize-security-group-ingress \
  --group-name crypto-streaming-sg \
  --protocol tcp \
  --port 22 \
  --cidr YOUR.IP.ADDRESS.HERE/32

# PostgreSQL from your IP (for initial testing)
aws ec2 authorize-security-group-ingress \
  --group-name crypto-streaming-sg \
  --protocol tcp \
  --port 5432 \
  --cidr YOUR.IP.ADDRESS.HERE/32
```

**Week 2: Enhanced Security**
```bash
# Option A: VPN Setup (more secure)
# Install OpenVPN or WireGuard on EC2
# Connect via VPN for all access

# Option B: Bastion Host
# Create t2.micro bastion in public subnet
# Access streaming server through bastion
```

**Month 2: Production Security**
```bash
# Remove direct PostgreSQL access
aws ec2 revoke-security-group-ingress \
  --group-name crypto-streaming-sg \
  --protocol tcp \
  --port 5432 \
  --cidr YOUR.IP.ADDRESS.HERE/32

# Use AWS Systems Manager Session Manager
# No SSH needed - access through AWS Console
# Most secure option for production
```

### IAM Role for EC2

```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Action": [
        "s3:PutObject",
        "s3:GetObject",
        "s3:ListBucket"
      ],
      "Resource": [
        "arn:aws:s3:::crypto-streaming-data-*/*",
        "arn:aws:s3:::crypto-streaming-data-*"
      ]
    },
    {
      "Effect": "Allow",
      "Action": [
        "cloudwatch:PutMetricData",
        "logs:CreateLogStream",
        "logs:PutLogEvents"
      ],
      "Resource": "*"
    }
  ]
}
```

### Environment Variables

```bash
# Create .env file
cat > /opt/crypto-streaming/.env << EOF
# Polygon.io Configuration
POLYGON_API_KEY=your-polygon-key
POLYGON_TIER_CRYPTO=starter
POLYGON_TIER_STOCKS=starter

# Database Configuration  
DB_HOST=localhost
DB_PORT=5432
DB_NAME=crypto_streams
DB_USER=streaming_user
DB_PASS=your-secure-password

# AWS Configuration
AWS_REGION=us-east-1
S3_BUCKET=crypto-streaming-data-<unique-suffix>
EOF

# Secure the file
chmod 600 /opt/crypto-streaming/.env
```

---

## Deployment Process

### Docker Deployment

```dockerfile
# Create Dockerfile
cat > /opt/crypto-streaming/Dockerfile << 'EOF'
FROM python:3.10-slim

WORKDIR /app

# Install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application
COPY src/ ./src/
COPY monitoring/ ./monitoring/

# Environment
ENV PYTHONUNBUFFERED=1

# Run supervisor
CMD ["supervisord", "-c", "/app/supervisor.conf"]
EOF
```

### Docker Compose Configuration

```yaml
# docker-compose.yml
version: '3.8'

services:
  streaming:
    build: .
    container_name: crypto-streaming
    restart: unless-stopped
    environment:
      - DB_HOST=host.docker.internal
    env_file:
      - .env
    volumes:
      - ./data:/app/data
      - ./logs:/app/logs
    network_mode: host
    logging:
      driver: "json-file"
      options:
        max-size: "10m"
        max-file: "3"
```

### Automated Deployment Script

```bash
#!/bin/bash
# deploy.sh

# Pull latest code
git pull origin main

# Build and deploy
docker-compose down
docker-compose build
docker-compose up -d

# Check status
docker-compose ps
docker-compose logs --tail=50

# Backup database
pg_dump -h localhost -U streaming_user crypto_streams | \
  gzip | \
  aws s3 cp - s3://crypto-streaming-data-xxx/backups/$(date +%Y%m%d_%H%M%S).sql.gz
```

---

## Monitoring & Alerts

### CloudWatch Setup

```bash
# Install CloudWatch agent
wget https://s3.amazonaws.com/amazoncloudwatch-agent/ubuntu/amd64/latest/amazon-cloudwatch-agent.deb
sudo dpkg -i amazon-cloudwatch-agent.deb

# Configure metrics
cat > /opt/aws/amazon-cloudwatch-agent/etc/config.json << EOF
{
  "metrics": {
    "namespace": "CryptoStreaming",
    "metrics_collected": {
      "cpu": {
        "measurement": [
          "cpu_usage_idle",
          "cpu_usage_active"
        ],
        "metrics_collection_interval": 60
      },
      "disk": {
        "measurement": [
          "used_percent"
        ],
        "metrics_collection_interval": 60,
        "resources": [
          "*"
        ]
      },
      "mem": {
        "measurement": [
          "mem_used_percent"
        ],
        "metrics_collection_interval": 60
      }
    }
  }
}
EOF
```

### Critical Alerts

```python
# monitoring/cloudwatch_alarms.py
import boto3

cloudwatch = boto3.client('cloudwatch')

# High CPU alert
cloudwatch.put_metric_alarm(
    AlarmName='crypto-streaming-high-cpu',
    ComparisonOperator='GreaterThanThreshold',
    EvaluationPeriods=2,
    MetricName='CPUUtilization',
    Namespace='AWS/EC2',
    Period=300,
    Statistic='Average',
    Threshold=80.0,
    ActionsEnabled=True,
    AlarmActions=['arn:aws:sns:us-east-1:xxx:crypto-alerts'],
    AlarmDescription='Alert when CPU exceeds 80%'
)

# Disk space alert
cloudwatch.put_metric_alarm(
    AlarmName='crypto-streaming-disk-space',
    ComparisonOperator='GreaterThanThreshold',
    EvaluationPeriods=1,
    MetricName='disk_used_percent',
    Namespace='CryptoStreaming',
    Period=3600,
    Statistic='Average',
    Threshold=85.0
)

# Custom metrics from application
def send_metric(metric_name, value, unit='Count'):
    cloudwatch.put_metric_data(
        Namespace='CryptoStreaming',
        MetricData=[
            {
                'MetricName': metric_name,
                'Value': value,
                'Unit': unit
            }
        ]
    )
```

---

## Cost Management

### Monthly Cost Breakdown

```
Fixed Costs:
├── EC2 t3.medium (24/7): $30.37
├── EBS 100GB GP3: $8.00
├── Elastic IP: $0 (while attached)
└── Base Total: $38.37

Variable Costs:
├── Data Transfer: ~$2-5
├── S3 Storage: ~$1-3
├── CloudWatch: ~$1-2
├── Backups: ~$1-2
└── Variable Total: ~$5-12

Expected Monthly: $45-55
```

### Scaled Usage Scenarios

**Heavy Usage Projection (1TB+ data)**
```
Base Infrastructure:
├── EC2 t3.medium: $30.37
├── EBS 100GB: $8.00
└── Subtotal: $38.37

Scaled Storage & Transfer:
├── S3 Storage (1TB): $23/month
├── Data Transfer (50GB out/month): $4.50
├── CloudWatch Logs (heavy): $5-10
├── Database snapshots (daily): $5
└── Subtotal: $37.50-42.50

Total Heavy Usage: ~$75-80/month
```

**When costs typically increase:**
- Multiple years of tick-level data (rare)
- Multiple users querying constantly
- Storing raw JSON without compression
- Not implementing lifecycle policies

**Reality:** Your use case likely stays under $60/month for 6-12 months

### Cost Optimization Strategies

1. **Reserved Instances** (After 3 months stable)
   ```bash
   # 1-year commitment saves 30%
   # Monthly cost: $30.37 → $21.26
   ```

2. **S3 Intelligent Tiering**
   ```bash
   # Automatically moves old data to cheaper storage
   aws s3api put-bucket-intelligent-tiering-configuration \
     --bucket crypto-streaming-data-xxx \
     --id crypto-archive \
     --intelligent-tiering-configuration file://tiering.json
   ```

3. **Scheduled Scaling** (If not 24/7 needed)
   ```python
   # Stop instance during development
   import boto3
   ec2 = boto3.client('ec2')
   
   # Stop at night
   ec2.stop_instances(InstanceIds=['i-xxx'])
   
   # Start in morning
   ec2.start_instances(InstanceIds=['i-xxx'])
   ```

---

## Career Development Value

### Skills Demonstrated

1. **AWS Core Services**
   - EC2 instance management
   - S3 object storage
   - CloudWatch monitoring
   - IAM security

2. **Production Architecture**
   - High availability design
   - Cost optimization
   - Security best practices
   - Infrastructure as Code

3. **Data Engineering**
   - Real-time data pipelines
   - Time-series databases
   - ETL/ELT processes
   - Data lifecycle management

### Interview Talking Points

```
"I built a production AWS infrastructure for real-time financial data streaming:

• Designed end-to-end architecture processing 2M+ messages daily
• Implemented cost-optimized EC2/S3/CloudWatch stack ($50/month)
• Configured TimescaleDB for efficient time-series storage
• Automated deployments with Docker and monitoring alerts
• Achieved 99.9% uptime for 24/7 crypto market data collection

This demonstrates my ability to own data infrastructure end-to-end,
similar to the requirements at SentiLink."
```

### Resume Bullets
- Architected and deployed AWS-based real-time data streaming infrastructure processing 2M+ financial transactions daily
- Reduced infrastructure costs by 40% through Reserved Instances and S3 lifecycle policies
- Implemented automated monitoring and alerting using CloudWatch, achieving 99.9% uptime
- Built end-to-end data pipeline from WebSocket ingestion to PostgreSQL storage with S3 backups

---

## Next Steps

### Phase 0: Free Tier Testing (Week 1)
- [ ] Create AWS account and configure CLI
- [ ] Launch t2.micro instance (FREE TIER)
- [ ] Test basic setup and configurations
- [ ] Verify all connections work
- [ ] Document any issues before scaling up

### Phase 1: Production Setup (Week 2)
- [ ] Upgrade to t3.medium instance
- [ ] Install Docker and TimescaleDB
- [ ] Deploy streaming containers
- [ ] Configure ML-focused database schema
- [ ] Test anomaly detection queries

### Phase 2: Production Hardening (Week 2)
- [ ] Configure automated backups to S3
- [ ] Set up CloudWatch monitoring
- [ ] Implement log aggregation
- [ ] Create deployment automation
- [ ] Test disaster recovery

### Phase 3: Advanced Features (Week 3-4)
- [ ] Add auto-scaling policies
- [ ] Implement data archival strategies
- [ ] Set up CI/CD pipeline
- [ ] Add VPC and enhanced security
- [ ] Consider multi-region setup

### Learning Resources
1. **AWS Free Training**: https://aws.amazon.com/training/
2. **AWS Well-Architected Framework**: Essential reading
3. **PostgreSQL Performance**: https://www.postgresql.org/docs/
4. **Docker Best Practices**: Production-grade containerization

---

## Troubleshooting Common Issues

### Connection Issues
```bash
# Test PostgreSQL connection
psql -h <elastic-ip> -U streaming_user -d crypto_streams

# Check security groups
aws ec2 describe-security-groups --group-names crypto-streaming-sg

# Verify instance status
aws ec2 describe-instance-status --instance-ids i-xxx
```

### Performance Issues
```bash
# Check system resources
top
df -h
free -m

# PostgreSQL slow queries
sudo -u postgres psql -c "SELECT * FROM pg_stat_statements ORDER BY total_time DESC LIMIT 10;"

# Docker logs
docker-compose logs --tail=100 streaming
```

### Cost Overruns
```bash
# Check unexpected resources
aws ce get-cost-and-usage \
  --time-period Start=2024-01-01,End=2024-01-31 \
  --granularity DAILY \
  --metrics "UnblendedCost" \
  --group-by Type=DIMENSION,Key=SERVICE
```

---

## Conclusion

This AWS architecture provides a production-grade foundation for your crypto streaming system while building valuable cloud engineering skills. The setup balances cost-effectiveness ($45-55/month) with professional practices that directly translate to senior data science roles.

Key advantages:
- **24/7 reliability** without home infrastructure concerns
- **Scalable architecture** that grows with your needs
- **Industry-standard stack** matching job requirements
- **Hands-on learning** with real production systems

Start with Phase 1 basic setup, validate the architecture, then progressively add production features as you gain confidence with AWS services.