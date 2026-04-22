"""
Data Source Refresher - Scheduled jobs to refresh external data at appropriate cadences

This module contains functions called by the scheduler to refresh:
- Annual: CDC SVI, FEMA NRI  
- Weekly: DHS Health Metrics, NWS Forecasts, OpenFEMA data, NOAA Storm Events
- Daily: EPA Air Quality

Each refresh function fetches data from external APIs and stores it in the database cache.
User requests read from this cache only - never hitting external APIs directly.

IMPORTANT: All refresh functions must run within Flask app context for database access.
"""

import logging
import time
from datetime import datetime
from typing import Dict, Any, List, Optional

logger = logging.getLogger(__name__)


def _get_app():
    """Get Flask app instance for creating app context in background threads."""
    try:
        from main import app
        return app
    except ImportError:
        logger.error("Could not import Flask app from main")
        return None


def refresh_all_cdc_svi() -> Dict[str, Any]:
    """
    Refresh CDC Social Vulnerability Index data for all Wisconsin counties.
    Called annually by scheduler.

    Uses a single bulk API call to fetch all 72 counties at once from the
    CDC/ATSDR SVI 2022 ArcGIS REST API. Falls back to individual per-county
    fetches only if the bulk call fails.
    """
    app = _get_app()
    if not app:
        return {'error': 'No Flask app available', 'success': 0, 'failed': 0}

    with app.app_context():
        from utils.data_cache_manager import save_cached_data
        from utils.svi_data import fetch_bulk_svi_data, fetch_live_svi_data, WI_COUNTY_FIPS

        results = {
            'source_type': 'cdc_svi',
            'started_at': datetime.utcnow().isoformat(),
            'success': 0,
            'failed': 0,
            'fallback': 0,
            'errors': []
        }

        start_time = time.time()
        bulk_data = fetch_bulk_svi_data()
        bulk_duration = time.time() - start_time

        if bulk_data:
            logger.info(f"Bulk SVI fetch returned {len(bulk_data)} counties in {bulk_duration:.1f}s")
            per_county_duration = bulk_duration / max(len(bulk_data), 1)

            for county_name in WI_COUNTY_FIPS.keys():
                try:
                    data = bulk_data.get(county_name)
                    used_fallback = data is None

                    if used_fallback:
                        data = {
                            "county": county_name.title(),
                            "overall": 0.5, "socioeconomic": 0.5,
                            "household_composition": 0.5, "minority_status": 0.5,
                            "housing_transportation": 0.5,
                            "data_source": "statewide_average",
                            "_fallback": True,
                            "_fallback_reason": "County not in bulk response",
                            "last_updated": datetime.utcnow().isoformat()
                        }

                    success = save_cached_data(
                        source_type='cdc_svi',
                        data=data,
                        county_name=county_name,
                        fetch_duration=per_county_duration,
                        api_source='CDC SVI 2022 ArcGIS (bulk)',
                        used_fallback=used_fallback,
                        fallback_reason=data.get('_fallback_reason') if used_fallback else None
                    )

                    if success:
                        if used_fallback:
                            results['fallback'] += 1
                        else:
                            results['success'] += 1
                    else:
                        results['failed'] += 1

                except Exception as e:
                    results['failed'] += 1
                    results['errors'].append({'county': county_name, 'error': str(e)})
                    logger.error(f"Error saving SVI for {county_name}: {e}")
        else:
            logger.warning("Bulk SVI fetch failed, falling back to individual county fetches")
            for county_name in WI_COUNTY_FIPS.keys():
                try:
                    county_start = time.time()
                    data = fetch_live_svi_data(county_name)
                    duration = time.time() - county_start

                    used_fallback = data.get('_fallback', False) or data.get('data_source') == 'statewide_average'
                    fallback_reason = data.get('_fallback_reason', 'Using statewide average') if used_fallback else None

                    success = save_cached_data(
                        source_type='cdc_svi',
                        data=data,
                        county_name=county_name,
                        fetch_duration=duration,
                        api_source='CDC SVI API',
                        used_fallback=used_fallback,
                        fallback_reason=fallback_reason
                    )

                    if success:
                        if used_fallback:
                            results['fallback'] += 1
                        else:
                            results['success'] += 1
                    else:
                        results['failed'] += 1

                except Exception as e:
                    results['failed'] += 1
                    results['errors'].append({'county': county_name, 'error': str(e)})
                    logger.error(f"Error refreshing SVI for {county_name}: {e}")

        results['finished_at'] = datetime.utcnow().isoformat()
        logger.info(f"CDC SVI refresh complete: {results['success']} success, {results['fallback']} fallback, {results['failed']} failed")

        return results


