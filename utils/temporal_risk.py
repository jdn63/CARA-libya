"""
Temporal Risk Component Framework for Risk Assessment

This module implements the Baseline-Seasonal-Trend-Acute (BSTA) framework for risk assessment
which decomposes risk scores into multiple temporal components:

1. Baseline: Long-term structural risk that changes very slowly (1-10 years)
2. Seasonal: Predictable cyclical variations (annual weather patterns, etc.)
3. Trend: Medium-term directional changes (population shifts, climate change effects)
4. Acute: Short-term, event-driven spikes (active emergencies, outbreaks)

This framework provides a more nuanced understanding of risks over time and helps
prioritize appropriate interventions:
- Baseline risks → Long-term infrastructure and capacity building
- Seasonal risks → Cyclical preparedness activities
- Trend risks → Strategic planning and adaptation
- Acute risks → Immediate response and resource allocation
"""

import os
import json
import logging
import datetime
from typing import Dict, List, Optional, Tuple
from datetime import date, datetime, timedelta
import calendar
from utils.config_manager import get_config_manager

# Get module logger (centralized config in core.py)
logger = logging.getLogger(__name__)

# Cache for historical data to avoid repeated calculations
_historical_data_cache = {}

def get_current_season() -> str:
    """
    Determine the current season based on the current date.
    
    Returns:
        str: Current season name (Spring, Summer, Fall, Winter)
    """
    now = datetime.now()
    month = now.month
    day = now.day
    
    # Define season boundaries (approximate dates)
    if (month == 3 and day >= 20) or month in [4, 5] or (month == 6 and day < 21):
        return "Spring"
    elif (month == 6 and day >= 21) or month in [7, 8] or (month == 9 and day < 22):
        return "Summer"
    elif (month == 9 and day >= 22) or month in [10, 11] or (month == 12 and day < 21):
        return "Fall"
    else:  # Winter
        return "Winter"

