import re
import html
import logging
from django.utils.html import escape
from django.core.cache import cache
from django.contrib.auth.models import User
from django.utils import timezone
from typing import Any, Dict, Optional

logger = logging.getLogger(__name__)


def sanitize_input(value: Any) -> str:
    """
    Comprehensive input sanitization to prevent XSS and injection attacks (CWE-79/80)
    """
    if value is None:
        return ""
    
    # Convert to string and strip whitespace
    clean_value = str(value).strip()
    
    # HTML escape to prevent XSS
    clean_value = html.escape(clean_value)
    
    # Additional XSS prevention patterns
    dangerous_patterns = [
        r'<script[^>]*>.*?</script>',
        r'javascript:',
        r'on\w+\s*=',
        r'data:text/html',
        r'vbscript:',
        r'<iframe[^>]*>.*?</iframe>',
        r'<object[^>]*>.*?</object>',
        r'<embed[^>]*>.*?</embed>'
    ]
    
    for pattern in dangerous_patterns:
        clean_value = re.sub(pattern, '', clean_value, flags=re.IGNORECASE | re.DOTALL)
    
    # Remove null bytes and control characters
    clean_value = re.sub(r'[\x00-\x08\x0B\x0C\x0E-\x1F\x7F]', '', clean_value)
    
    # Limit length to prevent log flooding
    if len(clean_value) > 1000:
        clean_value = clean_value[:1000] + "..."
    
    return clean_value


def validate_phone_number(phone: str) -> bool:
    """
    Validate Indian mobile number format
    """
    if not phone:
        return False
    
    # Remove spaces and special characters
    clean_phone = re.sub(r'[^\d]', '', phone)
    
    # Check if it's a valid 10-digit Indian mobile number
    return bool(re.match(r'^[6-9]\d{9}$', clean_phone))


def validate_email_format(email: str) -> bool:
    """
    Basic email format validation
    """
    if not email:
        return False
    
    email_pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    return bool(re.match(email_pattern, email.strip().lower()))


def validate_admission_number(admission_no: str) -> bool:
    """
    Validate admission number format
    """
    if not admission_no:
        return False
    
    # Allow alphanumeric, 3-20 characters
    return bool(re.match(r'^[A-Z0-9]{3,20}$', admission_no.upper().strip()))


def log_security_event(user: User, event_type: str, description: str, 
                      ip_address: Optional[str] = None, 
                      additional_data: Optional[Dict] = None) -> None:
    """
    Log security-related events for monitoring and audit
    """
    try:
        # Sanitize all inputs
        clean_event_type = sanitize_input(event_type)
        clean_description = sanitize_input(description)
        clean_ip = sanitize_input(ip_address) if ip_address else "unknown"
        
        # Create log entry
        log_entry = {
            'timestamp': timezone.now().isoformat(),
            'user_id': user.id if user else None,
            'username': sanitize_input(user.username) if user else "anonymous",
            'event_type': clean_event_type,
            'description': clean_description,
            'ip_address': clean_ip,
            'additional_data': additional_data or {}
        }
        
        # Log to Django logger
        logger.info(f"SECURITY_EVENT: {clean_event_type} - User: {log_entry['username']} - {clean_description}")
        
        # Store in cache for recent events (optional)
        cache_key = f"security_events_{user.id if user else 'anonymous'}"
        recent_events = cache.get(cache_key, [])
        recent_events.append(log_entry)
        
        # Keep only last 50 events per user
        if len(recent_events) > 50:
            recent_events = recent_events[-50:]
        
        cache.set(cache_key, recent_events, 3600)  # 1 hour
        
    except Exception as e:
        # Fallback logging if security logging fails
        logger.error(f"Failed to log security event: {sanitize_input(str(e))}")


def check_rate_limit(user: User, action: str, limit: int = 10, 
                    window_minutes: int = 5) -> bool:
    """
    Simple rate limiting to prevent abuse
    Returns True if rate limit exceeded
    """
    try:
        cache_key = f"rate_limit_{user.id if user else 'anonymous'}_{action}"
        current_count = cache.get(cache_key, 0)
        
        if current_count >= limit:
            log_security_event(
                user, 
                'rate_limit_exceeded', 
                f'Rate limit exceeded for action: {action}'
            )
            return True
        
        # Increment counter
        cache.set(cache_key, current_count + 1, window_minutes * 60)
        return False
        
    except Exception as e:
        logger.error(f"Rate limit check failed: {sanitize_input(str(e))}")
        return False  # Allow action if rate limiting fails


