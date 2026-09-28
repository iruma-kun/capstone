class LegalComplianceService:
    """Checks legal documents and contracts for regulatory, liability, and jurisdiction clauses."""

    @staticmethod
    def analyze(text: str) -> list:
        findings = []
        text_lower = text.lower()

        # Check 1: Missing Governing Law / Jurisdiction
        if "governing law" not in text_lower and "jurisdiction" not in text_lower:
            findings.append(
                {
                    "rule_id": "LEG-001",
                    "risk_level": "Critical",
                    "title": "Missing Governing Law & Jurisdiction Clause",
                    "description": "Contract does not specify which jurisdiction's laws govern disputes, creating significant legal exposure.",
                    "evidence": "No mention of governing law or jurisdiction found in agreement.",
                    "confidence": 0.97,
                }
            )

        # Check 2: Unlimited Liability Risk
        if (
            "limitation of liability" not in text_lower
            and "liability cap" not in text_lower
        ):
            findings.append(
                {
                    "rule_id": "LEG-002",
                    "risk_level": "High",
                    "title": "Absent Limitation of Liability Clause",
                    "description": "The contract fails to cap potential damages, exposing the organization to unlimited financial liability.",
                    "evidence": "Zero mentions of liability caps or limitation clauses.",
                    "confidence": 0.93,
                }
            )

        # Check 3: Missing Data Privacy / GDPR Clause
        if (
            "confidential" in text_lower
            and "gdpr" not in text_lower
            and "data privacy" not in text_lower
        ):
            findings.append(
                {
                    "rule_id": "LEG-003",
                    "risk_level": "Medium",
                    "title": "Missing Data Privacy / GDPR Protection Clause",
                    "description": "Document deals with confidential information or records but lacks modern data privacy and GDPR compliance terms.",
                    "evidence": "References to confidentiality without privacy/GDPR provisions.",
                    "confidence": 0.85,
                }
            )

        return findings
