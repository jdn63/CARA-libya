"""
CARA Template — data processor.

Orchestrates the full pipeline from connector data retrieval to domain scoring
and PHRAT composite score calculation.

Pipeline stages:
    1. Load jurisdiction configuration and profile
    2. Instantiate connector registry
    3. For each active domain, fetch connector data and compute domain score
    4. Pass domain scores to risk engine for PHRAT calculation
    5. Return structured result dict for templates and caching

This module is called by routes.py on each dashboard request (with DB caching).
"""

import logging
import os
from datetime import datetime
from typing import Any, Dict, List, Optional
import yaml

from utils.connector_registry import ConnectorRegistry, load_jurisdiction_config
from utils.risk_engine import load_weights, calculate_phrat, classify_risk, compute_all_domains

logger = logging.getLogger(__name__)


def get_profile() -> str:
    """Return the active CARA profile from environment."""
    return os.environ.get("CARA_PROFILE", "international")


def compute_risk_for_jurisdiction(jurisdiction_id: str) -> Dict[str, Any]:
    """
    Run the full risk pipeline for a single jurisdiction.

    Returns a dict with keys:
        jurisdiction_id, profile, computed_at,
        total_score, risk_level, risk_class,
        domain_scores, domain_components, data_sources_used, data_coverage
    """
    profile = get_profile()
    jconfig = load_jurisdiction_config()

    registry = ConnectorRegistry(profile=profile, jurisdiction_config=jconfig)

    domain_inputs = _gather_domain_inputs(registry, jurisdiction_id, jconfig)

    weights = load_weights(
        profile=profile,
        jurisdiction_overrides=jconfig.get("jurisdiction", {}).get("weight_overrides")
    )

    domain_results = compute_all_domains(
        connector_data=domain_inputs,
        jurisdiction_config=jconfig,
        profile=profile,
    )
    domain_scores = {k: v.get("score", 0.0) for k, v in domain_results.items()}
    domain_components = {k: v.get("components", {}) for k, v in domain_results.items()}

    total_score, _ = calculate_phrat(domain_scores, weights)
    risk_classification = classify_risk(total_score)
    risk_level = risk_classification.get('label', 'Unknown')
    risk_class = risk_classification.get('color_class', _risk_level_to_class(risk_level))

    available_connectors = [
        name for name, connector in registry.get_all_available().items()
    ]
    data_coverage = (
        len(available_connectors) / max(len(weights), 1)
        if weights else 0.0
    )

    return {
        "jurisdiction_id": jurisdiction_id,
        "profile": profile,
        "computed_at": datetime.utcnow().isoformat(),
        "total_score": round(total_score, 4),
        "risk_level": risk_level,
        "risk_class": risk_class,
        "domain_scores": {k: round(v, 4) for k, v in domain_scores.items()},
        "domain_components": domain_components,
        "data_sources_used": available_connectors,
        "data_coverage": round(min(data_coverage, 1.0), 3),
    }


def get_all_jurisdictions_summary(top_n: Optional[int] = None) -> List[Dict[str, Any]]:
    """
    Return a summary list of all jurisdictions with their cached or computed scores.

    If cached scores exist in the DB, they are returned directly.
    Otherwise returns jurisdictions with null scores (lazy evaluation).
    """
    from utils.geography.jurisdiction_manager import JurisdictionManager

    manager = JurisdictionManager()
    jurisdictions = manager.get_all()

    try:
        from app import db
        from models import JurisdictionCache

        cached = {
            row.jurisdiction_id: row
            for row in db.session.query(JurisdictionCache).all()
        }
    except Exception:
        cached = {}

    result = []
    for j in jurisdictions:
        jid = j["id"]
        row = cached.get(jid)
        result.append({
            "id": jid,
            "name": j.get("name", jid),
            "population": j.get("population", 0),
            "total_score": row.total_score if row else None,
            "risk_level": row.risk_level if row else None,
            "computed_at": row.computed_at.isoformat() if row and row.computed_at else None,
        })

    result.sort(key=lambda x: (x["total_score"] is None, -(x["total_score"] or 0)))
    return result[:top_n] if top_n else result


