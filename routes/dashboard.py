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


def _level_badge(level: str) -> str:
    return {
        'critical':    'danger',
        'high':        'danger',
        'moderate':    'warning',
        'low':         'info',
        'minimal':     'success',
        'unavailable': 'secondary',
    }.get(level, 'secondary')


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


# ---------------------------------------------------------------------------
# Connector data loading — cache-first, never blocks on network
# ---------------------------------------------------------------------------

def _load_connector_data(jurisdiction_id: str) -> dict:
    """
    Load fresh indicator data from all available connectors.
    Each connector reads from its local disk cache — no network calls.
    Normalises key names so domain modules (which expect legacy schema keys)
    receive the correct values.
    """
    data = {}

    # WHO Libya via OCHA HDX — primary health indicator source
    try:
        from utils.connectors.worldwide.who_hdx_connector import WHOHDXConnector
        c = WHOHDXConnector()
        raw = c.fetch(jurisdiction_id)
        beds_10k = raw.get('hospital_beds_per_10k')
        who_norm = {}
        if beds_10k is not None:
            who_norm['hospital_beds_per_1000'] = round(beds_10k / 10.0, 3)
            who_norm['hospital_beds_per_10k']  = beds_10k
        for key_src, key_dst in [
            ('measles_vaccination_pct',       'measles_vaccination_coverage'),
            ('under5_mortality_rate',          'under5_mortality_rate'),
            ('tb_incidence_per_100k',          'tb_incidence_per_100k'),
            ('ncd_mortality_30_70_pct',        'ncd_mortality_30_70_pct'),
            ('air_pollution_mortality_per_100k','air_pollution_mortality_per_100k'),
            ('pm25_annual_mean_ugm3',          'pm25_annual_mean_ugm3'),
            ('neonatal_mortality_rate',         'neonatal_mortality_rate'),
            ('infant_mortality_rate',           'infant_mortality_rate'),
            ('stunting_prevalence_pct',         'stunting_prevalence_pct'),
            ('obesity_prevalence_pct',          'obesity_prevalence_pct'),
            ('tb_treatment_coverage_pct',       'tb_treatment_coverage_pct'),
            ('tb_treatment_success_pct',        'tb_treatment_success_pct'),
            ('anaemia_children_prevalence_pct', 'anaemia_children_prevalence_pct'),
        ]:
            v = raw.get(key_src)
            if v is not None:
                who_norm[key_dst] = v
        # Preserve year metadata for popovers
        for k in list(raw.keys()):
            if k.endswith('_year') or k.endswith('_label_en') or k.endswith('_label_ar'):
                who_norm[k] = raw[k]
        data['who_gho'] = who_norm
        data['who_hdx_raw'] = raw
    except Exception as e:
        logger.warning(f'WHO HDX load failed for {jurisdiction_id}: {e}')

    # IDMC displacement via OCHA HDX
    try:
        from utils.connectors.worldwide.idmc_hdx_connector import IDMCHDXConnector
        c = IDMCHDXConnector()
        raw = c.fetch(jurisdiction_id)
        idmc_norm = {}
        stock = raw.get('total_displacement_stock')
        if stock is not None:
            idmc_norm['total_idps']   = stock
            idmc_norm['idp_stock']    = stock
        new_c = raw.get('new_displacements_conflict')
        if new_c is not None:
            idmc_norm['new_conflict_displacements'] = new_c
        data['idmc']      = idmc_norm
        data['idmc_raw']  = raw
    except Exception as e:
        logger.warning(f'IDMC HDX load failed for {jurisdiction_id}: {e}')

    # HeiGIT accessibility — district-level access scores
    try:
        from utils.connectors.worldwide.heigit_connector import HeiGITAccessibilityConnector
        c = HeiGITAccessibilityConnector()
        raw = c.fetch(jurisdiction_id)
        data['heigit'] = raw
    except Exception as e:
        logger.warning(f'HeiGIT load failed for {jurisdiction_id}: {e}')

    # IOM DTM displacement
    try:
        from utils.connectors.worldwide.iom_connector import IOMConnector
        c = IOMConnector()
        raw = c.fetch(jurisdiction_id)
        if raw.get('available'):
            data['iom'] = raw
    except Exception as e:
        logger.warning(f'IOM load failed for {jurisdiction_id}: {e}')

    # World Bank
    try:
        from utils.connectors.worldwide.worldbank_connector import WorldBankConnector
        c = WorldBankConnector(country_code='LY')
        raw = c.fetch(jurisdiction_id)
        if raw.get('available'):
            data['worldbank'] = raw
    except Exception as e:
        logger.warning(f'WorldBank load failed for {jurisdiction_id}: {e}')

    # COI Libya (manual upload — typically unavailable until uploaded)
    try:
        from utils.connectors.libya.coi_connector import COILibyaConnector
        c = COILibyaConnector()
        raw = c.fetch(jurisdiction_id)
        if raw.get('available'):
            data['coi_libya'] = raw
    except Exception as e:
        logger.warning(f'COI Libya load failed for {jurisdiction_id}: {e}')

    # NCDC Libya (manual upload)
    try:
        from utils.connectors.libya.ncdc_connector import NCDCLibyaConnector
        c = NCDCLibyaConnector()
        raw = c.fetch(jurisdiction_id)
        if raw.get('available'):
            data['ncdc_libya'] = raw
    except Exception as e:
        logger.warning(f'NCDC Libya load failed for {jurisdiction_id}: {e}')

    return data


# ---------------------------------------------------------------------------
# Show-work / popover content builder
# ---------------------------------------------------------------------------

def _na(val, unit='', year=None, decimals=1) -> str:
    """Format a value for display in a popover, or return an unavailability note."""
    if val is None:
        return '<span class="text-muted">البيانات غير متاحة / Data not available</span>'
    yr = f' ({year})' if year else ''
    fmt = f'{val:.{decimals}f}'
    return f'<b>{fmt}</b>{" " + unit if unit else ""}{yr}'


def _row(label_ar: str, label_en: str, val_html: str, source: str = '') -> str:
    src_html = f'<span class="text-muted" style="font-size:0.72rem">{source}</span>' if source else ''
    return (
        f'<div style="margin-bottom:0.3rem">'
        f'<span style="font-family:\'Cairo\',sans-serif">{label_ar}</span>'
        f' <span style="color:#888;font-size:0.8rem">/ {label_en}</span>: '
        f'{val_html}{("<br>" + src_html) if src_html else ""}'
        f'</div>'
    )


def _formula_row(formula: str, result_val, decimals: int = 2) -> str:
    if result_val is None:
        return ''
    return (
        f'<div style="margin-top:0.4rem;padding-top:0.3rem;border-top:1px solid #dee2e6">'
        f'<code style="font-size:0.78rem">{formula}</code> '
        f'= <b>{result_val:.{decimals}f}</b> (0–1)'
        f'</div>'
    )


HDX_SOURCE = 'المصدر: OCHA HDX / Source: OCHA HDX'
WHO_HDX_SOURCE = 'المصدر: WHO عبر OCHA HDX · 2024 / Source: WHO via OCHA HDX'
IDMC_SOURCE = 'المصدر: IDMC عبر OCHA HDX · 2024 / Source: IDMC via OCHA HDX'
HEIGIT_SOURCE = 'المصدر: HeiGIT / HDX · مستوى المديرية / Source: HeiGIT via HDX · District level'
WB_SOURCE = 'المصدر: البنك الدولي / Source: World Bank'
COI_SOURCE = 'المصدر: COI Libya — رفع يدوي / Source: COI Libya — manual upload'
NCDC_SOURCE = 'المصدر: NCDC Libya — رفع يدوي / Source: NCDC Libya — manual upload'
PROXY_NOTE = '<span style="color:#856404;font-size:0.72rem">&#9432; تقدير بديل — بانتظار بيانات المصدر الأصلي / Proxy estimate — awaiting primary source data</span>'


