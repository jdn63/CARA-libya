# CARA Application - Comprehensive Data Sources Analysis

## Overview

This document provides a complete mapping of all data sources used in the CARA application across all risk domains. All external data is pre-fetched by APScheduler jobs and stored in PostgreSQL cache. No external API calls occur during user assessments.

## Data Source Categories

### Scheduler-Cached Data Sources (Active)

These data sources are fetched on a schedule and cached in the database.

1. **NOAA NCEI Storm Events Database**
- Used For: County-level storm event counts (flood, tornado, winter storm, thunderstorm)
- Method: Bulk CSV download
- Refresh: Quarterly
- Module: `utils/noaa_storm_events.py`

2. **OpenFEMA APIs (keyless)**
- Disaster Declarations Summaries v2: WI disaster declarations by county and disaster type
- NFIP Redacted Claims v2: Flood insurance claims by county (flood exposure proxy)
- Hazard Mitigation Assistance Projects v4: Mitigation project data
- Refresh: Weekly
- Module: `utils/openfema_data.py`

3. **WI DNR Dam Safety Database (keyless, primary)**
- Source: Wisconsin Repository of Dams ArcGIS FeatureServer
- Used For: Dam inventory, hazard classifications, dam heights, downstream population exposure
- Refresh: Weekly
- Module: `utils/dam_failure_risk.py`, `utils/nid_data_fetcher.py`

4. **USACE NID ArcGIS FeatureServer (keyless, fallback)**
- Source: National Inventory of Dams
- Used For: Fallback dam inventory when WI DNR is unavailable
- Limitation: Cloud-hosted IPs may receive 503 errors
- Refresh: Weekly

5. **CDC/ATSDR SVI 2022 ArcGIS REST API (keyless)**
- Used For: County-level Social Vulnerability Index percentile rankings for all 72 WI counties
- Data: Real RPL_THEMES values (socioeconomic, household composition, minority status, housing type)
- Method: Single bulk API call via `fetch_bulk_svi_data()`
- Stored: `data/svi/wisconsin_svi_data.json`
- Refresh: Annual
- Module: `utils/svi_data.py`

6. **EPA AirNow API (keyed)**
- Used For: Air Quality Index readings at monitoring stations near county centroids
- Data: AQI values, pollutant categories, multi-point sampling
- Refresh: Daily
- Module: Air quality assessment in `utils/data_processor.py`

7. **NOAA/NWS API (keyless)**
- Used For: Heat forecasts, weather data for extreme heat risk
- Refresh: Daily

8. **WI DHS Respiratory Illness Surveillance**
- Source: Web scraper targeting dhs.wisconsin.gov respiratory illness pages
- Data: ILI activity levels, COVID-19 metrics, RSV activity, vaccination rate indicators
- Refresh: Weekly
- Module: `utils/dhs_data.py`, `utils/web_scraper.py`

9. **WI DHS EPHT Lyme/WNV Surveillance**
- Source: CSV downloads from dhs.wisconsin.gov/epht
- Files: `lyme-county.csv`, `west-nile-data-county.csv`
- Data: County-level confirmed + probable case counts, crude incidence rates per 100,000 for all 72 WI counties
- Refresh: Weekly automated CSV download
- Module: `utils/vbd_data_fetcher.py`, `utils/vector_borne_disease_risk.py`

### Static/Local Data Sources

These are pre-loaded datasets stored locally in the application.

10. **FEMA National Risk Index (NRI)**
- File: `attached_assets/NRI_Table_CensusTracts_Wisconsin_FloodTornadoWinterOnly.csv`
- Used For: Census tract-level natural hazard baseline risk scores (flood, tornado, winter storm)
- Update: Manual (static file from FEMA NRI download)

11. **US Census Bureau ACS (Local CSV Files)**
- Files: `data/census/wisconsin_housing_data.csv`, `data/census/wisconsin_demographics.csv`
- Used For: Mobile home counts/percentages, population aged 65+, total population by county
- Update: Annual manual update with latest ACS release

12. **Gun Violence Archive 2023**
- File: `attached_assets/GunViolenceArchive 2023 mass shootings data.csv`
- Used For: Historical mass shooting incidents for active shooter risk assessment
- Update: Manual (static 2023 data)

13. **NCES School Safety Data (SSOCS)**
- File: `attached_assets/SSOCS 2019_2020 data.zip`
- Used For: School safety indicators in active shooter risk calculations
- Update: Manual (static 2019-2020 data)

14. **NOAA Climate Normals 1991-2020**
- Used For: Historical baseline for extreme heat risk calculations
- Update: Static baselines embedded in code

15. **USDA NLCD 2021 Forest Cover**
- Used For: Forest cover percentage as tick habitat proxy for VBD risk
- Update: Static data embedded in code

16. **WI DNR Deer Density**
- Used For: Deer population density as tick host proxy for VBD risk
- Update: Static data embedded in code

## Risk Domain Data Source Mapping

### Natural Hazards Risk (28% PHRAT weight)
- FEMA NRI census tract data (static CSV)
- NOAA NCEI Storm Events (quarterly scheduler cache)
- OpenFEMA Disaster Declarations, NFIP Claims, HMA Projects (weekly scheduler cache)
- Census ACS demographics (local CSV)
- CDC SVI percentiles (annual scheduler cache)

