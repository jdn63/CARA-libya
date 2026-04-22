"""
Public routes for CARA application.

These routes handle public-facing pages that don't require authentication:
- Home page with jurisdiction selection
- Methodology and documentation pages
- FAQ and help pages
"""

import logging
from datetime import datetime
from flask import Blueprint, render_template, send_from_directory, request, redirect, url_for, flash
from utils.data_processor import get_wi_jurisdictions
from utils.herc_data import get_all_herc_regions
from utils.api_responses import api_not_found
from core import db

# Set up logger for this module
logger = logging.getLogger(__name__)

# Create Blueprint
public_bp = Blueprint('public', __name__)


@public_bp.route('/')
def index():
    """Main application index page"""
    try:
        logger.info("Fetching Wisconsin jurisdictions for index page")
        jurisdictions = get_wi_jurisdictions()
        
        # Debug - print loaded jurisdictions to logs
        logger.info(f"Loaded {len(jurisdictions)} jurisdictions: {[j['name'] for j in jurisdictions[:5]]}...")
        
        if not jurisdictions:
            logger.warning("No jurisdictions returned from get_wi_jurisdictions()")
            # Use minimal fallback rather than returning empty
            fallback_jurisdictions = [
                {'name': 'Milwaukee City Health Department', 'id': '41'},
                {'name': 'North Shore Health Department', 'id': '42'},
                {'name': 'Wauwatosa Health Department', 'id': '55'}
            ]
            logger.warning(f"Using minimal fallback list of {len(fallback_jurisdictions)} jurisdictions")
            jurisdictions = fallback_jurisdictions
            
        # Sort jurisdictions alphabetically by name
        sorted_jurisdictions = sorted(jurisdictions, key=lambda x: x['name'])
        
        # Use the jurisdictions we loaded directly from data_processor
        logger.info(f"Using {len(sorted_jurisdictions)} alphabetically sorted jurisdictions from data_processor")
        
        logger.info("Fetching HERC regions for index page")
        herc_regions = get_all_herc_regions()
        logger.info(f"Loaded {len(herc_regions)} HERC regions")
        
        return render_template('index.html', 
                              jurisdictions=sorted_jurisdictions,
                              herc_regions=herc_regions)
    except Exception as e:
        logger.error(f"Error fetching jurisdictions: {str(e)}")
        return render_template('index.html', 
                              jurisdictions=[],
                              herc_regions=[], 
                              error="Failed to load jurisdictions. Please try again later.")


@public_bp.route('/methodology')
def methodology():
    """Display the risk assessment methodology page"""
    try:
        return render_template('methodology.html')
    except Exception as e:
        logger.error(f"Error loading methodology page: {str(e)}")
        return render_template('error.html', 
                           message="An error occurred while loading the methodology page. Please try again.")


@public_bp.route('/gis-export')
def gis_export_redirect():
    """Redirect /gis-export to the GIS export tab on the home page"""
    return redirect('/#gis-export-tab')


@public_bp.route('/active-shooter-methodology')
def active_shooter_methodology():
    """Display the active shooter risk assessment methodology page"""
    try:
        return render_template('active_shooter_methodology.html')
    except Exception as e:
        logger.error(f"Error loading active shooter methodology page: {str(e)}")
        return render_template('error.html', 
                           message="An error occurred while loading the methodology page. Please try again.")


@public_bp.route('/docs/faq')
def faq():
    """Display the Frequently Asked Questions page"""
    try:
        return render_template('docs/faq.html')
    except Exception as e:
        logger.error(f"Error loading FAQ page: {str(e)}")
        return render_template('error.html', 
                           message="An error occurred while loading this page. Please try again.")


@public_bp.route('/docs/quick_start_guide')
def quick_start_guide():
    """Display the Quick Start Guide page"""
    try:
        return render_template('docs/quick_start_guide.html')
    except Exception as e:
        logger.error(f"Error loading Quick Start Guide page: {str(e)}")
        return render_template('error.html', 
                           message="An error occurred while loading this page. Please try again.")


@public_bp.route('/docs/<path:filename>')
def serve_documentation(filename):
    """Serve documentation files from the docs directory"""
    try:
        return send_from_directory('docs', filename)
    except Exception as e:
        logger.error(f"Error serving documentation: {str(e)}")
        return api_not_found("Documentation")


