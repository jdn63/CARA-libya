"""
Jurisdiction manager for CARA template.

Loads jurisdiction list from the profile configuration and GADM boundary data.
Provides a unified interface for the risk engine and templates to query
jurisdictions regardless of whether they're US counties, GADM districts,
or custom-defined administrative units.
"""

import json
import logging
import os
from typing import Any, Dict, List, Optional
import yaml

logger = logging.getLogger(__name__)

CONFIG_PATH = os.path.join('config', 'jurisdiction.yaml')


class JurisdictionManager:
    """
    Manages the list of jurisdictions for a CARA deployment.

    Jurisdictions can come from three sources (in priority order):
    1. Explicit subdivision list in jurisdiction.yaml
    2. GADM boundary file (if gadm_connector is available)
    3. A custom jurisdictions CSV or JSON provided by the deployer

    The manager provides:
    - get_all() — full list of jurisdictions
    - get_by_id(id) — single jurisdiction by its identifier
    - get_regional_groups() — regional groupings
    - get_population(id) — population for a jurisdiction
    """

    def __init__(self, config: Optional[Dict[str, Any]] = None):
        self.config = config or self._load_config()
        self._jurisdictions: Optional[List[Dict[str, Any]]] = None
        self._regional_groups: Optional[List[Dict[str, Any]]] = None

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
            self._regional_groups = (
                self.config.get('jurisdiction', {}).get('regional_groups', [])
            )
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

    def get_country_config(self) -> Dict[str, Any]:
        """Return the top-level jurisdiction configuration."""
        return self.config.get('jurisdiction', {})

    def _load_jurisdictions(self) -> List[Dict[str, Any]]:
        subdivisions = (
            self.config.get('jurisdiction', {}).get('subdivisions', [])
        )
        if subdivisions:
            logger.info(f"Loaded {len(subdivisions)} jurisdictions from jurisdiction.yaml")
            return [
                {
                    'id': s.get('id', ''),
                    'name': s.get('name', ''),
                    'level': s.get('level', 2),
                    'population': s.get('population', 0),
                    'area_sq_km': s.get('area_sq_km', 0),
                    'capital': s.get('capital', ''),
                    'gadm_gid': s.get('gadm_gid', ''),
                    'notes': s.get('notes', ''),
                }
                for s in subdivisions
                if s.get('id') and s.get('name')
            ]

        gadm_path = self._find_gadm_file()
        if gadm_path:
            return self._load_from_gadm(gadm_path)

        logger.warning(
            "No jurisdictions found in jurisdiction.yaml and no GADM file available. "
            "Add subdivisions to jurisdiction.yaml or download GADM data."
        )
        return []

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
                        'id': gid,
                        'name': name,
                        'level': level,
                        'population': 0,
                        'area_sq_km': 0,
                        'capital': '',
                        'gadm_gid': gid,
                        'notes': '',
                    })
            logger.info(f"Loaded {len(jurisdictions)} jurisdictions from GADM file")
            return sorted(jurisdictions, key=lambda x: x['name'])
        except Exception as e:
            logger.error(f"Failed to load jurisdictions from GADM: {e}")
            return []

    def _load_config(self) -> Dict[str, Any]:
        if os.path.exists(CONFIG_PATH):
            try:
                with open(CONFIG_PATH, 'r') as f:
                    return yaml.safe_load(f) or {}
            except Exception as e:
                logger.error(f"Failed to load jurisdiction config: {e}")
        return {}
