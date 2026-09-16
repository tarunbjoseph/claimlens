"""Raw text extraction from a claim PDF — the pipeline's only view of a claim.

No structure is imposed here. What comes back is exactly what a real
extraction pipeline would see: plain text, to be parsed by the classify/
extract passes rather than assumed.
"""

from __future__ import annotations

from pathlib import Path

from pypdf import PdfReader


def extract_pdf_text(pdf_path: Path) -> str:
    reader = PdfReader(str(pdf_path))
    return "\n".join(page.extract_text() or "" for page in reader.pages)