def _build_show_work(cd: dict) -> dict:
    """
    Build Bootstrap popover content for every sub-domain across all three pillars.
    Keys are '{pillar}__{sub_domain}' e.g. 'hazard__epidemiological_hazard'.
    Values are {'title': str, 'content': str} — content is HTML.
    """
    who  = cd.get('who_gho', {})
    who_r = cd.get('who_hdx_raw', {})
    idmc  = cd.get('idmc', {})
    idmc_r = cd.get('idmc_raw', {})
    heigit = cd.get('heigit', {})
    wb    = cd.get('worldbank', {})
    coi   = cd.get('coi_libya', {})
    iom   = cd.get('iom', {})

    sw = {}

    # ── HAZARD & EXPOSURE ────────────────────────────────────────────────

    # 1. Infrastructure Hazard
    beds_10k = who_r.get('hospital_beds_per_10k')
    beds_yr  = who_r.get('hospital_beds_per_10k_year')
    hosp_dens = who_r.get('hospital_density_per_100k')
    if beds_10k or hosp_dens:
        lines = []
        if beds_10k is not None:
            beds_1k = beds_10k / 10
            score = round(1.0 - min(1.0, beds_1k / 5.0), 3)
            lines.append(_row('أسرة المستشفيات', 'Hospital beds',
                               _na(beds_10k, 'لكل 10,000 / per 10k', beds_yr), WHO_HDX_SOURCE))
            lines.append(_formula_row(f'فجوة المستشفيات = 1 − min(1, {beds_1k:.2f}/5)', score))
        if hosp_dens is not None:
            lines.append(_row('كثافة المستشفيات', 'Hospital density',
                               _na(hosp_dens, 'لكل 100,000 / per 100k',
                                   who_r.get('hospital_density_per_100k_year')), WHO_HDX_SOURCE))
        if not beds_10k and not hosp_dens:
            lines.append(PROXY_NOTE)
        sw['hazard__infrastructure_hazard'] = {
            'title': 'مخاطر البنية التحتية / Infrastructure Hazard',
            'content': ''.join(lines),
        }

    # 2. Epidemiological Hazard
    u5mort = who.get('under5_mortality_rate')
    u5yr   = who_r.get('under5_mortality_rate_year')
    tb     = who.get('tb_incidence_per_100k') or who_r.get('tb_incidence_per_100k')
    tb_yr  = who_r.get('tb_incidence_per_100k_year')
    tb_trt = who.get('tb_treatment_coverage_pct')
    tb_trt_yr = who_r.get('tb_treatment_coverage_pct_year')

    lines = []
    if u5mort is not None:
        score_u5 = round(min(1.0, float(u5mort) / 50.0), 3)
        lines.append(_row('وفيات الأطفال دون 5 سنوات', 'Under-5 mortality',
                           _na(u5mort, 'لكل 1,000 مولود / per 1,000', u5yr), WHO_HDX_SOURCE))
        lines.append(_formula_row(f'min(1.0, {u5mort:.1f}/50)', score_u5))
    if tb is not None:
        score_tb = round(min(1.0, float(tb) / 200.0), 3)
        lines.append(_row('الإصابات بالسل', 'TB incidence',
                           _na(tb, 'لكل 100,000 / per 100k', tb_yr), WHO_HDX_SOURCE))
        lines.append(_formula_row(f'min(1.0, {tb:.0f}/200)', score_tb))
    if tb_trt is not None:
        lines.append(_row('تغطية علاج السل', 'TB treatment coverage',
                           _na(tb_trt, '%', tb_trt_yr), WHO_HDX_SOURCE))
    if not lines:
        lines.append(PROXY_NOTE + '<br>' + _row('', 'Status', 'بانتظار بيانات NCDC Libya / Awaiting NCDC Libya data', NCDC_SOURCE))
    sw['hazard__epidemiological_hazard'] = {
        'title': 'درجة الأمراض المعدية / Epidemiological Hazard',
        'content': ''.join(lines),
    }

    # 3. Natural Hazard
    pm25   = who.get('pm25_annual_mean_ugm3') or who_r.get('pm25_annual_mean_ugm3')
    pm25_yr = who_r.get('pm25_annual_mean_ugm3_year')
    air_mort = who.get('air_pollution_mortality_per_100k')
    air_yr   = who_r.get('air_pollution_mortality_per_100k_year')

    lines = []
    lines.append(_row('', 'Flood / Dam hazard', 'بانتظار بيانات EM-DAT · Derna 2023 موثقة / Awaiting EM-DAT · Derna 2023 documented', 'EM-DAT (قيد التوصيل)'))
    if pm25 is not None:
        score_pm = round(min(1.0, float(pm25) / 75.0), 3)
        lines.append(_row('تركيز PM2.5', 'PM2.5 concentration',
                           _na(pm25, 'μg/m³', pm25_yr), WHO_HDX_SOURCE))
        lines.append(_formula_row(f'min(1.0, {pm25:.1f}/75)', score_pm))
    if air_mort is not None:
        lines.append(_row('وفيات تلوث الهواء', 'Air pollution mortality',
                           _na(air_mort, 'لكل 100,000 / per 100k', air_yr), WHO_HDX_SOURCE))
    if not pm25 and not air_mort:
        lines.append(PROXY_NOTE)
    sw['hazard__natural_hazard'] = {
        'title': 'الكوارث الطبيعية / Natural Hazard',
        'content': ''.join(lines),
    }

    # 4. Road Safety Hazard
    lines = [_row('', 'Road traffic mortality', 'بانتظار بيانات WHO GHO / Awaiting WHO GHO data', WB_SOURCE), PROXY_NOTE]
    sw['hazard__road_safety_hazard'] = {
        'title': 'سلامة الطرق / Road Safety Hazard',
        'content': ''.join(lines),
    }

    # ── VULNERABILITY ───────────────────────────────────────────────────

    # 1. Displacement Vulnerability
    idp_stock   = idmc.get('idp_stock') or idmc.get('total_idps')
    new_c       = idmc.get('new_conflict_displacements')
    idp_yr      = idmc_r.get('data_year')
    mig_total   = iom.get('total_migrants')
    total_pop   = 7_100_000
    events      = idmc_r.get('recent_disaster_events', [])

    lines = []
    if idp_stock is not None:
        disp_total = float(idp_stock) + (float(mig_total) if mig_total else 0.0)
        score_d    = round(min(1.0, disp_total / (total_pop * 0.20)), 3)
        lines.append(_row('مخزون النازحين داخلياً', 'IDP stock',
                           _na(idp_stock, 'نسمة / persons', idp_yr, 0), IDMC_SOURCE))
        if new_c is not None:
            lines.append(_row('نازحون جدد (نزاع)', 'New conflict displacements',
                               _na(new_c, 'نسمة / persons', idp_yr, 0), IDMC_SOURCE))
        if mig_total is not None:
            lines.append(_row('إجمالي المهاجرين', 'Total migrants',
                               _na(mig_total, '', None, 0), HDX_SOURCE))
        lines.append(_formula_row(f'min(1.0, {int(disp_total):,} / ({total_pop:,}×0.20))', score_d))
        if events:
            ev = events[0]
            lines.append(f'<div style="font-size:0.75rem;margin-top:0.3rem"><b>آخر حادثة كوارث:</b> {ev.get("event_name","")[:50]} ({ev.get("year","")}) — {int(ev.get("new_displacements") or 0):,} نازح</div>')
    else:
        lines.append(PROXY_NOTE)
    sw['vulnerability__displacement_vulnerability'] = {
        'title': 'هشاشة النزوح / Displacement Vulnerability',
        'content': ''.join(lines),
    }

    # 2. Health Unawareness
    vacc    = who.get('measles_vaccination_coverage') or who_r.get('measles_vaccination_pct')
    vacc_yr = who_r.get('measles_vaccination_pct_year')
    stunt   = who.get('stunting_prevalence_pct') or who_r.get('stunting_prevalence_pct')
    stunt_yr = who_r.get('stunting_prevalence_pct_year')
    lines = []
    if vacc is not None:
        score_vacc = round(1.0 - min(1.0, float(vacc) / 100.0), 3)
        lines.append(_row('تغطية تطعيم الحصبة', 'Measles vaccination',
                           _na(vacc, '%', vacc_yr), WHO_HDX_SOURCE))
        lines.append(_formula_row(f'1 − ({vacc:.0f}/100)', score_vacc))
    if stunt is not None:
        lines.append(_row('انتشار التقزم (دون 5 سنوات)', 'Stunting prevalence',
                           _na(stunt, '%', stunt_yr), WHO_HDX_SOURCE))
    if not vacc and not stunt:
        lines.append(PROXY_NOTE)
    sw['vulnerability__health_unawareness'] = {
        'title': 'الوعي الصحي / Health Unawareness',
        'content': ''.join(lines),
    }

    # 3. Agency Capacity Gap
    lines = [
        _row('', 'Agency capacity', 'بانتظار بيانات COI Libya / Awaiting COI Libya data', COI_SOURCE),
        PROXY_NOTE,
    ]
    sw['vulnerability__agency_capacity_gap'] = {
        'title': 'نقص قدرة الاستجابة / Agency Capacity Gap',
        'content': ''.join(lines),
    }

    # 4. Urban Sprawl
    lines = [
        _row('', 'Urban population %', 'بانتظار بيانات البنك الدولي / Awaiting World Bank data', WB_SOURCE),
        PROXY_NOTE,
    ]
    sw['vulnerability__urban_sprawl'] = {
        'title': 'التوسع العمراني / Urban Sprawl',
        'content': ''.join(lines),
    }

    # 5. Security Vulnerability
    lines = [
        _row('', 'Rule of law / Political stability', 'بانتظار بيانات البنك الدولي / Awaiting World Bank data', WB_SOURCE),
        '<div style="font-size:0.72rem;color:#6c757d;margin-top:0.3rem">ملاحظة: مؤشر النزاعات المسلحة مستبعد من التقييم الحالي / Note: Armed clashes domain omitted pending review.</div>',
        PROXY_NOTE,
    ]
    sw['vulnerability__security_vulnerability'] = {
        'title': 'الهشاشة الأمنية / Security Vulnerability',
        'content': ''.join(lines),
    }

    # ── COPING CAPACITY ─────────────────────────────────────────────────

    # 1. Healthcare Access Gap
    hosp_pct  = heigit.get('hospital_access_pct')
    hosp_gap  = heigit.get('hospital_access_gap_pct')
    phc_pct   = heigit.get('primary_care_access_pct')
    beds_10k  = who_r.get('hospital_beds_per_10k')
    beds_yr_c = who_r.get('hospital_beds_per_10k_year')
    proxy_note = heigit.get('_proxy_note', '')
    lines = []
    if hosp_pct is not None:
        threshold = heigit.get('hospital_threshold_seconds', 3600)
        lines.append(_row('وصول إلى المستشفيات', 'Hospital access',
                           f'<b>{hosp_pct:.1f}%</b> من السكان خلال {threshold//60} دقيقة / of population within {threshold//60} min',
                           HEIGIT_SOURCE))
        if hosp_gap is not None:
            score_hg = round(hosp_gap / 100.0, 3)
            lines.append(_formula_row(f'فجوة الوصول = (100 − {hosp_pct:.1f}) / 100', score_hg))
    if phc_pct is not None:
        lines.append(_row('وصول إلى الرعاية الأولية', 'Primary care access',
                           f'<b>{phc_pct:.1f}%</b>', HEIGIT_SOURCE))
    if beds_10k is not None:
        lines.append(_row('أسرة المستشفيات', 'Hospital beds',
                           _na(beds_10k, 'لكل 10,000 / per 10k', beds_yr_c), WHO_HDX_SOURCE))
    if proxy_note:
        lines.append(f'<div style="font-size:0.72rem;color:#6c757d;margin-top:0.3rem">{proxy_note}</div>')
    if not hosp_pct and not beds_10k:
        lines.append(PROXY_NOTE)
    sw['coping__healthcare_access_gap'] = {
        'title': 'محدودية الرعاية الصحية / Healthcare Access Gap',
        'content': ''.join(lines),
    }

    # 2. Response Time Gap
    avg_resp = coi.get('avg_ambulance_response_minutes')
    if avg_resp:
        score_r = round(min(1.0, float(avg_resp) / 60.0), 3)
        lines = [
            _row('زمن استجابة الإسعاف', 'Ambulance response time',
                 _na(avg_resp, 'دقيقة / min'), COI_SOURCE),
            _formula_row(f'min(1.0, {avg_resp:.0f}/60)', score_r),
        ]
    elif beds_10k:
        beds_1k = beds_10k / 10
        score_r = round(1.0 - min(1.0, beds_1k / 5.0), 3)
        lines = [
            _row('', 'Proxy: hospital beds', _na(beds_10k, 'لكل 10,000 / per 10k', beds_yr_c), WHO_HDX_SOURCE),
            _formula_row(f'1 − min(1, {beds_1k:.2f}/5) [بديل/proxy]', score_r),
            PROXY_NOTE,
        ]
    else:
        lines = [
            _row('', 'Ambulance response time', 'بانتظار بيانات COI Libya / Awaiting COI Libya data', COI_SOURCE),
            PROXY_NOTE,
        ]
    sw['coping__response_time_gap'] = {
        'title': 'قصور وقت الاستجابة / Response Time Gap',
        'content': ''.join(lines),
    }

    # 3. Data Availability Gap
    n_available = sum(1 for v in cd.values() if isinstance(v, dict) and v.get('available'))
    n_total = 8
    gap = round(1.0 - min(1.0, n_available / n_total), 3)
    lines = [
        f'<div style="margin-bottom:0.3rem"><b>مصادر البيانات المتاحة:</b> {n_available} من أصل {n_total} / Data sources available: {n_available} of {n_total}</div>',
        _formula_row(f'1 − ({n_available}/{n_total})', gap),
        f'<div style="font-size:0.72rem;color:#6c757d;margin-top:0.3rem">يعكس هذا المؤشر توافر البيانات في حد ذاته — وليس بياناً خارجياً. / This indicator measures data availability itself.</div>',
    ]
    sw['coping__data_availability_gap'] = {
        'title': 'نقص توافر البيانات / Data Availability Gap',
        'content': ''.join(lines),
    }

    # 4. Community Support Gap
    ngo_score = coi.get('ngo_presence_score')
    lines = []
    if ngo_score:
        gap_n = round(1.0 - min(1.0, float(ngo_score)), 3)
        lines.append(_row('حضور المنظمات غير الحكومية', 'NGO presence', _na(ngo_score), COI_SOURCE))
        lines.append(_formula_row(f'1 − {ngo_score:.2f}', gap_n))
    else:
        lines.append(_row('', 'NGO/organization presence', 'بانتظار بيانات COI Libya / Awaiting COI Libya data', COI_SOURCE))
        lines.append(PROXY_NOTE)
    sw['coping__community_support_gap'] = {
        'title': 'غياب الدعم المجتمعي / Community Support Gap',
        'content': ''.join(lines),
    }

    # 5. Poverty Vulnerability
    poverty = wb.get('poverty_headcount_ratio')
    gni     = wb.get('gni_per_capita')
    lines = []
    if poverty:
        lines.append(_row('نسبة الفقر', 'Poverty headcount', _na(poverty, '%'), WB_SOURCE))
        lines.append(_formula_row(f'{poverty:.1f}/100', round(float(poverty)/100, 3)))
    elif gni:
        score_g = round(1.0 - min(1.0, float(gni) / 15000.0), 3)
        lines.append(_row('الدخل القومي الإجمالي للفرد', 'GNI per capita', _na(gni, 'USD'), WB_SOURCE))
        lines.append(_formula_row(f'1 − min(1, {gni:.0f}/15,000) [بديل/proxy]', score_g))
        lines.append(PROXY_NOTE)
    else:
        lines.append(_row('', 'Poverty / GNI', 'بانتظار بيانات البنك الدولي / Awaiting World Bank data', WB_SOURCE))
        lines.append(PROXY_NOTE)
    sw['coping__poverty_vulnerability'] = {
        'title': 'معدل الفقر / Poverty Vulnerability',
        'content': ''.join(lines),
    }

    return sw


