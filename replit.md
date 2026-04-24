# Libya CARA - Comprehensive Assessment of Risk Analytics

## Overview
Libya CARA is a bilingual (Arabic primary, English secondary) subnational risk assessment platform for Libya. It scores disaster and crisis risk at the national level and across 148 municipalities using the INFORM Risk Index methodology, aligned with the Sendai Framework for Disaster Risk Reduction 2015-2030. Access is restricted to official government use.

## User Preferences
Preferred communication style: Simple, everyday language.

DOCUMENTATION FORMATTING RULES (permanent, applies to every file without exception):
- Never add icons, emoji, or decorative symbols anywhere in any file.
- Never use box-drawing or tree-drawing characters. Use plain ASCII indentation or prose instead.
- Never use the multiplication sign or similar non-standard punctuation as a bullet or separator.
- Do not use decorative horizontal dividers made of repeated symbols unless required by Markdown table syntax.
- Keep all documentation plain and professional. No decorative formatting.

## System Architecture

### Backend
- Framework: Flask (Python), gunicorn, PostgreSQL
- Risk Engine: utils/domains/ pillar modules compute per-pillar scores; routes/dashboard.py/_run_pillars() composes the INFORM geometric mean (H x V x C)^(1/3)
- Geography: utils/geography/jurisdiction_manager.py — loads 148 municipalities from data/libya_municipalities.json, regional proxy fallback
- Domain modules: utils/domains/ (hazard_exposure.py, vulnerability.py, coping_capacity.py)
- Data connectors: utils/connectors/ — see full list in Data Sources section
- Automated refresh: APScheduler (BackgroundScheduler) — two jobs registered when CARA_PROFILE=libya:
    - refresh_libya_hdx: every 168 hours (7 days) — IOM DTM, OCHA 3W, UNHCR (HDX CKAN); HeiGIT accessibility CSVs; IDMC displacement CSVs (direct IDMC API returns 403)
    - refresh_libya_global: every 720 hours (30 days) — WHO Libya via HDX (primary); WHO GHO (legacy fallback); World Bank; OpenAQ
- CARA_PROFILE environment variable: set to "libya" in shared environment to activate Libya scheduler
- Configuration: config/jurisdiction.yaml, config/risk_weights.yaml, config/profiles/libya.yaml
- Routes: routes/public.py (home, methodology, about, data-sources), routes/dashboard.py (dashboard + action plan), routes/api.py
- Action Plan: GET /action-plan/<jurisdiction_id> — bilingual RTL preparedness action plan; reuses _run_pillars(); calls utils/action_plan_content.get_action_domains() to produce 11 INFORM-component domains sorted by score; each domain has 3-tier timeline (0-3mo / 3-12mo / 1-3yr) in Arabic+English with UN Cluster + Libyan govt counterpart + Sendai priority; template: templates/action_plan_libya.html; linked from dashboard "خطة العمل" button; print CSS included
- Dashboard connector pipeline: routes/dashboard.py/_load_connector_data() loads who_hdx, idmc_hdx, heigit, iom, worldbank, coi_libya, ncdc_libya from disk cache and normalises keys for domain modules (who_hdx beds per 10k divided by 10 to get per 1000; idmc_hdx total_displacement_stock mapped to idmc.total_idps; etc.)
- Dashboard sub-domain key mapping: domain modules use sub_domains (hazard) or indicators (vulnerability, coping) as the nested score dict; _run_pillars() flattens both into a uniform components dict for the template
- Formula transparency: _build_show_work() in dashboard.py builds per-sub-domain Bootstrap popover HTML with raw indicator values, formula string, and data source attribution; passed to template as show_work dict keyed by 'pillar__sub_domain'
- Granular indicator tiles: _build_indicator_tiles(cd, jurisdiction_id, is_national) in dashboard.py builds a 3-level hierarchy (pillar > sub-domain section > individual tile) with 34 individual indicator tiles across 12 sub-domain sections; each tile has id, labels, raw value, unit, year, 0-1 score, 0-10 display, risk level, badge colour, availability flag, proxy flag, source, source_kind, agency, formula, note, and pre-built popover_html; rendered in dashboard.html as a Bootstrap accordion below the 3-pillar summary
- Local-data overrides + transparency badges: utils/local_overrides.py builds an mtime-cached index of every consolidated municipal upload; on subnational dashboards _build_indicator_tiles substitutes uploaded values for 7 mappable indicators (tb_inc, u5mort, neo_mort, water, sanitation, electricity, pm25) and _stamp_source_kinds tags every tile with one of {'local', 'national_proxy', 'national', 'proxy', 'measured'} — the template renders a green "محلي / Local" badge for uploaded data and an amber "وطني / National" badge whenever a country-level WHO/WB figure is being applied as a per-municipality proxy. The national LY view never applies overrides and never shows badges.
- Popover HTML escaping: popover_html is built as a Python string in _T() and passed through Jinja2 | e in the template, converting < > " to HTML entities; the browser decodes entities on attribute read, Bootstrap sets innerHTML with html:true; this avoids the attribute-breaking bare-less-than bug that caused popovers to show only their title

