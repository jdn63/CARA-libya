"""
Libya CARA — guardrails against accidentally double-counting the
sub-baladiya overlays in national population rollups.

Task #23 introduced ``population_in_national_total`` on every entry and
pinned ``_metadata.national_total_deduped`` in
``data/libya_municipalities.json``. A naive sum across all municipality
entries over-counts the Tripoli/Benghazi/Susah/Tobruk muhalla overlays
that live inside their parent baladiya.

These tests fail CI if any code path outside the canonical helper
(``JurisdictionManager.national_population_deduped``) tries to compute
a national population by summing ``population`` across all municipality
entries without filtering by the deduplication flag.

Run as a standalone script (from the project root):
    python tests/test_population_rollup_guardrails.py

Run with pytest:
    pytest tests/test_population_rollup_guardrails.py -v
"""

import os
import re
import sys
from pathlib import Path

_SCRIPT_DIR = Path(__file__).resolve().parent
_TEMPLATE_DIR = _SCRIPT_DIR.parent
if str(_TEMPLATE_DIR) not in sys.path:
    sys.path.insert(0, str(_TEMPLATE_DIR))
if os.getcwd() != str(_TEMPLATE_DIR):
    try:
        os.chdir(_TEMPLATE_DIR)
    except OSError:
        pass

ROOT = _TEMPLATE_DIR

# Files that are explicitly allowed to compute the deduplicated national
# total themselves. Everything else must go through
# JurisdictionManager.national_population_deduped().
ALLOWED_PATHS = {
    # The canonical accessor lives here.
    "utils/geography/jurisdiction_manager.py",
    # The refresh script computes the canonical value and writes it back
    # into data/libya_municipalities.json's _metadata block.
    "scripts/refresh_population.py",
    # Schema/consistency invariants for the data file itself.
    "tests/test_population_data.py",
    # This guardrail file (must be allowed to mention the regex).
    "tests/test_population_rollup_guardrails.py",
}

# Directories to skip while walking the project.
SKIP_DIRS = {
    ".git", "__pycache__", ".pytest_cache", ".venv", "venv",
    "node_modules", ".cache", ".pythonlibs", "dist", "build",
    "migrations", "logs", ".upm", ".local", ".agents", ".github",
    ".config", "attached_assets", "data", "docs", "static",
    "templates",
}

# Regex variants that catch suspicious cross-municipality population
# aggregations. All of these styles are flagged:
#   sum(m.population for m in municipalities)
#   sum(m['population'] for m in municipalities)
#   sum(m.get('population', 0) for m in baladiyas)
#   sum(m.get("population") for m in jurisdictions)
#
# We use a single-line dot-match so inner parens (e.g. ``.get('population', 0)``)
# don't terminate the search; the line anchor scopes each match to one
# physical line of source so we don't span the whole file.
_SUSPECT_BODY = (
    r"sum\s*\(.*?population.*?for[^\n]*?"
    r"(?:\bmunicipalit\w*\b|\bjurisdictions?\b|\bbaladiyas?\b"
    r"|\bentries\b|\ball_municipalities\b)"
)
SUSPICIOUS_PATTERNS = [
    re.compile(_SUSPECT_BODY, re.IGNORECASE),
]


def _iter_python_files():
    for dirpath, dirnames, filenames in os.walk(ROOT):
        dirnames[:] = [d for d in dirnames if d not in SKIP_DIRS]
        for fn in filenames:
            if not fn.endswith(".py"):
                continue
            full = Path(dirpath) / fn
            rel = full.relative_to(ROOT).as_posix()
            yield rel, full


def test_no_naive_population_sum_outside_helper():
    """No file outside the allow-list may aggregate ``population`` across
    all municipality entries.

    The allow-list is intentionally tiny: only the canonical accessor in
    ``JurisdictionManager``, the refresh script that *creates* the pinned
    ``_metadata.national_total_deduped`` value, the data invariants test,
    and this guardrail itself. Every other consumer must call
    ``jm.national_population_deduped()`` (or filter by
    ``population_in_national_total=True`` before summing) so dashboards
    never silently inflate the national figure by ~17%.
    """
    violations = []
    for rel, full in _iter_python_files():
        if rel in ALLOWED_PATHS:
            continue
        try:
            text = full.read_text(encoding="utf-8")
        except (OSError, UnicodeDecodeError):
            continue
        for pat in SUSPICIOUS_PATTERNS:
            for match in pat.finditer(text):
                line_no = text.count("\n", 0, match.start()) + 1
                snippet = match.group(0).strip()
                violations.append(f"{rel}:{line_no}: {snippet}")

    assert not violations, (
        "Found naive population aggregations outside the canonical helper "
        "JurisdictionManager.national_population_deduped(). These risk "
        "double-counting sub-baladiya overlays. Either call the helper, "
        "or filter by population_in_national_total=True before summing.\n"
        + "\n".join(violations)
    )


def test_canonical_helper_exists_and_is_documented():
    """The canonical accessor must exist with a docstring that warns
    against naive sums, so future contributors know to use it.
    """
    from utils.geography.jurisdiction_manager import JurisdictionManager

    assert hasattr(JurisdictionManager, "national_population_deduped"), (
        "JurisdictionManager.national_population_deduped() is missing — "
        "this is the canonical accessor for Libya's deduplicated national "
        "population total."
    )
    doc = (JurisdictionManager.national_population_deduped.__doc__ or "").lower()
    assert "national_total_deduped" in doc, (
        "national_population_deduped() docstring should mention "
        "_metadata.national_total_deduped so callers understand the source."
    )
    assert "do not" in doc or "don't" in doc, (
        "national_population_deduped() docstring should warn against "
        "naive sums across all entries."
    )


def test_helper_returns_pinned_metadata_value():
    """The helper must return the same value pinned in
    ``_metadata.national_total_deduped`` so dashboards and the refresh
    script agree on the number.
    """
    import json
    from utils.geography.jurisdiction_manager import JurisdictionManager

    with open("data/libya_municipalities.json", "r", encoding="utf-8") as f:
        data = json.load(f)
    pinned = data["_metadata"]["national_total_deduped"]

    jm = JurisdictionManager()
    assert jm.national_population_deduped() == pinned, (
        f"JurisdictionManager.national_population_deduped() returned a "
        f"different value than _metadata.national_total_deduped "
        f"({pinned}); they must agree."
    )


if __name__ == "__main__":
    test_no_naive_population_sum_outside_helper()
    test_canonical_helper_exists_and_is_documented()
    test_helper_returns_pinned_metadata_value()
    print("All population rollup guardrails passed.")
