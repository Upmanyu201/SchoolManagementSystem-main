# core/middleware.py - Enhanced middleware for performance and security
from django.utils.deprecation import MiddlewareMixin
from django.http import JsonResponse
from django.core.cache import cache
from .security import SecurityEnhancements
import time
import logging

logger = logging.getLogger(__name__)

class PerformanceMiddleware(MiddlewareMixin):
    """Monitor and optimize performance"""
    
    def process_request(self, request):
        request._start_time = time.time()
        return None
    
    def process_response(self, request, response):
        if hasattr(request, '_start_time'):
            duration = time.time() - request._start_time
            
            # Log slow requests
            if duration > 2.0:  # 2 seconds threshold
                logger.warning(f"Slow request: {request.path} took {duration:.3f}s")
            
            # Add performance header
            response['X-Response-Time'] = f"{duration:.3f}s"
        
        return response

class SecurityMiddleware(MiddlewareMixin):
    """Enhanced security middleware"""
    
    def process_request(self, request):
        # Basic security headers
        if request.method == 'POST':
            # Log POST requests for audit - safely check user
            username = 'anonymous'
            if hasattr(request, 'user') and hasattr(request.user, 'username'):
                try:
                    username = request.user.username if request.user.is_authenticated else 'anonymous'
                except (AttributeError, TypeError):
                    username = 'anonymous'
            
            try:
                SecurityEnhancements.log_security_event(
                    'POST_REQUEST',
                    username,
                    f"Path: {request.path}"
                )
            except Exception:
                pass  # Fail silently for logging
        
        return None
    
    def process_response(self, request, response):
        # Add security headers
        response['X-Content-Type-Options'] = 'nosniff'
        response['X-Frame-Options'] = 'DENY'
        response['X-XSS-Protection'] = '1; mode=block'
        
        return response

class CacheMiddleware(MiddlewareMixin):
    """Smart caching middleware"""
    
    def process_request(self, request):
        # Cache GET requests for static data - safely check user
        if request.method == 'GET':
            # Check if user is authenticated safely
            is_authenticated = False
            if hasattr(request, 'user') and request.user:
                try:
                    is_authenticated = request.user.is_authenticated
                except AttributeError:
                    is_authenticated = False
            
            if not is_authenticated:
                cache_key = f"page_cache_{request.path}_{request.GET.urlencode()}"
                cached_response = cache.get(cache_key)
                
                if cached_response:
                    return cached_response
        
        return None