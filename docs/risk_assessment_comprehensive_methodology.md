# Libya CARA - Comprehensive Risk Assessment Methodology

## 1. Overview

Libya CARA scores subnational disaster and crisis risk for Libya at
the national level (LY) and across 148 municipalities organised into
three regions (West, East, South). It uses the INFORM Risk Index
methodology published by the European Commission Joint Research
Centre (JRC) and the Inter-Agency Standing Committee (IASC),
explicitly aligned with the Sendai Framework for Disaster Risk
Reduction 2015-2030.

### 1.1 Geographic Coverage

- 148 municipalities loaded from `data/libya_municipalities.json`
  (utils/geography/jurisdiction_manager.py)
- 106 municipalities populated as of the initial dataset; 42 flagged
  `needs_verification`
- 22 ADM1 districts grouped under three regions:
  West (الغرب), East (الشرق), South (الجنوب)

### 1.2 INFORM Formula

```
INFORM Risk = (Hazard and Exposure x Vulnerability x Lack of Coping Capacity) ^ (1/3)
```

The geometric mean is the authoritative INFORM composition. Each
pillar is itself a weighted average of its sub-indicators on a [0, 1]
scale, where 1.0 represents the maximum risk and 0.0 represents no
risk. The three pillars are equally weighted (0.333 each) for the
published Libya profile.

The legacy PHRAT quadratic-mean formula is retained in
`config/risk_weights.yaml` (`phrat_formula_retained: true`) for
historical reference only and is NOT the active formula for Libya
deployments.

## 2. Pillar Weights and Sub-Indicators

All weights live in `config/risk_weights.yaml` under
`profiles.libya`. Bilingual labels (Arabic primary, English secondary)
are stored next to each weight.

### 2.1 Pillar 1 - Hazard and Exposure (weight 0.333)

| Sub-domain | Weight | Component (weight) |
|------------|--------|--------------------|
| Infrastructure Hazard | 0.25 | Dam Safety (0.333), Electric Grid Reliability (0.333), Water and Sewage Systems (0.333) |
| Natural Hazard | 0.25 | Flooding (0.30), Wildfires (0.20), Extreme Cold Events (0.25), Sandstorms (0.25) |
| Epidemiological Hazard | 0.25 | Infectious and Emerging Diseases (0.60), Vector-Borne Diseases (0.40) |
| Road Safety Hazard | 0.25 | Road Accident Rate (1.00) |

### 2.2 Pillar 2 - Vulnerability (weight 0.333)

Equal weights (0.20 each):

| Sub-indicator | Notes |
|---------------|-------|
| Response Agency Capacity Gap | Understaffing, underfunding of emergency response agencies |
| Urban Sprawl / Ad Hoc Construction | Rapid unplanned residential building increases structural risk |
| Displacement and Migration Vulnerability | IDPs and migrants face compounded risks |
| Lack of Health Awareness | Low health literacy amplifies disease burden and slows response |
| Security and Safety Vulnerability | Rate of violence and insecurity; armed-clashes domain omitted pending review |

### 2.3 Pillar 3 - Lack of Coping Capacity (weight 0.333)

Scores represent the LACK of coping capacity (high score = low
resilience). Each indicator is inverted from its positive form before
aggregation. Equal weights (0.20 each):

| Sub-indicator | Notes |
|---------------|-------|
| Emergency Response Time Gap | Longer ambulance and response times = higher lack of coping |
| Lack of Data Availability | Limited historical disaster data and interoperability reduce resilience |
| Community Support Gap | Weak community-level mutual support and civil society engagement |
| Healthcare Access Gap | Distance and travel time to hospitals and primary care facilities |
| Institutional Capacity Gap | Government institutional readiness for DRR investment |

### 2.4 Out of Scope by Design

The armed-clashes / political-violence domain present in the upstream
INFORM model is intentionally omitted from the published Libya score
pending a political sensitivity review. This decision is documented in
`replit.md` under "Key Design Decisions".

