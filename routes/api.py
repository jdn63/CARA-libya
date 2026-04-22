"""
API routes for CARA application.

These routes handle REST API endpoints:
- Historical and predictive analysis data
- HERC and WEM region data  
- Geographic boundaries
- Admin functionality (scheduler, data refresh)
"""

import logging
from datetime import datetime
from flask import Blueprint
from utils.data_processor import get_historical_risk_data
from utils.predictive_analysis import RiskPredictor
from utils.herc_data import get_herc_statistics, get_all_herc_regions
from utils.wem_data import get_wem_statistics, get_all_wem_regions
from utils import geo_data
from utils.data_refresh_scheduler import get_scheduler_status, refresh_now
from utils.security_manager import require_api_key
from utils.api_responses import api_success, api_error, api_not_found, api_server_error

# Set up logger for this module
logger = logging.getLogger(__name__)

# Create Blueprint
api_bp = Blueprint('api', __name__, url_prefix='/api')


@api_bp.route('/historical-data/<jurisdiction_id>')
@require_api_key('readonly')  # Requires API key
def get_historical_risk_data_api(jurisdiction_id):
    """Get historical risk data for predictions (API endpoint)"""
    try:
        # Get historical data from the utility
        start_year = 2020  # Default start year
        end_year = 2024    # Default end year
        
        data = get_historical_risk_data(jurisdiction_id, start_year, end_year)
        
        # Log API access
        logger.info(f"API access: Historical data requested for jurisdiction {jurisdiction_id}")
        
        return api_success({
            'jurisdiction_id': jurisdiction_id,
            'data': data,
            'years_requested': f"{start_year}-{end_year}",
            'data_points': len(data)
        }, "Historical data retrieved successfully")
    except Exception as e:
        logger.error(f"Error fetching historical data: {str(e)}")
        return api_server_error(str(e))


@api_bp.route('/predictive-analysis/<jurisdiction_id>')
@require_api_key('readonly')  # Requires API key  
def get_predictive_analysis_api(jurisdiction_id):
    """Get predictive analysis for jurisdiction (API endpoint)"""
    try:
        # Get current risk data first
        from utils.data_processor import process_risk_data
        from routes.dashboard import sanitize_risk_data
        
        current_risk_data = process_risk_data(jurisdiction_id)
        current_risk_data = sanitize_risk_data(current_risk_data)
        
        # Generate predictions
        predictor = RiskPredictor()
        analysis = predictor.generate_predictions(jurisdiction_id, current_risk_data)
        
        logger.info(f"API access: Predictive analysis requested for jurisdiction {jurisdiction_id}")
        
        return api_success({
            'jurisdiction_id': jurisdiction_id,
            'analysis': analysis,
            'prediction_type': 'multi_domain_risk_forecast'
        }, "Predictive analysis generated successfully")
    except Exception as e:
        logger.error(f"Error generating predictive analysis: {str(e)}")
        return api_server_error(str(e))


@api_bp.route('/herc-region/<region_id>')
@require_api_key('readonly')
def get_herc_region_data_api(region_id):
    """Get HERC region data (API endpoint)"""
    try:
        herc_data = get_herc_statistics(region_id)
        
        if not herc_data:
            return api_not_found("HERC region")
            
        logger.info(f"API access: HERC region data requested for region {region_id}")
        
        return api_success(herc_data, "HERC region data retrieved successfully")
    except Exception as e:
        logger.error(f"Error getting HERC region data: {str(e)}")
        return api_server_error(str(e))


@api_bp.route('/herc-regions')
@require_api_key('readonly')
def get_all_herc_regions_api():
    """Get all HERC regions data (API endpoint)"""
    try:
        herc_regions = get_all_herc_regions()
        
        logger.info("API access: All HERC regions data requested")
        
        return api_success(herc_regions, "All HERC regions retrieved successfully")
    except Exception as e:
        logger.error(f"Error getting HERC regions: {str(e)}")
        return api_server_error(str(e))


@api_bp.route('/wem-region/<region_id>')
@require_api_key('readonly')
def get_wem_region_data_api(region_id):
    """Get WEM region data (API endpoint)"""
    try:
        wem_data = get_wem_statistics(region_id)
        
        if not wem_data:
            return api_not_found("WEM region")
            
        logger.info(f"API access: WEM region data requested for region {region_id}")
        
        return api_success(wem_data, "WEM region data retrieved successfully")
    except Exception as e:
        logger.error(f"Error getting WEM region data: {str(e)}")
        return api_server_error(str(e))


@api_bp.route('/wem-regions')
@require_api_key('readonly')
def get_all_wem_regions_api():
    """Get all WEM regions data (API endpoint)"""
    try:
        wem_regions = get_all_wem_regions()
        
        logger.info("API access: All WEM regions data requested")
        
        return api_success(wem_regions, "All WEM regions retrieved successfully")
    except Exception as e:
        logger.error(f"Error getting WEM regions: {str(e)}")
        return api_server_error(str(e))


@api_bp.route('/herc-boundaries')
@require_api_key('readonly')
def get_herc_boundaries_api():
    """Get HERC region boundaries (API endpoint)"""
    try:
        # Get HERC boundary data from geo_data utility
        boundaries = geo_data.get_herc_region_boundaries()
        
        logger.info("API access: HERC boundaries data requested")
        
        return api_success(boundaries, "HERC boundaries retrieved successfully")
    except Exception as e:
        logger.error(f"Error getting HERC boundaries: {str(e)}")
        return api_server_error(str(e))


@api_bp.route('/wem-boundaries')
@require_api_key('readonly')
def get_wem_boundaries_api():
    """Get WEM region boundaries (API endpoint)"""
    try:
        # Get WEM boundary data from geo_data utility
        boundaries = geo_data.get_wem_region_boundaries()
        
        logger.info("API access: WEM boundaries data requested")
        
        return api_success(boundaries, "WEM boundaries retrieved successfully")
    except Exception as e:
        logger.error(f"Error getting WEM boundaries: {str(e)}")
        return api_server_error(str(e))


@api_bp.route('/scheduler-status')
@require_api_key('admin')  # Requires admin access
def get_scheduler_status_api():
    """Get data refresh scheduler status (admin only)"""
    try:
        status = get_scheduler_status()
        
        logger.info("API access: Scheduler status requested (admin)")
        
        return api_success(status, "Scheduler status retrieved successfully")
    except Exception as e:
        logger.error(f"Error getting scheduler status: {str(e)}")
        return api_server_error(str(e))


@api_bp.route('/refresh-data/<source>')
@require_api_key('admin')  # Requires admin access for data refresh
def refresh_data_source_api(source):
    """Trigger data refresh for specific source (admin only)"""
    try:
        result = refresh_now(source)
        
        logger.info(f"API access: Data refresh triggered for {source} (admin)")
        
        return api_success({
            'source': source,
            'refresh_result': result,
            'timestamp': datetime.now().isoformat()
        }, "Data refresh completed successfully")
    except Exception as e:
        logger.error(f"Error refreshing data source {source}: {str(e)}")
        return api_server_error(str(e))