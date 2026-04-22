import json
import logging
import os
from typing import Dict, Any, Optional, Tuple

from utils.risk_calculation import calculate_residual_risk, get_health_impact_factor
from utils.svi_data import get_svi_data

logger = logging.getLogger(__name__)

_climate_projections_cache = None
_thunderstorm_severity_cache = None
_real_data_cache = {}

TRIBAL_COUNTY_MAPPING = {
    'HoChunk': 'Jackson',
    'Ho-Chunk': 'Jackson',
    'Menominee': 'Menominee',
    'Oneida': 'Brown',
    'Lac du Flambeau': 'Vilas',
    'Bad River': 'Ashland',
    'Red Cliff': 'Bayfield',
    'Potawatomi': 'Forest',
    'St. Croix': 'Burnett',
    'Sokaogon': 'Forest',
    'Lac Courte Oreilles': 'Sawyer'
}

TRIBAL_KEYWORDS = ['Ho-Chunk', 'HoChunk', 'Menominee', 'Oneida', 'Lac du Flambeau',
                   'Bad River', 'Red Cliff', 'Potawatomi', 'St. Croix', 'Sokaogon',
                   'Lac Courte Oreilles']

EOC_COUNTIES = ['Milwaukee', 'Dane', 'Brown', 'Waukesha', 'Racine',
                'La Crosse', 'Outagamie', 'Marathon', 'Eau Claire', 'Winnebago']

NORTHERN_TREE_COUNTIES = ['Bayfield', 'Ashland', 'Iron', 'Vilas', 'Forest',
                          'Florence', 'Marinette', 'Oconto', 'Langlade']


def _calculate_em_resilience(svi: Dict[str, float], census: Dict[str, float],
                             county_name: str) -> float:
    resilience_raw = 0.45
    resilience_raw += ((1.0 - svi['socioeconomic']) * 0.10)
    resilience_raw += ((1.0 - svi['housing_transportation']) * 0.15)
    if county_name in EOC_COUNTIES:
        resilience_raw += 0.20
    if census['population'] > 75000:
        resilience_raw += 0.10
    return max(0.1, min(0.9, resilience_raw))


def _resolve_tribal_county(county_name: str) -> str:
    for tribal_name, mapped in TRIBAL_COUNTY_MAPPING.items():
        if tribal_name in county_name:
            logger.info(f"Using {mapped} County data for {county_name}")
            return mapped
    return county_name


def _is_tribal(county_name: str) -> bool:
    return any(t in county_name for t in TRIBAL_KEYWORDS)


def load_climate_projections() -> Dict[str, Any]:
    global _climate_projections_cache
    if _climate_projections_cache is not None:
        return _climate_projections_cache

    try:
        path = 'data/climate/natural_hazard_climate_projections.json'
        if os.path.exists(path):
            with open(path) as f:
                _climate_projections_cache = json.load(f)
            logger.info("Loaded climate projections for natural hazards")
            return _climate_projections_cache
    except Exception as e:
        logger.warning(f"Error loading climate projections: {e}")

    _climate_projections_cache = {}
    return _climate_projections_cache


def get_climate_zone(county_name: str) -> str:
    projections = load_climate_projections()
    zones = projections.get('county_climate_zones', {})
    for zone, counties in zones.items():
        if county_name in counties:
            return zone
    return 'central_wisconsin'


def get_climate_multiplier(county_name: str, hazard_type: str) -> float:
    projections = load_climate_projections()
    hazard_data = projections.get(hazard_type, {})

    base_multiplier = hazard_data.get('exposure_multiplier', 1.0)
    regional = hazard_data.get('regional_variation', {})
    zone = get_climate_zone(county_name)
    regional_multiplier = regional.get(zone, base_multiplier)

    return regional_multiplier


def get_thunderstorm_severity(county_name: str) -> float:
    global _thunderstorm_severity_cache
    if _thunderstorm_severity_cache is None:
        projections = load_climate_projections()
        ts_data = projections.get('wisconsin_thunderstorm_severity', {})
        _thunderstorm_severity_cache = ts_data.get('counties', {})
    return _thunderstorm_severity_cache.get(county_name, 0.40)


def get_all_svi_themes(county_name: str) -> Dict[str, float]:
    svi_data = get_svi_data(county_name)
    return {
        'overall': svi_data.get('overall', 0.5),
        'socioeconomic': svi_data.get('socioeconomic', 0.5),
        'household_composition': svi_data.get('household_composition', 0.5),
        'minority_status': svi_data.get('minority_status', 0.5),
        'housing_transportation': svi_data.get('housing_transportation', 0.5)
    }


