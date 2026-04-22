"""
CARA Risk Engine — PHRAT quadratic mean formula.

This module is the authoritative risk scoring engine for the CARA template.
It accepts pre-computed domain scores and applies the PHRAT formula:

    Total = sqrt( sum( weight_i * score_i^2 ) )

where all weights sum to 1.0 and all scores are on [0, 1].

Domain scores come from domain modules in utils/domains/. The risk engine
itself does not fetch any data — it only aggregates scores that have already
been computed by domain objects.

This design ensures that:
- The scoring formula is consistent regardless of which connectors are active
- Domain scores can be computed independently and combined in any order
- The engine can be unit-tested without any network calls
"""

import logging
import math
import yaml
import os
from typing import Any, Dict, List, Optional, Tuple

logger = logging.getLogger(__name__)

WEIGHTS_CONFIG_PATH = os.path.join('config', 'risk_weights.yaml')


def load_weights(profile: str, jurisdiction_overrides: Optional[Dict] = None) -> Dict[str, float]:
    """
    Load domain weights for the given profile.

    Args:
        profile: 'us_state' or 'international'
        jurisdiction_overrides: Optional weight overrides from jurisdiction.yaml

    Returns:
        Dict of domain_id -> weight, guaranteed to sum to 1.0
    """
    try:
        with open(WEIGHTS_CONFIG_PATH, 'r') as f:
            weights_config = yaml.safe_load(f) or {}
    except Exception as e:
        logger.error(f"Failed to load weights config: {e}")
        weights_config = {}

    raw = weights_config.get('profiles', {}).get(profile, {})
    # Filter to numeric values only — the config may contain documentation strings
    # or null placeholders (e.g. in the custom profile section).
    weights = {
        k: float(v) for k, v in raw.items()
        if isinstance(v, (int, float)) and v is not None
    }

    if jurisdiction_overrides:
        for domain, weight in jurisdiction_overrides.items():
            if weight is not None:
                weights[domain] = float(weight)

    total = sum(weights.values())
    if total > 0 and abs(total - 1.0) > 0.001:
        logger.warning(f"Domain weights sum to {total:.4f}, normalizing to 1.0")
        weights = {k: v / total for k, v in weights.items()}

    return weights


def calculate_phrat(
    domain_scores: Dict[str, float],
    weights: Dict[str, float],
) -> Tuple[float, Dict[str, Any]]:
    """
    Compute the PHRAT composite risk score.

    Args:
        domain_scores: Dict of domain_id -> score [0, 1]
        weights: Dict of domain_id -> weight (must sum to 1.0)

    Returns:
        Tuple of:
            - total_score: float [0, 1]
            - breakdown: Dict with per-domain contribution details
    """
    contributions = {}
    sum_weighted_sq = 0.0
    total_weight_used = 0.0

    for domain_id, weight in weights.items():
        score = domain_scores.get(domain_id)
        if score is None:
            contributions[domain_id] = {
                'score': None,
                'weight': weight,
                'weighted_sq': 0.0,
                'contribution_pct': 0.0,
                'available': False,
            }
            continue

        score = max(0.0, min(1.0, float(score)))
        weighted_sq = weight * score ** 2
        sum_weighted_sq += weighted_sq
        total_weight_used += weight

        contributions[domain_id] = {
            'score': round(score, 4),
            'weight': weight,
            'weighted_sq': round(weighted_sq, 6),
            'available': True,
        }

    if sum_weighted_sq > 0:
        raw_phrat = math.sqrt(sum_weighted_sq)
    else:
        raw_phrat = 0.0

    if total_weight_used < 1.0 and total_weight_used > 0:
        scale_factor = math.sqrt(1.0 / total_weight_used)
        adjusted_phrat = raw_phrat * scale_factor
    else:
        adjusted_phrat = raw_phrat

    total_score = round(min(1.0, adjusted_phrat), 4)

    for domain_id, detail in contributions.items():
        if detail.get('available') and total_score > 0:
            detail['contribution_pct'] = round(
                detail['weighted_sq'] / (total_score ** 2) * 100, 1
            )
        else:
            detail['contribution_pct'] = 0.0

    return total_score, {
        'total': total_score,
        'domains': contributions,
        'data_coverage': round(total_weight_used, 4),
        'formula': 'phrat_quadratic_mean',
    }


