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
    _setup_logging(app)
    _log_startup_info()
    _validate_configuration()
    _start_scheduler(app)


def _setup_logging(app: Flask) -> None:
    """Wire production logging + audit-log channel.

    Both are file-rotated under ``logs/`` (ignored from git). The audit
    log is a separate JSON-lines file that records partner-auditable
    events (data uploads, local overrides applied, etc.) for the trust
    posture of the tool.
    """
    try:
        from utils.logging_config import (
            setup_production_logging, setup_audit_log, setup_sentry_integration,
        )
        setup_production_logging(app)
        setup_audit_log()
        setup_sentry_integration(app)
    except Exception as exc:  # pragma: no cover - never block startup on logging
        logger.warning("Could not initialise production logging: %s", exc)


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

        if profile == "libya":
            # HDX refresh: weekly (humanitarian datasets update quarterly at most,
            # but we poll weekly to catch emergency situation reports quickly).
            scheduler.add_job(
                func=lambda: _refresh_libya_hdx(app),
                trigger="interval",
                hours=168,         # every 7 days
                id="refresh_libya_hdx",
                replace_existing=True,
                misfire_grace_time=7200,
            )
            # Global connectors (WHO GHO, World Bank, OpenAQ): monthly.
            # These datasets update infrequently and are expensive to fetch.
            scheduler.add_job(
                func=lambda: _refresh_libya_global_connectors(app),
                trigger="interval",
                hours=720,         # every 30 days
                id="refresh_libya_global",
                replace_existing=True,
                misfire_grace_time=7200,
            )
            logger.info("Libya scheduler jobs registered: HDX weekly, global connectors monthly")

        elif profile == "international":
            scheduler.add_job(
                func=lambda: _refresh_global_data(app),
                trigger="interval",
                hours=24,
                id="refresh_global_data",
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


def _refresh_libya_hdx(app: Flask) -> None:
    """
    Weekly job: download fresh Libya humanitarian data from OCHA HDX.

    Fetches IOM DTM displacement data, OCHA 3W operational presence,
    and UNHCR displacement population data for all Libya municipalities.
    All network I/O happens here — web requests always read from the
    local disk cache written by this function.
    """
    with app.app_context():
        logger.info("Libya HDX refresh starting")
        try:
            from utils.connectors.worldwide.hdx_connector import HDXConnector
            connector = HDXConnector()
            summary = connector.refresh()
            ok = summary.get('datasets_ok', 0)
            total = summary.get('datasets_attempted', 0)
            errors = summary.get('errors', [])
            if errors:
                for err in errors:
                    logger.warning(f"Libya HDX refresh warning: {err}")
            logger.info(
                f"Libya HDX refresh complete: {ok}/{total} datasets downloaded "
                f"at {summary.get('timestamp', 'unknown')}"
            )
        except Exception as e:
            logger.error(f"Libya HDX refresh job failed: {e}")

        # HeiGIT accessibility (hospital, primary care, education access by district)
        try:
            from utils.connectors.worldwide.heigit_connector import HeiGITAccessibilityConnector
            heigit = HeiGITAccessibilityConnector()
            summary = heigit.refresh()
            logger.info(
                f"Libya HeiGIT refresh: {summary.get('files_ok', 0)}/"
                f"{summary.get('files_attempted', 0)} files at {summary.get('timestamp', '?')}"
            )
            if summary.get('errors'):
                for err in summary['errors']:
                    logger.warning(f"Libya HeiGIT warning: {err}")
        except Exception as e:
            logger.warning(f"Libya HeiGIT refresh failed: {e}")

        # IDMC displacement (via HDX CSV — direct IDMC API returns 403)
        try:
            from utils.connectors.worldwide.idmc_hdx_connector import IDMCHDXConnector
            idmc = IDMCHDXConnector()
            summary = idmc.refresh()
            logger.info(
                f"Libya IDMC-HDX refresh: {summary.get('files_ok', 0)}/"
                f"{summary.get('files_attempted', 0)} files at {summary.get('timestamp', '?')}"
            )
            if summary.get('errors'):
                for err in summary['errors']:
                    logger.warning(f"Libya IDMC-HDX warning: {err}")
        except Exception as e:
            logger.warning(f"Libya IDMC-HDX refresh failed: {e}")


def _refresh_libya_global_connectors(app: Flask) -> None:
    """
    Monthly job: refresh global API-based connectors for Libya.

    Covers WHO GHO (disease burden, health indicators), World Bank
    (development indicators, poverty), and OpenAQ (air quality).
    These connectors fetch country-level Libya data via public APIs.
    """
    with app.app_context():
        logger.info("Libya global connector refresh starting")
        try:
            import yaml
            with open(os.path.join("config", "jurisdiction.yaml"), "r") as f:
                jconfig = yaml.safe_load(f) or {}

            country_code = (
                jconfig.get("jurisdiction", {}).get("country_code", "LY")
            )

            # WHO Health Indicators via HDX (April 2026 export — more current than GHO OData API)
            try:
                from utils.connectors.worldwide.who_hdx_connector import WHOHDXConnector
                who_hdx = WHOHDXConnector()
                summary = who_hdx.refresh()
                logger.info(
                    f"Libya WHO-HDX refresh: {summary.get('files_ok', 0)}/"
                    f"{summary.get('files_attempted', 0)} files, "
                    f"{summary.get('indicators_parsed', 0)} indicators parsed"
                )
                if summary.get('errors'):
                    for err in summary['errors']:
                        logger.warning(f"Libya WHO-HDX warning: {err}")
            except Exception as e:
                logger.warning(f"Libya WHO-HDX refresh failed: {e}")

            # WHO GHO (legacy fallback — returns stale data for Libya but kept for non-Libya indicators)
            try:
                from utils.connectors.worldwide.who_gho_connector import WHOGHOConnector
                who = WHOGHOConnector(country_code=country_code)
                result = who.fetch(jurisdiction_id=country_code)
                if result.get("available"):
                    logger.info("Libya WHO GHO refresh: OK")
                else:
                    logger.warning(f"Libya WHO GHO: {result.get('message', 'no data')}")
            except Exception as e:
                logger.warning(f"Libya WHO GHO refresh failed: {e}")

            # World Bank
            try:
                from utils.connectors.worldwide.worldbank_connector import WorldBankConnector
                wb = WorldBankConnector(country_code=country_code)
                result = wb.fetch(jurisdiction_id=country_code)
                if result.get("available"):
                    logger.info("Libya World Bank refresh: OK")
                else:
                    logger.warning(f"Libya World Bank: {result.get('message', 'no data')}")
            except Exception as e:
                logger.warning(f"Libya World Bank refresh failed: {e}")

            # OpenAQ
            try:
                from utils.connectors.worldwide.openaq_connector import OpenAQConnector
                aq = OpenAQConnector(country_code=country_code)
                result = aq.fetch(jurisdiction_id=country_code)
                if result.get("available"):
                    logger.info("Libya OpenAQ refresh: OK")
                else:
                    logger.warning(f"Libya OpenAQ: {result.get('message', 'no data')}")
            except Exception as e:
                logger.warning(f"Libya OpenAQ refresh failed: {e}")

            logger.info("Libya global connector refresh complete")

        except Exception as e:
            logger.error(f"Libya global connector refresh job failed: {e}")


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
