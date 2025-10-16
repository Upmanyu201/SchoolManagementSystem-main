# Security Middleware for School Management System
# Provides comprehensive security monitoring and protection

import logging
import time
from django.http import HttpResponseForbidden, JsonResponse
from django.core.cache import cache
from django.utils.deprecation import MiddlewareMixin
from django.contrib.auth.models import AnonymousUser
from .security_utils import SecurityLogger, get_client_ip, get_user_agent

logger = logging.getLogger(__name__)

class SecurityMonitoringMiddleware(MiddlewareMixin):
    """Middleware for security monitoring and protection"""
    
    def __init__(self, get_response):
        self.get_response = get_response
        super().__init__(get_response)
    
    def process_request(self, request):
        """Process incoming requests for security monitoring"""
        # Get client information
        request.client_ip = get_client_ip(request)
        request.user_agent = get_user_agent(request)
        request.start_time = time.time()
        
        # Check for suspicious patterns
        if self._is_suspicious_request(request):
            SecurityLogger.log_suspicious_activity(
                activity_type='SUSPICIOUS_REQUEST_PATTERN',
                user=request.user if hasattr(request, 'user') and not isinstance(request.user, AnonymousUser) else None,
                details={
                    'path': request.path,
                    'method': request.method,
                    'user_agent': request.user_agent[:200]
                },
                ip_address=request.client_ip
            )
        
        # Rate limiting for anonymous users
        if not hasattr(request, 'user') or isinstance(request.user, AnonymousUser):
            if not self._check_anonymous_rate_limit(request):
                return HttpResponseForbidden("Rate limit exceeded")
        
        return None
    
    def process_response(self, request, response):
        """Process responses for security monitoring"""
        # Log slow requests
        if hasattr(request, 'start_time'):
            duration = time.time() - request.start_time
            if duration > 5.0:  # Log requests taking more than 5 seconds
                logger.warning(f"Slow request: {request.path} took {duration:.2f}s")
        
        # Add security headers
        response = self._add_security_headers(response)
        
        # Log failed authentication attempts
        if response.status_code == 403:
            SecurityLogger.log_security_event(
                event_type='ACCESS_DENIED',
                severity='MEDIUM',
                user=request.user if hasattr(request, 'user') and not isinstance(request.user, AnonymousUser) else None,
                details={
                    'path': request.path,
                    'method': request.method
                },
                ip_address=getattr(request, 'client_ip', None)
            )
        
        return response
    
    def _is_suspicious_request(self, request):
        """Check for suspicious request patterns"""
        suspicious_patterns = [
            # SQL injection attempts
            'union select', 'drop table', 'insert into', 'delete from',
            # XSS attempts
            '<script', 'javascript:', 'onerror=', 'onload=',
            # Path traversal attempts
            '../', '..\\', '/etc/passwd', '/windows/system32',
            # Command injection attempts
            '; cat ', '| cat ', '&& cat ', '|| cat ',
        ]
        
        # Check URL path
        path_lower = request.path.lower()
        for pattern in suspicious_patterns:
            if pattern in path_lower:
                return True
        
        # Check query parameters
        for key, value in request.GET.items():
            value_lower = str(value).lower()
            for pattern in suspicious_patterns:
                if pattern in value_lower:
                    return True
        
        # Check for excessive parameter count (potential DoS)
        if len(request.GET) > 50:
            return True
        
        # Check for excessively long parameters
        for key, value in request.GET.items():
            if len(str(value)) > 1000:
                return True
        
        return False
    
    def _check_anonymous_rate_limit(self, request):
        """Rate limiting for anonymous users"""
        ip = getattr(request, 'client_ip', 'unknown')
        cache_key = f"anon_rate_limit_{ip}"
        
        # Get current count
        current_count = cache.get(cache_key, 0)
        
        # Allow 100 requests per hour for anonymous users
        if current_count >= 100:
            return False
        
        # Increment counter
        cache.set(cache_key, current_count + 1, 3600)  # 1 hour timeout
        
        return True
    
    def _add_security_headers(self, response):
        """Add security headers to response"""
        # Prevent clickjacking
        response['X-Frame-Options'] = 'DENY'
        
        # Prevent MIME type sniffing
        response['X-Content-Type-Options'] = 'nosniff'
        
        # XSS protection
        response['X-XSS-Protection'] = '1; mode=block'
        
        # Referrer policy
        response['Referrer-Policy'] = 'strict-origin-when-cross-origin'
        
        # Content Security Policy (basic)
        if not response.get('Content-Security-Policy'):
            response['Content-Security-Policy'] = (
                "default-src 'self'; "
                "script-src 'self' 'unsafe-inline' https://cdn.jsdelivr.net; "
                "style-src 'self' 'unsafe-inline' https://fonts.googleapis.com; "
                "font-src 'self' https://fonts.gstatic.com; "
                "img-src 'self' data: https:; "
                "connect-src 'self' wss: https:;"
            )
        
        return response

