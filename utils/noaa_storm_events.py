"""
NOAA Storm Events Database Integration

Downloads and parses bulk CSV data from NCEI Storm Events Database
for Wisconsin counties, providing real historical event counts by type:
- Winter storms, blizzards, ice storms, extreme cold
- Thunderstorm wind, lightning, hail
- Tornadoes
- Floods, flash floods
- Heavy rain, heavy snow

Data source: https://www.ncei.noaa.gov/pub/data/swdi/stormevents/csvfiles/
Updated monthly with ~120-day lag. Refreshed weekly by scheduler.

County-level fields include: event count, property damage, crop damage,
injuries (direct/indirect), fatalities (direct/indirect).
"""

import gzip
import io
import logging
import os
import time
import requests
import csv
from datetime import datetime
from typing import Dict, Any, List, Optional

logger = logging.getLogger(__name__)

STORM_EVENTS_BASE_URL = "https://www.ncei.noaa.gov/pub/data/swdi/stormevents/csvfiles/"
STORM_EVENTS_CACHE_DIR = "data/noaa_storm_events"
REQUEST_TIMEOUT = 60

WINTER_EVENT_TYPES = {
    "Winter Storm", "Winter Weather", "Blizzard", "Ice Storm",
    "Heavy Snow", "Lake-Effect Snow", "Extreme Cold/Wind Chill",
    "Cold/Wind Chill", "Frost/Freeze", "Sleet"
}

THUNDERSTORM_EVENT_TYPES = {
    "Thunderstorm Wind", "Lightning", "Hail", "Strong Wind",
    "High Wind", "Funnel Cloud"
}

TORNADO_EVENT_TYPES = {"Tornado"}

FLOOD_EVENT_TYPES = {
    "Flood", "Flash Flood", "Coastal Flood", "Lakeshore Flood",
    "Heavy Rain"
}

HAZARD_CATEGORIES = {
    "winter": WINTER_EVENT_TYPES,
    "thunderstorm": THUNDERSTORM_EVENT_TYPES,
    "tornado": TORNADO_EVENT_TYPES,
    "flood": FLOOD_EVENT_TYPES
}

YEARS_TO_FETCH = 20


def _parse_damage_value(value: str) -> float:
    if not value or value.strip() == "":
        return 0.0
    value = value.strip().upper()
    try:
        if value.endswith("K"):
            return float(value[:-1]) * 1_000
        elif value.endswith("M"):
            return float(value[:-1]) * 1_000_000
        elif value.endswith("B"):
            return float(value[:-1]) * 1_000_000_000
        else:
            return float(value)
    except (ValueError, TypeError):
        return 0.0


def _get_year_files_to_download() -> List[int]:
    current_year = datetime.now().year
    return list(range(current_year - YEARS_TO_FETCH, current_year + 1))


def _download_storm_events_file(year: int) -> Optional[List[Dict]]:
    os.makedirs(STORM_EVENTS_CACHE_DIR, exist_ok=True)

    local_path = os.path.join(STORM_EVENTS_CACHE_DIR, f"storm_events_{year}.csv")
    if os.path.exists(local_path):
        mod_time = os.path.getmtime(local_path)
        age_days = (time.time() - mod_time) / 86400
        if age_days < 7:
            logger.debug(f"Using cached storm events file for {year} (age: {age_days:.1f} days)")
            try:
                with open(local_path, 'r', encoding='utf-8', errors='replace') as f:
                    reader = csv.DictReader(f)
                    return [row for row in reader if row.get("STATE", "").upper() == "WISCONSIN"]
            except Exception as e:
                logger.warning(f"Error reading cached file for {year}: {e}")

    listing_url = STORM_EVENTS_BASE_URL
    try:
        resp = requests.get(listing_url, timeout=REQUEST_TIMEOUT)
        if resp.status_code != 200:
            logger.warning(f"Could not list storm events directory: {resp.status_code}")
            return _try_cached_file(local_path)

        import re
        pattern = rf'StormEvents_details-ftp_v1\.0_d{year}_c\d+\.csv\.gz'
        matches = re.findall(pattern, resp.text)
        if not matches:
            logger.info(f"No storm events file found for year {year}")
            return _try_cached_file(local_path)

        filename = sorted(matches)[-1]
        download_url = f"{STORM_EVENTS_BASE_URL}{filename}"

        logger.info(f"Downloading storm events for {year}: {filename}")
        dl_resp = requests.get(download_url, timeout=REQUEST_TIMEOUT * 2, stream=True)
        if dl_resp.status_code != 200:
            logger.warning(f"Failed to download {filename}: {dl_resp.status_code}")
            return _try_cached_file(local_path)

        content = gzip.decompress(dl_resp.content)
        text = content.decode('utf-8', errors='replace')

        reader = csv.DictReader(io.StringIO(text))
        wi_records = [row for row in reader if row.get("STATE", "").upper() == "WISCONSIN"]

        with open(local_path, 'w', encoding='utf-8', newline='') as f:
            if wi_records:
                writer = csv.DictWriter(f, fieldnames=wi_records[0].keys())
                writer.writeheader()
                writer.writerows(wi_records)

        logger.info(f"Saved {len(wi_records)} Wisconsin records for {year}")
        return wi_records

    except Exception as e:
        logger.error(f"Error downloading storm events for {year}: {e}")
        return _try_cached_file(local_path)


