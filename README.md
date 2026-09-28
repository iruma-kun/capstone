# Cloud-Native Automated Compliance and Audit System (CACA)

**Category:** Enterprise Software Engineering & Applied Artificial Intelligence  
**Project Type:** College Final Year Capstone Project  
**Status:** Functional Prototype (MVP)

---

## 🚀 Quick Start (Zero-Setup)

### Linux / macOS

```bash
git clone <your-repo-url>
cd Capstone
./setup_and_run.sh
```

### Windows (PowerShell)

```powershell
git clone <your-repo-url>
cd Capstone
.\setup_and_run.ps1
```

**That's it!** The script automatically:

1. ✅ Creates isolated `.venv` environment
2. ✅ Installs all Python & Node.js dependencies
3. ✅ Initializes SQLite database with schema
4. ✅ Seeds 3 sample compliance documents (Financial, ESG, Legal)
5. ✅ Starts FastAPI backend at **http://localhost:8000**
6. ✅ Starts Next.js frontend at **http://localhost:3000**
7. ✅ Opens API docs at **http://localhost:8000/docs**

Press `Ctrl+C` to stop all services cleanly.

---

## 1. Abstract

The **Cloud-Native Automated Compliance and Audit System (CACA)** is an AI-driven platform designed to automate the labor-intensive process of auditing corporate documents. By leveraging Natural Language Processing (NLP) and an event-driven cloud architecture, the system identifies regulatory risks, financial inconsistencies, and ESG (Environmental, Social, and Governance) gaps in real-time. This project demonstrates a scalable approach to "RegTech" (Regulatory Technology) by transforming unstructured data into actionable compliance intelligence.

## 2. Problem Statement

Enterprises spend millions of dollars annually on manual document auditing to ensure compliance with legal, financial, and sustainability standards. Manual audits are:

- **Error-Prone**: Human auditors can overlook critical clauses in 500+ page documents.
- **Inconsistent**: Different auditors may interpret risks differently.
- **Slow**: Processing a single corporate report can take days, delaying critical business decisions.

## 3. The Solution

CACA provides a centralized, automated pipeline for document auditing:

1. **Automated Ingestion**: Documents are uploaded to a secure cloud data lake (Amazon S3).
2. **Multi-Stage Processing**: An event-driven Lambda trigger routes text to specialized NLP microservices.
3. **Risk Intelligence**: The system analyzes text against Finance, ESG, and Legal rule-sets to flag anomalies.
4. **Explainable Reporting**: Every finding is backed by "Evidence Excerpts," ensuring transparency for human auditors.

---

## 4. System Architecture

```mermaid
graph TD
    subgraph "Client Layer"
        User([Compliance Officer])
        Dashboard[React/Next.js Dashboard]
    end

    subgraph "Ingestion Layer (AWS S3 & Lambda)"
        S3[(Amazon S3 Data Lake)]
        Lambda[AWS Lambda Trigger]
    end

    subgraph "Core Intelligence (FastAPI Microservices)"
        API[API Gateway / Controller]
        Parser[Text Extraction Engine]
        NLP[NLP Classification Service]
        RuleEngine[Compliance Rule Engine]
    end

    subgraph "Domain Microservices"
        Finance[Financial Auditor]
        ESG[ESG Auditor]
        Legal[Legal Auditor]
    end

    subgraph "Persistence & Reporting"
        DB[(PostgreSQL/SQLite)]
        ReportGen[Audit Report Generator]
    end

    User -- "1. Upload Doc" --> S3
    S3 -- "2. Event Trigger" --> Lambda
    Lambda -- "3. Process" --> API
    API --> Parser --> NLP --> RuleEngine
    RuleEngine --> Finance
    RuleEngine --> ESG
    RuleEngine --> Legal
    Finance & ESG & Legal -- "4. Findings" --> ReportGen
    ReportGen -- "5. Persist" --> DB
    Dashboard -- "6. View Results" --> API
```

---

## 5. Technical Implementation Details

### **A. Natural Language Processing (NLP)**

