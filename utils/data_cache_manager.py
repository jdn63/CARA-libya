"""
Data Cache Manager - Centralized pre-cached data architecture

This module implements a database-backed caching layer that:
1. Stores all external API data in PostgreSQL
2. Refreshes data at appropriate cadences (annual, weekly, daily)
3. Provides fast read access without hitting external APIs
4. Tracks data freshness for user visibility

Refresh Cadences (per user specification):
- Annual: CDC SVI, FEMA NRI
- Weekly: DHS Health Metrics, NWS Forecasts
- Daily: EPA Air Quality
"""

import logging
import time
from datetime import datetime, timedelta
from typing import Dict, Any, Optional, List, Tuple
from functools import wraps

from flask import current_app, has_app_context

logger = logging.getLogger(__name__)

SOURCE_TYPES = {
    'cdc_svi': {
        'name': 'CDC Social Vulnerability Index',
        'refresh_cadence': 'annual',
        'expiry_days': 365,
        'description': 'Social vulnerability data for disaster preparedness'
    },
    'fema_nri': {
        'name': 'FEMA National Risk Index',
        'refresh_cadence': 'annual',
        'expiry_days': 365,
        'description': 'Natural hazard risk indices'
    },
    'dhs_health': {
        'name': 'DHS Health Metrics',
        'refresh_cadence': 'weekly',
        'expiry_days': 7,
        'description': 'Health surveillance data from Wisconsin DHS'
    },
    'nws_forecast': {
        'name': 'NWS Weather Forecasts',
        'refresh_cadence': 'weekly',
        'expiry_days': 7,
        'description': 'Weather forecasts and alerts'
    },
    'epa_air_quality': {
        'name': 'EPA Air Quality',
        'refresh_cadence': 'daily',
        'expiry_days': 1,
        'description': 'Air quality index data from EPA AirNow'
    },
    'openfema_disaster_declarations': {
        'name': 'FEMA Disaster Declarations',
        'refresh_cadence': 'weekly',
        'expiry_days': 30,
        'description': 'Federal disaster declarations per county from OpenFEMA'
    },
    'openfema_nfip_claims': {
        'name': 'NFIP Flood Claims',
        'refresh_cadence': 'weekly',
        'expiry_days': 30,
        'description': 'NFIP flood insurance claims per county from OpenFEMA'
    },
    'openfema_hma_projects': {
        'name': 'Hazard Mitigation Projects',
        'refresh_cadence': 'weekly',
        'expiry_days': 30,
        'description': 'Hazard mitigation assistance projects per county from OpenFEMA'
    },
    'noaa_storm_events': {
        'name': 'NOAA Storm Events',
        'refresh_cadence': 'weekly',
        'expiry_days': 7,
        'description': 'Historical severe weather events per county from NCEI Storm Events Database'
    },
    'nid_dam_inventory': {
        'name': 'NID Dam Inventory',
        'refresh_cadence': 'weekly',
        'expiry_days': 30,
        'description': 'Dam counts, hazard classifications, and EAP status per county from USACE National Inventory of Dams'
    },
    'dhs_vbd_surveillance': {
        'name': 'DHS EPHT VBD Surveillance',
        'refresh_cadence': 'weekly',
        'expiry_days': 7,
        'description': 'Vector-borne disease surveillance data (Lyme, WNV) from WI DHS EPHT and Vectorborne Disease Program'
    }
}

REFRESH_INTERVALS = {
    'annual': timedelta(days=365),
    'weekly': timedelta(days=7),
    'daily': timedelta(days=1)
}


def get_db_session():
    """Get database session with proper app context handling."""
    if not has_app_context():
        return None
    try:
        from core import db
        return db.session
    except Exception as e:
        logger.error(f"Failed to get database session: {e}")
        return None


def get_cached_data(
    source_type: str,
    jurisdiction_id: Optional[str] = None,
    county_name: Optional[str] = None
) -> Optional[Dict[str, Any]]:
    """
    Retrieve cached data for a specific source and jurisdiction.
    
    This is the primary read function - risk calculators should call this
    instead of making external API calls.
    
    Args:
        source_type: Type of data source (e.g., 'cdc_svi', 'epa_air_quality')
        jurisdiction_id: Optional jurisdiction ID
        county_name: Optional county name
        
    Returns:
        Cached data dict with freshness metadata, or None if not found
    """
    session = get_db_session()
    if not session:
        return None
    
    try:
        from models import DataSourceCache
        
        query = session.query(DataSourceCache).filter(
            DataSourceCache.source_type == source_type,
            DataSourceCache.is_valid == True
        )
        
        if jurisdiction_id:
            query = query.filter(DataSourceCache.jurisdiction_id == jurisdiction_id)
        elif county_name:
            query = query.filter(DataSourceCache.county_name == county_name.lower())
        
        cache_entry = query.order_by(DataSourceCache.fetched_at.desc()).first()
        
        if not cache_entry:
            logger.debug(f"No cache entry for {source_type} - {jurisdiction_id or county_name}")
            return None
        
        return {
            'data': cache_entry.data,
            'fetched_at': cache_entry.fetched_at,
            'is_fresh': cache_entry.is_fresh,
            'freshness_status': cache_entry.freshness_status,
            'age_hours': cache_entry.age_hours,
            'used_fallback': cache_entry.used_fallback,
            'fallback_reason': cache_entry.fallback_reason
        }
        
    except Exception as e:
        logger.error(f"Error retrieving cached data: {e}")
        return None


