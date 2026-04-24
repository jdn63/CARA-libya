"""
Libya CARA — per-indicator regression tests for the three INFORM pillar
domain modules.

The existing tests/test_inform.py covers the cube-root composition and the
end-to-end pillar pipeline on the all-proxy fallback path. It does NOT
exercise the dozen-plus sub-indicator helpers inside the pillar modules,
so a bug in any one of them would still produce an in-range pillar score
and a plausible-looking headline INFORM number.

This module pins each sub-indicator helper in the three Libya pillar
domain modules with at least one "real data present" case and one
"data missing -> proxy" case, asserting both the returned 0-1 score and
the proxy_used flag. It also pins the per-domain _weighted_average
helper with fully-populated, partially-populated, and all-missing inputs.

Run as a standalone script (from the project root):
    python tests/test_pillar_indicators.py

Run with pytest:
    pytest tests/test_pillar_indicators.py -v
"""

import importlib
import math
import os
import sys

# ---------------------------------------------------------------------------
# Standalone path setup (mirrors tests/test_inform.py).
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
        importlib.import_module("utils.domains.hazard_exposure")
        return ""
    except (ModuleNotFoundError, ImportError):
        pass
    try:
        importlib.import_module("cara_template.utils.domains.hazard_exposure")
        return "cara_template."
    except (ModuleNotFoundError, ImportError) as exc:
        raise RuntimeError(
            "Cannot import utils.domains.hazard_exposure. Run from project "
            "root or ensure the workspace root is on sys.path."
        ) from exc


def _get_prefix() -> str:
    global _PREFIX
    if _PREFIX is None:
        _PREFIX = _resolve_prefix()
    return _PREFIX


def _import(module_path: str):
    return importlib.import_module(f"{_get_prefix()}{module_path}")


# ---------------------------------------------------------------------------
# Helpers — instantiate one of each pillar domain.
# ---------------------------------------------------------------------------

def _hazard():
    return _import("utils.domains.hazard_exposure").HazardExposureDomain()


def _vuln():
    return _import("utils.domains.vulnerability").VulnerabilityDomain()


def _coping():
    return _import("utils.domains.coping_capacity").CopingCapacityDomain()


def _approx(actual: float, expected: float, tol: float = 1e-3) -> bool:
    return math.isclose(actual, expected, abs_tol=tol)


# ===========================================================================
# Pillar 1 — Hazard & Exposure sub-indicators
# ===========================================================================

# --- _infrastructure_hazard ------------------------------------------------

def test_infrastructure_hazard_real_data_uses_primary_sources():
    """All three sub-scores extracted from connector data, no proxy."""
    h = _hazard()
    score, proxy = h._infrastructure_hazard({
        'em_dat':    {'dam_failure_score': 0.7},
        'worldbank': {'electricity_access_gap': 0.6, 'water_access_gap': 0.5},
    })
    # weighted: 0.333*(0.7+0.6+0.5) = 0.5994
    assert _approx(score, 0.5994)
    assert proxy is False


def test_infrastructure_hazard_missing_data_falls_back_to_proxy():
    """Empty connector data -> documented proxy defaults, proxy flag True."""
    h = _hazard()
    score, proxy = h._infrastructure_hazard({})
    # weighted defaults: 0.333*(0.4+0.5+0.45) = 0.4496
    assert _approx(score, 0.4496)
    assert proxy is True


# --- _natural_hazard --------------------------------------------------------

def test_natural_hazard_real_data_uses_em_dat_and_openaq():
    """Flooding/wildfire/cold from EM-DAT counts, sandstorm from PM2.5."""
    h = _hazard()
    score, proxy = h._natural_hazard({
        'em_dat': {
            'flood_events_10yr': 5,         # 5/10 = 0.5
            'wildfire_events_10yr': 2,      # 2/5  = 0.4
            'extreme_cold_events_10yr': 1,  # 1/5  = 0.2
        },
        'openaq': {'pm25_annual_mean': 50},  # 50/100 = 0.5
    })
    # 0.30*0.5 + 0.20*0.4 + 0.25*0.2 + 0.25*0.5 = 0.15+0.08+0.05+0.125 = 0.405
    assert _approx(score, 0.405)
    assert proxy is False


