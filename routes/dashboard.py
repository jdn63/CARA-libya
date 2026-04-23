"""
Dashboard routes for Libya CARA.

Handles:
  /dashboard/<jurisdiction_id>   — INFORM risk assessment for a municipality or 'LY' (national)
"""

import logging
from datetime import datetime
from flask import Blueprint, render_template, redirect, url_for

from utils.geography.jurisdiction_manager import JurisdictionManager
from utils.domains.hazard_exposure import HazardExposureDomain
from utils.domains.vulnerability import VulnerabilityDomain
from utils.domains.coping_capacity import CopingCapacityDomain

logger = logging.getLogger(__name__)

dashboard_bp = Blueprint('dashboard', __name__)

_jm = None


def _get_jm() -> JurisdictionManager:
    global _jm
    if _jm is None:
        _jm = JurisdictionManager()
    return _jm


def _compute_inform_score(h: float, v: float, c: float) -> float:
    """Geometric mean of the three INFORM pillars."""
    return round((h * v * c) ** (1 / 3), 4)


def _score_to_level(score) -> str:
    if score is None:
        return 'unavailable'
    try:
        score = float(score)
    except (TypeError, ValueError):
        return 'unavailable'
    if score >= 0.75:
        return 'critical'
    if score >= 0.55:
        return 'high'
    if score >= 0.35:
        return 'moderate'
    if score >= 0.15:
        return 'low'
    return 'minimal'


LEVEL_LABELS_AR = {
    'critical':    'بالغ الخطورة',
    'high':        'مرتفع',
    'moderate':    'متوسط',
    'low':         'منخفض',
    'minimal':     'ضئيل',
    'unavailable': 'البيانات غير متاحة',
}

LEVEL_LABELS_EN = {
    'critical':    'Critical',
    'high':        'High',
    'moderate':    'Moderate',
    'low':         'Low',
    'minimal':     'Minimal',
    'unavailable': 'Data Not Available',
}


def _run_pillars(jurisdiction_id: str, jurisdiction_config: dict) -> dict:
    """
    Run all three INFORM pillars and return a structured result dict.

    Returns a dict with keys: hazard, vulnerability, coping, inform_score, all_unavailable
    Each pillar dict contains: score, level, label_ar, label_en, available, components, confidence
    """
    connector_data = {}  # Real connectors will populate this; stubs return unavailable
    profile = 'libya'

    results = {}
    available_scores = []

    for pillar_key, DomainClass in [
        ('hazard',        HazardExposureDomain),
        ('vulnerability', VulnerabilityDomain),
        ('coping',        CopingCapacityDomain),
    ]:
        try:
            domain = DomainClass()
            raw = domain.calculate(connector_data, jurisdiction_config, profile)
            score = raw.get('score')
            available = raw.get('available', False)
            if available and score is not None:
                available_scores.append(float(score))
            results[pillar_key] = {
                'score':      round(float(score), 4) if score is not None else None,
                'available':  available,
                'confidence': raw.get('confidence', 0.0),
                'components': raw.get('components', {}),
                'dominant':   raw.get('dominant_factor', ''),
                'data_sources': raw.get('data_sources', []),
                'level':      _score_to_level(score if available else None),
                'label_ar':   LEVEL_LABELS_AR[_score_to_level(score if available else None)],
                'label_en':   LEVEL_LABELS_EN[_score_to_level(score if available else None)],
            }
        except Exception as e:
            logger.error(f"Pillar {pillar_key} failed for {jurisdiction_id}: {e}")
            results[pillar_key] = {
                'score': None, 'available': False, 'confidence': 0.0,
                'components': {}, 'dominant': '', 'data_sources': [],
                'level': 'unavailable',
                'label_ar': LEVEL_LABELS_AR['unavailable'],
                'label_en': LEVEL_LABELS_EN['unavailable'],
            }

    # INFORM overall score — only if all three pillars have real data
    h = results['hazard']
    v = results['vulnerability']
    c = results['coping']

    if h['available'] and v['available'] and c['available']:
        inform_score = _compute_inform_score(h['score'], v['score'], c['score'])
        inform_level = _score_to_level(inform_score)
        results['inform_score'] = {
            'score': inform_score,
            'available': True,
            'level': inform_level,
            'label_ar': LEVEL_LABELS_AR[inform_level],
            'label_en': LEVEL_LABELS_EN[inform_level],
        }
    elif available_scores:
        # Partial proxy: geometric mean of available pillars (documented)
        proxy = round(sum(available_scores) / len(available_scores), 4)
        inform_level = _score_to_level(proxy)
        results['inform_score'] = {
            'score': proxy,
            'available': False,  # marks as proxy
            'proxy': True,
            'pillars_available': len(available_scores),
            'level': inform_level,
            'label_ar': LEVEL_LABELS_AR[inform_level],
            'label_en': LEVEL_LABELS_EN[inform_level],
        }
    else:
        results['inform_score'] = {
            'score': None, 'available': False, 'proxy': False,
            'level': 'unavailable',
            'label_ar': LEVEL_LABELS_AR['unavailable'],
            'label_en': LEVEL_LABELS_EN['unavailable'],
        }

    results['all_unavailable'] = not any(
        results[k]['available'] for k in ('hazard', 'vulnerability', 'coping')
    )

    return results


@dashboard_bp.route('/dashboard/<jurisdiction_id>')
def dashboard(jurisdiction_id):
    """INFORM risk dashboard for a Libya municipality or the national assessment."""
    try:
        jm = _get_jm()

        # National assessment
        if jurisdiction_id.upper() in ('LY', 'LIBYA', 'LY-NATIONAL'):
            jurisdiction = {
                'id': 'LY',
                'name_ar': 'ليبيا — التقييم الوطني',
                'name_en': 'Libya — National Assessment',
                'level': 1,
                'population': 6931000,
                'region': '',
                'district': '',
            }
            jurisdiction_config = jm.get_country_config()
            is_national = True
        else:
            jurisdiction = jm.get_by_id(jurisdiction_id)
            if not jurisdiction:
                logger.warning(f"Municipality not found: {jurisdiction_id}")
                return render_template(
                    'error.html',
                    message=f"البلدية غير موجودة / Municipality not found: {jurisdiction_id}"
                )
            jurisdiction_config = jm.get_country_config()
            is_national = False

        pillar_data = _run_pillars(jurisdiction_id, jurisdiction_config)

        return render_template(
            'dashboard.html',
            jurisdiction=jurisdiction,
            is_national=is_national,
            pillar_data=pillar_data,
            now=datetime.utcnow(),
            level_labels_ar=LEVEL_LABELS_AR,
            level_labels_en=LEVEL_LABELS_EN,
        )

    except Exception as e:
        logger.error(f"Dashboard error for {jurisdiction_id}: {e}", exc_info=True)
        return render_template(
            'error.html',
            message="حدث خطأ أثناء تحميل التقييم. / An error occurred loading the assessment."
        )
