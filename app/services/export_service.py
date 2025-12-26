from typing import Optional
import html as html_module
from datetime import datetime

try:
    import markdown as _md
except Exception:
    _md = None


def markdown_to_html(markdown_text: str) -> str:
    """Convert Markdown text to HTML with proper styling.
    Uses `markdown` package when available, otherwise returns a safe preformatted HTML fallback.
    """
    if markdown_text is None:
        markdown_text = ""
    
    # Convert markdown to HTML
    if _md:
        html_content = _md.markdown(markdown_text)
    else:
        # Fallback: escape and wrap in <pre>
        escaped = html_module.escape(markdown_text)
        html_content = f"<pre>{escaped}</pre>"
    
    # Wrap with proper styling
    styled_html = f"""
    <html>
    <head>
        <meta charset="UTF-8">
        <style>
            body {{
                font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, "Helvetica Neue", Arial, sans-serif;
                line-height: 1.6;
                color: #333;
                max-width: 900px;
                margin: 0 auto;
                padding: 20px;
            }}
            h1, h2, h3, h4, h5, h6 {{
                margin-top: 1.5em;
                margin-bottom: 0.5em;
                font-weight: 600;
            }}
            h1 {{
                font-size: 2em;
                border-bottom: 2px solid #007bff;
                padding-bottom: 0.3em;
            }}
            h2 {{
                font-size: 1.5em;
                border-bottom: 1px solid #ddd;
                padding-bottom: 0.2em;
            }}
            p {{
                margin: 0.5em 0;
            }}
            strong {{
                font-weight: 600;
                color: #333;
            }}
            code {{
                background-color: #f4f4f4;
                padding: 2px 6px;
                border-radius: 3px;
                font-family: "Courier New", monospace;
                font-size: 0.9em;
            }}
            pre {{
                background-color: #f4f4f4;
                padding: 10px;
                border-radius: 5px;
                overflow-x: auto;
                font-family: "Courier New", monospace;
            }}
            pre code {{
                background-color: transparent;
                padding: 0;
            }}
            blockquote {{
                border-left: 4px solid #007bff;
                margin: 0.5em 0;
                padding-left: 1em;
                color: #666;
            }}
            ul, ol {{
                margin: 0.5em 0;
                padding-left: 2em;
            }}
            li {{
                margin: 0.25em 0;
            }}
            table {{
                border-collapse: collapse;
                width: 100%;
                margin: 1em 0;
            }}
            table thead {{
                background-color: #f4f4f4;
            }}
            table th, table td {{
                border: 1px solid #ddd;
                padding: 8px 12px;
                text-align: left;
            }}
            a {{
                color: #007bff;
                text-decoration: none;
            }}
            a:hover {{
                text-decoration: underline;
            }}
        </style>
    </head>
    <body>
        {html_content}
    </body>
    </html>
    """
    return styled_html


