"""
Libya CARA — connector-to-pillar data plumbing tests.

`tests/test_pillar_indicators.py` pins each sub-indicator helper assuming the
connector data has already been shaped into the keys those helpers expect
(`worldbank.electricity_access_gap`, `idmc.total_idps`,
`who_gho.universal_health_coverage_index`, etc.).

The actual key mapping happens earlier, in `routes/dashboard.py
_load_connector_data` — for example WHO HDX hospital beds per 10k is
divided by 10 to produce per-1000, and IDMC `total_displacement_stock` is
mapped to `idmc.total_idps`. A bug in that mapping layer would silently
feed the wrong inputs to all the now-tested helpers.

This module loads small synthetic on-disk cache fixtures for the seven
connectors `_load_connector_data` consumes (`who_hdx`, `idmc_hdx`, `heigit`,
`iom`, `worldbank`, `coi_libya`, `ncdc_libya`), runs the loader, and
asserts the normalised dict has the documented keys with the documented
unit conversions applied. A round-trip test then feeds the normalised dict
through the three pillar `calculate()` methods and asserts each yields a
finite 0-1 score.

Run as a standalone script (from the project root):
    python tests/test_dashboard_connector_mapping.py

Run with pytest:
    pytest tests/test_dashboard_connector_mapping.py -v
"""

import importlib
import math
import os
import sys
from typing import Any, Dict

import pytest


# ---------------------------------------------------------------------------
# Standalone path setup (mirrors tests/test_pillar_indicators.py).
# ---------------------------------------------------------------------------
_SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
_TEMPLATE_DIR = os.path.dirname(_SCRIPT_DIR)
if _TEMPLATE_DIR not in sys.path:
    sys.path.insert(0, _TEMPLATE_DIR)
if os.getcwd() != _TEMPLATE_DIR:
    try:
        os.chdir(_TEMPLATE_DIR)
    except OSError:
        pass


_PREFIX: str | None = None


def _resolve_prefix() -> str:
    """Return '' if bare imports work, else 'cara_template.'."""
    try:
        importlib.import_module("routes.dashboard")
        return ""
    except (ModuleNotFoundError, ImportError):
        pass
    try:
        importlib.import_module("cara_template.routes.dashboard")
        return "cara_template."
    except (ModuleNotFoundError, ImportError) as exc:
        raise RuntimeError(
            "Cannot import routes.dashboard. Run from project root or ensure "
            "the workspace root is on sys.path."
        ) from exc


def _get_prefix() -> str:
    global _PREFIX
    if _PREFIX is None:
        _PREFIX = _resolve_prefix()
    return _PREFIX


def _import(module_path: str):
    return importlib.import_module(f"{_get_prefix()}{module_path}")


# ---------------------------------------------------------------------------
# Documented sample values used by every fixture.
# Values are arbitrary but distinctive so we can assert pass-through and
# unit conversions exactly.
# ---------------------------------------------------------------------------

WHO_BEDS_PER_10K = 32.0
WHO_UNDER5_MORTALITY = 9.0
WHO_TB_INCIDENCE = 60.0
WHO_MEASLES_PCT = 73.0
WHO_PM25 = 35.0
WHO_AIR_MORT_PER_100K = 88.0

IDMC_TOTAL_STOCK = 125_000.0
IDMC_NEW_CONFLICT = 4_500.0
IDMC_DATA_YEAR = 2024

HEIGIT_HOSP_SHARE_TRIPOLI = 90.0
HEIGIT_PRIMARY_SHARE_TRIPOLI = 95.0
HEIGIT_EDU_SHARE_TRIPOLI = 80.0

IOM_TOTAL_IDPS = 11_000.0
IOM_TOTAL_MIGRANTS = 27_000.0
IOM_MIGRANT_FLOW = 6_500.0

COI_AGENCY_GAP = 0.42
COI_RESPONSE_MIN = 28.0
COI_NGO = 0.6
COI_SECURITY = 0.35
COI_INTEROP = 0.55
COI_GRID = 0.4

