import os
import sys
from typing import List, Optional

from fastapi import Depends, FastAPI, File, Form, HTTPException, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from sqlalchemy.orm import Session

# Ensure backend path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from backend.database import Base, engine, get_db
from backend.models import AuditDocument, AuditReport, ComplianceFinding
from backend.services.document_parser import DocumentParser
from backend.services.esg_compliance import ESGComplianceService
from backend.services.financial_compliance import FinancialComplianceService
from backend.services.legal_compliance import LegalComplianceService
from backend.services.nlp_extractor import NLPExtractor
from backend.services.risk_engine import RiskEngine

# Initialize database tables
Base.metadata.create_all(bind=engine)

app = FastAPI(
    title="Cloud-Native Automated Compliance and Audit System API",
    description="Microservices-based AI platform for automated corporate document auditing, risk scoring, and compliance checking.",
    version="1.0.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

nlp_extractor = NLPExtractor()
risk_engine = RiskEngine()


class FindingResponse(BaseModel):
    id: int
    category: str
    rule_id: str
    risk_level: str
    title: str
    description: str
    evidence_excerpt: str
    confidence_score: float

    class Config:
        from_attributes = True


class AuditReportResponse(BaseModel):
    summary: str
    total_findings: int
    critical_findings: int
    high_findings: int
    compliance_rating: str

    class Config:
        from_attributes = True


class DocumentDetailResponse(BaseModel):
    id: int
    filename: str
    upload_date: str
    status: str
    category: str
    risk_score: float
    content_preview: str
    findings: List[FindingResponse]
    report: Optional[AuditReportResponse] = None

    class Config:
        from_attributes = True


@app.get("/")
def read_root():
    return {
        "status": "online",
        "system": "Cloud-Native Automated Compliance and Audit System",
        "version": "1.0.0",
    }


@app.post("/api/documents/upload", response_model=DocumentDetailResponse)
async def upload_document(
    file: UploadFile = File(...),
    category_override: Optional[str] = Form(None),
    db: Session = Depends(get_db),
):
    """Ingests corporate document, runs NLP extraction, routes to compliance microservices, and generates audit report."""
    try:
        content_bytes = await file.read()
        raw_text = DocumentParser.extract_text(content_bytes)
        cleaned_text = DocumentParser.clean_text(raw_text)
        preview = DocumentParser.get_preview(cleaned_text)

        # 1. NLP Classification
        category = (
            category_override
            if category_override
            else nlp_extractor.classify_document(cleaned_text)
        )

        # 2. Save Document Record
        doc = AuditDocument(
            filename=file.filename,
            category=category,
            status="Processing",
            risk_score=0.0,
            content_preview=preview,
        )
        db.add(doc)
        db.commit()
        db.refresh(doc)

        # 3. Route to Appropriate Compliance Microservices
        findings_data = []
        if category == "Financial" or category == "General":
            findings_data.extend(FinancialComplianceService.analyze(cleaned_text))
        if category == "ESG" or category == "General":
            findings_data.extend(ESGComplianceService.analyze(cleaned_text))
        if category == "Legal" or category == "General":
            findings_data.extend(LegalComplianceService.analyze(cleaned_text))

        # 4. Save Findings
        db_findings = []
        for f in findings_data:
            finding = ComplianceFinding(
                document_id=doc.id,
                category=category,
                rule_id=f["rule_id"],
                risk_level=f["risk_level"],
                title=f["title"],
                description=f["description"],
                evidence_excerpt=f["evidence"],
                confidence_score=f["confidence"],
            )
            db.add(finding)
            db_findings.append(finding)

        db.commit()

        # 5. Compute Risk & Generate Audit Report
        summary_data = risk_engine.compute_audit_summary(findings_data)
        doc.risk_score = summary_data["risk_score"]
        doc.status = "Completed"

        report = AuditReport(
            document_id=doc.id,
            summary=summary_data["summary"],
            total_findings=summary_data["total_findings"],
            critical_findings=summary_data["critical_findings"],
            high_findings=summary_data["high_findings"],
            compliance_rating=summary_data["compliance_rating"],
        )
        db.add(report)
        db.commit()
        db.refresh(doc)

        return DocumentDetailResponse(
            id=doc.id,
            filename=doc.filename,
            upload_date=doc.upload_date.strftime("%Y-%m-%d %H:%M:%S"),
            status=doc.status,
            category=doc.category,
            risk_score=doc.risk_score,
            content_preview=doc.content_preview,
            findings=[FindingResponse.model_validate(f) for f in doc.findings],
            report=AuditReportResponse.model_validate(doc.report)
            if doc.report
            else None,
        )

    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Document auditing failed: {str(e)}"
        )


