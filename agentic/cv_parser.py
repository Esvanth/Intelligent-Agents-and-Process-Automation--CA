"""Agentic component: extract plain text from a CV PDF using pdfplumber."""
from pathlib import Path
import pdfplumber


def parse_cv(pdf_path):
    pdf_path = Path(pdf_path)
    if not pdf_path.exists():
        raise FileNotFoundError(pdf_path)
    chunks = []
    with pdfplumber.open(pdf_path) as pdf:
        for page in pdf.pages:
            chunks.append(page.extract_text() or "")
    full = "\n".join(chunks).strip()
    return full if full else "[CV text could not be extracted from this PDF.]"