class TemporalRiskComponent:
    """
    Represents a risk score decomposed into temporal components:
    - Baseline: Long-term structural risk that changes very slowly
    - Seasonal: Predictable cyclical variations (annual weather patterns, etc.)
    - Trend: Medium-term directional changes (population shifts, climate change)
    - Acute: Short-term, event-driven spikes (active emergencies, outbreaks)
    """
    def __init__(self, risk_type: str, jurisdiction_id: str, county_name: str):
        self.risk_type = risk_type
        self.jurisdiction_id = jurisdiction_id
        self.county_name = county_name
        self.baseline = 0.0
        self.seasonal = 0.0
        self.trend = 0.0
        self.acute = 0.0
        self.last_calculated = None
        
        config_manager = get_config_manager()
        self.weights = config_manager.get_temporal_weights('strategic_planning', risk_type=risk_type)
        logger.info(f"Loaded temporal weights for {risk_type}: {self.weights}")
        
        # Get historical data for calculations
        self._load_historical_data()
    
    def _load_historical_data(self):
        """Load historical data for this risk type and jurisdiction"""
        global _historical_data_cache
        
        # Use cached data if available
        cache_key = f"{self.risk_type}_{self.jurisdiction_id}"
        if cache_key in _historical_data_cache:
            self.historical_data = _historical_data_cache[cache_key]
            return
            
        # Get historical data from appropriate source based on risk type
        from utils.data_processor import get_historical_risk_data
        
        # Load approximately 3-5 years of historical data if available
        self.historical_data = get_historical_risk_data(
            self.jurisdiction_id, 
            start_year=2020,  # Adjust based on available data
            end_year=datetime.now().year
        )
        
        # Filter for this specific risk type - check for risk_type with _risk suffix
        if self.historical_data:
            risk_key = f"{self.risk_type}_risk"  # e.g., 'flood' -> 'flood_risk'
            
            self.historical_data = [
                item for item in self.historical_data 
                if risk_key in item or  # Check for flood_risk, tornado_risk, etc.
                   self.risk_type in item or  # Check for exact match
                   self.risk_type in item.get('natural_hazards', {})  # Check nested structure
            ]
            
            logger.info(f"Filtered historical data for {self.risk_type}: {len(self.historical_data)} points available")
        
        # Cache the data
        _historical_data_cache[cache_key] = self.historical_data
    
    def calculate_components(self) -> Dict:
        """Calculate each temporal component based on historical and current data"""
        # Record calculation time
        self.last_calculated = datetime.now()
        
        # Baseline calculation (stable, structural factors)
        self.baseline = self._calculate_baseline()
        
        # Seasonal calculation (time-of-year adjustments)
        current_month = datetime.now().month
        self.seasonal = self._calculate_seasonal_factor(current_month)
        
        # Trend calculation (historical trajectory)
        self.trend = self._calculate_trend()
        
        # Acute calculation (current events/emergencies)
        self.acute = self._check_for_active_events()
        
        # Log the results
        logger.info(f"Calculated temporal components for {self.county_name}, {self.risk_type}: " +
                   f"B={self.baseline:.2f}, S={self.seasonal:.2f}, T={self.trend:.2f}, A={self.acute:.2f}")
        
        trend_metadata = getattr(self, '_trend_metadata', None)
        
        result = {
            'baseline': float(self.baseline),
            'seasonal': float(self.seasonal),
            'trend': float(self.trend),
            'acute': float(self.acute)
        }
        
        if trend_metadata:
            result['trend_metadata'] = trend_metadata
        
        return result
    
    def get_composite_score(self) -> float:
        """
        Combine components into single score with appropriate weighting.
        
        If components haven't been calculated yet, calculate them first.
        """
        if self.last_calculated is None:
            self.calculate_components()
            
        # Calculate weighted sum
        composite = (
            (self.baseline * self.weights['baseline']) +
            (self.seasonal * self.weights['seasonal']) +
            (self.trend * self.weights['trend']) +
            (self.acute * self.weights['acute'])
        )
        
        # Ensure result is between 0 and 1
        return max(0.0, min(1.0, composite))
    
    def _calculate_baseline(self) -> float:
        """
        Calculate baseline risk component.
        
        This represents the long-term, structural risk factors that change very slowly.
        """
        # If we have sufficient historical data, use the 3-year average
        if len(self.historical_data) >= 12:  # Assuming quarterly or monthly data
            # Extract risk values, filtering out acute spikes
            risk_values = []
            for item in self.historical_data:
                value = self._extract_risk_value(item)
                if value is not None:
                    risk_values.append(float(value))
            sorted_values = sorted(risk_values) if risk_values else []
            
            # Use the median 60% of values to avoid outliers
            start_idx = int(len(sorted_values) * 0.2)
            end_idx = int(len(sorted_values) * 0.8)
            baseline_values = sorted_values[start_idx:end_idx]
            
            # Calculate average of the "typical" values
            if baseline_values:
                baseline = sum(baseline_values) / len(baseline_values)
                return baseline
        
        # If insufficient historical data, use current calculated risk as baseline
        # In a real implementation, we'd use a more sophisticated fallback
        return 0.5  # Moderate baseline risk when historical data unavailable
    
    def _calculate_seasonal_factor(self, month: int) -> float:
        """
        Calculate seasonal risk component based on month of year.
        
        Different risk types have different seasonal patterns:
        - Flood: Spring months (3-6)
        - Tornado: Late spring/summer (4-8)
        - Winter Storm: Winter months (11-3)
        - Thunderstorm: Summer months (5-9)
        - Extreme Heat: Summer months (6-9)
        - Infectious Disease: Winter months for respiratory (11-3), varies for others
        """
        # Define seasonal patterns for different risk types
        seasonal_patterns = {
            'flood': {3: 0.7, 4: 0.9, 5: 1.0, 6: 0.8, 7: 0.5, 8: 0.4, 9: 0.3, 10: 0.2, 11: 0.1, 12: 0.1, 1: 0.1, 2: 0.3},
            'tornado': {3: 0.3, 4: 0.7, 5: 0.9, 6: 1.0, 7: 0.8, 8: 0.6, 9: 0.3, 10: 0.1, 11: 0.1, 12: 0.1, 1: 0.1, 2: 0.1},
            'winter_storm': {3: 0.5, 4: 0.1, 5: 0.0, 6: 0.0, 7: 0.0, 8: 0.0, 9: 0.0, 10: 0.2, 11: 0.7, 12: 1.0, 1: 1.0, 2: 0.8},
            'thunderstorm': {3: 0.2, 4: 0.5, 5: 0.8, 6: 1.0, 7: 1.0, 8: 0.9, 9: 0.6, 10: 0.3, 11: 0.1, 12: 0.1, 1: 0.1, 2: 0.1},
            'extreme_heat': {3: 0.0, 4: 0.1, 5: 0.3, 6: 0.7, 7: 1.0, 8: 0.9, 9: 0.4, 10: 0.1, 11: 0.0, 12: 0.0, 1: 0.0, 2: 0.0},
            'infectious_disease': {3: 0.5, 4: 0.3, 5: 0.2, 6: 0.1, 7: 0.1, 8: 0.2, 9: 0.4, 10: 0.6, 11: 0.8, 12: 1.0, 1: 0.9, 2: 0.7},
            'active_shooter': {1: 0.5, 2: 0.5, 3: 0.5, 4: 0.5, 5: 0.5, 6: 0.5, 7: 0.5, 8: 0.5, 9: 0.5, 10: 0.5, 11: 0.5, 12: 0.5},
            'cybersecurity': {1: 0.5, 2: 0.5, 3: 0.5, 4: 0.5, 5: 0.5, 6: 0.5, 7: 0.5, 8: 0.5, 9: 0.5, 10: 0.5, 11: 0.5, 12: 0.5},
            'electrical_outage': {1: 0.8, 2: 0.7, 3: 0.6, 4: 0.4, 5: 0.3, 6: 0.5, 7: 0.7, 8: 0.6, 9: 0.3, 10: 0.4, 11: 0.6, 12: 0.7},
            'utilities_disruption': {1: 0.7, 2: 0.7, 3: 0.5, 4: 0.4, 5: 0.3, 6: 0.4, 7: 0.6, 8: 0.6, 9: 0.3, 10: 0.4, 11: 0.6, 12: 0.7},
            'supply_chain': {1: 0.6, 2: 0.5, 3: 0.5, 4: 0.4, 5: 0.4, 6: 0.4, 7: 0.4, 8: 0.4, 9: 0.5, 10: 0.5, 11: 0.6, 12: 0.7},
            'fuel_shortage': {1: 0.7, 2: 0.6, 3: 0.5, 4: 0.4, 5: 0.4, 6: 0.5, 7: 0.6, 8: 0.5, 9: 0.4, 10: 0.5, 11: 0.6, 12: 0.7}
        }
        
        # Default to mid-range risk if pattern not defined
        pattern = seasonal_patterns.get(self.risk_type, {month: 0.5 for month in range(1, 13)})
        
        # Get seasonal factor for current month (0-1 scale)
        seasonal_factor = pattern.get(month, 0.5)
        
        # Further adjust based on historical seasonal patterns specific to this jurisdiction
        # This would use historical monthly averages if available
        jurisdiction_adjustment = self._get_historical_seasonal_adjustment(month)
        
        # Combine standard seasonal pattern with jurisdiction-specific adjustment
        # 70% standard pattern, 30% jurisdiction-specific adjustment
        return (seasonal_factor * 0.7) + (jurisdiction_adjustment * 0.3)
    
    def _get_historical_seasonal_adjustment(self, month: int) -> float:
        """
        Calculate jurisdiction-specific seasonal adjustment based on historical data.
        
        Args:
            month: Current month (1-12)
            
        Returns:
            Seasonal adjustment factor (0-1) based on historical patterns
        """
        # If we don't have enough historical data, return neutral adjustment
        if len(self.historical_data) < 12:
            return 0.5
            
        # Find historical data points for this month
        month_data = []
        for item in self.historical_data:
            if 'date' in item:
                try:
                    # Parse date to check if it matches current month
                    data_date = datetime.strptime(item['date'], '%Y-%m-%d')
                    if data_date.month == month:
                        risk_value = self._extract_risk_value(item)
                        if risk_value is not None:
                            month_data.append(risk_value)
                except (ValueError, TypeError):
                    pass
        
        # If we have month-specific data, use average
        if month_data:
            return sum(month_data) / len(month_data)
            
        # Otherwise use neutral value
        return 0.5
    
    def _calculate_trend(self) -> float:
        """
        Calculate trend component using real data from cached sources.
        
        Uses the real_trend_calculator module which compares actual historical
        event counts from NOAA Storm Events, OpenFEMA, climate projections,
        and Census data rather than synthetic data.
        
        Returns 0-1 scale: 0.5 = no trend, >0.5 = increasing risk, <0.5 = decreasing
        """
        try:
            from utils.real_trend_calculator import get_trend_score
            
            trend_data = get_trend_score(self.risk_type, self.county_name)
            
            if trend_data is None:
                logger.info(f"Trend disabled for {self.risk_type} (using acute instead)")
                self._trend_metadata = {
                    'score': 0.0,
                    'data_source': 'Trend disabled',
                    'description': 'Acute surveillance used instead of trend for this domain'
                }
                return 0.0
            
            self._trend_metadata = trend_data
            score = trend_data.get('score', 0.5)
            
            logger.info(f"Real trend for {self.risk_type} in {self.county_name}: "
                       f"{score:.3f} ({trend_data.get('data_source', 'unknown')})")
            
            return score
            
        except Exception as e:
            logger.error(f"Error in real trend calculation for {self.risk_type}: {e}")
            self._trend_metadata = {
                'score': 0.5,
                'data_source': 'Fallback',
                'description': f'Error calculating trend: {str(e)}'
            }
            return 0.5
    
    def _check_for_active_events(self) -> float:
        """
        Check for active events or emergencies that affect this risk type.
        
        This component detects current acute situations that temporarily
        elevate risk levels, such as:
        - Active weather events
        - Disease outbreaks
        - Infrastructure failures
        - Active threats
        """
        acute_score = 0.0
        
        # CARA Strategic Planning Mode: Focus on long-term trends rather than real-time weather events
        # Removed real-time weather alerts and current conditions for strategic planning focus
        # In strategic planning mode, acute components focus on outbreak patterns and infrastructure issues
            
        # Check for active disease outbreaks for infectious disease risk
        if self.risk_type == 'infectious_disease':
            acute_score = max(acute_score, self._check_disease_outbreaks())
            
        # Check for utility/infrastructure disruptions
        if self.risk_type in ['electrical_outage', 'utilities_disruption', 'supply_chain', 'fuel_shortage']:
            acute_score = max(acute_score, self._check_infrastructure_disruptions())
            
        # Check for active threatening situations
        if self.risk_type in ['active_shooter', 'cybersecurity']:
            acute_score = max(acute_score, self._check_active_threats())
            
        return acute_score
    
    def _check_weather_alerts(self) -> float:
        """Check for active weather alerts affecting this jurisdiction"""
        try:
            # Import in a try block to avoid import errors
            try:
                from utils.weather_alerts import get_active_alerts
            except ImportError as import_err:
                logger.error(f"Error importing weather alerts module: {str(import_err)}")
                return 0.0
            
            # Set up a short timeout for the entire function using signals
            # This avoids hanging the entire application if the weather API is slow
            import signal
            
            # Define timeout handler
            def timeout_handler(signum, frame):
                raise TimeoutError("Weather alerts check timed out")
            
            # Set timeout to 3 seconds for the entire function
            try:
                # Set the timeout
                signal.signal(signal.SIGALRM, timeout_handler)
                signal.alarm(3) 
                
                try:
                    # Get active alerts for this jurisdiction with additional error handling
                    alerts = get_active_alerts(self.jurisdiction_id)
                    logger.info(f"Retrieved {len(alerts)} weather alerts for {self.risk_type} risk in {self.county_name}")
                except Exception as weather_err:
                    logger.error(f"Error retrieving weather alerts for temporal risk calculation: {str(weather_err)}")
                    # Return neutral value if we can't get alerts
                    return 0.0
                finally:
                    # Cancel the timeout
                    signal.alarm(0)
            except TimeoutError as timeout_err:
                logger.error(f"Timeout while checking weather alerts: {str(timeout_err)}")
                return 0.0
            
            # If no alert data is available, return neutral value
            if not alerts:
                return 0.0
                
            # Map alert types to risk types
            alert_to_risk_mapping = {
                'Flood': 'flood',
                'Flash Flood': 'flood',
                'Tornado': 'tornado',
                'Tornado Watch': 'tornado',
                'Tornado Warning': 'tornado',
                'Winter Storm': 'winter_storm',
                'Winter Weather': 'winter_storm',
                'Ice Storm': 'winter_storm',
                'Blizzard': 'winter_storm',
                'Thunderstorm': 'thunderstorm',
                'Severe Thunderstorm': 'thunderstorm',
                'Heat Advisory': 'extreme_heat',
                'Excessive Heat': 'extreme_heat',
                'Extreme Heat Warning': 'extreme_heat',
                'Heat Warning': 'extreme_heat'
            }
            
            # Alert severity mapping (0-1 scale)
            severity_mapping = {
                'Advisory': 0.4,
                'Watch': 0.6,
                'Warning': 0.9,
                'Emergency': 1.0
            }
            
            # Check for relevant alerts
            max_severity = 0.0
            for alert in alerts:
                alert_type = alert.get('event', '')
                
                # Check if this alert is relevant to our risk type
                mapped_risk = alert_to_risk_mapping.get(alert_type)
                if mapped_risk != self.risk_type:
                    continue
                    
                # Get alert severity
                severity = alert.get('severity', '')
                severity_value = severity_mapping.get(severity, 0.3)  # Default moderate severity
                
                # Update max severity if this alert is more severe
                max_severity = max(max_severity, severity_value)
                
            return max_severity
            
        except Exception as e:
            logger.warning(f"Error checking weather alerts: {str(e)}")
            return 0.0
    
    def _check_extreme_heat_conditions(self) -> float:
        """
        Check for extreme heat conditions using Wisconsin DHS Heat Vulnerability Index.
        
        This method provides comprehensive heat risk assessment using the Wisconsin DHS
        Heat Vulnerability Index, which combines temperature data with demographic,
        health, and social vulnerability factors specific to Wisconsin jurisdictions.
        
        Returns:
            float: Acute heat risk score (0-1) based on DHS Heat Vulnerability Index
        """
        try:
            # Import Wisconsin DHS Heat Vulnerability functionality
            from utils.heat_vulnerability import calculate_heat_acute_risk
            from utils.weather_alerts import get_current_weather_data
            
            # Get current weather data for temperature context
            current_weather = get_current_weather_data(self.jurisdiction_id)
            current_temp = None
            
            if current_weather:
                current_temp = current_weather.get('temperature')
                # Convert to Fahrenheit if needed
                if isinstance(current_temp, (int, float)) and current_temp < 50:
                    current_temp = (current_temp * 9/5) + 32
            
            # Calculate acute heat risk using Wisconsin DHS Heat Vulnerability Index
            acute_risk = calculate_heat_acute_risk(
                self.jurisdiction_id, 
                self.county_name, 
                current_temp
            )
            
            logger.info(f"DHS Heat Vulnerability acute risk for {self.county_name}: {acute_risk:.2f}")
            return acute_risk
                
        except Exception as e:
            logger.warning(f"Error checking DHS heat vulnerability for {self.county_name}: {str(e)}")
            # Fallback to basic temperature assessment if DHS API unavailable
            return self._check_basic_heat_conditions()
    
    def _check_basic_heat_conditions(self) -> float:
        """
        Fallback heat assessment using basic temperature thresholds.
        
        Used only when Wisconsin DHS Heat Vulnerability Index is unavailable.
        """
        try:
            from utils.weather_alerts import get_current_weather_data
            
            current_weather = get_current_weather_data(self.jurisdiction_id)
            if not current_weather:
                return 0.0
                
            current_temp = current_weather.get('temperature')
            if current_temp is None:
                return 0.0
                
            # Convert to Fahrenheit if needed
            if isinstance(current_temp, (int, float)):
                temp_f = current_temp
                if temp_f < 50:  # Likely Celsius
                    temp_f = (temp_f * 9/5) + 32
            else:
                return 0.0
                
            # Wisconsin-specific heat thresholds (more conservative than national)
            if temp_f >= 95:    # Extreme heat for Wisconsin
                return 0.8
            elif temp_f >= 85:  # High heat for Wisconsin
                return 0.5
            elif temp_f >= 80:  # Moderate heat
                return 0.3
            else:
                return 0.0
                
        except Exception as e:
            logger.warning(f"Error in fallback heat assessment: {str(e)}")
            return 0.0
    
    def _check_disease_outbreaks(self) -> float:
        """
        Check for active disease outbreaks using WI DHS surveillance data.
        
        Evaluates current respiratory illness activity levels (flu, COVID-19, RSV)
        and vaccination coverage gaps to produce an acute risk score.
        """
        try:
            from utils.disease_surveillance import calculate_infectious_disease_risk
            
            disease_data = calculate_infectious_disease_risk(self.jurisdiction_id)
            
            if not disease_data or 'risk_score' not in disease_data:
                logger.debug(f"No disease surveillance data for {self.jurisdiction_id}, using baseline")
                return 0.1
            
            risk_score = float(disease_data.get('risk_score', 0.3))
            
            activity_levels = disease_data.get('activity_levels', {})
            elevated_count = 0
            for disease, level in activity_levels.items():
                if isinstance(level, str) and level.lower() in ('high', 'very high', 'very_high'):
                    elevated_count += 1
                elif isinstance(level, str) and level.lower() == 'moderate':
                    elevated_count += 0.5
            
            if elevated_count >= 2:
                acute_boost = 0.2
            elif elevated_count >= 1:
                acute_boost = 0.1
            else:
                acute_boost = 0.0
            
            acute_score = min(0.95, risk_score * 0.7 + acute_boost)
            
            vaccination_gap = disease_data.get('vaccination_gap_score', 0.0)
            if vaccination_gap > 0.3:
                acute_score = min(0.95, acute_score + 0.05)
            
            logger.info(f"Disease acute score for {self.county_name}: {acute_score:.2f} "
                       f"(base risk: {risk_score:.2f}, elevated diseases: {elevated_count})")
            
            return acute_score
            
        except Exception as e:
            logger.warning(f"Error checking disease outbreaks for {self.county_name}: {str(e)}")
            return 0.1
    
    def _check_infrastructure_disruptions(self) -> float:
        """Check for active infrastructure disruptions affecting this jurisdiction"""
        # In a real implementation, this would connect to infrastructure
        # monitoring systems or outage reporting APIs
        
        # Simplified implementation for demo purposes
        return 0.0
    
    def _check_active_threats(self) -> float:
        """Check for active threats affecting this jurisdiction"""
        # In a real implementation, this would connect to threat
        # intelligence or law enforcement alert systems
        
        # Simplified implementation for demo purposes
        return 0.0
    
    def _extract_risk_value(self, data_item: Dict) -> Optional[float]:
        """Extract risk value from historical data item based on risk type"""
        # Natural hazards are nested under 'natural_hazards'
        if 'natural_hazards' in data_item and self.risk_type in data_item['natural_hazards']:
            return data_item['natural_hazards'][self.risk_type]
            
        # Other risk types might be at the root level with '_risk' suffix
        risk_key = f"{self.risk_type}_risk"
        if risk_key in data_item:
            return data_item[risk_key]
            
        # Direct key might exist
        if self.risk_type in data_item:
            return data_item[self.risk_type]
            
        # Couldn't find relevant risk data
        return None