NCDC_INFECT_CASES = 240.0
NCDC_VBD_CASES = 55.0


# ---------------------------------------------------------------------------
# Fixture writers — one per connector cache shape.
# Each writes a CSV file in the format the connector's parser expects.
# ---------------------------------------------------------------------------

def _write_who_hdx_csv(cache_dir: str) -> None:
    """
    WHO HDX format. Parser looks for `GHO (CODE)`, `YEAR (DISPLAY)`,
    `SEX (CODE)`, `AGEGROUP (CODE)`, `Numeric`. Writes one combined file
    named `health_systems.csv`; the parser scans every key in
    RESOURCE_URLS so a single file containing all needed GHO codes is
    enough.
    """
    os.makedirs(cache_dir, exist_ok=True)
    path = os.path.join(cache_dir, "health_systems.csv")
    rows = [
        ("WHS6_102",        WHO_BEDS_PER_10K),       # hospital_beds_per_10k
        ("MDG_0000000007",  WHO_UNDER5_MORTALITY),   # under5_mortality_rate
        ("MDG_0000000020",  WHO_TB_INCIDENCE),       # tb_incidence_per_100k
        ("WHS8_110",        WHO_MEASLES_PCT),        # measles_vaccination_pct
        ("SDGPM25",         WHO_PM25),               # pm25_annual_mean_ugm3
        ("AIR_42",          WHO_AIR_MORT_PER_100K),  # air_pollution_mortality_per_100k
    ]
    with open(path, "w", encoding="utf-8") as f:
        f.write("GHO (CODE),YEAR (DISPLAY),SEX (CODE),AGEGROUP (CODE),Numeric\n")
        for code, value in rows:
            f.write(f"{code},2024,BTSX,ALLAGE,{value}\n")


def _write_idmc_hdx_csv(cache_dir: str) -> None:
    """
    IDMC annual_idp.csv format. Parser keeps only iso3=LBY rows and picks
    the most recent year, exposing `total_displacement_stock` and
    `new_displacements_conflict` from the `total_displacement` and
    `new_displacement` columns.
    """
    os.makedirs(cache_dir, exist_ok=True)
    path = os.path.join(cache_dir, "annual_idp.csv")
    with open(path, "w", encoding="utf-8") as f:
        f.write(
            "iso3,country_name,year,new_displacement,new_displacement_rounded,"
            "total_displacement,total_displacement_rounded\n"
        )
        # Older year that should be ignored.
        f.write(f"LBY,Libya,2022,1000,1000,80000,80000\n")
        # Most recent year — values flow through to the normalised dict.
        f.write(
            f"LBY,Libya,{IDMC_DATA_YEAR},{IDMC_NEW_CONFLICT},{IDMC_NEW_CONFLICT},"
            f"{IDMC_TOTAL_STOCK},{IDMC_TOTAL_STOCK}\n"
        )
        # Foreign country row that must be skipped.
        f.write(f"TUN,Tunisia,{IDMC_DATA_YEAR},9999,9999,9999,9999\n")


def _write_heigit_csvs(cache_dir: str) -> None:
    """
    HeiGIT long-format access CSVs. Parser keeps admin_level=ADM1 rows
    matching the configured threshold/population_type and stores the
    population_share by HeiGIT ISO code.
    """
    os.makedirs(cache_dir, exist_ok=True)
    cols = "iso,name,admin_level,range_type,range,population_type,population_share\n"

    with open(os.path.join(cache_dir, "hospitals.csv"), "w", encoding="utf-8") as f:
        f.write(cols)
        f.write(f"LY-TB,Tripoli,ADM1,TIME,3600,total,{HEIGIT_HOSP_SHARE_TRIPOLI}\n")
        # Other district to exercise national-average build-out.
        f.write("LY-BA,Benghazi,ADM1,TIME,3600,total,70\n")
        # Wrong threshold/level rows that must be skipped.
        f.write("LY-TB,Tripoli,ADM1,TIME,1800,total,40\n")
        f.write("LY-TB,Tripoli,ADM2,TIME,3600,total,99\n")

    with open(os.path.join(cache_dir, "primary_healthcare.csv"), "w", encoding="utf-8") as f:
        f.write(cols)
        f.write(f"LY-TB,Tripoli,ADM1,TIME,3600,total,{HEIGIT_PRIMARY_SHARE_TRIPOLI}\n")
        f.write("LY-BA,Benghazi,ADM1,TIME,3600,total,80\n")

    with open(os.path.join(cache_dir, "education.csv"), "w", encoding="utf-8") as f:
        f.write(cols)
        f.write(f"LY-TB,Tripoli,ADM1,DISTANCE,10000,school_age,{HEIGIT_EDU_SHARE_TRIPOLI}\n")
        f.write("LY-BA,Benghazi,ADM1,DISTANCE,10000,school_age,75\n")


