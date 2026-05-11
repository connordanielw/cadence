from io import BytesIO
from pathlib import Path

from pypdf import PdfWriter

from app.services import pdf_processor


def _make_pdf_with_text(tmp_path: Path, text: str) -> Path:
    """pypdf can't write text easily; use a tiny reportlab-free hack via a blank PDF.

    For the test we just confirm the function handles an empty/text PDF without crashing.
    A richer fixture would use reportlab to lay down real text.
    """
    writer = PdfWriter()
    writer.add_blank_page(width=72, height=72)
    p = tmp_path / "blank.pdf"
    with p.open("wb") as f:
        writer.write(f)
    return p


def test_extract_text_handles_blank_pdf(tmp_path):
    pdf = _make_pdf_with_text(tmp_path, "")
    # Should not raise; will fall through to OCR (which may or may not be installed),
    # but worst case returns ''.
    result = pdf_processor.extract_text(pdf)
    assert isinstance(result, str)