class AuthenticationLoggingMiddleware(MiddlewareMixin):
    """Middleware for logging authentication events"""
    
    def process_request(self, request):
        """Log authentication-related requests"""
        # Log login attempts
        if request.path in ['/login/', '/accounts/login/'] and request.method == 'POST':
            username = request.POST.get('username', 'unknown')
            SecurityLogger.log_user_action(
                user=request.user if hasattr(request, 'user') else None,
                action='LOGIN_ATTEMPT',
                details={'username': username},
                ip_address=getattr(request, 'client_ip', get_client_ip(request)),
                user_agent=getattr(request, 'user_agent', get_user_agent(request))
            )
        
        # Log logout attempts
        if request.path in ['/logout/', '/accounts/logout/']:
            SecurityLogger.log_user_action(
                user=request.user if hasattr(request, 'user') else None,
                action='LOGOUT_ATTEMPT',
                ip_address=getattr(request, 'client_ip', get_client_ip(request)),
                user_agent=getattr(request, 'user_agent', get_user_agent(request))
            )
        
        return None

class CSRFLoggingMiddleware(MiddlewareMixin):
    """Middleware for logging CSRF failures"""
    
    def process_view(self, request, view_func, view_args, view_kwargs):
        """Log CSRF token validation"""
        # This will be called before the view is executed
        return None
    
    def process_exception(self, request, exception):
        """Log CSRF failures"""
        if 'Forbidden (CSRF' in str(exception):
            SecurityLogger.log_security_event(
                event_type='CSRF_FAILURE',
                severity='HIGH',
                user=request.user if hasattr(request, 'user') and not isinstance(request.user, AnonymousUser) else None,
                details={
                    'path': request.path,
                    'method': request.method,
                    'referer': request.META.get('HTTP_REFERER', 'unknown')
                },
                ip_address=getattr(request, 'client_ip', get_client_ip(request))
            )
        
        return None

class FileUploadSecurityMiddleware(MiddlewareMixin):
    """Middleware for file upload security"""
    
    def process_request(self, request):
        """Validate file uploads"""
        if request.method == 'POST' and request.FILES:
            for field_name, uploaded_file in request.FILES.items():
                if not self._is_safe_file(uploaded_file):
                    SecurityLogger.log_security_event(
                        event_type='UNSAFE_FILE_UPLOAD',
                        severity='HIGH',
                        user=request.user if hasattr(request, 'user') and not isinstance(request.user, AnonymousUser) else None,
                        details={
                            'filename': uploaded_file.name,
                            'content_type': uploaded_file.content_type,
                            'size': uploaded_file.size
                        },
                        ip_address=getattr(request, 'client_ip', get_client_ip(request))
                    )
                    return HttpResponseForbidden("File upload not allowed")
        
        return None
    
    def _is_safe_file(self, uploaded_file):
        """Check if uploaded file is safe"""
        # Check file size (max 50MB)
        if uploaded_file.size > 50 * 1024 * 1024:
            return False
        
        # Check file extension
        allowed_extensions = [
            'jpg', 'jpeg', 'png', 'gif', 'pdf', 'doc', 'docx', 
            'xls', 'xlsx', 'csv', 'txt', 'zip'
        ]
        
        if uploaded_file.name:
            extension = uploaded_file.name.split('.')[-1].lower()
            if extension not in allowed_extensions:
                return False
        
        # Check content type
        safe_content_types = [
            'image/jpeg', 'image/png', 'image/gif',
            'application/pdf', 'application/msword',
            'application/vnd.openxmlformats-officedocument.wordprocessingml.document',
            'application/vnd.ms-excel',
            'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
            'text/csv', 'text/plain', 'application/zip'
        ]
        
        if uploaded_file.content_type not in safe_content_types:
            return False
        
        return True

class DatabaseQueryLoggingMiddleware(MiddlewareMixin):
    """Middleware for logging suspicious database queries"""
    
    def process_request(self, request):
        """Monitor for potential SQL injection attempts"""
        # This would integrate with Django's database logging
        # For now, we'll just set up the monitoring flag
        request._monitor_db_queries = True
        return None
    
    def process_response(self, request, response):
        """Log any suspicious database activity"""
        # This would analyze database queries made during the request
        # Implementation would depend on database logging configuration
        return response

# Utility function to enable all security middleware
def get_security_middleware():
    """Get list of all security middleware classes"""
    return [
        'core.security_middleware.SecurityMonitoringMiddleware',
        'core.security_middleware.AuthenticationLoggingMiddleware',
        'core.security_middleware.CSRFLoggingMiddleware',
        'core.security_middleware.FileUploadSecurityMiddleware',
    ]