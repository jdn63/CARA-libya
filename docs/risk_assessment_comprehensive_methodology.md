# CARA Comprehensive Risk Assessment Methodology
## Version 2.6.0

## 1. Overview

This document provides detailed documentation of the CARA risk assessment methodology, including data sources, calculation formulas, domain weights, and known limitations. CARA serves 95 Wisconsin public health jurisdictions (101 total entries including multi-county secondary mappings), organized into 7 Healthcare Emergency Readiness Coalition (HERC) regions.

### 1.1 Scope

Jurisdictions include:
- 84 local health departments
- 11 federally-recognized tribal nations

### 1.2 PHRAT Formula

CARA uses a Public Health Risk Assessment Tool (PHRAT) quadratic mean:

```
Total Risk Score = (w1 * R1^2 + w2 * R2^2 + ... + wn * Rn^2) ^ (1/2)
```

Where p=2 (quadratic mean). This formula emphasizes higher-risk domains more than a simple weighted average, ensuring that a single high-risk domain is not diluted by several low-risk domains.

### 1.3 Dual-Discipline Support

CARA supports both Public Health (PH) and Emergency Management (EM) assessment perspectives. Both use the same underlying data sources but apply different vulnerability/resilience sub-weights:
- PH weights emphasize population health outcomes (elderly vulnerability, healthcare capacity, disease transmission)
- EM weights emphasize critical infrastructure impacts (power grid, transportation, mutual aid capacity)

EM assessments include an 8th primary domain (utilities, 10% weight) that is supplementary in PH mode.

## 2. Primary PHRAT Domain Weights

### 2.1 Public Health Weights (Default)

| Domain | Weight | Key Data Sources |
|--------|--------|-----------------|
| Natural Hazards | 28% | NOAA Storm Events, OpenFEMA (declarations, NFIP claims, HMA), FEMA NRI, Census ACS |
| Active Shooter | 18% | Gun Violence Archive 2023, NCES SSOCS 2019-2020, Census ACS demographics |
| Health Metrics | 17% | WI DHS respiratory surveillance (web scraper), Census ACS |
| Air Quality | 12% | EPA AirNow API, Census ACS, CDC SVI |
| Extreme Heat | 11% | NOAA climate normals, NWS heat forecasts, Census ACS (65+, poverty), CDC SVI |
| Dam Failure | 7% | WI DNR Dam Safety DB, USACE NID (fallback), OpenFEMA NFIP, CDC SVI |
| Vector-Borne Disease | 7% | WI DHS EPHT Lyme/WNV county CSVs, USDA NLCD, WI DNR deer density |

### 2.2 Emergency Management Weights

| Domain | Weight |
|--------|--------|
| Natural Hazards | 32% |
| Active Shooter | 13% |
| Extreme Heat | 13% |
| Health Metrics | 10% |
| Utilities | 10% |
| Air Quality | 8% |
| Dam Failure | 8% |
| Vector-Borne Disease | 6% |

### 2.3 Weight Rationale

Weights reflect relative frequency, severity, and breadth of public health impact for each hazard type in Wisconsin, informed by:
- FEMA National Risk Index annualized expected loss data for Wisconsin
- CDC PHEP (Public Health Emergency Preparedness) capability priorities
- Wisconsin DHS Hazard Vulnerability Assessment guidance
- Historical disaster declaration frequency (FEMA, 2000-2024)

Weights are configurable in `config/risk_weights.yaml`.

## 3. Data Sources and Integration

### 3.1 Scheduler-Cached Data Sources

All external data is pre-fetched by APScheduler jobs and stored in PostgreSQL cache. No external API calls occur during user assessments.

