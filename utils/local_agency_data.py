"""Local agency data ingestion — Infectious Disease module.

Provides helpers to:

1. Build the downloadable Excel template that local response agencies use to
   submit infectious disease data (incidence / morbidity / mortality for HIV,
   HBV, HCV, TB) per municipality per capture date.
2. Read every workbook that has been uploaded to
   ``data/uploads/local_agencies/infectious_disease/`` and consolidate the
   most recent row per municipality into a single comparison table.
3. Build the consolidated comparison workbook that the operator can re-export
   for offline analysis.

Design notes
------------
* The schema is intentionally bilingual (Arabic primary, English secondary).
* Numeric fields are *rates per 100 000 population*; agencies that report raw
  counts must compute the rate before submission so that municipalities of
  very different sizes can be compared like-for-like.
* Empty cells are preserved as ``None`` — this drives the "Data not available"
  display in the comparison table rather than a silent zero.
"""

from __future__ import annotations

import io
import json
import logging
import os
from dataclasses import dataclass, field
from datetime import date, datetime
from pathlib import Path
from typing import Any

from openpyxl import Workbook, load_workbook
from openpyxl.styles import Alignment, Font, PatternFill, Side, Border
from openpyxl.utils import get_column_letter
from openpyxl.worksheet.datavalidation import DataValidation

logger = logging.getLogger(__name__)

# --------------------------------------------------------------------------- #
# Constants
# --------------------------------------------------------------------------- #

UPLOAD_DIR = Path("data/uploads/local_agencies/infectious_disease")
MUNICIPALITIES_FILE = Path("data/libya_municipalities.json")

DISEASES: list[tuple[str, str, str]] = [
    # (code, name_ar, name_en)
    ("hiv", "فيروس نقص المناعة البشرية", "HIV"),
    ("hbv", "التهاب الكبد الفيروسي بي", "HBV (Hepatitis B)"),
    ("hcv", "التهاب الكبد الفيروسي سي", "HCV (Hepatitis C)"),
    ("tb",  "السل",                       "TB (Tuberculosis)"),
]

METRICS: list[tuple[str, str, str]] = [
    # (code, name_ar, name_en) — all expressed per 100 000 population
    ("incidence", "معدل الانتشار (حالات جديدة لكل 100 ألف)",
                  "Incidence (new cases per 100k)"),
    ("morbidity", "معدل المرضية (حالات نشطة لكل 100 ألف)",
                  "Morbidity (active cases per 100k)"),
    ("mortality", "معدل الوفيات (وفيات لكل 100 ألف)",
                  "Mortality (deaths per 100k)"),
]

# Fixed columns that come before the disease block.
FIXED_COLUMNS: list[tuple[str, str, str]] = [
    ("municipality_id",  "رمز البلدية",            "Municipality ID"),
    ("name_ar",          "اسم البلدية (عربي)",     "Municipality (Arabic)"),
    ("name_en",          "اسم البلدية (إنجليزي)",  "Municipality (English)"),
    ("capture_date",     "تاريخ جمع البيانات",     "Date of Data Capture (YYYY-MM-DD)"),
    ("agency_name",      "اسم الجهة المُبلِّغة",    "Reporting Agency"),
]

NOTES_COLUMN: tuple[str, str, str] = (
    "notes", "ملاحظات / تباينات في البيانات",
    "Notes / Data Discrepancies",
)


def _disease_metric_columns() -> list[tuple[str, str, str]]:
    """Cartesian product of diseases × metrics, in stable order."""
    cols: list[tuple[str, str, str]] = []
    for d_code, d_ar, d_en in DISEASES:
        for m_code, m_ar, m_en in METRICS:
            cols.append((
                f"{d_code}_{m_code}",
                f"{d_ar} — {m_ar}",
                f"{d_en} — {m_en}",
            ))
    return cols


def all_columns() -> list[tuple[str, str, str]]:
    """Full ordered list of (key, ar_label, en_label) tuples."""
    return [*FIXED_COLUMNS, *_disease_metric_columns(), NOTES_COLUMN]


# --------------------------------------------------------------------------- #
# Municipality loader
# --------------------------------------------------------------------------- #

def _load_municipalities() -> list[dict[str, Any]]:
    """Return the canonical municipality list (id, name_ar, name_en)."""
    try:
        with MUNICIPALITIES_FILE.open(encoding="utf-8") as f:
            doc = json.load(f)
        return doc.get("municipalities", [])
    except FileNotFoundError:
        logger.warning("Municipality file %s not found", MUNICIPALITIES_FILE)
        return []
    except json.JSONDecodeError as exc:
        logger.error("Municipality file is not valid JSON: %s", exc)
        return []


