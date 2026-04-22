"""
CARA Template — Flask application factory.

This file is intentionally minimal. All initialization is in core.py.
Modify core.py to add startup logic, scheduler jobs, or middleware.
"""

import os
from flask import Flask
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

    return flask_app


app = create_app()
