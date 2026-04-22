#!/usr/bin/env python3
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import json
import logging

logging.basicConfig(level=logging.INFO, format='%(asctime)s %(levelname)s %(name)s: %(message)s')
logger = logging.getLogger(__name__)


def fetch_and_save():
    from utils.nid_data import fetch_wisconsin_dam_inventory

    logger.info("Fetching Wisconsin dam inventory...")
    result = fetch_wisconsin_dam_inventory()

    if 'error' in result:
        logger.error(f"Fetch failed: {result['error']}")
        return False

    county_data = result.get('county_data', {})
    logger.info(f"Source: {result.get('api_source', 'unknown')}")
    logger.info(f"Fetched data for {len(county_data)} counties, {result.get('total_dams_fetched', 0)} total active dams")

    output = {
        'metadata': {
            'description': 'County-level dam counts and hazard classifications for Wisconsin',
            'version': '2.0.0',
            'last_updated': result.get('fetch_time', ''),
            'sources': [result.get('api_source', 'Unknown')],
            'notes': 'Real dam data fetched from public API. Hazard classifications follow federal standards. Only active dams (On Landscape) are counted.'
        },
        'statewide_summary': {
            'total_dams': result.get('total_dams_fetched', 0),
            'counties_with_dams': len(county_data),
            'max_county_dam_count': result.get('max_county_dam_count', 25)
        },
        'county_dam_data': {}
    }

    for county_name in sorted(county_data.keys()):
        cd = county_data[county_name]
        output['county_dam_data'][county_name] = {
            'total_dams': cd['total_dams'],
            'high_hazard': cd['high_hazard'],
            'significant_hazard': cd['significant_hazard'],
            'low_hazard': cd['low_hazard'],
            'has_eap': cd['has_eap'],
            'eap_count': cd.get('eap_count', 0),
            'total_storage_acre_ft': cd.get('total_storage_acre_ft', 0),
            'max_dam_height_ft': cd.get('max_dam_height_ft', 0)
        }

    out_path = 'data/dam_inventory/wisconsin_dam_risk_factors.json'
    with open(out_path, 'w') as f:
        json.dump(output, f, indent=2)

    logger.info(f"Saved updated dam data to {out_path}")

    for county in sorted(list(county_data.keys()))[:5]:
        cd = county_data[county]
        logger.info(f"  {county}: {cd['total_dams']} dams (H:{cd['high_hazard']} S:{cd['significant_hazard']} L:{cd['low_hazard']}) EAP:{cd['has_eap']}")

    return True


def cache_to_db():
    logger.info("Caching NID data to PostgreSQL via scheduler refresh function...")
    from utils.data_source_refresher import refresh_all_nid_dam_inventory
    result = refresh_all_nid_dam_inventory()
    logger.info(f"Cache result: {result.get('success', 0)} success, {result.get('failed', 0)} failed")
    return result


if __name__ == '__main__':
    if len(sys.argv) > 1 and sys.argv[1] == '--cache':
        cache_to_db()
    else:
        success = fetch_and_save()
        if not success:
            sys.exit(1)
