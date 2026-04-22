# Risk Assessment Methodology

## Version 2.6.0
Last Updated: March 2026

## Overview

CARA uses a Public Health Risk Assessment Tool (PHRAT) quadratic mean formula to combine seven primary risk domains into a single composite score. Two supplementary domains (cybersecurity and utilities) are modeled from proxy indicators and displayed separately for planning context but are not included in the PHRAT score.

The formula uses p=2 (quadratic mean) to appropriately emphasize higher-risk domains rather than averaging them away:

```
Total Risk Score = sqrt(w1 * Risk1^2 + w2 * Risk2^2 + ... + w7 * Risk7^2)
```

## Primary PHRAT Domain Weights (Public Health Discipline)

| Domain | Weight | Rationale |
|--------|--------|-----------|
| Natural Hazards | 28% | Largest annualized expected losses in WI per FEMA NRI data. Covers 4 sub-types (flood, tornado, winter storm, thunderstorm). |
| Active Shooter | 18% | CDC/ASPR identifies active shooter as high-consequence threat requiring dedicated PHEP planning. |
| Health Metrics | 17% | Infectious disease is a core PHEP capability. |
| Air Quality | 12% | EPA data shows increasing wildfire smoke episodes affecting WI. |
| Extreme Heat | 11% | NOAA data: heat is leading weather-related cause of death nationally; WI's northern latitude tempers exposure. |
| Dam Failure | 7% | Standalone EVR domain using NID/WI DNR dam inventory and FEMA flood data. |
| Vector-Borne Disease | 7% | Lyme disease (WI top-5 nationally) and West Nile Virus using WI DHS surveillance data. |

Weights are defined in `config/risk_weights.yaml` and hard-coded in `utils/data_processor.py`. They sum to 1.0.

## Supplementary Domains (Not in PHRAT Score)

| Domain | Status | Description |
|--------|--------|-------------|
| Cybersecurity | Modeled from proxy indicators | County characteristics + SVI socioeconomic percentile. No direct empirical data source. |
| Utilities | Modeled from proxy indicators | Electrical outage, utilities disruption, supply chain, and fuel shortage sub-models. |

## Data Sources

### Active Data Sources (Scheduler-Cached)

| Data Type | Source | Refresh Frequency | Data Scale |
|-----------|--------|-------------------|------------|
| Storm Events | NOAA NCEI Storm Events Database | Quarterly bulk CSV download | County level |
| Disaster Declarations | OpenFEMA Disaster Declarations Summaries v2 | Weekly | County level |
| NFIP Claims | OpenFEMA NFIP Redacted Claims v2 | Weekly | County level |
| Hazard Mitigation | OpenFEMA HMA Projects v4 | Weekly | County level |
| Dam Inventory | WI DNR Dam Safety ArcGIS FeatureServer (primary) / USACE NID (fallback) | Weekly | County level |
| Social Vulnerability | CDC/ATSDR SVI 2022 ArcGIS REST API | Annual | County level (all 72 WI counties) |
| Air Quality | EPA AirNow API | Daily | Monitoring stations |
| Heat Forecasts | NOAA/NWS API | Daily | County level |
| Disease Surveillance | WI DHS respiratory illness pages (web scraper) | Weekly | Statewide |
| Vector-Borne Disease | WI DHS EPHT CSV downloads (Lyme, WNV county-level incidence) | Weekly | County level (all 72 counties) |

### Static/Local Data Sources

| Data Type | Source | File |
|-----------|--------|------|
| Natural Hazard Baselines | FEMA NRI Census Tract data | `attached_assets/NRI_Table_CensusTracts_Wisconsin_FloodTornadoWinterOnly.csv` |
| Gun Violence Incidents | Gun Violence Archive 2023 | `attached_assets/GunViolenceArchive 2023 mass shootings data.csv` |
| School Safety | NCES SSOCS 2019-2020 | `attached_assets/SSOCS 2019_2020 data.zip` |
| Demographics/Housing | US Census Bureau ACS | `data/census/wisconsin_housing_data.csv`, `data/census/wisconsin_demographics.csv` |
| Climate Normals | NOAA 1991-2020 | Static baselines for heat risk |

## Natural Hazards Risk Methodology

Uses an Exposure-Vulnerability-Resilience (EVR) framework with a health impact factor for each sub-type (flood, tornado, winter storm, thunderstorm).

The residual risk formula:
```
Residual Risk = (Exposure * Vulnerability * Health_Impact_Factor) / Resilience
```

Where:
- Exposure incorporates NOAA Storm Events historical counts and OpenFEMA disaster declarations/NFIP claims
- Vulnerability uses SVI theme percentiles with hazard-specific sub-weights from `config/risk_weights.yaml`
- Resilience uses inverse SVI socioeconomic and housing scores as proxies
- Health Impact Factor scales risk by population health indicators (elderly percentage, poverty rate)

### Mobile Home Impact on Tornado Risk
```
mobile_home_percentage = census_mobile_homes / total_housing_units
mobile_home_factor = min(1.0, mobile_home_percentage * 5)
adjusted_tornado_risk = min(1.0, base_tornado_risk * (1 + mobile_home_factor))
```

## Dam Failure Risk Methodology

Standalone EVR domain using:
- WI DNR Dam Safety Database (primary, ArcGIS FeatureServer) or USACE NID (fallback)
- Downstream population exposure based on dam height, hazard classification, and proximity
- OpenFEMA NFIP flood claims as flood exposure proxy
- SVI housing/transportation theme as vulnerability adjustment

## Vector-Borne Disease Risk Methodology

Standalone domain covering Lyme disease and West Nile Virus:
- County-level incidence rates per 100k from WI DHS EPHT CSV downloads (confirmed + probable cases)
- Environmental factors: forest cover (USDA NLCD 2021), deer density (WI DNR)
- Climate-adjusted range expansion projections
- Composite: Lyme (65% weight) + WNV (35% weight) based on relative WI burden

## SVI Integration

CDC/ATSDR Social Vulnerability Index 2022 data for all 72 Wisconsin counties. Four SVI theme percentile rankings (socioeconomic, household composition/disability, minority status/language, housing type/transportation) are used as vulnerability and resilience proxies across all risk domains. Adjustment factors are configurable in `config/risk_weights.yaml`.

## Risk Level Categories

| Level | Score Range |
|-------|------------|
| Low | Below 0.3 |
| Moderate | 0.3 to 0.5 |
| High | 0.5 to 0.7 |
| Very High | Above 0.7 |

## Predictive Analysis Limitations

The predictive analysis module (`utils/predictive_analysis.py`) uses `random.uniform()` to generate confidence intervals and simulated historical trend data. These projections are labeled as modeled estimates, not empirical forecasts. They should not be cited as data-driven predictions.

## References

1. FEMA National Risk Index (NRI) - Wisconsin Census Tract Data
2. NOAA NCEI Storm Events Database (bulk CSV)
3. OpenFEMA APIs: Disaster Declarations v2, NFIP Claims v2, HMA Projects v4
4. US Census Bureau American Community Survey (ACS 5-Year Estimates)
5. CDC/ATSDR Social Vulnerability Index 2022
6. WI DNR Dam Safety Database (ArcGIS FeatureServer)
7. USACE National Inventory of Dams (NID, ArcGIS FeatureServer)
8. EPA AirNow API
9. NOAA/NWS Heat Forecast API
10. Wisconsin DHS Respiratory Illness Surveillance (web scraper)
11. WI DHS Environmental Public Health Tracking (EPHT) - Lyme/WNV county CSVs
12. Gun Violence Archive
13. NCES School Safety and Climate Survey (SSOCS) 2019-2020
