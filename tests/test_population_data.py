"""
Libya CARA — regression tests for municipality population data.

These tests pin the schema and consistency invariants enforced by
`scripts/refresh_population.py`. They do not require any external network
access; they only inspect `data/libya_municipalities.json` as it stands on
disk after the most recent refresh.

Run as a standalone script (from the project root):
    python tests/test_population_data.py

Run with pytest:
    pytest tests/test_population_data.py -v
"""

import json
import os
import sys
from pathlib import Path

# Standalone path setup (mirrors tests/test_inform.py).
_SCRIPT_DIR = Path(__file__).resolve().parent
_TEMPLATE_DIR = _SCRIPT_DIR.parent
if str(_TEMPLATE_DIR) not in sys.path:
    sys.path.insert(0, str(_TEMPLATE_DIR))
if os.getcwd() != str(_TEMPLATE_DIR):
    try:
        os.chdir(_TEMPLATE_DIR)
    except OSError:
        pass

MUNICIPALITIES_FILE = Path("data/libya_municipalities.json")

# UN World Population Prospects 2024 medium variant for Libya.
UN_WPP_2024_LIBYA = 7_458_567

# Allowed status values for the population_status field.
VALID_STATUS = {
    "verified_ocha",
    "sub_baladiya_estimate",
    "estimated_pending_verification",
}

VALID_METHOD = {
    "hdx_ocha_baladiya",
    "expert_estimate",
}


def _load() -> dict:
    with open(MUNICIPALITIES_FILE, encoding="utf-8") as f:
        return json.load(f)


# ---------------------------------------------------------------------------
# File-level / schema invariants
# ---------------------------------------------------------------------------


def test_municipalities_file_loads():
    data = _load()
    assert "municipalities" in data
    assert "_metadata" in data
    assert isinstance(data["municipalities"], list)
    assert len(data["municipalities"]) >= 100, (
        f"Expected at least 100 entries; got {len(data['municipalities'])}"
    )


def test_every_entry_has_required_population_schema():
    """Every entry must declare the four documented provenance fields."""
    data = _load()
    required = {"population", "population_year", "population_source",
                "population_method", "population_status"}
    missing_per_entry = []
    for m in data["municipalities"]:
        miss = required - set(m.keys())
        if miss:
            missing_per_entry.append((m.get("id", "?"), sorted(miss)))
    assert not missing_per_entry, (
        f"Entries missing required fields: {missing_per_entry[:5]} "
        f"({len(missing_per_entry)} total)"
    )


def test_population_values_are_positive_integers():
    data = _load()
    for m in data["municipalities"]:
        pop = m["population"]
        assert isinstance(pop, int), f"{m['id']}: population must be int, got {type(pop).__name__}"
        assert pop > 0, f"{m['id']}: population must be > 0, got {pop}"


def test_population_year_is_plausible():
    data = _load()
    for m in data["municipalities"]:
        year = m["population_year"]
        assert isinstance(year, int)
        assert 2000 <= year <= 2030, f"{m['id']}: implausible population_year {year}"


def test_population_status_is_valid_enum():
    data = _load()
    for m in data["municipalities"]:
        status = m["population_status"]
        assert status in VALID_STATUS, (
            f"{m['id']}: invalid population_status {status!r}; "
            f"allowed: {sorted(VALID_STATUS)}"
        )


def test_population_method_is_valid_enum():
    data = _load()
    for m in data["municipalities"]:
        method = m["population_method"]
        assert method in VALID_METHOD, (
            f"{m['id']}: invalid population_method {method!r}; "
            f"allowed: {sorted(VALID_METHOD)}"
        )


def test_population_source_is_documented_string():
    """Source string must be non-empty and either name OCHA HNO or be an estimate."""
    data = _load()
    for m in data["municipalities"]:
        src = m["population_source"]
        assert isinstance(src, str) and src, f"{m['id']}: empty population_source"
        if m["population_status"] == "verified_ocha":
            assert "OCHA" in src and "HNO" in src, (
                f"{m['id']}: verified_ocha entry must cite OCHA HNO; got {src!r}"
            )