def analyze_temporal_risk(risk_type: str, jurisdiction_id: str, county_name: str) -> Dict:
    """
    Analyze temporal risk components for a given risk type and jurisdiction.
    
    Args:
        risk_type: Type of risk to analyze (flood, tornado, etc.)
        jurisdiction_id: ID of the jurisdiction
        county_name: Name of the county
        
    Returns:
        Dictionary containing:
        - temporal_components: Breakdown of baseline, seasonal, trend, acute
        - composite_score: Overall risk score combining all components
        - last_updated: Timestamp of calculation
    """
    try:
        # Create temporal component analyzer
        risk_analyzer = TemporalRiskComponent(risk_type, jurisdiction_id, county_name)
        
        # Calculate components
        components = risk_analyzer.calculate_components()
        
        # Get composite score
        composite = risk_analyzer.get_composite_score()
        
        return {
            'temporal_components': components,
            'composite_score': float(composite),
            'last_updated': datetime.now().isoformat()
        }
    except Exception as e:
        logger.error(f"Error analyzing temporal risk for {risk_type} in {county_name}: {str(e)}")
        # Return a fallback structure to prevent application crashes
        return {
            'temporal_components': {
                'baseline': 0.5,
                'seasonal': 0.5,
                'trend': 0.5,
                'acute': 0.0
            },
            'composite_score': 0.5,
            'last_updated': datetime.now().isoformat()
        }


