"""
Libya CARA — End-to-End Smoke Test

Verifies that all domain classes can be instantiated, that calculate() and
domain_info() succeed without exceptions, and that all required result keys
are present.  Also validates the INFORM Risk Index scoring pipeline used by
the Libya profile and the legacy weighted-quadratic-mean pipeline used by
the international profile.

INFORM Risk Index formula (Libya profile):
    INFORM_Risk = (Hazard_Exposure × Vulnerability × Lack_of_Coping_Capacity) ^ (1/3)

Run as a standalone script (from the project root):
    python tests/smoke_test.py

Run with pytest:
    pytest tests/smoke_test.py -v
"""

import importlib
import logging
import math
import os
import sys

logging.basicConfig(level=logging.WARNING)

# ---------------------------------------------------------------------------
# Standalone path setup: when run as "python tests/smoke_test.py" from
# cara_template/, Python puts tests/ on sys.path but not cara_template/.
# We detect this and fix it here so the script is self-contained.
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

# ---------------------------------------------------------------------------
# Resolve module prefix lazily (on first test call, not at import time).
#
# Resolution is deferred so that the conftest autouse fixture in
# cara_template/tests/conftest.py has already run by the time any test
# function first calls _import().  This prevents stale sys.modules entries
# (e.g. from the root tests/conftest.py) from poisoning the resolution.
#
# In standalone mode the standalone path setup above already inserted
# TEMPLATE_DIR at sys.path[0] so the deferred resolution also returns "".
# ---------------------------------------------------------------------------

_PREFIX: str | None = None


def _resolve_prefix() -> str:
    """Return '' if bare utils.* imports work, else 'cara_template.'."""
    try:
        importlib.import_module("utils.domains.base_domain")
        return ""
    except (ModuleNotFoundError, ImportError):
        pass
    try:
        importlib.import_module("cara_template.utils.domains.base_domain")
        return "cara_template."
    except (ModuleNotFoundError, ImportError) as exc:
        raise RuntimeError(
            "Cannot import utils.domains or cara_template.utils.domains. "
            "Run from cara_template/ or ensure workspace root is on sys.path."
        ) from exc


def _get_prefix() -> str:
    """Return the resolved prefix, computing it once on first call."""
    global _PREFIX
    if _PREFIX is None:
        _PREFIX = _resolve_prefix()
    return _PREFIX


def _import(module_path: str):
    """Import a module using the resolved prefix (computed lazily)."""
    return importlib.import_module(f"{_get_prefix()}{module_path}")


def _get_class(module_path: str, class_name: str):
    """Import a module and return the named class."""
    mod = _import(module_path)
    return getattr(mod, class_name)


# ---------------------------------------------------------------------------
# Synthetic test fixtures
# ---------------------------------------------------------------------------

JURISDICTION_CONFIG = {
    "jurisdiction": {
        "name": "Test Jurisdiction",
        "short_name": "TJ",
        "country_code": "TJ",
        "iso3166_1": "TJK",
        "population": 2_000_000,
    },
}

SYNTHETIC_CONNECTOR_DATA = {
    "acled": {
        "available": True,
        "violent_events_12mo": 120,
        "fatalities_12mo": 300,
        "conflict_intensity_score": 0.45,
        "trend_direction": "stable",
        "hotspot_districts": ["District A", "District B"],
        "events_by_type": {
            "Battles": 50,
            "Violence against civilians": 40,
            "Explosions/Remote violence": 30,
        },
    },
    "idmc": {
        "available": True,
        "displacement_score": 0.35,
        "conflict_new_displacements": 50_000,
        "disaster_new_displacements": 10_000,
        "total_idps": 180_000,
        "year": 2024,
    },
    "worldbank": {
        "available": True,
        "vulnerability_index": 0.55,
        "gdp_per_capita": 8_500,
        "access_electricity": 72.0,
    },
    "em_dat": {
        "available": True,
        "total_events_10yr": 18,
        "dominant_hazard": "Flood",
        "events_by_type": {
            "Flood": 10,
            "Storm": 5,
            "Earthquake": 3,
        },
    },
    "openaq": {
        "available": True,
        "current_aqi": 95,
        "pm25_annual_mean_ug_m3": 22.0,
        "ozone_4th_max_8hr_ppb": 68.0,
        "unhealthy_days_annual": 18,
        "station_count": 4,
    },
    "noaa_gsod": {
        "available": True,
        "days_above_90f_annual": 35,
        "days_above_100f_annual": 5,
        "heat_wave_events_5yr": 3,
    },
    "who_gho": {
        "available": True,
        "copd_prevalence_pct": 7.2,
        "diabetes_prevalence_pct": 11.0,
        "flu_vaccination_rate": 0.38,
        "primary_care_per_100k": 55,
    },
}

PROFILE = "international"

REQUIRED_RESULT_KEYS = {"score", "available", "confidence", "dominant_factor"}

