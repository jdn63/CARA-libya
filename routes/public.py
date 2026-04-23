"""
Public routes for Libya CARA application.

These routes handle the main pages:
- Home page with municipality selection
- Methodology and data provenance documentation
- About page
- Data sources page
"""

import logging
import os
from datetime import datetime
from flask import (Blueprint, render_template, redirect, url_for,
                   request, session, flash, jsonify)

from utils.geography.jurisdiction_manager import JurisdictionManager

logger = logging.getLogger(__name__)

public_bp = Blueprint('public', __name__)

_jurisdiction_manager = None


def _get_jm() -> JurisdictionManager:
    """Return (and cache) a JurisdictionManager instance."""
    global _jurisdiction_manager
    if _jurisdiction_manager is None:
        _jurisdiction_manager = JurisdictionManager()
    return _jurisdiction_manager


@public_bp.route('/')
def index():
    """Libya CARA home page — municipality selector."""
    try:
        jm = _get_jm()
        municipalities = jm.get_all()
        municipalities_sorted = sorted(
            municipalities,
            key=lambda x: (x.get('region', ''), x.get('name_ar', x.get('name', '')))
        )
        return render_template(
            'index.html',
            municipalities=municipalities_sorted,
            jurisdiction_name='ليبيا',
            current_year=datetime.utcnow().year,
        )
    except Exception as e:
        logger.error(f"Error loading Libya CARA home page: {e}")
        return render_template(
            'index.html',
            municipalities=[],
            jurisdiction_name='ليبيا',
            current_year=datetime.utcnow().year,
            error="حدث خطأ في تحميل البلديات. / Failed to load municipalities.",
        )


@public_bp.route('/methodology')
def methodology():
    """Methodology and data provenance documentation."""
    try:
        jm = _get_jm()
        country_config = jm.get_country_config()
        return render_template(
            'methodology.html',
            country_config=country_config,
            current_year=datetime.utcnow().year,
        )
    except Exception as e:
        logger.error(f"Error loading methodology page: {e}")
        return render_template('error.html', message="Failed to load methodology page.")


@public_bp.route('/about')
def about():
    """About this tool."""
    try:
        return render_template('about.html', current_year=datetime.utcnow().year)
    except Exception as e:
        logger.error(f"Error loading about page: {e}")
        return render_template('error.html', message="Failed to load about page.")


@public_bp.route('/data-sources')
def data_sources():
    """Data sources and provenance."""
    try:
        return render_template('data_sources.html', current_year=datetime.utcnow().year)
    except Exception as e:
        logger.error(f"Error loading data sources page: {e}")
        return render_template('error.html', message="Failed to load data sources page.")


@public_bp.route('/login', methods=['GET', 'POST'])
def login():
    """Bilingual login page — validates CARA_ACCESS_PASSWORD session secret."""
    cara_password = os.environ.get('CARA_ACCESS_PASSWORD', '')

    if not cara_password:
        session['cara_authenticated'] = True
        return redirect(request.args.get('next') or '/')

    if session.get('cara_authenticated'):
        return redirect(request.args.get('next') or '/')

    if request.method == 'POST':
        entered = request.form.get('password', '')
        if entered == cara_password:
            session['cara_authenticated'] = True
            session.permanent = False
            next_url = request.args.get('next', '/')
            if not next_url.startswith('/'):
                next_url = '/'
            return redirect(next_url)
        flash('كلمة المرور غير صحيحة / Incorrect password — please try again.', 'danger')
        logger.warning("Failed login attempt from %s", request.remote_addr)

    return render_template('login.html')


@public_bp.route('/logout')
def logout():
    """Clear session and redirect to login page."""
    session.clear()
    return redirect(url_for('public.login'))


@public_bp.route('/health')
def health():
    """
    Lightweight health-check endpoint for monitoring and readiness probes.
    Returns JSON — no authentication required.
    """
    try:
        jm = _get_jm()
        municipalities_loaded = len(jm.get_all())
    except Exception:
        municipalities_loaded = 0

    return jsonify({
        'status': 'ok',
        'service': 'CARA Libya',
        'municipalities_loaded': municipalities_loaded,
        'municipalities_target': 148,
        'data_coverage_pct': round(municipalities_loaded / 148 * 100, 1),
    })


@public_bp.route('/gis-export')
def gis_export_redirect():
    return redirect('/')