# --------------------------------------------------------------------------- #
# Template builder
# --------------------------------------------------------------------------- #

def _styled_header(cell, ar_label: str, en_label: str) -> None:
    """Render a two-line bilingual header cell."""
    cell.value = f"{ar_label}\n{en_label}"
    cell.font = Font(name="Calibri", bold=True, size=11, color="FFFFFF")
    cell.fill = PatternFill("solid", fgColor="1f4e79")
    cell.alignment = Alignment(
        wrap_text=True, vertical="center", horizontal="center"
    )
    thin = Side(border_style="thin", color="BFBFBF")
    cell.border = Border(left=thin, right=thin, top=thin, bottom=thin)


def build_template_workbook() -> bytes:
    """Build the Excel template that agencies download to fill in.

    Returns
    -------
    bytes
        The raw .xlsx file bytes, ready to send via Flask.
    """
    wb = Workbook()
    ws = wb.active
    ws.title = "Data Entry"
    ws.sheet_view.rightToLeft = True  # Arabic-first ergonomics

    columns = all_columns()

    # Header row
    for col_idx, (_key, ar, en) in enumerate(columns, start=1):
        _styled_header(ws.cell(row=1, column=col_idx), ar, en)

    # Pre-populate municipality rows so agencies don't have to type names.
    municipalities = _load_municipalities()
    for row_idx, m in enumerate(municipalities, start=2):
        ws.cell(row=row_idx, column=1, value=m.get("id", ""))
        ws.cell(row=row_idx, column=2, value=m.get("name_ar", ""))
        ws.cell(row=row_idx, column=3, value=m.get("name_en", ""))

    # Column widths — wider for fixed/notes, narrower for numerics.
    width_map = {
        "municipality_id": 14,
        "name_ar": 26,
        "name_en": 26,
        "capture_date": 18,
        "agency_name": 28,
        "notes": 40,
    }
    for col_idx, (key, _ar, _en) in enumerate(columns, start=1):
        ws.column_dimensions[get_column_letter(col_idx)].width = (
            width_map.get(key, 18)
        )

    # Frozen header + first 5 fixed columns so context stays visible.
    ws.freeze_panes = "F2"
    ws.row_dimensions[1].height = 42

    # Date validation on capture_date column.
    capture_col_idx = next(
        i for i, (k, *_rest) in enumerate(columns, start=1) if k == "capture_date"
    )
    capture_letter = get_column_letter(capture_col_idx)
    last_row = max(2 + len(municipalities), 200)
    date_dv = DataValidation(
        type="date",
        operator="greaterThan",
        formula1="2000-01-01",
        allow_blank=True,
        showErrorMessage=True,
        errorTitle="Invalid date",
        error="Use a real date on or after 2000-01-01 (format YYYY-MM-DD).",
    )
    date_dv.add(f"{capture_letter}2:{capture_letter}{last_row}")
    ws.add_data_validation(date_dv)

    # Numeric (>=0) validation on every disease/metric column.
    rate_dv = DataValidation(
        type="decimal",
        operator="greaterThanOrEqual",
        formula1=0,
        allow_blank=True,
        showErrorMessage=True,
        errorTitle="Invalid rate",
        error="Rates are non-negative numbers (per 100 000 population).",
    )
    for col_idx, (key, *_rest) in enumerate(columns, start=1):
        if any(key.startswith(d[0] + "_") for d in DISEASES):
            letter = get_column_letter(col_idx)
            rate_dv.add(f"{letter}2:{letter}{last_row}")
    ws.add_data_validation(rate_dv)

    # Instructions sheet
    inst = wb.create_sheet("Instructions")
    inst.sheet_view.rightToLeft = True
    inst.column_dimensions["A"].width = 110
    instructions = [
        ("التعليمات — Instructions",
         True),
        ("", False),
        ("١. لا تُعدِّل صف الترويسة أو ترتيب الأعمدة.",
         False),
        ("1. Do not modify the header row or the column order.",
         False),
        ("", False),
        ("٢. تاريخ جمع البيانات بصيغة YYYY-MM-DD (مثال: 2026-04-23).",
         False),
        ("2. Date of Data Capture must follow the format YYYY-MM-DD "
         "(e.g. 2026-04-23).",
         False),
        ("", False),
        ("٣. جميع المعدلات تُسجَّل لكل 100 ألف نسمة. اترك الخلية فارغة إذا "
         "لم تتوفر البيانات — لا تكتب صفراً ولا «N/A».",
         False),
        ("3. All rates are per 100 000 population. Leave the cell empty if data "
         "is not available — do NOT enter zero or 'N/A'.",
         False),
        ("", False),
        ("٤. أَدخِل صفّاً واحداً لكل بلدية لكل تاريخ جمع. لإرسال تحديث "
         "أحدث، أَضِف صفّاً جديداً — لا تَستبدل الصف القديم.",
         False),
        ("4. Enter one row per municipality per capture date. To submit an "
         "update later, add a new row — do not overwrite the old row.",
         False),
        ("", False),
        ("٥. استخدم حقل «الملاحظات» للإشارة إلى أيّ تباين في البيانات أو "
         "ظروف خاصة (نقص في الإبلاغ، تفشٍّ موضعي، تغيير منهجي…).",
         False),
        ("5. Use the Notes field to flag any data discrepancies or special "
         "circumstances (under-reporting, localised outbreak, methodology "
         "change, etc.).",
         False),
        ("", False),
        ("٦. عند الانتهاء، احفظ الملف بصيغة .xlsx وارفعه إلى البوابة.",
         False),
        ("6. When done, save the file as .xlsx and upload it through the "
         "portal.",
         False),
    ]
    for i, (text, is_heading) in enumerate(instructions, start=1):
        cell = inst.cell(row=i, column=1, value=text)
        cell.alignment = Alignment(wrap_text=True, vertical="top")
        if is_heading:
            cell.font = Font(bold=True, size=14, color="1f4e79")

    buf = io.BytesIO()
    wb.save(buf)
    return buf.getvalue()