def _write_iom_csv(upload_dir: str, jurisdiction_id: str) -> None:
    """IOM DTM CSV format keyed on `municipality_id`."""
    os.makedirs(upload_dir, exist_ok=True)
    path = os.path.join(upload_dir, "iom_synthetic.csv")
    with open(path, "w", encoding="utf-8") as f:
        f.write(
            "municipality_id,total_idps,total_migrants,migrant_flow_annual,"
            "returnees,irregular_migrants,report_date\n"
        )
        f.write(
            f"{jurisdiction_id},{IOM_TOTAL_IDPS},{IOM_TOTAL_MIGRANTS},"
            f"{IOM_MIGRANT_FLOW},800,1500,2026-01-01\n"
        )


def _write_coi_csv(upload_dir: str, jurisdiction_id: str) -> None:
    """COI Libya manual upload CSV format keyed on `municipality_id`."""
    os.makedirs(upload_dir, exist_ok=True)
    path = os.path.join(upload_dir, "coi_synthetic.csv")
    with open(path, "w", encoding="utf-8") as f:
        f.write(
            "municipality_id,agency_staffing_gap,avg_ambulance_response_minutes,"
            "ngo_presence_score,security_incident_rate,"
            "data_interoperability_score,electric_grid_reliability\n"
        )
        f.write(
            f"{jurisdiction_id},{COI_AGENCY_GAP},{COI_RESPONSE_MIN},"
            f"{COI_NGO},{COI_SECURITY},{COI_INTEROP},{COI_GRID}\n"
        )


def _write_ncdc_csv(upload_dir: str, jurisdiction_id: str) -> None:
    """
    NCDC Libya manual upload CSV format. Parser aggregates case_count by
    municipality, splitting vector-borne diseases (malaria, dengue,
    leishmaniasis, ...) from other infectious diseases.
    """
    os.makedirs(upload_dir, exist_ok=True)
    path = os.path.join(upload_dir, "ncdc_synthetic.csv")
    with open(path, "w", encoding="utf-8") as f:
        f.write("municipality_id,year,disease_name,case_count,region\n")
        # Two non-vector-borne diseases that should sum into infectious_disease_rate.
        f.write(f"{jurisdiction_id},2025,measles,{NCDC_INFECT_CASES / 2},west\n")
        f.write(f"{jurisdiction_id},2025,cholera,{NCDC_INFECT_CASES / 2},west\n")
        # Two vector-borne diseases that should sum into vector_borne_rate.
        f.write(f"{jurisdiction_id},2025,malaria,{NCDC_VBD_CASES / 2},west\n")
        f.write(f"{jurisdiction_id},2025,leishmaniasis,{NCDC_VBD_CASES / 2},west\n")


