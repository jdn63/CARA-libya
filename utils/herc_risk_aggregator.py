"""
HERC Risk Aggregation Module

This module calculates real risk scores for HERC regions by aggregating
risk data from all constituent jurisdictions within each region.

Includes database-backed caching for instant dashboard loading and
background pre-computation to prevent timeout issues.
"""

import logging
import time
from datetime import datetime
from typing import Dict, List, Any, Optional
from statistics import mean, median

from utils.jurisdictions_code import jurisdictions
from utils.jurisdiction_mapping_code import jurisdiction_mapping
from utils.herc_data import get_all_herc_regions
from utils.main_risk_calculator import CARARiskCalculator
from utils.data_processor import process_risk_data
from utils.config_manager import get_config_manager

logger = logging.getLogger(__name__)

# Cache for HERC region risk data (TTL: 1 hour)
_herc_cache: Dict[str, Dict[str, Any]] = {}
_herc_cache_ttl = 3600  # 1 hour in seconds

# Cache for individual jurisdiction risk data (TTL: 30 minutes)
_jurisdiction_cache: Dict[str, Dict[str, Any]] = {}
_jurisdiction_cache_ttl = 1800  # 30 minutes


def _get_cached_jurisdiction_risk(jurisdiction_id: str) -> Optional[Dict[str, Any]]:
    """Get cached jurisdiction risk data if available and not expired."""
    if jurisdiction_id in _jurisdiction_cache:
        cached = _jurisdiction_cache[jurisdiction_id]
        if time.time() - cached.get('_cached_at', 0) < _jurisdiction_cache_ttl:
            return cached
    return None


def _cache_jurisdiction_risk(jurisdiction_id: str, risk_data: Dict[str, Any]) -> None:
    """Cache jurisdiction risk data."""
    risk_data['_cached_at'] = time.time()
    _jurisdiction_cache[jurisdiction_id] = risk_data