# --------------------------------------------------------------------------- #
# Upload reader & comparison table
# --------------------------------------------------------------------------- #

@dataclass
class ConsolidatedRow:
    municipality_id: str
    name_ar: str
    name_en: str
    capture_date: date | None
    agency_name: str | None
    metrics: dict[str, float | None] = field(default_factory=dict)
    notes: str | None = None
    source_file: str = ""


def _parse_date(value: Any) -> date | None:
    if value is None or value == "":
        return None
    if isinstance(value, datetime):
        return value.date()
    if isinstance(value, date):
        return value
    try:
        return datetime.strptime(str(value).strip()[:10], "%Y-%m-%d").date()
    except (ValueError, TypeError):
        return None


def _safe_text(value: Any) -> str:
    """Neutralise spreadsheet formula injection on export.

    Cells whose first character is one of ``= + - @`` (or a leading tab/CR
    that some clients strip) are interpreted as formulas by Excel/LibreOffice
    when re-opened. Prefix such values with a single quote so they render as
    literal text.
    """
    if value is None:
        return ""
    s = str(value)
    if s and s[0] in ("=", "+", "-", "@", "\t", "\r"):
        return "'" + s
    return s


def _parse_rate(value: Any) -> float | None:
    if value is None or value == "":
        return None
    try:
        f = float(value)
    except (TypeError, ValueError):
        return None
    if f < 0:
        return None
    return f


def _read_workbook(path: Path) -> list[ConsolidatedRow]:
    """Read one uploaded workbook and yield its rows."""
    rows: list[ConsolidatedRow] = []
    try:
        wb = load_workbook(path, data_only=True, read_only=True)
    except Exception as exc:
        logger.warning("Could not open uploaded workbook %s: %s", path, exc)
        return rows
    ws = wb["Data Entry"] if "Data Entry" in wb.sheetnames else wb.active

    columns = all_columns()
    key_index = {key: i for i, (key, *_rest) in enumerate(columns)}

    for excel_row in ws.iter_rows(min_row=2, values_only=True):
        if excel_row is None:
            continue
        # Pad row if it is shorter than the column list.
        padded = list(excel_row) + [None] * (len(columns) - len(excel_row))

        capture = _parse_date(padded[key_index["capture_date"]])
        # Only consider rows with both an ID and a capture date — a row of
        # purely municipality identifiers (the unfilled template) is ignored.
        muni_id = padded[key_index["municipality_id"]]
        if not muni_id or capture is None:
            continue

        metrics: dict[str, float | None] = {}
        for d_code, *_d in DISEASES:
            for m_code, *_m in METRICS:
                key = f"{d_code}_{m_code}"
                metrics[key] = _parse_rate(padded[key_index[key]])

        notes_val = padded[key_index["notes"]]
        rows.append(ConsolidatedRow(
            municipality_id=str(muni_id).strip(),
            name_ar=str(padded[key_index["name_ar"]] or "").strip(),
            name_en=str(padded[key_index["name_en"]] or "").strip(),
            capture_date=capture,
            agency_name=(str(padded[key_index["agency_name"]]).strip()
                         if padded[key_index["agency_name"]] else None),
            metrics=metrics,
            notes=(str(notes_val).strip() if notes_val else None),
            source_file=path.name,
        ))
    return rows


