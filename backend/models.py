from sqlalchemy import Column, Integer, String, Float, DateTime, ForeignKey, Text
from sqlalchemy.orm import relationship
from datetime import datetime
from .database import Base

class AuditDocument(Base):
    __tablename__ = "audit_documents"

    id = Column(Integer, primary_key=True, index=True)
    filename = Column(String, index=True)
    upload_date = Column(DateTime, default=datetime.utcnow)
    status = Column(String, default="Processing")  # Processing, Completed, Failed
    category = Column(String)  # Financial, ESG, Legal, General
    risk_score = Column(Float, default=0.0)  # 0.0 to 10.0 (High Risk)
    content_preview = Column(Text)

    # Relationships
    findings = relationship("ComplianceFinding", back_populates="document", cascade="all, delete-orphan")
    report = relationship("AuditReport", back_populates="document", uselist=False, cascade="all, delete-orphan")

class ComplianceFinding(Base):
    __tablename__ = "compliance_findings"

    id = Column(Integer, primary_key=True, index=True)
    document_id = Column(Integer, ForeignKey("audit_documents.id"))
    category = Column(String)  # Finance, ESG, Legal
    rule_id = Column(String)
    risk_level = Column(String)  # Critical, High, Medium, Low
    title = Column(String)
    description = Column(Text)
    evidence_excerpt = Column(Text)  # The specific text found in the document
    confidence_score = Column(Float)

    # Relationships
    document = relationship("AuditDocument", back_populates="findings")

class AuditReport(Base):
    __tablename__ = "audit_reports"

    id = Column(Integer, primary_key=True, index=True)
    document_id = Column(Integer, ForeignKey("audit_documents.id"))
    generated_at = Column(DateTime, default=datetime.utcnow)
    summary = Column(Text)
    total_findings = Column(Integer, default=0)
    critical_findings = Column(Integer, default=0)
    high_findings = Column(Integer, default=0)
    compliance_rating = Column(String)  # Pass, Fail, Conditional

    # Relationships
    document = relationship("AuditDocument", back_populates="report")
