import re


class DocumentParser:
    """
    Handles extraction of text from raw document bytes or files.
    In a full production system, this would use libraries like PyMuPDF (fitz) or Amazon Textract.
    """

    @staticmethod
    def extract_text(raw_bytes: bytes) -> str:
        """Extracts text from bytes (mocking PDF/text extraction)."""
        try:
            return raw_bytes.decode("utf-8")
        except UnicodeDecodeError:
            # If not UTF-8, try latin-1 as fallback for some binary text formats
            return raw_bytes.decode("latin-1")

    @staticmethod
    def clean_text(text: str) -> str:
        """Standardizes text for NLP processing."""
        # Remove extra whitespace
        text = re.sub(r"\s+", " ", text)
        return text.strip()

    @staticmethod
    def get_preview(text: str, length: int = 500) -> str:
        """Returns a short preview of the document."""
        return text[:length] + "..." if len(text) > length else text