class HERCRiskAggregator:
    """
    Aggregates risk data for HERC regions from constituent jurisdictions.
    """
    
    def __init__(self):
        self.herc_regions = get_all_herc_regions()
        
    def get_jurisdictions_for_herc_region(self, herc_id: str) -> List[Dict[str, Any]]:
        """
        Get all jurisdictions that belong to a HERC region.
        
        Args:
            herc_id: ID of the HERC region
            
        Returns:
            List of jurisdiction dictionaries
        """
        # Find the HERC region
        region = next((r for r in self.herc_regions if r.get('id') == herc_id), None)
        if not region:
            logger.error(f"HERC region not found: {herc_id}")
            return []
        
        counties = region.get('counties', [])
        region_jurisdictions = []
        
        # Find all jurisdictions that belong to these counties
        for jurisdiction in jurisdictions:
            jurisdiction_id = jurisdiction['id']
            county = jurisdiction_mapping.get(jurisdiction_id)
            
            if county in counties:
                region_jurisdictions.append(jurisdiction)
        
        logger.info(f"Found {len(region_jurisdictions)} jurisdictions in HERC region {herc_id} ({region.get('name')})")
        return region_jurisdictions
    
    def calculate_herc_region_risk(self, herc_id: str) -> Optional[Dict[str, Any]]:
        """
        Calculate aggregated risk scores for a HERC region.
        
        Uses caching to prevent timeout issues from multiple API calls.
        
        Args:
            herc_id: ID of the HERC region
            
        Returns:
            Dictionary containing aggregated risk scores and metrics
        """
        try:
            # Check HERC-level cache first
            if herc_id in _herc_cache:
                cached = _herc_cache[herc_id]
                if time.time() - cached.get('_cached_at', 0) < _herc_cache_ttl:
                    logger.info(f"Returning cached HERC risk data for region {herc_id}")
                    return cached
            
            # Get region info
            region = next((r for r in self.herc_regions if r.get('id') == herc_id), None)
            if not region:
                logger.error(f"HERC region not found: {herc_id}")
                return None
            
            # Get all jurisdictions in this region
            region_jurisdictions = self.get_jurisdictions_for_herc_region(herc_id)
            
            if not region_jurisdictions:
                logger.warning(f"No jurisdictions found for HERC region {herc_id}")
                return None
            
            # Calculate risk for each jurisdiction
            jurisdiction_risks = []
            natural_hazards_scores = []
            health_scores = []
            active_shooter_scores = []
            extreme_heat_scores = []
            air_quality_scores = []
            cybersecurity_scores = []
            utilities_scores = []
            dam_failure_scores = []
            vector_borne_disease_scores = []
            
            # Natural hazard components
            flood_scores = []
            tornado_scores = []
            winter_storm_scores = []
            thunderstorm_scores = []
            
            # Temporal risk data structure
            temporal_data = {
                'flood': {'composite_scores': [], 'baseline': [], 'seasonal': [], 'trend': [], 'acute': []},
                'tornado': {'composite_scores': [], 'baseline': [], 'seasonal': [], 'trend': [], 'acute': []},
                'winter_storm': {'composite_scores': [], 'baseline': [], 'seasonal': [], 'trend': [], 'acute': []},
                'extreme_heat': {'composite_scores': [], 'baseline': [], 'seasonal': [], 'trend': [], 'acute': []},
                'thunderstorm': {'composite_scores': [], 'baseline': [], 'seasonal': [], 'trend': [], 'acute': []},
                'health': {'composite_scores': [], 'baseline': [], 'seasonal': [], 'trend': [], 'acute': []},
                'active_shooter': {'composite_scores': [], 'baseline': [], 'seasonal': [], 'trend': [], 'acute': []}
            }
            
            successful_calculations = 0
            
            for jurisdiction in region_jurisdictions:
                try:
                    jurisdiction_id = jurisdiction['id']
                    
                    # Check jurisdiction cache first
                    cached_data = _get_cached_jurisdiction_risk(jurisdiction_id)
                    if cached_data:
                        risk_data = cached_data.get('risk_data', {})
                        comprehensive_risk = cached_data.get('comprehensive_risk', {})
                    else:
                        # Calculate risk using real risk calculator
                        calculator = CARARiskCalculator(jurisdiction_id)
                        risk_data = process_risk_data(jurisdiction_id)
                        comprehensive_risk = calculator.calculate_comprehensive_risk(risk_data)
                        
                        # Cache for future use
                        _cache_jurisdiction_risk(jurisdiction_id, {
                            'risk_data': risk_data,
                            'comprehensive_risk': comprehensive_risk
                        })
                    
                    # Collect domain scores from domain_scores dict
                    domain_scores = comprehensive_risk.get('domain_scores', {})
                    natural_hazards_scores.append(domain_scores.get('natural_hazards', 0.0))
                    health_scores.append(domain_scores.get('health_metrics', 0.0))
                    active_shooter_scores.append(domain_scores.get('active_shooter', 0.0))
                    extreme_heat_scores.append(domain_scores.get('extreme_heat', 0.0))
                    air_quality_scores.append(domain_scores.get('air_quality', 0.0))
                    cybersecurity_scores.append(domain_scores.get('cybersecurity', 0.0))
                    utilities_scores.append(domain_scores.get('utilities', 0.0))
                    dam_failure_scores.append(domain_scores.get('dam_failure', 0.0))
                    vector_borne_disease_scores.append(domain_scores.get('vector_borne_disease', 0.0))
                    
                    # Collect natural hazard components
                    natural_hazards_detail = risk_data.get('natural_hazards', {})
                    flood_scores.append(natural_hazards_detail.get('flood', 0.0))
                    tornado_scores.append(natural_hazards_detail.get('tornado', 0.0))
                    winter_storm_scores.append(natural_hazards_detail.get('winter_storm', 0.0))
                    thunderstorm_scores.append(natural_hazards_detail.get('thunderstorm', 0.0))
                    
                    # Collect temporal risk data if available
                    temporal_risk_detail = risk_data.get('temporal_risk_detail', {})
                    for hazard_type in temporal_data.keys():
                        if hazard_type in temporal_risk_detail:
                            hazard_temporal = temporal_risk_detail[hazard_type]
                            if isinstance(hazard_temporal, dict):
                                temporal_data[hazard_type]['composite_scores'].append(
                                    hazard_temporal.get('composite_score', 0.0)
                                )
                                components = hazard_temporal.get('temporal_components', {})
                                temporal_data[hazard_type]['baseline'].append(components.get('baseline', 0.0))
                                temporal_data[hazard_type]['seasonal'].append(components.get('seasonal', 0.0))
                                temporal_data[hazard_type]['trend'].append(components.get('trend', 0.0))
                                temporal_data[hazard_type]['acute'].append(components.get('acute', 0.0))
                    
                    jurisdiction_risks.append(comprehensive_risk.get('total_risk_score', 0.0))
                    successful_calculations += 1
                    
                except Exception as e:
                    logger.warning(f"Failed to calculate risk for jurisdiction {jurisdiction.get('id')}: {e}")
                    continue
            
            if successful_calculations == 0:
                logger.error(f"No successful risk calculations for HERC region {herc_id}")
                return None
            
            # Calculate aggregated domain scores
            natural_hazards_avg = mean(natural_hazards_scores) if natural_hazards_scores else 0.0
            health_avg = mean(health_scores) if health_scores else 0.0
            active_shooter_avg = mean(active_shooter_scores) if active_shooter_scores else 0.0
            extreme_heat_avg = mean(extreme_heat_scores) if extreme_heat_scores else 0.0
            air_quality_avg = mean(air_quality_scores) if air_quality_scores else 0.0
            cybersecurity_avg = mean(cybersecurity_scores) if cybersecurity_scores else 0.0
            utilities_avg = mean(utilities_scores) if utilities_scores else 0.0
            dam_failure_avg = mean(dam_failure_scores) if dam_failure_scores else 0.0
            vector_borne_disease_avg = mean(vector_borne_disease_scores) if vector_borne_disease_scores else 0.0
            
            # Get weights configuration for total risk calculation
            config_manager = get_config_manager()
            weights = config_manager.get_overall_weights()
            
            # Calculate regional total risk score from aggregated domain scores
            total_risk = (
                natural_hazards_avg * weights.get('natural_hazards', 0.35) +
                health_avg * weights.get('health_metrics', 0.20) +
                active_shooter_avg * weights.get('active_shooter', 0.15) +
                extreme_heat_avg * weights.get('extreme_heat', 0.15) +
                cybersecurity_avg * weights.get('cybersecurity', 0.15) +
                dam_failure_avg * weights.get('dam_failure', 0.0) +
                vector_borne_disease_avg * weights.get('vector_borne_disease', 0.0)
            )
            
            # Calculate aggregated metrics (using mean for averaging)
            aggregated_risk = {
                'herc_id': herc_id,
                'name': region.get('name'),
                'counties': region.get('counties', []),
                'jurisdiction_count': len(region_jurisdictions),
                'successful_calculations': successful_calculations,
                
                # Overall scores - recalculated from aggregated domain scores
                'total_risk_score': round(total_risk, 4),
                
                # Domain scores
                'natural_hazards_risk': natural_hazards_avg,
                'health_risk': health_avg,
                'active_shooter_risk': active_shooter_avg,
                'extreme_heat_risk': extreme_heat_avg,
                'air_quality_risk': air_quality_avg,
                'cybersecurity_risk': cybersecurity_avg,
                'utilities_risk': utilities_avg,
                'dam_failure_risk': dam_failure_avg,
                'vector_borne_disease_risk': vector_borne_disease_avg,
                
                # Natural hazard components
                'flood_risk': mean(flood_scores) if flood_scores else 0.0,
                'tornado_risk': mean(tornado_scores) if tornado_scores else 0.0,
                'winter_storm_risk': mean(winter_storm_scores) if winter_storm_scores else 0.0,
                'thunderstorm_risk': mean(thunderstorm_scores) if thunderstorm_scores else 0.0,
                
                # Natural hazards breakdown for template
                'natural_hazards': {
                    'flood': mean(flood_scores) if flood_scores else 0.0,
                    'tornado': mean(tornado_scores) if tornado_scores else 0.0,
                    'winter_storm': mean(winter_storm_scores) if winter_storm_scores else 0.0,
                    'thunderstorm': mean(thunderstorm_scores) if thunderstorm_scores else 0.0
                }
            }
            
            # Calculate temporal risk data
            temporal_risk_data = {}
            for hazard_type, data in temporal_data.items():
                if data['composite_scores']:
                    temporal_risk_data[hazard_type] = {
                        'composite_score': mean(data['composite_scores']),
                        'temporal_components': {
                            'baseline': mean(data['baseline']) if data['baseline'] else 0.0,
                            'seasonal': mean(data['seasonal']) if data['seasonal'] else 0.0,
                            'trend': mean(data['trend']) if data['trend'] else 0.0,
                            'acute': mean(data['acute']) if data['acute'] else 0.0
                        }
                    }
            
            aggregated_risk['temporal_risk_data'] = temporal_risk_data
            
            logger.info(f"Successfully calculated aggregated risk for HERC region {herc_id}: " +
                       f"Total Risk = {aggregated_risk['total_risk_score']:.3f}")
            
            # Cache the HERC region result
            aggregated_risk['_cached_at'] = time.time()
            _herc_cache[herc_id] = aggregated_risk
            
            return aggregated_risk
            
        except Exception as e:
            logger.error(f"Error calculating HERC region risk for {herc_id}: {e}")
            import traceback
            logger.debug(f"Traceback: {traceback.format_exc()}")
            return None


