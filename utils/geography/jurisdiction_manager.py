"""
Jurisdiction manager for CARA — Libya deployment.

Loads the 148 Libya municipalities from data/libya_municipalities.json
(and falls back to GADM boundary data or explicit jurisdiction.yaml entries
for non-Libya profiles).

Provides:
  - get_all()                 — full list of municipalities
  - get_by_id(id)             — single municipality by ID
  - get_regional_groups()     — Libya's three historical regions
  - get_population(id)        — population for a municipality
  - get_regional_average(indicator, region) — documented proxy for missing data
  - get_name_ar(id)           — Arabic municipality name
  - get_name_en(id)           — English municipality name

Missing data policy:
  When indicator data is unavailable for a municipality, get_regional_average()
  returns the mean of available values in the same region (west/east/south),
  or the national mean if no regional data exists. All proxy substitutions
  are logged and flagged in output reports per Libya CARA data governance policy.
"""

import json
import logging
import os
from typing import Any, Dict, List, Optional
import yaml

logger = logging.getLogger(__name__)

CONFIG_PATH = os.path.join('config', 'jurisdiction.yaml')
MUNICIPALITIES_JSON = os.path.join('data', 'libya_municipalities.json')


class JurisdictionManager:
    """
    Manages the list of jurisdictions for a CARA deployment.

    For the Libya profile, jurisdictions are loaded from the municipalities
    JSON file. For other profiles, falls back to GADM or jurisdiction.yaml.
    """

    def __init__(self, config: Optional[Dict[str, Any]] = None):
        self.config = config or self._load_config()
        self._jurisdictions: Optional[List[Dict[str, Any]]] = None
        self._regional_groups: Optional[List[Dict[str, Any]]] = None
        self._municipalities_raw: Optional[Dict[str, Any]] = None

    def get_all(self) -> List[Dict[str, Any]]:
        """Return all jurisdictions for this deployment."""
        if self._jurisdictions is None:
            self._jurisdictions = self._load_jurisdictions()
        return self._jurisdictions

    def get_by_id(self, jurisdiction_id: str) -> Optional[Dict[str, Any]]:
        """Return a single jurisdiction by its identifier."""
        return next(
            (j for j in self.get_all() if j.get('id') == jurisdiction_id),
            None
        )

    def get_regional_groups(self) -> List[Dict[str, Any]]:
        """Return all regional groupings."""
        if self._regional_groups is None:
            jconfig = self.config.get('jurisdiction', {})
            self._regional_groups = jconfig.get('regional_groups', [])
        return self._regional_groups

    def get_group_for_jurisdiction(self, jurisdiction_id: str) -> Optional[Dict[str, Any]]:
        """Return the regional group containing the given jurisdiction."""
        for group in self.get_regional_groups():
            if jurisdiction_id in group.get('subdivision_ids', []):
                return group
        return None

    def get_jurisdictions_in_group(self, group_id: str) -> List[Dict[str, Any]]:
        """Return all jurisdictions belonging to the given regional group."""
        group = next(
            (g for g in self.get_regional_groups() if g.get('id') == group_id),
            None
        )
        if not group:
            return []
        ids = set(group.get('subdivision_ids', []))
        return [j for j in self.get_all() if j.get('id') in ids]

    def get_population(self, jurisdiction_id: str) -> int:
        """Return population for a jurisdiction, or 0 if unknown."""
        j = self.get_by_id(jurisdiction_id)
        return int(j.get('population', 0)) if j else 0

    def get_name_ar(self, jurisdiction_id: str) -> str:
        """Return the Arabic name for a municipality."""
        j = self.get_by_id(jurisdiction_id)
        return j.get('name_ar', j.get('name', jurisdiction_id)) if j else jurisdiction_id

    def get_name_en(self, jurisdiction_id: str) -> str:
        """Return the English name for a municipality."""
        j = self.get_by_id(jurisdiction_id)
        return j.get('name_en', j.get('name', jurisdiction_id)) if j else jurisdiction_id

    def get_district_for_municipality(self, jurisdiction_id: str) -> Optional[Dict[str, str]]:
        """Return the district (mantiqa) a municipality belongs to."""
        j = self.get_by_id(jurisdiction_id)
        if not j:
            return None
        district_id = j.get('district', '')
        raw = self._get_municipalities_raw()
        if raw:
            for d in raw.get('districts', []):
                if d.get('id') == district_id:
                    return d
        return {'id': district_id, 'name_ar': district_id, 'name_en': district_id}

    def get_region_for_municipality(self, jurisdiction_id: str) -> str:
        """Return the region ID ('west', 'east', or 'south') for a municipality."""
        j = self.get_by_id(jurisdiction_id)
        return j.get('region', 'west') if j else 'west'

    def get_regional_average(
        self,
        indicator_values: Dict[str, float],
        jurisdiction_id: str,
    ) -> Optional[float]:
        """
        Compute the regional average for an indicator as a proxy for missing data.

        This implements the Libya CARA missing-data policy: when a municipality
        lacks data for an indicator, use the mean of available values from other
        municipalities in the same region (west/east/south). Falls back to the
        national mean if no regional values are available.

        All callers should log proxy usage for audit purposes.

        Args:
            indicator_values: Dict of jurisdiction_id -> float (available values)
            jurisdiction_id:  The municipality needing the proxy

        Returns:
            float proxy value, or None if no reference data exists at all.
        """
        target_region = self.get_region_for_municipality(jurisdiction_id)

        region_values = []
        national_values = []

        for jid, val in indicator_values.items():
            if val is None:
                continue
            try:
                float_val = float(val)
            except (ValueError, TypeError):
                continue
            national_values.append(float_val)
            if self.get_region_for_municipality(jid) == target_region:
                region_values.append(float_val)

        if region_values:
            proxy = sum(region_values) / len(region_values)
            logger.info(
                f"[PROXY] Municipality {jurisdiction_id}: using regional average "
                f"{proxy:.4f} from {len(region_values)} {target_region}-region values. "
                f"Per Libya CARA missing-data policy."
            )
            return round(proxy, 4)

        if national_values:
            proxy = sum(national_values) / len(national_values)
            logger.warning(
                f"[PROXY] Municipality {jurisdiction_id}: no regional data for '{target_region}', "
                f"using national average {proxy:.4f} from {len(national_values)} values."
            )
            return round(proxy, 4)

        logger.error(
            f"[PROXY] Municipality {jurisdiction_id}: no data available at any geographic level."
        )
        return None

    def get_country_config(self) -> Dict[str, Any]:
        """Return the top-level jurisdiction configuration."""
        return self.config.get('jurisdiction', {})

    def _load_jurisdictions(self) -> List[Dict[str, Any]]:
        raw = self._get_municipalities_raw()
        if raw:
            municipalities = raw.get('municipalities', [])
            if municipalities:
                logger.info(f"Loaded {len(municipalities)} municipalities from {MUNICIPALITIES_JSON}")
                return [
                    {
                        'id':           m.get('id', ''),
                        'name':         m.get('name_ar', m.get('name_en', '')),
                        'name_ar':      m.get('name_ar', ''),
                        'name_en':      m.get('name_en', ''),
                        'level':        3,
                        'population':   m.get('population', 0),
                        'area_sq_km':   m.get('area_sq_km', 0),
                        'region':       m.get('region', ''),
                        'district':     m.get('district', ''),
                        'status':       m.get('status', 'needs_verification'),
                        'notes':        m.get('notes', ''),
                        'gadm_gid':     m.get('gadm_gid', ''),
                    }
                    for m in municipalities
                    if m.get('id') and (m.get('name_ar') or m.get('name_en'))
                ]

        subdivisions = self.config.get('jurisdiction', {}).get('subdivisions', [])
        if subdivisions:
            logger.info(f"Loaded {len(subdivisions)} jurisdictions from jurisdiction.yaml")
            return [
                {
                    'id':        s.get('id', ''),
                    'name':      s.get('name', ''),
                    'name_ar':   s.get('name_ar', s.get('name', '')),
                    'name_en':   s.get('name_en', s.get('name', '')),
                    'level':     s.get('level', 2),
                    'population':s.get('population', 0),
                    'area_sq_km':s.get('area_sq_km', 0),
                    'region':    s.get('region', ''),
                    'notes':     s.get('notes', ''),
                }
                for s in subdivisions
                if s.get('id') and s.get('name')
            ]

        gadm_path = self._find_gadm_file()
        if gadm_path:
            return self._load_from_gadm(gadm_path)

        logger.warning(
            "No jurisdictions found. Add municipalities to data/libya_municipalities.json "
            "or add subdivisions to config/jurisdiction.yaml."
        )
        return []

    def _get_municipalities_raw(self) -> Optional[Dict[str, Any]]:
        if self._municipalities_raw is not None:
            return self._municipalities_raw

        jconfig = self.config.get('jurisdiction', {})
        json_path = jconfig.get('geographic', {}).get('municipalities_file', MUNICIPALITIES_JSON)

        if os.path.exists(json_path):
            try:
                with open(json_path, 'r', encoding='utf-8') as f:
                    self._municipalities_raw = json.load(f)
                return self._municipalities_raw
            except Exception as e:
                logger.error(f"Failed to load municipalities JSON from {json_path}: {e}")

        return None

    def _find_gadm_file(self) -> Optional[str]:
        jconfig = self.config.get('jurisdiction', {})
        country = jconfig.get('geographic', {}).get('gadm_country', '')
        level = jconfig.get('geographic', {}).get('gadm_level', 2)
        if not country:
            return None
        path = os.path.join('data', 'gadm', f'gadm41_{country.upper()}_{level}.json')
        return path if os.path.exists(path) else None

    def _load_from_gadm(self, gadm_path: str) -> List[Dict[str, Any]]:
        jconfig = self.config.get('jurisdiction', {})
        level = jconfig.get('geographic', {}).get('gadm_level', 2)
        try:
            with open(gadm_path, 'r', encoding='utf-8') as f:
                geojson = json.load(f)
            features = geojson.get('features', [])
            name_key = f'NAME_{level}'
            gid_key = f'GID_{level}'
            jurisdictions = []
            for feat in features:
                props = feat.get('properties', {})
                gid = props.get(gid_key, '')
                name = props.get(name_key, '')
                if gid and name:
                    jurisdictions.append({
                        'id': gid, 'name': name, 'name_ar': name, 'name_en': name,
                        'level': level, 'population': 0, 'area_sq_km': 0,
                        'region': '', 'gadm_gid': gid, 'notes': '',
                    })
            logger.info(f"Loaded {len(jurisdictions)} jurisdictions from GADM file")
            return sorted(jurisdictions, key=lambda x: x['name'])
        except Exception as e:
            logger.error(f"Failed to load jurisdictions from GADM: {e}")
            return []

    def _load_config(self) -> Dict[str, Any]:
        if os.path.exists(CONFIG_PATH):
            try:
                with open(CONFIG_PATH, 'r', encoding='utf-8') as f:
                    return yaml.safe_load(f) or {}
            except Exception as e:
                logger.error(f"Failed to load jurisdiction config: {e}")
        return {}
