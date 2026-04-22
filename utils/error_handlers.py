"""
CARA Production Error Handlers

Comprehensive error handling for the CARA platform including:
- HTML error pages for browser requests
- JSON error responses for API requests
- Detailed error logging
- User-friendly error messages
- Security considerations (no sensitive data exposure)
"""

import traceback
from flask import request, jsonify, render_template, current_app
from utils.logging_config import get_contextual_logger


def register_comprehensive_error_handlers(app):
    """
    Register comprehensive error handlers for all error types.
    
    Replaces the basic error handlers with production-ready ones that:
    - Log detailed error information
    - Return appropriate responses based on request type (HTML vs JSON)
    - Protect sensitive information
    - Provide helpful user guidance
    """
    
    logger = get_contextual_logger(__name__)
    
    @app.errorhandler(400)
    def bad_request_error(error):
        """Handle 400 Bad Request errors."""
        logger.warning("Bad request error",
                      error_code=400,
                      error_message=str(error),
                      url=request.url,
                      method=request.method)
        
        if is_api_request():
            return jsonify({
                'success': False,
                'error': 'The request could not be understood by the server'
            }), 400
        
        return render_template('errors/400.html'), 400
    
    @app.errorhandler(401)
    def unauthorized_error(error):
        """Handle 401 Unauthorized errors."""
        logger.warning("Unauthorized access attempt",
                      error_code=401,
                      error_message=str(error),
                      url=request.url,
                      method=request.method,
                      user_agent=request.headers.get('User-Agent', ''))
        
        if is_api_request():
            return jsonify({
                'success': False,
                'error': 'Authentication required to access this resource'
            }), 401
        
        return render_template('errors/401.html'), 401
    
    @app.errorhandler(403)
    def forbidden_error(error):
        """Handle 403 Forbidden errors."""
        logger.warning("Forbidden access attempt",
                      error_code=403,
                      error_message=str(error),
                      url=request.url,
                      method=request.method)
        
        if is_api_request():
            return jsonify({
                'success': False,
                'error': 'You do not have permission to access this resource'
            }), 403
        
        return render_template('errors/403.html'), 403
    
    @app.errorhandler(404)
    def not_found_error(error):
        """Handle 404 Not Found errors with enhanced logging."""
        logger.warning("Page not found",
                      error_code=404,
                      error_message=str(error),
                      url=request.url,
                      method=request.method,
                      referrer=request.referrer)
        
        if is_api_request():
            return jsonify({
                'success': False,
                'error': 'The requested resource could not be found'
            }), 404
        
        return render_template('errors/404.html'), 404
    
    @app.errorhandler(429)
    def rate_limit_error(error):
        """Handle 429 Too Many Requests errors."""
        logger.warning("Rate limit exceeded",
                      error_code=429,
                      error_message=str(error),
                      url=request.url,
                      method=request.method,
                      remote_addr=request.remote_addr)
        
        if is_api_request():
            return jsonify({
                'success': False,
                'error': 'Rate limit exceeded. Please try again later.'
            }), 429
        
        return render_template('errors/429.html'), 429
    
    @app.errorhandler(500)
    def internal_server_error(error):
        """Handle 500 Internal Server Error with comprehensive logging."""
        
        # Log the full error details
        logger.error("Internal server error",
                    error_code=500,
                    error_message=str(error),
                    url=request.url,
                    method=request.method,
                    traceback=traceback.format_exc(),
                    request_data=get_safe_request_data())
        
        if is_api_request():
            # For API requests, return JSON with minimal information
            response_data = {
                'success': False,
                'error': 'An unexpected error occurred. Please try again later.'
            }
            
            # Add error ID for tracking in development/debugging
            if current_app.debug:
                response_data['error_id'] = getattr(error, 'error_id', 'unknown')
                
            return jsonify(response_data), 500
        
        return render_template('errors/500.html'), 500
    
    @app.errorhandler(502)
    def bad_gateway_error(error):
        """Handle 502 Bad Gateway errors."""
        logger.error("Bad gateway error",
                    error_code=502,
                    error_message=str(error),
                    url=request.url,
                    method=request.method)
        
        if is_api_request():
            return jsonify({
                'success': False,
                'error': 'The server received an invalid response from upstream'
            }), 502
        
        return render_template('errors/502.html'), 502
    
    @app.errorhandler(503)
    def service_unavailable_error(error):
        """Handle 503 Service Unavailable errors."""
        logger.error("Service unavailable",
                    error_code=503,
                    error_message=str(error),
                    url=request.url,
                    method=request.method)
        
        if is_api_request():
            return jsonify({
                'success': False,
                'error': 'The service is temporarily unavailable. Please try again later.'
            }), 503
        
        return render_template('errors/503.html'), 503
    
    @app.errorhandler(Exception)
    def handle_unexpected_error(error):
        """Handle any unexpected exceptions not caught by specific handlers."""
        
        logger.critical("Unexpected exception",
                       error_type=type(error).__name__,
                       error_message=str(error),
                       url=request.url,
                       method=request.method,
                       traceback=traceback.format_exc(),
                       request_data=get_safe_request_data())
        
        if is_api_request():
            return jsonify({
                'success': False,
                'error': 'An unexpected error occurred. Please contact support if this persists.'
            }), 500
        
        return render_template('errors/500.html'), 500
    
    logger.info("Comprehensive error handlers registered")


