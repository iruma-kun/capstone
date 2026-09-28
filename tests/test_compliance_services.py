"""
Unit tests for Compliance Microservices
Run with: pytest tests/ -v
"""

import os
import sys

import pytest

# Add backend to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "backend"))

from backend.services.esg_compliance import ESGComplianceService
from backend.services.financial_compliance import FinancialComplianceService
from backend.services.legal_compliance import LegalComplianceService
from backend.services.nlp_extractor import NLPExtractor
from backend.services.risk_engine import RiskEngine


class TestFinancialCompliance:
    """Tests for Financial Compliance Service"""

    def test_missing_auditor_detection(self):
        text = "This report was prepared by internal finance team. No external auditor involved."
        findings = FinancialComplianceService.analyze(text)

        assert len(findings) > 0
        auditor_finding = next((f for f in findings if f["rule_id"] == "FIN-001"), None)
        assert auditor_finding is not None
        assert auditor_finding["risk_level"] == "High"

    def test_liability_absence_detection(self):
        text = "Revenue grew 10% this quarter. Profit margins improved."
        findings = FinancialComplianceService.analyze(text)

        liability_finding = next(
            (f for f in findings if f["rule_id"] == "FIN-003"), None
        )
        assert liability_finding is not None
        assert liability_finding["risk_level"] == "Critical"


class TestESGCompliance:
    """Tests for ESG Compliance Service"""

    def test_unverified_net_zero_detection(self):
        text = "We commit to net-zero by 2040. Our operations will be carbon neutral."
        findings = ESGComplianceService.analyze(text)

        net_zero_finding = next(
            (f for f in findings if f["rule_id"] == "ESG-001"), None
        )
        assert net_zero_finding is not None
        assert net_zero_finding["risk_level"] == "High"

    def test_vague_claims_detection(self):
        text = "We have an eco-friendly initiative for a sustainable future."
        findings = ESGComplianceService.analyze(text)

        vague_finding = next((f for f in findings if f["rule_id"] == "ESG-002"), None)
        assert vague_finding is not None
        assert vague_finding["risk_level"] == "Medium"


class TestLegalCompliance:
    """Tests for Legal Compliance Service"""

    def test_missing_jurisdiction_detection(self):
        text = "This agreement is between Party A and Party B. Confidentiality is required."
        findings = LegalComplianceService.analyze(text)

        jurisdiction_finding = next(
            (f for f in findings if f["rule_id"] == "LEG-001"), None
        )
        assert jurisdiction_finding is not None
        assert jurisdiction_finding["risk_level"] == "Critical"

    def test_unlimited_liability_detection(self):
        text = "Contract for services. Payment terms net 30. Confidential information shared."
        findings = LegalComplianceService.analyze(text)

        liability_finding = next(
            (f for f in findings if f["rule_id"] == "LEG-002"), None
        )
        assert liability_finding is not None
        assert liability_finding["risk_level"] == "High"


class TestRiskEngine:
    """Tests for Risk Scoring Engine"""

    def test_empty_findings(self):
        engine = RiskEngine()
        result = engine.compute_audit_summary([])

        assert result["risk_score"] == 0.0
        assert result["compliance_rating"] == "Pass"
        assert result["total_findings"] == 0

    def test_critical_findings_fail_rating(self):
        engine = RiskEngine()
        findings = [
            {"risk_level": "Critical", "rule_id": "TEST-001", "confidence": 0.9}
        ]
        result = engine.compute_audit_summary(findings)

        assert result["risk_score"] >= 7.0
        assert result["compliance_rating"] == "Fail"
        assert result["critical_findings"] == 1

    def test_high_findings_conditional_rating(self):
        engine = RiskEngine()
        findings = [
            {"risk_level": "High", "rule_id": "TEST-001", "confidence": 0.8},
            {"risk_level": "Medium", "rule_id": "TEST-002", "confidence": 0.7},
        ]
        result = engine.compute_audit_summary(findings)

        assert result["compliance_rating"] == "Conditional"
        assert result["high_findings"] == 1


class TestNLPExtractor:
    """Tests for NLP Extraction Service"""

    def test_document_classification(self):
        extractor = NLPExtractor()

        financial_text = (
            "Revenue profit EBITDA audited balance sheet cash flow equity liability"
        )
        assert extractor.classify_document(financial_text) == "Financial"

        esg_text = "Carbon emissions sustainability diversity governance net-zero environmental"
        assert extractor.classify_document(esg_text) == "ESG"

        legal_text = "Contract agreement jurisdiction indemnification warranty clause termination"
        assert extractor.classify_document(legal_text) == "Legal"

        general_text = "This is a general business document about operations."
        assert extractor.classify_document(general_text) == "General"

    def test_entity_extraction(self):
        extractor = NLPExtractor()
        text = "Apple Inc. reported $50 million revenue on Jan 15, 2024."
        entities = extractor.extract_entities(text)

        assert "Apple Inc." in entities["orgs"]
        assert "$50 million" in entities["currency"]
        assert "Jan 15, 2024" in entities["dates"]


class TestIntegration:
    """Integration tests for the full pipeline"""

    def test_financial_document_pipeline(self):
        """Test complete analysis of a financial document"""
        text = "ACME Corp Q3 Report. Prepared by internal team. Revenue $45M. No liability disclosures."

        # Classify
        extractor = NLPExtractor()
        category = extractor.classify_document(text)
        assert category == "Financial"

        # Analyze
        findings = FinancialComplianceService.analyze(text)
        assert len(findings) >= 2  # Should catch missing auditor and missing liability

        # Risk score
        engine = RiskEngine()
        result = engine.compute_audit_summary(findings)
        assert result["total_findings"] >= 2
        assert result["risk_score"] > 0


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