- **Rule-Based Extraction**: Uses complex Regex and keyword density analysis to categorize documents and identify standard clauses.
- **Entity Recognition**: Automatically identifies Organizations, Dates, and Monetary values to correlate financial data.
- **Classification Engine**: Routes documents to specialized domain-specific auditors (Financial vs. Legal) based on content analysis.

### **B. Backend Microservices**

- **FastAPI**: Used for high-performance, asynchronous API endpoints.
- **SQLAlchemy (ORM)**: Manages a relational schema tracking Audit Documents, Findings, and Summary Reports.
- **Risk Scoring Algorithm**: A weighted scoring engine that computes a 0-10 Risk Score based on the severity (Critical/High/Medium/Low) of detected violations.

### **C. Frontend Dashboard**

- **Next.js & Tailwind CSS**: A modern, responsive interface designed for Compliance Officers.
- **Audit Traceability**: Allows users to "click-to-view" the exact evidence in the source document where a risk was found.

---

## 6. Compliance Rules Implemented

| Domain    | Rule ID | Check                            | Severity |
| --------- | ------- | -------------------------------- | -------- |
| Financial | FIN-001 | Missing Independent Auditor      | High     |
| Financial | FIN-002 | Unverified Revenue Projections   | Medium   |
| Financial | FIN-003 | Missing Liability Disclosures    | Critical |
| ESG       | ESG-001 | Unverified Net-Zero (No Scope 3) | High     |
| ESG       | ESG-002 | Vague Environmental Claims       | Medium   |
| ESG       | ESG-003 | Missing Governance Disclosure    | Low      |
| Legal     | LEG-001 | Missing Jurisdiction Clause      | Critical |
| Legal     | LEG-002 | Unlimited Liability              | High     |
| Legal     | LEG-003 | Missing Data Privacy/GDPR        | Medium   |

---

## 7. Future Work & Scalability

- **LLM Integration**: Replacing Regex-based rules with Large Language Models (e.g., GPT-4 or Claude via Amazon Bedrock) for deeper semantic understanding.
- **OCR (Optical Character Recognition)**: Integrating Amazon Textract to process scanned PDFs and handwritten notes.
- **Real-time Alerting**: Integrating AWS SNS (Simple Notification Service) to send Slack or Email alerts for 'Critical' compliance failures.
- **Blockchain for Immutability**: Storing the audit hash on a private ledger to ensure audit trails cannot be tampered with.

---

## 8. Manual Development Setup

If you prefer manual setup:

```bash
# Backend
python -m venv .venv
source .venv/bin/activate
pip install -r backend/requirements.txt
python -m uvicorn backend.main:app --reload

# Frontend (separate terminal)
cd frontend
npm install
npm run dev
```

### API Endpoints

| Method | Endpoint                | Description                   |
| ------ | ----------------------- | ----------------------------- |
| POST   | `/api/documents/upload` | Upload document for audit     |
| GET    | `/api/documents`        | List all audited documents    |
| GET    | `/api/documents/{id}`   | Get detailed audit report     |
| POST   | `/api/seed-samples`     | Load sample documents         |
| GET    | `/docs`                 | Interactive API documentation |

---

## 9. Project Structure

```
Capstone/
├── backend/                 # FastAPI Microservices
│   ├── main.py              # REST API endpoints
│   ├── models.py            # SQLAlchemy models
│   ├── database.py          # Database configuration
│   └── services/            # Compliance microservices
│       ├── document_parser.py
│       ├── nlp_extractor.py
│       ├── financial_compliance.py
│       ├── esg_compliance.py
│       ├── legal_compliance.py
│       └── risk_engine.py
├── frontend/                # Next.js Dashboard
│   └── pages/index.js       # Main dashboard
├── serverless/              # AWS SAM Template
│   ├── template.yaml
│   └── s3_trigger_handler.py
├── samples/                 # Test documents
├── tests/                   # Unit tests (12 passing)
├── .venv/                   # Auto-created isolated env
├── setup_and_run.sh         # Linux/macOS launcher
├── setup_and_run.ps1        # Windows launcher
├── Dockerfile               # Container support
├── docker-compose.yml       # Multi-service stack
└── Makefile                 # Dev commands
```

---

## 10. License

MIT License - see [LICENSE](LICENSE) for details.