def is_api_request():
    """
    Determine if the current request is an API request based on:
    - Accept header preferring JSON
    - URL path starting with /api/
    - Content-Type being application/json
    """
    return (
        request.path.startswith('/api/') or
        'application/json' in request.headers.get('Accept', '') or
        request.headers.get('Content-Type', '').startswith('application/json')
    )


def get_safe_request_data():
    """
    Get request data for logging while excluding sensitive information.
    
    Returns a dictionary with safe request information for logging purposes.
    Excludes passwords, tokens, and other sensitive data.
    """
    safe_data = {
        'method': request.method,
        'url': request.url,
        'remote_addr': request.remote_addr,
        'user_agent': request.headers.get('User-Agent', ''),
        'referrer': request.referrer
    }
    
    # Include form data but exclude sensitive fields
    if request.form:
        safe_form_data = {}
        sensitive_fields = ['password', 'token', 'secret', 'key', 'api_key']
        
        for key, value in request.form.items():
            if any(sensitive in key.lower() for sensitive in sensitive_fields):
                safe_form_data[key] = '[REDACTED]'
            else:
                safe_form_data[key] = value
                
        safe_data['form_data'] = safe_form_data
    
    # Include query parameters
    if request.args:
        safe_data['query_params'] = dict(request.args)
    
    return safe_data


def setup_api_error_handlers(app):
    """Setup additional error handlers specifically for API endpoints."""
    
    logger = get_contextual_logger(__name__)
    
    @app.errorhandler(ValueError)
    def handle_value_error(error):
        """Handle ValueError exceptions in API context."""
        if is_api_request():
            logger.warning("API ValueError",
                          error_message=str(error),
                          url=request.url,
                          method=request.method)
            
            return jsonify({
                'success': False,
                'error': 'Invalid input value provided'
            }), 400
        
        # Let other handlers deal with non-API requests
        raise error
    
    @app.errorhandler(KeyError)
    def handle_key_error(error):
        """Handle KeyError exceptions in API context."""
        if is_api_request():
            logger.warning("API KeyError",
                          error_message=str(error),
                          url=request.url,
                          method=request.method)
            
            return jsonify({
                'success': False,
                'error': f'Required field missing: {str(error)}'
            }), 400
        
        # Let other handlers deal with non-API requests
        raise error
    
    logger.info("API error handlers registered")


def log_security_event(event_type, details=None):
    """Log security-related events for monitoring and analysis."""
    
    logger = get_contextual_logger('security')
    
    security_data = {
        'event_type': event_type,
        'ip_address': request.remote_addr,
        'user_agent': request.headers.get('User-Agent', ''),
        'url': request.url,
        'method': request.method,
        'timestamp': request.environ.get('REQUEST_TIME', 'unknown')
    }
    
    if details:
        security_data.update(details)
    
    logger.warning("Security event detected", **security_data)