"""
EM-DAT (Emergency Events Database) connector — file-based.

EM-DAT is maintained by the Centre for Research on Epidemiology of Disasters
(CRED) at UC Louvain, Belgium.  Public data downloads (filtered by country) are
available at https://www.emdat.be — no API key required.

Place the downloaded Excel file at:
    data/emdat_libya.xlsx    (or any path matching DATA_FILE below)

EM-DAT classifies disasters into:
  Natural  — Geophysical, Meteorological, Hydrological, Climatological, Biological
  Technological — Transport, Industrial, Miscellaneous

For Libya, Storm Daniel (2023) dominates the natural hazard record:
  13,200 deaths · 1.6 M affected · USD 6.2 B damage
"""

import logging
import os
from datetime import datetime, timezone
from typing import Any, Dict, Optional

logger = logging.getLogger(__name__)

DATA_FILE = os.path.join(os.path.dirname(__file__), '..', '..', '..', 'data', 'emdat_libya.xlsx')

NATURAL_TYPES = {'Flood', 'Storm', 'Earthquake', 'Volcanic activity',
                 'Drought', 'Wildfire', 'Landslide', 'Extreme temperature',
                 'Fog', 'Glacial lake outburst'}

HYDRO_TYPES   = {'Flood', 'Storm'}   # Hydrological + meteorological


