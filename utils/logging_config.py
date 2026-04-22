"""
CARA Production Logging Configuration

This module provides comprehensive logging setup for the CARA platform including:
- File-based logging with rotation
- Structured error logging
- Performance monitoring
- Optional external service integration (Sentry)
- Request tracking and audit trails
"""

import os
import logging
import logging.handlers
from datetime import datetime
from flask import request, g
import json


class JSONFormatter(logging.Formatter):
    """Custom JSON formatter for structured logging."""
    
    def format(self, record):
        """Format log record as JSON for better parsing and analysis."""
        log_data = {
            'timestamp': datetime.utcnow().isoformat(),
            'level': record.levelname,
            'logger': record.name,
            'message': record.getMessage(),
            'module': record.module,
            'function': record.funcName,
            'line': record.lineno
        }
        
        # Add request context if available
        try:
            from flask import g, request
            
            if hasattr(g, 'request_id'):
                log_data['request_id'] = g.request_id
                
            if request:
                log_data['request'] = {
                    'method': request.method,
                    'url': request.url,
                    'user_agent': request.headers.get('User-Agent', ''),
                    'remote_addr': request.remote_addr
                }
        except RuntimeError:
            # Working outside of application context - skip request context
            pass
            
        # Add exception information if present
        if record.exc_info:
            log_data['exception'] = {
                'type': record.exc_info[0].__name__,
                'message': str(record.exc_info[1]),
                'traceback': self.formatException(record.exc_info)
            }
            
        # Add any extra fields
        for key, value in record.__dict__.items():
            if key not in ['name', 'msg', 'args', 'levelname', 'levelno', 
                          'pathname', 'filename', 'module', 'lineno', 
                          'funcName', 'created', 'msecs', 'relativeCreated',
                          'thread', 'threadName', 'processName', 'process',
                          'getMessage', 'exc_info', 'exc_text', 'stack_info']:
                log_data[key] = value
                
        return json.dumps(log_data)


class ContextualLogger:
    """Logger that automatically includes contextual information."""
    
    def __init__(self, name):
        self.logger = logging.getLogger(name)
        
    def log_with_context(self, level, message, **kwargs):
        """Log message with automatic context addition."""
        extra = kwargs.copy()
        
        # Only add Flask context if we're in a request context
        try:
            from flask import g
            
            # Add jurisdiction context if available
            if hasattr(g, 'jurisdiction_id'):
                extra['jurisdiction_id'] = g.jurisdiction_id
                extra['jurisdiction_name'] = getattr(g, 'jurisdiction_name', '')
                
            # Add user context if available
            if hasattr(g, 'user_id'):
                extra['user_id'] = g.user_id
                
            # Add performance metrics if available
            if hasattr(g, 'start_time'):
                extra['request_duration'] = (datetime.utcnow() - g.start_time).total_seconds()
                
        except RuntimeError:
            # Working outside of application context - skip Flask-specific context
            pass
            
        self.logger.log(level, message, extra=extra)
        
    def info(self, message, **kwargs):
        self.log_with_context(logging.INFO, message, **kwargs)
        
    def warning(self, message, **kwargs):
        self.log_with_context(logging.WARNING, message, **kwargs)
        
    def error(self, message, **kwargs):
        self.log_with_context(logging.ERROR, message, **kwargs)
        
    def critical(self, message, **kwargs):
        self.log_with_context(logging.CRITICAL, message, **kwargs)
        
    def debug(self, message, **kwargs):
        self.log_with_context(logging.DEBUG, message, **kwargs)


