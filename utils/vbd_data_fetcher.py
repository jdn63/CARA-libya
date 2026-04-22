import csv
import io
import json
import logging
import os
import time
import requests
from datetime import datetime
from typing import Dict, Any, Optional, List
from collections import defaultdict

logger = logging.getLogger(__name__)

DHS_LYME_COUNTY_CSV_URL = "https://www.dhs.wisconsin.gov/epht/lyme-county.csv"
DHS_LYME_STATE_CSV_URL = "https://www.dhs.wisconsin.gov/epht/lyme-state.csv"
DHS_WNV_COUNTY_CSV_URL = "https://www.dhs.wisconsin.gov/epht/west-nile-data-county.csv"
DHS_WNV_STATE_CSV_URL = "https://www.dhs.wisconsin.gov/epht/west-nile-data-state.csv"

DHS_LYME_DATA_URL = "https://www.dhs.wisconsin.gov/tick/lyme-data.htm"
DHS_WNV_DATA_URL = "https://www.dhs.wisconsin.gov/mosquito/wnv-data.htm"

RECENT_YEARS_WINDOW = 6

_real_data_cache = None


def load_real_vbd_data() -> Dict[str, Any]:
    global _real_data_cache
    if _real_data_cache is not None:
        return _real_data_cache

    try:
        path = 'data/disease/wisconsin_vbd_real_data.json'
        if os.path.exists(path):
            with open(path) as f:
                _real_data_cache = json.load(f)
            logger.info("Loaded real VBD data file with %d counties",
                       len(_real_data_cache.get('county_data', {})))
            return _real_data_cache
    except Exception as e:
        logger.warning(f"Error loading real VBD data: {e}")

    _real_data_cache = {}
    return _real_data_cache


def invalidate_cache():
    global _real_data_cache
    _real_data_cache = None


def get_county_real_data(county_name: str) -> Optional[Dict[str, Any]]:
    real_data = load_real_vbd_data()
    county_data = real_data.get('county_data', {}).get(county_name)

    if county_data:
        return county_data

    cached = _get_cached_county_data(county_name)
    if cached:
        return cached

    return county_data


def _get_cached_county_data(county_name: str) -> Optional[Dict[str, Any]]:
    try:
        from utils.data_cache_manager import get_cached_data
        cache_entry = get_cached_data(
            source_type='dhs_vbd_surveillance',
            county_name=county_name
        )
        if cache_entry and cache_entry.get('data'):
            return cache_entry['data']
    except Exception as e:
        logger.debug(f"No cached VBD data for {county_name}: {e}")
    return None


def get_statewide_summary() -> Dict[str, Any]:
    real_data = load_real_vbd_data()
    summary = real_data.get('statewide_summary', {})

    cached = _get_cached_statewide_data()
    if cached:
        summary.update(cached)

    return summary


def _get_cached_statewide_data() -> Optional[Dict[str, Any]]:
    try:
        from utils.data_cache_manager import get_cached_data
        cache_entry = get_cached_data(
            source_type='dhs_vbd_surveillance',
            county_name='_statewide'
        )
        if cache_entry and cache_entry.get('data'):
            return cache_entry['data']
    except Exception as e:
        logger.debug(f"VBD cache lookup failed: {e}")
    return None


def classify_lyme_rate(rate: float) -> str:
    if rate >= 100:
        return 'very_high'
    elif rate >= 50:
        return 'high'
    elif rate >= 20:
        return 'moderate'
    elif rate >= 5:
        return 'low'
    else:
        return 'minimal'


def classify_wnv_rate(rate: float, total_5yr: int = 0) -> str:
    if rate >= 5 or total_5yr >= 3:
        return 'high'
    elif rate >= 2.5:
        return 'moderate'
    elif rate >= 0.5:
        return 'low'
    else:
        return 'minimal'


def rate_to_score(rate: float, disease: str = 'lyme') -> float:
    if disease == 'lyme':
        if rate >= 200:
            return 0.95
        elif rate >= 100:
            return 0.75 + (rate - 100) * 0.002
        elif rate >= 50:
            return 0.55 + (rate - 50) * 0.004
        elif rate >= 20:
            return 0.35 + (rate - 20) * 0.0067
        elif rate >= 5:
            return 0.15 + (rate - 5) * 0.0133
        else:
            return max(0.05, rate * 0.03)
    else:
        if rate >= 10:
            return 0.90
        elif rate >= 5:
            return 0.60 + (rate - 5) * 0.06
        elif rate >= 2.5:
            return 0.40 + (rate - 2.5) * 0.08
        elif rate >= 0.5:
            return 0.15 + (rate - 0.5) * 0.125
        else:
            return max(0.05, rate * 0.30)


