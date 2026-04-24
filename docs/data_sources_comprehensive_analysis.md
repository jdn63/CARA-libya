# Libya CARA - Data Sources Comprehensive Analysis

## Overview

This document inventories every data source feeding the Libya CARA
INFORM Risk Index. All external data is fetched by APScheduler jobs
(registered in `core.py` when `CARA_PROFILE=libya`) and cached on
disk under `data/cache/`. No external API calls occur during user
assessments. The connector registry is `utils/connector_registry.py`.

Registered connectors:

```
hdx, heigit, idmc_hdx, who_hdx, iom, who_gho, worldbank,
openaq, ncdc_libya, coi_libya
```

## 1. Data Refresh Schedule

| Job | Cadence | Connectors |
|-----|---------|------------|
| refresh_libya_hdx | 168 h (weekly) | OCHA HDX (IOM DTM, OCHA 3W, UNHCR), HeiGIT, IDMC via HDX |
| refresh_libya_global | 720 h (monthly) | WHO Libya HDX (primary), WHO GHO (legacy fallback), World Bank, OpenAQ |

Scheduler config: `data/config/scheduler_config.json`.

## 2. Automated Sources - Weekly

### 2.1 OCHA Humanitarian Data Exchange (HDX)

- Endpoint: data.humdata.org/api/3/
- Authentication: none (public API)
- Datasets: IOM DTM displacement, OCHA 3W presence, UNHCR Libya
- Cache: `data/cache/hdx/`
- INFORM mapping: Vulnerability / displacement_vulnerability,
  Coping Capacity / institutional_capacity (3W presence)
- Connector: `utils/connectors/hdx.py`

### 2.2 HeiGIT Healthcare Accessibility

- Endpoint: hot.storage.heigit.org
- Authentication: none (public)
- Datasets: travel time to nearest hospital, primary healthcare,
  education facility - 22 ADM1 districts for Libya
- Cache: `data/cache/heigit/`
- INFORM mapping: Coping Capacity / healthcare_access_gap
- Notes: Values are produced at ADM1 (22 districts) and propagated to
  all 148 municipalities as a documented regional proxy. Affected
  tiles are flagged with the `proxy` source kind.

### 2.3 IDMC via OCHA HDX

- Endpoint: data.humdata.org/api/3/
- Authentication: none
- Datasets: annual conflict IDPs, IDP stock, disaster displacement
  events (Storm Daniel 2023 etc.)
- Cache: `data/cache/idmc/`
- INFORM mapping: Vulnerability / displacement_vulnerability
- Notes: Replaces direct IDMC API which returns 403 from most cloud
  IPs.

## 3. Automated Sources - Monthly

### 3.1 WHO Libya via OCHA HDX (Primary)

- Endpoint: data.humdata.org/api/3/
- Authentication: none
- Datasets: 7 CSV files, 17 health indicators (April 2026 cutover)
- Cache: `data/cache/who_hdx/`
- INFORM mapping: all three pillars (mortality, immunisation,
  workforce, infrastructure)
- Connector: `utils/connectors/who_hdx.py`

### 3.2 WHO Global Health Observatory (Legacy Fallback)

- Endpoint: ghoapi.azureedge.net/api/
- Authentication: none
- Status: legacy fallback only - returns stale Libya data
  (2008-2018 vintage)
- Connector: `utils/connectors/who_gho.py`

### 3.3 World Bank Open Data

- Endpoint: api.worldbank.org/v2/
- Authentication: none
- Datasets: development indicators (poverty headcount, GDP per
  capita, electricity access, water access, sanitation,
  unemployment)
- Cache: `data/cache/worldbank/`
- INFORM mapping: Vulnerability and Coping Capacity pillars
- Connector: `utils/connectors/worldbank.py`

### 3.4 OpenAQ

- Endpoint: api.openaq.org/v2/
- Authentication: none
- Status: no Libya stations confirmed as of April 2026; connector
  remains registered for future activation
- Cache: `data/cache/openaq/`
- INFORM mapping: Hazard / pm25 (air quality)
- Connector: `utils/connectors/openaq.py`

