"""
Background Export Job Worker

This module provides asynchronous processing of GIS export jobs to preserve
data accuracy while avoiding web request timeouts.
"""

import logging
import threading
import time
from datetime import datetime
from typing import Optional, List
import traceback
from concurrent.futures import ThreadPoolExecutor, as_completed

from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.interval import IntervalTrigger
from sqlalchemy.exc import SQLAlchemyError

from core import db, create_app
from models import ExportJob
from utils.gis_export import CARAGISExporter
from utils.data_processor import process_risk_data
from utils.main_risk_calculator import CARARiskCalculator
from utils.jurisdictions_code import jurisdictions

logger = logging.getLogger(__name__)

class ExportJobWorker:
    """
    Background worker that processes export jobs asynchronously.
    
    This worker runs in a separate thread and polls for queued jobs,
    processing them with controlled concurrency to avoid overwhelming
    external APIs while preserving data accuracy.
    """
    
    def __init__(self, app=None):
        self.app = app
        self.scheduler = None
        self.is_running = False
        self.worker_thread = None
        self.max_concurrent_requests = 3  # Limit concurrent API calls
        self.job_check_interval = 5  # Check for new jobs every 5 seconds
        
    def start_worker(self):
        """Start the background job worker."""
        if self.is_running:
            logger.warning("Export job worker is already running")
            return
            
        logger.info("Starting export job worker")
        self.is_running = True
        
        # Start scheduler for periodic job checking
        self.scheduler = BackgroundScheduler()
        self.scheduler.add_job(
            func=self._process_queued_jobs,
            trigger=IntervalTrigger(seconds=self.job_check_interval),
            id='export_job_processor',
            name='Process Export Jobs',
            max_instances=1,  # Prevent overlapping executions
            replace_existing=True
        )
        
        try:
            self.scheduler.start()
            logger.info(f"Export job worker started, checking for jobs every {self.job_check_interval} seconds")
        except Exception as e:
            logger.error(f"Failed to start export job worker: {e}")
            self.is_running = False
            raise
    
    def stop_worker(self):
        """Stop the background job worker."""
        if not self.is_running:
            return
            
        logger.info("Stopping export job worker")
        self.is_running = False
        
        if self.scheduler and self.scheduler.running:
            self.scheduler.shutdown(wait=False)
            
        logger.info("Export job worker stopped")
    
    def _process_queued_jobs(self):
        """Process all queued export jobs."""
        if not self.app:
            logger.error("No Flask app context available for job processing")
            return
            
        with self.app.app_context():
            try:
                # Get all queued jobs
                queued_jobs = db.session.query(ExportJob).filter(
                    ExportJob.status == 'queued'
                ).order_by(ExportJob.created_at).all()
                
                if not queued_jobs:
                    logger.debug("No queued export jobs found")
                    return
                
                logger.info(f"Found {len(queued_jobs)} queued export jobs")
                
                for job in queued_jobs:
                    try:
                        self._process_single_job(job)
                    except Exception as e:
                        logger.error(f"Failed to process job {job.id}: {e}")
                        self._mark_job_failed(job, str(e))
                        
            except SQLAlchemyError as e:
                logger.error(f"Database error while processing jobs: {e}")
            except Exception as e:
                logger.error(f"Unexpected error in job processor: {e}")
    
    def _process_single_job(self, job: ExportJob):
        """Process a single export job."""
        logger.info(f"Starting processing of job {job.id}")
        
        # Mark job as running
        job.status = 'running'
        job.started_at = datetime.utcnow()
        
        if job.export_type == 'all_jurisdictions':
            job.total_count = len(jurisdictions)
        else:
            job.total_count = 1
            
        db.session.commit()
        
        try:
            if job.export_type == 'all_jurisdictions':
                self._process_all_jurisdictions_job(job)
            else:
                self._process_single_jurisdiction_job(job)
                
            # Mark job as completed
            job.status = 'completed'
            job.finished_at = datetime.utcnow()
            db.session.commit()
            
            logger.info(f"Successfully completed job {job.id}")
            
        except Exception as e:
            logger.error(f"Error processing job {job.id}: {e}")
            self._mark_job_failed(job, str(e))
            raise
    
    def _process_all_jurisdictions_job(self, job: ExportJob):
        """Process export job for all Wisconsin jurisdictions."""
        logger.info(f"Processing all jurisdictions export job {job.id}")
        
        # Create exporter instance
        exporter = CARAGISExporter()
        all_data = []
        data_sources_used = {'fresh': 0, 'cached': 0, 'errors': 0}
        
        # Process jurisdictions in batches with controlled concurrency
        with ThreadPoolExecutor(max_workers=self.max_concurrent_requests) as executor:
            # Submit all jurisdiction processing tasks
            future_to_jurisdiction = {
                executor.submit(self._process_jurisdiction_data, j): j 
                for j in jurisdictions
            }
            
            # Collect results as they complete
            for future in as_completed(future_to_jurisdiction):
                jurisdiction = future_to_jurisdiction[future]
                
                try:
                    result = future.result(timeout=30)  # 30-second timeout per jurisdiction
                    if result:
                        all_data.append(result['data'])
                        # Track data source freshness
                        if result.get('fresh_data', True):
                            data_sources_used['fresh'] += 1
                        else:
                            data_sources_used['cached'] += 1
                    
                    # Update progress
                    job.completed_count += 1
                    db.session.commit()
                    
                    logger.debug(f"Completed jurisdiction {jurisdiction['id']} ({job.completed_count}/{job.total_count})")
                    
                except Exception as e:
                    logger.warning(f"Failed to process jurisdiction {jurisdiction['id']}: {e}")
                    job.error_count += 1
                    data_sources_used['errors'] += 1
                    job.completed_count += 1
                    db.session.commit()
        
        # Export data to files
        if all_data:
            try:
                csv_path = exporter.export_to_csv(all_data)
                geojson_path = exporter.export_to_geojson(all_data)
                
                job.result_files = {
                    'csv': csv_path,
                    'geojson': geojson_path,
                    'record_count': len(all_data)
                }
                job.data_sources_used = data_sources_used
                db.session.commit()
                
                logger.info(f"Export files created: CSV={csv_path}, GeoJSON={geojson_path}")
                
            except Exception as e:
                logger.error(f"Failed to create export files for job {job.id}: {e}")
                raise
        else:
            raise Exception("No jurisdiction data was successfully processed")
    
    def _process_single_jurisdiction_job(self, job: ExportJob):
        """Process export job for a single jurisdiction."""
        jurisdiction_id = job.params.get('jurisdiction_id')
        if not jurisdiction_id:
            raise ValueError("Single jurisdiction job missing jurisdiction_id parameter")
        
        logger.info(f"Processing single jurisdiction export job {job.id} for {jurisdiction_id}")
        
        # Find the jurisdiction
        jurisdiction = None
        for j in jurisdictions:
            if j['id'] == jurisdiction_id:
                jurisdiction = j
                break
        
        if not jurisdiction:
            raise ValueError(f"Jurisdiction {jurisdiction_id} not found")
        
        # Process the jurisdiction
        result = self._process_jurisdiction_data(jurisdiction)
        if not result:
            raise Exception(f"Failed to process jurisdiction {jurisdiction_id}")
        
        # Create exporter and export data
        exporter = CARAGISExporter()
        csv_path = exporter.export_to_csv([result['data']], 
                                        f'cara_jurisdiction_{jurisdiction_id}_{exporter.timestamp}.csv')
        geojson_path = exporter.export_to_geojson([result['data']], 
                                                f'cara_jurisdiction_{jurisdiction_id}_{exporter.timestamp}.geojson')
        
        job.result_files = {
            'csv': csv_path,
            'geojson': geojson_path,
            'record_count': 1
        }
        job.data_sources_used = {
            'fresh': 1 if result.get('fresh_data', True) else 0,
            'cached': 0 if result.get('fresh_data', True) else 1,
            'errors': 0
        }
        job.completed_count = 1
        db.session.commit()
    
    def _process_jurisdiction_data(self, jurisdiction):
        """
        Process risk data for a single jurisdiction with error handling.
        
        Returns:
            Dict with 'data' and 'fresh_data' keys, or None if failed
        """
        try:
            jurisdiction_id = jurisdiction['id']
            jurisdiction_name = jurisdiction['name']
            
            # Use the real risk calculation system
            calculator = CARARiskCalculator(jurisdiction_id)
            risk_data = process_risk_data(jurisdiction_id)
            comprehensive_risk = calculator.calculate_comprehensive_risk(risk_data)
            
            # Create the data record (similar to GIS export utility)
            from utils.gis_export import CARAGISExporter
            exporter = CARAGISExporter()
            
            from utils.jurisdiction_mapping_code import jurisdiction_mapping
            county_name = jurisdiction_mapping.get(jurisdiction_id, 'Unknown')
            centroid = exporter._get_jurisdiction_centroid(county_name)
            
            # Extract domain scores from the correct location in comprehensive_risk
            domain_scores = comprehensive_risk.get('domain_scores', {})
            normalized_scores = comprehensive_risk.get('normalized_scores', {})
            
            # Get natural hazards sub-components from risk_data
            natural_hazards = risk_data.get('natural_hazards', {})
            
            # Extract domain scores with multiple fallback sources
            # Priority: domain_scores > normalized_scores > risk_data top-level > default
            
            # Natural hazards - fall back to calculating from sub-components
            natural_hazards_risk = domain_scores.get('natural_hazards', normalized_scores.get('natural_hazards'))
            if natural_hazards_risk is None:
                # Try to calculate from sub-components
                if natural_hazards:
                    hazard_values = [v for v in natural_hazards.values() if isinstance(v, (int, float))]
                    if hazard_values:
                        natural_hazards_risk = sum(hazard_values) / len(hazard_values)
                # Guaranteed fallback
                if natural_hazards_risk is None:
                    natural_hazards_risk = 0.3
            
            # Health metrics
            health_risk = domain_scores.get('health_metrics', normalized_scores.get('health_metrics'))
            if health_risk is None:
                # Try to get from health_metrics in risk_data
                health_metrics = risk_data.get('health_metrics', {})
                if isinstance(health_metrics, dict) and health_metrics:
                    health_values = [v for v in health_metrics.values() if isinstance(v, (int, float))]
                    if health_values:
                        health_risk = sum(health_values) / len(health_values)
                # Guaranteed fallback
                if health_risk is None:
                    health_risk = 0.3
            
            # Active shooter - try risk_data fallback
            active_shooter_risk = domain_scores.get('active_shooter', normalized_scores.get('active_shooter'))
            if active_shooter_risk is None:
                active_shooter_risk = risk_data.get('active_shooter_risk')
                if active_shooter_risk is None:
                    analysis = risk_data.get('active_shooter_analysis', {})
                    if isinstance(analysis, dict):
                        active_shooter_risk = analysis.get('risk_score')
                # Guaranteed fallback
                if active_shooter_risk is None:
                    active_shooter_risk = 0.25
            
            # Extreme heat - try risk_data fallback
            extreme_heat_risk = domain_scores.get('extreme_heat', normalized_scores.get('extreme_heat'))
            if extreme_heat_risk is None:
                extreme_heat_risk = risk_data.get('extreme_heat_risk')
                if extreme_heat_risk is None:
                    heat_data = risk_data.get('extreme_heat', {})
                    if isinstance(heat_data, dict):
                        extreme_heat_risk = heat_data.get('risk_score')
                # Guaranteed fallback
                if extreme_heat_risk is None:
                    extreme_heat_risk = 0.3
            
            # Cybersecurity - try risk_data fallback
            cybersecurity_risk = domain_scores.get('cybersecurity', normalized_scores.get('cybersecurity'))
            if cybersecurity_risk is None:
                cybersecurity_risk = risk_data.get('cybersecurity_risk')
                if cybersecurity_risk is None:
                    cyber_data = risk_data.get('cybersecurity', {})
                    if isinstance(cyber_data, dict):
                        cybersecurity_risk = cyber_data.get('risk_score')
                # Guaranteed fallback
                if cybersecurity_risk is None:
                    cybersecurity_risk = 0.25
            
            # Log which scores came from primary vs fallback sources
            fallback_used = []
            if 'natural_hazards' not in domain_scores:
                fallback_used.append('natural_hazards')
            if 'health_metrics' not in domain_scores:
                fallback_used.append('health_metrics')
            if 'active_shooter' not in domain_scores:
                fallback_used.append('active_shooter')
            if 'extreme_heat' not in domain_scores:
                fallback_used.append('extreme_heat')
            if 'cybersecurity' not in domain_scores:
                fallback_used.append('cybersecurity')
                
            if fallback_used:
                logger.debug(f"Used fallback sources for {jurisdiction_id}: {fallback_used}")
            
            # Calculate risk components from actual domain scores
            exposure = float(natural_hazards_risk)
            vulnerability = float(health_risk)
            resilience = max(0.0, 1.0 - float(cybersecurity_risk))
            health_impact_factor = risk_data.get('health_impact_factor', 1.0)
            
            from utils.risk_calculation import calculate_residual_risk
            residual_risk = calculate_residual_risk(
                exposure=exposure,
                vulnerability=vulnerability,
                resilience=resilience,
                health_impact_factor=health_impact_factor
            )
            
            # Get specific hazard risks from natural_hazards sub-components
            flood_risk = natural_hazards.get('flood', natural_hazards.get('riverine', 0.0))
            tornado_risk = natural_hazards.get('tornado', 0.0)
            winter_storm_risk = natural_hazards.get('winter_storm', natural_hazards.get('cold_wave', 0.0))
            thunderstorm_risk = natural_hazards.get('thunderstorm', natural_hazards.get('lightning', 0.0))
            
            # Air quality and utilities from risk_data if available
            air_quality_risk = risk_data.get('air_quality_risk', risk_data.get('air_quality', {}).get('risk_score', 0.0))
            utilities_risk = risk_data.get('utilities_risk', 0.0)
            
            data_record = {
                'jurisdiction_id': jurisdiction_id,
                'jurisdiction': jurisdiction_name,
                'county': county_name,
                'fips_code': exporter._get_county_fips_code(county_name),
                
                # Risk domain scores (from calculator's domain_scores)
                'natural_hazards_risk': float(natural_hazards_risk),
                'health_risk': float(health_risk),
                'active_shooter_risk': float(active_shooter_risk),
                'extreme_heat_risk': float(extreme_heat_risk),
                'air_quality_risk': float(air_quality_risk),
                'cybersecurity_risk': float(cybersecurity_risk),
                'utilities_risk': float(utilities_risk),
                
                # Specific hazard types (from natural_hazards sub-components)
                'flood_risk': float(flood_risk),
                'tornado_risk': float(tornado_risk),
                'winter_storm_risk': float(winter_storm_risk),
                'thunderstorm_risk': float(thunderstorm_risk),
                
                # Comprehensive risk metrics
                'exposure': float(exposure),
                'vulnerability': float(vulnerability),
                'resilience': float(resilience),
                'residual_risk': float(residual_risk),
                'total_risk_score': float(comprehensive_risk.get('total_risk_score', 0.0)),
                'health_impact_factor': float(health_impact_factor),
                
                # Geographic data
                'lat': centroid['lat'],
                'lon': centroid['lon'],
                
                # Metadata
                'calculation_timestamp': datetime.now().isoformat(),
                'framework_version': '2.3',
                'data_source': 'CARA Risk Assessment Platform'
            }
            
            logger.debug(f"Processed {jurisdiction_id}: total_risk={comprehensive_risk.get('total_risk_score')}, domains={domain_scores}")
            
            return {
                'data': data_record,
                'fresh_data': True  # Real-time calculation
            }
            
        except Exception as e:
            logger.error(f"Error processing jurisdiction {jurisdiction.get('id', 'unknown')}: {e}")
            logger.debug(f"Traceback: {traceback.format_exc()}")
            return None
    
    def _mark_job_failed(self, job: ExportJob, error_message: str):
        """Mark a job as failed with error message."""
        try:
            job.status = 'failed'
            job.error_message = error_message
            job.finished_at = datetime.utcnow()
            db.session.commit()
        except Exception as e:
            logger.error(f"Failed to mark job {job.id} as failed: {e}")


# Global worker instance
_export_worker = None

def start_export_worker(app):
    """Start the global export job worker."""
    global _export_worker
    
    if _export_worker and _export_worker.is_running:
        logger.warning("Export worker is already running")
        return
        
    _export_worker = ExportJobWorker(app)
    _export_worker.start_worker()

def stop_export_worker():
    """Stop the global export job worker."""
    global _export_worker
    
    if _export_worker:
        _export_worker.stop_worker()
        _export_worker = None

def get_export_worker() -> Optional[ExportJobWorker]:
    """Get the global export worker instance."""
    return _export_worker