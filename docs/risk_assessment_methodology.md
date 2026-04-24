# Libya CARA - Risk Assessment Methodology

## Overview

Libya CARA scores subnational disaster and crisis risk for Libya at the
national level and across 148 municipalities using the INFORM Risk Index
methodology, aligned with the Sendai Framework for Disaster Risk
Reduction 2015-2030. The score is computed in
`routes/dashboard.py::_run_pillars()` and pinned by automated tests in
`tests/test_inform.py`.

## Formula

```
INFORM Risk = (Hazard and Exposure x Vulnerability x Lack of Coping Capacity) ^ (1/3)
```

Each pillar is itself a weighted average of its sub-indicators on a
[0, 1] scale, where 1.0 represents the maximum risk and 0.0 represents
no risk. The geometric mean is the authoritative INFORM composition
published by the European Commission Joint Research Centre (JRC) and the
Inter-Agency Standing Committee (IASC). See
https://drmkc.jrc.ec.europa.eu/inform-index.

The three pillars are equally weighted (0.333 each) for the published
Libya profile. All weights are defined in `config/risk_weights.yaml`
under the `profiles.libya` section.

## Pillar 1 - Hazard and Exposure (weight 0.333)

| Sub-domain | Weight | Components |
|------------|--------|------------|
| Infrastructure Hazard | 0.25 | Dam Safety, Electric Grid Reliability, Water and Sewage Systems |
| Natural Hazard | 0.25 | Flooding, Wildfires, Extreme Cold Events, Sandstorms |
| Epidemiological Hazard | 0.25 | Infectious and Emerging Diseases, Vector-Borne Diseases |
| Road Safety Hazard | 0.25 | Road Accident Rate |

## Pillar 2 - Vulnerability (weight 0.333)

Equal weights (0.20 each) across five sub-indicators:

- Response Agency Capacity Gap
- Urban Sprawl / Ad Hoc Construction
- Displacement and Migration Vulnerability
- Lack of Health Awareness
- Security and Safety Vulnerability

## Pillar 3 - Lack of Coping Capacity (weight 0.333)

Scores represent the LACK of coping capacity (high score = low
resilience). Equal weights (0.20 each) across five sub-indicators:

- Emergency Response Time Gap
- Lack of Data Availability
- Community Support Gap
- Healthcare Access Gap
- Institutional Capacity Gap

## Out of Scope by Design

The armed-clashes / political-violence domain present in the upstream
INFORM model is intentionally omitted from the published score pending
political sensitivity review. This decision is documented in
`replit.md` under "Key Design Decisions".

## Sendai Framework Alignment

- Priority 1 (Understanding risk) -> Hazard and Exposure + Vulnerability pillars
- Priority 2 (Governance) -> Coping Capacity pillar
- Priority 3 (Investment in DRR) -> Coping Capacity / institutional_capacity
- Priority 4 (Preparedness) -> Coping Capacity / emergency_response

## Risk Banding

The 0-1 INFORM score is mapped to five bands by
`utils.action_plan_content._inform_classify` (upper-exclusive cut points):

| Band | Score range |
|------|-------------|
| Very Low | 0.00 - 0.20 |
| Low | 0.20 - 0.40 |
| Medium | 0.40 - 0.60 |
| High | 0.60 - 0.80 |
| Very High | 0.80 - 1.00 |

Non-numeric or negative input returns "unavailable".

## Missing-Data Handling

When a municipality has no value for a given indicator, the dashboard
falls back to a regional or national proxy and tags the affected tile
with an explicit "البيانات غير متاحة / Data not available" badge or a
"national proxy" badge so users can see when a published indicator is
not direct evidence for that jurisdiction. Local consolidated uploads
override national proxies for the seven mappable indicators
(`tb_inc`, `u5mort`, `neo_mort`, `water`, `sanitation`, `electricity`,
`pm25`); see `utils/local_overrides.py`.

## Data Sources

See `docs/data_sources_comprehensive_analysis.md` for the full
connector inventory. Headline sources:

- OCHA HDX (data.humdata.org) - IOM DTM, OCHA 3W, UNHCR Libya
- WHO Libya via OCHA HDX (primary); WHO GHO (legacy fallback)
- HeiGIT Accessibility - hospital, primary healthcare, education access
- IDMC via OCHA HDX - displacement stocks and disaster events
- World Bank Open Data - development indicators
- OpenAQ - air quality readings (no Libya stations confirmed yet)
- EM-DAT (CRED/UCLouvain) - Libya disaster history 2000-present, file-based
- NCDC Libya - manual upload of disease surveillance CSVs
- COI Libya - manual upload of coordination capacity CSVs

## References

1. INFORM Risk Index - JRC / IASC.
   https://drmkc.jrc.ec.europa.eu/inform-index
2. Sendai Framework for Disaster Risk Reduction 2015-2030 - UNDRR.
   https://www.undrr.org/implementing-sendai-framework
3. WHO International Health Regulations (IHR) Monitoring Framework.
4. OCHA Humanitarian Data Exchange. https://data.humdata.org
5. EM-DAT International Disaster Database. https://www.emdat.be
6. IDMC Internal Displacement Database. https://www.internal-displacement.org
7. HeiGIT Healthcare Accessibility Analysis.
8. World Bank Open Data. https://data.worldbank.org
