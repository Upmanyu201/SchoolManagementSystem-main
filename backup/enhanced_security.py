# Enhanced Security Module - 2025 Standards
import os
import re
import html
import hashlib
import logging
from pathlib import Path
from typing import Any, Dict, List, Optional
from django.conf import settings
from django.core.exceptions import ValidationError, PermissionDenied
from django.contrib.auth.models import User
from django.utils import timezone

logger = logging.getLogger('backup.security')

class BackupSecurityManager:
    """Enhanced security manager with 2025 standards"""
    
    # Allowed file extensions
    ALLOWED_EXTENSIONS = {'.json', '.csv'}
    
    # Maximum file sizes (in bytes)
    MAX_FILE_SIZE = 100 * 1024 * 1024  # 100MB
    MAX_FILENAME_LENGTH = 100
    
    # Path traversal patterns
    DANGEROUS_PATTERNS = [
        r'\.\./',
        r'\.\.\\',
        r'/etc/',
        r'/var/',
        r'/usr/',
        r'C:\\',
        r'%2e%2e',
        r'%252e%252e'
    ]
    
    @classmethod
    def sanitize_filename(cls, filename: str) -> str:
        """Sanitize filename with enhanced security"""
        if not filename:
            return f"backup_{timezone.now().strftime('%Y%m%d_%H%M%S')}"
        
        # Remove path components
        filename = os.path.basename(filename)
        
        # Remove dangerous characters
        filename = re.sub(r'[<>:"/\\|?*\x00-\x1f]', '', filename)
        
        # Allow only safe characters
        filename = re.sub(r'[^a-zA-Z0-9._-]', '_', filename)
        
        # Remove multiple consecutive dots or underscores
        filename = re.sub(r'[._-]{2,}', '_', filename)
        
        # Ensure it doesn't start with dot or dash
        filename = re.sub(r'^[.-]', '', filename)
        
        # Limit length
        if len(filename) > cls.MAX_FILENAME_LENGTH:
            name, ext = os.path.splitext(filename)
            filename = name[:cls.MAX_FILENAME_LENGTH - len(ext)] + ext
        
        # Ensure it's not empty after sanitization
        if not filename or filename in ['.', '..']:
            filename = f"backup_{timezone.now().strftime('%Y%m%d_%H%M%S')}"
        
        return filename
    
    @classmethod
    def validate_backup_path(cls, file_path: str) -> Path:
        """Validate backup path with enhanced security"""
        try:
            # Convert to Path object
            path = Path(file_path)
            backup_dir = Path(settings.BASE_DIR) / 'backups'
            
            # Resolve absolute paths
            abs_backup_dir = backup_dir.resolve()
            abs_file_path = path.resolve()
            
            # Check if path is within backup directory
            try:
                abs_file_path.relative_to(abs_backup_dir)
            except ValueError:
                raise ValidationError("File path outside allowed directory")
            
            # Check for dangerous patterns
            path_str = str(abs_file_path).lower()
            for pattern in cls.DANGEROUS_PATTERNS:
                if re.search(pattern, path_str, re.IGNORECASE):
                    raise ValidationError(f"Dangerous path pattern detected: {pattern}")
            
            # Validate file extension
            if abs_file_path.suffix.lower() not in cls.ALLOWED_EXTENSIONS:
                raise ValidationError(f"File extension not allowed: {abs_file_path.suffix}")
            
            return abs_file_path
            
        except Exception as e:
            logger.error(f"Path validation failed: {e}")
            raise ValidationError(f"Invalid file path: {e}")
    
    @classmethod
    def sanitize_log_input(cls, input_data: Any) -> str:
        """Sanitize input for secure logging"""
        if input_data is None:
            return "None"
        
        # Convert to string
        text = str(input_data)
        
        # HTML escape to prevent XSS in log viewers
        text = html.escape(text)
        
        # Remove control characters and newlines
        text = re.sub(r'[\r\n\t\x00-\x1f\x7f-\x9f]', ' ', text)
        
        # Remove ANSI escape sequences
        text = re.sub(r'\x1b\[[0-9;]*m', '', text)
        
        # Limit length to prevent log flooding
        if len(text) > 500:
            text = text[:497] + "..."
        
        return text
    
    @classmethod
    def validate_file_size(cls, file_size: int, max_size: Optional[int] = None) -> bool:
        """Validate file size"""
        max_bytes = max_size or cls.MAX_FILE_SIZE
        return 0 < file_size <= max_bytes
    
    @classmethod
    def validate_json_structure(cls, data: Any) -> bool:
        """Validate JSON backup structure"""
        if not isinstance(data, list):
            return False
        
        if not data:  # Empty list is valid
            return True
        
        # Check first few items for structure
        for i, item in enumerate(data[:10]):
            if not isinstance(item, dict):
                logger.warning(f"Invalid item at index {i}: not a dict")
                return False
            
            if 'model' not in item:
                logger.warning(f"Invalid item at index {i}: missing 'model' field")
                return False
            
            # Validate model format (app.model)
            model = item.get('model', '')
            if not re.match(r'^[a-zA-Z_][a-zA-Z0-9_]*\.[a-zA-Z_][a-zA-Z0-9_]*$', model):
                logger.warning(f"Invalid model format at index {i}: {model}")
                return False
        
        return True
    
    @classmethod
    def compute_file_checksum(cls, file_path: str) -> str:
        """Compute secure file checksum"""
        try:
            sha256_hash = hashlib.sha256()
            with open(file_path, "rb") as f:
                for chunk in iter(lambda: f.read(8192), b""):
                    sha256_hash.update(chunk)
            return f"sha256:{sha256_hash.hexdigest()}"
        except Exception as e:
            logger.error(f"Checksum computation failed for {file_path}: {e}")
            return "sha256:error"
    
    @classmethod
    def validate_user_permissions(cls, user: User, operation: str) -> bool:
        """Validate user permissions for backup operations"""
        if not user.is_authenticated:
            return False
        
        permission_map = {
            'backup_create': 'backup.add_backupjob',
            'backup_download': 'backup.view_backupjob',
            'restore_upload': 'backup.add_restorejob',
            'restore_history': 'backup.add_restorejob',
            'backup_delete': 'backup.delete_backupjob'
        }
        
        required_permission = permission_map.get(operation)
        if not required_permission:
            return False
        
        return user.has_perm(required_permission)
    
    @classmethod
    def validate_restore_parameters(cls, data: Dict[str, Any]) -> Dict[str, Any]:
        """Validate and sanitize restore parameters"""
        validated = {}
        
        # Validate restore mode
        mode = data.get('restore_mode', 'merge')
        if mode not in ['merge', 'replace']:
            mode = 'merge'
        validated['restore_mode'] = mode
        
        # Validate restore category
        category = data.get('restore_category', 'full')
        allowed_categories = [
            'full', 'students', 'staff', 'financial', 
            'transport', 'core', 'system'
        ]
        if category not in allowed_categories:
            category = 'full'
        validated['restore_category'] = category
        
        # Validate duplicate strategy
        strategy = data.get('duplicate_strategy', 'update')
        if strategy not in ['skip', 'update']:
            strategy = 'update'
        validated['duplicate_strategy'] = strategy
        
        return validated
    
    @classmethod
    def create_secure_temp_file(cls, prefix: str = "backup_temp") -> Path:
        """Create secure temporary file"""
        backup_dir = Path(settings.BASE_DIR) / 'backups' / 'temp'
        backup_dir.mkdir(parents=True, exist_ok=True)
        
        # Generate secure filename
        timestamp = timezone.now().strftime('%Y%m%d_%H%M%S_%f')
        filename = f"{prefix}_{timestamp}.json"
        
        return backup_dir / filename
    
    @classmethod
    def make_backup_readonly(cls, file_path: Path):
        """Make backup file read-only for security"""
        import stat
        try:
            # Set read-only permissions (owner: read, group: read, others: none)
            file_path.chmod(stat.S_IRUSR | stat.S_IRGRP)
            logger.info(f"Made backup file read-only: {file_path.name}")
        except Exception as e:
            logger.error(f"Failed to set read-only permissions on {file_path}: {e}")
    
    @classmethod
    def make_backup_writable(cls, file_path: Path):
        """Temporarily make backup writable for deletion"""
        import stat
        try:
            # Add write permission for deletion
            file_path.chmod(stat.S_IRUSR | stat.S_IWUSR | stat.S_IRGRP)
            logger.info(f"Made backup file writable for deletion: {file_path.name}")
        except Exception as e:
            logger.error(f"Failed to set writable permissions on {file_path}: {e}")
    
    @classmethod
    def cleanup_temp_files(cls, max_age_hours: int = 24):
        """Clean up old temporary files"""
        try:
            temp_dir = Path(settings.BASE_DIR) / 'backups' / 'temp'
            if not temp_dir.exists():
                return
            
            cutoff_time = timezone.now().timestamp() - (max_age_hours * 3600)
            
            for file_path in temp_dir.glob('*'):
                if file_path.is_file() and file_path.stat().st_mtime < cutoff_time:
                    try:
                        file_path.unlink()
                        logger.info(f"Cleaned up temp file: {file_path.name}")
                    except Exception as e:
                        logger.error(f"Failed to cleanup {file_path}: {e}")
                        
        except Exception as e:
            logger.error(f"Temp file cleanup failed: {e}")

