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
- Risk Engine: utils/risk_engine.py — INFORM geometric mean formula
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
- 106 municipalities populated as of initial dataset; 42 flagged needs_verification
- Districts organized under each region in data/libya_municipalities.json

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

## Wisconsin Cleanup Status (April 2026)
The following Wisconsin/HERC-specific files have been permanently deleted:
- routes/herc.py
- config/county_baselines.yaml
- config/profiles/us_state.yaml
- templates/herc_dashboard.html, herc_print_summary.html, action_plan.html (Wisconsin), active_shooter_methodology.html
- utils/wisconsin_climate_data.py, wisconsin_dhs_scraper.py, wisconsin_mapping.py
- utils/herc_data.py, herc_risk_aggregator.py, kp_hva_export.py, hva_export.py
Additional files deleted (April 2026):
- utils/active_shooter_risk.py, utils/main_risk_calculator.py (imported it), routes/gis_export.py (referenced it, was unregistered)
- utils/gva_data_processor.py, data/gva_reports/ (GunViolenceArchive data)
- utils/natural_hazards_risk.py (called load_nri_data for US counties only)
- attached_assets/active_shooter_risk_model_config.json, Active_Shooter_Risk_Scoring_Framework.txt
- attached_assets/kp_incident_log_hva_(5)_1771953905117.xlsm
- attached_assets/NRI_Table_CensusTracts_Wisconsin_FloodTornadoWinterOnly.csv
Remaining US-specific utility files (census_data_loader.py, dhs_data.py, etc.) are inert — not imported by any active Libya code path.

## Test Suite
tests/smoke_test.py: 14 tests, all pass.
Includes test_inform_formula_cube_root() validating the INFORM (H x V x C)^(1/3) geometric mean formula with 4 known-value cases.
All PHRAT pipeline terminology replaced with INFORM/composite terminology throughout.

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
