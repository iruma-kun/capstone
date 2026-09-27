import re

# A specialized financial sentiment lexicon optimized for stock headlines and articles
FINANCIAL_LEXICON = {
    # Positive Financial Terms
    "surge": 2.0,
    "soar": 2.0,
    "beat": 1.5,
    "exceed": 1.5,
    "bullish": 1.8,
    "growth": 1.2,
    "outperform": 1.6,
    "profit": 1.4,
    "gain": 1.0,
    "dividend": 1.2,
    "upgrade": 1.8,
    "record-high": 2.0,
    "acquisition": 1.2,
    "partnership": 1.0,
    "breakout": 1.5,
    "rally": 1.6,
    "strong": 1.1,
    "positive": 1.0,
    "optimistic": 1.2,
    "rebound": 1.3,
    "successful": 1.1,

    # Negative Financial Terms
    "plunge": -2.0,
    "slump": -1.8,
    "miss": -1.5,
    "fall": -1.0,
    "drop": -1.0,
    "bearish": -1.8,
    "loss": -1.5,
    "deficit": -1.6,
    "underperform": -1.6,
    "downgrade": -1.8,
    "fine": -1.3,
    "scandal": -2.0,
    "lawsuit": -1.5,
    "decline": -1.1,
    "weak": -1.1,
    "negative": -1.0,
    "pessimistic": -1.2,
    "risk": -0.8,
    "warn": -1.0,
    "bankrupt": -2.5,
    "collapse": -2.2,
    "layoff": -1.4,
    "inflation": -0.7,
}

class FinancialSentimentAnalyzer:
    """
    A lightweight, ultra-fast sentiment analyzer tailored for financial news headlines.
    Uses a targeted financial lexicon to assign sentiment scores between -1.0 (very negative) and 1.0 (very positive).
    """

    @staticmethod
    def clean_text(text: str) -> str:
        """Cleans and tokenizes text for analysis."""
        text = text.lower()
        # Remove special characters except spaces
        text = re.sub(r'[^a-zA-Z0-9\s-]', '', text)
        return text

    def analyze(self, text: str) -> float:
        """
        Analyzes the input news text and returns a sentiment score between -1.0 and 1.0.
        """
        if not text:
            return 0.0

        cleaned = self.clean_text(text)
        words = cleaned.split()

        score = 0.0
        match_count = 0

        # Simple bigram handling for negation
        negation_words = {"no", "not", "never", "none", "hardly", "fail", "neither"}
        negate = False

        for i, word in enumerate(words):
            # Check for negation in the prior 2 words
            negate = any(words[j] in negation_words for j in range(max(0, i-2), i))

            # Check lexicon
            if word in FINANCIAL_LEXICON:
                weight = FINANCIAL_LEXICON[word]
                score += -weight if negate else weight
                match_count += 1

        # Calculate average score, normalized to [-1, 1] range using tanh-like scaling
        if match_count == 0:
            return 0.0

        avg_score = score / match_count
        # Normalize between -1.0 and 1.0 using a sigmoid-like capping
        normalized_score = max(-1.0, min(1.0, avg_score / 2.0))
        return round(normalized_score, 3)

    def analyze_batch(self, articles: list) -> float:
        """
        Analyzes a batch of headlines/descriptions and returns a single consensus score.
        Accepts a list of dicts with 'title' or list of strings.
        """
        scores = []
        for article in articles:
            text = article if isinstance(article, str) else article.get('title', '') + " " + article.get('summary', '')
            score = self.analyze(text)
            scores.append(score)

        return round(sum(scores) / len(scores), 3) if scores else 0.0

if __name__ == "__main__":
    analyzer = FinancialSentimentAnalyzer()

    test_headlines = [
        "Apple shares surge to record-high following strong iPhone sales and growth",
        "Tesla stock plunges after major earnings miss and production warning",
        "No growth expected as Microsoft warns of high inflation risk and potential layoff",
        "Federal Trade Commission hits Amazon with a massive fine over privacy issues"
    ]

    print("Testing Financial Sentiment Analyzer:")
    for headline in test_headlines:
        print(f"Headline: '{headline}' => Sentiment Score: {analyzer.analyze(headline)}")