def _fetch_csv(url: str, timeout: int = 30) -> Optional[List[Dict[str, str]]]:
    try:
        headers = {
            'User-Agent': 'Mozilla/5.0 (compatible; CARA/1.0; Wisconsin Public Health Assessment)',
            'Accept': 'text/csv, application/csv, */*'
        }
        response = requests.get(url, headers=headers, timeout=timeout)
        response.raise_for_status()

        content_type = response.headers.get('content-type', '')
        if 'csv' not in content_type and 'text' not in content_type:
            logger.warning(f"Unexpected content-type from {url}: {content_type}")

        text = response.text
        if len(text) < 100:
            logger.warning(f"CSV response too short from {url}: {len(text)} bytes")
            return None

        reader = csv.DictReader(io.StringIO(text))
        rows = list(reader)

        if not rows:
            logger.warning(f"No rows parsed from CSV at {url}")
            return None

        logger.info(f"Fetched {len(rows)} rows from {url}")
        return rows

    except requests.RequestException as e:
        logger.error(f"HTTP error fetching CSV from {url}: {e}")
        return None
    except csv.Error as e:
        logger.error(f"CSV parsing error from {url}: {e}")
        return None
    except Exception as e:
        logger.error(f"Unexpected error fetching CSV from {url}: {e}")
        return None


def _parse_lyme_county_csv(rows: List[Dict[str, str]]) -> Dict[str, Dict[str, Any]]:
    county_data = {}

    count_rows = [r for r in rows if r.get('Sub-topic') == 'Counts']
    rate_rows = [r for r in rows if r.get('Sub-topic') == 'Crude Rates per 100,000']

    all_years = set()
    for r in count_rows:
        try:
            yr = int(r['Year'])
            all_years.add(yr)
        except (ValueError, KeyError):
            pass

    if not all_years:
        logger.warning("No valid years found in Lyme county CSV")
        return county_data

    max_year = max(all_years)
    min_recent_year = max_year - RECENT_YEARS_WINDOW + 1
    recent_years = [y for y in all_years if y >= min_recent_year]

    county_counts = defaultdict(lambda: defaultdict(dict))
    for r in count_rows:
        try:
            county = r['County']
            year = int(r['Year'])
            confirmed = int(r['Number Confirmed']) if r.get('Number Confirmed') else 0
            probable = int(r['Number Probable']) if r.get('Number Probable') else 0
            total = int(r['Number Total']) if r.get('Number Total') else confirmed + probable
            county_counts[county][year] = {
                'confirmed': confirmed,
                'probable': probable,
                'total': total,
            }
        except (ValueError, KeyError):
            continue

    county_rates = defaultdict(dict)
    for r in rate_rows:
        try:
            county = r['County']
            year = int(r['Year'])
            rate = float(r['Crude Rate']) if r.get('Crude Rate') else None
            if rate is not None:
                county_rates[county][year] = rate
        except (ValueError, KeyError):
            continue

    for county in county_counts:
        recent_count_data = {y: d for y, d in county_counts[county].items() if y in recent_years}
        if not recent_count_data:
            continue

        recent_totals = [d['total'] for d in recent_count_data.values()]
        recent_confirmed = [d['confirmed'] for d in recent_count_data.values()]
        avg_annual_cases = round(sum(recent_totals) / len(recent_totals), 1)
        avg_annual_confirmed = round(sum(recent_confirmed) / len(recent_confirmed), 1)

        recent_rate_data = {y: r for y, r in county_rates.get(county, {}).items() if y in recent_years}
        if recent_rate_data:
            avg_rate = round(sum(recent_rate_data.values()) / len(recent_rate_data), 1)
        else:
            avg_rate = None

        latest_year_total = county_counts[county].get(max_year, {}).get('total')
        latest_year_rate = county_rates.get(county, {}).get(max_year)

        year_by_year = {}
        for y in sorted(recent_count_data.keys()):
            entry = {'total': recent_count_data[y]['total']}
            if y in county_rates.get(county, {}):
                entry['rate'] = county_rates[county][y]
            year_by_year[str(y)] = entry

        county_data[county] = {
            'lyme_avg_annual_rate': avg_rate,
            'lyme_avg_annual_cases': avg_annual_cases,
            'lyme_avg_annual_confirmed': avg_annual_confirmed,
            'lyme_latest_year': max_year,
            'lyme_latest_cases': latest_year_total,
            'lyme_latest_rate': latest_year_rate,
            'lyme_data_years': sorted(recent_count_data.keys()),
            'lyme_year_by_year': year_by_year,
        }

    logger.info(f"Parsed Lyme data for {len(county_data)} counties, years {min_recent_year}-{max_year}")
    return county_data


