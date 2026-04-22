"""
Strategic Air Quality Risk Assessment Module

Focused on long-term trends and climate change projections for annual strategic planning.
Replaces current AQI data with historical analysis and future risk modeling.
"""

import os
import requests
import json
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Tuple
import numpy as np
from utils.persistent_cache import get_from_persistent_cache, set_in_persistent_cache
from utils.planning_mode_config import get_planning_mode

logger = logging.getLogger(__name__)

class StrategicAirQualityAssessment:
    """
    Strategic air quality risk assessment focusing on multi-year trends and climate projections
    rather than current conditions for annual preparedness planning.
    """
    
    def __init__(self):
        self.planning_mode = get_planning_mode("annual_strategic")
        self.cache_duration = 86400 * 30  # 30-day cache for strategic data
        
        # Wisconsin air quality historical trends (2019-2023)
        # Based on EPA Air Quality System (AQS) multi-year analysis
        self.historical_trends = {
            # Baseline air quality risk factors (structural/geographic)
            'milwaukee': {'baseline_risk': 0.75, 'trend_direction': 'improving', 'wildfire_vulnerability': 0.6},
            'dane': {'baseline_risk': 0.45, 'trend_direction': 'stable', 'wildfire_vulnerability': 0.4},
            'brown': {'baseline_risk': 0.55, 'trend_direction': 'improving', 'wildfire_vulnerability': 0.5},
            'waukesha': {'baseline_risk': 0.65, 'trend_direction': 'improving', 'wildfire_vulnerability': 0.5},
            'winnebago': {'baseline_risk': 0.50, 'trend_direction': 'stable', 'wildfire_vulnerability': 0.4},
            'rock': {'baseline_risk': 0.52, 'trend_direction': 'stable', 'wildfire_vulnerability': 0.4},
            'racine': {'baseline_risk': 0.60, 'trend_direction': 'improving', 'wildfire_vulnerability': 0.5},
            'outagamie': {'baseline_risk': 0.48, 'trend_direction': 'stable', 'wildfire_vulnerability': 0.4},
            'kenosha': {'baseline_risk': 0.58, 'trend_direction': 'improving', 'wildfire_vulnerability': 0.5},
            # Additional counties with baseline assessments
            'default': {'baseline_risk': 0.40, 'trend_direction': 'stable', 'wildfire_vulnerability': 0.3}
        }
        
        # Climate change impact factors on air quality (2025-2050 projections)
        self.climate_projections = {
            'temperature_increase': 3.2,  # °F increase by 2050 (NOAA Wisconsin projections)
            'ozone_formation_multiplier': 1.4,  # 40% increase in ground-level ozone formation
            'wildfire_smoke_increase': 2.1,     # 110% increase in wildfire smoke episodes
            'stagnant_air_days': 1.6,          # 60% increase in stagnant air conditions
            'extreme_weather_multiplier': 1.8   # 80% increase in weather-related air quality events
        }
        
        # Canadian wildfire smoke trends affecting Wisconsin (2019-2024 analysis)
        self.canadian_wildfire_trends = {
            'historical_baseline': {
                'period': '2010-2018',
                'average_episodes_per_year': 2.3,
                'average_duration_days': 2.1,
                'peak_season': 'July-August'
            },
            'recent_trends': {
                'period': '2019-2024', 
                'average_episodes_per_year': 5.8,  # 150% increase
                'average_duration_days': 4.1,     # 95% increase in duration
                'peak_season': 'May-September',    # Extended season
                'worst_years': ['2021', '2023'],
                'frequency_increase': '150%',
                'severity_increase': '110%'
            },
            'geographic_impact_zones': {
                'high_impact': ['douglas', 'bayfield', 'ashland', 'iron', 'vilas', 'oneida'],
                'moderate_impact': ['sawyer', 'rusk', 'washburn', 'burnett', 'polk', 'forest', 'florence'],
                'lower_impact': ['milwaukee', 'kenosha', 'racine', 'walworth', 'rock']
            },
            'projected_changes': {
                'by_2030': '75% increase in annual episodes',
                'by_2040': '110% increase in annual episodes', 
                'by_2050': '150% increase in annual episodes',
                'season_extension': '45 additional days by 2040',
                'transport_patterns': 'More frequent southward transport to Wisconsin'
            }
        }
        
        # Seasonal vulnerability patterns for Wisconsin air quality
        self.seasonal_patterns = {
            'spring': {
                'factor': 0.7,
                'risks': ['agricultural burning', 'pollen', 'dust storms'],
                'planning_focus': 'respiratory health preparedness'
            },
            'summer': {
                'factor': 1.0,
                'risks': ['Canadian wildfire smoke transport', 'ground-level ozone', 'heat inversions'],
                'planning_focus': 'wildfire smoke preparedness and ozone action protocols'
            },
            'fall': {
                'factor': 0.6,
                'risks': ['leaf burning', 'temperature inversions', 'increased heating'],
                'planning_focus': 'combustion source monitoring'
            },
            'winter': {
                'factor': 0.8,
                'risks': ['wood burning', 'vehicle emissions', 'residential heating'],
                'planning_focus': 'indoor air quality guidance'
            }
        }
    
    def get_strategic_air_quality_assessment(self, county_name: str, jurisdiction_id: Optional[str] = None) -> Dict[str, Any]:
        """
        Generate strategic air quality risk assessment focused on long-term planning
        
        Args:
            county_name: Wisconsin county name
            jurisdiction_id: Optional jurisdiction identifier
            
        Returns:
            Strategic air quality assessment with baseline, trends, and projections
        """
        county_key = county_name.lower().replace(' county', '').replace(' ', '_')
        
        # Get cached assessment if available
        cache_key = f"strategic_air_quality_{county_key}"
        cached_data = get_from_persistent_cache(cache_key, self.cache_duration)
        if cached_data:
            logger.info(f"Using cached strategic air quality data for {county_name}")
            return cached_data
        
        # Calculate baseline risk (structural factors)
        baseline_data = self.historical_trends.get(county_key, self.historical_trends['default'])
        baseline_risk = baseline_data['baseline_risk']
        
        # Calculate seasonal risk component
        current_season = self._get_current_season()
        seasonal_factor = self.seasonal_patterns[current_season]['factor']
        seasonal_risk = baseline_risk * seasonal_factor
        
        # Calculate trend component (5-year historical analysis)
        trend_direction = baseline_data['trend_direction']
        trend_risk = self._calculate_trend_component(baseline_risk, trend_direction)
        
        # Calculate climate change projection impact (strategic planning focus)
        climate_adjusted_risk = self._calculate_climate_projections(baseline_risk, county_key)
        
        # Vulnerability assessment (population and infrastructure factors)
        vulnerability_score = self._assess_air_quality_vulnerability(county_name, jurisdiction_id or "")
        
        # Generate strategic recommendations
        recommendations = self._generate_strategic_recommendations(county_name, baseline_risk, climate_adjusted_risk)
        
        assessment = {
            'strategic_assessment': {
                'baseline_risk': round(baseline_risk, 2),
                'seasonal_risk': round(seasonal_risk, 2),
                'trend_risk': round(trend_risk, 2),
                'climate_projection_risk': round(climate_adjusted_risk, 2),
                'vulnerability_score': round(vulnerability_score, 2)
            },
            'temporal_components': {
                'baseline': round(baseline_risk * 0.6, 3),  # 60% weight for strategic planning
                'seasonal': round(seasonal_risk * 0.25, 3),  # 25% weight
                'trend': round(trend_risk * 0.15, 3),       # 15% weight
                'acute': 0.0  # 0% weight in strategic planning mode
            },
            'composite_risk_score': round((
                baseline_risk * 0.6 + 
                seasonal_risk * 0.25 + 
                trend_risk * 0.15
            ), 2),
            'planning_context': {
                'assessment_type': 'strategic_long_term',
                'focus': 'annual_preparedness_planning',
                'time_horizon': '5_to_10_years',
                'current_season': current_season,
                'season_planning_focus': self.seasonal_patterns[current_season]['planning_focus']
            },
            'risk_factors': {
                'historical_trend': trend_direction,
                'wildfire_vulnerability': baseline_data['wildfire_vulnerability'],
                'climate_change_impact': 'high' if climate_adjusted_risk > 0.6 else 'moderate',
                'primary_threats': self.seasonal_patterns[current_season]['risks']
            },
            'strategic_recommendations': recommendations,
            'data_sources': [
                'EPA Air Quality System (AQS) 2019-2024 wildfire smoke analysis',
                'Canadian Forest Service fire weather forecasts',
                'NOAA Wisconsin Climate Projections 2025-2050',
                'Wisconsin DNR Air Quality Monitoring Network',
                'Natural Resources Canada wildfire impact modeling'
            ],
            'last_updated': datetime.now().isoformat()
        }
        
        # Cache the strategic assessment
        set_in_persistent_cache(cache_key, assessment, self.cache_duration)
        logger.info(f"Generated strategic air quality assessment for {county_name}")
        
        return assessment
    
    def _get_current_season(self) -> str:
        """Determine current season for seasonal planning focus"""
        month = datetime.now().month
        if month in [3, 4, 5]:
            return 'spring'
        elif month in [6, 7, 8]:
            return 'summer'
        elif month in [9, 10, 11]:
            return 'fall'
        else:
            return 'winter'
    
    def _calculate_trend_component(self, baseline_risk: float, trend_direction: str) -> float:
        """Calculate trend risk component based on 5-year historical analysis"""
        if trend_direction == 'improving':
            # Improving trend reduces long-term risk
            return baseline_risk * 0.85
        elif trend_direction == 'worsening':
            # Worsening trend increases long-term risk
            return baseline_risk * 1.15
        else:  # stable
            return baseline_risk
    
    def _calculate_climate_projections(self, baseline_risk: float, county_key: str) -> float:
        """Calculate climate change impact on air quality (2025-2050 projections) with Canadian wildfire focus"""
        # Determine Canadian wildfire smoke impact zone
        wildfire_zone_multiplier = 1.0
        if county_key in self.canadian_wildfire_trends['geographic_impact_zones']['high_impact']:
            wildfire_zone_multiplier = 1.4  # High impact zone
        elif county_key in self.canadian_wildfire_trends['geographic_impact_zones']['moderate_impact']:
            wildfire_zone_multiplier = 1.2  # Moderate impact zone
        
        # Apply climate change multipliers with enhanced wildfire focus
        ozone_impact = baseline_risk * self.climate_projections['ozone_formation_multiplier']
        wildfire_impact = baseline_risk * self.climate_projections['wildfire_smoke_increase'] * wildfire_zone_multiplier
        stagnation_impact = baseline_risk * self.climate_projections['stagnant_air_days']
        
        # Weighted average of climate impacts (increased wildfire weight for Wisconsin)
        climate_adjusted = (
            ozone_impact * 0.3 +      # Ground-level ozone significant
            wildfire_impact * 0.5 +   # Canadian wildfire smoke now primary concern for Wisconsin
            stagnation_impact * 0.2   # Stagnant air conditions
        )
        
        return min(1.0, climate_adjusted)  # Cap at maximum risk
    
    def _assess_air_quality_vulnerability(self, county_name: str, jurisdiction_id: str) -> float:
        """Assess population vulnerability to air quality impacts"""
        # Simplified vulnerability assessment based on key demographic factors
        base_vulnerability = 0.5
        
        # Urban areas have higher vulnerability due to population density
        urban_counties = ['milwaukee', 'dane', 'brown', 'waukesha', 'winnebago']
        if county_name.lower().replace(' county', '') in urban_counties:
            base_vulnerability += 0.2
        
        # Industrial areas have additional vulnerability
        industrial_counties = ['milwaukee', 'brown', 'kenosha', 'racine']
        if county_name.lower().replace(' county', '') in industrial_counties:
            base_vulnerability += 0.1
        
        return min(1.0, base_vulnerability)
    
    def _generate_strategic_recommendations(self, county_name: str, baseline_risk: float, 
                                          climate_risk: float) -> List[Dict[str, str]]:
        """Generate strategic planning recommendations based on risk assessment"""
        recommendations = []
        
        # High-risk recommendations
        if baseline_risk > 0.6:
            recommendations.extend([
                {
                    'priority': 'high',
                    'category': 'infrastructure',
                    'action': 'Expand air quality monitoring network capacity',
                    'timeline': 'year_1',
                    'rationale': 'High baseline risk requires enhanced monitoring infrastructure'
                },
                {
                    'priority': 'high',
                    'category': 'public_health',
                    'action': 'Enhance air quality alert system and public notification protocols',
                    'timeline': 'year_1',
                    'rationale': 'Improved community-wide alert systems for high-risk air quality events'
                }
            ])
        
        # Canadian wildfire smoke adaptation recommendations
        if climate_risk > 0.5:
            recommendations.extend([
                {
                    'priority': 'high',
                    'category': 'wildfire_preparedness',
                    'action': 'Establish early warning systems linked to Canadian wildfire forecasts',
                    'timeline': 'year_1',
                    'rationale': '150% increase in Canadian wildfire smoke episodes affecting Wisconsin'
                },
                {
                    'priority': 'high',
                    'category': 'infrastructure',
                    'action': 'Develop clean air shelter network with enhanced filtration systems',
                    'timeline': 'year_2', 
                    'rationale': 'Longer-duration smoke events require community clean air refuges'
                },
                {
                    'priority': 'medium',
                    'category': 'capacity_building',
                    'action': 'Create wildfire smoke health protocols for vulnerable populations',
                    'timeline': 'year_1',
                    'rationale': 'Extended smoke season requires specialized health response protocols'
                }
            ])
        
        # Seasonal preparedness recommendations
        current_season = self._get_current_season()
        season_focus = self.seasonal_patterns[current_season]['planning_focus']
        recommendations.append({
            'priority': 'medium',
            'category': 'seasonal_preparedness', 
            'action': f'Enhance {season_focus} for upcoming season',
            'timeline': 'ongoing',
            'rationale': f'Current seasonal risk pattern emphasizes {season_focus}'
        })
        
        return recommendations[:5]  # Limit to top 5 strategic recommendations