class ESGComplianceService:
    """Analyzes environmental and sustainability claims for greenwashing and disclosure gaps."""

    @staticmethod
    def analyze(text: str) -> list:
        findings = []
        text_lower = text.lower()

        # Check 1: Unverified Net-Zero Claims
        if "net-zero" in text_lower and "scope 3" not in text_lower:
            findings.append(
                {
                    "rule_id": "ESG-001",
                    "risk_level": "High",
                    "title": "Unverified Net-Zero Target (Missing Scope 3 Emissions)",
                    "description": "Company claims net-zero targets without disclosing required Scope 3 (supply chain) emissions data.",
                    "evidence": "Found 'net-zero' claim without accompanying Scope 3 carbon metrics.",
                    "confidence": 0.91,
                }
            )

        # Check 2: Vague Environmental Claims (Greenwashing Risk)
        vague_phrases = [
            "eco-friendly",
            "green initiative",
            "sustainable future",
            "planet positive",
        ]
        for phrase in vague_phrases:
            if (
                phrase in text_lower
                and "audited" not in text_lower
                and "metric" not in text_lower
            ):
                findings.append(
                    {
                        "rule_id": "ESG-002",
                        "risk_level": "Medium",
                        "title": f"Vague Environmental Claim ('{phrase}')",
                        "description": "General sustainability phrasing detected without quantitative verification metrics.",
                        "evidence": f"Found unquantified claim: '{phrase}'.",
                        "confidence": 0.78,
                    }
                )
                break

        # Check 3: Missing Governance / Diversity Policy Reference
        if "diversity" not in text_lower and "board oversight" not in text_lower:
            findings.append(
                {
                    "rule_id": "ESG-003",
                    "risk_level": "Low",
                    "title": "Missing Governance or Board Diversity Disclosure",
                    "description": "ESG report lacks reference to board oversight or workplace diversity metrics.",
                    "evidence": "Zero occurrences of governance or diversity policies.",
                    "confidence": 0.82,
                }
            )

        return findings