def refresh_all_epa_air_quality() -> Dict[str, Any]:
    """
    Refresh EPA Air Quality data for all Wisconsin counties.
    Called daily by scheduler.
    
    IMPORTANT: Uses fetch_live_air_quality_data to bypass cache and always hit external sources.
    Wraps in app context for database access from background threads.
    """
    app = _get_app()
    if not app:
        return {'error': 'No Flask app available', 'success': 0, 'failed': 0}
    
    with app.app_context():
        from utils.data_cache_manager import save_cached_data
        from utils.air_quality_data import fetch_live_air_quality_data, WI_COUNTY_COORDINATES
        
        results = {
            'source_type': 'epa_air_quality',
            'started_at': datetime.utcnow().isoformat(),
            'success': 0,
            'failed': 0,
            'fallback': 0,
            'errors': []
        }
        
        logger.info("Starting EPA Air Quality data refresh for all counties (using live fetch)")
        
        for county_name in WI_COUNTY_COORDINATES.keys():
            try:
                start_time = time.time()
                # Use fetch_live_air_quality_data to bypass cache and hit external sources
                data = fetch_live_air_quality_data(county_name)
                duration = time.time() - start_time
                
                used_fallback = data.get('data_source') == 'statewide_baseline' or data.get('_fallback', False)
                fallback_reason = data.get('_fallback_reason', 'Using statewide baseline') if used_fallback else None
                
                success = save_cached_data(
                    source_type='epa_air_quality',
                    data=data,
                    county_name=county_name,
                    fetch_duration=duration,
                    api_source='EPA AirNow API',
                    used_fallback=used_fallback,
                    fallback_reason=fallback_reason
                )
                
                if success:
                    if used_fallback:
                        results['fallback'] += 1
                    else:
                        results['success'] += 1
                else:
                    results['failed'] += 1
                    
            except Exception as e:
                results['failed'] += 1
                results['errors'].append({'county': county_name, 'error': str(e)})
                logger.error(f"Error refreshing air quality for {county_name}: {e}")
        
        results['finished_at'] = datetime.utcnow().isoformat()
        logger.info(f"EPA Air Quality refresh complete: {results['success']} success, {results['fallback']} fallback, {results['failed']} failed")
        
        return results


def refresh_all_dhs_health() -> Dict[str, Any]:
    """
    Refresh DHS Health Metrics for all Wisconsin counties.
    Called weekly by scheduler.
    Wraps in app context for database access from background threads.
    """
    app = _get_app()
    if not app:
        return {'error': 'No Flask app available', 'success': 0, 'failed': 0}
    
    with app.app_context():
        from utils.data_cache_manager import save_cached_data
        from utils.dhs_data import get_dhs_health_metrics
        from utils.svi_data import WI_COUNTY_FIPS
        
        results = {
            'source_type': 'dhs_health',
            'started_at': datetime.utcnow().isoformat(),
            'success': 0,
            'failed': 0,
            'fallback': 0,
            'errors': []
        }
        
        logger.info("Starting DHS Health Metrics refresh for all counties")
        
        for county_name in WI_COUNTY_FIPS.keys():
            try:
                start_time = time.time()
                data = get_dhs_health_metrics(county_name)
                duration = time.time() - start_time
                
                used_fallback = data.get('data_source') == 'statewide_average' or data.get('_fallback', False)
                fallback_reason = 'Using statewide average' if used_fallback else None
                
                success = save_cached_data(
                    source_type='dhs_health',
                    data=data,
                    county_name=county_name,
                    fetch_duration=duration,
                    api_source='Wisconsin DHS API',
                    used_fallback=used_fallback,
                    fallback_reason=fallback_reason
                )
                
                if success:
                    if used_fallback:
                        results['fallback'] += 1
                    else:
                        results['success'] += 1
                else:
                    results['failed'] += 1
                    
            except Exception as e:
                results['failed'] += 1
                results['errors'].append({'county': county_name, 'error': str(e)})
                logger.error(f"Error refreshing DHS health for {county_name}: {e}")
        
        results['finished_at'] = datetime.utcnow().isoformat()
        logger.info(f"DHS Health refresh complete: {results['success']} success, {results['fallback']} fallback, {results['failed']} failed")
        
        return results