# ---------------------------------------------------------------------------
# Indicator tiles builder — granular per-indicator breakdown for dashboard
# ---------------------------------------------------------------------------

def _T(tid, la, le, value, unit, year, score, formula, source,
       proxy=False, note='', protective=False):
    """
    Build a single indicator tile dict with rich pre-built popover HTML.
    protective=True means the raw value shows a GOOD outcome (e.g. vaccination %)
    and the score already reflects the risk direction (1 - coverage).

    popover_html is built here as a Python string containing HTML, then stored
    in the dict.  The template uses {{ tile.popover_html | e }} so Jinja2 escapes
    < > " into HTML entities — the browser decodes them on read, Bootstrap renders
    as innerHTML.  This avoids the attribute-breaking bare-< bug.
    """
    avail = value is not None
    lev   = _score_to_level(score) if score is not None else 'unavailable'
    bdg   = _level_badge(lev)

    if value is None:
        vfmt = None
    elif isinstance(value, float):
        if value >= 100_000:
            vfmt = f'{value:,.0f}'
        elif value >= 1_000:
            vfmt = f'{value:,.0f}'
        elif value >= 100:
            vfmt = f'{value:.0f}'
        elif value >= 10:
            vfmt = f'{value:.1f}'
        else:
            vfmt = f'{value:.2f}'
    else:
        vfmt = str(value)

    score_f  = round(float(score), 3)   if score is not None else None
    score_d  = round(float(score) * 10, 1) if score is not None else None

    # ── Build rich popover HTML ─────────────────────────────────────
    p = []
    # Header: Arabic name
    p.append(f'<div style="direction:rtl;font-weight:700;font-size:0.85rem;'
             f'margin-bottom:6px;border-bottom:1px solid #eee;padding-bottom:4px;">'
             f'{la}</div>')

    # Data table
    p.append('<table style="width:100%;border-collapse:collapse;font-size:0.78rem;'
             'margin-bottom:6px;">')

    if vfmt is not None:
        yr_str = f' ({year})' if year else ''
        unit_str = f' {unit}' if unit else ''
        p.append(f'<tr>'
                 f'<td style="color:#888;padding:2px 8px 2px 0;white-space:nowrap;">'
                 f'القيمة الفعلية</td>'
                 f'<td><code style="color:#0d6efd;">{vfmt}</code>'
                 f'<span style="color:#999;font-size:0.72rem;">{unit_str}{yr_str}</span>'
                 f'</td></tr>')
    else:
        p.append('<tr><td style="color:#888;padding:2px 8px 2px 0;">القيمة الفعلية</td>'
                 '<td style="color:#aaa;font-style:italic;">لا بيانات أولية / N/A</td></tr>')

    if score_d is not None:
        level_label = LEVEL_LABELS_AR.get(lev, lev)
        p.append(f'<tr>'
                 f'<td style="color:#888;padding:2px 8px 2px 0;white-space:nowrap;">'
                 f'درجة المخاطر</td>'
                 f'<td><code style="color:#dc3545;">{score_d}/10</code>'
                 f'<span style="color:#999;font-size:0.72rem;"> — {level_label} / {lev.upper()}</span>'
                 f'</td></tr>')

    if protective:
        p.append('<tr><td></td>'
                 '<td style="color:#198754;font-size:0.72rem;">'
                 '&#8593; قيمة وقائية — الدرجة = 1 &minus; التغطية'
                 '</td></tr>')

    p.append('</table>')

    # Formula
    if formula:
        p.append('<div style="background:#f8f9fa;border-radius:4px;padding:6px 8px;'
                 'margin-bottom:6px;">'
                 '<div style="font-weight:600;font-size:0.75rem;color:#555;'
                 'margin-bottom:3px;">&#x2211; الصيغة الحسابية / Formula</div>'
                 f'<code style="font-size:0.76rem;word-break:break-all;'
                 f'color:#0d6efd;">{formula}</code>'
                 '</div>')

    # Source + year
    if source:
        yr_str = f' ({year})' if year else ''
        p.append(f'<div style="font-size:0.72rem;color:#888;margin-bottom:3px;">'
                 f'<b>&#x1F4CB; المصدر / Source:</b> {source}{yr_str}</div>')

    # Note
    if note:
        p.append(f'<div style="font-size:0.72rem;color:#666;border-top:1px solid #eee;'
                 f'padding-top:4px;margin-top:4px;">{note}</div>')

    # Proxy warning
    if proxy:
        p.append('<div style="font-size:0.72rem;color:#fd7e14;border-top:1px solid #eee;'
                 'padding-top:4px;margin-top:4px;">'
                 '<sup>~</sup> تقدير بديل موثق — لا تتوفر بيانات أولية مباشرة / '
                 'Documented proxy estimate — no primary data available</div>')

    popover_html = ''.join(p)
    # ── End popover HTML ────────────────────────────────────────────

    return {
        'id':            tid,
        'label_ar':      la,
        'label_en':      le,
        'value':         value,
        'value_fmt':     vfmt,
        'unit':          unit,
        'year':          year,
        'score':         score_f,
        'score_display': score_d,
        'level':         lev,
        'badge':         bdg,
        'available':     avail,
        'proxy':         proxy,
        'protective':    protective,
        'source':        source,
        'formula':       formula,
        'note':          note,
        'popover_html':  popover_html,
    }