def test_status_method_consistency():
    """verified_ocha entries use hdx_ocha_baladiya; others use expert_estimate."""
    data = _load()
    for m in data["municipalities"]:
        if m["population_status"] == "verified_ocha":
            assert m["population_method"] == "hdx_ocha_baladiya", (
                f"{m['id']}: verified_ocha must use hdx_ocha_baladiya method"
            )
        else:
            assert m["population_method"] == "expert_estimate", (
                f"{m['id']}: non-verified must use expert_estimate method"
            )


def test_verified_entries_carry_ocha_pcode():
    """Every verified entry records the upstream OCHA PCode for traceability."""
    data = _load()
    for m in data["municipalities"]:
        if m["population_status"] == "verified_ocha":
            pc = m.get("population_ocha_pcode", "")
            assert isinstance(pc, str) and pc.startswith("LY") and len(pc) == 8, (
                f"{m['id']}: verified entry must carry an OCHA PCode (LYxxxxxx); got {pc!r}"
            )


# ---------------------------------------------------------------------------
# Cross-entry / national totals
# ---------------------------------------------------------------------------


def test_naive_sum_double_counts_sub_baladiya_overlays():
    """A naive sum across ALL entries over-counts because sub-baladiya
    overlays in Tripoli/Benghazi live inside their parent baladiya which is
    already counted in the verified_ocha set. This test pins the size of
    that double-count so any future refactor that accidentally uses the
    naive sum for national rollups will be loud.
    """
    data = _load()
    naive = sum(m["population"] for m in data["municipalities"])
    deduped = sum(
        m["population"] for m in data["municipalities"]
        if m.get("population_in_national_total", True)
    )
    overlay = naive - deduped
    assert overlay > 0, (
        "Sub-baladiya overlays should add a measurable double-count above "
        "the deduped total; got 0 overlay which means the flag may be "
        "missing or sub-baladiya entries have no population set."
    )
    assert deduped < naive, (
        f"Deduped national total ({deduped:,}) must be strictly less than "
        f"naive sum ({naive:,})."
    )


def test_deduped_national_total_within_range_of_un_wpp_2024():
    """The deduplicated sum (excluding sub-baladiya overlays) must land
    within 80-105% of UN WPP 2024.

    OCHA HNO 2021 covers 100 of Libya's 148 baladiyas; only 59 are matched
    in this file, with 29 small villages providing workshop estimates. So
    the deduped figure is expected to fall a few percent BELOW UN WPP
    (currently ~89%) — the missing ~10% reflects the 41 unmatched OCHA
    baladiyas that still need to be added. The 105% upper bound catches
    any future regression that re-introduces overlay double-counting.
    """
    data = _load()
    deduped = sum(
        m["population"] for m in data["municipalities"]
        if m.get("population_in_national_total", True)
    )
    pct = 100 * deduped / UN_WPP_2024_LIBYA
    assert 80 <= pct <= 105, (
        f"Deduped national total {deduped:,} is {pct:.1f}% of UN WPP 2024 "
        f"({UN_WPP_2024_LIBYA:,}); expected 80-105%"
    )


def test_metadata_national_total_deduped_matches_computed_value():
    """_metadata.national_total_deduped must equal the runtime-computed
    deduped sum so dashboards and downstream rollups can rely on it
    without recomputing.
    """
    data = _load()
    md_value = data["_metadata"].get("national_total_deduped")
    computed = sum(
        m["population"] for m in data["municipalities"]
        if m.get("population_in_national_total", True)
    )
    assert md_value == computed, (
        f"_metadata.national_total_deduped ({md_value}) does not match "
        f"runtime-computed deduped sum ({computed})"
    )


def test_every_entry_has_population_in_national_total_flag():
    """Every entry must declare whether it counts in the national total."""
    data = _load()
    missing = [m["id"] for m in data["municipalities"]
               if "population_in_national_total" not in m]
    assert not missing, (
        f"{len(missing)} entries missing population_in_national_total flag: "
        f"{missing[:5]}"
    )


def test_sub_baladiya_entries_excluded_from_national_total():
    """Sub-baladiya overlays MUST be flagged population_in_national_total=False
    because their parent baladiya population is already counted via the
    OCHA verified set (Tripoli LY021104 contains LY-009..LY-014;
    Benghazi LY010304 contains LY-054..LY-062).
    """
    data = _load()
    bad = [
        m["id"] for m in data["municipalities"]
        if m.get("population_status") == "sub_baladiya_estimate"
        and m.get("population_in_national_total") is not False
    ]
    assert not bad, (
        f"Sub-baladiya entries must have population_in_national_total=False; "
        f"violators: {bad}"
    )