def save_cached_data(
    source_type: str,
    data: Dict[str, Any],
    jurisdiction_id: Optional[str] = None,
    county_name: Optional[str] = None,
    fetch_duration: Optional[float] = None,
    api_source: Optional[str] = None,
    used_fallback: bool = False,
    fallback_reason: Optional[str] = None
) -> bool:
    """
    Save data to the cache.
    
    Called by scheduled refresh jobs after fetching from external APIs.
    
    Args:
        source_type: Type of data source
        data: The data to cache
        jurisdiction_id: Optional jurisdiction ID
        county_name: Optional county name
        fetch_duration: How long the API call took
        api_source: URL/endpoint of the API
        used_fallback: Whether fallback data was used
        fallback_reason: Why fallback was used
        
    Returns:
        True if saved successfully
    """
    session = get_db_session()
    if not session:
        return False
    
    try:
        from models import DataSourceCache, DataQualityEvent
        
        source_config = SOURCE_TYPES.get(source_type, {})
        expiry_days = source_config.get('expiry_days', 7)
        
        query = session.query(DataSourceCache).filter(
            DataSourceCache.source_type == source_type
        )
        if jurisdiction_id:
            query = query.filter(DataSourceCache.jurisdiction_id == jurisdiction_id)
        elif county_name:
            query = query.filter(DataSourceCache.county_name == county_name.lower())
        
        existing = query.first()
        
        now = datetime.utcnow()
        expires_at = now + timedelta(days=expiry_days)
        
        if existing:
            existing.data = data
            existing.fetched_at = now
            existing.expires_at = expires_at
            existing.is_valid = True
            existing.fetch_duration_seconds = fetch_duration
            existing.api_source = api_source
            existing.used_fallback = used_fallback
            existing.fallback_reason = fallback_reason
        else:
            cache_entry = DataSourceCache(
                source_type=source_type,
                jurisdiction_id=jurisdiction_id,
                county_name=county_name.lower() if county_name else None,
                data=data,
                fetched_at=now,
                expires_at=expires_at,
                is_valid=True,
                fetch_duration_seconds=fetch_duration,
                api_source=api_source,
                used_fallback=used_fallback,
                fallback_reason=fallback_reason
            )
            session.add(cache_entry)
        
        if used_fallback:
            event = DataQualityEvent(
                event_type='fallback_used',
                source_type=source_type,
                jurisdiction_id=jurisdiction_id,
                county_name=county_name,
                severity='warning',
                message=fallback_reason or 'Fallback data used',
                details={'api_source': api_source}
            )
            session.add(event)
        
        session.commit()
        
        status = 'fallback' if used_fallback else 'fresh'
        logger.info(f"Cached {source_type} data for {jurisdiction_id or county_name} ({status})")
        return True
        
    except Exception as e:
        logger.error(f"Error saving cached data: {e}")
        if session:
            session.rollback()
        return False


def get_data_freshness_summary() -> Dict[str, Any]:
    """
    Get a summary of data freshness across all sources.
    
    Used for dashboard display and admin monitoring.
    
    Returns:
        Dict with freshness info per source type
    """
    session = get_db_session()
    if not session:
        return {'error': 'No database session'}
    
    try:
        from models import DataSourceCache
        from sqlalchemy import func
        
        summary = {}
        
        for source_type, config in SOURCE_TYPES.items():
            entries = session.query(DataSourceCache).filter(
                DataSourceCache.source_type == source_type,
                DataSourceCache.is_valid == True
            ).all()
            
            if not entries:
                summary[source_type] = {
                    'name': config['name'],
                    'status': 'no_data',
                    'count': 0,
                    'refresh_cadence': config['refresh_cadence']
                }
                continue
            
            oldest = min(e.fetched_at for e in entries)
            newest = max(e.fetched_at for e in entries)
            fresh_count = sum(1 for e in entries if e.is_fresh)
            fallback_count = sum(1 for e in entries if e.used_fallback)
            
            status = 'fresh'
            if fallback_count > 0:
                status = 'partial_fallback'
            if fresh_count < len(entries):
                status = 'stale'
            if fresh_count == 0:
                status = 'expired'
            
            summary[source_type] = {
                'name': config['name'],
                'status': status,
                'count': len(entries),
                'fresh_count': fresh_count,
                'fallback_count': fallback_count,
                'oldest_fetch': oldest.isoformat() if oldest else None,
                'newest_fetch': newest.isoformat() if newest else None,
                'refresh_cadence': config['refresh_cadence']
            }
        
        return summary
        
    except Exception as e:
        logger.error(f"Error getting freshness summary: {e}")
        return {'error': str(e)}