def _get_real_storm_data(county_name: str) -> Optional[Dict[str, Any]]:
    cache_key = f"storm_{county_name}"
    if cache_key in _real_data_cache:
        return _real_data_cache[cache_key]
    try:
        from utils.noaa_storm_events import get_county_storm_summary
        data = get_county_storm_summary(county_name)
        _real_data_cache[cache_key] = data
        return data
    except Exception as e:
        logger.debug(f"NOAA storm data not available for {county_name}: {e}")
        _real_data_cache[cache_key] = None
        return None


def _get_real_openfema_data(county_name: str) -> Dict[str, Any]:
    cache_key = f"fema_{county_name}"
    if cache_key in _real_data_cache:
        return _real_data_cache[cache_key]
    try:
        from utils.openfema_data import get_county_openfema_summary
        data = get_county_openfema_summary(county_name)
        _real_data_cache[cache_key] = data
        return data
    except Exception as e:
        logger.debug(f"OpenFEMA data not available for {county_name}: {e}")
        data = {"disaster_declarations": None, "nfip_claims": None, "hma_projects": None}
        _real_data_cache[cache_key] = data
        return data


def _format_damage(amount: float) -> str:
    if amount >= 1_000_000_000:
        return f"${amount / 1_000_000_000:.1f}B"
    elif amount >= 1_000_000:
        return f"${amount / 1_000_000:.1f}M"
    elif amount >= 1_000:
        return f"${amount / 1_000:.0f}K"
    elif amount > 0:
        return f"${amount:.0f}"
    return "$0"


def get_census_demographics(county_name: str) -> Dict[str, float]:
    try:
        from utils.census_data_loader import wisconsin_census
        elderly_pct = wisconsin_census.get_elderly_population_percentage(county_name) or 18.7
        mobile_home_pct = wisconsin_census.get_mobile_home_percentage(county_name) or 5.2
        population = wisconsin_census.get_county_population(county_name) or 80000
    except Exception as e:
        logger.warning(f"Census data loading failed for {county_name}: {e}")
        elderly_pct = 18.7
        mobile_home_pct = 5.2
        population = 80000

    elderly_factor = min(1.0, max(0.05, (elderly_pct - 10.0) / 25.0))
    mobile_home_factor = min(1.0, mobile_home_pct / 20.0)
    pop_density_factor = min(1.0, population / 300000.0)

    return {
        'elderly_pct': elderly_pct,
        'elderly_factor': elderly_factor,
        'mobile_home_pct': mobile_home_pct,
        'mobile_home_factor': mobile_home_factor,
        'population': population,
        'pop_density_factor': pop_density_factor
    }


