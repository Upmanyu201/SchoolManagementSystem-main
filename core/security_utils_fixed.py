"""
Comprehensive Security Utilities for School Management System
Fixes for CWE-22, CWE-79/80, CWE-89, CWE-862 and other security vulnerabilities
"""

import os
import re
import html
import logging
import time
from decimal import Decimal, InvalidOperation
from typing import Dict, Any, Optional, List
from urllib.parse import urlparse
from django.core.exceptions import ValidationError, PermissionDenied
from django.core.cache import cache
from django.conf import settings
from django.utils.html import escape, strip_tags
from django.http import JsonResponse
# import bleach  # Optional dependency

logger = logging.getLogger(__name__)

class SecurityUtils:
    """Comprehensive security utilities with proper vulnerability fixes"""
    
    # XSS Prevention
    ALLOWED_HTML_TAGS = ['b', 'i', 'u', 'em', 'strong', 'p', 'br']
    ALLOWED_HTML_ATTRIBUTES = {}
    
    # Path Traversal Prevention
    DANGEROUS_PATH_PATTERNS = [
        r'\.\.[\\/]',  # Directory traversal
        r'^[\\/]',     # Absolute paths
        r'[a-zA-Z]:[\\\/]',  # Windows drive letters
        r'~[\\/]',     # Home directory
        r'\$\{.*\}',   # Variable expansion
    ]
    
    # SQL Injection Prevention
    SQL_INJECTION_PATTERNS = [
        r"'.*--",
        r'".*--',
        r"';.*",
        r'";.*',
        r"'.*OR.*'.*'",
        r'".*OR.*".*"',
        r"'.*UNION.*",
        r'".*UNION.*',
        r"'.*DROP.*",
        r'".*DROP.*',
        r"'.*INSERT.*",
        r'".*INSERT.*',
        r"'.*DELETE.*",
        r'".*DELETE.*',
        r"'.*UPDATE.*",
        r'".*UPDATE.*',
        r"'.*SELECT.*",
        r'".*SELECT.*',
    ]
    
    @classmethod
    def sanitize_input(cls, input_str: str, allow_html: bool = False) -> str:
        """
        Comprehensive input sanitization to prevent XSS attacks
        Fixes CWE-79/80: Cross-site Scripting
        """
        if not isinstance(input_str, str):
            input_str = str(input_str)
        
        # Remove null bytes and control characters
        input_str = re.sub(r'[\x00-\x08\x0B\x0C\x0E-\x1F\x7F]', '', input_str)
        
        if allow_html:
            # Basic HTML sanitization without bleach
            input_str = strip_tags(input_str)
            input_str = html.escape(input_str, quote=True)
        else:
            # Complete HTML escaping
            input_str = html.escape(input_str, quote=True)
            
        # Remove dangerous JavaScript patterns
        js_patterns = [
            r'javascript:',
            r'vbscript:',
            r'data:',
            r'on\w+\s*=',  # Event handlers
            r'<script[^>]*>.*?</script>',
            r'<iframe[^>]*>.*?</iframe>',
            r'<object[^>]*>.*?</object>',
            r'<embed[^>]*>.*?</embed>',
        ]
        
        for pattern in js_patterns:
            input_str = re.sub(pattern, '', input_str, flags=re.IGNORECASE | re.DOTALL)
        
        return input_str.strip()
    
    @classmethod
    def validate_file_path(cls, file_path: str, allowed_dirs: Optional[List[str]] = None) -> str:
        """
        Validate file paths to prevent path traversal attacks
        Fixes CWE-22: Path Traversal
        """
        if not file_path:
            raise ValidationError("File path cannot be empty")
        
        # Normalize path
        normalized_path = os.path.normpath(file_path)
        
        # Check for dangerous patterns
        for pattern in cls.DANGEROUS_PATH_PATTERNS:
            if re.search(pattern, normalized_path, re.IGNORECASE):
                logger.warning(f"Dangerous path pattern detected: {file_path}")
                raise ValidationError("Invalid file path detected")
        
        # Ensure path is within allowed directories
        if allowed_dirs:
            abs_path = os.path.abspath(normalized_path)
            allowed = False
            for allowed_dir in allowed_dirs:
                allowed_abs = os.path.abspath(allowed_dir)
                if abs_path.startswith(allowed_abs):
                    allowed = True
                    break
            
            if not allowed:
                logger.warning(f"File path outside allowed directories: {file_path}")
                raise ValidationError("File path not in allowed directory")
        
        return normalized_path
    
    @classmethod
    def validate_search_input(cls, search_term: str) -> str:
        """
        Validate search input to prevent SQL injection
        Fixes CWE-89: SQL Injection
        """
        if not search_term:
            return ""
        
        # Check for SQL injection patterns
        for pattern in cls.SQL_INJECTION_PATTERNS:
            if re.search(pattern, search_term, re.IGNORECASE):
                logger.warning(f"SQL injection attempt detected: {search_term}")
                raise ValidationError("Invalid search term")
        
        # Sanitize and limit length
        sanitized = cls.sanitize_input(search_term)
        if len(sanitized) > 100:  # Reasonable search term limit
            raise ValidationError("Search term too long")
        
        return sanitized
    
    @classmethod
    def validate_amount(cls, amount: Any) -> Decimal:
        """
        Validate monetary amounts with proper type checking
        """
        try:
            if isinstance(amount, str):
                # Check for non-numeric strings first
                if not re.match(r'^-?\d*\.?\d*$', amount.strip()):
                    raise ValidationError("Invalid amount format")
                # Remove any non-numeric characters except decimal point
                amount = re.sub(r'[^\d.-]', '', amount)
            
            decimal_amount = Decimal(str(amount))
            
            if decimal_amount < 0:
                raise ValidationError("Amount cannot be negative")
            
            if decimal_amount > Decimal('999999.99'):
                raise ValidationError("Amount too large")
            
            # Check for reasonable decimal places
            if decimal_amount.as_tuple().exponent < -2:
                raise ValidationError("Too many decimal places")
            
            return decimal_amount
            
        except (InvalidOperation, ValueError, TypeError):
            raise ValidationError("Invalid amount format")
    
    @classmethod
    def check_authorization(cls, user, permission: str, obj=None) -> bool:
        """
        Comprehensive authorization checking
        Fixes CWE-862: Missing Authorization
        """
        if not user or not user.is_authenticated:
            return False
        
        # Check basic permission
        if not user.has_perm(permission):
            return False
        
        # Check object-level permissions if provided
        if obj and hasattr(user, 'has_perm'):
            return user.has_perm(permission, obj)
        
        return True
    
    @classmethod
    def check_rate_limit(cls, request, key_prefix: str = 'rate_limit', 
                        limit: int = 60, window: int = 60) -> bool:
        """
        Implement rate limiting to prevent abuse
        """
        # Get client identifier
        client_ip = cls.get_client_ip(request)
        user_id = getattr(request, 'user', None)
        user_id = user_id.id if user_id and hasattr(user_id, 'is_authenticated') and user_id.is_authenticated else 'anonymous'
        
        # Create cache key
        cache_key = f"{key_prefix}:{client_ip}:{user_id}"
        
        # Get current count
        current_count = cache.get(cache_key, 0)
        
        if current_count >= limit:
            logger.warning(f"Rate limit exceeded for {client_ip} (user: {user_id})")
            return False
        
        # Increment counter
        cache.set(cache_key, current_count + 1, window)
        return True
    
    @classmethod
    def get_client_ip(cls, request) -> str:
        """Get real client IP address"""
        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            ip = x_forwarded_for.split(',')[0].strip()
        else:
            ip = request.META.get('REMOTE_ADDR', '127.0.0.1')
        return ip
    
    @classmethod
    def sanitize_error_message(cls, error_msg: str) -> str:
        """
        Sanitize error messages to prevent information disclosure
        """
        # Remove file paths
        error_msg = re.sub(r'[/\\][a-zA-Z0-9_/\\.-]+', '[PATH_REMOVED]', error_msg)
        
        # Remove sensitive keywords
        sensitive_patterns = [
            (r'password[^a-zA-Z0-9]*[a-zA-Z0-9]+', 'password [REDACTED]'),
            (r'secret[^a-zA-Z0-9]*[a-zA-Z0-9]+', 'secret [REDACTED]'),
            (r'key[^a-zA-Z0-9]*[a-zA-Z0-9]+', 'key [REDACTED]'),
            (r'token[^a-zA-Z0-9]*[a-zA-Z0-9]+', 'token [REDACTED]'),
            (r'database.*error', 'database connection issue'),
            (r'sql.*error', 'database query issue'),
        ]
        
        for pattern, replacement in sensitive_patterns:
            error_msg = re.sub(pattern, replacement, error_msg, flags=re.IGNORECASE)
        
        return error_msg
    
    @classmethod
    def validate_file_type(cls, filename: str, allowed_extensions: Optional[List[str]] = None) -> bool:
        """
        Validate file types for secure uploads
        """
        if not filename:
            raise ValidationError("Filename cannot be empty")
        
        # Default allowed extensions
        if allowed_extensions is None:
            allowed_extensions = ['.pdf', '.jpg', '.jpeg', '.png', '.doc', '.docx', '.txt']
        
        # Get file extension
        _, ext = os.path.splitext(filename.lower())
        
        if ext not in allowed_extensions:
            raise ValidationError(f"File type '{ext}' not allowed")
        
        # Check for double extensions (e.g., file.php.jpg)
        if filename.count('.') > 1:
            parts = filename.split('.')
            for part in parts[:-1]:  # Check all parts except the last extension
                if part.lower() in ['php', 'asp', 'jsp', 'exe', 'bat', 'cmd', 'sh']:
                    raise ValidationError("Suspicious file name detected")
        
        return True
    
    @classmethod
    def add_security_headers(cls, response) -> Any:
        """
        Add comprehensive security headers
        """
        security_headers = {
            'X-Content-Type-Options': 'nosniff',
            'X-Frame-Options': 'DENY',
            'X-XSS-Protection': '1; mode=block',
            'Referrer-Policy': 'strict-origin-when-cross-origin',
            'Content-Security-Policy': "default-src 'self'; script-src 'self' 'unsafe-inline'; style-src 'self' 'unsafe-inline';",
            'Strict-Transport-Security': 'max-age=31536000; includeSubDomains',
        }
        
        for header, value in security_headers.items():
            response[header] = value
        
        return response
    
    @classmethod
    def create_secure_response(cls, data: Dict[str, Any], status: int = 200) -> JsonResponse:
        """
        Create a secure JSON response with proper headers
        """
        # Sanitize response data
        sanitized_data = cls._sanitize_response_data(data)
        
        response = JsonResponse(sanitized_data, status=status)
        return cls.add_security_headers(response)
    
    @classmethod
    def _sanitize_response_data(cls, data: Any) -> Any:
        """
        Recursively sanitize response data
        """
        if isinstance(data, dict):
            return {key: cls._sanitize_response_data(value) for key, value in data.items()}
        elif isinstance(data, list):
            return [cls._sanitize_response_data(item) for item in data]
        elif isinstance(data, str):
            return cls.sanitize_input(data)
        else:
            return data

