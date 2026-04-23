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
- Routes: routes/public.py (home, methodology, about, data-sources), routes/dashboard.py, routes/api.py
- Dashboard connector pipeline: routes/dashboard.py/_load_connector_data() loads who_hdx, idmc_hdx, heigit, iom, worldbank, coi_libya, ncdc_libya from disk cache and normalises keys for domain modules (who_hdx beds per 10k divided by 10 to get per 1000; idmc_hdx total_displacement_stock mapped to idmc.total_idps; etc.)
- Dashboard sub-domain key mapping: domain modules use sub_domains (hazard) or indicators (vulnerability, coping) as the nested score dict; _run_pillars() flattens both into a uniform components dict for the template
- Formula transparency: _build_show_work() in dashboard.py builds per-sub-domain Bootstrap popover HTML with raw indicator values, formula string, and data source attribution; passed to template as show_work dict keyed by 'pillar__sub_domain'

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

Manual upload (no public API — restricted government data):
- NCDC Libya: data/uploads/ncdc/ (disease surveillance CSV)
- COI Libya: data/uploads/coi/ (coordination capacity CSV)
- IOM DTM fallback: data/uploads/iom/ (if HDX download fails)

## Wisconsin Cleanup Status
herc_bp and gis_export_bp removed from routes/__init__.py.
routes/api.py rewritten with Libya-specific endpoints only.
Legacy files (routes/herc.py, routes/gis_export.py, utils/herc_data.py, utils/wem_data.py) remain on disk but are not registered or imported by active code paths.
