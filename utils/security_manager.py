"""
CARA Security Manager

Comprehensive security features for the CARA platform including:
- API key authentication for all API endpoints
- Rate limiting with Flask-Limiter
- Security headers (CSRF, XSS, etc.)
- Request validation and sanitization
- Security event logging
"""

import os
import secrets
import hashlib
import time
from functools import wraps
from flask import request, jsonify, g, current_app
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
from utils.logging_config import get_contextual_logger
from utils.error_handlers import log_security_event


class SecurityManager:
    """Central security management for CARA."""
    
    def __init__(self):
        self.logger = get_contextual_logger(__name__)
        self.limiter = None
        
    def initialize_security(self, app):
        """Initialize all security features for the Flask app."""
        
        # Initialize rate limiting
        self._setup_rate_limiting(app)
        
        # Setup security headers
        self._setup_security_headers(app)
        
        # Initialize API key management
        self._setup_api_key_management(app)
        
        self.logger.info("Security manager initialized with rate limiting and API authentication")
    
    def _setup_rate_limiting(self, app):
        """Configure Flask-Limiter for rate limiting."""
        
        # Use Redis if available, otherwise use in-memory storage
        storage_uri = os.environ.get('REDIS_URL', 'memory://')
        
        self.limiter = Limiter(
            app=app,
            key_func=get_remote_address,
            default_limits=["1000 per hour", "100 per minute"],
            storage_uri=storage_uri,
            headers_enabled=True,
            swallow_errors=os.getenv("FLASK_ENV") != "development",
            strategy="fixed-window"
        )
        
        # Custom rate limiting for API endpoints
        @self.limiter.limit("60 per minute")
        @self.limiter.limit("300 per hour")
        def api_rate_limit():
            """Stricter rate limits for API endpoints."""
            pass
        
        # Apply API rate limits to all /api/* routes
        @app.before_request
        def apply_api_rate_limits():
            if request.path.startswith('/api/'):
                if request.path in ('/api/health', '/health', '/health/detailed', '/metrics'):
                    return None

                try:
                    api_rate_limit()
                except Exception as e:
                    # Rate limit exceeded
                    self.logger.warning("API rate limit exceeded",
                                       endpoint=request.endpoint,
                                       remote_addr=request.remote_addr,
                                       user_agent=request.headers.get('User-Agent', ''))
                    
                    log_security_event('rate_limit_exceeded', {
                        'endpoint': request.endpoint,
                        'limit_type': 'api'
                    })
                    
                    return jsonify({
                        'error': 'Rate limit exceeded',
                        'message': 'Too many API requests. Please wait before trying again.',
                        'status_code': 429
                    }), 429
        
        self.logger.info("Rate limiting configured", storage=storage_uri)
    
    def _setup_security_headers(self, app):
        """Add security headers to all responses."""
        
        @app.after_request
        def add_security_headers(response):
            """Add comprehensive security headers."""
            
            # Content Security Policy
            csp_policy = (
                "default-src 'self'; "
                "script-src 'self' 'unsafe-inline' https://cdn.jsdelivr.net https://cdnjs.cloudflare.com; "
                "style-src 'self' 'unsafe-inline' https://cdn.jsdelivr.net https://cdnjs.cloudflare.com; "
                "img-src 'self' data: https:; "
                "font-src 'self' https://cdn.jsdelivr.net https://cdnjs.cloudflare.com; "
                "connect-src 'self' https://cdn.jsdelivr.net https://cdnjs.cloudflare.com; "
                "frame-ancestors 'self' https://*.replit.dev https://*.replit.app https://*.repl.co; "
                "base-uri 'self'; "
                "object-src 'none';"
            )
            response.headers['Content-Security-Policy'] = csp_policy
            
            # Additional security headers
            response.headers['X-Content-Type-Options'] = 'nosniff'
            response.headers['X-XSS-Protection'] = '1; mode=block'
            response.headers['Strict-Transport-Security'] = 'max-age=31536000; includeSubDomains'
            response.headers['Referrer-Policy'] = 'strict-origin-when-cross-origin'
            response.headers['Permissions-Policy'] = 'geolocation=(), microphone=(), camera=()'
            
            # Remove server information
            response.headers.pop('Server', None)
            
            return response
        
        self.logger.info("Security headers configured")
    
    def _setup_api_key_management(self, app):
        """Setup API key authentication system."""
        
        # Load API keys from environment
        self._load_api_keys()
        
        self.logger.info("API key management initialized")
    
    def _load_api_keys(self):
        """Load and validate API keys from environment variables."""
        
        # Primary API key for CARA system
        self.primary_api_key = os.environ.get('CARA_API_KEY')
        
        # Secondary API keys for different access levels
        self.readonly_api_key = os.environ.get('CARA_READONLY_API_KEY')
        self.admin_api_key = os.environ.get('CARA_ADMIN_API_KEY')
        
        # Wisconsin public health authorized keys
        self.wph_api_keys = []
        for i in range(1, 11):  # Support up to 10 Wisconsin public health API keys
            key = os.environ.get(f'WPH_API_KEY_{i}')
            if key:
                self.wph_api_keys.append(key)
        
        # Log API key status without exposing the keys
        key_count = sum([
            1 if self.primary_api_key else 0,
            1 if self.readonly_api_key else 0,
            1 if self.admin_api_key else 0,
            len(self.wph_api_keys)
        ])
        
        self.logger.info(f"Loaded {key_count} API keys for authentication")
    
    def generate_api_key(self, key_type='standard'):
        """Generate a new secure API key."""
        
        # Generate a random key with timestamp and type identifier
        timestamp = str(int(time.time()))
        random_part = secrets.token_urlsafe(32)
        
        # Create key with identifiable prefix
        prefix_map = {
            'admin': 'cara_admin',
            'readonly': 'cara_ro',
            'wph': 'cara_wph',
            'standard': 'cara_api'
        }
        
        prefix = prefix_map.get(key_type, 'cara_api')
        api_key = f"{prefix}_{timestamp}_{random_part}"
        
        # Create hash for validation
        key_hash = hashlib.sha256(api_key.encode()).hexdigest()
        
        self.logger.info(f"Generated new API key", key_type=key_type, key_hash=key_hash[:16])
        
        return api_key
    
    def validate_api_key(self, provided_key, required_level='readonly'):
        """
        Validate API key and determine access level.
        
        Args:
            provided_key: API key from request
            required_level: Minimum required access level
            
        Returns:
            dict: Validation result with access level and permissions
        """
        
        if not provided_key:
            return {
                'valid': False,
                'error': 'API key required',
                'access_level': None
            }
        
        # Check against different key types
        access_levels = {
            'admin': ['admin', 'write', 'readonly'],
            'write': ['write', 'readonly'],
            'readonly': ['readonly']
        }
        
        # Validate against known keys
        if provided_key == self.admin_api_key:
            user_level = 'admin'
        elif provided_key == self.primary_api_key:
            user_level = 'write'
        elif provided_key == self.readonly_api_key or provided_key in self.wph_api_keys:
            user_level = 'readonly'
        else:
            # Log failed authentication attempt
            key_hash = hashlib.sha256(provided_key.encode()).hexdigest()
            self.logger.warning("Invalid API key attempted",
                               key_hash=key_hash[:16],
                               remote_addr=request.remote_addr)
            
            log_security_event('invalid_api_key', {
                'key_hash': key_hash[:16],
                'endpoint': request.endpoint
            })
            
            return {
                'valid': False,
                'error': 'Invalid API key',
                'access_level': None
            }
        
        # Check if user level meets required level
        if required_level not in access_levels.get(user_level, []):
            return {
                'valid': False,
                'error': f'Insufficient permissions. Required: {required_level}, Available: {user_level}',
                'access_level': user_level
            }
        
        return {
            'valid': True,
            'access_level': user_level,
            'permissions': access_levels[user_level]
        }