### Frontend
- RTL layout, Bootstrap 5 RTL build
- Arabic (MSA) primary, English secondary on all UI elements
- Fonts: Cairo/Tajawal (Arabic), Inter (English)
- CSS: static/css/cara-libya.css
- JS: static/js/cara-libya.js (risk scoring helpers, cache, accessibility)
- Templates: templates/base.html, templates/index.html, templates/methodology.html, templates/about.html, templates/data_sources.html, templates/components/navigation.html, templates/components/footer.html

### INFORM Risk Formula
INFORM Risk = (Hazard and Exposure x Vulnerability x Lack of Coping Capacity) to the power of 1/3

Pillar 1 (Hazard and Exposure): infrastructure risk, natural hazards, disease, road accidents
Pillar 2 (Vulnerability): response capacity gaps, urban sprawl, displacement, health literacy, security fragility
Pillar 3 (Lack of Coping Capacity): emergency response time, data availability, organizations, healthcare, poverty

## Geography
- National assessment: Libya (LY)
- 148 municipalities across 3 regions: West (الغرب), East (الشرق), South (الجنوب)
- 106 municipalities populated as of initial dataset; 42 still pending addition to reach the 148 target
- Districts organized under each region in data/libya_municipalities.json
- Population provenance (per-baladiya): OCHA Libya HNO 2021 (CC BY 4.0, via HDX) — Non-displaced + Returnees columns. National anchor: UN World Population Prospects 2024 medium variant = 7,458,567. Refresh script: scripts/refresh_population.py (--dry-run, --no-fetch, --print-deltas, --audit-log). Each entry carries population_year, population_source, population_method, population_status, population_in_national_total, and (for verified entries) population_ocha_pcode + population_match_confidence (exact|high|approximate). Audit logs written to data/cache/hdx/audit/.
- Population status distribution: 59 verified_ocha (matched to OCHA HNO baladiya, in_national_total=True), 18 sub_baladiya_estimate (admin-4 muhalla zones inside Tripoli LY021104 / Benghazi LY010304, in_national_total=False to prevent double-counting their parent baladiya), 29 estimated_pending_verification (small villages outside HNO 100, in_national_total=True). Tests: tests/test_population_data.py (21 tests).
- National rollups MUST sum only entries where population_in_national_total is True. This deduped figure is also pre-computed and pinned at _metadata.national_total_deduped (currently 6,658,098 ≈ 89.3% of UN WPP 2024). The shortfall is real and reflects the ~41 OCHA HNO baladiyas not yet matched in this file — see _metadata.data_gap_note. The naive sum across all 106 entries (7,888,098) double-counts the Tripoli/Benghazi muhalla overlays and must NOT be used for national rollups.

## Key Design Decisions
- Armed clashes domain: OMITTED pending further political sensitivity review
- Missing data: Regional average proxy (documented, audit-logged) shown with explicit "البيانات غير متاحة / Data not available" label
- Domain weights: Equal-ish, fixed post-deployment, workshop-validated
- Access: Restricted government use only; no public access
- Low-connectivity: Cache-first operation; sessionStorage caching in JS