def cache_result(result: Dict[str, Any]) -> None:
    """Persist a compute_risk_for_jurisdiction result to the DB cache."""
    try:
        from app import db
        from models import JurisdictionCache

        jid = result["jurisdiction_id"]
        existing = (
            db.session.query(JurisdictionCache)
            .filter_by(jurisdiction_id=jid)
            .first()
        )
        if existing:
            existing.computed_at = datetime.utcnow()
            existing.total_score = result["total_score"]
            existing.risk_level = result["risk_level"]
            existing.domain_scores = result["domain_scores"]
            existing.domain_components = result["domain_components"]
            existing.data_sources_used = result["data_sources_used"]
            existing.data_coverage = result["data_coverage"]
            existing.profile = result["profile"]
        else:
            row = JurisdictionCache(
                jurisdiction_id=jid,
                profile=result["profile"],
                total_score=result["total_score"],
                risk_level=result["risk_level"],
                domain_scores=result["domain_scores"],
                domain_components=result["domain_components"],
                data_sources_used=result["data_sources_used"],
                data_coverage=result["data_coverage"],
            )
            db.session.add(row)
        db.session.commit()
    except Exception as e:
        logger.error(f"Failed to cache result for {result.get('jurisdiction_id')}: {e}")


def get_cached_result(jurisdiction_id: str,
                      max_age_hours: float = 4.0) -> Optional[Dict[str, Any]]:
    """
    Return a cached result if it exists and is not older than max_age_hours.
    Returns None if no valid cache entry exists.
    """
    try:
        from app import db
        from models import JurisdictionCache
        from datetime import timedelta

        cutoff = datetime.utcnow() - timedelta(hours=max_age_hours)
        row = (
            db.session.query(JurisdictionCache)
            .filter(
                JurisdictionCache.jurisdiction_id == jurisdiction_id,
                JurisdictionCache.computed_at >= cutoff,
            )
            .first()
        )
        if not row:
            return None
        return {
            "jurisdiction_id": row.jurisdiction_id,
            "profile": row.profile,
            "computed_at": row.computed_at.isoformat(),
            "total_score": row.total_score,
            "risk_level": row.risk_level,
            "risk_class": _risk_level_to_class(row.risk_level),
            "domain_scores": row.domain_scores or {},
            "domain_components": row.domain_components or {},
            "data_sources_used": row.data_sources_used or [],
            "data_coverage": row.data_coverage or 0.0,
        }
    except Exception as e:
        logger.error(f"Cache lookup failed for {jurisdiction_id}: {e}")
        return None


def _gather_domain_inputs(registry: ConnectorRegistry,
                          jurisdiction_id: str,
                          jconfig: Dict[str, Any]) -> Dict[str, Any]:
    """
    Fetch data from all available connectors and return as a domain_inputs dict.
    Keys are connector names; values are the raw fetch() result dicts.
    """
    domain_inputs: Dict[str, Any] = {}
    for name, connector in registry.get_all_available().items():
        try:
            data = connector.fetch(jurisdiction_id=jurisdiction_id)
            domain_inputs[name] = data
            logger.debug(f"Connector '{name}' fetched data (available={data.get('available')})")
        except Exception as e:
            logger.warning(f"Connector '{name}' fetch failed: {e}")
            domain_inputs[name] = {"available": False, "error": str(e)}
    return domain_inputs


def _risk_level_to_class(risk_level: Optional[str]) -> str:
    mapping = {
        "Critical": "danger",
        "High": "warning",
        "Moderate": "info",
        "Low": "success",
        "Minimal": "success",
    }
    return mapping.get(risk_level or "", "secondary")