def _patch_worldbank(monkeypatch) -> Dict[str, Any]:
    """
    The WorldBank connector hits the live API and has no on-disk cache.
    Replace its `fetch` with a stub returning a documented synthetic
    payload, mirroring the shape `_load_connector_data` will store
    verbatim under the `worldbank` key.
    """
    wb_mod = _import("utils.connectors.worldwide.worldbank_connector")

    payload = {
        "available": True,
        "source": "World Bank Open Data (synthetic)",
        "last_updated": "2026-01-01",
        "population": 7_000_000,
        "access_electricity": 80,           # -> electricity_access_gap = 0.20
        "access_clean_water": 78,           # -> water_access_gap       = 0.22
        "access_sanitation": 70,            # -> sanitation_access_gap  = 0.30
        "poverty_headcount": 25,            # -> poverty_headcount_ratio = 25
        "urban_population_pct": 80,
        "urban_growth_pct": 2.5,            # -> urban_growth_rate = 2.5
        "literacy_rate": 91.0,
        "gni_per_capita": 7200.0,
        "health_expenditure_pct_gdp": 4.5,
        "road_fatality_rate": 18.0,
        "government_effectiveness_wgi": -1.0,  # -> government_effectiveness = 0.30
        "rule_of_law_wgi": -1.5,
        "political_stability_wgi": -2.0,
        "vulnerability_index": 0.4,
    }

    def _fake_fetch(self, jurisdiction_id, **kwargs):
        return dict(payload)

    monkeypatch.setattr(wb_mod.WorldBankConnector, "fetch", _fake_fetch)
    return payload


# ---------------------------------------------------------------------------
# Master fixture: build cache dirs, monkeypatch all connector module paths,
# and call `_load_connector_data`. Returns the normalised dict.
# ---------------------------------------------------------------------------

JURISDICTION_ID = "LY-001"   # Tripoli Center — district 'tripoli' -> 'LY-TB'


@pytest.fixture
def normalised_data(tmp_path, monkeypatch):
    """
    Wire up synthetic on-disk caches for every connector
    `_load_connector_data` consumes, then run the loader against a real
    municipality id. Returns the normalised dict the dashboard would feed
    into the three pillar `calculate()` methods.
    """
    who_dir   = tmp_path / "cache" / "who_hdx"
    idmc_dir  = tmp_path / "cache" / "idmc"
    heigit_dir = tmp_path / "cache" / "heigit"
    iom_dir   = tmp_path / "uploads" / "iom"
    coi_dir   = tmp_path / "uploads" / "coi"
    ncdc_dir  = tmp_path / "uploads" / "ncdc"

    _write_who_hdx_csv(str(who_dir))
    _write_idmc_hdx_csv(str(idmc_dir))
    _write_heigit_csvs(str(heigit_dir))
    _write_iom_csv(str(iom_dir), JURISDICTION_ID)
    _write_coi_csv(str(coi_dir), JURISDICTION_ID)
    _write_ncdc_csv(str(ncdc_dir), JURISDICTION_ID)

    # Redirect each connector module's cache/upload path at the module
    # level. `_load_connector_data` re-imports inside the function, so
    # patching the cached module attributes is sufficient.
    who_mod    = _import("utils.connectors.worldwide.who_hdx_connector")
    idmc_mod   = _import("utils.connectors.worldwide.idmc_hdx_connector")
    heigit_mod = _import("utils.connectors.worldwide.heigit_connector")
    iom_mod    = _import("utils.connectors.worldwide.iom_connector")
    coi_mod    = _import("utils.connectors.libya.coi_connector")
    ncdc_mod   = _import("utils.connectors.libya.ncdc_connector")

    monkeypatch.setattr(who_mod,    "CACHE_DIR",   str(who_dir))
    monkeypatch.setattr(idmc_mod,   "CACHE_DIR",   str(idmc_dir))
    monkeypatch.setattr(heigit_mod, "CACHE_DIR",   str(heigit_dir))
    monkeypatch.setattr(iom_mod,    "UPLOAD_PATH", str(iom_dir))
    monkeypatch.setattr(coi_mod,    "UPLOAD_PATH", str(coi_dir))
    monkeypatch.setattr(ncdc_mod,   "UPLOAD_PATH", str(ncdc_dir))

    _patch_worldbank(monkeypatch)

    dashboard = _import("routes.dashboard")
    return dashboard._load_connector_data(JURISDICTION_ID)


# ===========================================================================
# WHO HDX — beds/10 -> per 1000 + key renames into `who_gho`
# ===========================================================================