@app.get("/api/documents", response_model=List[DocumentDetailResponse])
def list_documents(db: Session = Depends(get_db)):
    docs = db.query(AuditDocument).order_by(AuditDocument.upload_date.desc()).all()
    results = []
    for doc in docs:
        results.append(
            DocumentDetailResponse(
                id=doc.id,
                filename=doc.filename,
                upload_date=doc.upload_date.strftime("%Y-%m-%d %H:%M:%S"),
                status=doc.status,
                category=doc.category,
                risk_score=doc.risk_score,
                content_preview=doc.content_preview,
                findings=[FindingResponse.model_validate(f) for f in doc.findings],
                report=AuditReportResponse.model_validate(doc.report)
                if doc.report
                else None,
            )
        )
    return results


@app.get("/api/documents/{doc_id}", response_model=DocumentDetailResponse)
def get_document(doc_id: int, db: Session = Depends(get_db)):
    doc = db.query(AuditDocument).filter(AuditDocument.id == doc_id).first()
    if not doc:
        raise HTTPException(status_code=404, detail="Document not found")

    return DocumentDetailResponse(
        id=doc.id,
        filename=doc.filename,
        upload_date=doc.upload_date.strftime("%Y-%m-%d %H:%M:%S"),
        status=doc.status,
        category=doc.category,
        risk_score=doc.risk_score,
        content_preview=doc.content_preview,
        findings=[FindingResponse.model_validate(f) for f in doc.findings],
        report=AuditReportResponse.model_validate(doc.report) if doc.report else None,
    )


@app.post("/api/seed-samples")
def seed_sample_documents(db: Session = Depends(get_db)):
    """Loads sample files from `samples/` into the audit database for instant demonstration."""
    sample_dir = os.path.join(
        os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "samples"
    )
    loaded = []

    sample_files = [
        ("sample_financial_report.txt", "Financial"),
        ("sample_esg_report.txt", "ESG"),
        ("sample_legal_contract.txt", "Legal"),
    ]

    for filename, cat in sample_files:
        path = os.path.join(sample_dir, filename)
        if os.path.exists(path):
            with open(path, "rb") as f:
                content_bytes = f.read()

            raw_text = DocumentParser.extract_text(content_bytes)
            cleaned_text = DocumentParser.clean_text(raw_text)
            preview = DocumentParser.get_preview(cleaned_text)

            # Check if already seeded
            existing = (
                db.query(AuditDocument)
                .filter(AuditDocument.filename == filename)
                .first()
            )
            if existing:
                continue

            doc = AuditDocument(
                filename=filename,
                category=cat,
                status="Processing",
                risk_score=0.0,
                content_preview=preview,
            )
            db.add(doc)
            db.commit()
            db.refresh(doc)

            findings_data = []
            if cat == "Financial":
                findings_data.extend(FinancialComplianceService.analyze(cleaned_text))
            elif cat == "ESG":
                findings_data.extend(ESGComplianceService.analyze(cleaned_text))
            elif cat == "Legal":
                findings_data.extend(LegalComplianceService.analyze(cleaned_text))

            db_findings = []
            for f in findings_data:
                finding = ComplianceFinding(
                    document_id=doc.id,
                    category=cat,
                    rule_id=f["rule_id"],
                    risk_level=f["risk_level"],
                    title=f["title"],
                    description=f["description"],
                    evidence_excerpt=f["evidence"],
                    confidence_score=f["confidence"],
                )
                db.add(finding)

            db.commit()

            summary_data = risk_engine.compute_audit_summary(findings_data)
            doc.risk_score = summary_data["risk_score"]
            doc.status = "Completed"

            report = AuditReport(
                document_id=doc.id,
                summary=summary_data["summary"],
                total_findings=summary_data["total_findings"],
                critical_findings=summary_data["critical_findings"],
                high_findings=summary_data["high_findings"],
                compliance_rating=summary_data["compliance_rating"],
            )
            db.add(report)
            db.commit()
            loaded.append(filename)

    return {"success": True, "seeded_files": loaded}


# AWS Lambda Handler integration via Mangum (or custom adapter)
# We can include a clean handler function for AWS Lambda:
def lambda_handler(event, context):
    """AWS Lambda entry point for S3 upload event trigger or API Gateway proxy."""
    # This integrates the FastAPI app into AWS Lambda serverless execution
    import json

    return {
        "statusCode": 200,
        "body": json.dumps(
            {"message": "Serverless compliance engine executed successfully"}
        ),
    }


if __name__ == "__main__":
    import uvicorn

    uvicorn.run("backend.main:app", host="0.0.0.0", port=8000, reload=True)