## 3. Data Sources and Connectors

All external data is fetched by APScheduler jobs (registered in
`core.py` when `CARA_PROFILE=libya`) and cached on disk under
`data/cache/`. No external API calls occur during user assessments.
The connector registry is `utils/connector_registry.py`.

### 3.1 Automated - Weekly (168 hours, `refresh_libya_hdx`)

| Source | Endpoint | Used For | Cache |
|--------|----------|----------|-------|
| OCHA HDX (CKAN) | data.humdata.org/api/3/ | IOM DTM displacement, OCHA 3W presence, UNHCR Libya | data/cache/hdx/ |
| HeiGIT Accessibility | hot.storage.heigit.org | Hospital, primary healthcare, education travel time by district (22 ADM1 units, propagated to 148 municipalities as documented proxy) | data/cache/heigit/ |
| IDMC via OCHA HDX | data.humdata.org/api/3/ | Annual conflict IDPs, IDP stock, disaster displacement events (replaces direct IDMC API which returns 403) | data/cache/idmc/ |

### 3.2 Automated - Monthly (720 hours, `refresh_libya_global`)

| Source | Endpoint | Used For |
|--------|----------|----------|
| WHO Libya via OCHA HDX (primary) | data.humdata.org/api/3/ | 7 CSV files, 17 health indicators (April 2026 cutover) |
| WHO GHO (legacy fallback) | ghoapi.azureedge.net/api/ | Returns stale Libya data (2008-2018 vintage) - fallback only |
| World Bank Open Data | api.worldbank.org/v2/ | Development indicators |
| OpenAQ | api.openaq.org/v2/ | Air quality readings (no Libya stations confirmed as of April 2026) |

Scheduler config: `data/config/scheduler_config.json`.

### 3.3 File-Based (manual download, public)

| Source | File | Used For |
|--------|------|----------|
| EM-DAT (CRED/UCLouvain) | data/emdat_libya.xlsx | Libya disaster history 2000-present (76 records, version 2026-04-17). Headline event: Storm Daniel 2023 (13,200 deaths, 1.6M affected, $6.2B damage) |

### 3.4 Manual Upload (no public API - restricted government data)

| Source | Folder | Used For |
|--------|--------|----------|
| NCDC Libya | data/uploads/ncdc/ | Disease surveillance CSV |
| COI Libya | data/uploads/coi/ | Coordination capacity CSV |
| IOM DTM fallback | data/uploads/iom/ | Used if HDX download fails |

### 3.5 Local Consolidated Uploads

`utils/local_overrides.py` builds an mtime-cached index of every
consolidated municipal upload. On subnational dashboards, uploaded
values substitute the national/proxy values for seven mappable
indicators: `tb_inc`, `u5mort`, `neo_mort`, `water`, `sanitation`,
`electricity`, `pm25`. The national LY view never applies overrides.

## 4. Risk Calculation Pipeline

Each per-pillar module in `utils/domains/` (hazard_exposure.py,
vulnerability.py, coping_capacity.py) consumes the normalised
connector data and returns a [0, 1] score for every sub-indicator.
`routes/dashboard.py::_run_pillars()` then composes the geometric
mean:

```python
inform_score = (hazard ** (1/3)) * (vulnerability ** (1/3)) * (coping ** (1/3))
```

`_compute_inform_score()` clamps the result to [0, 1] and is pinned by
`tests/test_inform.py`.

### 4.1 Connector Pipeline

`routes/dashboard.py::_load_connector_data()` loads who_hdx,
idmc_hdx, heigit, iom, worldbank, coi_libya, and ncdc_libya from disk
cache and normalises keys for the domain modules:

- WHO HDX beds per 10k divided by 10 -> per 1000
- IDMC HDX `total_displacement_stock` mapped to `idmc.total_idps`
- HeiGIT 22 ADM1 access values propagated to 148 municipalities as a
  documented regional proxy

### 4.2 Show-Your-Work Transparency