def calculate_enhanced_flood_risk(county_name: str, discipline: str = 'public_health') -> Dict[str, Any]:
    original_name = county_name
    if _is_tribal(county_name):
        county_name = _resolve_tribal_county(county_name)

    from utils.data_processor import load_nri_data
    county_risk = load_nri_data().get(county_name, {'flood_risk': 0.3})
    base_flood_risk = county_risk.get('flood_risk', 0.3)

    svi = get_all_svi_themes(county_name)
    census = get_census_demographics(county_name)
    climate_mult = get_climate_multiplier(county_name, 'flood')
    health_factor = get_health_impact_factor(county_name, 'flood')

    river_counties = ['Buffalo', 'Crawford', 'Grant', 'La Crosse', 'Pepin', 'Pierce',
                      'Trempealeau', 'Vernon', 'Richland', 'Sauk', 'Columbia', 'Dodge',
                      'Jefferson', 'Waukesha', 'Milwaukee', 'Racine', 'Kenosha']
    lake_counties = ['Bayfield', 'Douglas', 'Ashland', 'Iron', 'Vilas', 'Florence',
                     'Marinette', 'Oconto', 'Brown', 'Kewaunee', 'Door', 'Manitowoc',
                     'Sheboygan', 'Ozaukee', 'Milwaukee', 'Racine', 'Kenosha']
    flat_terrain_counties = ['Columbia', 'Dodge', 'Fond du Lac', 'Green Lake', 'Marquette',
                             'Winnebago', 'Calumet', 'Outagamie', 'Brown']
    high_precip_counties = ['Bayfield', 'Douglas', 'Ashland', 'Iron', 'Vilas', 'Florence']

    exposure_factors = {
        'historical_nri': base_flood_risk * 0.7,
        'proximity_to_water': 0.0,
        'terrain_risk': 0.15,
        'precipitation_patterns': 0.15,
        'climate_trend': min(1.0, base_flood_risk * climate_mult) - base_flood_risk
    }

    if county_name in river_counties:
        exposure_factors['proximity_to_water'] += 0.3
    if county_name in lake_counties:
        exposure_factors['proximity_to_water'] += 0.2
    if county_name in flat_terrain_counties:
        exposure_factors['terrain_risk'] = 0.25
    if county_name in high_precip_counties:
        exposure_factors['precipitation_patterns'] = 0.25

    exposure_score = min(1.0, (
        (exposure_factors['historical_nri'] * 0.55) +
        (exposure_factors['proximity_to_water'] * 0.15) +
        (exposure_factors['terrain_risk'] * 0.10) +
        (exposure_factors['precipitation_patterns'] * 0.10) +
        (exposure_factors['climate_trend'] * 0.10)
    ))

    if discipline == 'em':
        infrastructure_density = census['pop_density_factor']
        rural_isolation = max(0.0, min(1.0, 1.0 - census['pop_density_factor']))
        vulnerability_score = min(1.0, (
            (svi['housing_transportation'] * 0.35) +
            (svi['socioeconomic'] * 0.10) +
            (svi['household_composition'] * 0.05) +
            (svi['minority_status'] * 0.05) +
            (infrastructure_density * 0.15) +
            (census['mobile_home_factor'] * 0.10) +
            (census['elderly_factor'] * 0.05) +
            (rural_isolation * 0.15)
        ))
        resilience_raw = _calculate_em_resilience(svi, census, county_name)
    else:
        vulnerability_score = min(1.0, (
            (svi['housing_transportation'] * 0.30) +
            (svi['socioeconomic'] * 0.20) +
            (svi['household_composition'] * 0.15) +
            (svi['minority_status'] * 0.10) +
            (census['elderly_factor'] * 0.15) +
            (census['mobile_home_factor'] * 0.10)
        ))

        resilience_raw = 0.5
        resilience_raw += ((1.0 - svi['socioeconomic']) * 0.20)
        resilience_raw += ((1.0 - svi['housing_transportation']) * 0.10)

        protected_counties = ['Milwaukee', 'Dane', 'Brown', 'Waukesha', 'Racine']
        if county_name in protected_counties:
            resilience_raw += 0.20
        elif county_name in ['La Crosse', 'Outagamie', 'Rock', 'Kenosha']:
            resilience_raw += 0.10

        resilience_raw = max(0.1, min(0.9, resilience_raw))

    residual_risk = calculate_residual_risk(
        exposure=exposure_score,
        vulnerability=vulnerability_score,
        resilience=resilience_raw,
        health_impact_factor=health_factor
    )

    storm_data = _get_real_storm_data(county_name)
    openfema = _get_real_openfema_data(county_name)

    flood_storm = storm_data.get('by_category', {}).get('flood', {}) if storm_data else {}
    nfip_data = openfema.get('nfip_claims')
    decl_data = openfema.get('disaster_declarations')
    hma_data = openfema.get('hma_projects')

    flood_decl_count = 0
    if decl_data:
        for itype in ['Flood', 'Coastal', 'Severe Storm(s)']:
            flood_decl_count += decl_data.get('by_incident_type', {}).get(itype, 0)

    metrics = {
        'historical_flood_events': flood_storm.get('event_count') if flood_storm.get('event_count') else None,
        'flood_property_damage': _format_damage(flood_storm.get('property_damage', 0)) if flood_storm.get('property_damage') else None,
        'flood_injuries': flood_storm.get('injuries', 0) if flood_storm else None,
        'nfip_claims_total': nfip_data.get('total_claims') if nfip_data else None,
        'nfip_total_payout': _format_damage(nfip_data.get('total_payout', 0)) if nfip_data else None,
        'federal_flood_declarations': flood_decl_count if decl_data else None,
        'mitigation_projects': hma_data.get('total_projects') if hma_data else None,
        'mitigation_federal_funding': _format_damage(hma_data.get('total_federal_share', 0)) if hma_data else None,
        'climate_trend_impact': f"+{int((climate_mult - 1.0) * 100)}%",
        'elderly_vulnerability_pct': round(census['elderly_pct'], 1),
        'mobile_home_vulnerability_pct': round(census['mobile_home_pct'], 1),
        'data_period': storm_data.get('years_covered', 'N/A') if storm_data else None,
        'has_real_data': bool(flood_storm.get('event_count') or nfip_data or decl_data)
    }

    data_sources = [
        'FEMA National Risk Index (NRI) - Census Tract Level',
        'CDC Social Vulnerability Index (SVI) - All 4 Themes',
        'U.S. Census Bureau ACS - Housing & Demographics',
        'NOAA/WICCI Climate Projections (2030-2050)',
        'FEMA NRI Health Impact Factor',
        'NOAA NCEI Storm Events Database',
        'OpenFEMA NFIP Redacted Claims',
        'OpenFEMA Disaster Declarations Summaries'
    ]

    return {
        'overall': residual_risk,
        'components': {
            'exposure': exposure_score,
            'vulnerability': vulnerability_score,
            'resilience': resilience_raw,
            'health_impact': health_factor,
            'climate_multiplier': climate_mult
        },
        'exposure_factors': exposure_factors,
        'vulnerability_breakdown': {
            'housing_transportation_svi': svi['housing_transportation'],
            'socioeconomic_svi': svi['socioeconomic'],
            'household_composition_svi': svi['household_composition'],
            'minority_status_svi': svi['minority_status'],
            'elderly_factor': census['elderly_factor'],
            'mobile_home_factor': census['mobile_home_factor']
        },
        'metrics': metrics,
        'data_sources': data_sources
    }


