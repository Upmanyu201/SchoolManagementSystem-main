from functools import wraps
from django.contrib.auth.decorators import login_required
from django.core.exceptions import PermissionDenied
from django.http import JsonResponse
from django.core.cache import cache
from django.utils import timezone
import time
import logging
import hashlib

logger = logging.getLogger('backup.security')

class RateLimiter:
    @staticmethod
    def get_client_identifier(request):
        if request.user.is_authenticated:
            return f"user_{request.user.id}"
        
        ip = request.META.get('HTTP_X_FORWARDED_FOR', '').split(',')[0] or request.META.get('REMOTE_ADDR', '')
        user_agent = request.META.get('HTTP_USER_AGENT', '')
        identifier = hashlib.md5(f"{ip}_{user_agent}".encode()).hexdigest()
        return f"anon_{identifier}"
    
    @staticmethod
    def is_rate_limited(request, operation, max_requests=5, window_minutes=60):
        client_id = RateLimiter.get_client_identifier(request)
        cache_key = f"rate_limit_{operation}_{client_id}"
        
        current_time = int(time.time())
        window_seconds = window_minutes * 60
        
        requests = cache.get(cache_key, [])
        requests = [req_time for req_time in requests if current_time - req_time < window_seconds]
        
        if len(requests) >= max_requests:
            logger.warning(f"Rate limit exceeded for {client_id} on operation {operation}")
            return True
        
        requests.append(current_time)
        cache.set(cache_key, requests, window_seconds)
        return False

def require_backup_permission(permission):
    def decorator(view_func):
        @wraps(view_func)
        @login_required
        def wrapper(request, *args, **kwargs):
            if not request.user.has_perm(permission):
                logger.warning(f"Permission denied for user {request.user} on {permission}")
                raise PermissionDenied("Insufficient permissions for backup operations")
            return view_func(request, *args, **kwargs)
        return wrapper
    return decorator

def rate_limit_backup_operations(max_requests=10, window_minutes=60):
    def decorator(view_func):
        @wraps(view_func)
        def wrapper(request, *args, **kwargs):
            operation = f"{view_func.__name__}"
            
            if RateLimiter.is_rate_limited(request, operation, max_requests, window_minutes):
                return JsonResponse({
                    'error': 'Rate limit exceeded',
                    'message': f'Maximum {max_requests} requests per {window_minutes} minutes allowed'
                }, status=429)
            
            return view_func(request, *args, **kwargs)
        return wrapper
    return decorator

def audit_backup_operation(operation_type):
    def decorator(view_func):
        @wraps(view_func)
        def wrapper(request, *args, **kwargs):
            start_time = time.time()
            
            logger.info(f"Backup operation started: {operation_type} by user {request.user} from IP {request.META.get('REMOTE_ADDR')}")
            
            try:
                result = view_func(request, *args, **kwargs)
                duration = time.time() - start_time
                logger.info(f"Backup operation completed: {operation_type} in {duration:.2f}s")
                return result
                
            except Exception as e:
                duration = time.time() - start_time
                logger.error(f"Backup operation failed: {operation_type} after {duration:.2f}s - Error: {str(e)}")
                raise
                
        return wrapper
    return decorator