`_build_show_work()` in `routes/dashboard.py` builds per-sub-domain
Bootstrap popover HTML with raw indicator values, formula string, and
data source attribution. `_build_indicator_tiles()` builds a 3-level
hierarchy (pillar > sub-domain section > individual tile) with 34
individual indicator tiles across 12 sub-domain sections, each with
id, bilingual labels, raw value, unit, year, 0-1 score, 0-10 display,
risk band, badge colour, availability flag, proxy flag, source,
agency, formula, note, and pre-built popover_html.

### 4.3 Risk Banding

`utils.action_plan_content._inform_classify` maps the 0-1 score to
five bands using upper-exclusive cut points:

| Band | Score range |
|------|-------------|
| Very Low | 0.00 - 0.20 |
| Low | 0.20 - 0.40 |
| Medium | 0.40 - 0.60 |
| High | 0.60 - 0.80 |
| Very High | 0.80 - 1.00 |

Non-numeric or negative input returns "unavailable".

## 5. Sendai Framework Alignment

| Sendai Priority | INFORM mapping |
|-----------------|----------------|
| Priority 1 (Understanding risk) | Hazard and Exposure + Vulnerability pillars |
| Priority 2 (Governance) | Coping Capacity pillar |
| Priority 3 (Investment in DRR) | Coping Capacity / institutional_capacity |
| Priority 4 (Preparedness) | Coping Capacity / emergency_response |

## 6. Action Plan Output

`GET /action-plan/<jurisdiction_id>` renders a bilingual RTL
preparedness action plan, reusing `_run_pillars()` and calling
`utils/action_plan_content.get_action_domains()`. Output: 11
INFORM-component domains sorted by score; each domain has a 3-tier
timeline (0-3 months, 3-12 months, 1-3 years) in Arabic and English,
mapped to UN Cluster lead, Libyan government counterpart, and Sendai
priority. Template: `templates/action_plan_libya.html`.

## 7. Known Limitations

1. **HeiGIT regional proxy.** Hospital, primary healthcare, and
   education access values are produced at ADM1 (22 districts) and
   propagated to all 148 municipalities. Tiles flagged with the
   `proxy` source kind.
2. **WHO GHO Libya staleness.** Direct WHO GHO returns 2008-2018
   vintage data for Libya; the WHO Libya HDX dataset is now the
   primary source as of April 2026.
3. **Direct IDMC API blocked.** IDMC's direct API returns 403 from
   most cloud IPs; the OCHA HDX mirror is used instead.
4. **OpenAQ coverage.** No Libya stations confirmed as of April 2026.
   The connector remains registered for future activation.
5. **Armed-clashes domain omitted.** See section 2.4. Risk scores for
   municipalities with high political-violence exposure may
   under-state composite risk.
6. **42 municipalities flagged needs_verification.** Identifier
   stability and population estimates pending Libyan government
   confirmation.

## 8. Test Coverage

`tests/test_inform.py` validates the INFORM pipeline at three levels:

1. The cube-root composition that combines the three pillars
   (`_compute_inform_score`)
2. The 0-1 banding helper used by the action plan
   (`_inform_classify`)
3. One full national-level dashboard score end-to-end through
   `_run_pillars` with synthetic connector data

See `tests/README.md` for the full suite description.

## 9. References

1. INFORM Risk Index - JRC / IASC.
   https://drmkc.jrc.ec.europa.eu/inform-index
2. Sendai Framework for Disaster Risk Reduction 2015-2030 - UNDRR.
   https://www.undrr.org/implementing-sendai-framework
3. OCHA Humanitarian Data Exchange. https://data.humdata.org
4. WHO Global Health Observatory. https://www.who.int/data/gho
5. EM-DAT International Disaster Database. https://www.emdat.be
6. IDMC Internal Displacement Database.
   https://www.internal-displacement.org
7. HeiGIT Healthcare Accessibility Analysis.
8. World Bank Open Data. https://data.worldbank.org
9. OpenAQ Open Air Quality Data. https://openaq.org