## Data Sources

Automated (APScheduler, no credentials required) — weekly 168h job:
- OCHA HDX (data.humdata.org/api/3/) — IOM DTM displacement, OCHA 3W presence, UNHCR Libya — cache: data/cache/hdx/
- HeiGIT Accessibility (hot.storage.heigit.org) — hospital, primary healthcare, education access by district (22 ADM1 units, propagated to all 148 municipalities as documented proxy) — cache: data/cache/heigit/ — INFORM: Coping Capacity / healthcare_access_gap
- IDMC via OCHA HDX (replaces direct IDMC API which returns 403) — annual conflict IDPs, IDP stock, disaster displacement events — cache: data/cache/idmc/ — INFORM: Vulnerability / displacement_vulnerability

Automated — monthly 720h job:
- WHO Libya via OCHA HDX (primary, April 2026 — replaces stale WHO GHO OData API for Libya) — 7 CSV files, 17 health indicators — cache: data/cache/who_hdx/ — INFORM: all three pillars
- WHO GHO (ghoapi.azureedge.net/api/) — legacy fallback only; returns stale Libya data (2008–2018 vintage)
- World Bank Open Data (api.worldbank.org/v2/) — development indicators — monthly
- OpenAQ (api.openaq.org/v2/) — air quality (no Libya stations confirmed as of April 2026)
- Scheduler config: data/config/scheduler_config.json

Connector registry: utils/connector_registry.py
Registered connectors: hdx, heigit, idmc_hdx, who_hdx, iom, who_gho, worldbank, openaq, ncdc_libya, coi_libya

File-based (public download, no API key required):
- EM-DAT (CRED/UCLouvain): data/emdat_libya.xlsx — Libya disaster history 2000-present; 76 records; file-based connector reads directly; update by re-downloading from emdat.be and replacing the file. Data version: 2026-04-17. INFORM: Hazard & Exposure / hydrometeorological_hazard — Key event: Storm Daniel 2023 (13,200 deaths, 1.6M affected, $6.2B damage)

Manual upload (no public API — restricted government data):
- NCDC Libya: data/uploads/ncdc/ (disease surveillance CSV)
- COI Libya: data/uploads/coi/ (coordination capacity CSV)
- IOM DTM fallback: data/uploads/iom/ (if HDX download fails)

## Access Control
Authentication is implemented via a before_request hook in app.py.
Set the CARA_ACCESS_PASSWORD Replit secret to enable password-gating.
If CARA_ACCESS_PASSWORD is not set the tool runs in open mode (development only).
Login route: /login (GET renders bilingual form; POST validates password and sets session).
Logout route: /logout (clears session, redirects to login).
Exempt from auth: /static/, /login, /logout, /health
Logout button is visible in the top navigation bar at all times.

## Health Check
GET /health returns JSON: status, service, municipalities_loaded, municipalities_target, data_coverage_pct.
No authentication required. Suitable for readiness probes and monitoring agents.

## Logging & Audit Trail
Wired in `core._setup_logging()` (called from `initialize_app`). Three channels under `logs/` (git-ignored):
- `logs/cara_app.log` — JSON-structured app log, 10 MB × 10 rotation, includes Flask request context (URL, IP, user-agent) for debugging.
- `logs/cara_errors.log` — ERROR-only mirror, 10 MB × 5 rotation.
- `logs/cara_audit.log` — partner-auditable trail, JSON, 5 MB × 30 rotation, **PII-free** (`include_request_context=False`). Records two event types today:
  - `upload_accepted` — when a workshop xlsx is saved (master/master_split/single_domain), with domain, source filename, stored path, byte count.
  - `local_override_applied` — when a municipal upload replaces a national value on the dashboard, with jurisdiction, indicator code, agency, year, replaced/new values. Per-request dedupe via `g._audit_overrides_seen`.
Use `from utils.logging_config import audit; audit('event_name', **fields)` to add new audit events.
Optional Sentry integration auto-activates when `SENTRY_DSN` is set (sentry-sdk already in deps).

