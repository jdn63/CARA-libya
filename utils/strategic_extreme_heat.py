"""
Strategic Extreme Heat Risk Assessment Module

Focused on climate change projections and multi-year heat trends for annual strategic planning.
Replaces current temperature data with historical analysis and future climate modeling.
"""

import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Tuple
import numpy as np
import json
from utils.persistent_cache import get_from_persistent_cache, set_in_persistent_cache
from utils.planning_mode_config import get_planning_mode

logger = logging.getLogger(__name__)

class StrategicExtremeHeatAssessment:
    """
    Strategic extreme heat risk assessment focusing on climate projections and long-term
    adaptation planning rather than current temperature conditions.
    """
    
    def __init__(self):
        self.planning_mode = get_planning_mode("annual_strategic")
        self.cache_duration = 86400 * 30  # 30-day cache for strategic planning data
        
        # Wisconsin climate change projections (2025-2050)
        # Source: Wisconsin Initiative on Climate Change Impacts (WICCI) 2021 Assessment
        self.climate_projections = {
            'temperature_increase': {
                'annual_avg': 4.5,      # °F increase by 2050 (mid-range scenario)
                'summer_max': 6.2,      # °F increase in summer maximum temperatures  
                'heat_wave_intensity': 7.1  # °F increase in peak heat wave temperatures
            },
            'frequency_changes': {
                'days_above_90f': 2.8,    # 2.8x increase in days above 90°F
                'days_above_95f': 4.2,    # 4.2x increase in days above 95°F  
                'heat_wave_frequency': 3.5, # 3.5x increase in heat wave events
                'consecutive_hot_days': 2.1  # 2.1x increase in multi-day heat events
            },
            'duration_changes': {
                'heat_wave_length': 1.9,   # 90% increase in heat wave duration
                'cooling_relief': 0.7      # 30% decrease in nighttime cooling
            }
        }
        
        # Wisconsin county baseline heat vulnerability (historical 2010-2020 analysis)
        # Based on CDC Social Vulnerability Index and Wisconsin DHS heat mortality data
        self.county_baseline_vulnerability = {
            'milwaukee': 0.82, 'dane': 0.45, 'brown': 0.58, 'waukesha': 0.52, 'winnebago': 0.61,
            'rock': 0.67, 'racine': 0.73, 'outagamie': 0.49, 'kenosha': 0.69, 'washington': 0.41,
            'la_crosse': 0.63, 'fond_du_lac': 0.56, 'marathon': 0.44, 'sheboygan': 0.59, 
            'eau_claire': 0.51, 'wood': 0.48, 'jefferson': 0.46, 'st_croix': 0.38, 'walworth': 0.55,
            'portage': 0.47, 'chippewa': 0.52, 'dodge': 0.54, 'ozaukee': 0.35, 'manitowoc': 0.57,
            'sauk': 0.50, 'calumet': 0.42, 'columbia': 0.48, 'barron': 0.53, 'green': 0.44,
            'dunn': 0.51, 'polk': 0.49, 'shawano': 0.60, 'grant': 0.56, 'iowa': 0.43,
            'juneau': 0.54, 'monroe': 0.58, 'pierce': 0.40, 'oneida': 0.47, 'lincoln': 0.45,
            'buffalo': 0.52, 'crawford': 0.59, 'waupaca': 0.53, 'vernon': 0.55, 'adams': 0.50,
            'richland': 0.57, 'jackson': 0.56, 'kewaunee': 0.46, 'green_lake': 0.48, 'marquette': 0.52,
            'waushara': 0.51, 'burnett': 0.54, 'clark': 0.58, 'washburn': 0.50, 'door': 0.43,
            'oconto': 0.49, 'langlade': 0.55, 'vilas': 0.41, 'bayfield': 0.48, 'sawyer': 0.52,
            'rusk': 0.56, 'taylor': 0.54, 'price': 0.50, 'ashland': 0.53, 'iron': 0.47,
            'forest': 0.49, 'florence': 0.44, 'marinette': 0.51, 'menominee': 0.65, 'pepin': 0.48
        }
        
        # Urban heat island intensity factors for Wisconsin cities
        self.urban_heat_island = {
            'milwaukee': 7.2,    # °F temperature increase due to urban heat island
            'madison': 5.8,      # Madison (Dane County)
            'green_bay': 4.9,    # Green Bay (Brown County)  
            'kenosha': 4.1,      # Kenosha
            'racine': 3.8,       # Racine
            'appleton': 3.5,     # Outagamie County
            'waukesha': 3.2,     # Waukesha
            'oshkosh': 2.9,      # Winnebago County
            'eau_claire': 2.6,   # Eau Claire
            'janesville': 2.4,   # Rock County
            'default_urban': 2.0, # Small cities
            'rural': 0.0         # Rural areas
        }
        
        # Seasonal heat risk patterns for Wisconsin strategic planning
        self.seasonal_patterns = {
            'spring': {
                'risk_factor': 0.3,
                'focus': 'early_heat_preparedness',
                'key_risks': ['rapid temperature increases', 'unprepared populations', 'HVAC system testing']
            },
            'summer': {
                'risk_factor': 1.0, 
                'focus': 'peak_heat_response',
                'key_risks': ['sustained high temperatures', 'heat waves', 'energy grid stress']
            },
            'fall': {
                'risk_factor': 0.4,
                'focus': 'late_season_heat_events', 
                'key_risks': ['unexpected hot weather', 'school heat concerns', 'cooling system maintenance']
            },
            'winter': {
                'risk_factor': 0.1,
                'focus': 'planning_and_preparation',
                'key_risks': ['infrastructure planning', 'vulnerable population identification', 'equipment readiness']
            }
        }
    
    def get_strategic_heat_assessment(self, county_name: str, jurisdiction_id: Optional[str] = None) -> Dict[str, Any]:
        """
        Generate strategic extreme heat risk assessment for annual planning
        
        Args:
            county_name: Wisconsin county name
            jurisdiction_id: Optional jurisdiction identifier
            
        Returns:
            Strategic heat assessment with climate projections and adaptation planning
        """
        county_key = county_name.lower().replace(' county', '').replace(' ', '_')
        
        # Check cache first
        cache_key = f"strategic_heat_{county_key}" 
        cached_data = get_from_persistent_cache(cache_key, self.cache_duration)
        if cached_data:
            logger.info(f"Using cached strategic heat assessment for {county_name}")
            return cached_data
        
        # Calculate baseline vulnerability (structural/demographic factors)
        baseline_vulnerability = self.county_baseline_vulnerability.get(county_key, 0.50)
        
        # Calculate climate change projection impact (2025-2050)
        climate_impact = self._calculate_climate_projections(county_key, baseline_vulnerability)
        
        # Calculate urban heat island amplification
        uhi_amplification = self._calculate_urban_heat_island(county_key)
        
        # Calculate seasonal risk component
        current_season = self._get_current_season()
        seasonal_factor = self.seasonal_patterns[current_season]['risk_factor']
        seasonal_risk = (baseline_vulnerability + climate_impact) * seasonal_factor
        
        # Calculate trend component (long-term climate trajectory)
        trend_risk = self._calculate_trend_component(baseline_vulnerability, climate_impact)
        
        # Infrastructure vulnerability assessment
        infrastructure_risk = self._assess_infrastructure_vulnerability(county_key, baseline_vulnerability)
        
        # Generate strategic adaptation recommendations
        recommendations = self._generate_adaptation_recommendations(
            county_name, baseline_vulnerability, climate_impact, infrastructure_risk
        )
        
        assessment = {
            'strategic_assessment': {
                'baseline_vulnerability': round(baseline_vulnerability, 2),
                'climate_projection_impact': round(climate_impact, 2), 
                'urban_heat_island_factor': round(uhi_amplification, 1),
                'seasonal_risk': round(seasonal_risk, 2),
                'infrastructure_vulnerability': round(infrastructure_risk, 2)
            },
            'temporal_components': {
                'baseline': round(baseline_vulnerability * 0.6, 3),  # 60% strategic planning weight
                'seasonal': round(seasonal_risk * 0.25, 3),         # 25% weight
                'trend': round(trend_risk * 0.15, 3),              # 15% weight
                'acute': 0.0  # 0% weight in strategic planning mode
            },
            'composite_risk_score': round((
                baseline_vulnerability * 0.6 +
                seasonal_risk * 0.25 + 
                trend_risk * 0.15
            ), 2),
            'climate_projections_2050': {
                'temperature_increase_f': self.climate_projections['temperature_increase']['annual_avg'],
                'days_above_90f_multiplier': self.climate_projections['frequency_changes']['days_above_90f'],
                'heat_wave_frequency_multiplier': self.climate_projections['frequency_changes']['heat_wave_frequency'],
                'heat_wave_duration_multiplier': self.climate_projections['duration_changes']['heat_wave_length']
            },
            'planning_context': {
                'assessment_type': 'strategic_climate_adaptation',
                'focus': 'long_term_heat_preparedness', 
                'time_horizon': '2025_to_2050',
                'current_season': current_season,
                'seasonal_planning_focus': self.seasonal_patterns[current_season]['focus']
            },
            'risk_factors': {
                'primary_vulnerability': 'high' if baseline_vulnerability > 0.6 else 'moderate',
                'climate_change_impact': 'high' if climate_impact > 0.5 else 'moderate',
                'urban_heat_amplification': uhi_amplification,
                'key_seasonal_risks': self.seasonal_patterns[current_season]['key_risks']
            },
            'strategic_recommendations': recommendations,
            'data_sources': [
                'Wisconsin Initiative on Climate Change Impacts (WICCI) 2021 Assessment',
                'NOAA Wisconsin Climate Projections 2025-2050',
                'CDC Social Vulnerability Index (SVI) 2020',
                'Wisconsin DHS Heat Vulnerability Index',
                'EPA Urban Heat Island research and mapping'
            ],
            'last_updated': datetime.now().isoformat()
        }
        
        # Cache the assessment
        set_in_persistent_cache(cache_key, assessment, self.cache_duration) 
        logger.info(f"Generated strategic heat assessment for {county_name}")
        
        return assessment
    
    def _get_current_season(self) -> str:
        """Determine current season for seasonal planning"""
        month = datetime.now().month
        if month in [3, 4, 5]:
            return 'spring'
        elif month in [6, 7, 8]:
            return 'summer'
        elif month in [9, 10, 11]:
            return 'fall' 
        else:
            return 'winter'
    
    def _calculate_climate_projections(self, county_key: str, baseline: float) -> float:
        """Calculate climate change impact on heat risk (2025-2050 projections)"""
        temp_impact = self.climate_projections['temperature_increase']['annual_avg'] / 10.0
        frequency_impact = (self.climate_projections['frequency_changes']['days_above_90f'] - 1.0) / 4.0  
        duration_impact = (self.climate_projections['duration_changes']['heat_wave_length'] - 1.0) / 2.0
        
        # Weighted climate impact calculation
        climate_factor = (
            temp_impact * 0.4 +      # Temperature increase most significant
            frequency_impact * 0.35 + # Frequency changes very important  
            duration_impact * 0.25    # Duration changes important for recovery
        )
        
        return min(0.8, baseline * (1 + climate_factor))  # Cap climate impact
    
    def _calculate_urban_heat_island(self, county_key: str) -> float:
        """Calculate urban heat island amplification factor"""
        # Map county to major city/urban area
        urban_mapping = {
            'milwaukee': 'milwaukee',
            'dane': 'madison', 
            'brown': 'green_bay',
            'kenosha': 'kenosha',
            'racine': 'racine',
            'outagamie': 'appleton', 
            'waukesha': 'waukesha',
            'winnebago': 'oshkosh',
            'eau_claire': 'eau_claire',
            'rock': 'janesville'
        }
        
        city_key = urban_mapping.get(county_key, 'rural')
        return self.urban_heat_island.get(city_key, self.urban_heat_island.get('default_urban', 0.0))
    
    def _calculate_trend_component(self, baseline: float, climate_impact: float) -> float:
        """Calculate long-term trend component based on climate trajectory"""
        # Increasing trend due to climate change
        trend_multiplier = 1.3  # 30% increase trajectory over planning period
        return min(1.0, (baseline + climate_impact) * trend_multiplier)
    
    def _assess_infrastructure_vulnerability(self, county_key: str, baseline: float) -> float:
        """Assess infrastructure vulnerability to extreme heat"""
        # Base infrastructure risk
        infra_risk = baseline * 0.8
        
        # Urban areas have higher infrastructure vulnerability 
        urban_counties = ['milwaukee', 'dane', 'brown', 'waukesha', 'winnebago', 'kenosha', 'racine']
        if county_key in urban_counties:
            infra_risk += 0.2
        
        # Rural areas may have limited cooling infrastructure
        rural_high_risk = ['menominee', 'forest', 'florence', 'iron', 'vilas']
        if county_key in rural_high_risk:
            infra_risk += 0.1
        
        return min(1.0, infra_risk)
    
    def _generate_adaptation_recommendations(self, county_name: str, baseline: float, 
                                           climate_impact: float, infrastructure_risk: float) -> List[Dict[str, str]]:
        """Generate strategic heat adaptation recommendations"""
        recommendations = []
        
        # High vulnerability recommendations
        if baseline > 0.6:
            recommendations.extend([
                {
                    'priority': 'high',
                    'category': 'public_health',
                    'action': 'Enhance heat emergency response and community outreach protocols',
                    'timeline': 'year_1',
                    'rationale': 'High baseline vulnerability requires strengthened community-wide response systems'
                },
                {
                    'priority': 'high', 
                    'category': 'infrastructure',
                    'action': 'Expand cooling center capacity and accessibility',
                    'timeline': 'year_1_2',
                    'rationale': 'Critical infrastructure gap for high-risk population'
                }
            ])
        
        # Climate adaptation recommendations
        if climate_impact > 0.4:
            recommendations.extend([
                {
                    'priority': 'medium',
                    'category': 'climate_adaptation',
                    'action': 'Update heat emergency thresholds for climate change',
                    'timeline': 'year_2',
                    'rationale': 'Climate projections require updated response trigger points'
                },
                {
                    'priority': 'medium',
                    'category': 'capacity_building',
                    'action': 'Train staff on extended heat wave response protocols', 
                    'timeline': 'year_2_3',
                    'rationale': 'Projected increase in heat wave duration requires enhanced protocols'
                }
            ])
        
        # Infrastructure adaptation recommendations
        if infrastructure_risk > 0.5:
            recommendations.append({
                'priority': 'medium',
                'category': 'infrastructure_resilience',
                'action': 'Assess cooling infrastructure adequacy for climate projections',
                'timeline': 'year_3',
                'rationale': 'Infrastructure planning must account for increased heat exposure'
            })
        
        # Seasonal preparedness
        current_season = self._get_current_season()
        seasonal_focus = self.seasonal_patterns[current_season]['focus']
        recommendations.append({
            'priority': 'ongoing',
            'category': 'seasonal_preparedness',
            'action': f'Implement {seasonal_focus.replace("_", " ")} strategies',
            'timeline': 'ongoing',
            'rationale': f'Current season requires focus on {seasonal_focus.replace("_", " ")}'
        })
        
        return recommendations[:6]  # Limit to top 6 strategic recommendations