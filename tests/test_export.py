import pytest

from app.services import export_service


def test_markdown_export_bytes():
    md = "# Hello\nWorld"
    b = export_service.export_markdown_bytes(md)
    assert isinstance(b, bytes)
    assert b.decode("utf-8") == md


def test_pdf_export_behavior():
    html = "<p>Hi</p>"
    try:
        import weasyprint  # type: ignore

        # If installed, ensure we get bytes back
        pdf = export_service.html_to_pdf_bytes(html)
        assert isinstance(pdf, (bytes, bytearray))
    except ImportError:
        with pytest.raises(RuntimeError):
            export_service.html_to_pdf_bytes(html)
