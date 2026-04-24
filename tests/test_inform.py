"""
Libya CARA — INFORM-formula automated tests.

Validates the headline INFORM Risk Index pipeline on three levels:

1. The cube-root composition that combines the three pillars
   (Hazard × Vulnerability × Coping)^(1/3) — `routes.dashboard._compute_inform_score`.
2. The 0-1 banding helper used by the action plan template
   (very_low / low / medium / high / very_high) —
   `utils.action_plan_content._inform_classify`.
3. One full national-level dashboard score end-to-end through
   `routes.dashboard._run_pillars` with synthetic connector data.

Run as a standalone script (from the project root):
    python tests/test_inform.py

Run with pytest:
    pytest tests/test_inform.py -v
"""

import importlib
import math
import os
import sys
from unittest.mock import patch

# ---------------------------------------------------------------------------
# Standalone path setup (mirrors tests/smoke_test.py).
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
# Synthetic fixtures
# ---------------------------------------------------------------------------

JURISDICTION_CONFIG = {
    "jurisdiction": {
        "name": "Libya",
        "short_name": "LY",
        "country_code": "LY",
        "iso3166_1": "LBY",
        "population": 7_000_000,
    },
    "domain_config": {},
}


# ---------------------------------------------------------------------------
# 1) Cube-root composition of the three INFORM pillars
# ---------------------------------------------------------------------------

def test_compute_inform_score_all_zero():
    """Geometric mean of three zeros is exactly zero."""
    dashboard = _import("routes.dashboard")
    assert dashboard._compute_inform_score(0.0, 0.0, 0.0) == 0.0


def test_compute_inform_score_all_one():
    """Geometric mean of three ones is exactly one."""
    dashboard = _import("routes.dashboard")
    assert dashboard._compute_inform_score(1.0, 1.0, 1.0) == 1.0


def test_compute_inform_score_equal_mixed():
    """Geometric mean of three equal values equals that value."""
    dashboard = _import("routes.dashboard")
    assert dashboard._compute_inform_score(0.5, 0.5, 0.5) == 0.5


def test_compute_inform_score_asymmetric():
    """Geometric mean of (0.8, 0.5, 0.2) ≈ 0.4309 (rounded to 4 dp)."""
    dashboard = _import("routes.dashboard")
    expected = round((0.8 * 0.5 * 0.2) ** (1.0 / 3.0), 4)
    got = dashboard._compute_inform_score(0.8, 0.5, 0.2)
    assert got == expected
    # Sanity check the math itself, independent of the implementation.
    assert math.isclose(got, 0.4309, abs_tol=1e-4)


def test_compute_inform_score_one_missing_pillar_collapses_to_zero():
    """A single zero (pillar effectively absent) drives the geometric mean to 0."""
    dashboard = _import("routes.dashboard")
    assert dashboard._compute_inform_score(0.5, 0.0, 0.5) == 0.0
    assert dashboard._compute_inform_score(0.0, 0.7, 0.9) == 0.0


def test_compute_inform_score_unequal_values():
    """Geometric mean of (0.4, 0.6, 0.8) ≈ 0.5769 (rounded to 4 dp)."""
    dashboard = _import("routes.dashboard")
    expected = round((0.4 * 0.6 * 0.8) ** (1.0 / 3.0), 4)
    got = dashboard._compute_inform_score(0.4, 0.6, 0.8)
    assert got == expected
    assert math.isclose(got, 0.5769, abs_tol=1e-4)


# ---------------------------------------------------------------------------
# 2) Banding cut points in utils.action_plan_content._inform_classify
# ---------------------------------------------------------------------------

def test_inform_classify_very_low_band():
    """Scores below 0.20 (upper-exclusive) are 'very_low'."""
    apc = _import("utils.action_plan_content")
    assert apc._inform_classify(0.0)['level'] == 'very_low'
    assert apc._inform_classify(0.10)['level'] == 'very_low'
    assert apc._inform_classify(0.1999)['level'] == 'very_low'


def test_inform_classify_low_band():
    """Scores in [0.20, 0.40) are 'low'."""
    apc = _import("utils.action_plan_content")
    assert apc._inform_classify(0.20)['level'] == 'low'
    assert apc._inform_classify(0.30)['level'] == 'low'
    assert apc._inform_classify(0.3999)['level'] == 'low'


def test_inform_classify_medium_band():
    """Scores in [0.40, 0.60) are 'medium'."""
    apc = _import("utils.action_plan_content")
    assert apc._inform_classify(0.40)['level'] == 'medium'
    assert apc._inform_classify(0.50)['level'] == 'medium'
    assert apc._inform_classify(0.5999)['level'] == 'medium'


def test_inform_classify_high_band():
    """Scores in [0.60, 0.80) are 'high'."""
    apc = _import("utils.action_plan_content")
    assert apc._inform_classify(0.60)['level'] == 'high'
    assert apc._inform_classify(0.70)['level'] == 'high'
    assert apc._inform_classify(0.7999)['level'] == 'high'


def test_inform_classify_very_high_band():
    """Scores >= 0.80 are 'very_high', including out-of-range values."""
    apc = _import("utils.action_plan_content")
    assert apc._inform_classify(0.80)['level'] == 'very_high'
    assert apc._inform_classify(0.95)['level'] == 'very_high'
    assert apc._inform_classify(1.00)['level'] == 'very_high'
    assert apc._inform_classify(1.50)['level'] == 'very_high'