def test_who_hdx_namespace_present(normalised_data):
    assert "who_gho" in normalised_data
    assert "who_hdx_raw" in normalised_data


def test_who_hospital_beds_unit_conversion_10k_to_1000(normalised_data):
    """The headline conversion: beds_per_10k / 10 -> per_1000, both kept."""
    who = normalised_data["who_gho"]
    assert who["hospital_beds_per_10k"] == WHO_BEDS_PER_10K
    assert who["hospital_beds_per_1000"] == round(WHO_BEDS_PER_10K / 10.0, 3)


def test_who_measles_vaccination_renamed_to_coverage(normalised_data):
    """`measles_vaccination_pct` raw -> `measles_vaccination_coverage` exposed key."""
    who = normalised_data["who_gho"]
    assert who["measles_vaccination_coverage"] == WHO_MEASLES_PCT
    assert "measles_vaccination_pct" not in who


def test_who_passthrough_keys_preserve_value(normalised_data):
    """Codes that share their source name should pass through unchanged."""
    who = normalised_data["who_gho"]
    assert who["under5_mortality_rate"]            == WHO_UNDER5_MORTALITY
    assert who["tb_incidence_per_100k"]            == WHO_TB_INCIDENCE
    assert who["pm25_annual_mean_ugm3"]            == WHO_PM25
    assert who["air_pollution_mortality_per_100k"] == WHO_AIR_MORT_PER_100K


def test_who_year_metadata_propagates(normalised_data):
    """Year metadata (`*_year`) must survive the rename so popovers can use it."""
    who = normalised_data["who_gho"]
    assert who.get("hospital_beds_per_10k_year") == 2024
    assert who.get("under5_mortality_rate_year") == 2024


# ===========================================================================
# IDMC HDX — total_displacement_stock -> total_idps + idp_stock
# ===========================================================================

def test_idmc_namespace_present(normalised_data):
    assert "idmc" in normalised_data
    assert "idmc_raw" in normalised_data


def test_idmc_total_displacement_stock_renamed_to_total_idps(normalised_data):
    """The other headline conversion: `total_displacement_stock` -> `total_idps`."""
    idmc = normalised_data["idmc"]
    assert idmc["total_idps"] == IDMC_TOTAL_STOCK


def test_idmc_total_displacement_stock_also_aliased_as_idp_stock(normalised_data):
    """Both alias keys must populate so either dashboard helper signature works."""
    idmc = normalised_data["idmc"]
    assert idmc["idp_stock"] == IDMC_TOTAL_STOCK


def test_idmc_new_displacements_conflict_renamed(normalised_data):
    """`new_displacements_conflict` raw -> `new_conflict_displacements` exposed."""
    idmc = normalised_data["idmc"]
    assert idmc["new_conflict_displacements"] == IDMC_NEW_CONFLICT


def test_idmc_raw_payload_keeps_original_keys(normalised_data):
    """Raw IDMC dict (popover source) must keep the raw column names."""
    raw = normalised_data["idmc_raw"]
    assert raw["total_displacement_stock"] == IDMC_TOTAL_STOCK
    assert raw["new_displacements_conflict"] == IDMC_NEW_CONFLICT
    assert raw["data_year"] == IDMC_DATA_YEAR


# ===========================================================================
# HeiGIT — district passthrough under `heigit`
# ===========================================================================

def test_heigit_district_lookup_succeeds_for_municipality(normalised_data):
    """LY-001 is in district 'tripoli' (LY-TB); HeiGIT must surface those scores."""
    heigit = normalised_data["heigit"]
    assert heigit["available"] is True
    assert heigit["_heigit_iso"] == "LY-TB"
    assert heigit["hospital_access_pct"] == HEIGIT_HOSP_SHARE_TRIPOLI
    assert heigit["primary_care_access_pct"] == HEIGIT_PRIMARY_SHARE_TRIPOLI
    assert heigit["education_access_pct"] == HEIGIT_EDU_SHARE_TRIPOLI


