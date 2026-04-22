"""
CARA Template — URL routes.

This file registers all routes with the Flask application. Routes are organized
into logical groups using Flask blueprints. Copy this pattern to add new pages.

For a full-featured deployment, you will want to adapt the routes from the
Wisconsin implementation (routes/ directory) to use the template's
jurisdiction_manager and connector_registry.
"""

import logging
import os
import yaml
from flask import Flask, render_template, jsonify, redirect, url_for
from utils.geography.jurisdiction_manager import JurisdictionManager
from utils.risk_engine import load_weights, calculate_phrat, classify_risk, compute_all_domains

logger = logging.getLogger(__name__)


def register_routes(app: Flask) -> None:
    """Register all URL routes with the Flask application."""

    @app.route('/')
    def index():
        """Home page — jurisdiction selection."""
        try:
            manager = JurisdictionManager()
            jurisdictions = manager.get_all()
            config = manager.get_country_config()
            return render_template(
                'index.html',
                jurisdictions=jurisdictions,
                jurisdiction_name=config.get('name', 'CARA'),
            )
        except Exception as e:
            logger.error(f"Index route error: {e}")
            return render_template('error.html', message=str(e)), 500

    @app.route('/dashboard/<jurisdiction_id>')
    def dashboard(jurisdiction_id: str):
        """Main risk assessment dashboard for a jurisdiction."""
        try:
            manager = JurisdictionManager()
            jurisdiction = manager.get_by_id(jurisdiction_id)
            if not jurisdiction:
                return render_template('error.html',
                                       message=f"Jurisdiction '{jurisdiction_id}' not found"), 404

            profile = os.environ.get('CARA_PROFILE', 'international')
            jconfig_path = os.path.join('config', 'jurisdiction.yaml')
            with open(jconfig_path, 'r') as f:
                jconfig = yaml.safe_load(f) or {}

            from utils.connector_registry import ConnectorRegistry
            registry = ConnectorRegistry(profile=profile, jurisdiction_config=jconfig)
            connector_data = {}
            for name, connector in registry.get_all_available().items():
                connector_data[name] = connector.fetch(jurisdiction_id)

            domain_results = compute_all_domains(
                connector_data=connector_data,
                jurisdiction_config=jconfig,
                profile=profile,
            )

            weights = load_weights(
                profile=profile,
                jurisdiction_overrides=jconfig.get('overrides', {}).get('weights'),
            )
            domain_scores = {k: v.get('score', 0.0) for k, v in domain_results.items()}
            total_score, breakdown = calculate_phrat(domain_scores, weights)
            risk_class = classify_risk(total_score)

            regional_group = manager.get_group_for_jurisdiction(jurisdiction_id)
            framework = _load_framework(profile)
            framework_name = getattr(framework, 'name', None) if framework else None

            tier = risk_class.get('level', 'minimal')
            tier_color_map = {
                'critical': 'danger', 'high': 'danger',
                'moderate': 'warning', 'low': 'success', 'minimal': 'secondary',
            }
            composite = {
                'score': total_score,
                'tier': tier,
                'tier_color': tier_color_map.get(tier, 'secondary'),
            }

            domains_view = []
            action_items = []
            for domain_id, weight in weights.items():
                result = domain_results.get(domain_id, {}) or {}
                domains_view.append({
                    'id': domain_id,
                    'label': domain_id.replace('_', ' ').title(),
                    'weight': weight,
                    'score': result.get('score'),
                    'data_sources': result.get('data_sources', []),
                    'components': result.get('components', {}),
                })
                for item in result.get('action_plan_items', []) or []:
                    action_items.append(item)

            top_domain = None
            scored = [d for d in domains_view if d['score'] is not None and d['components']]
            if scored:
                top = max(scored, key=lambda d: d['score'])
                top_domain = {
                    'label': top['label'],
                    'components': top['components'],
                }

            all_jurisdictions = manager.get_all()

            return render_template(
                'dashboard.html',
                jurisdiction=jurisdiction,
                composite=composite,
                domains=domains_view,
                action_items=action_items,
                top_domain=top_domain,
                all_jurisdictions=all_jurisdictions,
                framework_name=framework_name,
                profile=profile,
                last_refresh=None,
                map_html=None,
                framework_summary=None,
                regional_group=regional_group,
                breakdown=breakdown,
                domain_results=domain_results,
                app_name=jconfig.get('jurisdiction', {}).get('name'),
            )
        except Exception as e:
            logger.error(f"Dashboard error for {jurisdiction_id}: {e}", exc_info=True)
            return render_template('error.html', message=str(e)), 500

    @app.route('/api/status')
    def api_status():
        """Health check endpoint."""
        return jsonify({'status': 'ok', 'version': _get_version()})

    @app.route('/health')
    def health():
        """Render health check for deployment platforms."""
        return 'OK', 200

    @app.route('/methodology')
    def methodology():
        """Methodology documentation page."""
        profile = os.environ.get('CARA_PROFILE', 'international')
        framework = _load_framework(profile)
        framework_name = getattr(framework, 'name', None) if framework else None
        framework_key = 'who_ihr' if profile == 'international' else 'cdc_phep'

        try:
            jconfig_path = os.path.join('config', 'jurisdiction.yaml')
            with open(jconfig_path, 'r') as f:
                jconfig = yaml.safe_load(f) or {}
        except Exception:
            jconfig = {}
        jurisdiction_name = jconfig.get('jurisdiction', {}).get('name', 'CARA')

        weights = load_weights(
            profile=profile,
            jurisdiction_overrides=jconfig.get('overrides', {}).get('weights'),
        )

        try:
            profile_path = os.path.join('config', 'profiles', f'{profile}.yaml')
            with open(profile_path, 'r') as f:
                profile_cfg = yaml.safe_load(f) or {}
        except Exception:
            profile_cfg = {}
        domain_meta = profile_cfg.get('domains', {}) or {}

        domains = []
        for domain_id, weight in weights.items():
            meta = domain_meta.get(domain_id, {}) or {}
            domains.append({
                'id': domain_id,
                'label': meta.get('label', domain_id.replace('_', ' ').title()),
                'weight': weight,
                'source': meta.get('primary_source', 'See profile YAML'),
                'frequency': meta.get('refresh_frequency', 'Varies'),
            })

        data_source_detail = profile_cfg.get('data_source_detail') or None

        return render_template(
            'methodology.html',
            profile=profile,
            framework=framework,
            framework_name=framework_name,
            framework_key=framework_key,
            jurisdiction_name=jurisdiction_name,
            domains=domains,
            data_source_detail=data_source_detail,
        )

    @app.route('/about')
    def about():
        """About and attribution page."""
        return render_template('about.html')

    @app.errorhandler(404)
    def not_found(e):
        return render_template('error.html', message='Page not found'), 404

    @app.errorhandler(500)
    def server_error(e):
        return render_template('error.html', message='Internal server error'), 500


def _get_version() -> str:
    if os.path.exists('VERSION.txt'):
        with open('VERSION.txt') as f:
            return f.read().strip()
    return '0.1.0'


def _load_framework(profile: str):
    try:
        if profile == 'who_ihr' or profile == 'international':
            from utils.frameworks.who_ihr import WHOIHRFramework
            return WHOIHRFramework()
        else:
            from utils.frameworks.cdc_phep import CDCPHEPFramework
            return CDCPHEPFramework()
    except Exception:
        return None
