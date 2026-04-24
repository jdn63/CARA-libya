"""
PDF export helpers for Libya CARA.

Wraps WeasyPrint with sensible defaults (A4, embedded local fonts,
project root as base_url so static assets resolve correctly).

Usage:
    from utils.pdf_export import render_pdf_response
    return render_pdf_response(
        'action_plan_pdf.html',
        filename='Libya_CARA_Action_Plan_Tripoli.pdf',
        context={...},
    )
"""

from __future__ import annotations

import logging
import os
import re
from typing import Any, Mapping, Optional

from flask import Response, current_app, render_template

logger = logging.getLogger(__name__)


def _safe_filename(name: str) -> str:
    """Strip filesystem-unsafe characters and collapse whitespace."""
    cleaned = re.sub(r'[^\w\.\- ]+', '_', name, flags=re.UNICODE)
    cleaned = re.sub(r'\s+', '_', cleaned).strip('._')
    return cleaned or 'document.pdf'


def render_html_to_pdf(html: str, base_url: Optional[str] = None) -> bytes:
    """Render an HTML string to a PDF byte string using WeasyPrint.

    `base_url` should point to the project root so that relative URLs
    inside the HTML (e.g. `static/fonts/Cairo-Regular.woff2`) resolve to
    real files on disk.
    """
    # Imported lazily so the rest of the app keeps working even if the
    # native WeasyPrint dependencies are missing on a particular host.
    from weasyprint import HTML  # type: ignore[import-not-found]

    if base_url is None:
        base_url = current_app.root_path

    return HTML(string=html, base_url=base_url).write_pdf()


def render_pdf_response(
    template_name: str,
    *,
    filename: str,
    context: Mapping[str, Any],
    inline: bool = False,
) -> Response:
    """Render a Jinja template to PDF and return it as a Flask Response.

    Args:
        template_name: Jinja template path, e.g. 'action_plan_pdf.html'.
        filename: User-facing filename for the download.
        context: Template context.
        inline: If True, set Content-Disposition to 'inline' so browsers
            display the PDF in-tab; otherwise force a download.
    """
    html = render_template(template_name, **context)
    pdf_bytes = render_html_to_pdf(html, base_url=current_app.root_path)

    safe_name = _safe_filename(filename)
    disposition = 'inline' if inline else 'attachment'

    response = Response(pdf_bytes, mimetype='application/pdf')
    response.headers['Content-Disposition'] = (
        f"{disposition}; filename=\"{safe_name}\""
    )
    response.headers['Content-Length'] = str(len(pdf_bytes))
    response.headers['X-Content-Type-Options'] = 'nosniff'
    # PDFs of this size are quick to regenerate; prevent stale caches.
    response.headers['Cache-Control'] = 'no-store, max-age=0'

    logger.info(
        "Generated PDF %s (%d bytes) from template %s",
        safe_name, len(pdf_bytes), template_name,
    )
    return response
