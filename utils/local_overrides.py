"""Resolve dashboard indicator values from local-agency uploads.

Bridges the partner-facing Data Entry pipeline (utils/local_agency_data.py)
into the per-municipality dashboard. When a municipality has uploaded its
own measurement for an indicator, that value should override the
national-level WHO / World Bank proxy that would otherwise be applied to
every municipality identically.

Public API
----------
get_overrides_for(municipality_id) -> dict[str, dict]
    Returns a mapping ``{data_entry_indicator_code: {value, year,
    capture_date, agency, domain_key, domain_name_ar, domain_name_en}}``
    for the given municipality.  Returns an empty dict for the national
    jurisdiction or when no local data has been uploaded.

Caching
-------
A lightweight process-wide cache is invalidated whenever any of the
local-agency upload directories change (mtime check). Building the index
is fast (a few small workbooks) so a stale cache is acceptable; the
mtime invalidation guarantees correctness on the next request after an
upload completes.
"""

from __future__ import annotations

import os
from typing import Any

from utils.data_entry_domains import all_domains
from utils.local_agency_data import consolidated_table, upload_dir_for

# In-memory cache.
_INDEX: dict[str, dict[str, dict[str, Any]]] = {}
_SIGNATURE: tuple = ()


def _signature() -> tuple:
    """Cheap fingerprint of every upload dir's mtime."""
    parts = []
    for spec in all_domains():
        d = upload_dir_for(spec)
        try:
            parts.append((spec.key, os.path.getmtime(d)))
        except OSError:
            parts.append((spec.key, 0.0))
    return tuple(parts)


def _build_index() -> dict[str, dict[str, dict[str, Any]]]:
    """Walk every domain's consolidated table and bucket by municipality."""
    out: dict[str, dict[str, dict[str, Any]]] = {}
    for spec in all_domains():
        try:
            table = consolidated_table(spec)
        except Exception:
            continue
        for row in table.get("rows", []):
            mid = (row.municipality_id or "").strip()
            if not mid:
                continue
            bucket = out.setdefault(mid, {})
            for code, val in (row.metrics or {}).items():
                if val is None:
                    continue
                bucket[code] = {
                    "value": val,
                    "capture_date": row.capture_date,
                    "year": (row.capture_date.year
                             if row.capture_date else None),
                    "agency": row.agency_name,
                    "domain_key": spec.key,
                    "domain_name_ar": spec.name_ar,
                    "domain_name_en": spec.name_en,
                }
    return out


def get_overrides_for(municipality_id: str | None) -> dict[str, dict[str, Any]]:
    """Indicator values uploaded by local agencies for this municipality."""
    global _INDEX, _SIGNATURE
    if not municipality_id:
        return {}
    sig = _signature()
    if sig != _SIGNATURE:
        _INDEX = _build_index()
        _SIGNATURE = sig
    return _INDEX.get(municipality_id, {})