| Source | Endpoint/Method | Data Retrieved | Refresh |
|--------|-----------------|----------------|---------|
| NOAA NCEI Storm Events | Bulk CSV download | County-level storm event counts by type | Quarterly |
| OpenFEMA Disaster Declarations v2 | REST API (keyless) | WI disaster declarations by county and type | Weekly |
| OpenFEMA NFIP Claims v2 | REST API (keyless) | Flood insurance claims by county | Weekly |
| OpenFEMA HMA Projects v4 | REST API (keyless) | Hazard mitigation project data | Weekly |
| WI DNR Dam Safety Database | ArcGIS FeatureServer (keyless) | Wisconsin dam inventory, hazard classifications | Weekly |
| USACE NID | ArcGIS FeatureServer (keyless, fallback) | National dam inventory (used if DNR unavailable) | Weekly |
| CDC/ATSDR SVI 2022 | ArcGIS REST API (keyless) | County-level SVI percentile rankings (all 72 WI counties) | Annual |
| EPA AirNow | REST API (keyed) | AQI readings at monitoring stations | Daily |
| NOAA/NWS | REST API (keyless) | Heat forecasts, weather data | Daily |
| WI DHS Respiratory Surveillance | Web scraper (dhs.wisconsin.gov) | ILI, COVID-19, RSV activity levels | Weekly |
| WI DHS EPHT (Lyme/WNV) | CSV download (dhs.wisconsin.gov/epht) | County-level Lyme and WNV incidence rates per 100k | Weekly |
| US Census Bureau ACS | Local CSV files | Demographics, housing, mobile homes, elderly population | Annual (manual update) |

### 3.2 Static/Local Data Sources

| Source | File Path | Used For |
|--------|-----------|----------|
| FEMA NRI Census Tracts | `attached_assets/NRI_Table_CensusTracts_Wisconsin_FloodTornadoWinterOnly.csv` | Natural hazard baseline risk scores |
| Gun Violence Archive 2023 | `attached_assets/GunViolenceArchive 2023 mass shootings data.csv` | Active shooter historical incidents |
| NCES SSOCS 2019-2020 | `attached_assets/SSOCS 2019_2020 data.zip` | School safety indicators |
| NOAA Climate Normals 1991-2020 | Static baselines in code | Heat risk baseline calculations |
| USDA NLCD 2021 | Static data in code | Forest cover for VBD risk |
| WI DNR Deer Density | Static data in code | Tick habitat proxy for VBD risk |

### 3.3 Supplementary Domains (Proxy-Modeled, Not in PHRAT)

| Domain | Method | Limitation |
|--------|--------|------------|
| Cybersecurity | Modeled from county characteristics and SVI socioeconomic percentile | No direct cybersecurity breach data. SVI-based adjustment assumes lower-income communities have fewer IT security resources -- a proxy assumption without direct empirical validation. |
| Utilities | Composite of 4 sub-models (electrical outage 30%, utilities disruption 30%, supply chain 20%, fuel shortage 20%) | All use statistical models with proxy indicators, not real utility company data. |

## 4. Risk Calculation Details

### 4.1 Natural Hazards (EVR Framework)

Each sub-type (flood, tornado, winter storm, thunderstorm) uses an Exposure-Vulnerability-Resilience framework with health impact factor:

```
Residual_Risk = (Exposure * Vulnerability * Health_Impact_Factor) / Resilience
```

**Exposure** incorporates:
- NOAA Storm Events historical counts (event frequency by county)
- OpenFEMA disaster declarations (declaration frequency by disaster type)
- OpenFEMA NFIP claims (flood insurance claims as flood exposure proxy)
- FEMA NRI baseline scores (census tract level, aggregated to county)

**Vulnerability** uses CDC SVI theme percentiles with hazard-specific sub-weights:
- Flood: socioeconomic (0.20), housing/transportation (0.30), household composition (0.15), minority status (0.15), infrastructure density (0.15), mobile home factor (0.10), elderly factor (0.05), rural isolation (0.15) [PH weights shown; EM weights differ]
- Tornado, winter storm, thunderstorm: similar SVI-based sub-weight structures with hazard-appropriate adjustments

**Resilience** uses inverse SVI scores as proxies for community adaptive capacity.

**Health Impact Factor** scales risk by population health indicators (elderly percentage, poverty rate).