def consolidated_table() -> dict[str, Any]:
    """Read every uploaded workbook and build the comparison table.

    Returns
    -------
    dict
        ``{"rows": [...], "freshness": date|None, "upload_count": int,
           "last_upload_at": datetime|None}``

        ``rows`` is sorted alphabetically by ``name_en`` and contains the
        single most-recent capture per municipality.
    """
    UPLOAD_DIR.mkdir(parents=True, exist_ok=True)

    files = sorted(UPLOAD_DIR.glob("*.xlsx"))
    if not files:
        return {
            "rows": [],
            "freshness": None,
            "upload_count": 0,
            "last_upload_at": None,
        }

    # Process files oldest → newest by mtime so that on capture-date ties
    # the row from the most recent upload deterministically wins.
    files = sorted(files, key=lambda p: (os.path.getmtime(p), p.name))
    latest_per_muni: dict[str, ConsolidatedRow] = {}
    for f in files:
        for row in _read_workbook(f):
            existing = latest_per_muni.get(row.municipality_id)
            if existing is None:
                latest_per_muni[row.municipality_id] = row
                continue
            # Replace when the new row has a strictly newer capture date,
            # OR when the dates tie (newer upload wins because we iterate
            # files in chronological order).
            if (row.capture_date and existing.capture_date
                    and row.capture_date >= existing.capture_date):
                latest_per_muni[row.municipality_id] = row

    rows = sorted(latest_per_muni.values(), key=lambda r: r.name_en or r.municipality_id)
    freshness = max((r.capture_date for r in rows if r.capture_date),
                    default=None)
    last_upload_at = datetime.fromtimestamp(
        max(os.path.getmtime(f) for f in files)
    )
    return {
        "rows": rows,
        "freshness": freshness,
        "upload_count": len(files),
        "last_upload_at": last_upload_at,
    }


# --------------------------------------------------------------------------- #
# Export consolidated table
# --------------------------------------------------------------------------- #

def build_export_workbook(table: dict[str, Any]) -> bytes:
    """Export the consolidated comparison table back to .xlsx."""
    wb = Workbook()
    ws = wb.active
    ws.title = "Comparison"
    ws.sheet_view.rightToLeft = True

    columns = all_columns()

    # Add a freshness banner row (merged across all columns).
    freshness = table.get("freshness")
    fresh_text = (
        f"تاريخ أحدث البيانات: {freshness.isoformat() if freshness else 'غير متاح'}   |   "
        f"Latest capture date: {freshness.isoformat() if freshness else 'N/A'}   |   "
        f"Files consolidated: {table.get('upload_count', 0)}"
    )
    ws.cell(row=1, column=1, value=fresh_text)
    ws.merge_cells(
        start_row=1, start_column=1,
        end_row=1, end_column=len(columns),
    )
    banner = ws.cell(row=1, column=1)
    banner.font = Font(bold=True, color="FFFFFF", size=11)
    banner.fill = PatternFill("solid", fgColor="2e7d32")
    banner.alignment = Alignment(horizontal="center", vertical="center")
    ws.row_dimensions[1].height = 26

    # Header row at row 2.
    for col_idx, (_key, ar, en) in enumerate(columns, start=1):
        _styled_header(ws.cell(row=2, column=col_idx), ar, en)
    ws.row_dimensions[2].height = 42
    ws.freeze_panes = "F3"

    # Data rows. All free-text fields are passed through _safe_text() to
    # block CSV/XLSX formula injection from untrusted uploads.
    for row_idx, row in enumerate(table.get("rows", []), start=3):
        ws.cell(row=row_idx, column=1, value=_safe_text(row.municipality_id))
        ws.cell(row=row_idx, column=2, value=_safe_text(row.name_ar))
        ws.cell(row=row_idx, column=3, value=_safe_text(row.name_en))
        ws.cell(row=row_idx, column=4,
                value=row.capture_date.isoformat() if row.capture_date else "")
        ws.cell(row=row_idx, column=5, value=_safe_text(row.agency_name))
        col = 6
        for d_code, *_d in DISEASES:
            for m_code, *_m in METRICS:
                ws.cell(row=row_idx, column=col,
                        value=row.metrics.get(f"{d_code}_{m_code}"))
                col += 1
        ws.cell(row=row_idx, column=col, value=_safe_text(row.notes))

    # Column widths
    width_map = {
        "municipality_id": 14, "name_ar": 26, "name_en": 26,
        "capture_date": 14, "agency_name": 26, "notes": 40,
    }
    for col_idx, (key, *_rest) in enumerate(columns, start=1):
        ws.column_dimensions[get_column_letter(col_idx)].width = (
            width_map.get(key, 18)
        )

    buf = io.BytesIO()
    wb.save(buf)
    return buf.getvalue()
