from django import template
from django.contrib.auth.models import AnonymousUser
from users.models import UserModulePermission

register = template.Library()

@register.simple_tag
def has_module_permission(user, module_name, permission_type='view'):
    """
    Template tag to check module permissions
    Usage: {% has_module_permission user 'students' 'view' as can_view_students %}
    """
    if isinstance(user, AnonymousUser) or not user.is_authenticated:
        return False
    
    if user.is_superuser:
        return True
    
    permissions = UserModulePermission.get_user_permissions(user)
    return permissions.get(module_name, {}).get(permission_type, False)

@register.inclusion_tag('users/permission_badge.html')
def permission_badge(user, module_name):
    """
    Display permission badge for a module
    Usage: {% permission_badge user 'students' %}
    """
    if isinstance(user, AnonymousUser) or not user.is_authenticated:
        return {'has_view': False, 'has_edit': False, 'module_name': module_name}
    
    if user.is_superuser:
        return {'has_view': True, 'has_edit': True, 'module_name': module_name}
    
    permissions = UserModulePermission.get_user_permissions(user)
    module_perms = permissions.get(module_name, {})
    
    return {
        'has_view': module_perms.get('view', False),
        'has_edit': module_perms.get('edit', False),
        'module_name': module_name
    }

@register.filter
def can_access_module(user, module_name):
    """
    Filter to check if user can access module (view permission)
    Usage: {{ user|can_access_module:'students' }}
    """
    if isinstance(user, AnonymousUser) or not user.is_authenticated:
        return False
    
    if user.is_superuser:
        return True
    
    permissions = UserModulePermission.get_user_permissions(user)
    return permissions.get(module_name, {}).get('view', False)

@register.filter
def can_edit_module(user, module_name):
    """
    Filter to check if user can edit module
    Usage: {{ user|can_edit_module:'students' }}
    """
    if isinstance(user, AnonymousUser) or not user.is_authenticated:
        return False
    
    if user.is_superuser:
        return True
    
    permissions = UserModulePermission.get_user_permissions(user)
    return permissions.get(module_name, {}).get('edit', False)

@register.simple_tag
def get_user_modules(user):
    """
    Get all modules user has access to
    Usage: {% get_user_modules user as user_modules %}
    """
    if isinstance(user, AnonymousUser) or not user.is_authenticated:
        return {}
    
    if user.is_superuser:
        return UserModulePermission._get_superuser_permissions()
    
    return UserModulePermission.get_user_permissions(user)

@register.inclusion_tag('users/module_access_links.html')
def render_module_links(user):
    """
    Render navigation links based on user permissions
    Usage: {% render_module_links user %}
    """
    if isinstance(user, AnonymousUser) or not user.is_authenticated:
        return {'modules': {}}
    
    permissions = UserModulePermission.get_user_permissions(user)
    
    # Module configuration with icons and URLs
    module_config = {
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
    
    # Filter modules based on permissions
    accessible_modules = {}
    for module_name, config in module_config.items():
        if permissions.get(module_name, {}).get('view', False):
            accessible_modules[module_name] = {
                **config,
                'can_edit': permissions.get(module_name, {}).get('edit', False)
            }
    
    return {'modules': accessible_modules, 'user': user}