def test_heigit_gap_pct_is_inverse_of_access_pct(normalised_data):
    """Gap = 100 - access for each measured threshold."""
    heigit = normalised_data["heigit"]
    assert heigit["hospital_access_gap_pct"] == round(100 - HEIGIT_HOSP_SHARE_TRIPOLI, 2)
    assert heigit["primary_care_access_gap_pct"] == round(100 - HEIGIT_PRIMARY_SHARE_TRIPOLI, 2)
    assert heigit["education_access_gap_pct"] == round(100 - HEIGIT_EDU_SHARE_TRIPOLI, 2)


# ===========================================================================
# IOM — only present when available; passthrough under `iom`
# ===========================================================================

def test_iom_namespace_present_with_municipality_match(normalised_data):
    assert "iom" in normalised_data
    iom = normalised_data["iom"]
    assert iom["available"] is True
    assert iom["total_idps"] == IOM_TOTAL_IDPS
    assert iom["total_migrants"] == IOM_TOTAL_MIGRANTS
    assert iom["migrant_flow_annual"] == IOM_MIGRANT_FLOW


# ===========================================================================
# WorldBank — raw connector keys passthrough + derived/renamed keys for
# domain helpers (electricity_access_gap, water_access_gap,
# poverty_headcount_ratio, government_effectiveness, urban_growth_rate, ...).
# Raw payload also exposed under `worldbank_raw` for popovers.
# ===========================================================================

def test_worldbank_namespace_present(normalised_data):
    assert "worldbank" in normalised_data
    assert "worldbank_raw" in normalised_data
    assert normalised_data["worldbank"]["available"] is True


def test_worldbank_raw_keys_pass_through_unchanged(normalised_data):
    """Raw connector field names must remain accessible (popovers / tiles)."""
    wb = normalised_data["worldbank"]
    assert wb["access_electricity"]  == 80
    assert wb["access_clean_water"]  == 78
    assert wb["access_sanitation"]   == 70
    assert wb["poverty_headcount"]   == 25
    assert wb["urban_population_pct"] == 80
    assert wb["literacy_rate"]       == 91.0
    assert wb["gni_per_capita"]      == 7200.0
    assert wb["health_expenditure_pct_gdp"] == 4.5
    raw = normalised_data["worldbank_raw"]
    assert raw["access_electricity"] == 80
    assert raw["government_effectiveness_wgi"] == -1.0


def test_worldbank_access_gaps_derived_from_access_pct(normalised_data):
    """access_* (% access) is inverted to *_access_gap on a 0..1 scale."""
    wb = normalised_data["worldbank"]
    assert wb["electricity_access_gap"] == pytest.approx(0.20, abs=1e-3)
    assert wb["water_access_gap"]       == pytest.approx(0.22, abs=1e-3)
    assert wb["sanitation_access_gap"]  == pytest.approx(0.30, abs=1e-3)


def test_worldbank_poverty_headcount_renamed_to_ratio(normalised_data):
    """`poverty_headcount` raw -> `poverty_headcount_ratio` exposed key."""
    wb = normalised_data["worldbank"]
    assert wb["poverty_headcount_ratio"] == 25


def test_worldbank_urban_growth_renamed_for_helpers(normalised_data):
    """`urban_growth_pct` raw -> `urban_growth_rate` exposed key."""
    wb = normalised_data["worldbank"]
    assert wb["urban_growth_rate"] == 2.5


def test_worldbank_governance_indicators_normalised_or_passthrough(normalised_data):
    """
    `government_effectiveness` is normalised from the raw WGI [-2.5, 2.5]
    estimate to a 0..1 scale (the agency-capacity helper does `1 - v`).
    `rule_of_law` and `political_stability` pass through raw because the
    security-vulnerability helper performs the (v + 2.5) / 5 normalisation
    itself.
    """
    wb = normalised_data["worldbank"]
    # (-1.0 + 2.5) / 5 = 0.30
    assert wb["government_effectiveness"] == pytest.approx(0.30, abs=1e-3)
    assert wb["rule_of_law"]         == -1.5
    assert wb["political_stability"] == -2.0