def setup_production_logging(app):
    """
    Configure comprehensive production logging for CARA.
    
    Sets up:
    - File logging with rotation
    - Structured JSON logging
    - Error-specific logging
    - Performance logging
    - Request tracking
    """
    
    # Ensure logs directory exists
    log_dir = os.path.join(os.getcwd(), 'logs')
    os.makedirs(log_dir, exist_ok=True)
    
    # Configure root logger
    root_logger = logging.getLogger()
    root_logger.setLevel(logging.INFO)
    
    # Clear existing handlers
    root_logger.handlers.clear()
    
    # 1. Main application log with rotation
    app_log_file = os.path.join(log_dir, 'cara_app.log')
    app_handler = logging.handlers.RotatingFileHandler(
        app_log_file,
        maxBytes=10 * 1024 * 1024,  # 10MB
        backupCount=10
    )
    app_handler.setLevel(logging.INFO)
    app_handler.setFormatter(JSONFormatter())
    
    # 2. Error-specific log
    error_log_file = os.path.join(log_dir, 'cara_errors.log')
    error_handler = logging.handlers.RotatingFileHandler(
        error_log_file,
        maxBytes=10 * 1024 * 1024,  # 10MB
        backupCount=5
    )
    error_handler.setLevel(logging.ERROR)
    error_handler.setFormatter(JSONFormatter())
    
    # 3. Console handler for development
    console_handler = logging.StreamHandler()
    console_handler.setLevel(logging.WARNING)
    console_formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    console_handler.setFormatter(console_formatter)
    
    # Add handlers to root logger
    root_logger.addHandler(app_handler)
    root_logger.addHandler(error_handler)
    
    # Add console handler only in development
    if app.debug or os.environ.get('FLASK_ENV') == 'development':
        root_logger.addHandler(console_handler)
    
    # Configure specific loggers
    configure_logger_levels()
    
    # Log configuration completion
    logger = ContextualLogger(__name__)
    logger.info("Production logging configured", 
                log_files=[app_log_file, error_log_file],
                log_level=logging.getLevelName(root_logger.level))


def configure_logger_levels():
    """Configure specific logger levels to reduce noise."""
    
    # Reduce noise from third-party libraries
    logging.getLogger('urllib3').setLevel(logging.WARNING)
    logging.getLogger('requests').setLevel(logging.WARNING)
    logging.getLogger('werkzeug').setLevel(logging.WARNING)
    
    # Set appropriate levels for CARA modules
    logging.getLogger('utils').setLevel(logging.INFO)
    logging.getLogger('app').setLevel(logging.INFO)
    logging.getLogger('core').setLevel(logging.INFO)


def setup_sentry_integration(app):
    """
    Setup optional Sentry integration for external error monitoring.
    
    Only initializes if SENTRY_DSN environment variable is provided.
    """
    sentry_dsn = os.environ.get('SENTRY_DSN')
    
    if sentry_dsn:
        try:
            import sentry_sdk
            from sentry_sdk.integrations.flask import FlaskIntegration
            from sentry_sdk.integrations.logging import LoggingIntegration
            
            # Configure logging integration
            sentry_logging = LoggingIntegration(
                level=logging.INFO,        # Capture info and above as breadcrumbs
                event_level=logging.ERROR  # Send errors as events
            )
            
            sentry_sdk.init(
                dsn=sentry_dsn,
                integrations=[
                    FlaskIntegration(transaction_style='endpoint'),
                    sentry_logging
                ],
                traces_sample_rate=0.1,  # Capture 10% of transactions for performance monitoring
                environment=os.environ.get('FLASK_ENV', 'production'),
                release=os.environ.get('CARA_VERSION', '2.1.0')
            )
            
            logger = ContextualLogger(__name__)
            logger.info("Sentry integration initialized", sentry_dsn=sentry_dsn[:20] + "...")
            
        except ImportError:
            logger = ContextualLogger(__name__)
            logger.warning("Sentry SDK not installed but SENTRY_DSN provided")
    else:
        logger = ContextualLogger(__name__)
        logger.info("Sentry integration disabled (no SENTRY_DSN provided)")


def log_performance_metrics(app):
    """Setup request performance logging."""
    
    @app.before_request
    def before_request():
        g.start_time = datetime.utcnow()
        g.request_id = f"{datetime.utcnow().timestamp():.6f}"
        
    @app.after_request
    def after_request(response):
        if hasattr(g, 'start_time'):
            duration = (datetime.utcnow() - g.start_time).total_seconds()
            
            logger = ContextualLogger('performance')
            logger.info("Request completed",
                       method=request.method,
                       url=request.url,
                       status_code=response.status_code,
                       duration_seconds=duration,
                       content_length=response.content_length)
                       
        return response


def get_contextual_logger(name):
    """Get a contextual logger instance for a specific module."""
    return ContextualLogger(name)