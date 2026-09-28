import re


class NLPExtractor:
    """
    NLP Engine for entity extraction, clause identification, and document classification.
    """

    # Keyword sets for classification
    CLASSIFICATION_KEYWORDS = {
        "Financial": [
            "revenue",
            "profit",
            "ebitda",
            "audited",
            "balance sheet",
            "cash flow",
            "equity",
            "liability",
        ],
        "ESG": [
            "carbon",
            "sustainability",
            "emissions",
            "diversity",
            "environmental",
            "governance",
            "social",
            "net-zero",
        ],
        "Legal": [
            "contract",
            "agreement",
            "jurisdiction",
            "indemnification",
            "warranty",
            "clause",
            "termination",
            "liability",
        ],
    }

    def classify_document(self, text: str) -> str:
        """Categorizes document based on keyword density."""
        text_lower = text.lower()
        scores = {cat: 0 for cat in self.CLASSIFICATION_KEYWORDS}

        for cat, keywords in self.CLASSIFICATION_KEYWORDS.items():
            for word in keywords:
                scores[cat] += text_lower.count(word)

        # Determine winning category
        best_cat = max(scores, key=scores.get)
        if scores[best_cat] == 0:
            return "General"
        return best_cat

    def extract_entities(self, text: str) -> dict:
        """Extracts key entities like dates, currency, and company-like names using regex."""
        entities = {
            "dates": re.findall(
                r"\b\d{1,2}[/-]\d{1,2}[/-]\d{2,4}\b|\b(?:Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)[a-z]* \d{1,2},? \d{4}\b",
                text,
            ),
            "currency": re.findall(
                r"\$?\b[0-9]+(?:\.[0-9]+)?\s*(?:million|billion|thousand)\b|\$[0-9]{1,3}(?:,[0-9]{3})*(?:\.[0-9]{2})?",
                text,
                re.IGNORECASE,
            ),
            "orgs": re.findall(
                r"\b[A-Z][a-zA-Z0-9&]{2,}(?: Inc\.| Ltd\.| Corp\.| LLC| Group| Co\.)",
                text,
            ),
        }
        return entities

    def find_clauses(self, text: str, patterns: list) -> list:
        """Finds specific clauses matching a list of regex patterns."""
        findings = []
        for name, pattern in patterns:
            matches = re.finditer(pattern, text, re.IGNORECASE)
            for match in matches:
                findings.append(
                    {
                        "type": name,
                        "text": match.group(0),
                        "context": text[
                            max(0, match.start() - 50) : min(
                                len(text), match.end() + 50
                            )
                        ],
                    }
                )
        return findings