def test_natural_hazard_missing_data_falls_back_to_proxy():
    """Empty connector data -> all four sub-scores use documented defaults."""
    h = _hazard()
    score, proxy = h._natural_hazard({})
    # 0.30*0.4 + 0.20*0.2 + 0.25*0.3 + 0.25*0.6 = 0.385
    assert _approx(score, 0.385)
    assert proxy is True


# --- _epidemiological_hazard ----------------------------------------------

def test_epidemiological_hazard_real_data_uses_ncdc_libya():
    """NCDC Libya local surveillance preferred over WHO GHO."""
    h = _hazard()
    score, proxy = h._epidemiological_hazard({
        'ncdc_libya': {'infectious_disease_rate': 100,  # 100/500 = 0.20
                       'vector_borne_rate': 30},        # 30/100  = 0.30
    })
    # 0.60*0.20 + 0.40*0.30 = 0.12 + 0.12 = 0.24
    assert _approx(score, 0.24)
    assert proxy is False


def test_epidemiological_hazard_missing_data_falls_back_to_proxy():
    """Empty connector data -> documented proxy defaults."""
    h = _hazard()
    score, proxy = h._epidemiological_hazard({})
    # 0.60*0.35 + 0.40*0.30 = 0.21 + 0.12 = 0.33
    assert _approx(score, 0.33)
    assert proxy is True


# --- _road_safety_hazard ---------------------------------------------------

def test_road_safety_hazard_real_data_uses_who_road_traffic_mortality():
    """WHO road traffic mortality rate scaled by 1/30 cap."""
    h = _hazard()
    score, proxy = h._road_safety_hazard({
        'who_gho': {'road_traffic_mortality_rate': 15},  # 15/30 = 0.5
    })
    assert _approx(score, 0.5)
    assert proxy is False


def test_road_safety_hazard_missing_data_falls_back_to_proxy():
    """Empty connector data -> 0.5 proxy with proxy_used True."""
    h = _hazard()
    score, proxy = h._road_safety_hazard({})
    assert _approx(score, 0.5)
    assert proxy is True


# ===========================================================================
# Pillar 2 — Vulnerability sub-indicators
# ===========================================================================

# --- _agency_capacity_gap --------------------------------------------------

def test_agency_capacity_gap_real_data_uses_local_staffing():
    """COI Libya agency_staffing_gap is the primary signal, no proxy."""
    v = _vuln()
    score, proxy = v._agency_capacity_gap({
        'coi_libya': {'agency_staffing_gap': 0.7},
    })
    assert _approx(score, 0.7)
    assert proxy is False


def test_agency_capacity_gap_missing_data_falls_back_to_proxy():
    """Empty connector data -> documented 0.55 proxy."""
    v = _vuln()
    score, proxy = v._agency_capacity_gap({})
    assert _approx(score, 0.55)
    assert proxy is True


# --- _urban_sprawl ---------------------------------------------------------

def test_urban_sprawl_real_data_uses_worldbank_growth_rate():
    """Urban growth rate scaled by 1/5 cap."""
    v = _vuln()
    score, proxy = v._urban_sprawl({
        'worldbank': {'urban_growth_rate': 2.5},  # 2.5/5 = 0.5
    })
    assert _approx(score, 0.5)
    assert proxy is False


def test_urban_sprawl_missing_data_falls_back_to_proxy():
    """Empty connector data -> documented 0.40 proxy."""
    v = _vuln()
    score, proxy = v._urban_sprawl({})
    assert _approx(score, 0.40)
    assert proxy is True


# --- _displacement_vulnerability -------------------------------------------

def test_displacement_vulnerability_real_data_uses_idmc_and_iom():
    """IDP stock + migrant total normalised against 20% of population."""
    v = _vuln()
    score, proxy = v._displacement_vulnerability({
        'idmc': {'total_idps': 200_000},
        'iom':  {'total_migrants': 300_000},
    })
    # (200_000 + 300_000) / (7_100_000 * 0.20) = 500_000 / 1_420_000 = 0.3521
    assert _approx(score, 0.3521)
    assert proxy is False