def validate_file_upload(file, max_size_mb: int = 10, 
                        allowed_types: Optional[list] = None) -> Dict[str, Any]:
    """
    Comprehensive file upload validation (CWE-22 Path Traversal prevention)
    """
    from django.core.exceptions import ValidationError
    
    result = {'valid': True, 'errors': []}
    
    if not file:
        result['valid'] = False
        result['errors'].append("No file provided")
        return result
    
    # Check file size
    max_size_bytes = max_size_mb * 1024 * 1024
    if file.size > max_size_bytes:
        result['valid'] = False
        result['errors'].append(f"File size must be less than {max_size_mb}MB")
    
    # Check file type if specified
    if allowed_types and hasattr(file, 'content_type'):
        if file.content_type not in allowed_types:
            result['valid'] = False
            result['errors'].append(f"File type not allowed. Allowed types: {', '.join(allowed_types)}")
    
    # Enhanced filename security validation
    if hasattr(file, 'name') and file.name:
        filename = file.name
        
        # Check for path traversal patterns
        dangerous_patterns = ['..', '~', '/etc/', '/proc/', '/sys/', 'C:\\', 'C:/', '\\\\', '//']
        for pattern in dangerous_patterns:
            if pattern in filename:
                result['valid'] = False
                result['errors'].append("Invalid filename: path traversal detected")
                break
        
        # Check for executable file extensions
        dangerous_extensions = ['.exe', '.bat', '.cmd', '.com', '.scr', '.pif', '.js', '.vbs', '.jar']
        file_ext = filename.lower().split('.')[-1] if '.' in filename else ''
        if f'.{file_ext}' in dangerous_extensions:
            result['valid'] = False
            result['errors'].append("Executable file types not allowed")
        
        # Check filename length and characters
        if len(filename) > 255:
            result['valid'] = False
            result['errors'].append("Filename too long")
        
        # Only allow safe characters in filename
        if not re.match(r'^[a-zA-Z0-9._-]+$', filename.replace(' ', '_')):
            result['valid'] = False
            result['errors'].append("Filename contains invalid characters")
    
    return result


def clean_search_query(query: str, max_length: int = 100) -> str:
    """
    Clean and validate search queries to prevent injection (CWE-89)
    """
    from django.core.exceptions import ValidationError
    
    if not query:
        return ""
    
    # Sanitize input first
    clean_query = sanitize_input(query.strip())[:max_length]
    
    # Enhanced SQL injection prevention patterns
    dangerous_patterns = [
        r'union\s+select', r'drop\s+table', r'delete\s+from',
        r'insert\s+into', r'update\s+set', r'exec\s*\(',
        r'script\s*>', r'javascript:', r'vbscript:',
        r'--', r'/\*', r'\*/', r';', r'\|\|', r'&&',
        r'0x[0-9a-f]+', r'char\s*\(', r'ascii\s*\(',
        r'substring\s*\(', r'concat\s*\(', r'load_file\s*\(',
        r'into\s+outfile', r'into\s+dumpfile'
    ]
    
    for pattern in dangerous_patterns:
        if re.search(pattern, clean_query, flags=re.IGNORECASE):
            raise ValidationError("Invalid search query detected")
    
    # Remove any remaining dangerous characters
    clean_query = re.sub(r'[;\|&<>"\']', '', clean_query)
    
    return clean_query


def generate_secure_filename(original_filename: str, prefix: str = "") -> str:
    """
    Generate secure filename to prevent path traversal and conflicts
    """
    import uuid
    from pathlib import Path
    
    if not original_filename:
        return f"{prefix}_{uuid.uuid4().hex}"
    
    # Get file extension safely
    file_path = Path(original_filename)
    extension = file_path.suffix.lower()
    
    # Generate unique filename
    unique_id = uuid.uuid4().hex[:8]
    timestamp = timezone.now().strftime('%Y%m%d_%H%M%S')
    
    safe_filename = f"{prefix}_{timestamp}_{unique_id}{extension}"
    
    return safe_filename


def mask_sensitive_data(data: str, mask_char: str = "*", 
                       visible_chars: int = 4) -> str:
    """
    Mask sensitive data for logging (e.g., phone numbers, emails)
    """
    if not data or len(data) <= visible_chars:
        return mask_char * len(data) if data else ""
    
    visible_part = data[:visible_chars]
    masked_part = mask_char * (len(data) - visible_chars)
    
    return visible_part + masked_part


# Security validation decorators
def validate_user_input(max_length: int = 1000):
    """
    Decorator to validate user input in view functions with enhanced security
    """
    def decorator(func):
        def wrapper(request, *args, **kwargs):
            try:
                # Validate POST data
                if request.method == 'POST':
                    for key, value in request.POST.items():
                        if isinstance(value, str):
                            # Check length
                            if len(value) > max_length:
                                from django.http import JsonResponse
                                return JsonResponse({
                                    'success': False,
                                    'message': f'Input too long for field: {sanitize_input(key)}'
                                }, status=400)
                            
                            # Check for suspicious patterns
                            try:
                                clean_search_query(value, max_length)
                            except Exception:
                                from django.http import JsonResponse
                                return JsonResponse({
                                    'success': False,
                                    'message': 'Invalid input detected'
                                }, status=400)
                
                # Validate GET parameters
                if request.method == 'GET':
                    for key, value in request.GET.items():
                        if isinstance(value, str) and len(value) > max_length:
                            from django.http import JsonResponse
                            return JsonResponse({
                                'success': False,
                                'message': f'Parameter too long: {sanitize_input(key)}'
                            }, status=400)
                
                return func(request, *args, **kwargs)
                
            except Exception as e:
                logger.error(f"Input validation error: {sanitize_input(str(e))}")
                from django.http import JsonResponse
                return JsonResponse({
                    'success': False,
                    'message': 'Request validation failed'
                }, status=400)
        return wrapper
    return decorator


# Constants for validation
ALLOWED_IMAGE_TYPES = ['image/jpeg', 'image/jpg', 'image/png', 'image/gif']
ALLOWED_DOCUMENT_TYPES = ['application/pdf', 'image/jpeg', 'image/jpg', 'image/png']
MAX_FILE_SIZE_MB = 10
MAX_IMAGE_SIZE_MB = 5

# Security headers for responses
SECURITY_HEADERS = {
    'X-Content-Type-Options': 'nosniff',
    'X-Frame-Options': 'DENY',
    'X-XSS-Protection': '1; mode=block',
    'Referrer-Policy': 'strict-origin-when-cross-origin'
}