def get_herc_region_risk(herc_id: str) -> Optional[Dict[str, Any]]:
    """
    Convenience function to get HERC region risk data.
    
    First checks database cache, then falls back to live calculation if needed.
    
    Args:
        herc_id: ID of the HERC region
        
    Returns:
        Dictionary containing aggregated risk scores
    """
    # Try database cache first
    cached = get_cached_herc_risk(herc_id)
    if cached:
        logger.info(f"Returning database-cached HERC risk data for region {herc_id}")
        return cached
    
    # Fall back to live calculation
    logger.info(f"No cached data for HERC region {herc_id}, calculating live...")
    aggregator = HERCRiskAggregator()
    result = aggregator.calculate_herc_region_risk(herc_id)
    
    # Save to database cache for future requests
    if result:
        save_herc_risk_to_cache(herc_id, result)
    
    return result


def get_cached_herc_risk(herc_id: str, max_age_hours: int = 4) -> Optional[Dict[str, Any]]:
    """
    Get cached HERC risk data from database.
    
    Args:
        herc_id: ID of the HERC region
        max_age_hours: Maximum age of cached data in hours (default: 4)
        
    Returns:
        Cached risk data if available and fresh, None otherwise
    """
    try:
        from core import db
        from models import HERCRiskCache
        from flask import has_app_context
        
        # Only query if we have an app context
        if not has_app_context():
            logger.debug("No app context available for HERC cache query")
            return None
        
        cache_entry = db.session.query(HERCRiskCache).filter_by(
            herc_id=herc_id,
            is_valid=True
        ).first()
        
        if not cache_entry:
            logger.debug(f"No cache entry found for HERC region {herc_id}")
            return None
        
        # Check if cache is fresh enough
        age_hours = cache_entry.age_minutes / 60 if cache_entry.age_minutes else float('inf')
        if age_hours > max_age_hours:
            logger.info(f"Cache for HERC region {herc_id} is stale ({age_hours:.1f}h old)")
            return None
        
        logger.info(f"Found fresh cache for HERC region {herc_id} ({age_hours:.1f}h old)")
        risk_data = dict(cache_entry.risk_data)  # Make a copy
        risk_data['_from_db_cache'] = True
        risk_data['_cache_age_minutes'] = cache_entry.age_minutes
        return risk_data
            
    except Exception as e:
        logger.warning(f"Error reading HERC cache from database: {e}")
        return None


