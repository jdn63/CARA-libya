"""
CARA Risk Engine — INFORM Risk Index formula.

This module implements the INFORM (Index for Risk Management) Risk Index formula
for the Libya CARA deployment:

    INFORM_Risk = (Hazard_Exposure × Vulnerability × Coping_Capacity_Gap) ^ (1/3)

Each pillar is a weighted mean of its sub-indicators, scored on [0, 1].
A score of 1.0 represents maximum risk; 0.0 represents no measurable risk.

The INFORM formula was developed by the Inter-Agency Standing Committee (IASC)
and the European Commission Joint Research Centre (JRC). See:
https://drmkc.jrc.ec.europa.eu/inform-index

PHRAT formula (original Wisconsin template):
The original PHRAT quadratic mean formula is retained for non-Libya profiles
(us_state, international) for backward compatibility. The Libya profile
exclusively uses INFORM.

Sendai Framework alignment:
- Priority 1 (Understanding risk): Hazard & Exposure + Vulnerability
- Priority 2 (Governance):         Coping Capacity
- Priority 3 (Investment in DRR):  Coping Capacity: institutional_capacity
- Priority 4 (Preparedness):       Coping Capacity: emergency_response
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

    For the 'libya' profile, returns the INFORM pillar weights.
    For 'us_state' and 'international' profiles, returns PHRAT domain weights.

    Args:
        profile: 'libya', 'us_state', or 'international'
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

    if profile == 'libya':
        weights = {
            'hazard_exposure': float(raw.get('hazard_exposure', {}).get('weight', 0.333)),
            'vulnerability':   float(raw.get('vulnerability', {}).get('weight', 0.333)),
            'coping_capacity': float(raw.get('coping_capacity', {}).get('weight', 0.333)),
        }
    else:
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


def calculate_inform(
    pillar_scores: Dict[str, Optional[float]],
) -> Tuple[float, Dict[str, Any]]:
    """
    Compute the INFORM composite risk score.

    The INFORM formula uses a geometric mean of three pillars:
        INFORM = (H × V × CC) ^ (1/3)

    where H = Hazard & Exposure, V = Vulnerability, CC = Lack of Coping Capacity,
    each scored on [0, 1].

    Partial data handling: When a pillar score is unavailable (None), the tool
    substitutes the mean of available pillars with explicit documentation.
    This follows the INFORM methodology guidance for data-sparse contexts.

    Args:
        pillar_scores: Dict with keys 'hazard_exposure', 'vulnerability',
                       'coping_capacity', each mapped to float [0,1] or None.

    Returns:
        Tuple of:
            - total_score: float [0, 1]
            - breakdown: Dict with pillar details and formula metadata
    """
    h = pillar_scores.get('hazard_exposure')
    v = pillar_scores.get('vulnerability')
    c = pillar_scores.get('coping_capacity')

    available_pillars = {k: val for k, val in pillar_scores.items() if val is not None}
    missing_pillars = [k for k, val in pillar_scores.items() if val is None]

    proxy_notes = []
    if missing_pillars:
        if available_pillars:
            proxy_value = sum(available_pillars.values()) / len(available_pillars)
            logger.warning(
                f"INFORM: Missing pillar(s) {missing_pillars}. "
                f"Substituting proxy value {proxy_value:.3f} (mean of available pillars). "
                f"Per Libya CARA missing-data policy."
            )
            if h is None:
                h = proxy_value
                proxy_notes.append(f"hazard_exposure substituted with regional proxy {proxy_value:.3f}")
            if v is None:
                v = proxy_value
                proxy_notes.append(f"vulnerability substituted with regional proxy {proxy_value:.3f}")
            if c is None:
                c = proxy_value
                proxy_notes.append(f"coping_capacity substituted with regional proxy {proxy_value:.3f}")
        else:
            return 0.0, {
                'total': 0.0,
                'pillars': {},
                'available': False,
                'formula': 'inform_geometric_mean',
                'note': 'No pillar data available for any INFORM pillar.',
            }

    h = max(0.0, min(1.0, float(h)))
    v = max(0.0, min(1.0, float(v)))
    c = max(0.0, min(1.0, float(c)))

    if h == 0.0 or v == 0.0 or c == 0.0:
        product = 0.0
        total_score = 0.0
    else:
        product = h * v * c
        total_score = round(product ** (1.0 / 3.0), 4)

    breakdown = {
        'total': total_score,
        'pillars': {
            'hazard_exposure': {
                'score': round(h, 4),
                'label_ar': 'المخاطر والتعرض',
                'label_en': 'Hazard & Exposure',
                'available': pillar_scores.get('hazard_exposure') is not None,
            },
            'vulnerability': {
                'score': round(v, 4),
                'label_ar': 'الهشاشة',
                'label_en': 'Vulnerability',
                'available': pillar_scores.get('vulnerability') is not None,
            },
            'coping_capacity': {
                'score': round(c, 4),
                'label_ar': 'القدرة على المواجهة (العكسية)',
                'label_en': 'Lack of Coping Capacity',
                'available': pillar_scores.get('coping_capacity') is not None,
            },
        },
        'formula': 'inform_geometric_mean',
        'formula_string': f'({h:.4f} × {v:.4f} × {c:.4f}) ^ (1/3) = {total_score:.4f}',
        'sendai_aligned': True,
        'data_coverage': len(available_pillars) / 3.0,
        'proxy_substitutions': proxy_notes,
    }

    return total_score, breakdown


def calculate_phrat(
    domain_scores: Dict[str, float],
    weights: Dict[str, float],
) -> Tuple[float, Dict[str, Any]]:
    """
    Compute the PHRAT composite risk score (retained for us_state / international profiles).

    Formula: Total = sqrt( sum( weight_i * score_i^2 ) )

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
    Classify a risk score [0,1] into a named category with bilingual labels and color coding.

    Returns:
        Dict with 'level', 'label_ar', 'label_en', 'color', 'description_ar', 'description_en'
    """
    thresholds = [
        (0.75, 'critical', 'بالغ الخطورة', 'Critical',
         '#8B0000', 'إجراء فوري مطلوب', 'Immediate action required'),
        (0.55, 'high',     'مرتفع',        'High',
         '#CC3300', 'تخطيط ذو أولوية واستجابة', 'Priority planning and response'),
        (0.35, 'moderate', 'متوسط',        'Moderate',
         '#FF8800', 'رصد معزز وتأهب',   'Enhanced monitoring and preparation'),
        (0.15, 'low',      'منخفض',        'Low',
         '#FFD700', 'أنشطة التأهب القياسية', 'Standard preparedness activities'),
        (0.0,  'minimal',  'ضئيل',         'Minimal',
         '#336633', 'الحفاظ على المراقبة الأساسية', 'Maintain baseline surveillance'),
    ]
    for threshold, level, label_ar, label_en, color, desc_ar, desc_en in thresholds:
        if score >= threshold:
            return {
                'level': level,
                'label': label_en,          # backward-compat alias
                'label_ar': label_ar,
                'label_en': label_en,
                'color': color,
                'description': desc_en,     # backward-compat alias
                'description_ar': desc_ar,
                'description_en': desc_en,
            }
    return {
        'level': 'minimal',
        'label': 'Minimal',
        'label_ar': 'ضئيل',
        'label_en': 'Minimal',
        'color': '#336633',
        'description': 'Maintain baseline surveillance',
        'description_ar': 'الحفاظ على المراقبة الأساسية',
        'description_en': 'Maintain baseline surveillance',
    }


def compute_all_domains(
    connector_data: Dict[str, Any],
    jurisdiction_config: Dict[str, Any],
    profile: str,
    enabled_domains: Optional[List[str]] = None,
) -> Dict[str, Any]:
    """
    Run all enabled domain calculations and return scores + breakdowns.

    For the 'libya' profile, runs the three INFORM pillars.
    For other profiles, falls back to the original domain set.

    Args:
        connector_data: Dict of connector_name -> connector result
        jurisdiction_config: Jurisdiction configuration dict
        profile: 'libya', 'us_state', or 'international'
        enabled_domains: Optional list of domain IDs to run; defaults to all

    Returns:
        Dict of domain_id -> domain result dict (includes 'score', 'components', etc.)
    """
    if profile == 'libya':
        return _compute_libya_domains(connector_data, jurisdiction_config, enabled_domains)

    from utils.domains.conflict_displacement import ConflictDisplacementDomain
    from utils.domains.mass_casualty import MassCasualtyDomain

    all_domain_classes = {
        'conflict_displacement': ConflictDisplacementDomain,
        'mass_casualty': MassCasualtyDomain,
    }

    for mod_name, class_name, domain_id in [
        ('natural_hazards', 'NaturalHazardsDomain', 'natural_hazards'),
        ('health_metrics', 'HealthMetricsDomain', 'health_metrics'),
        ('air_quality', 'AirQualityDomain', 'air_quality'),
        ('extreme_heat', 'ExtremeHeatDomain', 'extreme_heat'),
        ('vector_borne_disease', 'VectorBorneDiseaseDomain', 'vector_borne_disease'),
        ('dam_failure', 'DamFailureDomain', 'dam_failure'),
    ]:
        try:
            mod = __import__(f'utils.domains.{mod_name}', fromlist=[class_name])
            all_domain_classes[domain_id] = getattr(mod, class_name)
        except (ImportError, AttributeError):
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


def _compute_libya_domains(
    connector_data: Dict[str, Any],
    jurisdiction_config: Dict[str, Any],
    enabled_domains: Optional[List[str]],
) -> Dict[str, Any]:
    """
    Run the three INFORM pillar domain calculations for the Libya profile.
    """
    from utils.domains.hazard_exposure import HazardExposureDomain
    from utils.domains.vulnerability import VulnerabilityDomain
    from utils.domains.coping_capacity import CopingCapacityDomain

    all_domain_classes = {
        'hazard_exposure': HazardExposureDomain,
        'vulnerability':   VulnerabilityDomain,
        'coping_capacity': CopingCapacityDomain,
    }

    if enabled_domains is None:
        enabled_domains = list(all_domain_classes.keys())

    results = {}
    for domain_id in enabled_domains:
        domain_class = all_domain_classes.get(domain_id)
        if not domain_class:
            continue
        try:
            domain = domain_class()
            results[domain_id] = domain.calculate(
                connector_data=connector_data,
                jurisdiction_config=jurisdiction_config,
                profile='libya',
            )
        except Exception as e:
            logger.error(f"Libya domain {domain_id} failed: {e}")
            results[domain_id] = {'score': 0.0, 'available': False, 'error': str(e)}

    return results