class SecureLogger:
    """Secure logging utility"""
    
    def __init__(self, name: str):
        self.logger = logging.getLogger(name)
    
    def info(self, message: str, *args, **kwargs):
        """Secure info logging"""
        safe_message = BackupSecurityManager.sanitize_log_input(message)
        safe_args = [BackupSecurityManager.sanitize_log_input(arg) for arg in args]
        safe_kwargs = {k: BackupSecurityManager.sanitize_log_input(v) 
                      for k, v in kwargs.items()}
        self.logger.info(safe_message, *safe_args, **safe_kwargs)
    
    def error(self, message: str, *args, **kwargs):
        """Secure error logging"""
        safe_message = BackupSecurityManager.sanitize_log_input(message)
        safe_args = [BackupSecurityManager.sanitize_log_input(arg) for arg in args]
        safe_kwargs = {k: BackupSecurityManager.sanitize_log_input(v) 
                      for k, v in kwargs.items()}
        self.logger.error(safe_message, *safe_args, **safe_kwargs)
    
    def warning(self, message: str, *args, **kwargs):
        """Secure warning logging"""
        safe_message = BackupSecurityManager.sanitize_log_input(message)
        safe_args = [BackupSecurityManager.sanitize_log_input(arg) for arg in args]
        safe_kwargs = {k: BackupSecurityManager.sanitize_log_input(v) 
                      for k, v in kwargs.items()}
        self.logger.warning(safe_message, *safe_args, **safe_kwargs)

# Create secure logger instance
secure_log = SecureLogger('backup.secure')