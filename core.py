"""
CARA Template — application initialization.

This module runs once at startup after the Flask app and database are ready.
Add scheduler jobs, connector initialization, and startup validation here.

To add a new scheduled data refresh:
1. Create a function that calls your connector's fetch() method and stores
   the result to the database cache
2. Add it to the scheduler below with an appropriate interval
"""

import logging
import os
from typing import Optional
from flask import Flask

logger = logging.getLogger(__name__)


def initialize_app(app: Flask) -> None:
    """Called once at startup after db.create_all()."""
    _log_startup_info()
    _validate_configuration()
    _start_scheduler(app)


def _log_startup_info() -> None:
    profile = os.environ.get("CARA_PROFILE", "international")
    jurisdiction_name = _get_jurisdiction_name()
    version = _get_version()
    logger.info(f"CARA Template v{version} starting — profile: {profile}, "
                f"jurisdiction: {jurisdiction_name}")


def _validate_configuration() -> None:
    import yaml

    config_path = os.path.join("config", "jurisdiction.yaml")
    if not os.path.exists(config_path):
        logger.warning(
            "jurisdiction.yaml not found. Copy config/jurisdiction.yaml.example "
            "to config/jurisdiction.yaml and fill in your jurisdiction details."
        )
        return

    try:
        with open(config_path, "r") as f:
            config = yaml.safe_load(f)
        jconfig = config.get("jurisdiction", {})
        if jconfig.get("name") in ("Your Jurisdiction Name", "", None):
            logger.warning(
                "jurisdiction.yaml contains placeholder values. "
                "Update it with your jurisdiction's actual details."
            )
    except Exception as e:
        logger.error(f"Failed to validate jurisdiction.yaml: {e}")


def _start_scheduler(app: Flask) -> None:
    enable_scrapers = os.environ.get("ENABLE_SCRAPERS", "1") == "1"
    if not enable_scrapers:
        logger.info("Scheduler disabled (ENABLE_SCRAPERS=0)")
        return

    try:
        from apscheduler.schedulers.background import BackgroundScheduler
        scheduler = BackgroundScheduler(daemon=True)

        profile = os.environ.get("CARA_PROFILE", "international")

        if profile == "international":
            scheduler.add_job(
                func=lambda: _refresh_global_data(app),
                trigger="interval",
                hours=24,
                id="refresh_global_data",
                replace_existing=True,
                misfire_grace_time=3600,
            )

        elif profile == "us_state":
            scheduler.add_job(
                func=lambda: _refresh_us_data(app),
                trigger="interval",
                hours=24,
                id="refresh_us_data",
                replace_existing=True,
                misfire_grace_time=3600,
            )

        scheduler.start()
        logger.info(f"Scheduler started for profile: {profile}")
        app.scheduler = scheduler

    except ImportError:
        logger.warning("APScheduler not installed — scheduled data refresh disabled")
    except Exception as e:
        logger.error(f"Scheduler startup failed: {e}")


def _refresh_global_data(app: Flask) -> None:
    """Refresh all global connector data (international profile)."""
    with app.app_context():
        logger.info("Starting global data refresh")
        try:
            from utils.connector_registry import ConnectorRegistry
            import yaml

            with open(os.path.join("config", "jurisdiction.yaml"), "r") as f:
                jconfig = yaml.safe_load(f) or {}

            registry = ConnectorRegistry(profile="international", jurisdiction_config=jconfig)
            jid = jconfig.get("jurisdiction", {}).get("short_name", "XX")

            for name, connector in registry.get_all_available().items():
                try:
                    result = connector.fetch(jurisdiction_id=jid)
                    if result.get("available"):
                        logger.info(f"Refreshed connector: {name}")
                    else:
                        logger.warning(f"Connector {name} returned no data: {result.get('message')}")
                except Exception as e:
                    logger.error(f"Connector {name} refresh failed: {e}")
        except Exception as e:
            logger.error(f"Global data refresh failed: {e}")


def _refresh_us_data(app: Flask) -> None:
    """Refresh all US connector data (us_state profile)."""
    with app.app_context():
        logger.info("Starting US data refresh")
        try:
            from utils.connector_registry import ConnectorRegistry
            import yaml

            with open(os.path.join("config", "jurisdiction.yaml"), "r") as f:
                jconfig = yaml.safe_load(f) or {}

            registry = ConnectorRegistry(profile="us_state", jurisdiction_config=jconfig)
            jid = jconfig.get("jurisdiction", {}).get("short_name", "XX")

            for name, connector in registry.get_all_available().items():
                try:
                    result = connector.fetch(jurisdiction_id=jid)
                    if result.get("available"):
                        logger.info(f"Refreshed connector: {name}")
                    else:
                        logger.warning(
                            f"Connector {name} returned no data: {result.get('message')}"
                        )
                except Exception as e:
                    logger.error(f"Connector {name} refresh failed: {e}")
        except Exception as e:
            logger.error(f"US data refresh failed: {e}")


def _get_jurisdiction_name() -> str:
    try:
        import yaml
        config_path = os.path.join("config", "jurisdiction.yaml")
        if os.path.exists(config_path):
            with open(config_path, "r") as f:
                config = yaml.safe_load(f) or {}
            return config.get("jurisdiction", {}).get("name", "Unknown")
    except Exception:
        pass
    return "Unknown"


def _get_version() -> str:
    version_path = "VERSION.txt"
    if os.path.exists(version_path):
        with open(version_path) as f:
            return f.read().strip()
    return "0.1.0"