def _build_indicator_tiles(cd: dict) -> dict:
    """
    Build the full 3-pillar tile hierarchy.
    Returns {'hazard': {...}, 'vulnerability': {...}, 'coping': {...}}
    Each pillar has: label_ar, label_en, sections[]
    Each section has: id, label_ar, label_en, score (from domain), tiles[]
    Each tile is built with _T().
    """
    who  = cd.get('who_gho', {})
    who_r = cd.get('who_hdx_raw', {})
    idmc  = cd.get('idmc', {})
    idmc_r = cd.get('idmc_raw', {})
    hg    = cd.get('heigit', {})
    wb    = cd.get('worldbank', {})
    coi   = cd.get('coi_libya', {})

    def _yr(key):
        return who_r.get(key + '_year', '')

    # ── shorthand values ────────────────────────────────────────────────
    pm25           = who_r.get('pm25_annual_mean_ugm3')
    air_mort       = who_r.get('air_pollution_mortality_per_100k')
    u5mort         = who_r.get('under5_mortality_rate')
    neo_mort       = who_r.get('neonatal_mortality_rate')
    inf_mort       = who_r.get('infant_mortality_rate')
    tb_inc         = who_r.get('tb_incidence_per_100k')
    tb_trt         = who_r.get('tb_treatment_coverage_pct')
    tb_succ        = who_r.get('tb_treatment_success_pct')
    ncd_mort       = who_r.get('ncd_mortality_30_70_pct')
    stunting       = who_r.get('stunting_prevalence_pct')
    obesity        = who_r.get('obesity_prevalence_pct')
    anaemia        = who_r.get('anaemia_children_prevalence_pct')
    inactivity     = who_r.get('physical_inactivity_prevalence_pct')
    mcv1           = who_r.get('measles_vaccination_pct')
    mcv2           = who_r.get('measles_2nd_dose_vaccination_pct')
    beds_10k       = who_r.get('hospital_beds_per_10k')
    hosp_dens      = who_r.get('hospital_density_per_100k')
    health_exp_pct = wb.get('health_expenditure_pct_gdp')

    idp_stock      = idmc.get('total_idps')
    new_conf       = idmc_r.get('new_displacements_conflict')
    events         = idmc_r.get('recent_disaster_events', [])
    event_displ    = sum(e.get('new_displacements', 0) or 0 for e in events)

    hosp_gap       = hg.get('hospital_access_gap_pct')
    hosp_pct       = hg.get('hospital_access_pct')
    phc_gap        = hg.get('primary_care_access_gap_pct')
    phc_pct        = hg.get('primary_care_access_pct')
    edu_gap        = hg.get('education_access_gap_pct')
    edu_pct        = hg.get('education_access_pct')

    water_pct      = wb.get('access_clean_water')
    sanit_pct      = wb.get('access_sanitation')
    elec_pct       = wb.get('access_electricity')
    urban_pct      = wb.get('urban_population_pct')
    pop_density    = wb.get('population_density')
    food_insec     = wb.get('food_insecurity_pct')
    gdp_cap        = wb.get('gdp_per_capita')
    vuln_idx       = wb.get('vulnerability_index')

    WHO_SRC   = 'WHO Libya via OCHA HDX'
    IDMC_SRC  = 'IDMC via OCHA HDX'
    HEIGIT_SRC = 'HeiGIT / OCHA HDX'
    WB_SRC    = 'World Bank'
    EMDAT_SRC = 'EM-DAT (قيد التوصيل / pending)'
    COI_SRC   = 'COI Libya — رفع يدوي / manual upload'
    PROXY_SRC = 'تقدير بديل / proxy estimate'

    def _fmt(v, d=1):
        if v is None:
            return 'N/A'
        return f'{v:.{d}f}'

    # ════════════════════════════════════════════════════════════════════
    # PILLAR 1: HAZARD & EXPOSURE
    # ════════════════════════════════════════════════════════════════════

    # ── Natural Hazards ─────────────────────────────────────────────────
    flood_disp  = event_displ if events else None
    flood_score = min(1.0, float(flood_disp) / 50_000) if flood_disp else None
    nat_tiles = [
        _T('flooding',
           'الفيضانات', 'Flooding',
           flood_disp, 'نازح / displaced', idmc_r.get('data_year', ''),
           flood_score,
           f'min(1.0, {int(flood_disp or 0):,} / 50,000) = {flood_score:.3f}' if flood_score else 'لا بيانات EM-DAT',
           IDMC_SRC,
           proxy=(flood_disp is None),
           note='حوادث 2024: فيضان مصراتة (504) + فيضان الكفرة (3,000) / 2024 events via IDMC' if events else 'يشمل أحداث درنة 2023 — بانتظار EM-DAT / Includes Derna 2023 — awaiting EM-DAT'),

        _T('sandstorms',
           'العواصف الرملية', 'Sandstorms / Dust',
           None, '', '',
           0.45,
           'تقدير بديل: ليبيا في حزام الصحراء الكبرى / Proxy: Libya in Saharan dust belt',
           PROXY_SRC, proxy=True,
           note='لا توجد قاعدة بيانات وطنية للعواصف الرملية متاحة حتى الآن'),

        _T('drought',
           'الجفاف', 'Drought',
           None, '', '',
           0.35,
           'تقدير بديل: مناخ جاف شبه صحراوي / Proxy: semi-arid climate',
           PROXY_SRC, proxy=True),

        _T('pm25',
           'تلوث الهواء PM2.5', 'Air Pollution PM2.5',
           pm25, 'μg/m³', _yr('pm25_annual_mean_ugm3'),
           min(1.0, float(pm25) / 75.0) if pm25 else None,
           f'min(1.0, {_fmt(pm25)} / 75) = {min(1.0,float(pm25)/75):.2f}' if pm25 else 'N/A',
           WHO_SRC,
           note='حد منظمة الصحة العالمية السنوي: 5 μg/m³ / WHO annual guideline: 5 μg/m³'),

        _T('air_mort',
           'وفيات تلوث الهواء', 'Air Pollution Mortality',
           air_mort, 'لكل 100,000 / per 100k', _yr('air_pollution_mortality_per_100k'),
           min(1.0, float(air_mort) / 50.0) if air_mort else None,
           f'min(1.0, {_fmt(air_mort)} / 50) = {min(1.0,float(air_mort)/50):.3f}' if air_mort else 'N/A',
           WHO_SRC),
    ]

    # ── Epidemiological Hazards ──────────────────────────────────────────
    epi_tiles = [
        _T('u5mort',
           'وفيات الأطفال دون 5 سنوات', 'Under-5 Mortality',
           u5mort, 'لكل 1,000 مولود / per 1,000', _yr('under5_mortality_rate'),
           min(1.0, float(u5mort) / 50.0) if u5mort else None,
           f'min(1.0, {_fmt(u5mort)} / 50) = {min(1.0,float(u5mort)/50):.3f}' if u5mort else 'N/A',
           WHO_SRC,
           note='المعدل العالمي للدول المرتفعة الدخل ≈ 4.5 / High-income country rate ≈ 4.5'),

        _T('inf_mort',
           'وفيات الرضع', 'Infant Mortality',
           inf_mort, 'لكل 1,000 مولود / per 1,000', _yr('infant_mortality_rate'),
           min(1.0, float(inf_mort) / 50.0) if inf_mort else None,
           f'min(1.0, {_fmt(inf_mort)} / 50) = {min(1.0,float(inf_mort)/50):.3f}' if inf_mort else 'N/A',
           WHO_SRC),

        _T('neo_mort',
           'وفيات حديثي الولادة', 'Neonatal Mortality',
           neo_mort, 'لكل 1,000 مولود / per 1,000', _yr('neonatal_mortality_rate'),
           min(1.0, float(neo_mort) / 30.0) if neo_mort else None,
           f'min(1.0, {_fmt(neo_mort)} / 30) = {min(1.0,float(neo_mort)/30):.3f}' if neo_mort else 'N/A',
           WHO_SRC),

        _T('tb_inc',
           'إصابات السل', 'TB Incidence',
           tb_inc, 'لكل 100,000 / per 100k', _yr('tb_incidence_per_100k'),
           min(1.0, float(tb_inc) / 200.0) if tb_inc else None,
           f'min(1.0, {_fmt(tb_inc,0)} / 200) = {min(1.0,float(tb_inc)/200):.3f}' if tb_inc else 'N/A',
           WHO_SRC,
           note='حد الدول عالية العبء: 200/100,000 / High-burden threshold: 200/100k'),

        _T('ncd_mort',
           'وفيات الأمراض غير المعدية (30–70 سنة)', 'NCD Premature Mortality (30–70y)',
           ncd_mort, '%', _yr('ncd_mortality_30_70_pct'),
           min(1.0, float(ncd_mort) / 30.0) if ncd_mort else None,
           f'min(1.0, {_fmt(ncd_mort)} / 30) = {min(1.0,float(ncd_mort)/30):.3f}' if ncd_mort else 'N/A',
           WHO_SRC,
           note='نسبة الوفاة بأمراض القلب والسكري والسرطان بين 30–70 عاماً'),

        _T('stunting',
           'التقزم (دون 5 سنوات)', 'Stunting Prevalence',
           stunting, '%', _yr('stunting_prevalence_pct'),
           min(1.0, float(stunting) / 40.0) if stunting else None,
           f'min(1.0, {_fmt(stunting)} / 40) = {min(1.0,float(stunting)/40):.3f}' if stunting else 'N/A',
           WHO_SRC),
    ]

    # ── Infrastructure Hazards ──────────────────────────────────────────
    water_score = (1.0 - min(1.0, float(water_pct) / 100.0)) if water_pct else None
    sanit_score = (1.0 - min(1.0, float(sanit_pct) / 100.0)) if sanit_pct else None
    elec_score  = (1.0 - min(1.0, float(elec_pct)  / 100.0)) if elec_pct else None
    beds_score  = (1.0 - min(1.0, (float(beds_10k)/10.0) / 5.0)) if beds_10k else None

    infra_tiles = [
        _T('hosp_beds',
           'أسرة المستشفيات', 'Hospital Beds',
           beds_10k, 'لكل 10,000 / per 10k', _yr('hospital_beds_per_10k'),
           beds_score,
           f'فجوة = 1 − min(1, {_fmt(beds_10k,0)}/10÷5) = {beds_score:.3f}' if beds_score else 'N/A',
           WHO_SRC,
           note='معيار WHO: 50 سرير/10,000 (ليبيا: 35) / WHO reference: 50 beds/10k'),

        _T('hosp_dens',
           'كثافة المستشفيات', 'Hospital Density',
           hosp_dens, 'لكل 100,000 / per 100k', _yr('hospital_density_per_100k'),
           (1.0 - min(1.0, float(hosp_dens) / 10.0)) if hosp_dens else None,
           f'1 − min(1, {_fmt(hosp_dens)} / 10) = {1-min(1,float(hosp_dens)/10):.3f}' if hosp_dens else 'N/A',
           WHO_SRC,
           note='بيانات 2013 — بانتظار تحديث من النظام الصحي الليبي / 2013 data — awaiting Libya MoH update'),

        _T('water',
           'إمكانية الحصول على مياه نظيفة', 'Access to Clean Water',
           water_pct, '%', '',
           water_score,
           f'1 − ({_fmt(water_pct)} / 100) = {water_score:.3f}' if water_score is not None else 'N/A',
           WB_SRC, protective=True),

        _T('sanitation',
           'إمكانية الحصول على الصرف الصحي', 'Access to Sanitation',
           sanit_pct, '%', '',
           sanit_score,
           f'1 − ({_fmt(sanit_pct)} / 100) = {sanit_score:.3f}' if sanit_score is not None else 'N/A',
           WB_SRC, protective=True),

        _T('electricity',
           'إمكانية الحصول على الكهرباء', 'Access to Electricity',
           elec_pct, '%', '',
           elec_score,
           f'1 − ({_fmt(elec_pct)} / 100) = {elec_score:.3f}' if elec_score is not None else 'N/A',
           WB_SRC, protective=True,
           note='الفجوة تعكس السكان غير المتصلين بالشبكة الكهربائية / Gap reflects population off-grid'),
    ]

    # ── Road Safety ─────────────────────────────────────────────────────
    road_tiles = [
        _T('road_traffic',
           'وفيات حوادث المرور', 'Road Traffic Mortality',
           None, 'لكل 100,000 / per 100k', '',
           0.50,
           'تقدير بديل — بانتظار بيانات WHO GHO / Proxy — awaiting WHO GHO data',
           PROXY_SRC, proxy=True,
           note='بيانات ليبيا غير متاحة من WHO GHO حتى الآن — القيمة الافتراضية 0.50'),
    ]

    # ════════════════════════════════════════════════════════════════════
    # PILLAR 2: VULNERABILITY
    # ════════════════════════════════════════════════════════════════════

    # ── Displacement ────────────────────────────────────────────────────
    total_pop = 7_381_023
    idp_score = min(1.0, float(idp_stock) / (total_pop * 0.20)) if idp_stock else None
    conf_score = min(1.0, float(new_conf) / 100_000) if new_conf else None
    ev_score  = min(1.0, float(event_displ) / 50_000) if event_displ else None

    disp_tiles = [
        _T('idp_stock',
           'مخزون النازحين داخلياً', 'IDP Stock',
           idp_stock, 'نسمة / persons', idmc_r.get('data_year', ''),
           idp_score,
           f'min(1.0, {int(idp_stock or 0):,} / ({total_pop:,}×0.20)) = {idp_score:.4f}' if idp_score else 'N/A',
           IDMC_SRC,
           note=f'المجموع المُقرَّب: {int(idmc_r.get("total_displacement_rounded",0)):,} / Rounded total: {int(idmc_r.get("total_displacement_rounded",0)):,}'),

        _T('conf_disp',
           'نازحون جدد بسبب النزاع', 'New Conflict Displacements',
           new_conf, 'نسمة / persons', idmc_r.get('data_year', ''),
           conf_score,
           f'min(1.0, {int(new_conf or 0):,} / 100,000) = {conf_score:.4f}' if conf_score else 'N/A',
           IDMC_SRC),

        _T('disaster_disp',
           'نازحون بسبب الكوارث (2024)', 'Disaster Displacements (2024)',
           event_displ if events else None,
           'نسمة / persons', idmc_r.get('data_year', ''),
           ev_score,
           f'min(1.0, {int(event_displ):,} / 50,000) = {ev_score:.4f}' if ev_score else 'N/A',
           IDMC_SRC,
           note=f'{len(events)} حادثة مسجلة: ' + ' / '.join(
               f'{e.get("event_name","")[:30]}' for e in events[:2]
           ) if events else ''),
    ]

    # ── Health Unawareness ──────────────────────────────────────────────
    mcv1_score = (1.0 - min(1.0, float(mcv1) / 100.0)) if mcv1 else None
    mcv2_score = (1.0 - min(1.0, float(mcv2) / 100.0)) if mcv2 else None
    obes_score = min(1.0, float(obesity) / 50.0) if obesity else None
    anae_score = min(1.0, float(anaemia) / 50.0) if anaemia else None
    inac_score = min(1.0, float(inactivity) / 60.0) if inactivity else None
    food_score = min(1.0, float(food_insec) / 50.0) if food_insec else None

    health_tiles = [
        _T('mcv1',
           'تغطية تطعيم الحصبة (الجرعة الأولى)', 'Measles Vaccination MCV1',
           mcv1, '%', _yr('measles_vaccination_pct'),
           mcv1_score,
           f'عدم الوعي = 1 − ({_fmt(mcv1)} / 100) = {mcv1_score:.3f}' if mcv1_score is not None else 'N/A',
           WHO_SRC, protective=True,
           note='الهدف العالمي: 95% / Global target: 95%'),

        _T('mcv2',
           'تغطية تطعيم الحصبة (الجرعة الثانية)', 'Measles Vaccination MCV2',
           mcv2, '%', _yr('measles_2nd_dose_vaccination_pct'),
           mcv2_score,
           f'1 − ({_fmt(mcv2)} / 100) = {mcv2_score:.3f}' if mcv2_score is not None else 'N/A',
           WHO_SRC, protective=True),

        _T('anaemia',
           'فقر الدم لدى الأطفال', 'Anaemia in Children',
           anaemia, '%', _yr('anaemia_children_prevalence_pct'),
           anae_score,
           f'min(1.0, {_fmt(anaemia)} / 50) = {anae_score:.3f}' if anae_score else 'N/A',
           WHO_SRC),

        _T('obesity',
           'انتشار السمنة (البالغون)', 'Obesity Prevalence (Adults)',
           obesity, '%', _yr('obesity_prevalence_pct'),
           obes_score,
           f'min(1.0, {_fmt(obesity)} / 50) = {obes_score:.3f}' if obes_score else 'N/A',
           WHO_SRC,
           note='مؤشر على أنماط الحياة وجاهزية الرعاية الصحية / Indicates lifestyle disease burden'),

        _T('inactivity',
           'الخمول البدني', 'Physical Inactivity',
           inactivity, '%', _yr('physical_inactivity_prevalence_pct'),
           inac_score,
           f'min(1.0, {_fmt(inactivity)} / 60) = {inac_score:.3f}' if inac_score else 'N/A',
           WHO_SRC),

        _T('food_insec',
           'انعدام الأمن الغذائي', 'Food Insecurity',
           food_insec, '%', '',
           food_score,
           f'min(1.0, {_fmt(food_insec)} / 50) = {food_score:.3f}' if food_score else 'N/A',
           WB_SRC),
    ]

    # ── Urban Sprawl ────────────────────────────────────────────────────
    urb_score = min(1.0, float(urban_pct) / 100.0) * 0.6 if urban_pct else None
    dens_score = min(1.0, float(pop_density) / 100.0) if pop_density else None
    urban_tiles = [
        _T('urban_pop',
           'نسبة السكان الحضريين', 'Urban Population Share',
           urban_pct, '%', '',
           urb_score,
           f'min(1, {_fmt(urban_pct)} / 100) × 0.6 = {urb_score:.3f}' if urb_score else 'N/A',
           WB_SRC,
           note='التمركز الحضري يزيد من تعرض البنية التحتية للصدمات / Urban concentration amplifies shock exposure'),

        _T('pop_density',
           'الكثافة السكانية', 'Population Density',
           pop_density, 'شخص/كم² / persons/km²', '',
           dens_score,
           f'min(1.0, {_fmt(pop_density)} / 100) = {dens_score:.3f}' if dens_score else 'N/A',
           WB_SRC),
    ]

    # ── Economic Vulnerability ──────────────────────────────────────────
    gdp_score = (1.0 - min(1.0, float(gdp_cap) / 15_000.0)) if gdp_cap else None
    vuln_score = float(vuln_idx) if vuln_idx else None
    econ_tiles = [
        _T('gdp_cap',
           'الناتج المحلي الإجمالي للفرد', 'GDP per Capita',
           gdp_cap, 'USD', '',
           gdp_score,
           f'1 − min(1, {_fmt(gdp_cap,0)} / 15,000) = {gdp_score:.3f}' if gdp_score else 'N/A',
           WB_SRC,
           note='ليبيا دولة ذات دخل متوسط أعلى / Libya is an upper-middle income country'),

        _T('vuln_idx',
           'مؤشر الهشاشة الاقتصادية', 'Economic Vulnerability Index',
           vuln_idx, '(0–1)', '',
           vuln_score,
           f'مؤشر مباشر = {_fmt(vuln_idx)} / Direct index value' if vuln_score else 'N/A',
           WB_SRC),
    ]

    # ════════════════════════════════════════════════════════════════════
    # PILLAR 3: COPING CAPACITY
    # ════════════════════════════════════════════════════════════════════

    # ── Healthcare Access ────────────────────────────────────────────────
    hosp_gap_score = min(1.0, float(hosp_gap) / 100.0) if hosp_gap is not None else None
    phc_gap_score  = min(1.0, float(phc_gap) / 100.0) if phc_gap is not None else None
    edu_gap_score  = min(1.0, float(edu_gap) / 100.0) if edu_gap is not None else None
    health_exp_score = (1.0 - min(1.0, float(health_exp_pct) / 10.0)) if health_exp_pct else None

    access_tiles = [
        _T('hosp_access',
           'وصول إلى المستشفيات (60 دقيقة)', 'Hospital Access (60 min)',
           hosp_pct, '%', '',
           hosp_gap_score,
           f'فجوة = {_fmt(hosp_gap)} / 100 = {hosp_gap_score:.3f}' if hosp_gap_score else 'N/A',
           HEIGIT_SRC, protective=True,
           note='النسبة المئوية من السكان الذين يصلون إلى مستشفى خلال 60 دقيقة'),

        _T('phc_access',
           'وصول إلى الرعاية الصحية الأولية', 'Primary Healthcare Access',
           phc_pct, '%', '',
           phc_gap_score,
           f'فجوة = {_fmt(phc_gap)} / 100 = {phc_gap_score:.3f}' if phc_gap_score else 'N/A',
           HEIGIT_SRC, protective=True),

        _T('edu_access',
           'وصول إلى المدارس', 'School Accessibility',
           edu_pct, '%', '',
           edu_gap_score,
           f'فجوة = {_fmt(edu_gap)} / 100 = {edu_gap_score:.3f}' if edu_gap_score else 'N/A',
           HEIGIT_SRC, protective=True,
           note='مؤشر إضافي — لا يدخل في حساب INFORM الحالي / Supplementary — not in current INFORM formula'),

        _T('health_exp',
           'الإنفاق الصحي كنسبة من الناتج المحلي', 'Health Expenditure (% GDP)',
           health_exp_pct, '%', '',
           health_exp_score,
           f'1 − min(1, {_fmt(health_exp_pct)} / 10) = {health_exp_score:.3f}' if health_exp_score else 'N/A',
           WB_SRC, protective=True,
           note='نسبة 10% من الناتج المحلي تُعدّ تغطية شاملة / 10% GDP is considered universal coverage'),

        _T('hosp_beds_coping',
           'أسرة المستشفيات (قدرة الاستجابة)', 'Hospital Beds (Response Capacity)',
           beds_10k, 'لكل 10,000 / per 10k', _yr('hospital_beds_per_10k'),
           beds_score,
           f'فجوة = 1 − min(1, {_fmt(beds_10k,0)}/10÷5) = {beds_score:.3f}' if beds_score else 'N/A',
           WHO_SRC),
    ]

    # ── Data Availability ────────────────────────────────────────────────
    n_sources = sum(1 for v in cd.values() if isinstance(v, dict) and v.get('available'))
    n_total   = 8
    data_score = round(1.0 - min(1.0, n_sources / n_total), 3)
    data_tiles = [
        _T('data_avail',
           'توافر مصادر البيانات', 'Data Source Availability',
           n_sources, f'مصادر من أصل {n_total} / sources of {n_total}', '',
           data_score,
           f'1 − ({n_sources} / {n_total}) = {data_score:.3f}',
           'CARA — محسوب ذاتياً / self-computed',
           note='الدرجة 0.0 = جميع المصادر متاحة / Score 0.0 = all sources available'),
    ]

    # ── Community Support ────────────────────────────────────────────────
    ngo_score = coi.get('ngo_presence_score')
    comm_tiles = [
        _T('ngo',
           'حضور المنظمات غير الحكومية', 'NGO / Organization Presence',
           None, '', '',
           0.55 if not ngo_score else (1.0 - float(ngo_score)),
           'بانتظار بيانات COI Libya / Awaiting COI Libya data',
           COI_SRC, proxy=True,
           note='يتطلب رفع ملف COI Libya يدوياً / Requires COI Libya manual upload'),
    ]

    # ── Economic Coping ──────────────────────────────────────────────────
    poverty_tiles = [
        _T('gdp_coping',
           'الناتج المحلي للفرد (قدرة التعافي)', 'GDP per Capita (Recovery Capacity)',
           gdp_cap, 'USD', '',
           gdp_score,
           f'1 − min(1, {_fmt(gdp_cap,0)} / 15,000) = {gdp_score:.3f}' if gdp_score else 'N/A',
           WB_SRC),

        _T('food_coping',
           'انعدام الأمن الغذائي (قدرة الصمود)', 'Food Insecurity (Resilience)',
           food_insec, '%', '',
           food_score,
           f'min(1.0, {_fmt(food_insec)} / 50) = {food_score:.3f}' if food_score else 'N/A',
           WB_SRC),
    ]

    # ════════════════════════════════════════════════════════════════════
    # Assemble hierarchy
    # ════════════════════════════════════════════════════════════════════
    return {
        'hazard': {
            'label_ar': 'المخاطر والتعرض',
            'label_en': 'Hazard & Exposure',
            'sections': [
                {'id': 'natural',    'label_ar': 'الكوارث الطبيعية',    'label_en': 'Natural Hazards',         'tiles': nat_tiles},
                {'id': 'epi',        'label_ar': 'الأمراض المعدية',     'label_en': 'Epidemiological Hazards', 'tiles': epi_tiles},
                {'id': 'infra',      'label_ar': 'مخاطر البنية التحتية','label_en': 'Infrastructure Hazards',  'tiles': infra_tiles},
                {'id': 'road',       'label_ar': 'سلامة الطرق',         'label_en': 'Road Safety',             'tiles': road_tiles},
            ],
        },
        'vulnerability': {
            'label_ar': 'الهشاشة',
            'label_en': 'Vulnerability',
            'sections': [
                {'id': 'displacement','label_ar': 'هشاشة النزوح',      'label_en': 'Displacement',            'tiles': disp_tiles},
                {'id': 'health_aware','label_ar': 'الوعي الصحي',       'label_en': 'Health & Lifestyle',      'tiles': health_tiles},
                {'id': 'urban',       'label_ar': 'التوسع العمراني',    'label_en': 'Urban Sprawl',            'tiles': urban_tiles},
                {'id': 'economic',    'label_ar': 'الهشاشة الاقتصادية','label_en': 'Economic Fragility',      'tiles': econ_tiles},
            ],
        },
        'coping': {
            'label_ar': 'القدرة على المواجهة',
            'label_en': 'Coping Capacity',
            'sections': [
                {'id': 'access',     'label_ar': 'إمكانية الوصول',     'label_en': 'Service Accessibility',  'tiles': access_tiles},
                {'id': 'data',       'label_ar': 'توافر البيانات',      'label_en': 'Data Availability',      'tiles': data_tiles},
                {'id': 'community',  'label_ar': 'الدعم المجتمعي',      'label_en': 'Community Support',      'tiles': comm_tiles},
                {'id': 'economic_c', 'label_ar': 'المرونة الاقتصادية',  'label_en': 'Economic Resilience',    'tiles': poverty_tiles},
            ],
        },
    }


