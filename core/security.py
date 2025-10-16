# core/security.py - Security enhancements
from django.core.cache import cache
from django.http import JsonResponse
from django.utils.html import escape
from functools import wraps
import time
import logging

logger = logging.getLogger(__name__)

class SecurityEnhancements:
    @staticmethod
    def rate_limit(max_requests=60, window=60, key_func=None):
        """Rate limiting decorator"""
        def decorator(func):
            @wraps(func)
            def wrapper(request, *args, **kwargs):
                # Generate rate limit key
                if key_func:
                    key = key_func(request)
                else:
                    key = f"rate_limit_{request.META.get('REMOTE_ADDR', 'unknown')}"
                
                # Check current count
                current_count = cache.get(key, 0)
                
                if current_count >= max_requests:
                    return JsonResponse({
                        'error': 'Too many requests. Please try again later.',
                        'retry_after': window
                    }, status=429)
                
                # Increment counter
                cache.set(key, current_count + 1, window)
                
                return func(request, *args, **kwargs)
            return wrapper
        return decorator
    
    @staticmethod
    def sanitize_input(data):
        """Sanitize user input"""
        if isinstance(data, str):
            return escape(data.strip())
        elif isinstance(data, dict):
            return {k: SecurityEnhancements.sanitize_input(v) for k, v in data.items()}
        elif isinstance(data, list):
            return [SecurityEnhancements.sanitize_input(item) for item in data]
        return data
    
    @staticmethod
    def log_security_event(event_type, user, details):
        """Log security events"""
        logger.warning(f"Security Event: {event_type} - User: {user} - Details: {details}")
    
    @staticmethod
    def validate_file_upload(file):
        """Validate file uploads"""
        allowed_extensions = ['.jpg', '.jpeg', '.png', '.pdf', '.doc', '.docx']
        max_size = 5 * 1024 * 1024  # 5MB
        
        if file.size > max_size:
            raise ValueError("File too large. Maximum size is 5MB.")
        
        if not any(file.name.lower().endswith(ext) for ext in allowed_extensions):
            raise ValueError("File type not allowed.")
        
        return True

# Quick decorators
rate_limit_api = SecurityEnhancements.rate_limit(100, 3600)  # 100 requests per hour
rate_limit_strict = SecurityEnhancements.rate_limit(10, 60)  # 10 requests per minute