**Mobile home adjustment for tornado risk:**
```
mobile_home_factor = min(1.0, mobile_home_percentage * 5)
adjusted_tornado_risk = min(1.0, base_tornado_risk * (1 + mobile_home_factor))
```

The four sub-type scores are combined into a single natural hazards score.

### 4.2 Active Shooter Risk

Multi-component risk model using:
- Gun Violence Archive 2023 mass shooting data (static CSV)
- NCES SSOCS 2019-2020 school safety survey data (static)
- Census ACS demographics (population, density)
- CDC SVI percentiles for vulnerability adjustment

### 4.3 Health Metrics (Infectious Disease)

Based on WI DHS respiratory illness surveillance data obtained via web scraper:
- ILI (Influenza-like Illness) activity levels
- COVID-19 metrics
- RSV activity levels
- Vaccination rate proxies

### 4.4 Air Quality Risk

- EPA AirNow API provides daily AQI readings at monitoring stations
- Multi-point sampling: nearest monitoring stations to county centroid
- SVI adjustment: housing/transportation vulnerability (up to 30% increase) and socioeconomic status (up to 20% increase)
- Combined SVI multiplier capped at 1.5x

### 4.5 Extreme Heat Risk

Climate-adjusted heat vulnerability assessment using:
- NOAA climate normals (1991-2020 baselines)
- NWS heat forecast data (cached daily)
- Census ACS: population 65+, poverty rate
- CDC SVI percentiles
- Climate trend factors and urban heat island multipliers

### 4.6 Dam Failure Risk (EVR)

Standalone EVR domain:
- WI DNR Dam Safety Database (ArcGIS FeatureServer, primary)
- USACE NID (ArcGIS FeatureServer, keyless, fallback -- cloud IPs may receive 503 errors)
- Downstream population exposure based on dam height, hazard classification, and proximity
- OpenFEMA NFIP claims as flood exposure proxy
- SVI housing/transportation adjustment (up to 20% increase)

### 4.7 Vector-Borne Disease Risk

County-level Lyme disease and West Nile Virus assessment:
- WI DHS EPHT CSV downloads: confirmed + probable case counts, crude rates per 100,000 for all 72 WI counties
- Composite score: Lyme (65% weight) + WNV (35% weight), reflecting relative WI disease burden
- Environmental factors: forest cover (USDA NLCD 2021), deer density (WI DNR)
- Climate-adjusted range expansion projections (tick and mosquito habitat suitability under warming scenarios)
- SVI socioeconomic adjustment (up to 15% increase)

### 4.8 SVI Integration Across All Domains

CDC/ATSDR Social Vulnerability Index 2022 data covers all 72 Wisconsin counties. Real RPL_THEMES percentile values fetched via single bulk ArcGIS API call. Four themes used:
- Socioeconomic Status (RPL_THEME1)
- Household Characteristics and Disability (RPL_THEME2)
- Racial and Ethnic Minority Status and Language (RPL_THEME3)
- Housing Type and Transportation (RPL_THEME4)

SVI adjustment factors are configurable in `config/risk_weights.yaml` under `svi_adjustment_factors`.

### 4.9 PHRAT Final Score Assembly

```python
weights = {
    'natural_hazards': 0.28,
    'health_metrics': 0.17,
    'active_shooter': 0.18,
    'extreme_heat': 0.11,
    'air_quality': 0.12,
    'dam_failure': 0.07,
    'vector_borne_disease': 0.07,
}
p = 2.0
weighted_sum = sum(w * (risk ** p) for w, risk in zip(weights, risks))
total_risk_score = max(0.0, min(1.0, weighted_sum ** (1.0 / p)))
```

## 5. Temporal Framework (BSTA)

CARA uses a Baseline-Seasonal-Trend-Acute (BSTA) temporal framework. In the default Annual Strategic Planning mode:
- Baseline (60% weight): structural/foundational risks
- Seasonal (25% weight): cyclical preparedness needs
- Trend (15% weight): emerging long-term changes
- Acute (informational only): current events for context