def test_displacement_vulnerability_missing_data_falls_back_to_proxy():
    """Empty connector data -> documented 0.45 proxy."""
    v = _vuln()
    score, proxy = v._displacement_vulnerability({})
    assert _approx(score, 0.45)
    assert proxy is True


# --- _health_unawareness ---------------------------------------------------

def test_health_unawareness_real_data_inverts_vaccination_and_literacy():
    """1 - measles vaccination, 1 - literacy rate, averaged."""
    v = _vuln()
    score, proxy = v._health_unawareness({
        'who_gho':   {'measles_vaccination_coverage': 80},  # 1 - 0.8 = 0.2
        'worldbank': {'literacy_rate': 70},                  # 1 - 0.7 = 0.3
    })
    # mean(0.2, 0.3) = 0.25
    assert _approx(score, 0.25)
    assert proxy is False


def test_health_unawareness_missing_data_falls_back_to_proxy():
    """Empty connector data -> documented 0.35 proxy."""
    v = _vuln()
    score, proxy = v._health_unawareness({})
    assert _approx(score, 0.35)
    assert proxy is True


# --- _security_vulnerability -----------------------------------------------

def test_security_vulnerability_real_data_uses_local_incident_rate():
    """COI security_incident_rate is the preferred direct signal."""
    v = _vuln()
    score, proxy = v._security_vulnerability({
        'coi_libya': {'security_incident_rate': 0.6},
    })
    assert _approx(score, 0.6)
    assert proxy is False


def test_security_vulnerability_missing_data_falls_back_to_proxy():
    """Empty connector data -> documented 0.60 proxy."""
    v = _vuln()
    score, proxy = v._security_vulnerability({})
    assert _approx(score, 0.60)
    assert proxy is True


# ===========================================================================
# Pillar 3 — Lack of Coping Capacity sub-indicators
# ===========================================================================

# --- _response_time_gap ----------------------------------------------------

def test_response_time_gap_real_data_uses_ambulance_response_minutes():
    """COI ambulance response minutes scaled against 60-minute cap."""
    c = _coping()
    score, proxy = c._response_time_gap({
        'coi_libya': {'avg_ambulance_response_minutes': 30},  # 30/60 = 0.5
    })
    assert _approx(score, 0.5)
    assert proxy is False


def test_response_time_gap_missing_data_falls_back_to_proxy():
    """Empty connector data -> documented 0.60 proxy."""
    c = _coping()
    score, proxy = c._response_time_gap({})
    assert _approx(score, 0.60)
    assert proxy is True


# --- _data_availability_gap ------------------------------------------------

def test_data_availability_gap_real_data_uses_interoperability_score():
    """1 - data_interoperability_score is the preferred signal."""
    c = _coping()
    score, proxy = c._data_availability_gap({
        'coi_libya': {'data_interoperability_score': 0.7},  # 1 - 0.7 = 0.3
    })
    assert _approx(score, 0.3)
    assert proxy is False


def test_data_availability_gap_missing_data_falls_back_to_proxy():
    """Empty connector data (no nested dicts) -> documented 0.70 proxy."""
    c = _coping()
    score, proxy = c._data_availability_gap({})
    assert _approx(score, 0.70)
    assert proxy is True


# --- _community_support_gap ------------------------------------------------

def test_community_support_gap_real_data_uses_ngo_presence_score():
    """1 - ngo_presence_score is the preferred signal."""
    c = _coping()
    score, proxy = c._community_support_gap({
        'coi_libya': {'ngo_presence_score': 0.6},  # 1 - 0.6 = 0.4
    })
    assert _approx(score, 0.4)
    assert proxy is False


def test_community_support_gap_missing_data_falls_back_to_proxy():
    """Empty connector data -> documented 0.55 proxy."""
    c = _coping()
    score, proxy = c._community_support_gap({})
    assert _approx(score, 0.55)
    assert proxy is True


# --- _healthcare_access_gap ------------------------------------------------