class RateLimiter:
    """Advanced rate limiting with different strategies"""
    
    @staticmethod
    def sliding_window_rate_limit(request, key: str, limit: int, window: int) -> bool:
        """
        Sliding window rate limiting implementation
        """
        now = time.time()
        cache_key = f"rate_limit_sliding:{key}"
        
        # Get existing timestamps
        timestamps = cache.get(cache_key, [])
        
        # Remove old timestamps
        timestamps = [ts for ts in timestamps if now - ts < window]
        
        # Check if limit exceeded
        if len(timestamps) >= limit:
            return False
        
        # Add current timestamp
        timestamps.append(now)
        cache.set(cache_key, timestamps, window)
        
        return True
    
    @staticmethod
    def token_bucket_rate_limit(request, key: str, capacity: int, refill_rate: float) -> bool:
        """
        Token bucket rate limiting implementation
        """
        now = time.time()
        cache_key = f"rate_limit_bucket:{key}"
        
        # Get bucket state
        bucket_data = cache.get(cache_key, {'tokens': capacity, 'last_refill': now})
        
        # Calculate tokens to add
        time_passed = now - bucket_data['last_refill']
        tokens_to_add = time_passed * refill_rate
        
        # Update bucket
        bucket_data['tokens'] = min(capacity, bucket_data['tokens'] + tokens_to_add)
        bucket_data['last_refill'] = now
        
        # Check if request can be processed
        if bucket_data['tokens'] >= 1:
            bucket_data['tokens'] -= 1
            cache.set(cache_key, bucket_data, 3600)  # Cache for 1 hour
            return True
        
        cache.set(cache_key, bucket_data, 3600)
        return False

# Decorator for easy rate limiting
def rate_limit(key_func=None, limit=60, window=60, method='sliding'):
    """
    Decorator for rate limiting views
    """
    def decorator(view_func):
        def wrapper(request, *args, **kwargs):
            # Generate rate limit key
            if key_func:
                key = key_func(request)
            else:
                key = f"{request.META.get('REMOTE_ADDR', '127.0.0.1')}:{request.user.id if request.user.is_authenticated else 'anon'}"
            
            # Apply rate limiting
            if method == 'sliding':
                allowed = RateLimiter.sliding_window_rate_limit(request, key, limit, window)
            elif method == 'token_bucket':
                allowed = RateLimiter.token_bucket_rate_limit(request, key, limit, window/60)
            else:
                allowed = SecurityUtils.check_rate_limit(request, 'default', limit, window)
            
            if not allowed:
                return SecurityUtils.create_secure_response({
                    'error': 'Rate limit exceeded. Please try again later.',
                    'retry_after': window
                }, status=429)
            
            return view_func(request, *args, **kwargs)
        return wrapper
    return decorator