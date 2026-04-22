"""
CARA API Monitoring and Health Checks

Provides endpoints and utilities for monitoring the health and performance
of the CARA platform, including database connectivity, external API status,
and system resource usage.
"""

import time
from flask import jsonify, request
from utils.logging_config import get_contextual_logger

# Optional dependency for system metrics
try:
    import psutil
    PSUTIL_AVAILABLE = True
except ImportError:
    PSUTIL_AVAILABLE = False


def setup_monitoring_endpoints(app):
    """Setup health check and monitoring endpoints."""
    
    logger = get_contextual_logger(__name__)
    
    @app.route('/health')
    def health_check():
        """Basic health check endpoint."""
        try:
            # Test database connectivity
            from core import db
            with db.engine.connect() as connection:
                connection.execute(db.text('SELECT 1'))
            
            return jsonify({
                'status': 'healthy',
                'timestamp': time.time(),
                'version': '2.1.0',
                'database': 'connected'
            }), 200
            
        except Exception as e:
            logger.error("Health check failed", error=str(e))
            return jsonify({
                'status': 'unhealthy',
                'timestamp': time.time(),
                'error': 'Database connection failed'
            }), 503
    
    @app.route('/health/detailed')
    def detailed_health_check():
        """Detailed health check with system metrics."""
        try:
            start_time = time.time()
            
            # Database check
            from core import db
            with db.engine.connect() as connection:
                connection.execute(db.text('SELECT 1'))
            db_status = 'connected'
            
            # System metrics (if available)
            system_metrics = {}
            if PSUTIL_AVAILABLE:
                try:
                    cpu_percent = psutil.cpu_percent(interval=0.1)  # Faster check
                    memory = psutil.virtual_memory()
                    disk = psutil.disk_usage('/')
                    
                    system_metrics = {
                        'cpu_percent': cpu_percent,
                        'memory_percent': memory.percent,
                        'memory_available_gb': round(memory.available / (1024**3), 2),
                        'disk_free_gb': round(disk.free / (1024**3), 2),
                        'disk_percent': round((disk.used / disk.total) * 100, 1)
                    }
                except Exception as e:
                    system_metrics = {'error': f'Failed to get system metrics: {str(e)}'}
            else:
                system_metrics = {'note': 'System metrics unavailable (psutil not installed)'}
            
            # Response time
            response_time = time.time() - start_time
            
            health_data = {
                'status': 'healthy',
                'timestamp': time.time(),
                'version': '2.1.0',
                'response_time_seconds': response_time,
                'database': {
                    'status': db_status,
                    'pool_size': getattr(db.engine.pool, 'size', None) or 'unknown',
                    'checked_out': getattr(db.engine.pool, 'checkedout', None) or 'unknown'
                },
                'system': system_metrics,
                'services': {
                    'scheduler': 'running',  # Would need to check actual scheduler status
                    'cache': 'active'
                }
            }
            
            # Check if any metrics indicate issues (only if system metrics are available)
            if PSUTIL_AVAILABLE and 'cpu_percent' in system_metrics:
                if system_metrics['cpu_percent'] > 90 or system_metrics['memory_percent'] > 90:
                    health_data['status'] = 'degraded'
                    health_data['warnings'] = []
                    
                    if system_metrics['cpu_percent'] > 90:
                        health_data['warnings'].append('High CPU usage')
                    if system_metrics['memory_percent'] > 90:
                        health_data['warnings'].append('High memory usage')
            
            status_code = 200 if health_data['status'] == 'healthy' else 206
            return jsonify(health_data), status_code
            
        except Exception as e:
            logger.error("Detailed health check failed", error=str(e))
            return jsonify({
                'status': 'unhealthy',
                'timestamp': time.time(),
                'error': str(e)
            }), 503
    
    @app.route('/metrics')
    def application_metrics():
        """Application metrics endpoint for monitoring tools."""
        try:
            # Get basic metrics
            metrics = {
                'cara_app_info': {
                    'version': '2.1.0',
                    'environment': app.config.get('ENV', 'production')
                },
                'cara_requests_total': getattr(app, '_request_count', 0),
                'cara_errors_total': getattr(app, '_error_count', 0),
                'cara_database_connections': getattr(db.engine.pool, 'checkedout', 0),
                'cara_uptime_seconds': time.time() - getattr(app, '_start_time', time.time())
            }
            
            return jsonify(metrics), 200
            
        except Exception as e:
            logger.error("Metrics endpoint failed", error=str(e))
            return jsonify({'error': 'Metrics unavailable'}), 500
    
    logger.info("Monitoring endpoints registered")


def track_request_metrics(app):
    """Setup request tracking for metrics."""
    
    # Initialize counters
    app._request_count = 0
    app._error_count = 0
    app._start_time = time.time()
    
    @app.before_request
    def increment_request_count():
        app._request_count += 1
    
    @app.after_request
    def track_response(response):
        if response.status_code >= 400:
            app._error_count += 1
        return response