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


# ---------------------------------------------------------------------------
# Compatibility shims for Wisconsin-specific route imports
# ---------------------------------------------------------------------------

def get_wi_jurisdictions() -> List[Dict[str, Any]]:
    """Return a list of jurisdiction dicts with 'id' and 'name' keys."""
    try:
        summary = get_all_jurisdictions_summary()
        return [{"id": j["id"], "name": j["name"]} for j in summary]
    except Exception as e:
        logger.error(f"get_wi_jurisdictions failed: {e}")
        return []


def process_risk_data(jurisdiction_id: str, **kwargs) -> Dict[str, Any]:
    """
    Compute risk data for a jurisdiction and return in legacy format.

    Tries a cached result first; falls back to a fresh computation.
    Maps the new pipeline output keys to the fields expected by older routes.
    """
    cached = get_cached_result(jurisdiction_id)
    if cached:
        result = cached
    else:
        try:
            result = compute_risk_for_jurisdiction(jurisdiction_id)
            cache_result(result)
        except Exception as e:
            logger.error(f"process_risk_data failed for {jurisdiction_id}: {e}")
            return {}

    domain_scores = result.get("domain_scores", {})
    jconfig = {}
    try:
        from utils.connector_registry import load_jurisdiction_config
        jconfig = load_jurisdiction_config()
    except Exception:
        pass
    jinfo = jconfig.get("jurisdiction", {})

    natural_hazards_risk = domain_scores.get(
        "natural_hazards", domain_scores.get("hazards", 0.0)
    )
    health_risk = domain_scores.get(
        "health", domain_scores.get("infectious_disease", 0.0)
    )
    active_shooter_risk = domain_scores.get(
        "active_shooter", domain_scores.get("violence", 0.0)
    )
    total_risk_score = result.get("total_score", 0.0)

    return {
        "jurisdiction_id": jurisdiction_id,
        "location": jinfo.get("name", jurisdiction_id),
        "county": jinfo.get("name", jurisdiction_id),
        "county_name": jinfo.get("name", jurisdiction_id),
        "total_risk_score": total_risk_score,
        "risk_level": result.get("risk_level", "Unknown"),
        "risk_class": result.get("risk_class", "secondary"),
        "natural_hazards_risk": natural_hazards_risk,
        "health_risk": health_risk,
        "active_shooter_risk": active_shooter_risk,
        "natural_hazards": {k: v for k, v in domain_scores.items()},
        "domain_scores": domain_scores,
        "domain_components": result.get("domain_components", {}),
        "data_sources_used": result.get("data_sources_used", []),
        "data_coverage": result.get("data_coverage", 0.0),
        "profile": result.get("profile", ""),
        "computed_at": result.get("computed_at", ""),
    }


def get_historical_risk_data(jurisdiction_id: str,
                             start_year: int = 2020,
                             end_year: int = 2024) -> List[Dict[str, Any]]:
    """
    Return a list of historical risk data points for a jurisdiction.

    This implementation returns a single-point snapshot of the current risk
    scores because the generic template does not maintain a historical
    time-series database.
    """
    try:
        risk = process_risk_data(jurisdiction_id)
        if not risk:
            return []
        from datetime import datetime as _dt
        current_year = _dt.now().year
        return [{
            "year": current_year,
            "total_risk_score": risk.get("total_risk_score", 0.0),
            "natural_hazards_risk": risk.get("natural_hazards_risk", 0.0),
            "health_risk": risk.get("health_risk", 0.0),
            "active_shooter_risk": risk.get("active_shooter_risk", 0.0),
        }]
    except Exception as e:
        logger.error(f"get_historical_risk_data failed for {jurisdiction_id}: {e}")
        return []


def get_em_jurisdictions() -> List[Dict[str, Any]]:
    """Alias for get_wi_jurisdictions for EM comparison exports."""
    return get_wi_jurisdictions()


def get_county_for_jurisdiction(jurisdiction_id: str) -> str:
    """Return a county name string for a given jurisdiction ID."""
    try:
        jconfig = load_jurisdiction_config()
        subdivisions = jconfig.get("jurisdiction", {}).get("subdivisions", [])
        for sub in subdivisions:
            if str(sub.get("id")) == str(jurisdiction_id):
                return sub.get("name", jurisdiction_id)
    except Exception:
        pass
    return jurisdiction_id


def load_nri_data() -> Dict[str, Any]:
    """Return National Risk Index data keyed by county name. Stub — populate with real NRI data."""
    return {}


def get_mobile_home_percentage(county_name: str) -> Optional[float]:
    """Return mobile home percentage for a county. Stub — populate with real data."""
    return None


def get_elderly_population_pct(county_name: str) -> Optional[float]:
    """Return elderly population percentage for a county. Stub — populate with real data."""
    return None
