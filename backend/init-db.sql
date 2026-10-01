-- Cloud-Native Automated Compliance & Audit System (CACA)
-- PostgreSQL Initialization Script
-- Runs automatically on first container startup

-- Enable UUID extension
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- Create audit_documents table
CREATE TABLE IF NOT EXISTS audit_documents (
    id SERIAL PRIMARY KEY,
    filename VARCHAR(255) NOT NULL,
    upload_date TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    status VARCHAR(50) DEFAULT 'Processing',
    category VARCHAR(50),
    risk_score DECIMAL(3,1) DEFAULT 0.0,
    content_preview TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Create compliance_findings table
CREATE TABLE IF NOT EXISTS compliance_findings (
    id SERIAL PRIMARY KEY,
    document_id INTEGER NOT NULL REFERENCES audit_documents(id) ON DELETE CASCADE,
    category VARCHAR(50) NOT NULL,
    rule_id VARCHAR(20) NOT NULL,
    risk_level VARCHAR(20) NOT NULL,
    title VARCHAR(255) NOT NULL,
    description TEXT,
    evidence_excerpt TEXT,
    confidence_score DECIMAL(3,2),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Create audit_reports table
CREATE TABLE IF NOT EXISTS audit_reports (
    id SERIAL PRIMARY KEY,
    document_id INTEGER NOT NULL UNIQUE REFERENCES audit_documents(id) ON DELETE CASCADE,
    summary TEXT,
    total_findings INTEGER DEFAULT 0,
    critical_findings INTEGER DEFAULT 0,
    high_findings INTEGER DEFAULT 0,
    medium_findings INTEGER DEFAULT 0,
    low_findings INTEGER DEFAULT 0,
    compliance_rating VARCHAR(20),
    generated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Create indexes for performance
CREATE INDEX IF NOT EXISTS idx_audit_documents_category ON audit_documents(category);
CREATE INDEX IF NOT EXISTS idx_audit_documents_status ON audit_documents(status);
CREATE INDEX IF NOT EXISTS idx_audit_documents_upload_date ON audit_documents(upload_date DESC);
CREATE INDEX IF NOT EXISTS idx_compliance_findings_document_id ON compliance_findings(document_id);
CREATE INDEX IF NOT EXISTS idx_compliance_findings_risk_level ON compliance_findings(risk_level);
CREATE INDEX IF NOT EXISTS idx_compliance_findings_category ON compliance_findings(category);

-- Grant permissions
GRANT ALL PRIVILEGES ON ALL TABLES IN SCHEMA public TO compliance;
GRANT ALL PRIVILEGES ON ALL SEQUENCES IN SCHEMA public TO compliance;

-- Insert sample data version marker
CREATE TABLE IF NOT EXISTS schema_version (
    version INTEGER PRIMARY KEY,
    applied_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);
INSERT INTO schema_version (version) VALUES (1) ON CONFLICT DO NOTHING;
