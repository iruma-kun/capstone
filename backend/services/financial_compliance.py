import re


class FinancialComplianceService:
    """Checks financial disclosures and flags potential accounting or disclosure anomalies."""

    @staticmethod
    def analyze(text: str) -> list:
        findings = []
        text_lower = text.lower()

        # Check 1: Missing Audited Statement Note
        if "audited" not in text_lower and "independent auditor" not in text_lower:
            findings.append(
                {
                    "rule_id": "FIN-001",
                    "risk_level": "High",
                    "title": "Missing Independent Auditor Disclosure",
                    "description": "The financial document does not contain required references to an independent auditor review or audit opinion.",
                    "evidence": text[:150] if len(text) > 150 else text,
                    "confidence": 0.89,
                }
            )

        # Check 2: Unverified Revenue Recognition Claims
        if (
            "unverified" in text_lower
            or "estimated revenue" in text_lower
            or "unaudited projections" in text_lower
        ):
            findings.append(
                {
                    "rule_id": "FIN-002",
                    "risk_level": "Medium",
                    "title": "Unaudited Financial Projections Flagged",
                    "description": "Document contains unaudited or estimated revenue figures which require formal reconciliation.",
                    "evidence": "Found estimated/unaudited revenue phrasing in disclosures.",
                    "confidence": 0.84,
                }
            )

        # Check 3: Missing Liability Disclosures
        # Look for positive liability mentions (not negated like "no liability" or "no liabilities")
        # First check if there are any liability-related words
        liability_mentions = re.findall(r"liabilit(?:y|ies)", text_lower)
        debt_mentions = re.findall(r"\bdebt\b", text_lower)

        # Check if mentions are negated (e.g., "no liability", "without liability", "zero liability")
        negated_liability = re.search(
            r"(?:no|zero|without|absence of|lack of)\s+(?:any\s+)?liabilit(?:y|ies)",
            text_lower,
        )
        negated_debt = re.search(
            r"(?:no|zero|without|absence of|lack of)\s+(?:any\s+)?debt", text_lower
        )

        has_positive_liability = (
            len(liability_mentions) > 0 and not negated_liability
        ) or (len(debt_mentions) > 0 and not negated_debt)

        if not has_positive_liability:
            findings.append(
                {
                    "rule_id": "FIN-003",
                    "risk_level": "Critical",
                    "title": "Complete Absence of Liability Disclosures",
                    "description": "No mention of liabilities or debt obligations found in financial filing.",
                    "evidence": "Document scan yielded zero positive mentions of liabilities.",
                    "confidence": 0.95,
                }
            )

        return findings