def _parse_wnv_county_csv(rows: List[Dict[str, str]]) -> Dict[str, Dict[str, Any]]:
    county_data = {}

    single_year_all = [
        r for r in rows
        if r.get('range') == 'Single Year'
        and r.get('disease') == 'All'
        and r.get('SUB_TOPIC') == 'Counts'
        and r.get('COUNTY', '') != 'All'
    ]

    all_years = set()
    for r in single_year_all:
        try:
            yr = int(r['Year'])
            all_years.add(yr)
        except (ValueError, KeyError):
            pass

    if not all_years:
        logger.warning("No valid years found in WNV county CSV")
        return county_data

    max_year = max(all_years)
    min_recent_year = max_year - RECENT_YEARS_WINDOW + 1
    recent_years = [y for y in all_years if y >= min_recent_year]

    five_yr_min = max_year - 4
    five_yr_range = [y for y in all_years if y >= five_yr_min]

    county_yearly = defaultdict(lambda: defaultdict(int))
    for r in single_year_all:
        try:
            county = r['COUNTY']
            year = int(r['Year'])
            total = int(r['COUNT_TOTAL']) if r.get('COUNT_TOTAL') else 0
            county_yearly[county][year] = total
        except (ValueError, KeyError):
            continue

    rate_rows = [
        r for r in rows
        if r.get('range') == 'Single Year'
        and r.get('disease') == 'All'
        and r.get('SUB_TOPIC') == 'Crude Rates per 100,000'
        and r.get('COUNTY', '') != 'All'
    ]
    county_rates = defaultdict(dict)
    for r in rate_rows:
        try:
            county = r['COUNTY']
            year = int(r['Year'])
            rate = float(r['CRUDERATE']) if r.get('CRUDERATE') else None
            if rate is not None:
                county_rates[county][year] = rate
        except (ValueError, KeyError):
            continue

    for county in county_yearly:
        five_yr_totals = [county_yearly[county].get(y, 0) for y in five_yr_range]
        total_5yr = sum(five_yr_totals)

        recent_totals = [county_yearly[county].get(y, 0) for y in recent_years]
        avg_annual = round(sum(recent_totals) / len(recent_totals), 2) if recent_totals else 0

        recent_rate_vals = [county_rates.get(county, {}).get(y) for y in recent_years]
        recent_rate_vals = [r for r in recent_rate_vals if r is not None]
        avg_rate = round(sum(recent_rate_vals) / len(recent_rate_vals), 1) if recent_rate_vals else 0

        county_data[county] = {
            'wnv_total_cases_5yr': total_5yr,
            'wnv_avg_annual_cases': avg_annual,
            'wnv_avg_annual_rate': avg_rate,
            'wnv_latest_year': max_year,
            'wnv_latest_cases': county_yearly[county].get(max_year, 0),
        }

    logger.info(f"Parsed WNV data for {len(county_data)} counties, years {min_recent_year}-{max_year}")
    return county_data


def _parse_lyme_state_csv(rows: List[Dict[str, str]]) -> Dict[str, Any]:
    statewide = {}

    count_rows = [r for r in rows if r.get('Sub Topic') == 'Counts (All)']
    for r in count_rows:
        try:
            year = int(r.get('Select a year', ''))
            total = int(r.get('Number Total', '') or r.get('Number Confirmed', '') or 0)
            if total > 0:
                statewide[f'cases_{year}'] = total
        except (ValueError, KeyError):
            continue

    if statewide:
        years = sorted([int(k.replace('cases_', '')) for k in statewide if k.startswith('cases_')])
        if years:
            latest = years[-1]
            statewide['latest_year'] = latest
            statewide['latest_cases'] = statewide.get(f'cases_{latest}', 0)
            recent_5 = years[-5:]
            avg = sum(statewide.get(f'cases_{y}', 0) for y in recent_5) / len(recent_5)
            statewide['avg_annual_cases_recent'] = round(avg, 0)

    logger.info(f"Parsed statewide Lyme data: {len(statewide)} entries")
    return statewide