## Wisconsin / HERC / Tribal Cleanup Status (April 2026)

Earlier removals (prior tasks):
- routes/herc.py; routes/gis_export.py (unregistered)
- config/county_baselines.yaml; config/profiles/us_state.yaml
- templates: herc_dashboard.html, herc_print_summary.html, action_plan.html (Wisconsin), active_shooter_methodology.html
- utils: wisconsin_climate_data.py, wisconsin_dhs_scraper.py, wisconsin_mapping.py, herc_data.py, herc_risk_aggregator.py, kp_hva_export.py, hva_export.py, active_shooter_risk.py, main_risk_calculator.py, gva_data_processor.py, natural_hazards_risk.py
- data/gva_reports/, attached_assets/ Wisconsin/active-shooter artefacts

Final purge (Task #7, April 2026): ~53 MB and ~50 source files removed; the codebase no longer carries any Wisconsin/HERC/tribal data, templates, JS, CSS, models, or utility modules.

Data + assets:
- data/tribal/, data/herc/, data/wi_herc_regions.geojson; data/svi/wisconsin_svi_data.json; data/disease/wisconsin_*.json; data/dam_inventory/wisconsin_dam_risk_factors.json; data/census/wisconsin_*.csv + README_DATA_SOURCES.md; data/climate/natural_hazard_climate_projections.json; data/noaa_storm_events/ (25 MB of Wisconsin storm CSVs 2008-2025); tribal_territories.json, wi_health_departments.json, wisconsin_tribal_areas.pdf
- Images: static/images/wisconsin_*.png; static/images/regions/wisconsin_*.png; attached_assets/tribalgovernmentmap600.png; attached_assets/Wisconsin_Local_Public_Health_Department_Office_Boundaries.geojson (7.2 MB)
- Stray export: HERC_Region_1_HVA_Export.xlsx

Templates (8 deleted, 4 fixed):
- Deleted (zero render_template hits): results.html, print_summary.html, docs/quick_start_guide.html, docs/faq.html
- Edited: templates/errors/404.html and 400.html replaced dead /docs/faq links with /methodology
- Edited: templates/errors/500.html replaced "For Wisconsin Public Health Officials / regional HERC coordinator" block with bilingual "For Authorised Users" Libya CARA admin contact text
- Edited: templates/errors/503.html replaced Wisconsin Emergency Management phone numbers with bilingual Libyan civil-defence / MoH EOC / Red Crescent guidance

Utilities (29 modules deleted in total):
- Direct Wisconsin (16): tribal_boundaries.py, tribal_air_quality_mapping.py, dam_failure_risk.py, svi_data.py, census_data_loader.py, vector_borne_disease_risk.py, vbd_data_fetcher.py, dhs_data.py, weather_alerts.py, data_freshness.py, data_processor.py, risk_engine.py, air_quality_data.py, heat_vulnerability.py, boundary_mapping.py, correctional_facilities.py
- Cascade-orphan (11) whose only callers were the 16 above: em_comparison_export.py, export_job_worker.py, utilities_risk.py, update_risk_functions.py, temporal_risk.py, real_trend_calculator.py, gis_export.py, extreme_heat_metrics.py, disease_surveillance.py, data_source_refresher.py, data_refresh_scheduler.py
- Cascade-orphan (4) discovered in the second pass: noaa_storm_events.py, openfema_data.py, data_cache_manager.py (the cache layer they shared), scheduler_init.py (only imported the deleted data_refresh_scheduler)
- Third-pass dead-orphan utilities (20) discovered after architect re-review — none had any importer outside utils/ itself, and the only intra-utils edge (climate_adjusted_risk → risk_calculation) was inside the deleted set: web_scraper.py (Wisconsin DHS scraping), nces_ssocs_processor.py (Wisconsin schools), strategic_extreme_heat.py + strategic_air_quality.py (WICCI/Wisconsin DNR projections), map_generator.py (Wisconsin folium map), jurisdictions_code.py + jurisdiction_mapping_code.py (Wisconsin county directory), security_manager.py (Wisconsin PH API key bank), jurisdiction_geojson.py (Wisconsin LPHD boundaries), risk_calculation.py (Wisconsin NRI lookup), geo_data.py + predictive_analysis.py (HERC/WEM boundary helpers), ph_data.py + wha_integration.py (Wisconsin Hospital Association), nid_data.py (USACE NID Wisconsin dam fetcher), email_notifications.py (HERC integration field), wem_data.py + wem_integration.py (Wisconsin Emergency Management WebEOC), download_census_data.py (Wisconsin ACS pull), climate_adjusted_risk.py (Wisconsin heat-vulnerability heuristics)

Dead scripts: scripts/precompute_em_comparison.py, scripts/fetch_nid_data.py
Legacy module: routes.py (the routes/ package shadowed it on Python import; never executed)
Models: removed HERCRiskCache class from models.py (zero usages; no other code reads herc_risk_cache table). Note: the application uses db.create_all() with no migration framework, so no migration step is required for runtime — but existing development/production databases will retain a stale, never-touched herc_risk_cache table until manually dropped. Optional cleanup: `DROP TABLE IF EXISTS herc_risk_cache;`.
Workflow: removed orphan "artifacts/mockup-sandbox: Component Preview Server"

Frontend JS purge:
- The new Libya UI loads ONLY static/js/cara-libya.js from templates/base.html (plus inline scripts in a few page templates such as templates/action_plan_libya.html that own their own jurisdiction-display element).
- Confirmed via grep that templates/components/scripts.html (the Wisconsin-era partial that loaded the modules/ chain) was referenced by no template, and that the entire static/js/modules/ chain (utils.js, navigation.js, accessibility.js, legacy-navigation.js, dashboard.js) plus the top-level static/js/{index,main,accessibility,lazy-load,performance,return-to-top}.js files were never loaded by any live template either. No template references any of selectJurisdiction(), StorageUtils.*, DomUtils.*, ModalManager.*, getRiskLevel(), getRiskColor(), getColorForRisk(), or legacy-navigation symbols.
- All of the above were deleted: templates/components/scripts.html, static/js/modules/ (entire directory), and static/js/{index,main,accessibility,lazy-load,performance,return-to-top}.js.
- Net result: static/js/ now contains exactly one file — cara-libya.js — which exposes window.CARA.{getRiskClass,getRiskColor,getRiskLabelAr,scoreToLevel,...}.

CSS (static/css/custom.css):
- Deleted ~205 lines of dead .herc-label / .herc-control / .herc-stats-panel / .wem-label / .wem-stats-panel rules + their @media (max-width: 768px) and @media print companion blocks (no template referenced any of these classes)
- Updated print @page top-center branding from "CARA - Wisconsin Public Health Risk Assessment" to "Libya CARA - Climate Adaptation & Risk Assessment"

Known status to flag (out of Task #7 scope):
- **Authentication is currently disabled.** `app.py:_require_login()` returns `None` unconditionally
  (commit 55abc1a "Disable login requirement for all users temporarily" by jdn63 on 2026-04-23).
  This was a deliberate pre-Task-#7 user decision and has been preserved as-is to honour the
  "temporarily" intent. To re-enable: delete the early `return None` at app.py:70 and ensure
  `CARA_ACCESS_PASSWORD` is set in Replit Secrets for both workspace and deployment. Re-enabling
  is a strict prerequisite to the "official government use only" / restricted-access posture
  described in this README and should be tracked as a follow-up task before any public-facing
  publish.

Known retained-on-purpose items (NOT dead, NOT to delete in this task):
- utils/cache_config.py and utils/planning_mode_config.py still list a "tribal_boundaries" cache key / planning-mode flag — these are config catalogue entries with no live readers (the producers were deleted) and will become orphan data on the next config audit.
- utils/metadata_config.py still lists tribal_status / tribal_counties / tribal_primary_county metadata field names; the consuming Wisconsin jurisdictions code is gone, but Libyan governorate metadata may want analogous fields.

## us_state Scaffolding Removal (Task #12, April 2026)

**Decision: option (a) — REMOVED the us_state scaffolding entirely.**

Rationale: Libya is the sole live deployment, the us_state branch was never executed, and Task #9 explicitly deferred the cleanup. Committing to us_state as a real future-fork target (option b) would have required building config/profiles/us_state.yaml, real (non-stub) connector implementations, and dedicated smoke tests — work no current stakeholder is sponsoring. Carrying dead skeletons indefinitely was the worst of both worlds, so the skeleton was deleted. A future US fork can be reintroduced cleanly from version control history if the need ever arises.

What was deleted:
- utils/connectors/us/ (entire directory: airnow, nws, open_fema, cdc_nssp connectors + __init__.py + README.md)
- utils/domains/dam_failure.py (us_state-only module, never in DOMAIN_CLASS_MAP)
- docs/adapting_for_us_state.md
- core.py: `elif profile == "us_state":` scheduler branch and `_refresh_us_data()` function
- utils/connector_registry.py: airnow / nws / open_fema / cdc_nssp elif branches
- config/risk_weights.yaml: entire `us_state:` profiles block
- utils/domains/mass_casualty.py: `US_WEIGHTS` constant, `_calculate_us()` method, `us_subtype` branch in `calculate()`, US-specific docstring + data sources + `us_active_shooter_subtype` payload
- utils/domains/conflict_displacement.py: `if profile == 'us_state'` early-return guard
- tests/smoke_test.py: `domain_config: {mass_casualty: {us_subtype: False}}` fixture entry
- config/profiles/international.yaml: orphan `domain_config.mass_casualty.us_subtype: false`, `include_firearm_data: false`, and `disabled: [dam_failure]` entries (the consuming code paths are gone)
- .env.example: `AIRNOW_API_KEY` and `CENSUS_API_KEY` lines (US-only; no live consumer)

What was rewritten:
- `applicable_profiles` lists across 7 domain modules (health_metrics, vector_borne_disease, natural_hazards, extreme_heat, air_quality, mass_casualty, plus base_domain.py docstring) changed from `["us_state", "international"]` to `["libya", "international"]`
- Domain module docstrings (air_quality, extreme_heat, natural_hazards, vector_borne_disease, mass_casualty) and their domain_info() descriptions: dropped "US deployments: ..." bullet lines and US sub-type prose; kept the international data-source language only
- docs/configuration_reference.md: profile values, env-var description, and profiles/ directory listing now read `libya | international` (not `us_state | international`); AIRNOW_API_KEY / CENSUS_API_KEY rows removed from the env-var table
- docs/adding_custom_connector.md: example connector path is now `utils/connectors/worldwide/` (not `utils/connectors/us/`); profile YAML reference is now `libya.yaml` (not `us_state.yaml`)

Verification: `pytest -q` — 81/81 pass (smoke 7/7 + INFORM 14/14 + pillar indicators + others).

Out of scope (left as-is, flagged for future cleanup): docs/template_review_findings.md is a historical April-2026 snapshot and still references the now-deleted us_state.yaml / dam_failure.py — preserved as a dated review document.

Active-shooter sweep (April 2026, completed): removed every remaining "active_shooter" / "Active Shooter Risk" reference from live code paths and rewrote the methodology / data-source / data-dictionary / api-management docs to describe the Libya INFORM pipeline. Deletions: utils/frameworks/ (dead CDC PHEP / WHO IHR scaffolding never read by Python — assessment_framework YAML key has no consumer), utils/report_generator.py (referenced an undefined active_shooter_risk key and was unimported anywhere). Edits: utils/risk_alignment.py (dropped active_shooter entries from major_risks dict and name_mapping; file remains unimported but is now scrubbed), utils/config_manager.py (removed active_shooter from _load_fallback_config and updated the docstring example to use INFORM pillar names). Doc rewrites: docs/risk_assessment_methodology.md, docs/risk_assessment_comprehensive_methodology.md, docs/data_sources_comprehensive_analysis.md, docs/data_dictionary.md, docs/api_management_guide.md (removed FBI_CRIME_DATA_API_KEY / CENSUS_API_KEY references). Workshop guides (docs/CARA_Adaptation_Workshop_Guide.md, docs/CARA_Replit_Workshop_Guide.md): replaced Active-Shooter example domains with neutral examples; broader Wisconsin-to-X adaptation framing intentionally retained as the guides remain useful as adaptation training material.

Compensating fix in core utility:
- utils/action_plan_content.py used the deleted risk_engine.classify_risk(); replaced with a local _inform_classify() banding helper (very_low / low / medium / high / very_high using upper-exclusive 0.20 / 0.40 / 0.60 / 0.80 cut points; non-numeric or negative input returns "unavailable").

Note on remaining "tribal" string matches in utils/action_plan_content.py: those refer to Libyan tribal networks and religious institutions as a social-cohesion / coping resource, not Wisconsin tribal nations, and are intentionally retained.

## Test Suite
81 tests total, all pass via `pytest -q`.

tests/smoke_test.py: 7 tests. Each exercises the Libya domain pipeline:
domain modules import, instantiate, return required keys (location, score, dominant_factor, available),
keep score in 0..1, and return non-empty strings for dominant_factor and the data-availability flag.

tests/test_inform.py: 14 tests covering the INFORM Risk Index pipeline:
- 6 cube-root composition tests on routes.dashboard._compute_inform_score
  (all-zero, all-one, equal-mixed 0.5/0.5/0.5, asymmetric 0.8/0.5/0.2, one-missing-pillar
  collapses to 0, unequal 0.4/0.6/0.8).
- 6 banding cut-point tests on utils.action_plan_content._inform_classify covering all
  five bands (very_low / low / medium / high / very_high) at and around the 0.20 / 0.40 /
  0.60 / 0.80 cut points, plus the unavailable path for None / non-numeric / negative input.
- 1 end-to-end consistency test that monkeypatches routes.dashboard._load_connector_data
  with an empty dict (forcing the documented proxy fallbacks), runs _run_pillars('LY', ...),
  and asserts the headline INFORM score equals (h*v*c)^(1/3) of the three pillar scores it
  produced and that the formula_values block and level banding are internally consistent.
- 1 end-to-end deterministic fixture test that pins each pillar domain's calculate() return
  to fixed scores (h=0.5, v=0.4, c=0.6) and asserts the exact expected national INFORM score
  (0.4932), formula_values block (h=5.0, v=4.0, c=6.0, result=4.9), dashboard level
  ('moderate' / 'warning' badge), and action-plan template band ('medium').

tests/test_pillar_indicators.py: 37 tests covering each sub-indicator helper inside the three
Libya pillar domain modules (utils/domains/hazard_exposure.py, utils/domains/vulnerability.py,
utils/domains/coping_capacity.py). Two cases per helper — "real connector data present" (asserting
the exact 0-1 score the helper returns and proxy_used=False) and "data missing -> proxy"
(asserting the documented fallback constant and proxy_used=True) — across 14 helpers:
_infrastructure_hazard, _natural_hazard, _epidemiological_hazard, _road_safety_hazard
(Pillar 1); _agency_capacity_gap, _urban_sprawl, _displacement_vulnerability, _health_unawareness,
_security_vulnerability (Pillar 2); _response_time_gap, _data_availability_gap,
_community_support_gap, _healthcare_access_gap, _poverty_vulnerability (Pillar 3). Plus the
_weighted_average helper exercised with fully-populated, partial (one missing indicator
rescaled), and all-missing inputs across all three pillar domains (3 cases x 3 domains =
9 tests). Note: _weighted_average currently lives on each pillar class (HazardExposureDomain,
VulnerabilityDomain, CopingCapacityDomain) rather than on BaseDomain; the three
implementations are nearly identical and tested independently. Consolidation onto BaseDomain
is tracked as a follow-up. Together these pin each branch so a regression in any single
sub-indicator or aggregation step cannot silently produce an in-range pillar score and a
plausible-looking INFORM number.

tests/test_login_redirect.py: 23 tests covering safe redirect-target validation on the
/login route (relative-path-only, blocks scheme/netloc/protocol-relative URLs, collapses
unsafe inputs to root).

The 7 legacy Wisconsin/PHRAT pipeline tests (load_weights_international, composite_score_valid_range,
inform_formula_cube_root via risk_engine, classify_risk, compute_all_domains_returns_all_7_international_domains,
risk_engine_end_to_end_pipeline, data_processor_orchestration) were removed when the underlying
risk_engine.py and data_processor.py modules were deleted; the new tests/test_inform.py covers
the equivalent INFORM-formula coverage against the current routes/dashboard.py/_run_pillars() pipeline.

## Local-Agency Data Entry
Domain-driven pipeline that lets local response agencies upload municipal-level data via Excel.
- Registry: utils/data_entry_domains.py — DomainSpec dataclass + 5 workshop domains:
    - infectious-disease (HIV, HBV, HCV, TB x incidence/morbidity/mortality)
    - vector-borne-disease (Malaria, Dengue, Leishmaniasis x same)
    - ncds (Diabetes, Hypertension, CVD, Cancer x prevalence/morbidity/mortality)
    - maternal-child-health (6 flat indicators, mixed units)
    - environmental-health (5 flat indicators: water, sanitation, electricity, waste, PM2.5)
- DomainSpec.sheet_title: short (<=31 char) English worksheet name used inside the master workbook.
- Engine: utils/local_agency_data.py — schema-agnostic, consumes a DomainSpec to build template, consolidate uploads, build export. _populate_data_entry_sheet() is the shared per-tab builder reused by both single-domain and master templates.
- Routes: routes/data_entry.py
    Per-domain (for partners with data in only one area):
        GET  /data-entry/                       hub
        GET  /data-entry/<key>                  download/upload/compare
        GET  /data-entry/<key>/template.xlsx    single-domain template
        POST /data-entry/<key>/upload           ingest single-domain workbook
        GET  /data-entry/<key>/export.xlsx      single-domain comparison
    Master (primary CTA, one file, all domains):
        GET  /data-entry/master                 master landing page with per-tab status
        GET  /data-entry/master/template.xlsx   combined template (1 Instructions tab + 5 domain tabs)
        POST /data-entry/master/upload          split per tab, ingest non-empty tabs, skip empty tabs
        GET  /data-entry/master/export.xlsx     combined comparison workbook (5 sheets)
- Templates: templates/data_entry/index.html (hub + master CTA), templates/data_entry/master.html (master page), templates/data_entry/domain.html (generic single-domain page).
- Storage: data/uploads/local_agencies/<domain_key>/ (timestamped audit trail; files never deleted). Master uploads are split into one standalone per-domain workbook per non-empty tab and saved as TIMESTAMP__master__STEM__DOMAIN.xlsx so the existing consolidation logic is unchanged.
- Partial-submission rule: a master tab is ingested only if it has at least one row with municipality_id + valid capture_date + at least one non-blank indicator. Empty tabs are SKIPPED, never "cleared" — previously submitted data is preserved.
- Domain marker: every generated workbook embeds cara_libya_domain_key as a custom workbook property. Single-domain files carry the domain slug; master files carry "__libya_cara_master__". Upload routes reject files whose marker doesn't match the endpoint, with bilingual flashes that point the user to the correct page.
- Security: filename sanitization, OOXML zip validation, hard 10MB cap (no Content-Length trust), formula-injection guard (_safe_text neutralises leading = + - @ on every text cell in exports).
- Consolidation: latest capture per municipality wins; on date ties, newer upload (mtime) wins deterministically.
- Date bounds: _parse_date rejects dates outside [2000-01-01, today] so a user who bypasses Excel data validation cannot poison the comparison table.
- Adding a new domain is a pure-data change: append a DomainSpec to utils.data_entry_domains.DOMAINS (set a sheet_title <=31 chars to control the master tab name).

## Bootstrap Icons
Bootstrap Icons CDN (v1.11.3) is loaded in templates/base.html and templates/login.html.
Used in action_plan_libya.html for bi-arrow-right-circle and bi-printer icons.
