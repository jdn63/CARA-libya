import logging
import time
import requests
from datetime import datetime
from typing import Dict, Any, List, Optional

logger = logging.getLogger(__name__)

WI_DNR_DAM_SERVICE = "https://dnrmaps.wi.gov/arcgis2/rest/services/WT_DAM/WT_Dam_WTM_Ext/MapServer/0/query"

NID_FEATURE_SERVER = "https://geospatial.sec.usace.army.mil/dls/rest/services/NID/National_Inventory_of_Dams_Public_Service/FeatureServer/0/query"

MAX_RECORD_COUNT = 2000
REQUEST_TIMEOUT = 30
MAX_RETRIES = 3


def _api_get(url: str, params: Dict[str, str]) -> Optional[Dict]:
    for attempt in range(MAX_RETRIES):
        try:
            response = requests.get(url, params=params, timeout=REQUEST_TIMEOUT)
            if response.status_code == 200:
                data = response.json()
                if 'error' in data:
                    logger.warning(f"API error from {url}: {data['error']}")
                    return None
                return data
            if response.status_code == 503:
                logger.warning(f"API unavailable (503) at {url}, attempt {attempt + 1}/{MAX_RETRIES}")
                time.sleep(5 * (attempt + 1))
                continue
            logger.warning(f"API returned {response.status_code} from {url}")
            return None
        except requests.exceptions.RequestException as e:
            logger.warning(f"API request failed (attempt {attempt + 1}): {e}")
            if attempt < MAX_RETRIES - 1:
                time.sleep(2 ** attempt)
    return None


def fetch_wisconsin_dam_inventory() -> Dict[str, Any]:
    result = _fetch_from_wi_dnr()
    if result and 'error' not in result:
        return result

    logger.info("WI DNR source unavailable, trying USACE NID FeatureServer")
    result = _fetch_from_usace_nid()
    if result and 'error' not in result:
        return result

    return {'error': 'All NID data sources unavailable', 'county_data': {}}


def _fetch_from_wi_dnr() -> Optional[Dict[str, Any]]:
    start_time = time.time()
    all_dams = []
    offset = 0

    while True:
        params = {
            'where': '1=1',
            'outFields': 'COUNTY_NAME,HAZARD_RATING,PHYSICAL_STATUS,MAX_STORAGE_ACFT_AMT,STRUC_HT_FT_AMT,EAP_NR333_YEAR',
            'resultRecordCount': str(MAX_RECORD_COUNT),
            'resultOffset': str(offset),
            'returnGeometry': 'false',
            'f': 'json'
        }

        data = _api_get(WI_DNR_DAM_SERVICE, params)
        if not data or 'features' not in data:
            if offset == 0:
                logger.error("WI DNR Dam Service: No data returned")
                return None
            break

        features = data['features']
        if not features:
            break

        for feat in features:
            attrs = feat.get('attributes', {})
            if attrs.get('PHYSICAL_STATUS') == 'On Landscape':
                all_dams.append(attrs)

        if len(features) < MAX_RECORD_COUNT:
            break
        offset += MAX_RECORD_COUNT

    logger.info(f"WI DNR: Fetched {len(all_dams)} active Wisconsin dams in {time.time() - start_time:.1f}s")

    county_data = _aggregate_wi_dnr(all_dams)
    max_dam_count = max((d['total_dams'] for d in county_data.values()), default=25)

    return {
        'fetch_time': datetime.utcnow().isoformat(),
        'fetch_duration': time.time() - start_time,
        'total_dams_fetched': len(all_dams),
        'counties_with_data': len(county_data),
        'max_county_dam_count': max_dam_count,
        'county_data': county_data,
        'api_source': 'WI DNR Dam Safety Database (ArcGIS FeatureServer)'
    }


