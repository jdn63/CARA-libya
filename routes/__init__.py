"""
Routes package for CARA application.

This package contains all Flask blueprints organized by functionality:
- public: Public pages (home, methodology, docs)
- dashboard: User dashboard and jurisdiction views
- api: REST API endpoints  
- herc: HERC region specific functionality
"""

from routes.public import public_bp
from routes.dashboard import dashboard_bp
from routes.api import api_bp
from routes.herc import herc_bp
from routes.gis_export import gis_export_bp


def register_routes(app):
    """Register all blueprints with the Flask application."""
    app.register_blueprint(public_bp)
    app.register_blueprint(dashboard_bp)
    app.register_blueprint(api_bp)
    app.register_blueprint(herc_bp)
    app.register_blueprint(gis_export_bp)
