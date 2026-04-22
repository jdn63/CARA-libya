# CARA Template Configuration Reference

## Files overview

```
config/
  profiles/
    us_state.yaml          Profile for US states, territories, Tribal nations
    international.yaml     Profile for countries and non-US jurisdictions
  jurisdiction.yaml        Your deployment-specific configuration (from .example)
  risk_weights.yaml        Domain weights and scoring thresholds
```

## jurisdiction.yaml

### jurisdiction block

| Key | Type | Required | Description |
|-----|------|----------|-------------|
| name | string | yes | Full jurisdiction name |
| short_name | string | yes | Abbreviation (2-6 chars) |
| profile | string | yes | 'us_state' or 'international' |
| country_code | string | yes | ISO 3166-1 alpha-2 |
| language | string | no | Default: 'en' |
| timezone | string | no | e.g. 'Africa/Nairobi' |
| population | integer | no | Total population |
| area_sq_km | float | no | Area in square kilometers |

### jurisdiction.geographic block

| Key | Type | Description |
|-----|------|-------------|
| gadm_country | string | ISO2 country code for GADM download |
| gadm_level | integer | Administrative level (1=state/province, 2=district/county) |
| bounding_box | object | north/south/east/west decimal degrees |
| center | object | lat/lon decimal degrees |

### jurisdiction.administrative_hierarchy block

Labels for each administrative level. Example for Kenya:
```yaml
administrative_hierarchy:
  level_0: "Country"
  level_1: "County"
  level_2: "Sub-county"
  level_3: "Ward"
  primary_assessment_level: 1
```

### jurisdiction.subdivisions block

List of administrative units for assessment. Each entry:

| Key | Type | Description |
|-----|------|-------------|
| id | string | Unique identifier (use GADM GID if available) |
| name | string | Display name |
| level | integer | Administrative level |
| gadm_gid | string | GADM GID for boundary lookup |
| population | integer | Population (used for displacement rate calculations) |
| area_sq_km | float | Area |
| capital | string | Capital city or main town |
| notes | string | Optional deployment notes |

### jurisdiction.regional_groups block

Groups of subdivisions for regional-level aggregation:

```yaml
regional_groups:
  - id: "region_north"
    name: "Northern Region"
    label: "Region"
    subdivision_ids:
      - "district_01"
      - "district_02"
```

### jurisdiction.acled_config block

```yaml
acled_config:
  country: "Kenya"
  region_id: null         # Optional ACLED region filter
  admin1_filter: null     # Optional state/province filter
```

### jurisdiction.idmc_config block

```yaml
idmc_config:
  iso3: "KEN"             # ISO 3166-1 alpha-3 code
  country_name: "Kenya"
```

### jurisdiction.overrides block

```yaml
overrides:
  weights:
    conflict_displacement: 0.25
    natural_hazards: 0.20
    health_metrics: 0.17
    mass_casualty: 0.10
    air_quality: 0.10
    extreme_heat: 0.10
    vector_borne_disease: 0.08
  domain_thresholds: {}
  custom_notes: "Override reason documented here"
```

## config/profiles/international.yaml

Key configurable sections:

### domains block

```yaml
domains:
  enabled:
    - natural_hazards
    - health_metrics
    - air_quality
    - extreme_heat
    - vector_borne_disease
    - mass_casualty
    - conflict_displacement
  disabled:
    - dam_failure
```

Add domains to `disabled` to exclude them. The risk engine rebalances weights.

### domain_config.conflict_displacement block

```yaml
domain_config:
  conflict_displacement:
    acled_event_types:
      - battles
      - explosions_remote_violence
      - violence_against_civilians
      - protests
      - riots
    displacement_metrics:
      - internally_displaced
      - refugees_generated
      - returnees
    lookback_years: 3
```

## Environment variables

| Variable | Required | Description |
|----------|----------|-------------|
| SESSION_SECRET | yes | Flask session secret (random string) |
| DATABASE_URL | yes | PostgreSQL connection string |
| CARA_PROFILE | yes | 'international' or 'us_state' |
| ENABLE_SCRAPERS | no | Set to 0 to disable scheduler (default: 1) |
| ACLED_API_KEY | for conflict | ACLED API key |
| ACLED_EMAIL | for conflict | ACLED registered email |
| EMDAT_API_KEY | for disasters | EM-DAT API key |
| OPENAQ_API_KEY | no | OpenAQ key (improves rate limits) |
| NOAA_CDO_TOKEN | no | NOAA CDO token (improves rate limits) |
| AIRNOW_API_KEY | for US air quality | EPA AirNow key |
| CENSUS_API_KEY | for US demographics | US Census key |

## Scoring formula

CARA uses the PHRAT quadratic mean formula:

```
Total = sqrt( sum( weight_i * score_i^2 ) )
```

All domain scores are on [0, 1]. All weights must sum to 1.0.
The formula is implemented in `utils/risk_engine.py`.

## Risk classification

| Score | Level | Color |
|-------|-------|-------|
| 0.75 - 1.00 | Critical | Dark red |
| 0.55 - 0.74 | High | Red |
| 0.35 - 0.54 | Moderate | Orange |
| 0.15 - 0.34 | Low | Yellow |
| 0.00 - 0.14 | Minimal | Green |