def refresh_source_for_all_jurisdictions(
    source_type: str,
    fetch_function: callable,
    jurisdictions: List[Dict[str, Any]]
) -> Dict[str, Any]:
    """
    Refresh a data source for all jurisdictions.
    
    Args:
        source_type: Type of data source to refresh
        fetch_function: Function that takes county_name and returns data
        jurisdictions: List of jurisdiction dicts with 'id' and 'county'
        
    Returns:
        Summary of refresh results
    """
    results = {
        'source_type': source_type,
        'total': len(jurisdictions),
        'success': 0,
        'failed': 0,
        'fallback': 0,
        'errors': []
    }
    
    for jurisdiction in jurisdictions:
        jid = jurisdiction.get('id')
        county = jurisdiction.get('county')
        
        try:
            start_time = time.time()
            data = fetch_function(county)
            duration = time.time() - start_time
            
            used_fallback = False
            fallback_reason = None
            
            if data.get('_fallback'):
                used_fallback = True
                fallback_reason = data.get('_fallback_reason', 'API unavailable')
                results['fallback'] += 1
            
            success = save_cached_data(
                source_type=source_type,
                data=data,
                jurisdiction_id=str(jid),
                county_name=county,
                fetch_duration=duration,
                used_fallback=used_fallback,
                fallback_reason=fallback_reason
            )
            
            if success:
                results['success'] += 1
            else:
                results['failed'] += 1
                
        except Exception as e:
            results['failed'] += 1
            results['errors'].append({
                'jurisdiction': jid,
                'county': county,
                'error': str(e)
            })
            logger.error(f"Error refreshing {source_type} for {county}: {e}")
    
    logger.info(f"Refreshed {source_type}: {results['success']}/{results['total']} successful, "
                f"{results['fallback']} used fallback, {results['failed']} failed")
    
    return results


def get_recent_data_quality_events(
    limit: int = 50,
    severity: Optional[str] = None,
    source_type: Optional[str] = None
) -> List[Dict[str, Any]]:
    """
    Get recent data quality events for monitoring.
    
    Args:
        limit: Maximum number of events to return
        severity: Filter by severity level
        source_type: Filter by source type
        
    Returns:
        List of event dicts
    """
    session = get_db_session()
    if not session:
        return []
    
    try:
        from models import DataQualityEvent
        
        query = session.query(DataQualityEvent).order_by(
            DataQualityEvent.occurred_at.desc()
        )
        
        if severity:
            query = query.filter(DataQualityEvent.severity == severity)
        if source_type:
            query = query.filter(DataQualityEvent.source_type == source_type)
        
        events = query.limit(limit).all()
        
        return [
            {
                'id': e.id,
                'event_type': e.event_type,
                'source_type': e.source_type,
                'jurisdiction_id': e.jurisdiction_id,
                'county_name': e.county_name,
                'severity': e.severity,
                'message': e.message,
                'occurred_at': e.occurred_at.isoformat() if e.occurred_at else None,
                'is_resolved': e.is_resolved
            }
            for e in events
        ]
        
    except Exception as e:
        logger.error(f"Error getting data quality events: {e}")
        return []


def get_svi_from_cache(county_name: str) -> Optional[Dict[str, Any]]:
    """
    Get SVI data from cache with freshness metadata.
    Falls back to live fetch if cache miss.
    """
    cached = get_cached_data('cdc_svi', county_name=county_name)
    if cached and cached.get('is_fresh'):
        data = cached['data']
        data['_from_cache'] = True
        data['_cache_age_hours'] = cached.get('age_hours')
        data['_freshness_status'] = cached.get('freshness_status')
        return data
    return None


def get_air_quality_from_cache(county_name: str) -> Optional[Dict[str, Any]]:
    """
    Get air quality data from cache with freshness metadata.
    Falls back to live fetch if cache miss.
    """
    cached = get_cached_data('epa_air_quality', county_name=county_name)
    if cached and cached.get('is_fresh'):
        data = cached['data']
        data['_from_cache'] = True
        data['_cache_age_hours'] = cached.get('age_hours')
        data['_freshness_status'] = cached.get('freshness_status')
        return data
    return None


def get_dhs_health_from_cache(county_name: str) -> Optional[Dict[str, Any]]:
    """
    Get DHS health metrics from cache with freshness metadata.
    Falls back to live fetch if cache miss.
    """
    cached = get_cached_data('dhs_health', county_name=county_name)
    if cached and cached.get('is_fresh'):
        data = cached['data']
        data['_from_cache'] = True
        data['_cache_age_hours'] = cached.get('age_hours')
        data['_freshness_status'] = cached.get('freshness_status')
        return data
    return None


def get_weather_from_cache(county_name: str) -> Optional[Dict[str, Any]]:
    """
    Get weather forecast data from cache with freshness metadata.
    Falls back to live fetch if cache miss.
    """
    cached = get_cached_data('nws_forecast', county_name=county_name)
    if cached and cached.get('is_fresh'):
        data = cached['data']
        data['_from_cache'] = True
        data['_cache_age_hours'] = cached.get('age_hours')
        data['_freshness_status'] = cached.get('freshness_status')
        return data
    return None
