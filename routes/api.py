"""
API routes for Libya CARA application.

REST API endpoints for:
- Municipality risk data
- Jurisdiction list
- Data source status
- Cache refresh (admin)
"""

import logging
from datetime import datetime
from flask import Blueprint, jsonify, request

from utils.geography.jurisdiction_manager import JurisdictionManager
from utils.api_responses import api_success, api_error, api_not_found, api_server_error

logger = logging.getLogger(__name__)

api_bp = Blueprint('api', __name__, url_prefix='/api')

_jm = None


def _get_jm() -> JurisdictionManager:
    global _jm
    if _jm is None:
        _jm = JurisdictionManager()
    return _jm


@api_bp.route('/municipalities')
@api_bp.route('/jurisdictions')
def get_municipalities():
    """Return all municipalities as JSON.

    Exposed at both /api/municipalities (canonical, current naming) and
    /api/jurisdictions (legacy alias kept so external callers and the
    Task #7 acceptance smoke check continue to work).
    """
    try:
        jm = _get_jm()
        municipalities = jm.get_all()
        return api_success(municipalities, f"{len(municipalities)} municipalities loaded")
    except Exception as e:
        logger.error(f"Error fetching municipalities: {e}")
        return api_server_error(str(e))


@api_bp.route('/municipality/<jurisdiction_id>')
def get_municipality(jurisdiction_id):
    """Return a single municipality by ID."""
    try:
        jm = _get_jm()
        muni = jm.get_by_id(jurisdiction_id)
        if not muni:
            return api_not_found(f"Municipality {jurisdiction_id}")
        return api_success(muni, "Municipality found")
    except Exception as e:
        logger.error(f"Error fetching municipality {jurisdiction_id}: {e}")
        return api_server_error(str(e))


@api_bp.route('/regions')
def get_regions():
    """Return regional groupings."""
    try:
        jm = _get_jm()
        groups = jm.get_regional_groups()
        return api_success(groups, "Regional groups loaded")
    except Exception as e:
        logger.error(f"Error fetching regions: {e}")
        return api_server_error(str(e))


@api_bp.route('/status')
def get_status():
    """Return application status — useful for low-connectivity health checks."""
    try:
        jm = _get_jm()
        municipalities = jm.get_all()
        return api_success({
            'status': 'ok',
            'municipalities_loaded': len(municipalities),
            'framework': 'INFORM Risk Index',
            'sendai_aligned': True,
            'timestamp': datetime.utcnow().isoformat(),
            'access': 'restricted_official_use_only',
        }, "Libya CARA is operational")
    except Exception as e:
        logger.error(f"Status check failed: {e}")
        return api_server_error(str(e))
