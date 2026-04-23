"""Local-agency data entry blueprint — domain-driven.

A single set of routes serves every workshop domain registered in
:mod:`utils.data_entry_domains`:

* ``GET  /data-entry/``                          → hub listing all domains
* ``GET  /data-entry/<key>``                     → page (download · upload · compare)
* ``GET  /data-entry/<key>/template.xlsx``       → blank template
* ``POST /data-entry/<key>/upload``              → ingest workbook
* ``GET  /data-entry/<key>/export.xlsx``         → consolidated export
* ``GET  /data-entry/infectious-disease``        → 301 → /data-entry/infectious-disease (kept for old links)
"""

from __future__ import annotations

import logging
import re
import zipfile
from datetime import datetime
from io import BytesIO
from pathlib import Path

from flask import (Blueprint, abort, flash, redirect, render_template,
                   request, send_file, url_for)
from werkzeug.utils import secure_filename

from utils.data_entry_domains import all_domains, get_domain
from utils.local_agency_data import (
    build_export_workbook, build_template_workbook,
    consolidated_table, upload_dir_for, workbook_domain_key,
)

logger = logging.getLogger(__name__)

data_entry_bp = Blueprint("data_entry", __name__, url_prefix="/data-entry")

XLSX_MIME = (
    "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
)
MAX_UPLOAD_BYTES = 10 * 1024 * 1024  # 10 MB hard cap per file


# --------------------------------------------------------------------------- #
# Hub
# --------------------------------------------------------------------------- #

@data_entry_bp.route("/", methods=["GET"])
def hub():
    """List every workshop data-entry domain with quick-status badges."""
    domains_with_status = []
    for spec in all_domains():
        table = consolidated_table(spec)
        domains_with_status.append({
            "spec": spec,
            "upload_count": table["upload_count"],
            "freshness": table["freshness"],
            "muni_count": len(table["rows"]),
        })
    return render_template(
        "data_entry/index.html",
        domains=domains_with_status,
        current_year=datetime.utcnow().year,
    )


# --------------------------------------------------------------------------- #
# Per-domain page
# --------------------------------------------------------------------------- #

@data_entry_bp.route("/<key>", methods=["GET"])
def domain_page(key: str):
    spec = get_domain(key)
    if spec is None:
        abort(404)
    table = consolidated_table(spec)
    return render_template(
        "data_entry/domain.html",
        spec=spec,
        table=table,
        current_year=datetime.utcnow().year,
    )


# --------------------------------------------------------------------------- #
# Template download
# --------------------------------------------------------------------------- #

@data_entry_bp.route("/<key>/template.xlsx", methods=["GET"])
def domain_template(key: str):
    spec = get_domain(key)
    if spec is None:
        abort(404)
    try:
        data = build_template_workbook(spec)
    except Exception as exc:
        logger.exception("Failed to build %s template: %s", key, exc)
        abort(500)
    return send_file(
        BytesIO(data),
        mimetype=XLSX_MIME,
        as_attachment=True,
        download_name=f"cara_libya_{key.replace('-', '_')}_template.xlsx",
    )


# --------------------------------------------------------------------------- #
# Upload
# --------------------------------------------------------------------------- #