def calculate_enhanced_tornado_risk(county_name: str, discipline: str = 'public_health') -> Dict[str, Any]:
    original_name = county_name
    if _is_tribal(county_name):
        county_name = _resolve_tribal_county(county_name)

    from utils.data_processor import load_nri_data
    county_risk = load_nri_data().get(county_name, {'tornado_risk': 0.3})
    base_tornado_risk = county_risk.get('tornado_risk', 0.3)

    svi = get_all_svi_themes(county_name)
    census = get_census_demographics(county_name)
    climate_mult = get_climate_multiplier(county_name, 'tornado')
    health_factor = get_health_impact_factor(county_name, 'tornado')

    tornado_alley_counties = ['Grant', 'Iowa', 'Lafayette', 'Green', 'Rock', 'Walworth',
                              'Jefferson', 'Waukesha', 'Dane', 'Columbia', 'Sauk']
    open_terrain_counties = ['Columbia', 'Dodge', 'Fond du Lac', 'Green Lake', 'Marquette',
                             'Winnebago', 'Calumet', 'Outagamie', 'Brown', 'Rock', 'Walworth']

    exposure_factors = {
        'historical_nri': base_tornado_risk * 0.8,
        'tornado_alley_proximity': 0.2,
        'terrain_factors': 0.1,
        'climate_trend': min(1.0, base_tornado_risk * climate_mult) - base_tornado_risk
    }

    if county_name in tornado_alley_counties:
        exposure_factors['tornado_alley_proximity'] = 0.4
    if county_name in open_terrain_counties:
        exposure_factors['terrain_factors'] = 0.3

    exposure_score = min(1.0, (
        (exposure_factors['historical_nri'] * 0.55) +
        (exposure_factors['tornado_alley_proximity'] * 0.20) +
        (exposure_factors['terrain_factors'] * 0.10) +
        (exposure_factors['climate_trend'] * 0.15)
    ))

    if discipline == 'em':
        infrastructure_density = census['pop_density_factor']
        vulnerability_score = min(1.0, (
            (svi['housing_transportation'] * 0.30) +
            (svi['socioeconomic'] * 0.10) +
            (svi['household_composition'] * 0.05) +
            (svi['minority_status'] * 0.05) +
            (infrastructure_density * 0.15) +
            (census['mobile_home_factor'] * 0.25) +
            (census['elderly_factor'] * 0.05) +
            (census['pop_density_factor'] * 0.05)
        ))
        resilience_raw = _calculate_em_resilience(svi, census, county_name)
    else:
        vulnerability_score = min(1.0, (
            (svi['housing_transportation'] * 0.25) +
            (svi['socioeconomic'] * 0.15) +
            (svi['household_composition'] * 0.10) +
            (svi['minority_status'] * 0.10) +
            (census['mobile_home_factor'] * 0.25) +
            (census['elderly_factor'] * 0.10) +
            (census['pop_density_factor'] * 0.05)
        ))

        resilience_raw = 0.5
        resilience_raw += ((1.0 - svi['socioeconomic']) * 0.20)
        resilience_raw += ((1.0 - svi['housing_transportation']) * 0.10)

        prepared_counties = ['Milwaukee', 'Dane', 'Brown', 'Waukesha', 'La Crosse']
        if county_name in prepared_counties:
            resilience_raw += 0.20
        elif county_name in ['Outagamie', 'Rock', 'Kenosha', 'Marathon']:
            resilience_raw += 0.10

        urban_counties = ['Milwaukee', 'Dane', 'Waukesha', 'Brown', 'Racine', 'Kenosha']
        if county_name in urban_counties:
            resilience_raw -= 0.05

        resilience_raw = max(0.1, min(0.9, resilience_raw))

    residual_risk = calculate_residual_risk(
        exposure=exposure_score,
        vulnerability=vulnerability_score,
        resilience=resilience_raw,
        health_impact_factor=health_factor
    )

    storm_data = _get_real_storm_data(county_name)
    openfema = _get_real_openfema_data(county_name)

    tornado_storm = storm_data.get('by_category', {}).get('tornado', {}) if storm_data else {}
    decl_data = openfema.get('disaster_declarations')

    tornado_decl_count = 0
    if decl_data:
        tornado_decl_count = decl_data.get('by_incident_type', {}).get('Tornado', 0)

    tornado_mags = storm_data.get('tornado_magnitudes', []) if storm_data else []
    avg_ef = None
    if tornado_mags:
        ef_values = []
        for m in tornado_mags:
            m_clean = m.replace('EF', '').replace('F', '').strip()
            try:
                ef_values.append(int(m_clean))
            except (ValueError, TypeError):
                pass
        if ef_values:
            avg_ef = round(sum(ef_values) / len(ef_values), 1)

    metrics = {
        'historical_tornado_events': tornado_storm.get('event_count') if tornado_storm.get('event_count') else None,
        'average_ef_rating': avg_ef,
        'tornado_property_damage': _format_damage(tornado_storm.get('property_damage', 0)) if tornado_storm.get('property_damage') else None,
        'tornado_injuries': tornado_storm.get('injuries', 0) if tornado_storm else None,
        'tornado_fatalities': tornado_storm.get('fatalities', 0) if tornado_storm else None,
        'federal_tornado_declarations': tornado_decl_count if decl_data else None,
        'climate_trend_impact': f"+{int((climate_mult - 1.0) * 100)}%",
        'mobile_home_vulnerability_pct': round(census['mobile_home_pct'], 1),
        'data_period': storm_data.get('years_covered', 'N/A') if storm_data else None,
        'has_real_data': bool(tornado_storm.get('event_count') or decl_data)
    }

    data_sources = [
        'FEMA National Risk Index (NRI) - Census Tract Level',
        'CDC Social Vulnerability Index (SVI) - All 4 Themes',
        'U.S. Census Bureau ACS - Housing & Demographics',
        'NOAA/IPCC Climate Projections (2030-2050)',
        'FEMA NRI Health Impact Factor',
        'NOAA NCEI Storm Events Database',
        'OpenFEMA Disaster Declarations Summaries'
    ]

    return {
        'overall': residual_risk,
        'components': {
            'exposure': exposure_score,
            'vulnerability': vulnerability_score,
            'resilience': resilience_raw,
            'health_impact': health_factor,
            'climate_multiplier': climate_mult
        },
        'exposure_factors': exposure_factors,
        'vulnerability_breakdown': {
            'housing_transportation_svi': svi['housing_transportation'],
            'socioeconomic_svi': svi['socioeconomic'],
            'household_composition_svi': svi['household_composition'],
            'minority_status_svi': svi['minority_status'],
            'mobile_home_factor': census['mobile_home_factor'],
            'elderly_factor': census['elderly_factor'],
            'pop_density_factor': census['pop_density_factor']
        },
        'metrics': metrics,
        'data_sources': data_sources
    }


