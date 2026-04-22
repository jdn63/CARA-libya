"""
CARA Risk Assessment Configuration Manager

This module handles loading and managing risk assessment weights from YAML configuration,
including jurisdiction-specific overrides, normalization settings, and contribution logging.
"""

import os
import yaml
import logging
import threading
from typing import Dict, Any, Optional, List, Tuple
from sklearn.preprocessing import StandardScaler, QuantileTransformer, MinMaxScaler
import numpy as np
from datetime import datetime

logger = logging.getLogger(__name__)

class RiskConfigManager:
    """
    Manages risk assessment configuration including weights, normalization, and logging settings.
    All mutable state is protected by a threading lock for concurrent access safety.
    """
    
    def __init__(self, config_path: str = 'config/risk_weights.yaml'):
        self.config_path = config_path
        self.config = {}
        self.jurisdiction_cache = {}
        self.scalers = {}
        self.contribution_logs = []
        self._lock = threading.Lock()
        self.load_config()
    
    def load_config(self) -> None:
        """Load configuration from YAML file"""
        try:
            with open(self.config_path, 'r') as file:
                self.config = yaml.safe_load(file)
            logger.info(f"Loaded risk configuration from {self.config_path}")
            
            # Validate critical sections exist
            required_sections = ['overall_risk_weights', 'temporal_weights', 'normalization']
            for section in required_sections:
                if section not in self.config:
                    logger.warning(f"Missing required configuration section: {section}")
                    
        except FileNotFoundError:
            logger.error(f"Configuration file not found: {self.config_path}")
            self._load_fallback_config()
        except yaml.YAMLError as e:
            logger.error(f"Error parsing YAML configuration: {e}")
            self._load_fallback_config()
    
    def _load_fallback_config(self) -> None:
        """Load minimal fallback configuration if main config fails"""
        logger.warning("Loading fallback configuration")
        self.config = {
            'overall_risk_weights': {
                'natural_hazards': 0.35,
                'health_metrics': 0.20,
                'active_shooter': 0.15,
                'extreme_heat': 0.15,
                'cybersecurity': 0.15
            },
            'temporal_weights': {
                'strategic_planning': {
                    'baseline': 0.60,
                    'seasonal': 0.25,
                    'trend': 0.15,
                    'acute': 0.00
                }
            },
            'normalization': {
                'method': 'zscore'
            },
            'contribution_logging': {
                'enabled': True,
                'top_contributors_count': 5
            }
        }
    
    def get_overall_weights(self, jurisdiction_id: Optional[str] = None) -> Dict[str, float]:
        """
        Get overall risk domain weights, with optional jurisdiction-specific overrides.
        
        Args:
            jurisdiction_id: Optional jurisdiction identifier for custom weights
            
        Returns:
            Dictionary of risk domain weights
        """
        base_weights = self.config.get('overall_risk_weights', {})
        
        # Check for jurisdiction-specific overrides
        if jurisdiction_id:
            overrides = self.config.get('jurisdiction_overrides', {})
            if jurisdiction_id in overrides:
                override_weights = overrides[jurisdiction_id].get('overall_risk_weights', {})
                # Merge overrides with base weights
                weights = {**base_weights, **override_weights}
                logger.info(f"Applied jurisdiction override weights for {jurisdiction_id}")
                return weights
        
        return base_weights
    
    def get_temporal_weights(self, mode: str = 'strategic_planning', risk_type: str = None) -> Dict[str, float]:
        """
        Get temporal component weights based on planning mode and optional risk type.
        
        If a domain-specific override exists for the risk_type, those weights
        are returned instead of the mode-level defaults.
        
        Args:
            mode: Planning mode ('strategic_planning' or 'emergency_response')
            risk_type: Optional risk domain for domain-specific overrides
            
        Returns:
            Dictionary of temporal component weights
        """
        temporal_config = self.config.get('temporal_weights', {})
        
        if risk_type:
            domain_overrides = temporal_config.get('domain_overrides', {})
            if risk_type in domain_overrides:
                override = domain_overrides[risk_type]
                logger.info(f"Using domain-specific temporal weights for {risk_type}: {override}")
                return override
        
        mode_weights = temporal_config.get(mode, temporal_config.get('strategic_planning', {}))
        
        if not mode_weights:
            logger.warning(f"No temporal weights found for mode '{mode}', using defaults")
            return {'baseline': 0.60, 'seasonal': 0.25, 'trend': 0.15, 'acute': 0.00}
        
        return mode_weights
    
    def get_domain_weights(self, domain: str) -> Dict[str, float]:
        """
        Get sub-domain weights for a specific risk domain.
        
        Args:
            domain: Risk domain name (e.g., 'active_shooter', 'natural_hazards')
            
        Returns:
            Dictionary of sub-domain weights
        """
        weights_key = f"{domain}_weights"
        return self.config.get(weights_key, {})
    
    def normalize_scores(self, scores: Dict[str, float], domain: str) -> Dict[str, float]:
        """
        Apply normalization to risk scores based on configuration.
        
        Args:
            scores: Dictionary of raw scores to normalize
            domain: Domain name for scaler caching
            
        Returns:
            Dictionary of normalized scores
        """
        normalization_config = self.config.get('normalization', {})
        method = normalization_config.get('method', 'none')
        
        if method == 'none' or not scores:
            return scores
        
        # Convert scores to numpy array for sklearn
        score_names = list(scores.keys())
        score_values = np.array(list(scores.values())).reshape(-1, 1)
        
        scaler_key = f"{domain}_{method}"
        with self._lock:
            if scaler_key not in self.scalers:
                if method == 'zscore':
                    self.scalers[scaler_key] = StandardScaler()
                elif method == 'quantile':
                    n_quantiles = min(100, len(score_values))
                    self.scalers[scaler_key] = QuantileTransformer(n_quantiles=n_quantiles)
                elif method == 'minmax':
                    self.scalers[scaler_key] = MinMaxScaler()
                else:
                    logger.warning(f"Unknown normalization method: {method}")
                    return scores

            try:
                if len(score_values) == 1:
                    logger.debug(f"Single value normalization skipped for domain {domain}")
                    return scores

                if not hasattr(self.scalers[scaler_key], 'scale_'):
                    normalized_values = self.scalers[scaler_key].fit_transform(score_values)
                else:
                    normalized_values = self.scalers[scaler_key].transform(score_values)

                normalized_scores = {}
                for i, name in enumerate(score_names):
                    normalized_scores[name] = float(normalized_values[i][0])

                if method == 'zscore' and normalization_config.get('zscore', {}).get('clip_outliers', False):
                    threshold = normalization_config.get('zscore', {}).get('outlier_threshold', 3.0)
                    for name in normalized_scores:
                        normalized_scores[name] = np.clip(normalized_scores[name], -threshold, threshold)

                logger.debug(f"Applied {method} normalization to {domain} scores")
                return normalized_scores

            except Exception as e:
                logger.error(f"Error during normalization: {e}")
                return scores
    
    def log_contribution(self, domain: str, variable_contributions: List[Tuple[str, float, Any]], 
                        final_score: float, jurisdiction_id: Optional[str] = None) -> None:
        """
        Log the top contributing variables to a risk score.
        
        Args:
            domain: Risk domain name
            variable_contributions: List of (variable_name, contribution_value, raw_value) tuples
            final_score: Final calculated risk score
            jurisdiction_id: Optional jurisdiction identifier
        """
        logging_config = self.config.get('contribution_logging', {})
        
        if not logging_config.get('enabled', False):
            return
        
        top_count = logging_config.get('top_contributors_count', 5)
        log_level = logging_config.get('log_level', 'INFO')
        include_raw = logging_config.get('include_raw_values', True)
        include_normalized = logging_config.get('include_normalized_values', True)
        
        # Sort contributions by absolute value (highest impact first)
        sorted_contributions = sorted(variable_contributions, 
                                    key=lambda x: abs(x[1]), reverse=True)[:top_count]
        
        # Create log entry
        log_entry = {
            'timestamp': datetime.now().isoformat(),
            'domain': domain,
            'jurisdiction_id': jurisdiction_id,
            'final_score': final_score,
            'top_contributors': []
        }
        
        contribution_msg = f"[{domain.upper()}] Risk Score: {final_score:.4f} | Top Contributors:"
        
        for i, (var_name, contribution, raw_value) in enumerate(sorted_contributions, 1):
            contrib_info = {
                'rank': i,
                'variable': var_name,
                'contribution': contribution
            }
            
            if include_raw:
                contrib_info['raw_value'] = raw_value
            
            log_entry['top_contributors'].append(contrib_info)
            
            # Build log message
            contrib_detail = f" {i}. {var_name}: {contribution:.4f}"
            if include_raw:
                contrib_detail += f" (raw: {raw_value})"
            contribution_msg += contrib_detail
        
        # Log at specified level
        if log_level.upper() == 'DEBUG':
            logger.debug(contribution_msg)
        elif log_level.upper() == 'WARNING':
            logger.warning(contribution_msg)
        elif log_level.upper() == 'ERROR':
            logger.error(contribution_msg)
        else:  # Default to INFO
            logger.info(contribution_msg)
        
        with self._lock:
            self.contribution_logs.append(log_entry)
    
    def get_contribution_history(self, domain: Optional[str] = None, 
                               jurisdiction_id: Optional[str] = None) -> List[Dict]:
        """
        Retrieve contribution logging history.
        
        Args:
            domain: Optional domain filter
            jurisdiction_id: Optional jurisdiction filter
            
        Returns:
            List of contribution log entries
        """
        with self._lock:
            filtered_logs = list(self.contribution_logs)
        
        if domain:
            filtered_logs = [log for log in filtered_logs if log['domain'] == domain]
        
        if jurisdiction_id:
            filtered_logs = [log for log in filtered_logs if log['jurisdiction_id'] == jurisdiction_id]
        
        return filtered_logs
    
    def validate_weights(self, weights: Dict[str, float], tolerance: float = 0.01) -> bool:
        """
        Validate that weights sum to approximately 1.0.
        
        Args:
            weights: Dictionary of weights to validate
            tolerance: Acceptable deviation from 1.0
            
        Returns:
            True if weights are valid, False otherwise
        """
        total = sum(weights.values())
        is_valid = abs(total - 1.0) <= tolerance
        
        if not is_valid:
            logger.warning(f"Weight validation failed: sum={total:.4f}, expected=1.0±{tolerance}")
        
        return is_valid
    
    def get_config_info(self) -> Dict[str, Any]:
        """
        Get configuration metadata and summary information.
        
        Returns:
            Dictionary with configuration information
        """
        return {
            'version': self.config.get('version', 'unknown'),
            'last_updated': self.config.get('last_updated', 'unknown'),
            'config_path': self.config_path,
            'normalization_method': self.config.get('normalization', {}).get('method', 'none'),
            'contribution_logging_enabled': self.config.get('contribution_logging', {}).get('enabled', False),
            'jurisdiction_overrides_count': len(self.config.get('jurisdiction_overrides', {})),
            'total_contribution_logs': len(self.contribution_logs)  # approximate; not locked for stats
        }

# Global configuration manager instance
config_manager = RiskConfigManager()

def get_config_manager() -> RiskConfigManager:
    """Get the global configuration manager instance"""
    return config_manager