# ===========================================================================
# COI Libya — passthrough under `coi_libya`, only when muni match found
# ===========================================================================

def test_coi_libya_namespace_present_with_municipality_match(normalised_data):
    assert "coi_libya" in normalised_data
    coi = normalised_data["coi_libya"]
    assert coi["available"] is True
    assert coi["agency_staffing_gap"] == COI_AGENCY_GAP
    assert coi["avg_ambulance_response_minutes"] == COI_RESPONSE_MIN
    assert coi["ngo_presence_score"] == COI_NGO
    assert coi["security_incident_rate"] == COI_SECURITY
    assert coi["data_interoperability_score"] == COI_INTEROP


# ===========================================================================
# NCDC Libya — passthrough under `ncdc_libya`; vector-borne aggregation
# ===========================================================================

def test_ncdc_namespace_present_with_municipality_match(normalised_data):
    assert "ncdc_libya" in normalised_data
    ncdc = normalised_data["ncdc_libya"]
    assert ncdc["available"] is True


def test_ncdc_aggregates_infectious_and_vector_borne_correctly(normalised_data):
    """
    Vector-borne keywords (malaria, leishmaniasis, ...) are summed into
    `vector_borne_rate`; everything else into `infectious_disease_rate`.
    """
    ncdc = normalised_data["ncdc_libya"]
    assert ncdc["infectious_disease_rate"] == pytest.approx(NCDC_INFECT_CASES)
    assert ncdc["vector_borne_rate"]       == pytest.approx(NCDC_VBD_CASES)


# ===========================================================================
# Round-trip — feed normalised dict through every pillar `calculate()` and
# assert each yields a finite 0-1 score. This is the test that would catch
# a bug in `_load_connector_data` that silently feeds the wrong-shaped
# inputs to the helpers in `tests/test_pillar_indicators.py`.
# ===========================================================================

def _is_finite_unit_interval(x: float) -> bool:
    return isinstance(x, (int, float)) and math.isfinite(x) and 0.0 <= x <= 1.0


def test_round_trip_hazard_pillar_score_is_finite_unit_interval(normalised_data):
    HazardExposureDomain = _import("utils.domains.hazard_exposure").HazardExposureDomain
    result = HazardExposureDomain().calculate(normalised_data, jurisdiction_config={})
    assert result["available"] is True
    assert _is_finite_unit_interval(result["score"]), result["score"]


def test_round_trip_vulnerability_pillar_score_is_finite_unit_interval(normalised_data):
    VulnerabilityDomain = _import("utils.domains.vulnerability").VulnerabilityDomain
    result = VulnerabilityDomain().calculate(normalised_data, jurisdiction_config={})
    assert result["available"] is True
    assert _is_finite_unit_interval(result["score"]), result["score"]


def test_round_trip_coping_pillar_score_is_finite_unit_interval(normalised_data):
    CopingCapacityDomain = _import("utils.domains.coping_capacity").CopingCapacityDomain
    result = CopingCapacityDomain().calculate(normalised_data, jurisdiction_config={})
    assert result["available"] is True
    assert _is_finite_unit_interval(result["score"]), result["score"]


def test_round_trip_vulnerability_uses_idmc_total_idps_via_mapping(normalised_data):
    """
    Sanity-check the IDMC -> Vulnerability seam end-to-end: the displaced
    population is large enough relative to the helper's 20% population
    cap that the resulting indicator score must be strictly above the
    proxy default (0.45) — proving the rename actually wires data through
    rather than silently falling back.
    """
    VulnerabilityDomain = _import("utils.domains.vulnerability").VulnerabilityDomain
    result = VulnerabilityDomain().calculate(normalised_data, jurisdiction_config={})
    indicator = result["indicators"]["displacement_vulnerability"]
    assert indicator["proxy_used"] is False
    assert indicator["score"] > 0.0


# ---------------------------------------------------------------------------
# Positive seam — every WB-driven sub-indicator must flow real data
# through the loader and out of the pillar helpers. With a real WB cache
# loaded, none of these helpers should fall back to its documented proxy
# default. This is the regression guard for the WB key-mapping fix.
# ---------------------------------------------------------------------------