def get_hazard_calendar(risk_type: str, year: Optional[int] = None) -> Dict[str, float]:
    """
    Generate a calendar of risk levels for a specific hazard type throughout the year.
    
    Args:
        risk_type: Type of risk to generate calendar for
        year: Year to generate calendar for (default: current year)
        
    Returns:
        Dictionary mapping dates to risk levels (0-1)
    """
    if year is None:
        year = datetime.now().year
        
    # Define seasonal patterns for different risk types (month -> factor)
    seasonal_patterns = {
        'flood': {3: 0.7, 4: 0.9, 5: 1.0, 6: 0.8, 7: 0.5, 8: 0.4, 9: 0.3, 10: 0.2, 11: 0.1, 12: 0.1, 1: 0.1, 2: 0.3},
        'tornado': {3: 0.3, 4: 0.7, 5: 0.9, 6: 1.0, 7: 0.8, 8: 0.6, 9: 0.3, 10: 0.1, 11: 0.1, 12: 0.1, 1: 0.1, 2: 0.1},
        'winter_storm': {3: 0.5, 4: 0.1, 5: 0.0, 6: 0.0, 7: 0.0, 8: 0.0, 9: 0.0, 10: 0.2, 11: 0.7, 12: 1.0, 1: 1.0, 2: 0.8},
        'thunderstorm': {3: 0.2, 4: 0.5, 5: 0.8, 6: 1.0, 7: 1.0, 8: 0.9, 9: 0.6, 10: 0.3, 11: 0.1, 12: 0.1, 1: 0.1, 2: 0.1},
        'extreme_heat': {3: 0.0, 4: 0.1, 5: 0.3, 6: 0.7, 7: 1.0, 8: 0.9, 9: 0.4, 10: 0.1, 11: 0.0, 12: 0.0, 1: 0.0, 2: 0.0},
        'infectious_disease': {3: 0.5, 4: 0.3, 5: 0.2, 6: 0.1, 7: 0.1, 8: 0.2, 9: 0.4, 10: 0.6, 11: 0.8, 12: 1.0, 1: 0.9, 2: 0.7}
    }
    
    # Get pattern for requested risk type (default to flat pattern)
    pattern = seasonal_patterns.get(risk_type, {m: 0.5 for m in range(1, 13)})
    
    # Generate daily calendar
    calendar_data = {}
    for month in range(1, 13):
        # Get days in month
        days_in_month = calendar.monthrange(year, month)[1]
        
        # Get base risk for this month
        base_risk = pattern.get(month, 0.5)
        
        # Generate entry for each day
        for day in range(1, days_in_month + 1):
            date_str = f"{year}-{month:02d}-{day:02d}"
            
            # Add some daily variation (±10%)
            import random
            daily_variation = random.uniform(-0.1, 0.1)
            daily_risk = max(0.0, min(1.0, base_risk + daily_variation))
            
            calendar_data[date_str] = float(daily_risk)
    
    return calendar_data