A Dynamic Monitoring mode is available for emergency managers (40/20/20/20 split).

See `docs/temporal_framework_usage_strategy.md` for full details.

## 6. Current Limitations

### 6.1 Data Source Limitations

1. **Census Data Timing**: ACS 5-year estimates have statistical margins of error. Rural areas have higher uncertainty. Data updated annually from local CSV files.
2. **Static Datasets**: GVA (2023), NCES SSOCS (2019-2020), FEMA NRI, and climate normals are point-in-time snapshots that require manual updates.
3. **USACE NID Cloud Access**: The NID ArcGIS FeatureServer may return 503 errors from cloud-hosted IPs. WI DNR Dam Safety Database is the primary source and works from cloud.
4. **DHS Web Scraper**: Respiratory surveillance data depends on WI DHS page structure remaining stable. Format changes can break the scraper.
5. **VBD Data Lag**: WI DHS EPHT CSV data may have reporting delays of several weeks.

### 6.2 Methodological Limitations

1. **SVI as Proxy**: Using SVI percentiles as vulnerability/resilience proxies assumes socioeconomic factors correlate with disaster outcomes. The SVI-cybersecurity linkage is particularly indirect (no empirical validation).
2. **Supplementary Domains**: Cybersecurity and utilities domains use proxy indicators, not real incident data. Scores should be interpreted as relative estimates only.
3. **Predictive Analysis**: The predictive analysis module (`utils/predictive_analysis.py`) uses `random.uniform()` to generate confidence intervals and simulated historical trends. These are labeled as modeled estimates, not empirical forecasts.
4. **Health Impact Factor**: Based on available Census demographic proxies (elderly percentage, poverty rate), not direct epidemiological outcomes data.
5. **Linear SVI Adjustments**: Multiplier-based SVI adjustments assume linear relationships between vulnerability and risk, which may oversimplify complex interactions.

### 6.3 Geographic Resolution

- Most risk data is at county level. Census tract-level NRI data is aggregated to counties.
- Tribal jurisdictions may have unique risk patterns not fully captured by county-level data.
- Urban/rural differences within counties are only partially captured through SVI and population density.

## 7. Data Validation

- Automated outlier detection and capping (SVI adjustment multipliers capped)
- Cross-validation between NOAA Storm Events and OpenFEMA disaster declarations
- Scheduler-managed data freshness with configurable cache expiration
- Fallback data sources for critical APIs (WI DNR primary, USACE NID fallback for dams)
- Risk scores clamped to [0.0, 1.0] range

## 8. Version History

- v2.6.0 (March 2026): Thread-safety fixes, concurrency capacity increase, methodology documentation reconciled with implementation.
- v2.5.0 (February 2026): Real CDC/ATSDR SVI 2022 data for all 72 WI counties. Dam failure and VBD as separate PHRAT domains. EVR framework for natural hazards.
- v1.1.0 (April 2025): Coverage expanded to all 95 WI public health jurisdictions.
- v1.0.0 (March 2025): Initial release.

## 9. References

1. FEMA National Risk Index (NRI) - Wisconsin Census Tract Data
2. NOAA NCEI Storm Events Database
3. OpenFEMA APIs: Disaster Declarations Summaries v2, NFIP Redacted Claims v2, HMA Projects v4
4. US Census Bureau American Community Survey (ACS 5-Year Estimates)
5. CDC/ATSDR Social Vulnerability Index 2022
6. WI DNR Dam Safety Database (ArcGIS FeatureServer)
7. USACE National Inventory of Dams (NID ArcGIS FeatureServer)
8. EPA AirNow API
9. NOAA/NWS Heat Forecast API
10. Wisconsin DHS Respiratory Illness Surveillance
11. WI DHS Environmental Public Health Tracking (EPHT) - Lyme/WNV
12. Gun Violence Archive 2023
13. NCES School Safety and Climate Survey (SSOCS) 2019-2020
14. CDC PHEP Capability Standards
15. WICCI/NOAA Climate Projections
