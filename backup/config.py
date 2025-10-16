# Modern Backup System Configuration - 2025 Standards
from pathlib import Path
from django.conf import settings

# Version and compatibility
BACKUP_SYSTEM_VERSION = '2.0.0'
MIN_DJANGO_VERSION = '4.2'
SUPPORTED_FORMATS = ['json']

# Security settings (2025 standards)
SECURITY_CONFIG = {
    'MAX_FILE_SIZE_MB': 100,
    'ALLOWED_EXTENSIONS': ['.json'],
    'REQUIRE_AUTHENTICATION': True,
    'VALIDATE_PATHS': True,
    'SANITIZE_INPUTS': True,
    'LOG_SECURITY_EVENTS': True,
}

# Performance settings
PERFORMANCE_CONFIG = {
    'ASYNC_OPERATIONS': True,
    'BATCH_SIZE': 1000,
    'MAX_CONCURRENT_JOBS': 3,
    'PROGRESS_TRACKING': True,
    'MEMORY_LIMIT_MB': 512,
}

# Backup retention policy
RETENTION_CONFIG = {
    'MAX_BACKUP_FILES': 50,
    'MAX_AGE_DAYS': 90,
    'AUTO_CLEANUP': True,
    'CLEANUP_INTERVAL_HOURS': 24,
}

# Model processing order (fixed dependencies)
MODEL_DEPENDENCY_ORDER = [
    'subjects.classsection',  # Primary - all students reference this
    'school_profile.schoolprofile',
    'teachers.teacher',
    'subjects.subject',
    'students.student',
    'transport.route',
    'transport.stoppage',
    'fees.feesgroup',
    'fees.feestype',
    'fines.finetype',
    'transport.transportassignment',
    'student_fees.feedeposit',
    'fines.fine',
    'fines.finestudent',
    'attendance.attendance',
]

# Updated allowed apps (includes messaging)
ALLOWED_APPS = [
    'core',
    'school_profile', 
    'teachers',
    'subjects',
    'students',
    'transport',
    'student_fees',
    'fees',
    'fines',
    'attendance',
    'promotion',
    'reports',
    'messaging',
]

# Critical models to preserve (never delete)
PRESERVE_MODELS = [
    'auth.user',
    'auth.group', 
    'auth.permission',
    'users.customuser',
    'sessions.session',
    'contenttypes.contenttype',
    'admin.logentry',
]

# Backup categories for selective restore
BACKUP_CATEGORIES = {
    'full': {
        'apps': ALLOWED_APPS,
        'description': 'Complete system backup'
    },
    'students': {
        'apps': ['students', 'student_fees', 'attendance'],
        'description': 'Student data and related records'
    },
    'financial': {
        'apps': ['fees', 'student_fees', 'fines'],
        'description': 'Financial records and fee structures'
    },
    'teachers': {
        'apps': ['teachers', 'subjects'],
        'description': 'Teacher profiles and subjects'
    },
    'transport': {
        'apps': ['transport'],
        'description': 'Transport routes and assignments'
    },
}

# Default settings
DEFAULT_RESTORE_MODE = 'merge'
ENABLE_DATA_CLEARING = False
REQUIRE_CONFIRMATION_FOR_REPLACE = True
CREATE_SNAPSHOTS_BY_DEFAULT = True

# Logging configuration
LOGGING_CONFIG = {
    'level': 'INFO',
    'log_operations': True,
    'log_security_events': True,
    'max_log_size_mb': 100,
    'log_retention_days': 30,
}

# API configuration
API_CONFIG = {
    'version': 'v2',
    'rate_limit': '100/hour',
    'timeout_seconds': 300,
    'max_request_size_mb': 100,
}

# Helper functions
def get_backup_directory():
    """Get secure backup directory path"""
    backup_dir = Path(settings.BASE_DIR) / 'backups'
    backup_dir.mkdir(exist_ok=True)
    return backup_dir

def get_temp_directory():
    """Get temporary files directory"""
    temp_dir = get_backup_directory() / 'temp'
    temp_dir.mkdir(exist_ok=True)
    return temp_dir