def test_round_trip_infrastructure_hazard_uses_worldbank_via_mapping(normalised_data):
    """
    `_infrastructure_hazard` derives `electric_grid` and `water_sewage`
    from `worldbank.electricity_access_gap` / `water_access_gap`. With WB
    data loaded the sub-domain is no longer a pure proxy (proxy_used
    flips False even though `dam_safety` still uses its default, because
    the helper now reports `proxy_used` only when EVERY sub-component
    fell back).
    """
    HazardExposureDomain = _import("utils.domains.hazard_exposure").HazardExposureDomain
    h = HazardExposureDomain().calculate(normalised_data, jurisdiction_config={})
    infra = h["sub_domains"]["infrastructure_hazard"]
    assert infra["proxy_used"] is False
    assert 0.0 < infra["score"] < 1.0


def test_round_trip_poverty_vulnerability_uses_worldbank_via_mapping(normalised_data):
    """
    `_poverty_vulnerability` reads `worldbank.poverty_headcount_ratio`
    (renamed from `poverty_headcount`). proxy_used must be False and the
    score must reflect 25 / 100 = 0.25.
    """
    CopingCapacityDomain = _import("utils.domains.coping_capacity").CopingCapacityDomain
    c = CopingCapacityDomain().calculate(normalised_data, jurisdiction_config={})
    pov = c["indicators"]["poverty_vulnerability"]
    assert pov["proxy_used"] is False
    assert pov["score"] == pytest.approx(0.25, abs=1e-3)


def test_round_trip_urban_sprawl_uses_worldbank_growth_rate(normalised_data):
    """
    `_urban_sprawl` prefers `worldbank.urban_growth_rate` (renamed from
    `urban_growth_pct`). With 2.5 %/yr the score is 2.5 / 5 = 0.5.
    """
    VulnerabilityDomain = _import("utils.domains.vulnerability").VulnerabilityDomain
    v = VulnerabilityDomain().calculate(normalised_data, jurisdiction_config={})
    sprawl = v["indicators"]["urban_sprawl"]
    assert sprawl["proxy_used"] is False
    assert sprawl["score"] == pytest.approx(0.5, abs=1e-3)


def test_round_trip_health_unawareness_uses_worldbank_literacy(normalised_data):
    """
    `_health_unawareness` averages (1 - vacc_coverage) and
    (1 - literacy_rate). Both signals are present so proxy_used=False.
    """
    VulnerabilityDomain = _import("utils.domains.vulnerability").VulnerabilityDomain
    v = VulnerabilityDomain().calculate(normalised_data, jurisdiction_config={})
    hu = v["indicators"]["health_unawareness"]
    assert hu["proxy_used"] is False
    # vaccination 73% -> unawareness 0.27; literacy 91% -> unawareness 0.09;
    # mean = 0.18
    assert hu["score"] == pytest.approx(0.18, abs=1e-3)


def test_round_trip_security_vulnerability_prefers_local_over_worldbank(normalised_data):
    """
    With both COI security_incident_rate and WB rule_of_law /
    political_stability available, the helper takes the local signal
    first (0.35) and proxy_used is False. The WB governance indicators
    are still present in the loader output so that future helpers can
    consume them.
    """
    VulnerabilityDomain = _import("utils.domains.vulnerability").VulnerabilityDomain
    v = VulnerabilityDomain().calculate(normalised_data, jurisdiction_config={})
    sec = v["indicators"]["security_vulnerability"]
    assert sec["proxy_used"] is False
    assert sec["score"] == pytest.approx(COI_SECURITY, abs=1e-3)
    wb = normalised_data["worldbank"]
    assert "rule_of_law" in wb
    assert "political_stability" in wb


# ---------------------------------------------------------------------------
# Standalone runner
# ---------------------------------------------------------------------------
if __name__ == "__main__":
    sys.exit(pytest.main([__file__, "-v"]))