def _aggregate_wi_dnr(dams: List[Dict]) -> Dict[str, Dict[str, Any]]:
    from collections import defaultdict

    county_buckets: Dict[str, List[Dict]] = defaultdict(list)

    for dam in dams:
        county = (dam.get('COUNTY_NAME') or '').strip()
        if not county:
            continue
        normalized = county.title()
        if normalized == 'Fond Du Lac':
            normalized = 'Fond du Lac'
        elif normalized == 'St. Croix':
            normalized = 'St. Croix'
        elif normalized == 'La Crosse':
            normalized = 'La Crosse'
        county_buckets[normalized].append(dam)

    result = {}
    for county_name, dams_list in county_buckets.items():
        high = 0
        significant = 0
        low = 0
        undetermined = 0
        eap_count = 0
        total_storage = 0.0
        max_height = 0.0

        for dam in dams_list:
            hazard = (dam.get('HAZARD_RATING') or '').strip()
            if hazard == 'High':
                high += 1
            elif hazard == 'Significant':
                significant += 1
            elif hazard == 'Low':
                low += 1
            else:
                undetermined += 1

            eap_year = dam.get('EAP_NR333_YEAR')
            if eap_year:
                eap_count += 1

            storage = dam.get('MAX_STORAGE_ACFT_AMT') or 0
            if isinstance(storage, (int, float)) and storage > 0:
                total_storage += storage

            height = dam.get('STRUC_HT_FT_AMT') or 0
            if isinstance(height, (int, float)) and height > max_height:
                max_height = height

        result[county_name] = {
            'total_dams': len(dams_list),
            'high_hazard': high,
            'significant_hazard': significant,
            'low_hazard': low,
            'undetermined_hazard': undetermined,
            'has_eap': eap_count > 0,
            'eap_count': eap_count,
            'total_storage_acre_ft': round(total_storage, 1),
            'max_dam_height_ft': round(max_height, 1),
            'data_source': 'NID'
        }

    return result


def _fetch_from_usace_nid() -> Optional[Dict[str, Any]]:
    start_time = time.time()
    all_dams = []
    offset = 0

    nid_fields = "DAM_NAME,COUNTY,STATE,HAZARD,EAP,DAM_HEIGHT,NID_STORAGE,CONDITION_ASSESSMENT"

    while True:
        params = {
            'where': "STATE='WI'",
            'outFields': nid_fields,
            'f': 'json',
            'resultRecordCount': str(MAX_RECORD_COUNT),
            'resultOffset': str(offset),
            'returnGeometry': 'false'
        }

        data = _api_get(NID_FEATURE_SERVER, params)
        if not data or 'features' not in data:
            if offset == 0:
                logger.error("USACE NID API: No data returned for Wisconsin")
                return None
            break

        features = data['features']
        if not features:
            break

        for feat in features:
            attrs = feat.get('attributes', {})
            all_dams.append(attrs)

        if len(features) < MAX_RECORD_COUNT:
            break
        offset += MAX_RECORD_COUNT

    logger.info(f"USACE NID: Fetched {len(all_dams)} Wisconsin dams in {time.time() - start_time:.1f}s")

    county_data = _aggregate_usace_nid(all_dams)
    max_dam_count = max((d['total_dams'] for d in county_data.values()), default=25)

    return {
        'fetch_time': datetime.utcnow().isoformat(),
        'fetch_duration': time.time() - start_time,
        'total_dams_fetched': len(all_dams),
        'counties_with_data': len(county_data),
        'max_county_dam_count': max_dam_count,
        'county_data': county_data,
        'api_source': 'USACE NID ArcGIS FeatureServer'
    }


