"""Local-agency data ingestion engine — domain-driven.

This module is **schema-agnostic**: it consumes a :class:`DomainSpec` from
:mod:`utils.data_entry_domains` and produces

1. the downloadable Excel template that local response agencies fill in
   (one row per Libyan municipality, bilingual headers, RTL, validations,
   per-domain Instructions sheet);
2. a consolidator that reads every workbook in the per-domain upload
   directory and returns the most-recent capture per municipality
   (deterministic tie-break by upload mtime so re-submissions on the same
   day overwrite older entries from earlier files);
3. an export workbook that mirrors the comparison table back to .xlsx, with
   spreadsheet-formula injection neutralised on every text cell.

All five workshop domains (infectious disease, vector-borne disease, NCDs,
MNCH, environmental health) — and any future ones added to ``DOMAINS`` —
are handled by this single pipeline.
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
from openpyxl.packaging.custom import CustomPropertyList, StringProperty
from openpyxl.styles import Alignment, Font, PatternFill, Side, Border
from openpyxl.utils import get_column_letter
from openpyxl.worksheet.datavalidation import DataValidation

from utils.data_entry_domains import DomainSpec, Indicator

# Custom workbook property used to identify which domain a template / upload
# belongs to. The ``domain_upload`` route checks this on every upload so that
# the infectious-disease template cannot be silently mis-routed to MNCH (or
# any other domain whose column count happens to match).
DOMAIN_PROPERTY_NAME = "cara_libya_domain_key"

# Earliest date we accept on the server side. Excel-side validation enforces
# the same bound, but we mirror it here so a user who bypasses the workbook
# validation cannot poison the consolidated table with year-1900 rows.
EARLIEST_CAPTURE_DATE = date(2000, 1, 1)

logger = logging.getLogger(__name__)

# --------------------------------------------------------------------------- #
# Constants
# --------------------------------------------------------------------------- #

UPLOAD_ROOT = Path("data/uploads/local_agencies")
MUNICIPALITIES_FILE = Path("data/libya_municipalities.json")

# Fixed columns that come before the indicator block, in order.
FIXED_COLUMNS: list[tuple[str, str, str]] = [
    ("municipality_id", "رمز البلدية",            "Municipality ID"),
    ("name_ar",         "اسم البلدية (عربي)",     "Municipality (Arabic)"),
    ("name_en",         "اسم البلدية (إنجليزي)",  "Municipality (English)"),
    ("capture_date",    "تاريخ جمع البيانات",     "Date of Data Capture (YYYY-MM-DD)"),
    ("agency_name",     "اسم الجهة المُبلِّغة",    "Reporting Agency"),
]

NOTES_COLUMN: tuple[str, str, str] = (
    "notes", "ملاحظات / تباينات في البيانات",
    "Notes / Data Discrepancies",
)


def _indicator_header(ind: Indicator) -> tuple[str, str]:
    """Build the bilingual two-line header for an indicator column.

    The header always carries the unit so reporting agencies do not have to
    refer back to a separate codebook while filling the template.
    """
    if ind.group_ar:
        ar = f"{ind.group_ar} — {ind.name_ar} ({ind.unit_ar})"
        en = f"{ind.group_en} — {ind.name_en} ({ind.unit_en})"
    else:
        ar = f"{ind.name_ar} ({ind.unit_ar})"
        en = f"{ind.name_en} ({ind.unit_en})"
    return ar, en


def all_columns(spec: DomainSpec) -> list[tuple[str, str, str]]:
    """Full ordered list of (key, ar_label, en_label) tuples for a domain."""
    cols: list[tuple[str, str, str]] = list(FIXED_COLUMNS)
    for ind in spec.indicators:
        ar, en = _indicator_header(ind)
        cols.append((ind.code, ar, en))
    cols.append(NOTES_COLUMN)
    return cols


def upload_dir_for(spec: DomainSpec) -> Path:
    """Per-domain upload directory under ``data/uploads/local_agencies/``."""
    safe = spec.key.replace("-", "_")
    return UPLOAD_ROOT / safe


# --------------------------------------------------------------------------- #
# Municipality loader
# --------------------------------------------------------------------------- #

def _load_municipalities() -> list[dict[str, Any]]:
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
# Helpers
# --------------------------------------------------------------------------- #

def _safe_text(value: Any) -> str:
    """Neutralise spreadsheet formula injection on export.

    Cells whose first character is ``= + - @`` (or a leading tab/CR that
    some clients strip) are interpreted as formulas by Excel/LibreOffice
    when re-opened. Prefix such values with a single quote so they render
    as literal text.
    """
    if value is None:
        return ""
    s = str(value)
    if s and s[0] in ("=", "+", "-", "@", "\t", "\r"):
        return "'" + s
    return s


def _styled_header(cell, ar_label: str, en_label: str) -> None:
    cell.value = f"{ar_label}\n{en_label}"
    cell.font = Font(name="Calibri", bold=True, size=11, color="FFFFFF")
    cell.fill = PatternFill("solid", fgColor="1f4e79")
    cell.alignment = Alignment(
        wrap_text=True, vertical="center", horizontal="center"
    )
    thin = Side(border_style="thin", color="BFBFBF")
    cell.border = Border(left=thin, right=thin, top=thin, bottom=thin)


# --------------------------------------------------------------------------- #
# Template builder
# --------------------------------------------------------------------------- #

def build_template_workbook(spec: DomainSpec) -> bytes:
    """Build the Excel template that agencies download to fill in.

    Returns
    -------
    bytes
        Raw .xlsx bytes ready for Flask's ``send_file``.
    """
    wb = Workbook()
    ws = wb.active
    ws.title = "Data Entry"
    ws.sheet_view.rightToLeft = True

    columns = all_columns(spec)

    # Header row.
    for col_idx, (_key, ar, en) in enumerate(columns, start=1):
        _styled_header(ws.cell(row=1, column=col_idx), ar, en)

    # Pre-populate municipality rows.
    municipalities = _load_municipalities()
    for row_idx, m in enumerate(municipalities, start=2):
        ws.cell(row=row_idx, column=1, value=_safe_text(m.get("id", "")))
        ws.cell(row=row_idx, column=2, value=_safe_text(m.get("name_ar", "")))
        ws.cell(row=row_idx, column=3, value=_safe_text(m.get("name_en", "")))

    # Column widths.
    width_map = {
        "municipality_id": 14, "name_ar": 26, "name_en": 26,
        "capture_date": 18, "agency_name": 28, "notes": 40,
    }
    for col_idx, (key, _ar, _en) in enumerate(columns, start=1):
        ws.column_dimensions[get_column_letter(col_idx)].width = (
            width_map.get(key, 22)
        )

    # Frozen header + first 5 fixed columns.
    ws.freeze_panes = "F2"
    ws.row_dimensions[1].height = 56

    # Date validation on the capture-date column.
    capture_col_idx = next(
        i for i, (k, *_rest) in enumerate(columns, start=1)
        if k == "capture_date"
    )
    capture_letter = get_column_letter(capture_col_idx)
    last_row = max(2 + len(municipalities), 200)
    date_dv = DataValidation(
        type="date", operator="greaterThan", formula1="2000-01-01",
        allow_blank=True, showErrorMessage=True,
        errorTitle="Invalid date",
        error="Use a real date on or after 2000-01-01 (format YYYY-MM-DD).",
    )
    date_dv.add(f"{capture_letter}2:{capture_letter}{last_row}")
    ws.add_data_validation(date_dv)

    # Numeric validation per indicator (each indicator may have its own
    # max bound, e.g. percentages cap at 100).
    indicator_cols: dict[str, int] = {
        key: idx for idx, (key, *_r) in enumerate(columns, start=1)
        if key not in {"municipality_id", "name_ar", "name_en",
                       "capture_date", "agency_name", "notes"}
    }
    for ind in spec.indicators:
        col_idx = indicator_cols[ind.code]
        letter = get_column_letter(col_idx)
        if ind.max_value is None:
            dv = DataValidation(
                type="decimal", operator="greaterThanOrEqual",
                formula1=ind.min_value, allow_blank=True,
                showErrorMessage=True, errorTitle="Invalid value",
                error=f"Value must be ≥ {ind.min_value}.",
            )
        else:
            dv = DataValidation(
                type="decimal", operator="between",
                formula1=ind.min_value, formula2=ind.max_value,
                allow_blank=True, showErrorMessage=True,
                errorTitle="Invalid value",
                error=(f"Value must be between {ind.min_value} "
                       f"and {ind.max_value}."),
            )
        dv.add(f"{letter}2:{letter}{last_row}")
        ws.add_data_validation(dv)

    # Embed the domain key as a workbook custom property so the upload route
    # can verify the file was generated for this domain. Robust against
    # cosmetic edits to the header row.
    props = CustomPropertyList()
    props.append(StringProperty(name=DOMAIN_PROPERTY_NAME, value=spec.key))
    wb.custom_doc_props = props

    # Instructions sheet — bilingual, RTL.
    inst = wb.create_sheet("Instructions")
    inst.sheet_view.rightToLeft = True
    inst.column_dimensions["A"].width = 110
    instructions: list[tuple[str, bool]] = [
        (f"{spec.name_ar} — التعليمات", True),
        (f"{spec.name_en} — Instructions", True),
        ("", False),
        ("١. لا تُعدِّل صف الترويسة أو ترتيب الأعمدة.", False),
        ("1. Do not modify the header row or the column order.", False),
        ("", False),
        ("٢. تاريخ جمع البيانات بصيغة YYYY-MM-DD (مثال: 2026-04-23).", False),
        ("2. Date of Data Capture must follow the format YYYY-MM-DD "
         "(e.g. 2026-04-23).", False),
        ("", False),
        ("٣. وحدة كل عمود مذكورة بين قوسين في الترويسة. اترك الخلية فارغة "
         "إذا لم تتوفر البيانات — لا تكتب صفراً ولا «N/A».", False),
        ("3. The unit for each column is shown in parentheses in the "
         "header. Leave the cell empty if data is unavailable — do NOT "
         "enter zero or 'N/A'.", False),
        ("", False),
        ("٤. أَدخِل صفّاً واحداً لكل بلدية لكل تاريخ جمع. لإرسال تحديث "
         "أحدث، أَضِف صفّاً جديداً — لا تَستبدل الصف القديم.", False),
        ("4. Enter one row per municipality per capture date. To submit "
         "an update later, add a new row — do not overwrite the old row.",
         False),
        ("", False),
        ("٥. استخدم حقل «الملاحظات» للإشارة إلى أيّ تباين في البيانات أو "
         "ظرف خاص (نقص في الإبلاغ، تفشٍّ موضعي، تغيير منهجي…).", False),
        ("5. Use the Notes field to flag any data discrepancies or "
         "special circumstances (under-reporting, localised outbreak, "
         "methodology change, etc.).", False),
        ("", False),
        ("٦. عند الانتهاء، احفظ الملف بصيغة .xlsx وارفعه إلى البوابة.",
         False),
        ("6. When done, save the file as .xlsx and upload it through the "
         "portal.", False),
        ("", False),
        (f"دور هذا المجال في INFORM: {spec.inform_role_ar}", False),
        (f"INFORM linkage: {spec.inform_role_en}", False),
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
        d = value.date()
    elif isinstance(value, date):
        d = value
    else:
        try:
            d = datetime.strptime(str(value).strip()[:10], "%Y-%m-%d").date()
        except (ValueError, TypeError):
            return None
    # Reject dates outside the plausible window — guards against bypassed
    # Excel validation poisoning the comparison table.
    if d < EARLIEST_CAPTURE_DATE:
        return None
    if d > date.today():
        return None
    return d


def workbook_domain_key(raw: bytes) -> str | None:
    """Read the ``cara_libya_domain_key`` custom property from a workbook
    given its raw bytes. Returns ``None`` if absent or unreadable.

    Used by the upload route to confirm an uploaded file was generated for
    the same domain it is being uploaded to.
    """
    try:
        wb = load_workbook(io.BytesIO(raw), read_only=True, data_only=True)
    except Exception:
        return None
    try:
        container = wb.custom_doc_props
        items = getattr(container, "props", None) or []
        for prop in items:
            if getattr(prop, "name", None) == DOMAIN_PROPERTY_NAME:
                return str(prop.value) if prop.value is not None else None
    except Exception:
        return None
    return None


def _parse_value(value: Any, ind: Indicator) -> float | None:
    if value is None or value == "":
        return None
    try:
        f = float(value)
    except (TypeError, ValueError):
        return None
    if f < ind.min_value:
        return None
    if ind.max_value is not None and f > ind.max_value:
        return None
    return f


def _read_workbook(path: Path, spec: DomainSpec) -> list[ConsolidatedRow]:
    rows: list[ConsolidatedRow] = []
    try:
        wb = load_workbook(path, data_only=True, read_only=True)
    except Exception as exc:
        logger.warning("Could not open uploaded workbook %s: %s", path, exc)
        return rows
    ws = wb["Data Entry"] if "Data Entry" in wb.sheetnames else wb.active

    columns = all_columns(spec)
    key_index = {key: i for i, (key, *_rest) in enumerate(columns)}

    for excel_row in ws.iter_rows(min_row=2, values_only=True):
        if excel_row is None:
            continue
        padded = list(excel_row) + [None] * (len(columns) - len(excel_row))

        capture = _parse_date(padded[key_index["capture_date"]])
        muni_id = padded[key_index["municipality_id"]]
        if not muni_id or capture is None:
            continue

        metrics: dict[str, float | None] = {}
        for ind in spec.indicators:
            metrics[ind.code] = _parse_value(padded[key_index[ind.code]], ind)

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


def consolidated_table(spec: DomainSpec) -> dict[str, Any]:
    """Read every uploaded workbook for this domain and consolidate."""
    upload_dir = upload_dir_for(spec)
    upload_dir.mkdir(parents=True, exist_ok=True)

    files = sorted(upload_dir.glob("*.xlsx"))
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
        for row in _read_workbook(f, spec):
            existing = latest_per_muni.get(row.municipality_id)
            if existing is None:
                latest_per_muni[row.municipality_id] = row
                continue
            if (row.capture_date and existing.capture_date
                    and row.capture_date >= existing.capture_date):
                latest_per_muni[row.municipality_id] = row

    rows = sorted(latest_per_muni.values(),
                  key=lambda r: r.name_en or r.municipality_id)
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

def build_export_workbook(spec: DomainSpec, table: dict[str, Any]) -> bytes:
    """Export the consolidated comparison table back to .xlsx."""
    wb = Workbook()
    ws = wb.active
    ws.title = "Comparison"
    ws.sheet_view.rightToLeft = True

    columns = all_columns(spec)

    # Freshness banner (merged across all columns).
    freshness = table.get("freshness")
    fresh_text = (
        f"{spec.name_ar}   |   {spec.name_en}   ||   "
        f"تاريخ أحدث البيانات: {freshness.isoformat() if freshness else 'غير متاح'}   |   "
        f"Latest capture date: {freshness.isoformat() if freshness else 'N/A'}   |   "
        f"Files consolidated: {table.get('upload_count', 0)}"
    )
    ws.cell(row=1, column=1, value=fresh_text)
    ws.merge_cells(start_row=1, start_column=1,
                   end_row=1, end_column=len(columns))
    banner = ws.cell(row=1, column=1)
    banner.font = Font(bold=True, color="FFFFFF", size=11)
    banner.fill = PatternFill("solid", fgColor="2e7d32")
    banner.alignment = Alignment(horizontal="center", vertical="center")
    ws.row_dimensions[1].height = 26

    # Header row at row 2.
    for col_idx, (_key, ar, en) in enumerate(columns, start=1):
        _styled_header(ws.cell(row=2, column=col_idx), ar, en)
    ws.row_dimensions[2].height = 56
    ws.freeze_panes = "F3"

    # Data rows. All free-text fields go through _safe_text().
    indicator_codes = [ind.code for ind in spec.indicators]
    for row_idx, row in enumerate(table.get("rows", []), start=3):
        ws.cell(row=row_idx, column=1, value=_safe_text(row.municipality_id))
        ws.cell(row=row_idx, column=2, value=_safe_text(row.name_ar))
        ws.cell(row=row_idx, column=3, value=_safe_text(row.name_en))
        ws.cell(row=row_idx, column=4,
                value=row.capture_date.isoformat() if row.capture_date else "")
        ws.cell(row=row_idx, column=5, value=_safe_text(row.agency_name))
        col = 6
        for code in indicator_codes:
            ws.cell(row=row_idx, column=col, value=row.metrics.get(code))
            col += 1
        ws.cell(row=row_idx, column=col, value=_safe_text(row.notes))

    # Column widths.
    width_map = {
        "municipality_id": 14, "name_ar": 26, "name_en": 26,
        "capture_date": 14, "agency_name": 26, "notes": 40,
    }
    for col_idx, (key, *_rest) in enumerate(columns, start=1):
        ws.column_dimensions[get_column_letter(col_idx)].width = (
            width_map.get(key, 22)
        )

    buf = io.BytesIO()
    wb.save(buf)
    return buf.getvalue()