def save_herc_risk_to_cache(herc_id: str, risk_data: Dict[str, Any], 
                            duration_seconds: float = None) -> bool:
    """
    Save HERC risk data to database cache.
    
    Args:
        herc_id: ID of the HERC region
        risk_data: Calculated risk data to cache
        duration_seconds: How long the calculation took
        
    Returns:
        True if saved successfully, False otherwise
    """
    try:
        from core import db
        from models import HERCRiskCache
        from flask import has_app_context
        
        # Only save if we have an app context
        if not has_app_context():
            logger.debug("No app context available for HERC cache save")
            return False
        
        # Clean up internal cache keys before saving
        clean_data = {k: v for k, v in risk_data.items() 
                     if not k.startswith('_')}
        
        # Check if entry exists
        cache_entry = db.session.query(HERCRiskCache).filter_by(
            herc_id=herc_id
        ).first()
        
        if cache_entry:
            # Update existing entry
            cache_entry.risk_data = clean_data
            cache_entry.calculated_at = datetime.utcnow()
            cache_entry.is_valid = True
            cache_entry.calculation_duration_seconds = duration_seconds
            cache_entry.jurisdiction_count = risk_data.get('jurisdiction_count')
            cache_entry.error_message = None
        else:
            # Create new entry
            cache_entry = HERCRiskCache(
                herc_id=herc_id,
                name=risk_data.get('name', f'HERC Region {herc_id}'),
                risk_data=clean_data,
                calculated_at=datetime.utcnow(),
                is_valid=True,
                calculation_duration_seconds=duration_seconds,
                jurisdiction_count=risk_data.get('jurisdiction_count')
            )
            db.session.add(cache_entry)
        
        db.session.commit()
        logger.info(f"Saved HERC risk data to database cache for region {herc_id}")
        return True
            
    except Exception as e:
        logger.error(f"Error saving HERC cache to database: {e}")
        db.session.rollback()
        return False


