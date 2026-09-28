# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [1.0.0] - 2026-09-28

### Added
- **Core NLP Engine**: Document classification, entity extraction, and clause identification
- **Financial Compliance Microservice**: Auditor disclosure checks, revenue recognition validation, liability detection
- **ESG Compliance Microservice**: Greenwashing detection, net-zero claim verification, governance disclosure checks
- **Legal Compliance Microservice**: Jurisdiction clause validation, liability cap detection, data privacy checks
- **Risk Scoring Engine**: Weighted risk calculation (Critical/High/Medium/Low) with 0-10 scoring
- **FastAPI Backend**: Async REST API with automatic OpenAPI documentation
- **React/Next.js Dashboard**: Real-time audit visualization with evidence traceability
- **AWS Serverless Architecture**: SAM template for S3-triggered Lambda processing pipeline
- **Sample Documents**: Financial, ESG, and Legal documents for immediate testing
- **Docker Support**: Multi-stage Dockerfile and docker-compose for containerized deployment
- **Database Models**: SQLAlchemy models for Documents, Findings, and Audit Reports

### Infrastructure
- SQLite for local development
- PostgreSQL-ready configuration for production
- CORS configuration for frontend integration
- Health check endpoints for container orchestration

## [Unreleased]

### Planned
- LLM Integration (Amazon Bedrock / OpenAI) for semantic rule evaluation
- OCR Support via Amazon Textract for scanned documents
- Real-time alerting via AWS SNS (Slack/Email)
- User authentication and RBAC (Role-Based Access Control)
- Multi-tenant support for consulting firms
- Compliance rule versioning and audit trail immutability
- Export to PDF/Word for formal audit reports
- CI/CD pipeline with GitHub Actions
