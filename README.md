# CARA Template

Comprehensive Automated Risk Assessment (CARA) — Deployable Template

CARA is an open-source geospatial public health and emergency preparedness risk assessment
platform. This repository is the deployable template, designed to be adapted for any jurisdiction:
US states, territories, Tribal nations, countries, provinces, districts, or other administrative
entities.

## Two deployment profiles included

**US State / Territory / Tribal Nation profile**
Uses US-specific data sources: FEMA NRI, NOAA Storm Events, OpenFEMA, CDC NSSP, EPA AirNow,
CDC SVI, County Health Rankings, CDC PLACES, and USACE NID dam inventory.
Assessment framework: CDC PHEP (15 capabilities).

**International profile**
Uses globally available data sources: WHO Global Health Observatory, EM-DAT, ACLED conflict
data, IDMC displacement data, OpenAQ, NOAA GSOD, World Bank Open Data, and GADM boundaries.
Assessment framework: WHO International Health Regulations (IHR 2005, 19 core capacities).

Both profiles use the same PHRAT quadratic mean scoring formula and produce the same
risk dashboard, action plan, methodology documentation, and data export outputs.

## What is new in the international profile

The international profile includes two domains not found in the Wisconsin deployment:

**Conflict and Displacement Risk**
Fully implemented using ACLED political violence data and IDMC internal displacement figures.
Scores jurisdiction risk from armed conflict, mass violence, and population displacement
using the EVR (Exposure-Vulnerability-Resilience) framework. Includes action plan items
aligned with WHO and UNHCR cluster standards.

**Mass Casualty and Public Safety Events (generalized)**
The US-specific "active shooter" domain is replaced with a general mass casualty domain
covering terrorism, mass violence, civil unrest, and large-scale industrial accidents.
For US state deployments, the active shooter sub-component is re-enabled via profile
configuration.

## Quick start

```
git clone https://github.com/jdn63/CARA-template.git
cd CARA-template
cp config/jurisdiction.yaml.example config/jurisdiction.yaml
# Edit jurisdiction.yaml with your jurisdiction details
cp .env.example .env
# Edit .env with your API keys and database URL
pip install -r requirements.txt
alembic upgrade head
python main.py
```

For international deployments: see `docs/adapting_for_international.md`
For US state deployments: see `docs/adapting_for_us_state.md`

## Documentation

- `docs/adapting_for_international.md` — full guide for international deployments
- `docs/adapting_for_us_state.md` — full guide for US state / territory deployments
- `docs/adding_custom_connector.md` — how to add any data source as a CARA connector
- `docs/configuration_reference.md` — complete reference for all configuration options

## Reference implementation

The Wisconsin deployment of CARA (serving 101 jurisdiction entries across 7 HERC regions
for the Wisconsin Department of Health Services) is the reference implementation:
https://github.com/jdn63/CARA

## Risk engine

CARA uses the PHRAT (Public Health Risk Assessment Tool) quadratic mean formula:

    Total Score = sqrt( sum( weight_i x score_i^2 ) )

All domain scores are on [0, 1]. Domain weights are configurable per profile and
per jurisdiction. The formula is implemented in `utils/risk_engine.py`.

## Data sources (international profile)

| Source | Use | Key Required |
|--------|-----|-------------|
| WHO Global Health Observatory | Health metrics | No |
| GADM | Administrative boundaries | No |
| EM-DAT (CRED/UCLouvain) | Disaster history | Free registration |
| World Bank Open Data | Social vulnerability | No |
| ACLED | Conflict event data | Free registration |
| IDMC | Displacement data | No |
| OpenAQ | Air quality | No (optional key for higher limits) |
| NOAA GSOD | Climate / extreme heat | No (optional token) |

## License

GNU Affero General Public License v3.0 (AGPLv3). See LICENSE.

Deployments of CARA that are accessible over a network must make their complete
source code available to users. This ensures that public health improvements made
to CARA benefit all users.

## Citation

Developed and maintained by Jaime Niedermeier. If you use CARA in a publication or
policy document, please cite the reference implementation and this template repository.