def crs_to_professional_html(content: str, project_name: str = "Project") -> str:
    """Convert CRS Markdown content to a professional, corporate-style HTML document.
    
    Args:
        content: Markdown-formatted CRS content
        project_name: Name of the project for the document header
        
    Returns:
        HTML string with professional formatting suitable for PDF export
    """
    if content is None:
        content = ""
    
    # Convert markdown to HTML
    if _md:
        html_content = _md.markdown(content)
    else:
        escaped = html_module.escape(content)
        html_content = f"<pre>{escaped}</pre>"
    
    current_date = datetime.now().strftime("%B %d, %Y")
    
    # Professional corporate styling for CRS documents - simplified for weasyprint compatibility
    styled_html = f"""<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <style>
        * {{
            margin: 0;
            padding: 0;
        }}
        
        body {{
            font-family: Arial, sans-serif;
            line-height: 1.7;
            color: #2c3e50;
            background: white;
            padding: 40px;
            font-size: 11pt;
        }}
        
        .document-header {{
            border-top: 5px solid #0066cc;
            border-bottom: 2px solid #0066cc;
            padding: 25px 0;
            margin-bottom: 30px;
        }}
        
        .document-title {{
            font-size: 28pt;
            font-weight: bold;
            color: #0066cc;
            margin-bottom: 8px;
        }}
        
        .document-subtitle {{
            font-size: 16pt;
            color: #555;
            font-weight: bold;
            margin-bottom: 12px;
        }}
        
        .document-meta {{
            font-size: 10pt;
            color: #666;
            border-top: 1px solid #ddd;
            padding-top: 10px;
        }}
        
        .meta-line {{
            margin: 3px 0;
        }}
        
        .meta-label {{
            font-weight: bold;
            color: #0066cc;
            display: inline-block;
            width: 100px;
        }}
        
        .content {{
            margin-top: 20px;
        }}
        
        h1 {{
            font-size: 20pt;
            font-weight: bold;
            color: #0066cc;
            margin: 25px 0 15px 0;
            padding-bottom: 10px;
            border-bottom: 2px solid #0066cc;
            page-break-after: avoid;
        }}
        
        h2 {{
            font-size: 16pt;
            font-weight: bold;
            color: #0088dd;
            margin: 20px 0 12px 0;
            padding-bottom: 8px;
            border-bottom: 1px solid #ddd;
            page-break-after: avoid;
        }}
        
        h3 {{
            font-size: 13pt;
            font-weight: bold;
            color: #333;
            margin: 15px 0 10px 0;
            page-break-after: avoid;
        }}
        
        h4, h5, h6 {{
            font-size: 11pt;
            font-weight: bold;
            margin: 12px 0 8px 0;
        }}
        
        p {{
            margin-bottom: 12px;
            text-align: justify;
        }}
        
        strong {{
            font-weight: bold;
            color: #0066cc;
        }}
        
        em {{
            font-style: italic;
        }}
        
        code {{
            background-color: #f5f5f5;
            padding: 2px 4px;
            font-family: "Courier New", monospace;
            font-size: 9pt;
            color: #c41e3a;
        }}
        
        pre {{
            background-color: #f8f8f8;
            border: 1px solid #ddd;
            padding: 12px;
            overflow-x: auto;
            margin: 15px 0;
            font-family: "Courier New", monospace;
            font-size: 9pt;
            line-height: 1.4;
            color: #333;
        }}
        
        blockquote {{
            border-left: 4px solid #0066cc;
            background-color: #f0f7ff;
            margin: 15px 0;
            padding: 12px 15px;
            color: #2c3e50;
        }}
        
        ul {{
            margin: 12px 0;
            padding-left: 25px;
        }}
        
        ol {{
            margin: 12px 0;
            padding-left: 25px;
        }}
        
        li {{
            margin-bottom: 6px;
        }}
        
        table {{
            border-collapse: collapse;
            width: 100%;
            margin: 15px 0;
            border: 1px solid #ddd;
        }}
        
        table thead {{
            background-color: #0066cc;
            color: white;
        }}
        
        table th {{
            padding: 10px;
            text-align: left;
            font-weight: bold;
            font-size: 10pt;
            border: 1px solid #0066cc;
        }}
        
        table td {{
            padding: 8px 10px;
            border: 1px solid #ddd;
            font-size: 10pt;
        }}
        
        table tbody tr:nth-child(odd) {{
            background-color: #fafafa;
        }}
        
        a {{
            color: #0066cc;
            text-decoration: underline;
        }}
        
        hr {{
            border: none;
            border-top: 2px solid #ddd;
            margin: 25px 0;
        }}
    </style>
</head>
<body>
    <div class="document-header">
        <div class="document-title">Client Requirements Specification</div>
        <div class="document-subtitle">{project_name}</div>
        <div class="document-meta">
            <div class="meta-line"><span class="meta-label">Generated:</span> {current_date}</div>
            <div class="meta-line"><span class="meta-label">Document Type:</span> CRS</div>
            <div class="meta-line"><span class="meta-label">Status:</span> Official</div>
        </div>
    </div>
    
    <div class="content">
        {html_content}
    </div>
</body>
</html>
"""
    return styled_html


def export_markdown_bytes(markdown_text: str) -> bytes:
    """Return raw markdown bytes for download."""
    if markdown_text is None:
        markdown_text = ""
    return markdown_text.encode("utf-8")


def html_to_pdf_bytes(html: str) -> bytes:
    """Render HTML to PDF bytes.

    Tries to use WeasyPrint. If it's not installed or fails, raises RuntimeError
    to indicate the runtime dependency is required.
    """
    if html is None:
        html = ""
    try:
        from weasyprint import HTML
    except Exception as e:
        raise RuntimeError("PDF export requires weasyprint to be installed") from e

    try:
        pdf = HTML(string=html).write_pdf()
        return pdf
    except Exception as e:
        raise RuntimeError("Failed to render PDF") from e
