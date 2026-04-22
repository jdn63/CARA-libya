"""
HERC region routes for CARA application.

These routes handle HERC (Hospital Emergency Readiness Coalition) specific functionality:
- HERC region dashboards
- Kaiser Permanente HVA exports
- HERC print summaries
"""

import logging
from datetime import datetime
from flask import Blueprint, render_template, send_file, redirect, url_for
from utils.herc_data import get_herc_statistics, get_all_herc_regions

# Set up logger for this module
logger = logging.getLogger(__name__)

# Create Blueprint
herc_bp = Blueprint('herc', __name__)


@herc_bp.route('/herc-dashboard/<herc_id>')
def herc_dashboard(herc_id):
    """Display HERC region dashboard with real aggregated risk calculations"""
    try:
        logger.info(f"Loading HERC dashboard for region {herc_id}")
        
        # Get HERC region basic info
        region_info = get_herc_statistics(herc_id)
        
        if not region_info:
            logger.error(f"No HERC data available for region ID: {herc_id}")
            return render_template('error.html', 
                           message="No HERC data available for the requested region.")
        
        # Calculate real risk data using aggregator
        from utils.herc_risk_aggregator import get_herc_region_risk
        
        risk_data = get_herc_region_risk(herc_id)
        
        if not risk_data:
            logger.error(f"Failed to calculate risk data for HERC region {herc_id}")
            return render_template('error.html', 
                           message="Unable to calculate risk data for the requested HERC region.")
        
        # Merge region info with calculated risk data
        risk_data.update({
            'location': region_info.get('name', f'HERC Region {herc_id}'),
            'jurisdiction_id': herc_id,
            'county_name': region_info.get('name', f'HERC Region {herc_id}'),
            'statistics': region_info.get('statistics', {})
        })
        
        # Get all HERC regions for navigation
        all_herc_regions = get_all_herc_regions()
        
        logger.info(f"Successfully loaded HERC dashboard for region {herc_id} with real risk calculations")
        
        return render_template('herc_dashboard.html',
                             risk_data=risk_data,
                             herc_regions=all_herc_regions,
                             current_herc_id=herc_id,
                             now=datetime.now())
        
    except Exception as e:
        logger.error(f"Error loading HERC dashboard for region {herc_id}: {str(e)}")
        import traceback
        logger.debug(f"Traceback: {traceback.format_exc()}")
        return render_template('error.html', 
                           message="An error occurred while loading the HERC dashboard. Please try again.")


@herc_bp.route('/herc-dashboard')
@herc_bp.route('/herc-dashboard/')
def herc_dashboard_redirect():
    """Handle HERC dashboard without ID - redirect to main page"""
    logger.info("HERC dashboard accessed without region ID, redirecting to main page")
    return redirect(url_for('public.index'))


@herc_bp.route('/herc-kp-hva-export/<herc_id>')
def herc_kp_hva_export(herc_id):
    """Generate Kaiser Permanente HVA Excel export for HERC region using official KP template"""
    try:
        from utils.herc_data import get_all_herc_regions
        from utils.herc_risk_aggregator import get_herc_region_risk
        from utils.kp_hva_export import generate_kp_hva_herc_export
        import os
        
        logger.info(f"Generating Kaiser Permanente HVA export for HERC region {herc_id}")
        
        # Get HERC region info
        all_herc_regions = get_all_herc_regions()
        herc_region = None
        for region in all_herc_regions:
            if str(region['id']) == str(herc_id):
                herc_region = region
                break
        
        if not herc_region:
            logger.error(f"HERC region not found: {herc_id}")
            return render_template('error.html', 
                           message="The requested HERC region was not found.")
        
        # Calculate real risk data for the region
        risk_data = get_herc_region_risk(herc_id)
        if not risk_data:
            logger.error(f"Failed to calculate risk data for HERC region: {herc_id}")
            return render_template('error.html', 
                           message="Unable to calculate risk data for the requested HERC region.")
        
        # Generate the Excel file using official KP template
        excel_file_path = generate_kp_hva_herc_export(risk_data)
        
        if not excel_file_path or not os.path.exists(excel_file_path):
            logger.error(f"Failed to generate Excel file for HERC region {herc_id}")
            return render_template('error.html', 
                           message="Failed to generate Kaiser Permanente HVA export file")
        
        logger.info(f"Successfully generated Kaiser Permanente HVA export: {excel_file_path}")
        
        # Generate filename for download
        region_name = herc_region.get('name', f'HERC_Region_{herc_id}')
        download_filename = f"KP_HVA_{region_name}_{datetime.now().strftime('%Y-%m-%d')}.xlsm"
        
        return send_file(
            excel_file_path,
            as_attachment=True,
            download_name=download_filename,
            mimetype='application/vnd.ms-excel.sheet.macroEnabled.12'
        )
        
    except Exception as e:
        logger.error(f"Error generating Kaiser Permanente HVA export for HERC region {herc_id}: {str(e)}")
        import traceback
        logger.debug(f"Traceback: {traceback.format_exc()}")
        return render_template('error.html', 
                           message="An error occurred while generating the Kaiser Permanente HVA export. Please try again.")


@herc_bp.route('/herc-print-summary/<herc_id>')
def herc_print_summary(herc_id):
    """Generate printable risk summary for HERC region with real risk calculations"""
    try:
        logger.info(f"Generating print summary for HERC region {herc_id}")
        
        # Get HERC region basic info
        region_info = get_herc_statistics(herc_id)
        
        if not region_info:
            logger.error(f"No HERC data available for print summary: {herc_id}")
            return render_template('error.html', 
                           message="No HERC data available for the requested region.")
        
        # Calculate real risk data using aggregator
        from utils.herc_risk_aggregator import get_herc_region_risk
        
        risk_data = get_herc_region_risk(herc_id)
        
        if not risk_data:
            logger.error(f"Failed to calculate risk data for HERC region {herc_id}")
            return render_template('error.html', 
                           message="Unable to calculate risk data for the requested HERC region.")
        
        # Merge region info with calculated risk data
        risk_data.update({
            'location': region_info.get('name', f'HERC Region {herc_id}'),
            'statistics': region_info.get('statistics', {})
        })
        
        # Add current date for print summary
        current_date = datetime.now().strftime("%B %d, %Y")
        
        logger.info(f"Successfully generated print summary for HERC region {herc_id} with real risk data")
        
        return render_template('herc_print_summary.html', 
                             risk_data=risk_data,
                             current_date=current_date)
        
    except Exception as e:
        logger.error(f"Error generating print summary for HERC region {herc_id}: {str(e)}")
        import traceback
        logger.debug(f"Traceback: {traceback.format_exc()}")
        return render_template('error.html', 
                           message="An error occurred while generating the print summary. Please try again.")