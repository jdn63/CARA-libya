# CARA Data Dictionary

## Overview

This document provides a comprehensive reference for all data variables, risk metrics, and calculated fields used in the CARA (Comprehensive Automated Risk Assessment) platform. CARA serves 95 Wisconsin public health jurisdictions with multi-domain risk assessments.

## Table of Contents

- [Risk Assessment Variables](#risk-assessment-variables)
- [Geographic Variables](#geographic-variables)
- [Temporal Variables](#temporal-variables)
- [Data Sources](#data-sources)
- [Calculated Fields](#calculated-fields)
- [API Response Formats](#api-response-formats)

## Risk Assessment Variables

### Overall Risk Score

| Variable | Type | Range | Unit | Description |
|----------|------|-------|------|-------------|
| `overall_risk` | Float | 0.0 - 1.0 | Normalized | Combined risk score across all domains |
| `risk_level` | String | - | Categorical | LOW, MODERATE, HIGH, VERY_HIGH |
| `confidence` | Float | 0.0 - 1.0 | Normalized | Statistical confidence in assessment |

### Natural Hazards

#### Winter Storm Risk
| Variable | Type | Range | Unit | Description |
|----------|------|-------|------|-------------|
| `winter_storm_exposure` | Float | 0.0 - 1.0 | Normalized | Historical frequency and severity of winter storms |
| `winter_storm_vulnerability` | Float | 0.0 - 1.0 | Normalized | Infrastructure and population vulnerability |
| `winter_storm_resilience` | Float | 0.0 - 1.0 | Normalized | Emergency response and recovery capacity |
| `snowfall_inches_annual` | Float | 0 - 200 | Inches | Average annual snowfall |
| `ice_storm_frequency` | Float | 0 - 10 | Events/year | Historical ice storm frequency |

#### Flood Risk
| Variable | Type | Range | Unit | Description |
|----------|------|-------|------|-------------|
| `flood_exposure` | Float | 0.0 - 1.0 | Normalized | FEMA flood zone and historical flooding |
| `flood_vulnerability` | Float | 0.0 - 1.0 | Normalized | Population and infrastructure in flood zones |
| `flood_resilience` | Float | 0.0 - 1.0 | Normalized | Flood mitigation and response capacity |
| `fema_flood_zone` | String | - | Categorical | A, AE, X, etc. (FEMA flood zone designations) |
| `dam_count` | Integer | 0 - 50 | Count | Number of dams in jurisdiction |

#### Tornado Risk
| Variable | Type | Range | Unit | Description |
|----------|------|-------|------|-------------|
| `tornado_exposure` | Float | 0.0 - 1.0 | Normalized | Historical tornado frequency and strength |
| `tornado_vulnerability` | Float | 0.0 - 1.0 | Normalized | Mobile home density and shelter availability |
| `tornado_resilience` | Float | 0.0 - 1.0 | Normalized | Warning systems and shelter capacity |
| `tornado_frequency_annual` | Float | 0 - 5 | Events/year | Average annual tornado frequency |
| `f3_plus_historical` | Integer | 0 - 20 | Count | Historical F3+ tornadoes (1950-present) |

### Extreme Heat Risk (Climate-Adjusted)

| Variable | Type | Range | Unit | Description |
|----------|------|-------|------|-------------|
| `heat_exposure` | Float | 0.0 - 0.95 | Normalized | Climate-adjusted heat exposure |
| `heat_vulnerability` | Float | 0.0 - 1.0 | Normalized | Population vulnerability to extreme heat |
| `heat_resilience` | Float | 0.0 - 1.0 | Normalized | Cooling resources and adaptation capacity |
| `wet_bulb_risk` | Float | 0.0 - 1.0 | Normalized | Dangerous humidity-heat combinations |
| `climate_trend_factor` | Float | 1.0 - 1.5 | Multiplier | Climate change amplification factor |
| `heat_island_factor` | Float | 1.0 - 1.4 | Multiplier | Urban heat island amplification |
| `cooling_degree_days` | Integer | 0 - 2000 | Degree Days | Annual cooling energy demand |
| `heat_days_90f_projected` | Integer | 0 - 60 | Days/year | Projected 90°F+ days by 2050 |

### Air Quality Risk (Strategic)

| Variable | Type | Range | Unit | Description |
|----------|------|-------|------|-------------|
| `air_quality_exposure` | Float | 0.0 - 1.0 | Normalized | Historical AQI patterns and projections |
| `air_quality_vulnerability` | Float | 0.0 - 1.0 | Normalized | Sensitive population density |
| `air_quality_resilience` | Float | 0.0 - 1.0 | Normalized | Healthcare capacity and air quality programs |
| `aqi_baseline_5year` | Float | 0 - 200 | AQI | 5-year average Air Quality Index |
| `ozone_action_days_annual` | Integer | 0 - 30 | Days/year | Annual ozone action days |
| `pm25_exposure_projected` | Float | 0.0 - 1.0 | Normalized | Projected PM2.5 exposure increase |
| `wildfire_smoke_risk` | Float | 0.0 - 1.0 | Normalized | Projected wildfire smoke episodes |

### Infectious Disease Risk

| Variable | Type | Range | Unit | Description |
|----------|------|-------|------|-------------|
| `disease_exposure` | Float | 0.0 - 1.0 | Normalized | Disease transmission potential |
| `disease_vulnerability` | Float | 0.0 - 1.0 | Normalized | Population susceptibility |
| `disease_resilience` | Float | 0.0 - 1.0 | Normalized | Healthcare and public health capacity |
| `population_density` | Float | 0 - 5000 | People/sq mi | Population density |
| `vaccination_rate` | Float | 0.0 - 1.0 | Proportion | Age-appropriate vaccination coverage |
| `healthcare_capacity` | Float | 0.0 - 1.0 | Normalized | Hospital beds per capita |
| `syndromic_surveillance` | Float | 0.0 - 1.0 | Normalized | Disease surveillance capability |

### Active Shooter Risk

| Variable | Type | Range | Unit | Description |
|----------|------|-------|------|-------------|
| `shooter_exposure` | Float | 0.0 - 1.0 | Normalized | Venue density and historical patterns |
| `shooter_vulnerability` | Float | 0.0 - 1.0 | Normalized | Population concentration in vulnerable venues |
| `shooter_resilience` | Float | 0.0 - 1.0 | Normalized | Law enforcement and emergency response |
| `school_count` | Integer | 0 - 200 | Count | Number of educational institutions |
| `venue_density_score` | Float | 0.0 - 1.0 | Normalized | Soft target venue concentration |
| `law_enforcement_ratio` | Float | 0 - 10 | Officers/1000 | Law enforcement officers per 1000 residents |

## Geographic Variables

### Jurisdiction Information

| Variable | Type | Range | Unit | Description |
|----------|------|-------|------|-------------|
| `jurisdiction_id` | String | - | ID | Unique jurisdiction identifier |
| `jurisdiction_name` | String | - | Text | Official jurisdiction name |
| `jurisdiction_type` | String | - | Categorical | COUNTY, TRIBAL, MUNICIPAL |
| `fips_code` | String | 5 digits | Code | Federal Information Processing Standards code |
| `herc_region` | Integer | 1 - 7 | Region | Health Emergency Readiness Coalition region |
| `wem_region` | String | - | Code | Wisconsin Emergency Management region |

### Geographic Characteristics

| Variable | Type | Range | Unit | Description |
|----------|------|-------|------|-------------|
| `area_square_miles` | Float | 0 - 2000 | Square miles | Total jurisdiction area |
| `population_total` | Integer | 0 - 1000000 | People | Total population (latest census) |
| `population_density` | Float | 0 - 5000 | People/sq mi | Population per square mile |
| `urban_percentage` | Float | 0.0 - 1.0 | Proportion | Urban vs rural population split |
| `coastline_miles` | Float | 0 - 200 | Miles | Great Lakes coastline length |
| `elevation_mean` | Integer | 500 - 1500 | Feet | Mean elevation above sea level |

### Boundary Data

| Variable | Type | Range | Unit | Description |
|----------|------|-------|------|-------------|
| `geometry` | GeoJSON | - | Geographic | Jurisdiction boundary polygon |
| `centroid_lat` | Float | 42.5 - 47.3 | Degrees | Geographic center latitude |
| `centroid_lon` | Float | -92.9 - -86.2 | Degrees | Geographic center longitude |
| `bounding_box` | Array | - | Coordinates | [min_lon, min_lat, max_lon, max_lat] |

## Temporal Variables

### Assessment Timing

| Variable | Type | Range | Unit | Description |
|----------|------|-------|------|-------------|
| `assessment_date` | DateTime | - | ISO 8601 | Timestamp of risk assessment |
| `data_freshness` | Integer | 0 - 365 | Days | Days since data last updated |
| `temporal_framework` | String | - | Categorical | STRATEGIC, OPERATIONAL, TACTICAL |
| `planning_horizon` | String | - | Categorical | ANNUAL, SEASONAL, MONTHLY |

### Strategic Planning Weights

| Variable | Type | Range | Unit | Description |
|----------|------|-------|------|-------------|
| `baseline_weight` | Float | 0.0 - 1.0 | Proportion | Weight given to baseline historical data |
| `seasonal_weight` | Float | 0.0 - 1.0 | Proportion | Weight given to seasonal patterns |
| `trend_weight` | Float | 0.0 - 1.0 | Proportion | Weight given to trend analysis |
| `acute_weight` | Float | 0.0 - 1.0 | Proportion | Weight given to acute current conditions |

## Data Sources

### External APIs

| Source | Update Frequency | Variables | Coverage |
|--------|-----------------|-----------|----------|
| US Census Bureau ACS | Annual (local CSV) | Demographics, housing, mobile homes | All jurisdictions |
| NOAA NCEI Storm Events | Quarterly (scheduler cache) | Storm event counts by type | County level |
| NOAA/NWS | Daily (scheduler cache) | Heat forecasts, weather data | Statewide |
| EPA AirNow | Daily (scheduler cache) | Air quality indices | Monitoring stations |
| OpenFEMA (3 endpoints) | Weekly (scheduler cache) | Declarations, NFIP claims, HMA | Statewide |
| WI DNR Dam Safety | Weekly (scheduler cache) | Dam inventory, hazard classifications | Statewide |
| CDC/ATSDR SVI 2022 | Annual (scheduler cache) | Social vulnerability percentiles | All 72 WI counties |
| WI DHS Respiratory | Weekly (web scraper cache) | ILI, COVID, RSV activity | Statewide |
| WI DHS EPHT (VBD) | Weekly (CSV download cache) | Lyme/WNV incidence rates | All 72 WI counties |
| FEMA NRI | Static file | Census tract hazard scores | Statewide |

### Internal Data Processing

| Dataset | Update Frequency | Source | Variables |
|---------|-----------------|--------|-----------|
| Jurisdiction boundaries | As needed | Wisconsin DHS | Geographic boundaries |
| Tribal territories | As needed | Bureau of Indian Affairs | Tribal jurisdiction data |
| HERC regions | As needed | Wisconsin DHS | Health region assignments |
| Risk weights | Configurable | `config/risk_weights.yaml` | Domain weights, SVI adjustment factors |

## Calculated Fields

### Risk Score Formulas

```
PHRAT Quadratic Mean:
Total Risk = sqrt(w1 * R1^2 + w2 * R2^2 + ... + w7 * R7^2)

Where:
- R1..R7: Individual domain risk scores (0.0-1.0) from 7 primary domains
- w1..w7: Domain weights from config/risk_weights.yaml (sum to 1.0)
- p=2 (quadratic mean emphasizes higher-risk domains)

Per-Domain (EVR Framework for natural hazards, dam failure):
Residual Risk = (Exposure * Vulnerability * Health_Impact_Factor) / Resilience
```

### Confidence Calculations

```
Confidence = min(Data_Quality, Model_Accuracy, Temporal_Relevance)

Where:
- Data_Quality: Completeness and accuracy of input data (0.0-1.0)
- Model_Accuracy: Validated performance of risk algorithms (0.0-1.0)  
- Temporal_Relevance: Recency and relevance of data (0.0-1.0)
```

### Climate Adjustment Factors

```
Climate_Adjusted_Risk = Base_Risk × Climate_Trend_Factor × Heat_Island_Factor

Where:
- Base_Risk: Historical baseline risk level
- Climate_Trend_Factor: IPCC regional warming projections (1.0-1.5)
- Heat_Island_Factor: Urban heat amplification (1.0-1.4)
```

## API Response Formats

### Risk Assessment Response

```json
{
  "jurisdiction_id": "55025",
  "jurisdiction_name": "Dane County",
  "assessment_date": "2024-01-15T14:30:00Z",
  "overall_risk": 0.68,
  "risk_level": "MODERATE",
  "confidence": 0.82,
  "domains": {
    "natural_hazards": {
      "winter_storm": {
        "exposure": 0.72,
        "vulnerability": 0.58,
        "resilience": 0.75,
        "overall_risk": 0.56
      }
    },
    "climate_risks": {
      "extreme_heat": {
        "exposure": 0.65,
        "vulnerability": 0.52,
        "resilience": 0.78,
        "wet_bulb_risk": 0.48,
        "climate_trend_factor": 1.35,
        "overall_risk": 0.61
      }
    }
  },
  "metadata": {
    "methodology": "CARA v2.1",
    "temporal_framework": "STRATEGIC",
    "data_sources": ["US_CENSUS", "NOAA", "WI_DHS"],
    "last_updated": "2024-01-15T06:00:00Z"
  }
}
```

## Data Quality Standards

### Completeness Requirements

- **Tier 1** (Critical): 100% complete (jurisdiction boundaries, population)
- **Tier 2** (Important): 90% complete (most risk variables)
- **Tier 3** (Supplementary): 70% complete (enhanced risk factors)

### Accuracy Standards

- **Geographic Data**: ±100 meter accuracy for boundaries
- **Population Data**: ±5% accuracy (latest census estimates)
- **Risk Scores**: ±0.05 normalized scale accuracy
- **Temporal Data**: ±1 hour for current conditions

### Update Frequencies

- **Real-time**: Weather conditions, air quality (hourly)
- **Daily**: Disease surveillance, emergency declarations
- **Weekly**: Seasonal risk adjustments
- **Monthly**: Economic and social indicators
- **Annually**: Demographics, infrastructure, baseline risks

---

*This data dictionary is maintained as part of the CARA platform documentation and reflects the current data model.*

**Last Updated**: March 2026
**Version**: 2.6.0
**Coverage**: 95 Wisconsin Public Health Jurisdictions