def refresh_all_nws_forecasts() -> Dict[str, Any]:
    """
    Refresh NWS Weather Forecast data for all Wisconsin counties.
    Called weekly by scheduler.
    Wraps in app context for database access from background threads.
    """
    app = _get_app()
    if not app:
        return {'error': 'No Flask app available', 'success': 0, 'failed': 0}
    
    with app.app_context():
        from utils.data_cache_manager import save_cached_data
        from utils.weather_alerts import get_weather_alerts
        from utils.svi_data import WI_COUNTY_FIPS
        
        results = {
            'source_type': 'nws_forecast',
            'started_at': datetime.utcnow().isoformat(),
            'success': 0,
            'failed': 0,
            'fallback': 0,
            'errors': []
        }
        
        logger.info("Starting NWS Forecast refresh for all counties")
        
        for county_name in WI_COUNTY_FIPS.keys():
            try:
                start_time = time.time()
                data = get_weather_alerts(county_name)
                duration = time.time() - start_time
                
                used_fallback = data.get('data_source') == 'fallback' or data.get('_fallback', False)
                fallback_reason = 'Using fallback data' if used_fallback else None
                
                success = save_cached_data(
                    source_type='nws_forecast',
                    data=data,
                    county_name=county_name,
                    fetch_duration=duration,
                    api_source='NWS API',
                    used_fallback=used_fallback,
                    fallback_reason=fallback_reason
                )
                
                if success:
                    if used_fallback:
                        results['fallback'] += 1
                    else:
                        results['success'] += 1
                else:
                    results['failed'] += 1
                    
            except Exception as e:
                results['failed'] += 1
                results['errors'].append({'county': county_name, 'error': str(e)})
                logger.error(f"Error refreshing NWS forecast for {county_name}: {e}")
        
        results['finished_at'] = datetime.utcnow().isoformat()
        logger.info(f"NWS Forecast refresh complete: {results['success']} success, {results['fallback']} fallback, {results['failed']} failed")
        
        return results


def refresh_all_fema_nri() -> Dict[str, Any]:
    """
    Refresh FEMA National Risk Index data for all Wisconsin counties.
    Called annually by scheduler.
    Wraps in app context for database access from background threads.
    """
    app = _get_app()
    if not app:
        return {'error': 'No Flask app available', 'success': 0, 'failed': 0}
    
    with app.app_context():
        from utils.data_cache_manager import save_cached_data
        from utils.svi_data import WI_COUNTY_FIPS
        
        results = {
            'source_type': 'fema_nri',
            'started_at': datetime.utcnow().isoformat(),
            'success': 0,
            'failed': 0,
            'fallback': 0,
            'errors': []
        }
        
        logger.info("Starting FEMA NRI data refresh for all counties")
        
        try:
            from utils.fema_rapt_connector import FEMARAPTConnector
            connector = FEMARAPTConnector()
            facilities_data = connector.get_correctional_facilities()
            
            for county_name in WI_COUNTY_FIPS.keys():
                try:
                    county_key = county_name.title()
                    data = facilities_data.get(county_key, {})
                    
                    if not data:
                        data = {'facilities': [], 'weights': {}}
                    
                    success = save_cached_data(
                        source_type='fema_nri',
                        data=data,
                        county_name=county_name,
                        api_source='FEMA RAPT API',
                        used_fallback=True,
                        fallback_reason='Limited FEMA data available'
                    )
                    
                    if success:
                        results['fallback'] += 1
                    else:
                        results['failed'] += 1
                        
                except Exception as e:
                    results['failed'] += 1
                    results['errors'].append({'county': county_name, 'error': str(e)})
                    
        except Exception as e:
            logger.error(f"Error connecting to FEMA: {e}")
            results['errors'].append({'error': str(e)})
        
        results['finished_at'] = datetime.utcnow().isoformat()
        logger.info(f"FEMA NRI refresh complete: {results['success']} success, {results['fallback']} fallback, {results['failed']} failed")
        
        return results


def refresh_all_openfema_declarations() -> Dict[str, Any]:
    """
    Refresh OpenFEMA Disaster Declarations data for all Wisconsin counties.
    Called weekly by scheduler. No API key required.
    """
    app = _get_app()
    if not app:
        return {'error': 'No Flask app available', 'success': 0, 'failed': 0}
    
    with app.app_context():
        from utils.data_cache_manager import save_cached_data
        from utils.openfema_data import fetch_disaster_declarations_wi
        
        results = {
            'source_type': 'openfema_disaster_declarations',
            'started_at': datetime.utcnow().isoformat(),
            'success': 0,
            'failed': 0,
            'errors': []
        }
        
        logger.info("Starting OpenFEMA disaster declarations refresh")
        
        try:
            data = fetch_disaster_declarations_wi()
            county_data = data.get("county_data", {})
            
            for county_name, county_info in county_data.items():
                try:
                    success = save_cached_data(
                        source_type='openfema_disaster_declarations',
                        data=county_info,
                        county_name=county_name,
                        api_source='OpenFEMA DisasterDeclarationsSummaries v2',
                        fetch_duration=data.get("fetch_duration")
                    )
                    if success:
                        results['success'] += 1
                    else:
                        results['failed'] += 1
                except Exception as e:
                    results['failed'] += 1
                    results['errors'].append({'county': county_name, 'error': str(e)})
                    
        except Exception as e:
            logger.error(f"Error fetching disaster declarations: {e}")
            results['errors'].append({'error': str(e)})
        
        results['finished_at'] = datetime.utcnow().isoformat()
        logger.info(f"OpenFEMA declarations refresh: {results['success']} success, {results['failed']} failed")
        return results