def classify_risk(score: float) -> Dict[str, str]:
    """
    Classify a risk score into a named category with color coding.

    Returns:
        Dict with 'level', 'label', 'color', 'description'
    """
    thresholds = [
        (0.75, 'critical', 'Critical',   '#8B0000', 'Immediate action required'),
        (0.55, 'high',     'High',        '#CC3300', 'Priority planning and response'),
        (0.35, 'moderate', 'Moderate',    '#FF8800', 'Enhanced monitoring and preparation'),
        (0.15, 'low',      'Low',         '#FFD700', 'Standard preparedness activities'),
        (0.0,  'minimal',  'Minimal',     '#336633', 'Maintain baseline surveillance'),
    ]
    for threshold, level, label, color, description in thresholds:
        if score >= threshold:
            return {
                'level': level,
                'label': label,
                'color': color,
                'description': description,
            }
    return {'level': 'minimal', 'label': 'Minimal', 'color': '#336633',
            'description': 'Maintain baseline surveillance'}


def compute_all_domains(
    connector_data: Dict[str, Any],
    jurisdiction_config: Dict[str, Any],
    profile: str,
    enabled_domains: Optional[List[str]] = None,
) -> Dict[str, Any]:
    """
    Run all enabled domain calculations and return scores + breakdowns.

    Args:
        connector_data: Dict of connector_name -> connector result
        jurisdiction_config: Jurisdiction configuration dict
        profile: 'us_state' or 'international'
        enabled_domains: Optional list of domain IDs to run; defaults to all

    Returns:
        Dict of domain_id -> domain result dict (includes 'score', 'components', etc.)
    """
    from utils.domains.conflict_displacement import ConflictDisplacementDomain
    from utils.domains.mass_casualty import MassCasualtyDomain

    all_domain_classes = {
        'conflict_displacement': ConflictDisplacementDomain,
        'mass_casualty': MassCasualtyDomain,
    }

    try:
        from utils.domains.natural_hazards import NaturalHazardsDomain
        all_domain_classes['natural_hazards'] = NaturalHazardsDomain
    except ImportError:
        pass

    try:
        from utils.domains.health_metrics import HealthMetricsDomain
        all_domain_classes['health_metrics'] = HealthMetricsDomain
    except ImportError:
        pass

    try:
        from utils.domains.air_quality import AirQualityDomain
        all_domain_classes['air_quality'] = AirQualityDomain
    except ImportError:
        pass

    try:
        from utils.domains.extreme_heat import ExtremeHeatDomain
        all_domain_classes['extreme_heat'] = ExtremeHeatDomain
    except ImportError:
        pass

    try:
        from utils.domains.vector_borne_disease import VectorBorneDiseaseDomain
        all_domain_classes['vector_borne_disease'] = VectorBorneDiseaseDomain
    except ImportError:
        pass

    try:
        from utils.domains.dam_failure import DamFailureDomain
        all_domain_classes['dam_failure'] = DamFailureDomain
    except ImportError:
        pass

    if enabled_domains is None:
        enabled_domains = list(all_domain_classes.keys())

    results = {}
    for domain_id in enabled_domains:
        domain_class = all_domain_classes.get(domain_id)
        if not domain_class:
            logger.debug(f"Domain not found: {domain_id}")
            continue
        try:
            domain = domain_class()
            results[domain_id] = domain.calculate(
                connector_data=connector_data,
                jurisdiction_config=jurisdiction_config,
                profile=profile,
            )
        except Exception as e:
            logger.error(f"Domain {domain_id} failed: {e}")
            results[domain_id] = {'score': 0.0, 'available': False, 'error': str(e)}

    return results