def _parse_wnv_state_csv(rows: List[Dict[str, str]]) -> Dict[str, Any]:
    statewide = {}

    count_rows = [
        r for r in rows
        if r.get('COUNTY', '') == 'All'
        and r.get('range') == 'Single Year'
        and r.get('disease') == 'All'
        and r.get('SUB_TOPIC') == 'Counts'
    ]

    for r in count_rows:
        try:
            year = int(r.get('Year', ''))
            total = int(r.get('COUNT_TOTAL', '') or 0)
            statewide[f'cases_{year}'] = total
        except (ValueError, KeyError):
            continue

    if statewide:
        years = sorted([int(k.replace('cases_', '')) for k in statewide if k.startswith('cases_')])
        if years:
            latest = years[-1]
            statewide['latest_year'] = latest
            statewide['latest_cases'] = statewide.get(f'cases_{latest}', 0)
            recent_5 = years[-5:]
            avg = sum(statewide.get(f'cases_{y}', 0) for y in recent_5) / len(recent_5)
            statewide['avg_annual_cases'] = round(avg, 1)

    logger.info(f"Parsed statewide WNV data: {len(statewide)} entries")
    return statewide


def fetch_dhs_county_data() -> Dict[str, Any]:
    result = {
        'county_data': {},
        'statewide_lyme': {},
        'statewide_wnv': {},
        'fetched_at': datetime.now().isoformat(),
        'success': False,
        'sources': [],
        'errors': []
    }

    lyme_rows = _fetch_csv(DHS_LYME_COUNTY_CSV_URL)
    if lyme_rows:
        lyme_county = _parse_lyme_county_csv(lyme_rows)
        for county, data in lyme_county.items():
            if county not in result['county_data']:
                result['county_data'][county] = {}
            result['county_data'][county].update(data)
        result['sources'].append(DHS_LYME_COUNTY_CSV_URL)
    else:
        result['errors'].append('Failed to fetch Lyme county CSV')

    wnv_rows = _fetch_csv(DHS_WNV_COUNTY_CSV_URL)
    if wnv_rows:
        wnv_county = _parse_wnv_county_csv(wnv_rows)
        for county, data in wnv_county.items():
            if county not in result['county_data']:
                result['county_data'][county] = {}
            result['county_data'][county].update(data)
        result['sources'].append(DHS_WNV_COUNTY_CSV_URL)
    else:
        result['errors'].append('Failed to fetch WNV county CSV')

    lyme_state_rows = _fetch_csv(DHS_LYME_STATE_CSV_URL)
    if lyme_state_rows:
        result['statewide_lyme'] = _parse_lyme_state_csv(lyme_state_rows)
        result['sources'].append(DHS_LYME_STATE_CSV_URL)

    wnv_state_rows = _fetch_csv(DHS_WNV_STATE_CSV_URL)
    if wnv_state_rows:
        result['statewide_wnv'] = _parse_wnv_state_csv(wnv_state_rows)
        result['sources'].append(DHS_WNV_STATE_CSV_URL)

    if result['county_data']:
        result['success'] = True

    return result


def _build_real_data_json(county_data: Dict[str, Dict[str, Any]],
                          statewide_lyme: Dict[str, Any],
                          statewide_wnv: Dict[str, Any]) -> Dict[str, Any]:
    all_lyme_years = set()
    for cd in county_data.values():
        all_lyme_years.update(cd.get('lyme_data_years', []))

    if all_lyme_years:
        data_years = f"{min(all_lyme_years)}-{max(all_lyme_years)}"
    else:
        data_years = "unknown"

    formatted_counties = {}
    for county, data in county_data.items():
        formatted_counties[county] = {
            'lyme_avg_annual_rate': data.get('lyme_avg_annual_rate', 0),
            'lyme_avg_annual_cases': data.get('lyme_avg_annual_cases', 0),
            'lyme_avg_annual_confirmed': data.get('lyme_avg_annual_confirmed', 0),
            'wnv_avg_annual_rate': data.get('wnv_avg_annual_rate', 0),
            'wnv_total_cases_5yr': data.get('wnv_total_cases_5yr', 0),
            'wnv_avg_annual_cases': data.get('wnv_avg_annual_cases', 0),
            'population_2023': None,
        }

    lyme_latest_year = statewide_lyme.get('latest_year')
    lyme_latest_cases = statewide_lyme.get('latest_cases', 0)
    wnv_latest_cases = statewide_wnv.get('latest_cases', 0)
    wnv_avg = statewide_wnv.get('avg_annual_cases', 18)

    return {
        'metadata': {
            'description': 'County-level vector-borne disease case data for Wisconsin from WI DHS EPHT CSV downloads',
            'version': '3.0.0',
            'last_updated': datetime.now().strftime('%Y-%m-%d'),
            'data_years': data_years,
            'sources': {
                'lyme_disease': {
                    'primary': 'Wisconsin DHS Environmental Public Health Tracking Program (EPHT)',
                    'url': DHS_LYME_COUNTY_CSV_URL,
                    'data_system': 'Wisconsin Electronic Disease Surveillance System (WEDSS)',
                    'notes': 'County-level confirmed/probable case counts and crude rates per 100,000. Case definition changed Jan 2022 (lab-based).'
                },
                'west_nile_virus': {
                    'primary': 'Wisconsin DHS Environmental Public Health Tracking Program (EPHT)',
                    'url': DHS_WNV_COUNTY_CSV_URL,
                    'data_system': 'Wisconsin Electronic Disease Surveillance System (WEDSS)',
                    'notes': 'County-level confirmed/probable case counts. Includes neuroinvasive and non-neuroinvasive. 80% of infections asymptomatic.'
                },
                'statewide_totals': {
                    'lyme_latest_year': lyme_latest_year,
                    'lyme_latest_cases': lyme_latest_cases,
                    'wnv_latest_cases': wnv_latest_cases,
                    'wnv_avg_annual': wnv_avg,
                    'source': f'WI DHS EPHT CSV downloads, fetched {datetime.now().strftime("%Y-%m-%d")}'
                }
            },
            'methodology': 'County-level incidence rates from official WI DHS EPHT CSV data downloads. Crude rates per 100,000 population. Multi-year averages computed from the most recent 6 years of available data.'
        },
        'statewide_summary': {
            'lyme': {
                'total_cases_latest': lyme_latest_cases,
                'latest_year': lyme_latest_year,
                'avg_annual_recent': statewide_lyme.get('avg_annual_cases_recent', 0),
                'trend': 'increasing',
                'trend_note': 'Incidence has increased significantly over past 20 years per WI DHS',
                'case_definition_change_2022': True,
            },
            'wnv': {
                'total_cases_latest': wnv_latest_cases,
                'latest_year': statewide_wnv.get('latest_year'),
                'avg_annual': wnv_avg,
                'underreporting_note': '80% of WNV infections are asymptomatic; reported cases represent severe illness'
            }
        },
        'county_data': formatted_counties
    }


