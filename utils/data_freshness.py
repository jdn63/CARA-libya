import logging
from datetime import datetime

logger = logging.getLogger(__name__)

DOMAIN_SOURCE_MAP = {
    'natural_hazards': {
        'sources': ['FEMA NRI', 'CDC SVI', 'NOAA Storm Events', 'Census ACS'],
        'refresh': 'Annual',
        'cache_types': ['fema_nri', 'cdc_svi'],
    },
    'health_metrics': {
        'sources': ['Wisconsin DHS Surveillance PDFs', 'County Health Rankings'],
        'refresh': 'Weekly',
        'cache_types': ['dhs_health', 'vaccination_data'],
    },
    'active_shooter': {
        'sources': ['Census ACS (local files)', 'CDC SVI', 'NCES SSOCS 2019-2020'],
        'refresh': 'Annual',
        'cache_types': ['cdc_svi'],
    },
    'extreme_heat': {
        'sources': ['NOAA/NWS Forecasts', 'Wisconsin DHS HVI', 'WICCI Climate Projections'],
        'refresh': 'Weekly (forecasts) / Annual (projections)',
        'cache_types': ['nws_forecast'],
    },
    'air_quality': {
        'sources': ['EPA AirNow', 'Wisconsin DNR', 'NOAA Wildfire Smoke'],
        'refresh': 'Daily',
        'cache_types': ['epa_air_quality'],
    },
    'cybersecurity': {
        'sources': ['Modeled from proxy indicators (county characteristics + SVI)'],
        'refresh': 'N/A (static model)',
        'cache_types': [],
    },
    'utilities': {
        'sources': ['Modeled from proxy indicators (county characteristics + SVI)'],
        'refresh': 'N/A (static model)',
        'cache_types': [],
    },
}


def get_data_confidence(risk_data):
    confidence = {}

    nh = risk_data.get('natural_hazards', {})
    has_fema = any(k for k in nh if 'fema' in str(k).lower() or 'nri' in str(k).lower())
    has_svi = any(k for k in nh if 'svi' in str(k).lower())
    if has_fema or has_svi or nh:
        confidence['natural_hazards'] = 'High'
    else:
        confidence['natural_hazards'] = 'Low'

    hm = risk_data.get('health_metrics', {})
    if isinstance(hm, dict):
        metrics = hm.get('metrics', hm)
        if isinstance(metrics, dict) and len([v for v in metrics.values() if v is not None and v != 0]) > 2:
            confidence['health_metrics'] = 'High'
        elif isinstance(metrics, dict) and len([v for v in metrics.values() if v is not None and v != 0]) > 0:
            confidence['health_metrics'] = 'Moderate'
        else:
            confidence['health_metrics'] = 'Low'
    else:
        confidence['health_metrics'] = 'Low'

    as_score = risk_data.get('active_shooter_risk', 0)
    as_details = risk_data.get('active_shooter_details', {})
    if isinstance(as_details, dict) and as_details:
        ds = []
        for v in as_details.values():
            if isinstance(v, dict):
                ds.extend(v.get('data_sources', []))
        if any('Census' in s or 'SVI' in s for s in ds):
            confidence['active_shooter'] = 'Moderate'
        elif any('Estimated' in s for s in ds):
            confidence['active_shooter'] = 'Low'
        else:
            confidence['active_shooter'] = 'Moderate'
    else:
        confidence['active_shooter'] = 'Moderate'

    heat = risk_data.get('extreme_heat_risk', 0)
    heat_comp = risk_data.get('heat_vulnerability', {})
    if isinstance(heat_comp, dict) and heat_comp:
        confidence['extreme_heat'] = 'High'
    elif heat > 0:
        confidence['extreme_heat'] = 'Moderate'
    else:
        confidence['extreme_heat'] = 'Low'

    aq = risk_data.get('air_quality_risk', 0)
    aq_comp = risk_data.get('air_quality_components', {})
    if isinstance(aq_comp, dict) and aq_comp:
        confidence['air_quality'] = 'Moderate'
    elif aq > 0:
        confidence['air_quality'] = 'Low'
    else:
        confidence['air_quality'] = 'Low'

    confidence['cybersecurity'] = 'Low'
    confidence['utilities'] = 'Low'

    return confidence


def get_data_freshness_summary():
    try:
        from models import DataSourceCache
        from core import db

        freshness = {}
        for domain, info in DOMAIN_SOURCE_MAP.items():
            cache_types = info.get('cache_types', [])
            if not cache_types:
                freshness[domain] = {
                    'status': 'static',
                    'label': 'Expert Estimates',
                    'css_class': 'text-muted',
                    'badge_class': 'bg-secondary',
                    'sources': info['sources'],
                    'refresh_cadence': info['refresh'],
                }
                continue

            latest = None
            for ct in cache_types:
                try:
                    record = db.session.query(DataSourceCache).filter(
                        DataSourceCache.source_type == ct,
                        DataSourceCache.is_valid == True
                    ).order_by(DataSourceCache.fetched_at.desc()).first()
                    if record and (latest is None or record.fetched_at > latest.fetched_at):
                        latest = record
                except Exception as e:
                    logger.debug(f"Data freshness query failed for {ct}: {e}")

            if latest:
                age_hours = latest.age_hours or 0
                if age_hours < 24:
                    status = 'fresh'
                    label = f'Updated {int(age_hours)}h ago'
                    css_class = 'text-success'
                    badge_class = 'bg-success'
                elif age_hours < 168:
                    status = 'recent'
                    label = f'Updated {int(age_hours / 24)}d ago'
                    css_class = 'text-info'
                    badge_class = 'bg-info'
                elif age_hours < 720:
                    status = 'aging'
                    label = f'Updated {int(age_hours / 24)}d ago'
                    css_class = 'text-warning'
                    badge_class = 'bg-warning'
                else:
                    status = 'stale'
                    label = f'Updated {int(age_hours / 720)}mo ago'
                    css_class = 'text-danger'
                    badge_class = 'bg-danger'

                freshness[domain] = {
                    'status': status,
                    'label': label,
                    'css_class': css_class,
                    'badge_class': badge_class,
                    'sources': info['sources'],
                    'refresh_cadence': info['refresh'],
                    'used_fallback': latest.used_fallback,
                }
            else:
                freshness[domain] = {
                    'status': 'no_cache',
                    'label': 'Pre-computed data',
                    'css_class': 'text-muted',
                    'badge_class': 'bg-secondary',
                    'sources': info['sources'],
                    'refresh_cadence': info['refresh'],
                }

        return freshness

    except Exception as e:
        logger.warning(f"Could not retrieve data freshness: {e}")
        result = {}
        for domain, info in DOMAIN_SOURCE_MAP.items():
            result[domain] = {
                'status': 'unknown',
                'label': info['refresh'],
                'css_class': 'text-muted',
                'badge_class': 'bg-secondary',
                'sources': info['sources'],
                'refresh_cadence': info['refresh'],
            }
        return result
