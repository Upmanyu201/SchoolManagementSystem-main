"""
2025 Industry Standard: Module permission utilities
"""

from django.core.cache import cache
from .models import UserModulePermission

# Corrected module configuration
MODULE_CONFIG = {
    'students': {
        'name': 'Students',
        'icon': 'fas fa-user-graduate',
        'url': '/students/',
        'color': 'blue'
    },
    'teachers': {
        'name': 'Teachers',
        'icon': 'fas fa-chalkboard-teacher',
        'url': 'teacher_list',
        'color': 'green'
    },
    'subjects': {
        'name': 'Subjects',
        'icon': 'fas fa-book',
        'url': 'subjects_management',
        'color': 'indigo'
    },
    'fees': {
        'name': 'Fee Setup',
        'icon': 'fas fa-money-bill-wave',
        'url': 'fees:fees_setup',
        'color': 'green'
    },
    'payments': {
        'name': 'Fee Deposit',
        'icon': 'fas fa-credit-card',
        'url': 'student_fees:fee_deposit',
        'color': 'blue'
    },
    'fines': {
        'name': 'Fine Management',
        'icon': 'fas fa-exclamation-triangle',
        'url': 'fines:base_fine',
        'color': 'red'
    },
    'attendance': {
        'name': 'Attendance',
        'icon': 'fas fa-calendar-check',
        'url': 'attendance:attendance_manage',
        'color': 'purple'
    },
    'transport': {
        'name': 'Transport',
        'icon': 'fas fa-bus',
        'url': 'transport_management',
        'color': 'yellow'
    },
    'reports': {
        'name': 'Reports',
        'icon': 'fas fa-chart-bar',
        'url': 'reports:fees_report',
        'color': 'indigo'
    },
    'messaging': {
        'name': 'Messaging',
        'icon': 'fas fa-comments',
        'url': 'messaging:dashboard',
        'color': 'pink'
    },
    'promotion': {
        'name': 'Promotion Class',
        'icon': 'fas fa-graduation-cap',
        'url': 'promotion:promotion_class',
        'color': 'teal'
    },
    'users': {
        'name': 'Manage Users',
        'icon': 'fas fa-users',
        'url': 'users:user_management',
        'color': 'red'
    },
    'settings': {
        'name': 'Settings',
        'icon': 'fas fa-cogs',
        'url': 'language_settings',
        'color': 'gray'
    },
    'backup': {
        'name': 'Backup / Restore',
        'icon': 'fas fa-database',
        'url': 'backup:backup_restore',
        'color': 'cyan'
    },
    'school_profile': {
        'name': 'School Profile',
        'icon': 'fas fa-building',
        'url': 'school_profile_view',
        'color': 'emerald'
    }
}

def get_module_config():
    """Get the corrected module configuration"""
    return MODULE_CONFIG

def get_active_modules():
    """Get list of active module names"""
    return list(MODULE_CONFIG.keys())

def check_user_permission(user, module_name, permission_type='view'):
    """
    Check if user has permission for a module
    
    Args:
        user: User instance
        module_name: Name of the module
        permission_type: 'view' or 'edit'
    
    Returns:
        bool: True if user has permission
    """
    if not user.is_authenticated:
        return False
    
    if user.is_superuser:
        return True
    
    permissions = UserModulePermission.get_user_permissions(user)
    return permissions.get(module_name, {}).get(permission_type, False)

def get_user_accessible_modules(user):
    """
    Get all modules user has access to with their configuration
    
    Args:
        user: User instance
    
    Returns:
        dict: Module configuration for accessible modules
    """
    if not user.is_authenticated:
        return {}
    
    permissions = UserModulePermission.get_user_permissions(user)
    accessible_modules = {}
    
    for module_name, config in MODULE_CONFIG.items():
        if permissions.get(module_name, {}).get('view', False):
            accessible_modules[module_name] = {
                **config,
                'can_edit': permissions.get(module_name, {}).get('edit', False)
            }
    
    return accessible_modules

def clear_permission_cache(user_id=None):
    """
    Clear permission cache for specific user or all users
    
    Args:
        user_id: Optional user ID to clear cache for specific user
    """
    if user_id:
        cache_key = f"user_permissions_{user_id}"
        cache.delete(cache_key)
    else:
        # Clear all permission caches (pattern-based deletion)
        cache.clear()