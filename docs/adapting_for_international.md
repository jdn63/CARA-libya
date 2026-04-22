# Adapting CARA for International Deployment

This guide walks through adapting the CARA template for a country, province, district,
Tribal territory, or other non-US jurisdiction.

## Prerequisites

- Python 3.11 or later
- PostgreSQL 14 or later with PostGIS extension
- A free ACLED registration (for conflict data): https://acleddata.com/register/
- A free EM-DAT registration (for disaster history): https://www.emdat.be/
- Git

## Step 1: Clone the template

```
git clone https://github.com/jdn63/CARA-template.git my-cara-deployment
cd my-cara-deployment
```

## Step 2: Configure your jurisdiction

Copy the example jurisdiction configuration and edit it:

```
cp config/jurisdiction.yaml.example config/jurisdiction.yaml
```

Open `config/jurisdiction.yaml` and fill in:

- `jurisdiction.name` — your jurisdiction's full name
- `jurisdiction.country_code` — ISO 3166-1 alpha-2 code (e.g., KE for Kenya)
- `jurisdiction.iso3166_1` — same as above
- `jurisdiction.profile` — set to `international`
- `jurisdiction.population` — total population
- `jurisdiction.geographic.gadm_country` — same as country_code
- `jurisdiction.geographic.gadm_level` — administrative level for assessments (usually 2)
- `jurisdiction.subdivisions` — list your districts/counties/provinces

If your country uses a different administrative hierarchy, update
`jurisdiction.administrative_hierarchy` to label the levels correctly
(e.g., Governorate instead of Province).

## Step 3: Set the profile

Set `CARA_PROFILE=international` in your `.env` file (copy from `.env.example`).

## Step 4: Get GADM boundaries

The template will automatically download GADM boundary data for your country
the first time a dashboard is loaded. You can also trigger it manually:

```python
from utils.connectors.global.gadm_connector import GADMConnector
connector = GADMConnector(country_code='KE', level=2)
connector.fetch('country')
```

GADM files are cached in `data/gadm/` after first download. They are large
(typically 5-50 MB per country at level 2) and do not need frequent refreshes.

## Step 5: Configure API keys

ACLED and EM-DAT require free registrations. After registering:

ACLED: Set `ACLED_API_KEY` and `ACLED_EMAIL` in your environment.
EM-DAT: Set `EMDAT_API_KEY` in your environment.

All other global connectors (WHO GHO, World Bank, IDMC, OpenAQ) require no API key.

## Step 6: Set up the database

```
export DATABASE_URL=postgresql://cara:password@localhost:5432/cara
alembic upgrade head
```

## Step 7: Run locally

```
export SESSION_SECRET=$(python3 -c "import secrets; print(secrets.token_hex(32))")
python main.py
```

Visit http://localhost:5000 and select a district to see a risk assessment.

## Step 8: Deploy to production

Copy `render.yaml.example` to `render.yaml` and adapt it for your platform.
For Render.com, this file is ready to use with minor edits (database name,
service name, API keys set via Render dashboard).

## Enabled domains for the international profile

- Natural hazards (EM-DAT historical disasters + NOAA GSOD climate)
- Health metrics (WHO GHO indicators)
- Air quality (OpenAQ monitoring network)
- Extreme heat (NOAA GSOD temperature data)
- Vector-borne disease (WHO GHO disease surveillance)
- Mass casualty and public safety events (EM-DAT + ACLED)
- Conflict and displacement (ACLED + IDMC) — fully implemented

## Assessment framework

The international profile uses the WHO International Health Regulations (IHR)
framework for action plan generation. The 19 IHR core capacities and JEE
references are mapped to CARA domain scores automatically.

## Adding sub-national data sources

If your country has official sub-national health or hazard data sources,
implement them as custom connectors. See `docs/adding_custom_connector.md`.

## Adjusting weights

The default international weights are:

- Natural hazards: 25%
- Conflict and displacement: 20%
- Health metrics: 17%
- Mass casualty: 12%
- Air quality: 10%
- Extreme heat: 10%
- Vector-borne disease: 6%

To override these for your jurisdiction, add entries under
`overrides.weights` in `config/jurisdiction.yaml`.

## Disabling domains

To disable a domain (e.g., if conflict data is not relevant), add it to
`domains.disabled` in `config/profiles/international.yaml`. The risk engine
will rebalance weights automatically to sum to 1.0.