def _try_cached_file(local_path: str) -> Optional[List[Dict]]:
    if os.path.exists(local_path):
        try:
            with open(local_path, 'r', encoding='utf-8', errors='replace') as f:
                reader = csv.DictReader(f)
                return [row for row in reader if row.get("STATE", "").upper() == "WISCONSIN"]
        except Exception as e:
            logger.warning(f"Failed to read local storm events file {local_path}: {e}")
    return None


def fetch_all_storm_events_wi() -> Dict[str, Any]:
    """
    Download and aggregate all storm events for Wisconsin counties.
    Returns county-level aggregated data by hazard category.
    """
    start_time = time.time()
    years = _get_year_files_to_download()
    all_records = []

    for year in years:
        records = _download_storm_events_file(year)
        if records:
            all_records.extend(records)

    fetch_duration = time.time() - start_time
    logger.info(f"Loaded {len(all_records)} total Wisconsin storm event records in {fetch_duration:.1f}s")

    county_data = _aggregate_by_county(all_records)

    return {
        "county_data": county_data,
        "total_records": len(all_records),
        "years_covered": f"{min(years)}-{max(years)}",
        "fetch_duration": fetch_duration
    }


def _aggregate_by_county(records: List[Dict]) -> Dict[str, Any]:
    county_data = {}

    for record in records:
        county_raw = (record.get("CZ_NAME") or "").strip().title()
        cz_type = record.get("CZ_TYPE", "C")
        if cz_type != "C":
            continue
        if not county_raw:
            continue

        event_type = record.get("EVENT_TYPE", "Unknown")
        if county_raw not in county_data:
            county_data[county_raw] = _empty_county_record()

        cd = county_data[county_raw]
        cd["total_events"] += 1

        prop_damage = _parse_damage_value(record.get("DAMAGE_PROPERTY", "0"))
        crop_damage = _parse_damage_value(record.get("DAMAGE_CROPS", "0"))
        direct_injuries = int(record.get("INJURIES_DIRECT", 0) or 0)
        indirect_injuries = int(record.get("INJURIES_INDIRECT", 0) or 0)
        direct_deaths = int(record.get("DEATHS_DIRECT", 0) or 0)
        indirect_deaths = int(record.get("DEATHS_INDIRECT", 0) or 0)

        cd["total_property_damage"] += prop_damage
        cd["total_crop_damage"] += crop_damage
        cd["total_injuries"] += direct_injuries + indirect_injuries
        cd["total_fatalities"] += direct_deaths + indirect_deaths

        for category, event_types in HAZARD_CATEGORIES.items():
            if event_type in event_types:
                cat = cd["by_category"][category]
                cat["event_count"] += 1
                cat["property_damage"] += prop_damage
                cat["crop_damage"] += crop_damage
                cat["injuries"] += direct_injuries + indirect_injuries
                cat["fatalities"] += direct_deaths + indirect_deaths

                cat["event_types"][event_type] = cat["event_types"].get(event_type, 0) + 1
                break

        year = record.get("YEAR") or record.get("BEGIN_YEARMONTH", "")[:4]
        if year:
            cd["events_by_year"][str(year)] = cd["events_by_year"].get(str(year), 0) + 1

        if event_type == "Tornado":
            magnitude = record.get("TOR_F_SCALE") or record.get("TOR_E_SCALE") or ""
            if magnitude:
                cd["tornado_magnitudes"].append(magnitude)

    return county_data


def _empty_county_record() -> Dict[str, Any]:
    return {
        "total_events": 0,
        "total_property_damage": 0.0,
        "total_crop_damage": 0.0,
        "total_injuries": 0,
        "total_fatalities": 0,
        "events_by_year": {},
        "tornado_magnitudes": [],
        "by_category": {
            "winter": {"event_count": 0, "property_damage": 0.0, "crop_damage": 0.0,
                       "injuries": 0, "fatalities": 0, "event_types": {}},
            "thunderstorm": {"event_count": 0, "property_damage": 0.0, "crop_damage": 0.0,
                             "injuries": 0, "fatalities": 0, "event_types": {}},
            "tornado": {"event_count": 0, "property_damage": 0.0, "crop_damage": 0.0,
                        "injuries": 0, "fatalities": 0, "event_types": {}},
            "flood": {"event_count": 0, "property_damage": 0.0, "crop_damage": 0.0,
                      "injuries": 0, "fatalities": 0, "event_types": {}}
        }
    }


def get_county_storm_summary(county_name: str) -> Optional[Dict[str, Any]]:
    """
    Get storm events summary for a county from cache.
    Called during dashboard rendering.
    """
    try:
        from utils.data_cache_manager import get_cached_data

        cache = get_cached_data("noaa_storm_events", county_name=county_name)
        if cache and cache.get("data"):
            return cache["data"]
        return None
    except Exception as e:
        logger.error(f"Error getting storm events for {county_name}: {e}")
        return None


def format_damage(amount: float) -> str:
    if amount >= 1_000_000_000:
        return f"${amount / 1_000_000_000:.1f}B"
    elif amount >= 1_000_000:
        return f"${amount / 1_000_000:.1f}M"
    elif amount >= 1_000:
        return f"${amount / 1_000:.0f}K"
    elif amount > 0:
        return f"${amount:.0f}"
    else:
        return "$0"