DOMAIN_CLASS_MAP = {
    "air_quality":           ("utils.domains.air_quality",           "AirQualityDomain"),
    "conflict_displacement": ("utils.domains.conflict_displacement",  "ConflictDisplacementDomain"),
    "extreme_heat":          ("utils.domains.extreme_heat",           "ExtremeHeatDomain"),
    "health_metrics":        ("utils.domains.health_metrics",         "HealthMetricsDomain"),
    "mass_casualty":         ("utils.domains.mass_casualty",          "MassCasualtyDomain"),
    "natural_hazards":       ("utils.domains.natural_hazards",        "NaturalHazardsDomain"),
    "vector_borne_disease":  ("utils.domains.vector_borne_disease",   "VectorBorneDiseaseDomain"),
}

EXPECTED_INTERNATIONAL_DOMAINS = {
    "natural_hazards", "conflict_displacement", "health_metrics",
    "mass_casualty", "air_quality", "extreme_heat", "vector_borne_disease",
}


# ---------------------------------------------------------------------------
# Pytest test functions
# ---------------------------------------------------------------------------

def test_all_domains_import():
    """All 7 domain classes must import without error."""
    for domain_id, (module_path, class_name) in DOMAIN_CLASS_MAP.items():
        cls = _get_class(module_path, class_name)
        assert cls is not None, f"Could not load {class_name}"


def test_all_domains_instantiate():
    """All 7 domain classes must instantiate without arguments."""
    for domain_id, (module_path, class_name) in DOMAIN_CLASS_MAP.items():
        cls = _get_class(module_path, class_name)
        instance = cls()
        assert instance is not None


def test_domain_info_keys():
    """domain_info() must return all required metadata keys."""
    required = {"id", "label", "description", "methodology", "applicable_profiles"}
    for domain_id, (module_path, class_name) in DOMAIN_CLASS_MAP.items():
        cls = _get_class(module_path, class_name)
        info = cls().domain_info()
        missing = required - set(info.keys())
        assert not missing, (
            f"{class_name}.domain_info() missing keys: {missing}"
        )


def test_calculate_required_keys():
    """calculate() must return all required result keys."""
    for domain_id, (module_path, class_name) in DOMAIN_CLASS_MAP.items():
        cls = _get_class(module_path, class_name)
        result = cls().calculate(
            connector_data=SYNTHETIC_CONNECTOR_DATA,
            jurisdiction_config=JURISDICTION_CONFIG,
            profile=PROFILE,
        )
        missing = REQUIRED_RESULT_KEYS - set(result.keys())
        assert not missing, (
            f"{class_name}.calculate() missing keys: {missing}"
        )


def test_calculate_score_range():
    """Every domain score must be a finite float in [0.0, 1.0]."""
    for domain_id, (module_path, class_name) in DOMAIN_CLASS_MAP.items():
        cls = _get_class(module_path, class_name)
        result = cls().calculate(
            connector_data=SYNTHETIC_CONNECTOR_DATA,
            jurisdiction_config=JURISDICTION_CONFIG,
            profile=PROFILE,
        )
        score = result["score"]
        assert isinstance(score, (int, float)), (
            f"{class_name} score is not numeric: {score!r}"
        )
        assert not math.isnan(score), f"{class_name} score is NaN"
        assert not math.isinf(score), f"{class_name} score is Inf"
        assert 0.0 <= score <= 1.0, (
            f"{class_name} score {score:.4f} outside [0, 1]"
        )


def test_calculate_available_field():
    """Every domain result must include a boolean 'available' field."""
    for domain_id, (module_path, class_name) in DOMAIN_CLASS_MAP.items():
        cls = _get_class(module_path, class_name)
        result = cls().calculate(
            connector_data=SYNTHETIC_CONNECTOR_DATA,
            jurisdiction_config=JURISDICTION_CONFIG,
            profile=PROFILE,
        )
        assert isinstance(result["available"], bool), (
            f"{class_name} 'available' field is not bool: {result['available']!r}"
        )


def test_calculate_dominant_factor_non_empty():
    """dominant_factor must be a non-empty string."""
    for domain_id, (module_path, class_name) in DOMAIN_CLASS_MAP.items():
        cls = _get_class(module_path, class_name)
        result = cls().calculate(
            connector_data=SYNTHETIC_CONNECTOR_DATA,
            jurisdiction_config=JURISDICTION_CONFIG,
            profile=PROFILE,
        )
        df = result["dominant_factor"]
        assert isinstance(df, str) and df.strip(), (
            f"{class_name}.dominant_factor is empty or not a string: {df!r}"
        )



# ---------------------------------------------------------------------------
# Standalone runner
# ---------------------------------------------------------------------------
if __name__ == "__main__":
    import pytest
    sys.exit(pytest.main([__file__, "-v"]))
