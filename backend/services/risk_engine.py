class RiskEngine:
    """Calculates risk scores, severity counts, and generates executive audit summaries."""

    RISK_WEIGHTS = {"Critical": 10.0, "High": 7.0, "Medium": 4.0, "Low": 1.5}

    def compute_audit_summary(self, findings: list) -> dict:
        total = len(findings)
        critical_count = sum(1 for f in findings if f.get("risk_level") == "Critical")
        high_count = sum(1 for f in findings if f.get("risk_level") == "High")
        medium_count = sum(1 for f in findings if f.get("risk_level") == "Medium")
        low_count = sum(1 for f in findings if f.get("risk_level") == "Low")

        # Calculate weighted score (0 to 10 scale)
        if total == 0:
            score = 0.0
            rating = "Pass"
        else:
            raw_sum = sum(
                self.RISK_WEIGHTS.get(f.get("risk_level"), 2.0) for f in findings
            )
            score = round(min(10.0, raw_sum / max(1, total) * 1.5), 1)

            # Rating logic: Fail only if Critical findings OR score >= 8.0
            # Conditional if High findings OR score >= 5.0
            if critical_count > 0:
                rating = "Fail"
            elif high_count > 0:
                rating = "Conditional"
            elif score >= 8.0:
                rating = "Fail"
            elif score >= 5.0:
                rating = "Conditional"
            else:
                rating = "Pass"

        # Generate summary text
        summary = (
            f"Compliance audit completed. Evaluated {total} compliance rules. "
            f"Detected {critical_count} critical and {high_count} high-severity risks. "
            f"Overall Document Risk Score: {score}/10. Status: {rating}."
        )

        return {
            "risk_score": score,
            "total_findings": total,
            "critical_findings": critical_count,
            "high_findings": high_count,
            "medium_findings": medium_count,
            "low_findings": low_count,
            "compliance_rating": rating,
            "summary": summary,
        }
