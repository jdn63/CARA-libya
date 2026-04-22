"""
GADM boundary downloader and cache for CARA template.

Downloads administrative boundary GeoJSON files from the GADM API for any country
and administrative level, stores them locally under data/gadm/, and provides
a simple loader interface used by the JurisdictionManager.

GADM public data: https://gadm.org/data.html
Level 0 = country, 1 = first-level subdivisions, 2 = second-level subdivisions.
"""

import json
import logging
import os
import urllib.request
import urllib.error
from typing import Any, Dict, List, Optional

logger = logging.getLogger(__name__)

GADM_BASE_URL = "https://geodata.ucdavis.edu/gadm/gadm4.1/json"
GADM_DATA_DIR = os.path.join("data", "gadm")


def gadm_file_path(country_code: str, level: int) -> str:
    """Return the local cache path for a GADM GeoJSON file."""
    os.makedirs(GADM_DATA_DIR, exist_ok=True)
    return os.path.join(GADM_DATA_DIR, f"gadm41_{country_code.upper()}_{level}.json")


def is_cached(country_code: str, level: int) -> bool:
    """Return True if the GADM file is already downloaded."""
    return os.path.exists(gadm_file_path(country_code, level))


def download_gadm(country_code: str, level: int, force: bool = False) -> bool:
    """
    Download a GADM GeoJSON file for the given country and administrative level.

    Args:
        country_code: ISO 3166-1 alpha-3 country code (e.g. "LBY", "USA", "MEX").
        level: Administrative level (1 or 2 for sub-national use; 0 = country outline).
        force: If True, re-download even if the file is already cached.

    Returns:
        True if the file is available (downloaded or already cached), False on failure.
    """
    path = gadm_file_path(country_code, level)
    if os.path.exists(path) and not force:
        logger.debug(f"GADM cache hit: {path}")
        return True

    url = f"{GADM_BASE_URL}/gadm41_{country_code.upper()}_{level}.json"
    logger.info(f"Downloading GADM boundaries: {url}")

    try:
        req = urllib.request.Request(
            url,
            headers={"User-Agent": "CARA-Template/1.0 (github.com/jdn63/CARA-template)"}
        )
        with urllib.request.urlopen(req, timeout=60) as response:
            data = response.read()

        with open(path, "wb") as f:
            f.write(data)

        size_kb = len(data) / 1024
        logger.info(f"GADM download complete: {path} ({size_kb:.0f} KB)")
        return True

    except urllib.error.HTTPError as e:
        if e.code == 404:
            logger.warning(
                f"GADM file not found for {country_code} level {level}. "
                f"Check the country code at https://gadm.org/download_country.html"
            )
        else:
            logger.error(f"GADM download HTTP error {e.code}: {e.reason}")
    except urllib.error.URLError as e:
        logger.error(f"GADM download network error: {e.reason}")
    except Exception as e:
        logger.error(f"GADM download failed: {e}")

    return False


def load_gadm(country_code: str, level: int,
              auto_download: bool = True) -> Optional[Dict[str, Any]]:
    """
    Load a GADM GeoJSON file as a Python dict.

    Downloads the file first if not cached and auto_download is True.

    Args:
        country_code: ISO 3166-1 alpha-3 country code.
        level: Administrative level.
        auto_download: If True, attempt download if file is not cached.

    Returns:
        GeoJSON dict, or None if unavailable.
    """
    path = gadm_file_path(country_code, level)

    if not os.path.exists(path):
        if auto_download:
            success = download_gadm(country_code, level)
            if not success:
                return None
        else:
            logger.warning(
                f"GADM file not found: {path}. "
                f"Call download_gadm('{country_code}', {level}) to download it."
            )
            return None

    try:
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception as e:
        logger.error(f"Failed to parse GADM file {path}: {e}")
        return None


def list_subdivisions(country_code: str, level: int,
                      auto_download: bool = True) -> List[Dict[str, Any]]:
    """
    Return a flat list of subdivision records from a GADM file.

    Each record contains:
        id      — GID string (e.g. "LBY.3_1")
        name    — English name
        gadm_gid — same as id
        level   — administrative level

    Args:
        country_code: ISO 3166-1 alpha-3 country code.
        level: Administrative level to enumerate.
        auto_download: Download if not cached.

    Returns:
        List of subdivision dicts, sorted by name.
    """
    geojson = load_gadm(country_code, level, auto_download=auto_download)
    if not geojson:
        return []

    features = geojson.get("features", [])
    name_key = f"NAME_{level}"
    gid_key = f"GID_{level}"

    result = []
    for feat in features:
        props = feat.get("properties", {})
        gid = props.get(gid_key, "")
        name = props.get(name_key, "")
        if gid and name:
            result.append({
                "id": gid,
                "name": name,
                "gadm_gid": gid,
                "level": level,
                "population": 0,
                "area_sq_km": 0,
            })

    return sorted(result, key=lambda x: x["name"])


def gadm_feature_for_id(country_code: str, level: int,
                        gid: str) -> Optional[Dict[str, Any]]:
    """
    Return the GeoJSON feature for a specific GID string.

    Useful for extracting a single subdivision's geometry.
    """
    geojson = load_gadm(country_code, level, auto_download=False)
    if not geojson:
        return None

    gid_key = f"GID_{level}"
    for feat in geojson.get("features", []):
        if feat.get("properties", {}).get(gid_key) == gid:
            return feat
    return None