# Global security manager instance
security_manager = SecurityManager()


def require_api_key(required_level='readonly'):
    """
    Decorator to require API key authentication for routes.
    
    Usage:
        @require_api_key('admin')  # Requires admin access
        @require_api_key('write')  # Requires write access
        @require_api_key()         # Requires readonly access (default)
    """
    
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            # Extract API key from headers or query parameters
            api_key = (
                request.headers.get('X-API-Key') or
                request.headers.get('Authorization', '').replace('Bearer ', '')
            )
            
            # Validate the API key
            validation_result = security_manager.validate_api_key(api_key, required_level)
            
            if not validation_result['valid']:
                return jsonify({
                    'success': False,
                    'error': validation_result['error']
                }), 401
            
            # Store access level in Flask context for use in route
            g.api_access_level = validation_result['access_level']
            g.api_permissions = validation_result['permissions']
            
            # Log successful API access
            logger = get_contextual_logger('api_access')
            logger.info("API access granted",
                       endpoint=request.endpoint,
                       access_level=validation_result['access_level'],
                       method=request.method)
            
            return f(*args, **kwargs)
        
        return decorated_function
    return decorator


def setup_security(app):
    """Initialize security features for the CARA application."""
    
    # Initialize the security manager
    security_manager.initialize_security(app)
    
    # Add security context to all requests
    @app.before_request
    def security_context():
        """Add security context to request."""
        g.security_manager = security_manager
        g.request_start_time = time.time()
    
    return security_manager