def calculate_enhanced_winter_storm_risk(county_name: str, discipline: str = 'public_health') -> Dict[str, Any]:
    original_name = county_name
    if _is_tribal(county_name):
        county_name = _resolve_tribal_county(county_name)

    from utils.data_processor import load_nri_data
    county_risk = load_nri_data().get(county_name, {'winter_storm_risk': 0.3})
    base_winter_risk = county_risk.get('winter_storm_risk', 0.3)

    svi = get_all_svi_themes(county_name)
    census = get_census_demographics(county_name)
    climate_mult = get_climate_multiplier(county_name, 'winter_storm')
    health_factor = get_health_impact_factor(county_name, 'winter_storm')

    northern_counties = ['Douglas', 'Bayfield', 'Ashland', 'Iron', 'Vilas', 'Forest',
                         'Florence', 'Marinette', 'Langlade', 'Lincoln', 'Sawyer',
                         'Price', 'Oneida', 'Taylor', 'Rusk', 'Barron', 'Washburn',
                         'Burnett', 'Polk', 'Chippewa']
    lake_effect_counties = ['Bayfield', 'Douglas', 'Ashland', 'Iron', 'Vilas', 'Florence',
                            'Kenosha', 'Racine', 'Milwaukee', 'Ozaukee', 'Sheboygan',
                            'Manitowoc', 'Kewaunee', 'Door', 'Brown', 'Oconto', 'Marinette']

    exposure_factors = {
        'historical_nri': base_winter_risk * 0.8,
        'northern_location': 0.2,
        'lake_effect': 0.1,
        'climate_trend': 0.0
    }

    if county_name in northern_counties:
        exposure_factors['northern_location'] = 0.6
    elif county_name in ['Marathon', 'Clark', 'Eau Claire', 'Dunn', 'St. Croix']:
        exposure_factors['northern_location'] = 0.4

    if county_name in lake_effect_counties:
        exposure_factors['lake_effect'] = 0.5

    climate_ice_storm_boost = 0.0
    climate_data = load_climate_projections().get('winter_storm', {}).get('sub_factors', {})
    ice_storm_mult = climate_data.get('ice_storm_frequency', 1.0)
    climate_ice_storm_boost = max(0, (ice_storm_mult - 1.0) * 0.3)
    exposure_factors['climate_trend'] = min(0.15, (climate_mult - 1.0) * base_winter_risk + climate_ice_storm_boost)

    exposure_score = min(1.0, (
        (exposure_factors['historical_nri'] * 0.50) +
        (exposure_factors['northern_location'] * 0.20) +
        (exposure_factors['lake_effect'] * 0.10) +
        (exposure_factors['climate_trend'] * 0.20)
    ))

    vulnerable_grid_counties = ['Bayfield', 'Ashland', 'Iron', 'Vilas', 'Forest',
                                'Florence', 'Sawyer', 'Price', 'Oneida', 'Lincoln']
    moderate_grid_counties = ['Washburn', 'Burnett', 'Polk', 'Barron', 'Rusk',
                              'Taylor', 'Langlade', 'Oconto', 'Marinette']
    rural_counties = ['Bayfield', 'Ashland', 'Iron', 'Vilas', 'Forest', 'Florence',
                      'Sawyer', 'Price', 'Burnett', 'Washburn', 'Polk', 'Rusk']

    power_grid_vuln = 0.3
    if county_name in vulnerable_grid_counties:
        power_grid_vuln = 0.7
    elif county_name in moderate_grid_counties:
        power_grid_vuln = 0.5

    rural_isolation = 0.3
    if county_name in rural_counties:
        rural_isolation = 0.7
    elif county_name in ['Barron', 'Taylor', 'Lincoln', 'Langlade', 'Oconto', 'Marinette',
                          'Shawano', 'Waupaca', 'Clark', 'Marathon']:
        rural_isolation = 0.5

    if discipline == 'em':
        em_power_grid_vuln = svi['housing_transportation']
        if county_name in rural_counties or county_name in moderate_grid_counties:
            em_power_grid_vuln = min(1.0, em_power_grid_vuln + 0.15)
        em_rural_isolation = max(0.0, min(1.0, 1.0 - census['pop_density_factor']))
        vulnerability_score = min(1.0, (
            (svi['housing_transportation'] * 0.25) +
            (svi['socioeconomic'] * 0.05) +
            (svi['household_composition'] * 0.05) +
            (svi['minority_status'] * 0.05) +
            (em_power_grid_vuln * 0.25) +
            (em_rural_isolation * 0.20) +
            (census['mobile_home_factor'] * 0.05) +
            (census['elderly_factor'] * 0.10)
        ))
        resilience_raw = _calculate_em_resilience(svi, census, county_name)
    else:
        vulnerability_score = min(1.0, (
            (svi['housing_transportation'] * 0.20) +
            (svi['socioeconomic'] * 0.10) +
            (svi['household_composition'] * 0.15) +
            (svi['minority_status'] * 0.05) +
            (census['elderly_factor'] * 0.20) +
            (census['mobile_home_factor'] * 0.05) +
            (power_grid_vuln * 0.15) +
            (rural_isolation * 0.10)
        ))

        resilience_raw = 0.5
        resilience_raw += ((1.0 - svi['socioeconomic']) * 0.15)
        resilience_raw += ((1.0 - svi['housing_transportation']) * 0.10)

        prepared_counties = ['Milwaukee', 'Dane', 'Brown', 'Waukesha', 'La Crosse', 'Marathon']
        if county_name in prepared_counties:
            resilience_raw += 0.20

        if county_name in northern_counties:
            resilience_raw += 0.10

        resilience_raw = max(0.1, min(0.9, resilience_raw))

    residual_risk = calculate_residual_risk(
        exposure=exposure_score,
        vulnerability=vulnerability_score,
        resilience=resilience_raw,
        health_impact_factor=health_factor
    )

    storm_data = _get_real_storm_data(county_name)
    openfema = _get_real_openfema_data(county_name)

    winter_storm = storm_data.get('by_category', {}).get('winter', {}) if storm_data else {}
    decl_data = openfema.get('disaster_declarations')

    winter_decl_count = 0
    if decl_data:
        for itype in ['Snow', 'Ice Storm', 'Severe Ice Storm', 'Freezing']:
            winter_decl_count += decl_data.get('by_incident_type', {}).get(itype, 0)

    winter_event_breakdown = {}
    if winter_storm.get('event_types'):
        winter_event_breakdown = winter_storm['event_types']

    metrics = {
        'historical_winter_events': winter_storm.get('event_count') if winter_storm.get('event_count') else None,
        'winter_property_damage': _format_damage(winter_storm.get('property_damage', 0)) if winter_storm.get('property_damage') else None,
        'winter_injuries': winter_storm.get('injuries', 0) if winter_storm else None,
        'winter_fatalities': winter_storm.get('fatalities', 0) if winter_storm else None,
        'winter_event_breakdown': winter_event_breakdown if winter_event_breakdown else None,
        'federal_winter_declarations': winter_decl_count if decl_data else None,
        'climate_trend_impact': f"+{int((climate_mult - 1.0) * 100)}% intensity, +{int((ice_storm_mult - 1.0) * 100)}% ice storms",
        'elderly_vulnerability_pct': round(census['elderly_pct'], 1),
        'data_period': storm_data.get('years_covered', 'N/A') if storm_data else None,
        'has_real_data': bool(winter_storm.get('event_count') or decl_data)
    }

    data_sources = [
        'FEMA National Risk Index (NRI) - Census Tract Level',
        'CDC Social Vulnerability Index (SVI) - All 4 Themes',
        'U.S. Census Bureau ACS - Housing & Demographics',
        'NOAA/WICCI Climate Projections (2030-2050)',
        'FEMA NRI Health Impact Factor',
        'NOAA NCEI Storm Events Database'
    ]

    return {
        'overall': residual_risk,
        'components': {
            'exposure': exposure_score,
            'vulnerability': vulnerability_score,
            'resilience': resilience_raw,
            'health_impact': health_factor,
            'climate_multiplier': climate_mult
        },
        'exposure_factors': exposure_factors,
        'vulnerability_breakdown': {
            'housing_transportation_svi': svi['housing_transportation'],
            'socioeconomic_svi': svi['socioeconomic'],
            'household_composition_svi': svi['household_composition'],
            'minority_status_svi': svi['minority_status'],
            'elderly_factor': census['elderly_factor'],
            'mobile_home_factor': census['mobile_home_factor'],
            'power_grid_vulnerability': power_grid_vuln,
            'rural_isolation': rural_isolation
        },
        'metrics': metrics,
        'data_sources': data_sources
    }


