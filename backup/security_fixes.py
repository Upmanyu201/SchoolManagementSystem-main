# Security fixes for backup system
import os
import logging
from django.conf import settings
from django.utils._os import safe_join

logger = logging.getLogger('backup.security')

class BackupSecurityManager:
    """Centralized security management for backup operations"""
    
    ALLOWED_EXTENSIONS = ['.json']
    MAX_FILE_SIZE = 50 * 1024 * 1024  # 50MB
    ALLOWED_CHARS = 'abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789_-'
    
    @staticmethod
    def validate_filename(filename):
        """Validate filename for security"""
        if not filename:
            raise ValueError("Filename cannot be empty")
        
        # Check extension
        ext = os.path.splitext(filename)[1].lower()
        if ext not in BackupSecurityManager.ALLOWED_EXTENSIONS:
            raise ValueError(f"Invalid file extension. Allowed: {BackupSecurityManager.ALLOWED_EXTENSIONS}")
        
        # Check for path traversal
        if '..' in filename or '/' in filename or '\\' in filename:
            raise ValueError("Invalid filename: path traversal detected")
        
        # Check length
        if len(filename) > 255:
            raise ValueError("Filename too long")
        
        return True
    
    @staticmethod
    def sanitize_filename(filename):
        """Sanitize filename removing dangerous characters"""
        # Remove extension temporarily
        name, ext = os.path.splitext(filename)
        
        # Keep only allowed characters
        sanitized = ''.join(c for c in name if c in BackupSecurityManager.ALLOWED_CHARS)
        
        # Ensure not empty
        if not sanitized:
            sanitized = 'backup'
        
        # Limit length
        if len(sanitized) > 50:
            sanitized = sanitized[:50]
        
        return sanitized + ext
    
    @staticmethod
    def get_safe_path(base_dir, filename):
        """Get safe file path preventing traversal"""
        try:
            # Sanitize filename first
            safe_filename = BackupSecurityManager.sanitize_filename(filename)
            
            # Use Django's safe_join
            return safe_join(base_dir, safe_filename)
        except ValueError as e:
            logger.error(f"Path traversal attempt detected: {filename}")
            raise ValueError("Invalid file path")
    
    @staticmethod
    def validate_file_size(file_size):
        """Validate file size"""
        if file_size > BackupSecurityManager.MAX_FILE_SIZE:
            raise ValueError(f"File too large. Maximum size: {BackupSecurityManager.MAX_FILE_SIZE / (1024*1024):.1f}MB")
        return True
    
    @staticmethod
    def log_security_event(event_type, user, details):
        """Log security events"""
        from .security_utils import safe_log_warning
        safe_log_warning(
            logger, 
            "Security event: %s by user %s - %s", 
            event_type, 
            user, 
            details
        )
    
    @staticmethod
    def compute_file_checksum(file_path):
        """Compute file checksum for integrity"""
        import hashlib
        try:
            with open(file_path, 'rb') as f:
                return hashlib.sha256(f.read()).hexdigest()
        except Exception:
            return None
    
    @staticmethod
    def validate_file_size(file_size):
        """Validate file size"""
        return file_size <= BackupSecurityManager.MAX_FILE_SIZE
    
    @staticmethod
    def validate_json_structure(data):
        """Validate JSON backup structure"""
        if not isinstance(data, list):
            return False
        
        for item in data:
            if not isinstance(item, dict) or 'model' not in item:
                return False
        
        return True

# Apply security fixes to existing functions
def secure_backup_path(backup_dir, filename):
    """Secure wrapper for backup path generation"""
    return BackupSecurityManager.get_safe_path(backup_dir, filename)

def validate_backup_file(file_obj):
    """Validate uploaded backup file"""
    # Check file size
    BackupSecurityManager.validate_file_size(file_obj.size)
    
    # Check filename
    BackupSecurityManager.validate_filename(file_obj.name)
    
    return True