"""
CARA Template — End-to-End Smoke Test

Verifies that all 7 risk domains can be instantiated, that calculate() and
domain_info() succeed without exceptions, that all required result keys are
present, and that the PHRAT pipeline produces a valid numeric score via both
the risk_engine and data_processor orchestration paths.

Run as a standalone script (from the cara_template/ directory):
    python tests/smoke_test.py

Run with pytest (from the workspace root):
    pytest cara_template/tests/smoke_test.py -v
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
    "domain_config": {
        "mass_casualty": {"us_subtype": False},
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


def test_load_weights_international():
    """load_weights must return 7 domains that sum to 1.0 for international profile."""
    risk_engine = _import("utils.risk_engine")
    weights = risk_engine.load_weights(profile=PROFILE)
    assert weights, "load_weights returned empty dict"
    assert abs(sum(weights.values()) - 1.0) < 0.01, (
        f"weights sum to {sum(weights.values()):.4f}, expected 1.0"
    )
    assert len(weights) == 7, (
        f"Expected 7 domain weights for international profile, got {len(weights)}: "
        f"{sorted(weights.keys())}"
    )


def test_phrat_produces_valid_score():
    """calculate_phrat must return a finite float in [0, 1]."""
    risk_engine = _import("utils.risk_engine")

    domain_scores = {}
    for domain_id, (module_path, class_name) in DOMAIN_CLASS_MAP.items():
        cls = _get_class(module_path, class_name)
        result = cls().calculate(
            connector_data=SYNTHETIC_CONNECTOR_DATA,
            jurisdiction_config=JURISDICTION_CONFIG,
            profile=PROFILE,
        )
        domain_scores[domain_id] = result["score"]

    weights = risk_engine.load_weights(profile=PROFILE)
    total_score, breakdown = risk_engine.calculate_phrat(domain_scores, weights)

    assert isinstance(total_score, (int, float)), (
        f"PHRAT score is not numeric: {total_score!r}"
    )
    assert not math.isnan(total_score), "PHRAT score is NaN"
    assert not math.isinf(total_score), "PHRAT score is Inf"
    assert 0.0 <= total_score <= 1.0, (
        f"PHRAT score {total_score:.4f} outside [0, 1]"
    )
    assert "domains" in breakdown, "PHRAT breakdown missing 'domains' key"


def test_classify_risk_returns_dict_with_required_keys():
    """classify_risk must return a dict with 'level', 'label', 'color', 'description'."""
    risk_engine = _import("utils.risk_engine")

    for score in [0.0, 0.15, 0.35, 0.55, 0.75, 1.0]:
        result = risk_engine.classify_risk(score)
        assert isinstance(result, dict), (
            f"classify_risk({score}) returned {type(result).__name__}, expected dict"
        )
        for key in ("level", "label", "color", "description"):
            assert key in result, (
                f"classify_risk({score}) missing key '{key}': {result}"
            )


def test_compute_all_domains_returns_all_7_international_domains():
    """
    compute_all_domains must return all 7 international-profile domains.
    A missing domain indicates a silent import error (e.g. wrong class name)
    that drops coverage from the live pipeline.
    """
    risk_engine = _import("utils.risk_engine")

    results = risk_engine.compute_all_domains(
        connector_data=SYNTHETIC_CONNECTOR_DATA,
        jurisdiction_config=JURISDICTION_CONFIG,
        profile=PROFILE,
    )

    missing = EXPECTED_INTERNATIONAL_DOMAINS - set(results.keys())
    assert not missing, (
        f"compute_all_domains did not return expected domains: {missing}"
    )
    assert len(results) >= 7, (
        f"Expected at least 7 domains, got {len(results)}: {sorted(results.keys())}"
    )


def test_risk_engine_end_to_end_pipeline():
    """
    Full risk_engine pipeline: compute_all_domains → load_weights → calculate_phrat.
    Verifies that all 7 domain scores feed into a valid composite PHRAT score.
    """
    risk_engine = _import("utils.risk_engine")

    domain_results = risk_engine.compute_all_domains(
        connector_data=SYNTHETIC_CONNECTOR_DATA,
        jurisdiction_config=JURISDICTION_CONFIG,
        profile=PROFILE,
    )
    assert len(domain_results) >= 7, (
        f"Expected 7 domains from compute_all_domains, got {len(domain_results)}"
    )

    domain_scores = {k: v.get("score", 0.0) for k, v in domain_results.items()}
    weights = risk_engine.load_weights(profile=PROFILE)
    total_score, _ = risk_engine.calculate_phrat(domain_scores, weights)

    assert isinstance(total_score, (int, float)), f"Non-numeric PHRAT score: {total_score!r}"
    assert not math.isnan(total_score), "PHRAT score is NaN"
    assert 0.0 <= total_score <= 1.0, f"PHRAT score {total_score:.4f} outside [0, 1]"


def test_data_processor_orchestration():
    """
    Validate the data_processor orchestration path:
    compute_all_domains → load_weights → calculate_phrat → classify_risk.
    Uses synthetic connector data; no network calls or database required.
    This mirrors compute_risk_for_jurisdiction() in data_processor.py,
    exercising every scoring step except config file loading and connector fetching.
    """
    risk_engine = _import("utils.risk_engine")

    domain_results = risk_engine.compute_all_domains(
        connector_data=SYNTHETIC_CONNECTOR_DATA,
        jurisdiction_config=JURISDICTION_CONFIG,
        profile=PROFILE,
    )

    domain_scores = {k: v.get("score", 0.0) for k, v in domain_results.items()}
    domain_components = {k: v.get("components", {}) for k, v in domain_results.items()}

    weights = risk_engine.load_weights(
        profile=PROFILE,
        jurisdiction_overrides=JURISDICTION_CONFIG.get("jurisdiction", {}).get("weight_overrides"),
    )

    total_score, breakdown = risk_engine.calculate_phrat(domain_scores, weights)
    classification = risk_engine.classify_risk(total_score)

    risk_level = classification["label"]
    assert isinstance(risk_level, str) and risk_level.strip(), (
        f"risk_level is not a non-empty string: {risk_level!r}"
    )

    result = {
        "jurisdiction_id": "test_jurisdiction",
        "profile": PROFILE,
        "total_score": round(total_score, 4),
        "risk_level": risk_level,
        "domain_scores": {k: round(v, 4) for k, v in domain_scores.items()},
        "domain_components": domain_components,
    }

    assert isinstance(result["total_score"], float)
    assert 0.0 <= result["total_score"] <= 1.0
    assert result["risk_level"] in (
        "Minimal", "Low", "Moderate", "High", "Critical"
    ), f"Unexpected risk_level: {result['risk_level']!r}"
    assert len(result["domain_scores"]) >= 7, (
        f"Expected 7 domain scores in result, got {len(result['domain_scores'])}"
    )


# ---------------------------------------------------------------------------
# Standalone script runner (no pytest required)
# ---------------------------------------------------------------------------

def _run_standalone():
    """Execute all test_* functions and print a summary."""
    test_functions = [
        (name, obj)
        for name, obj in sorted(globals().items())
        if name.startswith("test_") and callable(obj)
    ]

    print()
    print("=" * 65)
    print("  CARA Template — Smoke Test (standalone)")
    print("=" * 65)
    print(f"  Module prefix resolved to: '{_get_prefix()}utils.*'")

    passed = failed = 0
    for name, fn in test_functions:
        try:
            fn()
            print(f"  [PASS] {name}")
            passed += 1
        except Exception as exc:
            print(f"  [FAIL] {name}")
            print(f"         {exc}")
            failed += 1

    print()
    print("=" * 65)
    if failed == 0:
        print(f"  RESULT: {passed}/{passed} PASSED  ✓")
    else:
        print(f"  RESULT: {passed} passed, {failed} FAILED  ✗")
    print("=" * 65)
    print()
    return failed == 0


if __name__ == "__main__":
    success = _run_standalone()
    sys.exit(0 if success else 1)
