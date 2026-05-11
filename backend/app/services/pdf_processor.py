"""Extract text from a PDF. Try pypdf first; fall back to OCR if the doc is image-only."""
from __future__ import annotations

from pathlib import Path

from pypdf import PdfReader

OCR_TEXT_THRESHOLD = 80  # chars; below this we assume the PDF is scanned and OCR


def extract_text(pdf_path: Path) -> str:
    text = _extract_with_pypdf(pdf_path)
    if len(text.strip()) < OCR_TEXT_THRESHOLD:
        try:
            text = _extract_with_ocr(pdf_path)
        except Exception:
            # OCR is best-effort; if it fails just return whatever pypdf gave us.
            pass
    return text.strip()


def _extract_with_pypdf(pdf_path: Path) -> str:
    reader = PdfReader(str(pdf_path))
    parts: list[str] = []
    for page in reader.pages:
        try:
            parts.append(page.extract_text() or "")
        except Exception:
            continue
    return "\n\n".join(parts)


def _extract_with_ocr(pdf_path: Path) -> str:
    # Imported lazily so a missing tesseract install doesn't break the happy path.
    from pdf2image import convert_from_path
    import pytesseract

    images = convert_from_path(str(pdf_path), dpi=200)
    return "\n\n".join(pytesseract.image_to_string(img) for img in images)
