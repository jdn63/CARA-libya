# Adapting CARA for a US State, Territory, or Tribal Nation

This guide covers deploying CARA for any US jurisdiction: states, territories,
Tribal nations, or sub-state health departments.

## Prerequisites

- Python 3.11 or later
- PostgreSQL 14 or later with PostGIS extension
- A free AirNow API key: https://docs.airnowapi.org/
- A free Census Bureau API key: https://api.census.gov/data/key_signup.html
- Git

## Step 1: Clone the template

```
git clone https://github.com/jdn63/CARA-template.git my-cara-deployment
cd my-cara-deployment
```

## Step 2: Copy US connector implementations

The template includes the connector interface and global connectors.
US-specific connector implementations must be copied from the
CARA Wisconsin deployment (jdn63/CARA). Copy these files from the
Wisconsin repo into `utils/connectors/us/`:

- `utils/air_quality_data.py` (AirNow) -> rename to `utils/connectors/us/airnow_connector.py`
- `utils/nssp_respiratory.py` (CDC NSSP) -> `utils/connectors/us/cdc_nssp_connector.py`
- `utils/noaa_storm_events.py` (NOAA) -> `utils/connectors/us/noaa_ncei_connector.py`
- And so on for each connector you need.

Each connector must be adapted to implement `BaseConnector.fetch()`,
`is_available()`, and `source_info()`. See `docs/adding_custom_connector.md`.

## Step 3: Configure your jurisdiction

```
cp config/jurisdiction.yaml.example config/jurisdiction.yaml
```

Edit `config/jurisdiction.yaml`:

- Set `jurisdiction.profile` to `us_state`
- Set `jurisdiction.country_code` to `US`
- Set your state FIPS code and subdivision list (counties or districts)
- Replace the Wisconsin county list with your state's counties
- Update `regional_groups` to reflect your state's health districts or regions

## Step 4: Set the profile

In your `.env` file, set `CARA_PROFILE=us_state`.

## Step 5: Replace Wisconsin-specific static data

The Wisconsin deployment uses several static data files in `attached_assets/`.
These include the FEMA NRI extract for Wisconsin counties. For another state:

1. Download the FEMA NRI table for your state from:
   https://hazards.fema.gov/nri/data-resources
2. Replace the NRI CSV in `attached_assets/` with your state's file
3. Update the NRI connector to use the new filename

## Step 6: Configure API keys

```
AIRNOW_API_KEY=your_key
CENSUS_API_KEY=your_key
CARA_PROFILE=us_state
```

## Step 7: Assessment framework

The US state profile uses the CDC PHEP (Public Health Emergency Preparedness)
framework. The 15 PHEP capabilities are mapped to domain scores automatically.
Action plans are generated using PHEP capability language.

## Step 8: Active shooter domain

The US profile enables the active shooter sub-type of the mass casualty domain.
Data sources:
- Gun Violence Archive (GVA) — real-time incident data
- RAND State Firearm Law Database — state law restrictiveness score
- NCES School Survey on Crime and Safety — school security data

If active shooter data sources are unavailable in your deployment, the mass
casualty domain falls back to proxy-based estimation clearly labeled as such.

## Enabled domains for the US state profile

- Natural hazards (FEMA NRI + NOAA Storm Events + OpenFEMA)
- Health metrics (CDC NSSP + County Health Rankings + CDC PLACES)
- Air quality (EPA AirNow)
- Extreme heat (NWS Alerts + NOAA Climate at a Glance)
- Dam failure (USACE NID + WI DNR or equivalent state dam database)
- Vector-borne disease (state or CDC ArboNET surveillance data)
- Mass casualty / active shooter (GVA + RAND + NCES SSOCS)

Conflict and displacement is disabled for the US profile.

## Regional groupings

The US profile supports grouping counties into health districts, emergency
management regions, or other sub-state groupings. Configure your groupings
in `config/jurisdiction.yaml` under `regional_groups`. For Wisconsin-style
HERC regions, the six HERC region groupings are an example of this pattern.

## HVA compatibility

The US profile includes support for Kaiser Permanente Hazard Vulnerability
Analysis (HVA) compatible Excel exports. To enable, set `hva_compatible: true`
in your profile configuration (already set for the us_state profile).

## Adjusting weights

Default weights for the US state profile:

- Natural hazards: 28%
- Mass casualty: 18%
- Health metrics: 17%
- Air quality: 12%
- Extreme heat: 11%
- Dam failure: 7%
- Vector-borne disease: 7%

To override, add entries under `overrides.weights` in `config/jurisdiction.yaml`.
Weights must sum to 1.0; the engine normalizes automatically if they do not.
