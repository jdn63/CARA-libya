"""Local-agency data entry blueprint.

Currently exposes the Infectious Disease pipeline:

* ``GET  /data-entry/infectious-disease``                    → page
* ``GET  /data-entry/infectious-disease/template.xlsx``      → blank template
* ``POST /data-entry/infectious-disease/upload``             → ingest workbook
* ``GET  /data-entry/infectious-disease/export.xlsx``        → consolidated export
"""

from __future__ import annotations

import logging
import re
import zipfile
from datetime import datetime
from pathlib import Path

from flask import (Blueprint, abort, flash, redirect, render_template,
                   request, send_file, url_for)
from werkzeug.utils import secure_filename
from io import BytesIO

from utils.local_agency_data import (
    UPLOAD_DIR, DISEASES, METRICS,
    build_export_workbook, build_template_workbook, consolidated_table,
)

logger = logging.getLogger(__name__)

data_entry_bp = Blueprint("data_entry", __name__, url_prefix="/data-entry")

XLSX_MIME = (
    "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
)
MAX_UPLOAD_BYTES = 10 * 1024 * 1024  # 10 MB hard cap per file


# --------------------------------------------------------------------------- #
# Page
# --------------------------------------------------------------------------- #

@data_entry_bp.route("/infectious-disease", methods=["GET"])
def infectious_disease_page():
    """Render the Infectious Disease data-entry page (form + comparison table)."""
    table = consolidated_table()
    return render_template(
        "data_entry/infectious_disease.html",
        table=table,
        diseases=DISEASES,
        metrics=METRICS,
        current_year=datetime.utcnow().year,
    )


# --------------------------------------------------------------------------- #
# Template download
# --------------------------------------------------------------------------- #

@data_entry_bp.route("/infectious-disease/template.xlsx", methods=["GET"])
def infectious_disease_template():
    """Send the blank Excel template for agencies to complete."""
    try:
        data = build_template_workbook()
    except Exception as exc:
        logger.exception("Failed to build infectious-disease template: %s", exc)
        abort(500)
    return send_file(
        BytesIO(data),
        mimetype=XLSX_MIME,
        as_attachment=True,
        download_name="cara_libya_infectious_disease_template.xlsx",
    )


# --------------------------------------------------------------------------- #
# Upload
# --------------------------------------------------------------------------- #

@data_entry_bp.route("/infectious-disease/upload", methods=["POST"])
def infectious_disease_upload():
    """Accept a completed workbook from a local response agency."""
    file = request.files.get("workbook")
    if file is None or not file.filename:
        flash("لم يتم اختيار ملف. / No file selected.", "warning")
        return redirect(url_for("data_entry.infectious_disease_page"))

    filename = secure_filename(file.filename)
    if not filename.lower().endswith(".xlsx"):
        flash("الملف يجب أن يكون بصيغة .xlsx فقط. / "
              "Only .xlsx files are accepted.", "danger")
        return redirect(url_for("data_entry.infectious_disease_page"))

    # Read the upload into memory with a hard cap. We read 1 byte past the
    # limit so we can reject files whose Content-Length header was missing or
    # spoofed by the client.
    raw = file.stream.read(MAX_UPLOAD_BYTES + 1)
    if len(raw) > MAX_UPLOAD_BYTES:
        flash("الملف يتجاوز الحد الأقصى 10 ميغابايت. / "
              "File exceeds 10 MB limit.", "danger")
        return redirect(url_for("data_entry.infectious_disease_page"))
    if len(raw) == 0:
        flash("الملف فارغ. / The uploaded file is empty.", "danger")
        return redirect(url_for("data_entry.infectious_disease_page"))

    # Validate that the bytes are actually an OOXML workbook (a ZIP archive
    # containing xl/workbook.xml). Extension-only checks let attackers store
    # arbitrary blobs that we'd then re-parse on every page load.
    try:
        with zipfile.ZipFile(BytesIO(raw)) as zf:
            names = set(zf.namelist())
            if "xl/workbook.xml" not in names:
                raise zipfile.BadZipFile("missing xl/workbook.xml")
    except zipfile.BadZipFile:
        flash("الملف ليس مصنف Excel صالحاً (.xlsx). / "
              "The file is not a valid Excel workbook (.xlsx).", "danger")
        return redirect(url_for("data_entry.infectious_disease_page"))

    UPLOAD_DIR.mkdir(parents=True, exist_ok=True)
    timestamp = datetime.utcnow().strftime("%Y%m%dT%H%M%SZ")
    safe_stem = re.sub(r"[^A-Za-z0-9_.-]+", "_", Path(filename).stem)[:80]
    target = UPLOAD_DIR / f"{timestamp}__{safe_stem}.xlsx"

    try:
        target.write_bytes(raw)
    except Exception as exc:
        logger.exception("Could not save uploaded file: %s", exc)
        flash("تعذّر حفظ الملف على الخادم. / "
              "Could not save the uploaded file.", "danger")
        return redirect(url_for("data_entry.infectious_disease_page"))

    # Quick sanity-parse so we can report row count to the user.
    try:
        table = consolidated_table()
        flash(
            f"تم رفع الملف بنجاح. / File uploaded successfully. "
            f"({table['upload_count']} ملف في قاعدة البيانات / "
            f"file(s) in store, {len(table['rows'])} بلدية / municipalities)",
            "success",
        )
    except Exception as exc:
        logger.exception("Upload saved but consolidation failed: %s", exc)
        flash("تم حفظ الملف لكن تعذّر تحليله — راجع التنسيق. / "
              "File saved but could not be parsed — please check the format.",
              "warning")

    return redirect(url_for("data_entry.infectious_disease_page"))


# --------------------------------------------------------------------------- #
# Export consolidated table
# --------------------------------------------------------------------------- #

@data_entry_bp.route("/infectious-disease/export.xlsx", methods=["GET"])
def infectious_disease_export():
    """Export the consolidated comparison table as .xlsx."""
    table = consolidated_table()
    try:
        data = build_export_workbook(table)
    except Exception as exc:
        logger.exception("Failed to build export workbook: %s", exc)
        abort(500)

    fresh = table.get("freshness")
    suffix = fresh.isoformat() if fresh else "empty"
    return send_file(
        BytesIO(data),
        mimetype=XLSX_MIME,
        as_attachment=True,
        download_name=f"cara_libya_infectious_disease_comparison_{suffix}.xlsx",
    )
