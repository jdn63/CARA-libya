# Libya CARA - Data Dictionary

## Overview

This document is the reference for variables, scores, and identifiers
used by the Libya CARA platform. Libya CARA scores subnational
disaster and crisis risk for Libya at the national level (LY) and
across 148 municipalities, using the INFORM Risk Index methodology
aligned with the Sendai Framework.

## Table of Contents

- [Score Variables](#score-variables)
- [Hazard and Exposure Pillar](#hazard-and-exposure-pillar)
- [Vulnerability Pillar](#vulnerability-pillar)
- [Coping Capacity Pillar](#coping-capacity-pillar)
- [Geographic Variables](#geographic-variables)
- [Temporal Variables](#temporal-variables)
- [Source Kinds and Tile Badges](#source-kinds-and-tile-badges)
- [API Response Format](#api-response-format)

## Score Variables

### Composite Score

| Variable | Type | Range | Unit | Description |
|----------|------|-------|------|-------------|
| `inform_score` | Float | 0.0 - 1.0 | Normalised | Geometric-mean composite of the three pillars |
| `risk_band` | String | - | Categorical | very_low, low, medium, high, very_high (returns `unavailable` for missing input) |
| `hazard_exposure_score` | Float | 0.0 - 1.0 | Normalised | Pillar 1 weighted average |
| `vulnerability_score` | Float | 0.0 - 1.0 | Normalised | Pillar 2 weighted average |
| `coping_capacity_score` | Float | 0.0 - 1.0 | Normalised | Pillar 3 weighted average (LACK of coping; high = low resilience) |

INFORM formula:

```
inform_score = (hazard_exposure_score * vulnerability_score * coping_capacity_score) ^ (1/3)
```

### Risk Bands

`utils.action_plan_content._inform_classify` (upper-exclusive cuts):

| Band | Score range |
|------|-------------|
| very_low | 0.00 - 0.20 |
| low | 0.20 - 0.40 |
| medium | 0.40 - 0.60 |
| high | 0.60 - 0.80 |
| very_high | 0.80 - 1.00 |

## Hazard and Exposure Pillar

Pillar weight: 0.333. Sub-domains weighted equally (0.25 each).

### Infrastructure Hazard

| Variable | Range | Source | Description |
|----------|-------|--------|-------------|
| `dam_safety` | 0.0 - 1.0 | Government data | Structural risk of major dams (Derna events as historical anchor) |
| `electric_grid` | 0.0 - 1.0 | World Bank `EG.ELC.ACCS.ZS`, government data | Grid reliability and access |
| `water_sewage` | 0.0 - 1.0 | World Bank water/sanitation indicators, NCDC outbreak signals | Water and sewage system risk |

### Natural Hazard

| Variable | Range | Source | Description |
|----------|-------|--------|-------------|
| `flooding` | 0.0 - 1.0 | EM-DAT, IDMC disaster events | Pluvial and fluvial flooding (Storm Daniel 2023 anchor) |
| `wildfire` | 0.0 - 1.0 | EM-DAT | Wildfire and bushfire frequency and severity |
| `extreme_cold` | 0.0 - 1.0 | EM-DAT, NOAA reanalysis where available | Extreme cold events |
| `sandstorm` | 0.0 - 1.0 | EM-DAT, NCDC respiratory signals | Sandstorm frequency and impact |

### Epidemiological Hazard

| Variable | Range | Source | Description |
|----------|-------|--------|-------------|
| `infectious_disease` | 0.0 - 1.0 | NCDC Libya, WHO Libya HDX | Combined burden of infectious and emerging diseases |
| `vector_borne` | 0.0 - 1.0 | NCDC Libya, WHO Libya HDX | Vector-borne disease incidence |
| `tb_inc` | Float | WHO Libya HDX | Tuberculosis incidence per 100k (overridable per municipality) |
| `u5mort` | Float | WHO Libya HDX | Under-5 mortality per 1000 live births (overridable per municipality) |
| `neo_mort` | Float | WHO Libya HDX | Neonatal mortality per 1000 live births (overridable per municipality) |

### Road Safety Hazard

| Variable | Range | Source | Description |
|----------|-------|--------|-------------|
| `accident_rate` | 0.0 - 1.0 | WHO Libya HDX, government statistics | Road accident rate |

## Vulnerability Pillar

Pillar weight: 0.333. Sub-indicators weighted equally (0.20 each).

| Variable | Range | Source | Description |
|----------|-------|--------|-------------|
| `agency_capacity_gap` | 0.0 - 1.0 | OCHA 3W, COI Libya | Understaffing, underfunding of emergency response agencies |
| `urban_sprawl` | 0.0 - 1.0 | World Bank urbanisation, government data | Rate of unplanned residential building |
| `displacement_vulnerability` | 0.0 - 1.0 | IDMC via HDX, IOM DTM, UNHCR | IDP and migrant exposure to compounded risk |
| `health_unawareness` | 0.0 - 1.0 | WHO Libya HDX literacy / education proxies | Lack of health awareness |
| `security_vulnerability` | 0.0 - 1.0 | Government data, news monitoring | Rate of violence and insecurity (armed-clashes domain omitted by design) |

## Coping Capacity Pillar

Pillar weight: 0.333. Sub-indicators weighted equally (0.20 each).
Scores represent the LACK of coping capacity (high score = low
resilience).

| Variable | Range | Source | Description |
|----------|-------|--------|-------------|
| `response_time_gap` | 0.0 - 1.0 | HeiGIT travel time, COI Libya | Emergency response time gap |
| `data_availability_gap` | 0.0 - 1.0 | Internal completeness audit | Lack of historical and interoperable data |
| `community_support_gap` | 0.0 - 1.0 | OCHA 3W presence, COI Libya | Weak community-level mutual support and civil-society engagement |
| `healthcare_access_gap` | 0.0 - 1.0 | HeiGIT hospital and primary-care travel time | Healthcare access gap |
| `institutional_capacity_gap` | 0.0 - 1.0 | World Bank governance indicators, COI Libya | Government readiness for DRR investment |
| `water` | Float | World Bank `SH.H2O.BASW.ZS` | Basic drinking water access (overridable per municipality) |
| `sanitation` | Float | World Bank `SH.STA.BASS.ZS` | Basic sanitation access (overridable per municipality) |
| `electricity` | Float | World Bank `EG.ELC.ACCS.ZS` | Electricity access (overridable per municipality) |
| `pm25` | Float | OpenAQ where available | Annual mean PM2.5 (overridable per municipality) |

## Geographic Variables

### Jurisdiction Information

| Variable | Type | Description |
|----------|------|-------------|
| `jurisdiction_id` | String | `LY` for the national view; `LY-NNN` for one of the 148 municipalities |
| `jurisdiction_name` | String | Official jurisdiction name (Arabic primary, English secondary) |
| `jurisdiction_type` | String | `national`, `municipality` |
| `region` | String | West (الغرب), East (الشرق), South (الجنوب) |
| `district` | String | One of 22 ADM1 districts |
| `needs_verification` | Boolean | Flagged when identifier or population estimate is pending Libyan government confirmation |

Source: `data/libya_municipalities.json`. Loader:
`utils/geography/jurisdiction_manager.py`.

### Geographic Characteristics

| Variable | Type | Description |
|----------|------|-------------|
| `population_total` | Integer | Population estimate (latest available) |
| `area_square_km` | Float | Total jurisdiction area in km^2 |
| `centroid_lat` | Float | Geographic centre latitude |
| `centroid_lon` | Float | Geographic centre longitude |

## Temporal Variables

| Variable | Type | Description |
|----------|------|-------------|
| `assessment_date` | DateTime | ISO 8601 timestamp of the assessment run |
| `data_freshness_days` | Integer | Days since each connector cache was refreshed |
| `connector_year` | Integer | Reporting year of the underlying source value (per indicator) |

### Refresh Cadence

| Job | Cadence | Connectors |
|-----|---------|------------|
| `refresh_libya_hdx` | 168 h (weekly) | OCHA HDX (IOM DTM, OCHA 3W, UNHCR), HeiGIT, IDMC via HDX |
| `refresh_libya_global` | 720 h (monthly) | WHO Libya HDX (primary), WHO GHO (legacy fallback), World Bank, OpenAQ |

Scheduler config: `data/config/scheduler_config.json`.

## Source Kinds and Tile Badges

`_stamp_source_kinds` (in `routes/dashboard.py`) tags every tile with
one of the following source kinds for transparency. The dashboard
template renders a green "محلي / Local" badge for `local` data and an
amber "وطني / National" badge whenever a country-level value is being
applied as a per-municipality proxy.

| `source_kind` | Meaning |
|---------------|---------|
| `local` | Value comes from a consolidated municipal upload |
| `measured` | Direct measurement at this jurisdiction |
| `national` | Country-level value applied as-is for the national view |
| `national_proxy` | Country-level value used at the municipal level |
| `proxy` | Regional or ADM1 value propagated to municipal level |

Local override scope (subnational only, seven indicators):
`tb_inc`, `u5mort`, `neo_mort`, `water`, `sanitation`, `electricity`,
`pm25`. The national LY view never applies overrides. See
`utils/local_overrides.py`.

## API Response Format

`GET /api/risk-assessment/<jurisdiction_id>`:

```json
{
  "jurisdiction_id": "LY-063",
  "jurisdiction_name": "Misrata",
  "jurisdiction_name_ar": "مصراتة",
  "assessment_date": "2026-04-24T08:00:00Z",
  "inform_score": 0.58,
  "risk_band": "medium",
  "pillars": {
    "hazard_exposure": {
      "score": 0.62,
      "sub_domains": {
        "infrastructure_hazard": 0.55,
        "natural_hazard": 0.71,
        "epidemiological_hazard": 0.60,
        "road_safety_hazard": 0.62
      }
    },
    "vulnerability": {
      "score": 0.55,
      "indicators": {
        "agency_capacity_gap": 0.50,
        "urban_sprawl": 0.65,
        "displacement_vulnerability": 0.60,
        "health_unawareness": 0.50,
        "security_vulnerability": 0.50
      }
    },
    "coping_capacity": {
      "score": 0.57,
      "indicators": {
        "response_time_gap": 0.60,
        "data_availability_gap": 0.65,
        "community_support_gap": 0.50,
        "healthcare_access_gap": 0.55,
        "institutional_capacity_gap": 0.55
      }
    }
  },
  "metadata": {
    "methodology": "INFORM",
    "profile": "libya",
    "sendai_aligned": true,
    "armed_clashes_omitted": true,
    "connectors": ["who_hdx", "idmc_hdx", "heigit", "iom", "worldbank", "ncdc_libya", "coi_libya"]
  }
}
```

## Out of Scope by Design

The armed-clashes / political-violence domain present in the upstream
INFORM model is intentionally omitted from the published Libya score
pending political sensitivity review.

## Test Coverage

`tests/test_inform.py` validates the cube-root composition, the 0-1
banding helper, and a full national-level dashboard score
end-to-end with synthetic connector data. See `tests/README.md` for
the full suite description.

---

Last reviewed: April 2026.