# ---------------------------------------------------------------------------
# Pillar runner
# ---------------------------------------------------------------------------

def _run_pillars(jurisdiction_id: str, jurisdiction_config: dict) -> dict:
    """
    Load real connector data, run all three INFORM pillars, return structured result.
    Each pillar dict: score, level, label_ar, label_en, available, components, confidence
    """
    connector_data = _load_connector_data(jurisdiction_id)
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
            score     = raw.get('score')
            available = raw.get('available', False)
            if available and score is not None:
                available_scores.append(float(score))
            # Domain modules return sub_domains (hazard) or indicators (vuln/coping):
            # {key: {score, weight, proxy_used}}. Flatten to {key: float_score} for template.
            sub_domains = raw.get('sub_domains') or raw.get('indicators') or raw.get('components', {})
            components = {}
            for k, v in sub_domains.items():
                if isinstance(v, dict):
                    components[k] = v.get('score')
                elif isinstance(v, (int, float)):
                    components[k] = float(v)
            level = _score_to_level(score if available else None)
            results[pillar_key] = {
                'score':        round(float(score), 4) if score is not None else None,
                'available':    available,
                'confidence':   raw.get('data_coverage', raw.get('confidence', 0.0)),
                'components':   components,
                'proxy_flags':  {k: v.get('proxy_used', False) for k, v in sub_domains.items() if isinstance(v, dict)},
                'dominant':     raw.get('dominant_factor', ''),
                'data_sources': raw.get('data_sources', []),
                'level':        level,
                'badge':        _level_badge(level),
                'label_ar':     LEVEL_LABELS_AR[level],
                'label_en':     LEVEL_LABELS_EN[level],
            }
        except Exception as e:
            logger.error(f"Pillar {pillar_key} failed for {jurisdiction_id}: {e}")
            results[pillar_key] = {
                'score': None, 'available': False, 'confidence': 0.0,
                'components': {}, 'dominant': '', 'data_sources': [],
                'level': 'unavailable', 'badge': 'secondary',
                'label_ar': LEVEL_LABELS_AR['unavailable'],
                'label_en': LEVEL_LABELS_EN['unavailable'],
            }

    h = results['hazard']
    v = results['vulnerability']
    c = results['coping']

    if h['available'] and v['available'] and c['available']:
        inform_score = _compute_inform_score(h['score'], v['score'], c['score'])
        inform_level = _score_to_level(inform_score)
        results['inform_score'] = {
            'score':    inform_score,
            'available': True,
            'level':    inform_level,
            'badge':    _level_badge(inform_level),
            'label_ar': LEVEL_LABELS_AR[inform_level],
            'label_en': LEVEL_LABELS_EN[inform_level],
            'formula_values': {
                'h': round(h['score'] * 10, 1),
                'v': round(v['score'] * 10, 1),
                'c': round(c['score'] * 10, 1),
                'result': round(inform_score * 10, 1),
            },
        }
    elif available_scores:
        proxy = round(sum(available_scores) / len(available_scores), 4)
        inform_level = _score_to_level(proxy)
        results['inform_score'] = {
            'score': proxy, 'available': False, 'proxy': True,
            'pillars_available': len(available_scores),
            'level':    inform_level,
            'badge':    _level_badge(inform_level),
            'label_ar': LEVEL_LABELS_AR[inform_level],
            'label_en': LEVEL_LABELS_EN[inform_level],
        }
    else:
        results['inform_score'] = {
            'score': None, 'available': False, 'proxy': False,
            'level': 'unavailable', 'badge': 'secondary',
            'label_ar': LEVEL_LABELS_AR['unavailable'],
            'label_en': LEVEL_LABELS_EN['unavailable'],
        }

    results['all_unavailable'] = not any(
        results[k]['available'] for k in ('hazard', 'vulnerability', 'coping')
    )
    results['connector_data'] = connector_data

    return results


# ---------------------------------------------------------------------------
# Route
# ---------------------------------------------------------------------------

@dashboard_bp.route('/dashboard/<jurisdiction_id>')
def dashboard(jurisdiction_id):
    """INFORM risk dashboard for a Libya municipality or the national assessment."""
    try:
        jm = _get_jm()

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

        pillar_data     = _run_pillars(jurisdiction_id, jurisdiction_config)
        cd              = pillar_data.get('connector_data', {})
        show_work       = _build_show_work(cd)
        indicator_tiles = _build_indicator_tiles(cd)

        return render_template(
            'dashboard.html',
            jurisdiction=jurisdiction,
            is_national=is_national,
            pillar_data=pillar_data,
            show_work=show_work,
            indicator_tiles=indicator_tiles,
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