def refresh_all_openfema_nfip() -> Dict[str, Any]:
    """
    Refresh OpenFEMA NFIP Claims data for all Wisconsin counties.
    Called weekly by scheduler. No API key required.
    """
    app = _get_app()
    if not app:
        return {'error': 'No Flask app available', 'success': 0, 'failed': 0}
    
    with app.app_context():
        from utils.data_cache_manager import save_cached_data
        from utils.openfema_data import fetch_nfip_claims_wi
        
        results = {
            'source_type': 'openfema_nfip_claims',
            'started_at': datetime.utcnow().isoformat(),
            'success': 0,
            'failed': 0,
            'errors': []
        }
        
        logger.info("Starting OpenFEMA NFIP claims refresh")
        
        try:
            data = fetch_nfip_claims_wi()
            county_data = data.get("county_data", {})
            
            for county_name, county_info in county_data.items():
                try:
                    success = save_cached_data(
                        source_type='openfema_nfip_claims',
                        data=county_info,
                        county_name=county_name,
                        api_source='OpenFEMA FimaNfipClaims v2',
                        fetch_duration=data.get("fetch_duration")
                    )
                    if success:
                        results['success'] += 1
                    else:
                        results['failed'] += 1
                except Exception as e:
                    results['failed'] += 1
                    results['errors'].append({'county': county_name, 'error': str(e)})
                    
        except Exception as e:
            logger.error(f"Error fetching NFIP claims: {e}")
            results['errors'].append({'error': str(e)})
        
        results['finished_at'] = datetime.utcnow().isoformat()
        logger.info(f"OpenFEMA NFIP refresh: {results['success']} success, {results['failed']} failed")
        return results


def refresh_all_openfema_hma() -> Dict[str, Any]:
    """
    Refresh OpenFEMA Hazard Mitigation Projects data for all Wisconsin counties.
    Called weekly by scheduler. No API key required.
    """
    app = _get_app()
    if not app:
        return {'error': 'No Flask app available', 'success': 0, 'failed': 0}
    
    with app.app_context():
        from utils.data_cache_manager import save_cached_data
        from utils.openfema_data import fetch_hma_projects_wi
        
        results = {
            'source_type': 'openfema_hma_projects',
            'started_at': datetime.utcnow().isoformat(),
            'success': 0,
            'failed': 0,
            'errors': []
        }
        
        logger.info("Starting OpenFEMA HMA projects refresh")
        
        try:
            data = fetch_hma_projects_wi()
            county_data = data.get("county_data", {})
            
            for county_name, county_info in county_data.items():
                try:
                    success = save_cached_data(
                        source_type='openfema_hma_projects',
                        data=county_info,
                        county_name=county_name,
                        api_source='OpenFEMA HazardMitigationAssistanceProjects v4',
                        fetch_duration=data.get("fetch_duration")
                    )
                    if success:
                        results['success'] += 1
                    else:
                        results['failed'] += 1
                except Exception as e:
                    results['failed'] += 1
                    results['errors'].append({'county': county_name, 'error': str(e)})
                    
        except Exception as e:
            logger.error(f"Error fetching HMA projects: {e}")
            results['errors'].append({'error': str(e)})
        
        results['finished_at'] = datetime.utcnow().isoformat()
        logger.info(f"OpenFEMA HMA refresh: {results['success']} success, {results['failed']} failed")
        return results


