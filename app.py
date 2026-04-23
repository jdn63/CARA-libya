"""
CARA Libya — Flask application factory.

Intentionally minimal: all startup logic lives in core.py.
Authentication (before_request) and route registration are wired here.
"""

import os
from flask import Flask, session, redirect, url_for, request
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.orm import DeclarativeBase
from sqlalchemy.pool import NullPool


class Base(DeclarativeBase):
    pass


db = SQLAlchemy(model_class=Base)


def create_app() -> Flask:
    flask_app = Flask(__name__)

    flask_app.secret_key = os.environ.get("SESSION_SECRET")
    if not flask_app.secret_key:
        raise ValueError("SESSION_SECRET environment variable must be set")

    database_url = os.environ.get("DATABASE_URL", "")
    if database_url.startswith("postgres://"):
        database_url = database_url.replace("postgres://", "postgresql://", 1)
    flask_app.config["SQLALCHEMY_DATABASE_URI"] = database_url
    flask_app.config["SQLALCHEMY_ENGINE_OPTIONS"] = {
        "poolclass": NullPool,
        "connect_args": {"connect_timeout": 10},
    }
    flask_app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

    db.init_app(flask_app)

    with flask_app.app_context():
        import models  # noqa: F401
        db.create_all()

        from core import initialize_app
        initialize_app(flask_app)

        from routes import register_routes
        register_routes(flask_app)

    @flask_app.before_request
    def _require_login():
        """
        Restrict access to all routes unless a valid session exists.

        Access control is enabled only when the CARA_ACCESS_PASSWORD environment
        variable is set. If the variable is absent the tool runs in open mode
        (useful during local development). Set the variable via Replit Secrets
        before any public-facing deployment.

        Exempt paths:
          /static/   — CSS, JS, fonts (always public)
          /login     — the login form itself
          /logout    — session teardown
          /health    — monitoring/readiness probe
        """
        exempt_prefixes = ('/static/', '/login', '/logout', '/health')
        if any(request.path.startswith(p) for p in exempt_prefixes):
            return None

        cara_password = os.environ.get('CARA_ACCESS_PASSWORD', '')
        if not cara_password:
            return None

        if not session.get('cara_authenticated'):
            return redirect(url_for('public.login', next=request.path))

    return flask_app


app = create_app()