def test_healthcare_access_gap_real_data_uses_uchi_inverse():
    """1 - (UHC index / 100) is the preferred signal."""
    c = _coping()
    score, proxy = c._healthcare_access_gap({
        'who_gho': {'universal_health_coverage_index': 70},  # 1 - 0.7 = 0.3
    })
    assert _approx(score, 0.3)
    assert proxy is False


def test_healthcare_access_gap_missing_data_falls_back_to_proxy():
    """Empty connector data -> documented 0.50 proxy."""
    c = _coping()
    score, proxy = c._healthcare_access_gap({})
    assert _approx(score, 0.50)
    assert proxy is True


# --- _poverty_vulnerability ------------------------------------------------

def test_poverty_vulnerability_real_data_uses_poverty_headcount_ratio():
    """Poverty headcount as a fraction (capped at 1.0)."""
    c = _coping()
    score, proxy = c._poverty_vulnerability({
        'worldbank': {'poverty_headcount_ratio': 25},  # 25/100 = 0.25
    })
    assert _approx(score, 0.25)
    assert proxy is False


def test_poverty_vulnerability_missing_data_falls_back_to_proxy():
    """Empty connector data -> documented 0.45 proxy."""
    c = _coping()
    score, proxy = c._poverty_vulnerability({})
    assert _approx(score, 0.45)
    assert proxy is True


# ===========================================================================
# _weighted_average — fully populated, partial, and all-missing
#
# Note: the helper currently lives on each pillar domain (rather than on
# BaseDomain). All three implementations should agree for these canonical
# cases, so we exercise each one with the same fixture.
# ===========================================================================

WEIGHTS = {'a': 0.5, 'b': 0.5}


def _weighted_cases(domain):
    """Return (full, partial, missing) results for a domain instance."""
    return (
        domain._weighted_average({'a': 0.5, 'b': 0.5}, WEIGHTS),
        domain._weighted_average({'a': 0.8}, WEIGHTS),  # b missing
        domain._weighted_average({}, WEIGHTS),           # both missing
    )


def test_weighted_average_full_inputs_hazard():
    full, _, _ = _weighted_cases(_hazard())
    score, coverage = full
    assert _approx(score, 0.5)
    assert _approx(coverage, 1.0)


def test_weighted_average_partial_inputs_hazard():
    """Single available indicator should drive the score (rescaled)."""
    _, partial, _ = _weighted_cases(_hazard())
    score, coverage = partial
    assert _approx(score, 0.8)
    assert _approx(coverage, 0.5)


def test_weighted_average_all_missing_hazard():
    """No inputs -> 0 score and 0 coverage (never NaN, never raises)."""
    _, _, missing = _weighted_cases(_hazard())
    score, coverage = missing
    assert score == 0.0
    assert coverage == 0.0


def test_weighted_average_full_inputs_vulnerability():
    full, _, _ = _weighted_cases(_vuln())
    score, coverage = full
    assert _approx(score, 0.5)
    assert _approx(coverage, 1.0)


def test_weighted_average_partial_inputs_vulnerability():
    _, partial, _ = _weighted_cases(_vuln())
    score, coverage = partial
    assert _approx(score, 0.8)
    assert _approx(coverage, 0.5)


def test_weighted_average_all_missing_vulnerability():
    _, _, missing = _weighted_cases(_vuln())
    score, coverage = missing
    assert score == 0.0
    assert coverage == 0.0


def test_weighted_average_full_inputs_coping():
    full, _, _ = _weighted_cases(_coping())
    score, coverage = full
    assert _approx(score, 0.5)
    assert _approx(coverage, 1.0)


def test_weighted_average_partial_inputs_coping():
    _, partial, _ = _weighted_cases(_coping())
    score, coverage = partial
    assert _approx(score, 0.8)
    assert _approx(coverage, 0.5)


def test_weighted_average_all_missing_coping():
    _, _, missing = _weighted_cases(_coping())
    score, coverage = missing
    assert score == 0.0
    assert coverage == 0.0


# ---------------------------------------------------------------------------
# Standalone runner
# ---------------------------------------------------------------------------
if __name__ == "__main__":
    import pytest
    sys.exit(pytest.main([__file__, "-v"]))