def refresh_all_noaa_storm_events() -> Dict[str, Any]:
    """
    Refresh NOAA Storm Events data for all Wisconsin counties.
    Downloads bulk CSV from NCEI, filters Wisconsin, aggregates by county.
    Called weekly by scheduler. No API key required.
    """
    app = _get_app()
    if not app:
        return {'error': 'No Flask app available', 'success': 0, 'failed': 0}
    
    with app.app_context():
        from utils.data_cache_manager import save_cached_data
        from utils.noaa_storm_events import fetch_all_storm_events_wi
        
        results = {
            'source_type': 'noaa_storm_events',
            'started_at': datetime.utcnow().isoformat(),
            'success': 0,
            'failed': 0,
            'errors': []
        }
        
        logger.info("Starting NOAA Storm Events refresh")
        
        try:
            data = fetch_all_storm_events_wi()
            county_data = data.get("county_data", {})
            
            years_covered = data.get("years_covered", "")
            for county_name, county_info in county_data.items():
                try:
                    county_info["years_covered"] = years_covered
                    success = save_cached_data(
                        source_type='noaa_storm_events',
                        data=county_info,
                        county_name=county_name,
                        api_source='NOAA NCEI Storm Events Database',
                        fetch_duration=data.get("fetch_duration")
                    )
                    if success:
                        results['success'] += 1
                    else:
                        results['failed'] += 1
                except Exception as e:
                    results['failed'] += 1
                    results['errors'].append({'county': county_name, 'error': str(e)})
                    
        except Exception as e:
            logger.error(f"Error fetching NOAA storm events: {e}")
            results['errors'].append({'error': str(e)})
        
        results['finished_at'] = datetime.utcnow().isoformat()
        logger.info(f"NOAA Storm Events refresh: {results['success']} success, {results['failed']} failed")
        return results


def refresh_all_nid_dam_inventory() -> Dict[str, Any]:
    app = _get_app()
    if not app:
        return {'error': 'No Flask app available', 'success': 0, 'failed': 0}

    with app.app_context():
        from utils.data_cache_manager import save_cached_data
        from utils.nid_data import fetch_wisconsin_dam_inventory

        results = {
            'source_type': 'nid_dam_inventory',
            'started_at': datetime.utcnow().isoformat(),
            'success': 0,
            'failed': 0,
            'errors': []
        }

        logger.info("Starting NID dam inventory refresh for Wisconsin")

        try:
            data = fetch_wisconsin_dam_inventory()

            if 'error' in data:
                logger.warning(f"NID fetch returned error: {data['error']}")
                results['errors'].append({'error': data['error']})
                results['finished_at'] = datetime.utcnow().isoformat()
                return results

            county_data = data.get('county_data', {})
            statewide_meta = {
                'total_dams_fetched': data.get('total_dams_fetched', 0),
                'max_county_dam_count': data.get('max_county_dam_count', 25),
                'fetch_time': data.get('fetch_time'),
                'api_source': data.get('api_source')
            }

            for county_name, county_info in county_data.items():
                try:
                    county_info['statewide_meta'] = statewide_meta
                    success = save_cached_data(
                        source_type='nid_dam_inventory',
                        data=county_info,
                        county_name=county_name,
                        api_source='USACE NID ArcGIS FeatureServer',
                        fetch_duration=data.get('fetch_duration')
                    )
                    if success:
                        results['success'] += 1
                    else:
                        results['failed'] += 1
                except Exception as e:
                    results['failed'] += 1
                    results['errors'].append({'county': county_name, 'error': str(e)})

        except Exception as e:
            logger.error(f"Error fetching NID dam inventory: {e}")
            results['errors'].append({'error': str(e)})

        results['finished_at'] = datetime.utcnow().isoformat()
        logger.info(f"NID dam inventory refresh: {results['success']} success, {results['failed']} failed")
        return results


def run_all_refreshes() -> Dict[str, Any]:
    """
    Run all data source refreshes. Used for initial cache population.
    Each individual refresh function handles its own app context.
    """
    logger.info("Starting full data cache refresh")
    
    results = {
        'started_at': datetime.utcnow().isoformat(),
        'sources': {}
    }
    
    results['sources']['cdc_svi'] = refresh_all_cdc_svi()
    results['sources']['epa_air_quality'] = refresh_all_epa_air_quality()
    results['sources']['dhs_health'] = refresh_all_dhs_health()
    results['sources']['nws_forecast'] = refresh_all_nws_forecasts()
    results['sources']['fema_nri'] = refresh_all_fema_nri()
    results['sources']['openfema_declarations'] = refresh_all_openfema_declarations()
    results['sources']['openfema_nfip'] = refresh_all_openfema_nfip()
    results['sources']['openfema_hma'] = refresh_all_openfema_hma()
    results['sources']['noaa_storm_events'] = refresh_all_noaa_storm_events()
    results['sources']['nid_dam_inventory'] = refresh_all_nid_dam_inventory()
    
    results['finished_at'] = datetime.utcnow().isoformat()
    
    logger.info("Full data cache refresh complete")
    return results
