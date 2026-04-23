"""
Routes package for Libya CARA application.

Blueprints:
- public:     Home page, methodology, about, data sources
- dashboard:  Municipality and national risk dashboards
- api:        REST API endpoints
"""

from routes.public import public_bp
from routes.dashboard import dashboard_bp
from routes.api import api_bp
from routes.data_entry import data_entry_bp


def register_routes(app):
    """Register all blueprints with the Flask application."""
    app.register_blueprint(public_bp)
    app.register_blueprint(dashboard_bp)
    app.register_blueprint(api_bp)
    app.register_blueprint(data_entry_bp)