@data_entry_bp.route("/<key>/upload", methods=["POST"])
def domain_upload(key: str):
    spec = get_domain(key)
    if spec is None:
        abort(404)

    file = request.files.get("workbook")
    if file is None or not file.filename:
        flash("لم يتم اختيار ملف. / No file selected.", "warning")
        return redirect(url_for("data_entry.domain_page", key=key))

    filename = secure_filename(file.filename)
    if not filename.lower().endswith(".xlsx"):
        flash("الملف يجب أن يكون بصيغة .xlsx فقط. / "
              "Only .xlsx files are accepted.", "danger")
        return redirect(url_for("data_entry.domain_page", key=key))

    # Read with a hard cap (one byte beyond the limit) so that uploads
    # without (or with spoofed) Content-Length are still rejected.
    raw = file.stream.read(MAX_UPLOAD_BYTES + 1)
    if len(raw) > MAX_UPLOAD_BYTES:
        flash("الملف يتجاوز الحد الأقصى 10 ميغابايت. / "
              "File exceeds 10 MB limit.", "danger")
        return redirect(url_for("data_entry.domain_page", key=key))
    if len(raw) == 0:
        flash("الملف فارغ. / The uploaded file is empty.", "danger")
        return redirect(url_for("data_entry.domain_page", key=key))

    # Validate that the bytes are a real OOXML workbook (ZIP + xl/workbook.xml).
    try:
        with zipfile.ZipFile(BytesIO(raw)) as zf:
            if "xl/workbook.xml" not in set(zf.namelist()):
                raise zipfile.BadZipFile("missing xl/workbook.xml")
    except zipfile.BadZipFile:
        flash("الملف ليس مصنف Excel صالحاً (.xlsx). / "
              "The file is not a valid Excel workbook (.xlsx).", "danger")
        return redirect(url_for("data_entry.domain_page", key=key))

    # Domain check — every template generated by this app embeds a custom
    # workbook property identifying the domain it was built for. Reject
    # uploads that target the wrong endpoint (e.g. the infectious-disease
    # template POSTed to /data-entry/maternal-child-health/upload) so we
    # never silently map unrelated columns onto target indicators.
    file_domain = workbook_domain_key(raw)
    if file_domain is None:
        flash(
            "تعذّر التحقق من نوع القالب. الرجاء تنزيل قالب جديد من هذه "
            "الصفحة وإعادة المحاولة. / "
            "Could not verify the template type. Please download a fresh "
            "template from this page and try again.",
            "danger",
        )
        return redirect(url_for("data_entry.domain_page", key=key))
    if file_domain != spec.key:
        other = get_domain(file_domain)
        other_label = other.name_en if other else file_domain
        flash(
            f"الملف المرفوع تابع لمجال آخر ({other_label}). الرجاء تنزيل "
            f"قالب «{spec.name_ar}» وإعادة المحاولة. / "
            f"This file belongs to a different domain ({other_label}). "
            f"Please download the {spec.name_en} template and try again.",
            "danger",
        )
        return redirect(url_for("data_entry.domain_page", key=key))

    upload_dir = upload_dir_for(spec)
    upload_dir.mkdir(parents=True, exist_ok=True)
    timestamp = datetime.utcnow().strftime("%Y%m%dT%H%M%SZ")
    safe_stem = re.sub(r"[^A-Za-z0-9_.-]+", "_", Path(filename).stem)[:80]
    target = upload_dir / f"{timestamp}__{safe_stem}.xlsx"

    try:
        target.write_bytes(raw)
    except Exception as exc:
        logger.exception("Could not save uploaded file: %s", exc)
        flash("تعذّر حفظ الملف على الخادم. / "
              "Could not save the uploaded file.", "danger")
        return redirect(url_for("data_entry.domain_page", key=key))

    try:
        table = consolidated_table(spec)
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

    return redirect(url_for("data_entry.domain_page", key=key))


# --------------------------------------------------------------------------- #
# Export
# --------------------------------------------------------------------------- #

@data_entry_bp.route("/<key>/export.xlsx", methods=["GET"])
def domain_export(key: str):
    spec = get_domain(key)
    if spec is None:
        abort(404)
    table = consolidated_table(spec)
    try:
        data = build_export_workbook(spec, table)
    except Exception as exc:
        logger.exception("Failed to build %s export: %s", key, exc)
        abort(500)

    fresh = table.get("freshness")
    suffix = fresh.isoformat() if fresh else "empty"
    return send_file(
        BytesIO(data),
        mimetype=XLSX_MIME,
        as_attachment=True,
        download_name=(
            f"cara_libya_{key.replace('-', '_')}_comparison_{suffix}.xlsx"
        ),
    )