def precompute_all_herc_regions() -> Dict[str, Any]:
    """
    Pre-compute risk data for all HERC regions and save to database.
    
    This function is designed to be called by the background scheduler
    to ensure HERC dashboards load instantly.
    
    Returns:
        Dictionary with results for each region
    """
    logger.info("Starting pre-computation of all HERC regions...")
    start_time = time.time()
    
    herc_regions = get_all_herc_regions()
    results = {
        'started_at': datetime.utcnow().isoformat(),
        'regions': {},
        'success_count': 0,
        'error_count': 0
    }
    
    aggregator = HERCRiskAggregator()
    
    for region in herc_regions:
        herc_id = region.get('id')
        region_name = region.get('name', f'Region {herc_id}')
        
        try:
            region_start = time.time()
            logger.info(f"Pre-computing HERC region {herc_id}: {region_name}")
            
            # Calculate risk data (bypassing cache)
            risk_data = aggregator.calculate_herc_region_risk(herc_id)
            
            if risk_data:
                duration = time.time() - region_start
                
                # Save to database
                save_herc_risk_to_cache(herc_id, risk_data, duration)
                
                results['regions'][herc_id] = {
                    'status': 'success',
                    'name': region_name,
                    'duration_seconds': round(duration, 2),
                    'total_risk_score': risk_data.get('total_risk_score')
                }
                results['success_count'] += 1
                logger.info(f"Successfully pre-computed HERC region {herc_id} in {duration:.1f}s")
            else:
                results['regions'][herc_id] = {
                    'status': 'error',
                    'name': region_name,
                    'error': 'Calculation returned None'
                }
                results['error_count'] += 1
                
        except Exception as e:
            logger.error(f"Error pre-computing HERC region {herc_id}: {e}")
            results['regions'][herc_id] = {
                'status': 'error',
                'name': region_name,
                'error': str(e)
            }
            results['error_count'] += 1
    
    total_duration = time.time() - start_time
    results['total_duration_seconds'] = round(total_duration, 2)
    results['finished_at'] = datetime.utcnow().isoformat()
    
    logger.info(f"HERC pre-computation complete: {results['success_count']} success, " +
               f"{results['error_count']} errors in {total_duration:.1f}s")
    
    return results