def refresh_all_dhs_vbd_surveillance() -> Dict[str, Any]:
    app = None
    try:
        from main import app as flask_app
        app = flask_app
    except ImportError:
        logger.error("Could not import Flask app")
        return {'error': 'No Flask app available', 'success': False}

    with app.app_context():
        from utils.data_cache_manager import save_cached_data

        fetch_result = fetch_dhs_county_data()

        if fetch_result['success']:
            new_json = _build_real_data_json(
                fetch_result['county_data'],
                fetch_result.get('statewide_lyme', {}),
                fetch_result.get('statewide_wnv', {})
            )

            json_path = 'data/disease/wisconsin_vbd_real_data.json'
            try:
                with open(json_path, 'w') as f:
                    json.dump(new_json, f, indent=2)
                logger.info(f"Updated {json_path} with {len(new_json['county_data'])} counties")
            except Exception as e:
                logger.error(f"Failed to write {json_path}: {e}")

            invalidate_cache()

            save_cached_data(
                source_type='dhs_vbd_surveillance',
                data={
                    'county_count': len(fetch_result['county_data']),
                    'sources': fetch_result['sources'],
                    'fetched_at': fetch_result['fetched_at'],
                },
                county_name='_statewide',
                api_source=', '.join(fetch_result['sources']),
                used_fallback=False
            )

            for county, county_data in fetch_result['county_data'].items():
                save_cached_data(
                    source_type='dhs_vbd_surveillance',
                    data=county_data,
                    county_name=county,
                    api_source=', '.join(fetch_result['sources']),
                    used_fallback=False
                )

            logger.info(f"Saved VBD surveillance data for {len(fetch_result['county_data'])} counties to cache")

            try:
                from utils.persistent_cache import clear_cache_by_prefix
                clear_cache_by_prefix('dashboard_full_')
                logger.info("Cleared dashboard cache after VBD data refresh")
            except Exception as e:
                logger.warning(f"Could not clear dashboard cache: {e}")
        else:
            save_cached_data(
                source_type='dhs_vbd_surveillance',
                data={
                    'fetched_at': datetime.now().isoformat(),
                    'note': 'CSV fetch failed, using existing baseline',
                    'errors': fetch_result.get('errors', [])
                },
                county_name='_statewide',
                api_source=DHS_LYME_COUNTY_CSV_URL,
                used_fallback=True,
                fallback_reason='DHS EPHT CSV download failed'
            )

        return {
            'source_type': 'dhs_vbd_surveillance',
            'success': fetch_result['success'],
            'county_count': len(fetch_result.get('county_data', {})),
            'sources': fetch_result.get('sources', []),
            'errors': fetch_result.get('errors', []),
            'fetched_at': fetch_result.get('fetched_at', datetime.now().isoformat())
        }