def test_inform_classify_unavailable_for_invalid_input():
    """Non-numeric or negative scores return 'unavailable'."""
    apc = _import("utils.action_plan_content")
    assert apc._inform_classify(None)['level'] == 'unavailable'
    assert apc._inform_classify("not-a-number")['level'] == 'unavailable'
    assert apc._inform_classify(-0.01)['level'] == 'unavailable'
    assert apc._inform_classify(-1.0)['level'] == 'unavailable'


# ---------------------------------------------------------------------------
# 3) Full national-level dashboard score end-to-end
# ---------------------------------------------------------------------------

def test_run_pillars_end_to_end_inform_score_matches_geometric_mean():
    """
    Exercise routes.dashboard._run_pillars with synthetic connector data
    (empty dict → pillar domains fall back to documented proxies) and
    assert that the headline INFORM Risk Index equals the geometric mean
    of the three pillar scores it itself produced.
    """
    dashboard = _import("routes.dashboard")
    apc = _import("utils.action_plan_content")

    with patch.object(dashboard, "_load_connector_data", return_value={}):
        results = dashboard._run_pillars("LY", JURISDICTION_CONFIG)

    # All three pillars present and available
    for key in ("hazard", "vulnerability", "coping"):
        assert key in results, f"Missing pillar: {key}"
        assert results[key]["available"] is True, (
            f"Pillar {key} unexpectedly unavailable on proxy fixture"
        )
        score = results[key]["score"]
        assert isinstance(score, float)
        assert 0.0 <= score <= 1.0

    h = results["hazard"]["score"]
    v = results["vulnerability"]["score"]
    c = results["coping"]["score"]

    # INFORM headline number
    inform = results["inform_score"]
    assert inform["available"] is True
    assert inform["score"] == dashboard._compute_inform_score(h, v, c)
    assert math.isclose(inform["score"], (h * v * c) ** (1.0 / 3.0), abs_tol=1e-4)

    # Headline level matches the dashboard banding helper
    assert inform["level"] == dashboard._score_to_level(inform["score"])

    # Action-plan banding helper agrees on the same score
    assert apc._inform_classify(inform["score"])["level"] in {
        "very_low", "low", "medium", "high", "very_high",
    }

    # formula_values block exposes the same numbers, scaled to 0-10
    fv = inform["formula_values"]
    assert fv["h"] == round(h * 10, 1)
    assert fv["v"] == round(v * 10, 1)
    assert fv["c"] == round(c * 10, 1)
    assert fv["result"] == round(inform["score"] * 10, 1)


def test_run_pillars_end_to_end_deterministic_fixture():
    """
    End-to-end regression test against a small *deterministic* fixture: pin
    the three pillar domain calculate() returns to fixed scores and assert
    the exact expected headline INFORM Risk Index and risk level.

    Fixture: hazard=0.5, vulnerability=0.4, coping=0.6
    Expected: (0.5 * 0.4 * 0.6) ^ (1/3) = 0.12 ^ (1/3) = 0.4932 (4 dp)
    Expected dashboard level: 'moderate' (>= 0.35 and < 0.55)
    Expected action-plan band: 'medium' (>= 0.40 and < 0.60)
    Expected formula_values 0-10: h=5.0, v=4.0, c=6.0, result=4.9
    """
    dashboard = _import("routes.dashboard")
    apc = _import("utils.action_plan_content")

    def _fake_calc(score, components):
        def _calculate(self, connector_data, jurisdiction_config, profile='libya'):
            return {
                'score': score,
                'available': True,
                'data_coverage': 1.0,
                'sub_domains': {k: {'score': v, 'proxy_used': False}
                                for k, v in components.items()},
                'dominant_factor': 'fixture',
                'data_sources': ['fixture'],
            }
        return _calculate

    HazardExposureDomain = dashboard.HazardExposureDomain
    VulnerabilityDomain  = dashboard.VulnerabilityDomain
    CopingCapacityDomain = dashboard.CopingCapacityDomain

    with patch.object(dashboard, "_load_connector_data", return_value={}), \
         patch.object(HazardExposureDomain, "calculate",
                      _fake_calc(0.5, {'infrastructure_hazard': 0.5})), \
         patch.object(VulnerabilityDomain, "calculate",
                      _fake_calc(0.4, {'agency_capacity_gap': 0.4})), \
         patch.object(CopingCapacityDomain, "calculate",
                      _fake_calc(0.6, {'response_time_gap': 0.6})):
        results = dashboard._run_pillars("LY", JURISDICTION_CONFIG)

    # Pillar scores match the fixture exactly
    assert results["hazard"]["score"] == 0.5
    assert results["vulnerability"]["score"] == 0.4
    assert results["coping"]["score"] == 0.6
    assert results["hazard"]["available"] is True
    assert results["vulnerability"]["available"] is True
    assert results["coping"]["available"] is True

    # Headline INFORM number is the exact expected geometric mean (4 dp)
    inform = results["inform_score"]
    assert inform["available"] is True
    assert inform["score"] == 0.4932
    # And the round-tripped formula_values block
    assert inform["formula_values"] == {
        'h': 5.0, 'v': 4.0, 'c': 6.0, 'result': 4.9,
    }

    # Dashboard level banding is exactly 'moderate' for 0.4932
    assert inform["level"] == 'moderate'
    assert inform["badge"] == 'warning'

    # Action-plan template banding is exactly 'medium' for 0.4932
    assert apc._inform_classify(inform["score"])["level"] == 'medium'


# ---------------------------------------------------------------------------
# Standalone runner
# ---------------------------------------------------------------------------
if __name__ == "__main__":
    import pytest
    sys.exit(pytest.main([__file__, "-v"]))
