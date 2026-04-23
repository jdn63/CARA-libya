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
- Data connectors: utils/connectors/ (WHO GHO, IDMC, IOM, OpenAQ, EM-DAT, World Bank; NCDC Libya and COI file-upload stubs)
- Configuration: config/jurisdiction.yaml, config/risk_weights.yaml, config/profiles/libya.yaml
- Routes: routes/public.py (home, methodology, about, data-sources), routes/dashboard.py, routes/api.py

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
WHO GHO, IDMC, IOM DTM (file upload), EM-DAT, World Bank, OpenAQ, NCDC Libya (file upload), COI (file upload)
Upload directories: data/uploads/ncdc/, data/uploads/coi/, data/uploads/iom/

## Wisconsin Cleanup Status
herc_bp and gis_export_bp removed from routes/__init__.py.
routes/api.py rewritten with Libya-specific endpoints only.
Legacy files (routes/herc.py, routes/gis_export.py, utils/herc_data.py, utils/wem_data.py) remain on disk but are not registered or imported by active code paths.