## 4. File-Based Sources (Public, Manual Download)

### 4.1 EM-DAT (CRED / UCLouvain)

- File: `data/emdat_libya.xlsx`
- Coverage: Libya disaster history 2000-present (76 records, version
  2026-04-17)
- Update process: re-download from emdat.be and replace the file
- INFORM mapping: Hazard and Exposure / hydrometeorological_hazard
- Headline event: Storm Daniel 2023 (13,200 deaths, 1.6M affected,
  $6.2B damage)

## 5. Manual Upload Sources (Restricted Government Data, no Public API)

### 5.1 NCDC Libya

- Folder: `data/uploads/ncdc/`
- Format: disease surveillance CSV
- INFORM mapping: Hazard / epidemiological_hazard
- Update process: government partner uploads through the admin
  interface; loaded by `utils/connectors/ncdc_libya.py`

### 5.2 COI Libya

- Folder: `data/uploads/coi/`
- Format: coordination capacity CSV
- INFORM mapping: Coping Capacity / institutional_capacity
- Connector: `utils/connectors/coi_libya.py`

### 5.3 IOM DTM Fallback

- Folder: `data/uploads/iom/`
- Used when the HDX download for IOM DTM fails

### 5.4 Local Consolidated Municipal Uploads

- Index: `utils/local_overrides.py` (mtime-cached)
- Override scope: seven mappable indicators on subnational
  dashboards: `tb_inc`, `u5mort`, `neo_mort`, `water`, `sanitation`,
  `electricity`, `pm25`
- The national LY view never applies overrides
- Tile badges: green "محلي / Local" for uploaded data, amber
  "وطني / National" when a country-level value is applied as a
  per-municipality proxy

## 6. Source Kinds and Tile Badges

`_stamp_source_kinds` (in `routes/dashboard.py`) tags every tile
with one of the following source kinds for transparency:

| Source kind | Meaning |
|-------------|---------|
| local | Value comes from a consolidated municipal upload |
| measured | Direct measurement at this jurisdiction |
| national | Country-level value applied as-is for the national view |
| national_proxy | Country-level value used at the municipal level |
| proxy | Regional or ADM1 value propagated to municipal level |

## 7. Coverage Gaps and Known Limitations

1. **HeiGIT regional proxy.** Hospital, primary healthcare, and
   education access values are produced at ADM1 (22 districts) and
   propagated to all 148 municipalities. Tiles flagged with the
   `proxy` source kind.
2. **WHO GHO Libya staleness.** Direct WHO GHO returns 2008-2018
   vintage data for Libya; the WHO Libya HDX dataset is the primary
   source as of April 2026.
3. **Direct IDMC API blocked.** IDMC's direct API returns 403 from
   most cloud IPs; the OCHA HDX mirror is used instead.
4. **OpenAQ coverage.** No Libya stations confirmed as of April
   2026.
5. **42 municipalities flagged needs_verification.** Identifier
   stability and population estimates pending Libyan government
   confirmation.
6. **Armed-clashes domain omitted.** Pending political sensitivity
   review (see `docs/risk_assessment_methodology.md`).

## 8. Data Lineage Summary

Every published score can be traced from the dashboard tile back to
the raw source via:

1. The tile popover (built by
   `routes/dashboard.py::_build_show_work()`) which lists the raw
   indicator value, the formula, the source agency, and the source
   year.
2. The cached file under `data/cache/<connector>/` for automated
   sources, or `data/uploads/<source>/` for manual uploads.
3. The connector module under `utils/connectors/` which documents
   the upstream endpoint and the parsing logic.

## 9. References

1. OCHA Humanitarian Data Exchange. https://data.humdata.org
2. WHO Global Health Observatory. https://www.who.int/data/gho
3. EM-DAT International Disaster Database. https://www.emdat.be
4. IDMC Internal Displacement Database.
   https://www.internal-displacement.org
5. HeiGIT Healthcare Accessibility Analysis.
6. World Bank Open Data. https://data.worldbank.org
7. OpenAQ Open Air Quality Data. https://openaq.org