def test_verified_and_estimated_entries_count_in_national_total():
    """verified_ocha and estimated_pending_verification entries represent
    real, independent baladiyas and MUST count in the national total.
    """
    data = _load()
    bad = [
        m["id"] for m in data["municipalities"]
        if m.get("population_status") in {"verified_ocha", "estimated_pending_verification"}
        and m.get("population_in_national_total") is not True
    ]
    assert not bad, (
        f"verified_ocha/estimated_pending_verification entries must have "
        f"population_in_national_total=True; violators: {bad}"
    )


def test_verified_entries_carry_match_confidence():
    """Every verified_ocha entry should declare its mapping confidence
    so auditors can see which links are exact, high-confidence, or
    approximate (closest-baladiya heuristic)."""
    data = _load()
    valid = {"exact", "high", "approximate"}
    bad = []
    for m in data["municipalities"]:
        if m.get("population_status") != "verified_ocha":
            continue
        c = m.get("population_match_confidence")
        if c not in valid:
            bad.append((m["id"], c))
    assert not bad, (
        f"verified_ocha entries with missing/invalid population_match_confidence "
        f"(must be one of {valid}): {bad[:5]}"
    )


def test_national_block_population_estimate_matches_metadata():
    """data['national']['population_estimate'] must equal
    _metadata.population_estimate so the national jurisdiction block and
    metadata cannot drift apart.
    """
    data = _load()
    nat = data.get("national", {}).get("population_estimate")
    md = data.get("_metadata", {}).get("population_estimate")
    assert nat == md, (
        f"national.population_estimate ({nat}) and "
        f"_metadata.population_estimate ({md}) must agree."
    )


def test_data_gap_note_reflects_current_count():
    """data_gap_note should mention the current_count so it doesn't go
    stale when entries are added or removed."""
    data = _load()
    md = data["_metadata"]
    cc = md.get("current_count", 0)
    note = md.get("data_gap_note", "")
    assert str(cc) in note, (
        f"data_gap_note should reference current_count ({cc}); got: {note!r}"
    )


def test_majority_of_entries_are_ocha_verified():
    """A solid majority of the 106 entries (>= 55) should be OCHA-verified.

    The current coverage is 59 (Apr 2026): the OCHA HNO 2021 file has 100
    baladiyas, but 18 of our entries are sub-baladiya muhalla zones in
    Tripoli/Benghazi and 29 are small villages outside HNO scope. The 55
    floor leaves headroom for one or two future re-classifications without
    triggering a false-positive regression.
    """
    data = _load()
    n = sum(1 for m in data["municipalities"]
            if m["population_status"] == "verified_ocha")
    assert n >= 55, f"Only {n} entries are OCHA-verified; expected >= 55"


def test_no_two_entries_share_an_ocha_pcode():
    """Each OCHA baladiya should map to at most one of our entries."""
    data = _load()
    pcode_to_ids = {}
    for m in data["municipalities"]:
        pc = m.get("population_ocha_pcode")
        if pc:
            pcode_to_ids.setdefault(pc, []).append(m["id"])
    dups = {pc: ids for pc, ids in pcode_to_ids.items() if len(ids) > 1}
    assert not dups, f"Duplicate OCHA PCode mappings: {dups}"


# ---------------------------------------------------------------------------
# Metadata
# ---------------------------------------------------------------------------


def test_metadata_records_provenance():
    data = _load()
    md = data["_metadata"]
    assert md.get("population_estimate") == UN_WPP_2024_LIBYA, (
        f"_metadata.population_estimate must be UN WPP 2024 ({UN_WPP_2024_LIBYA}); "
        f"got {md.get('population_estimate')}"
    )
    assert "UN World Population Prospects" in md.get("population_estimate_source", "")
    prov = md.get("population_provenance", {})
    assert "OCHA" in prov.get("primary", "")
    assert "CC BY" in prov.get("primary_license", "")
    assert prov.get("primary_url", "").startswith("https://data.humdata.org/")


# ---------------------------------------------------------------------------
# Standalone runner
# ---------------------------------------------------------------------------
if __name__ == "__main__":
    import pytest
    sys.exit(pytest.main([__file__, "-v"]))