def calculate_enhanced_thunderstorm_risk(county_name: str, discipline: str = 'public_health') -> Dict[str, Any]:
    original_name = county_name
    if _is_tribal(county_name):
        county_name = _resolve_tribal_county(county_name)

    thunderstorm_severity = get_thunderstorm_severity(county_name)

    svi = get_all_svi_themes(county_name)
    census = get_census_demographics(county_name)
    climate_mult = get_climate_multiplier(county_name, 'thunderstorm')
    health_factor = get_health_impact_factor(county_name, 'thunderstorm')

    high_thunderstorm_counties = ['Milwaukee', 'Waukesha', 'Washington', 'Ozaukee', 'Racine',
                                  'Kenosha', 'Walworth', 'Rock', 'Green', 'Lafayette', 'Grant']
    moderate_thunderstorm_counties = ['Iowa', 'Dane', 'Jefferson', 'Dodge', 'Columbia',
                                     'Sauk', 'Richland', 'Crawford', 'Vernon', 'La Crosse']

    lightning_density = 0.35
    heavy_rainfall_freq = 0.40
    if county_name in high_thunderstorm_counties:
        lightning_density = 0.70
        heavy_rainfall_freq = 0.65
    elif county_name in moderate_thunderstorm_counties:
        lightning_density = 0.50
        heavy_rainfall_freq = 0.55

    exposure_factors = {
        'noaa_severity_index': thunderstorm_severity * 0.8,
        'lightning_density': lightning_density,
        'heavy_rainfall_frequency': heavy_rainfall_freq,
        'climate_trend': min(0.15, (climate_mult - 1.0) * thunderstorm_severity)
    }

    exposure_score = min(1.0, (
        (exposure_factors['noaa_severity_index'] * 0.40) +
        (exposure_factors['lightning_density'] * 0.20) +
        (exposure_factors['heavy_rainfall_frequency'] * 0.20) +
        (exposure_factors['climate_trend'] * 0.20)
    ))

    flood_prone_counties = ['Milwaukee', 'Racine', 'Kenosha', 'Waukesha', 'Washington',
                            'Ozaukee', 'Crawford', 'Grant', 'Vernon', 'La Crosse']
    high_tree_counties = ['Bayfield', 'Douglas', 'Ashland', 'Iron', 'Vilas', 'Forest',
                          'Florence', 'Marinette', 'Oconto', 'Shawano', 'Menominee']
    moderate_tree_counties = ['Oneida', 'Lincoln', 'Langlade', 'Marathon', 'Waupaca',
                              'Outagamie', 'Sheboygan', 'Washington', 'Waukesha']

    flood_suscept = 0.4
    if county_name in flood_prone_counties:
        flood_suscept = 0.7
    tree_coverage = 0.4
    if county_name in high_tree_counties:
        tree_coverage = 0.8
    elif county_name in moderate_tree_counties:
        tree_coverage = 0.6

    if discipline == 'em':
        infrastructure_density = census['pop_density_factor']
        em_tree_coverage = 0.4 if county_name in NORTHERN_TREE_COUNTIES else 0.25
        em_flood_suscept = flood_suscept if flood_suscept != 0.4 else 0.3
        vulnerability_score = min(1.0, (
            (svi['housing_transportation'] * 0.30) +
            (svi['socioeconomic'] * 0.05) +
            (svi['household_composition'] * 0.05) +
            (svi['minority_status'] * 0.05) +
            (infrastructure_density * 0.15) +
            (em_tree_coverage * 0.15) +
            (em_flood_suscept * 0.15) +
            (census['mobile_home_factor'] * 0.10)
        ))
        resilience_raw = _calculate_em_resilience(svi, census, county_name)
    else:
        vulnerability_score = min(0.90, (
            (svi['housing_transportation'] * 0.25) +
            (svi['socioeconomic'] * 0.10) +
            (svi['household_composition'] * 0.10) +
            (svi['minority_status'] * 0.05) +
            (census['elderly_factor'] * 0.10) +
            (census['mobile_home_factor'] * 0.10) +
            (flood_suscept * 0.15) +
            (tree_coverage * 0.15)
        ))

        resilience_raw = 0.5
        resilience_raw += ((1.0 - svi['socioeconomic']) * 0.15)
        resilience_raw += ((1.0 - svi['housing_transportation']) * 0.10)

        high_resilience_counties = ['Milwaukee', 'Dane', 'Brown', 'Waukesha', 'Racine', 'Kenosha']
        moderate_resilience_counties = ['Outagamie', 'Rock', 'La Crosse', 'Marathon', 'Eau Claire', 'Sheboygan']
        if county_name in high_resilience_counties:
            resilience_raw += 0.20
        elif county_name in moderate_resilience_counties:
            resilience_raw += 0.10

        resilience_raw = max(0.1, min(0.9, resilience_raw))

    residual_risk = calculate_residual_risk(
        exposure=exposure_score,
        vulnerability=vulnerability_score,
        resilience=resilience_raw,
        health_impact_factor=health_factor
    )

    storm_data = _get_real_storm_data(county_name)

    ts_storm = storm_data.get('by_category', {}).get('thunderstorm', {}) if storm_data else {}

    ts_event_breakdown = {}
    if ts_storm.get('event_types'):
        ts_event_breakdown = ts_storm['event_types']

    metrics = {
        'historical_thunderstorm_events': ts_storm.get('event_count') if ts_storm.get('event_count') else None,
        'thunderstorm_property_damage': _format_damage(ts_storm.get('property_damage', 0)) if ts_storm.get('property_damage') else None,
        'thunderstorm_injuries': ts_storm.get('injuries', 0) if ts_storm else None,
        'thunderstorm_fatalities': ts_storm.get('fatalities', 0) if ts_storm else None,
        'thunderstorm_event_breakdown': ts_event_breakdown if ts_event_breakdown else None,
        'climate_trend_impact': f"+{int((climate_mult - 1.0) * 100)}%",
        'noaa_severity_index': round(thunderstorm_severity, 2),
        'data_period': storm_data.get('years_covered', 'N/A') if storm_data else None,
        'has_real_data': bool(ts_storm.get('event_count'))
    }

    data_sources = [
        'NOAA NCEI Storm Events Database',
        'CDC Social Vulnerability Index (SVI) - All 4 Themes',
        'U.S. Census Bureau ACS - Housing & Demographics',
        'EPA/NOAA Climate Projections (2030-2050)',
        'FEMA NRI Health Impact Factor'
    ]

    return {
        'overall': residual_risk,
        'components': {
            'exposure': exposure_score,
            'vulnerability': vulnerability_score,
            'resilience': resilience_raw,
            'health_impact': health_factor,
            'climate_multiplier': climate_mult
        },
        'exposure_factors': exposure_factors,
        'vulnerability_breakdown': {
            'housing_transportation_svi': svi['housing_transportation'],
            'socioeconomic_svi': svi['socioeconomic'],
            'household_composition_svi': svi['household_composition'],
            'minority_status_svi': svi['minority_status'],
            'elderly_factor': census['elderly_factor'],
            'mobile_home_factor': census['mobile_home_factor'],
            'flood_susceptibility': flood_suscept,
            'tree_coverage': tree_coverage
        },
        'metrics': metrics,
        'data_sources': data_sources
    }