class EMDATConnector:
    """
    Reads the Libya EM-DAT public export and derives indicators for CARA.

    Returned keys (all counts/sums are for the rolling 10-year window unless
    noted):
        natural_events_10yr        – total natural disaster events
        natural_deaths_10yr        – total deaths (natural disasters)
        natural_affected_10yr      – total affected persons
        natural_damage_usd         – total economic damage (USD)

        flood_events_10yr          – flood + storm events (hydrometeorological)
        flood_deaths_10yr          – deaths from floods + storms
        flood_affected_10yr        – affected from floods + storms

        storm_daniel_deaths        – deaths attributed to Storm Daniel 2023
        storm_daniel_affected      – persons affected by Storm Daniel 2023
        storm_daniel_damage_usd    – economic damage from Storm Daniel (USD)

        wildfire_events_10yr       – wildfire events (0 for Libya)
        extreme_cold_events_10yr   – extreme cold events (0 for Libya)

        migrant_water_events_10yr  – migrant drowning incidents (transport/water)
        migrant_water_deaths_10yr  – migrant drowning deaths

        dominant_hazard            – most frequent natural hazard type
        disaster_risk_score        – composite 0–1 score

        data_version               – EM-DAT data version string
        data_year                  – year of latest event in file
        total_records              – total records in the export
        available                  – True if file was parsed successfully
    """

    CACHE_DURATION_SECONDS = 86400 * 30   # file rarely changes

    def __init__(self, country: str = 'Libya', iso2: str = 'LY',
                 config: Optional[Dict[str, Any]] = None):
        self.country = country
        self.iso2 = iso2.upper()

    def is_available(self) -> bool:
        return os.path.exists(DATA_FILE)

    def source_info(self) -> Dict[str, str]:
        return {
            'name': 'EM-DAT (Emergency Events Database, CRED/UCLouvain)',
            'url': 'https://www.emdat.be',
            'update_frequency': 'Monthly — re-download and replace data/emdat_libya.xlsx',
            'license': 'Free for non-commercial use — download from emdat.be',
            'geographic_coverage': 'Libya (LBY) — all disasters recorded since 2000',
            'notes': 'No API key required. File-based connector reads data/emdat_libya.xlsx.',
        }

    def fetch(self, jurisdiction_id: str = 'LY', **kwargs) -> Dict[str, Any]:
        if not self.is_available():
            return {
                'available': False,
                'unavailable_reason': (
                    'EM-DAT data file not found. Download a country export from '
                    'https://www.emdat.be and save it as data/emdat_libya.xlsx'
                ),
            }

        try:
            import pandas as pd
        except ImportError:
            return {'available': False, 'unavailable_reason': 'pandas not installed'}

        try:
            df = pd.read_excel(DATA_FILE, sheet_name='EM-DAT Data', engine='openpyxl')
        except Exception as e:
            logger.error(f'EM-DAT file read error: {e}')
            return {'available': False, 'unavailable_reason': f'File read error: {e}'}

        # ── Rolling 10-year cutoff ───────────────────────────────────────────
        current_year = datetime.now(timezone.utc).year
        cutoff_year  = current_year - 10
        df10 = df[df['Start Year'] >= cutoff_year].copy()

        # ── Natural disasters ────────────────────────────────────────────────
        nat = df10[df10['Disaster Group'] == 'Natural']
        nat_events   = int(len(nat))
        nat_deaths   = int(nat['Total Deaths'].fillna(0).sum())
        nat_affected = int(nat['Total Affected'].fillna(0).sum())
        nat_damage_k = float(nat["Total Damage ('000 US$)"].fillna(0).sum())
        nat_damage   = nat_damage_k * 1_000  # convert USD thousands → USD

        # ── Hydrometeorological (floods + storms) ───────────────────────────
        hydro = nat[nat['Disaster Type'].isin(HYDRO_TYPES)]
        hydro_events   = int(len(hydro))
        hydro_deaths   = int(hydro['Total Deaths'].fillna(0).sum())
        hydro_affected = int(hydro['Total Affected'].fillna(0).sum())

        # ── Storm Daniel specifically (2023-0610-LBY) ───────────────────────
        daniel = df[df['DisNo.'] == '2023-0610-LBY']
        daniel_deaths   = int(daniel['Total Deaths'].fillna(0).sum())
        daniel_affected = int(daniel['Total Affected'].fillna(0).sum())
        daniel_damage_k = float(daniel["Total Damage ('000 US$)"].fillna(0).sum())
        daniel_damage   = daniel_damage_k * 1_000

        # ── Flood-only events (no storms) ───────────────────────────────────
        floods_only = nat[nat['Disaster Type'] == 'Flood']
        floods_events = int(len(floods_only))

        # ── Migrant drownings (Technological/Transport/Water) ────────────────
        mig = df10[(df10['Disaster Group'] == 'Technological') &
                   (df10['Disaster Type'] == 'Water')]
        mig_events = int(len(mig))
        mig_deaths = int(mig['Total Deaths'].fillna(0).sum())

        # ── Dominant natural hazard type ─────────────────────────────────────
        dominant = 'لا بيانات'
        if not nat.empty:
            type_counts = nat['Disaster Type'].value_counts()
            if not type_counts.empty:
                dominant = str(type_counts.idxmax())

        # ── Composite risk score (INFORM-style, natural hazards only) ────────
        freq_score     = min(1.0, nat_events / 10.0)
        mort_score     = min(1.0, nat_deaths / 5_000.0)
        affected_score = min(1.0, nat_affected / 500_000.0)
        damage_score   = min(1.0, nat_damage / 1_000_000_000.0)   # $1B cap
        risk_score = round(
            freq_score * 0.15 + mort_score * 0.40 +
            affected_score * 0.25 + damage_score * 0.20,
            4
        )

        # ── Data version from info sheet ─────────────────────────────────────
        data_version = 'غير محدد'
        try:
            info = pd.read_excel(DATA_FILE, sheet_name='EM-DAT Info', engine='openpyxl')
            ver_rows = info[info.iloc[:, 0].astype(str).str.startswith('Version')]
            if not ver_rows.empty:
                data_version = str(ver_rows.iloc[0, 1])
        except Exception:
            pass

        return {
            'available': True,

            # ── Natural hazard totals (10-year) ──────────────────────────
            'natural_events_10yr':    nat_events,
            'natural_deaths_10yr':    nat_deaths,
            'natural_affected_10yr':  nat_affected,
            'natural_damage_usd':     nat_damage,

            # ── Hydrometeorological (flood + storm) combined ─────────────
            'flood_events_10yr':      hydro_events,    # used by hazard_exposure.py
            'flood_deaths_10yr':      hydro_deaths,
            'flood_affected_10yr':    hydro_affected,

            # ── Flood-only ───────────────────────────────────────────────
            'flood_only_events_10yr': floods_events,

            # ── Storm Daniel (major event) ───────────────────────────────
            'storm_daniel_deaths':    daniel_deaths,
            'storm_daniel_affected':  daniel_affected,
            'storm_daniel_damage_usd': daniel_damage,

            # ── Other hazard types (for hazard_exposure.py) ──────────────
            'wildfire_events_10yr':      0,
            'extreme_cold_events_10yr':  0,
            'dam_failure_score':         None,

            # ── Migrant drownings (transport/maritime hazard) ────────────
            'migrant_water_events_10yr': mig_events,
            'migrant_water_deaths_10yr': mig_deaths,

            # ── Summary ──────────────────────────────────────────────────
            'dominant_hazard':    dominant,
            'disaster_risk_score': risk_score,

            # ── Metadata ─────────────────────────────────────────────────
            'data_version':  data_version,
            'data_year':     str(current_year),
            'total_records': int(len(df)),
            '_last_updated': datetime.now(timezone.utc).isoformat(),
        }