WI_COUNTY_NAMES = {
    "ADAMS": "Adams", "ASHLAND": "Ashland", "BARRON": "Barron", "BAYFIELD": "Bayfield",
    "BROWN": "Brown", "BUFFALO": "Buffalo", "BURNETT": "Burnett", "CALUMET": "Calumet",
    "CHIPPEWA": "Chippewa", "CLARK": "Clark", "COLUMBIA": "Columbia", "CRAWFORD": "Crawford",
    "DANE": "Dane", "DODGE": "Dodge", "DOOR": "Door", "DOUGLAS": "Douglas",
    "DUNN": "Dunn", "EAU CLAIRE": "Eau Claire", "FLORENCE": "Florence", "FOND DU LAC": "Fond du Lac",
    "FOREST": "Forest", "GRANT": "Grant", "GREEN": "Green", "GREEN LAKE": "Green Lake",
    "IOWA": "Iowa", "IRON": "Iron", "JACKSON": "Jackson", "JEFFERSON": "Jefferson",
    "JUNEAU": "Juneau", "KENOSHA": "Kenosha", "KEWAUNEE": "Kewaunee", "LA CROSSE": "La Crosse",
    "LAFAYETTE": "Lafayette", "LANGLADE": "Langlade", "LINCOLN": "Lincoln", "MANITOWOC": "Manitowoc",
    "MARATHON": "Marathon", "MARINETTE": "Marinette", "MARQUETTE": "Marquette", "MENOMINEE": "Menominee",
    "MILWAUKEE": "Milwaukee", "MONROE": "Monroe", "OCONTO": "Oconto", "ONEIDA": "Oneida",
    "OUTAGAMIE": "Outagamie", "OZAUKEE": "Ozaukee", "PEPIN": "Pepin", "PIERCE": "Pierce",
    "POLK": "Polk", "PORTAGE": "Portage", "PRICE": "Price", "RACINE": "Racine",
    "RICHLAND": "Richland", "ROCK": "Rock", "RUSK": "Rusk", "SAUK": "Sauk",
    "SAWYER": "Sawyer", "SHAWANO": "Shawano", "SHEBOYGAN": "Sheboygan", "ST. CROIX": "St. Croix",
    "TAYLOR": "Taylor", "TREMPEALEAU": "Trempealeau", "VERNON": "Vernon", "VILAS": "Vilas",
    "WALWORTH": "Walworth", "WASHBURN": "Washburn", "WASHINGTON": "Washington", "WAUKESHA": "Waukesha",
    "WAUPACA": "Waupaca", "WAUSHARA": "Waushara", "WINNEBAGO": "Winnebago", "WOOD": "Wood",
    "ST CROIX": "St. Croix", "FOND DU LAC": "Fond du Lac", "GREEN LAKE": "Green Lake",
    "EAU CLAIRE": "Eau Claire", "LA CROSSE": "La Crosse"
}


def _normalize_county_name(raw_county: str) -> Optional[str]:
    if not raw_county:
        return None
    upper = raw_county.strip().upper()
    if upper in WI_COUNTY_NAMES:
        return WI_COUNTY_NAMES[upper]
    cleaned = upper.replace(" COUNTY", "").replace(" CO.", "").replace(" CO", "").strip()
    if cleaned in WI_COUNTY_NAMES:
        return WI_COUNTY_NAMES[cleaned]
    return None


def _aggregate_usace_nid(dams: List[Dict]) -> Dict[str, Dict[str, Any]]:
    from collections import defaultdict

    county_buckets: Dict[str, List[Dict]] = defaultdict(list)

    for dam in dams:
        raw_county = dam.get('COUNTY', '')
        county_name = _normalize_county_name(raw_county)
        if not county_name:
            continue
        county_buckets[county_name].append(dam)

    result = {}
    for county_name, dams_list in county_buckets.items():
        high = 0
        significant = 0
        low = 0
        undetermined = 0
        eap_count = 0
        total_storage = 0.0
        max_height = 0.0

        for dam in dams_list:
            hazard = (dam.get('HAZARD') or '').upper().strip()
            if hazard in ('H', 'HIGH'):
                high += 1
            elif hazard in ('S', 'SIGNIFICANT'):
                significant += 1
            elif hazard in ('L', 'LOW'):
                low += 1
            else:
                undetermined += 1

            eap = (dam.get('EAP') or '').upper().strip()
            if eap in ('Y', 'YES'):
                eap_count += 1

            storage = dam.get('NID_STORAGE') or 0
            if isinstance(storage, (int, float)) and storage > 0:
                total_storage += storage

            height = dam.get('DAM_HEIGHT') or 0
            if isinstance(height, (int, float)) and height > max_height:
                max_height = height

        result[county_name] = {
            'total_dams': len(dams_list),
            'high_hazard': high,
            'significant_hazard': significant,
            'low_hazard': low,
            'undetermined_hazard': undetermined,
            'has_eap': eap_count > 0,
            'eap_count': eap_count,
            'total_storage_acre_ft': round(total_storage, 1),
            'max_dam_height_ft': round(max_height, 1),
            'data_source': 'NID'
        }

    return result
