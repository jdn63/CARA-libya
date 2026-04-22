# CARA Template Review: Findings for Smooth Jurisdiction Adaptation

This document records the results of a code-and-docs review of `cara_template/`
performed in April 2026 in parallel with the Wisconsin documentation alignment
audit. The goals were to (a) confirm the template did not inherit the same
documentation drift items found in the Wisconsin live deployment, and (b) flag
any obstacles a new jurisdiction would hit when adapting the template.

## Documentation alignment with the Wisconsin audit

The four documentation drift items recently fixed in the Wisconsin codebase
were checked against the template. Status:

- Reference to a deprecated WI DHS Tableau scraper: not present in the template.
  No `web_scraper`, `wisconsin_dhs`, or `Tableau` strings appear outside of the
  README's section that explicitly identifies Wisconsin as the reference
  implementation.
- Wrong EVR formula (the dividing-by-resilience form): not present. The
  template uses a weighted-sum form
  `0.40 * Exposure + 0.30 * Vulnerability + 0.20 * (1 - Resilience) + 0.10 * HealthImpact`,
  which is a deliberate template-level design choice, not drift.
- `v2.1` version stamps inconsistent with `VERSION.txt`: not present.
  `VERSION.txt` is `1.0.0` and the docs match.
- `ENABLE_SCRAPERS` described as scraper-specific: already correctly described
  in `docs/configuration_reference.md` as a generic scheduler toggle.

The one related gap that did exist in the template, and was fixed in this
review, was that `methodology.html` did not document the PHRAT
domain-dropout / weight-rescaling behavior that `risk_engine.calculate_phrat()`
already implements (the `data_coverage` field returned in the breakdown). A
paragraph was added explaining this.

## Bugs blocking smooth jurisdiction adaptation

The following items were fixed as part of this review.

1. `routes.py` `/dashboard` did not pass the variables that
   `templates/dashboard.html` actually expects. The route was passing
   `total_score, risk_level, domain_results, breakdown, regional_group`, but
   the template reads `composite{score, tier, tier_color}, domains[],
   action_items, all_jurisdictions, last_refresh, framework_name, top_domain`.
   Out of the box this would render an empty dashboard. The route now builds
   each of those view models before rendering, so a fresh deployment can
   render a working dashboard with no template edits.

2. `routes.py` `/methodology` only passed `(profile, framework)`, but
   `templates/methodology.html` expects
   `domains, data_source_detail, framework_name, framework_key,
   jurisdiction_name`. The route now loads weights from `risk_engine`,
   reads optional `domains:` and `data_source_detail:` blocks from the
   profile YAML if present, and passes them through.

3. Risk band labels diverged across three files. `classify_risk()` in
   `utils/risk_engine.py` defines five bands (Critical, High, Moderate, Low,
   Minimal) with breakpoints at 0.75 / 0.55 / 0.35 / 0.15 / 0.0, but
   `dashboard.html` and `methodology.html` advertised four bands with
   different breakpoints. Both templates were updated to match the
   `classify_risk()` thresholds. The configuration reference in
   `docs/configuration_reference.md` already used the correct thresholds.

4. `core.py _refresh_us_data()` was an empty stub. It is now implemented
   symmetrically with `_refresh_global_data()`, instantiating the
   `us_state` profile registry and calling `fetch()` on each available
   connector.

## Items NOT auto-fixed (recommended follow-up)

5. Wisconsin-specific HERC (Healthcare Emergency Readiness Coalition) leakage
   in `static/`. These files contain hard-coded references to HERC region
   selectors and the `/herc-dashboard/<id>` and `/herc-data/<id>` routes
   that the template's `routes.py` does not provide:
   - `static/js/index.js` (lines 9-46)
   - `static/js/modules/navigation.js` (multiple methods)
   - `static/js/modules/utils.js` (the `selectedHercId` / `selectedHercName`
     localStorage helpers)
   - `static/js/main.js` (window-scoped HERC functions)
   - `static/css/custom.css` (`.herc-label`, `.herc-control` block)

   Recommendation: replace HERC-specific naming with the generic
   `regional_group` concept already present in `jurisdiction.yaml` and
   exposed via `JurisdictionManager.get_group_for_jurisdiction()`. A new
   jurisdiction adapting the template can use this generic regional grouping
   without editing JS or CSS.

6. `routes.py` does not yet read from `JurisdictionCache` /
   `ConnectorDataCache`. Today the dashboard route fetches every connector
   on every page load, which is fine for development but will be slow for
   any real deployment with several connectors. The data models exist
   (`models.py` defines both cache tables) and `data_processor.py` defines
   `cache_result()` and `get_cached_result()` helpers, but the route does
   not call them. Wiring those calls is a small change but has been left
   out of this review to avoid changing runtime behavior unannounced.

7. `connector_registry._build_connector()` defaults `country_code` to `'XX'`
   when missing from `jurisdiction.yaml`. Every worldwide connector then
   silently fails or returns empty data for `'XX'`. Consider raising a
   loud `ValueError` (or at least a `logger.error`) when `'XX'` is detected
   at instantiation time, so misconfigured deployments fail fast instead of
   silently producing zero-score dashboards.

8. The `utils/connectors/us/` README references additional US connectors
   (FEMA NRI, CDC SVI, US Census, County Health Rankings, CDC PLACES,
   NOAA NCEI, USACE NID) that are not yet present as stub files. New US
   adapters will need to either implement these from the Wisconsin
   reference, or remove the references. Consider committing minimal stub
   files that raise `NotImplementedError` so the registry does not log
   `ImportError` warnings on startup for a default install.

## Profile and config files reviewed

- `config/profiles/us_state.yaml` (104 lines): clean, no Wisconsin-specific
  identifiers, weights sum to 1.0.
- `config/profiles/international.yaml` (132 lines): clean, weights sum to
  1.0.
- `config/risk_weights.yaml`: clean.
- `config/jurisdiction.yaml.example`: uses placeholder values throughout,
  flagged correctly by `core._validate_configuration()` at startup.

## Domain modules reviewed

`utils/domains/` contains nine modules (`air_quality`, `conflict_displacement`,
`dam_failure`, `extreme_heat`, `health_metrics`, `mass_casualty`,
`natural_hazards`, `vector_borne_disease`, plus `base_domain`). All read from
the generic `connector_data` dict the registry produces and use the same
EVR weighted-sum formulation; no domain hard-codes a Wisconsin connector
name. The pattern is sound for adaptation.

## Frameworks and geography modules

- `utils/frameworks/`: `who_ihr.py`, `cdc_phep.py`, `base_framework.py`
  present and selected at runtime by `routes._load_framework(profile)`.
- `utils/geography/`: `jurisdiction_manager.py` and `gadm_loader.py`
  present. `JurisdictionManager` is the canonical reader for
  `config/jurisdiction.yaml` and powers the `/dashboard/<id>` route.

## Summary

The template is in good shape for adaptation after the four route and template
fixes landed in this review. The remaining items (HERC leakage, caching
wiring, country-code validation, missing US connector stubs) are non-blocking
for a developer who reads the docs, but each one will eventually trip up a
first-time adapter. They are recorded here so they can be addressed in
priority order.