### Active Shooter Risk (18% PHRAT weight)
- Gun Violence Archive 2023 (static CSV)
- NCES SSOCS 2019-2020 (static)
- Census ACS demographics (local CSV)
- CDC SVI percentiles (annual scheduler cache)

### Health Metrics / Infectious Disease Risk (17% PHRAT weight)
- WI DHS respiratory illness surveillance (weekly web scraper cache)
- Census ACS demographics (local CSV)

### Air Quality Risk (12% PHRAT weight)
- EPA AirNow API (daily scheduler cache)
- Census ACS demographics (local CSV)
- CDC SVI housing/socioeconomic themes (annual scheduler cache)

### Extreme Heat Risk (11% PHRAT weight)
- NOAA climate normals 1991-2020 (static)
- NWS heat forecasts (daily scheduler cache)
- Census ACS: population 65+, poverty rate (local CSV)
- CDC SVI percentiles (annual scheduler cache)

### Dam Failure Risk (7% PHRAT weight)
- WI DNR Dam Safety Database (weekly scheduler cache, primary)
- USACE NID (weekly scheduler cache, fallback)
- OpenFEMA NFIP Claims (weekly scheduler cache)
- CDC SVI housing/transportation theme (annual scheduler cache)
- Census ACS demographics (local CSV)

### Vector-Borne Disease Risk (7% PHRAT weight)
- WI DHS EPHT Lyme county-level incidence rates (weekly scheduler cache)
- WI DHS EPHT WNV county-level incidence rates (weekly scheduler cache)
- USDA NLCD 2021 forest cover (static)
- WI DNR deer density (static)
- Climate-adjusted range expansion projections (static)
- CDC SVI socioeconomic theme (annual scheduler cache)

### Cybersecurity Risk (Supplementary, not in PHRAT)
- Modeled from county characteristics and CDC SVI socioeconomic percentile
- No direct cybersecurity incident data source
- Proxy assumption: lower SVI socioeconomic scores correlate with fewer IT security resources

### Utilities Risk (Supplementary, not in PHRAT for PH; 10% in EM)
- Electrical outage risk: statistical model with proxy indicators
- Utilities disruption risk: statistical model with proxy indicators
- Supply chain disruption risk: statistical model with proxy indicators
- Fuel shortage risk: statistical model with proxy indicators
- No real utility company data sources

## Data Refresh Schedule

| Data Source | Refresh Interval | Cache Location | Status |
|-------------|------------------|----------------|--------|
| NOAA Storm Events | Quarterly | PostgreSQL cache | Active |
| OpenFEMA (3 endpoints) | Weekly | PostgreSQL cache | Active |
| WI DNR Dam Safety | Weekly | PostgreSQL cache | Active |
| USACE NID (fallback) | Weekly | PostgreSQL cache | Active (may 503 from cloud) |
| CDC SVI 2022 | Annual | JSON file + cache | Active |
| EPA AirNow | Daily | PostgreSQL cache | Active |
| NOAA/NWS Heat | Daily | PostgreSQL cache | Active |
| WI DHS Respiratory | Weekly | PostgreSQL cache | Active |
| WI DHS EPHT (Lyme/WNV) | Weekly | PostgreSQL cache | Active |
| Census ACS | Manual/Annual | Local CSV files | Active |
| FEMA NRI | Manual | Local CSV file | Active |
| GVA 2023 | Manual | Local CSV file | Static |
| NCES SSOCS | Manual | Local ZIP file | Static (2019-2020) |

## Known Data Gaps

### Not Currently Addressable
1. **Real cybersecurity incident data**: No free, county-level cybersecurity breach API exists. HHS Breach Portal, FBI IC3, and CISA KEV do not provide county-level data suitable for jurisdictional risk scoring.
2. **Real utility outage data**: Requires data-sharing agreements with utility companies. No public API available.
3. **Real-time hospital capacity**: Would require WHA API access or similar. Not currently integrated.

### Could Be Improved
1. **GVA data freshness**: Currently using 2023 data. Could be updated annually with new GVA download.
2. **NCES SSOCS data**: 2019-2020 vintage. Next SSOCS release would improve school safety indicators.
3. **Climate projections**: Currently using static NOAA climate normals and basic trend factors. Could integrate CMIP6 downscaled projections for Wisconsin.

## Transparency Notes

**For Public Health Officials**: CARA uses a mix of scheduler-cached API data, static datasets, and proxy-modeled estimates. The seven primary PHRAT domains use real data from authoritative sources. The two supplementary domains (cybersecurity, utilities) use statistical models with proxy indicators and should be interpreted as relative planning estimates, not empirical risk measurements.

**For Technical Users**: Data source configurations are in `data/config/scheduler_config.json`. Risk domain weights are in `config/risk_weights.yaml` and hard-coded in `utils/data_processor.py`. SVI adjustment factors are configurable in the weights YAML. Individual risk modules contain detailed documentation of their data processing methods.

---

**Last Updated**: March 2026
**Version**: 2.6.0
