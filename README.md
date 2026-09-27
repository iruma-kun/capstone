# Enterprise FinTech Intelligence & Autonomous Portfolio Manager

## Overview
A full-stack, cloud-deployed platform that predicts market trends and manages mock portfolios based on ESG scores and real-time news sentiment.

## Architecture

### Machine Learning Engine
- **Models**: LSTMs and RNNs for time-series forecasting.
- **NLP**: Sentiment analysis on financial news and reports.

### Backend
- **Language**: Python (FastAPI)
- **Logic**: Trading logic, API requests, portfolio management.
- **Database**: PostgreSQL (via AWS RDS).

### Frontend
- **Framework**: Next.js / Tailwind CSS
- **Features**: Real-time dashboard, portfolio visualization, rebalancing alerts.

### Infrastructure
- **Cloud**: AWS (S3, RDS, Lambda, VPC)
- **IaC**: Terraform or AWS CDK

## Project Structure
- `backend/`: API and trading logic.
- `frontend/`: User dashboard.
- `ml_engine/`: Model training and inference scripts.
- `infrastructure/`: Cloud infrastructure definitions.
- `data/`: Data ingestion and processing scripts.
