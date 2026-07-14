"""
Document parser — converts raw files to a list of page dicts.

Supports:
  - PDF: text extraction via pdfplumber (primary)
  - PDF: OCR fallback via pytesseract for image-only / scanned pages
"""

import logging
from pathlib import Path
from typing import Protocol

import pdfplumber
import pytesseract
from PIL import Image

logger = logging.getLogger(__name__)


class ParsedPage(Protocol):
    page_num: int
    text: str

def parse_txt(file_path: str) -> list[dict]:
    path = Path(file_path)
    if not path.exists():
        raise FileNotFoundError(f"File not found: {file_path}")
    text = path.read_text(encoding="utf-8")
    return [{"page_num": 1, "text": text.strip()}]

def parse_pdf(file_path: str) -> list[dict]:
    """
    Parse a PDF file and return a list of page dicts.

    Returns:
        list of {"page_num": int, "text": str}

    Text extraction uses pdfplumber. If a page yields no text, pytesseract OCR is used as a fallback.
    """
    path = Path(file_path)
    if not path.exists():
        raise FileNotFoundError(f"File not found: {file_path}")

    pages: list[dict] = []

    with pdfplumber.open(file_path) as pdf:
        for i, page in enumerate(pdf.pages):
            page_num = i + 1
            text = page.extract_text() or ""

            if not text.strip():
                logger.debug("Page %d: no text extracted, attempting OCR", page_num)
                try:
                    pil_image: Image.Image = page.to_image(resolution=300).original
                    text = pytesseract.image_to_string(pil_image)
                except Exception as exc:
                    logger.warning("OCR failed for page %d: %s", page_num, exc)
                    text = ""

            pages.append({"page_num": page_num, "text": text.strip()})

    logger.info("Parsed %d pages from %s", len(pages), path.name)
    return pages
