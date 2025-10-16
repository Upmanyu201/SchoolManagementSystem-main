from .models import UserModulePermission
from .utils import get_module_config, get_user_accessible_modules

def user_permissions(request):
    """
    2025 Industry Standard: Context processor with corrected module configuration
    Makes module permissions available globally in templates as 'user_perms'
    """
    if request.user.is_authenticated:
        permissions = UserModulePermission.get_user_permissions(request.user)
        accessible_modules = get_user_accessible_modules(request.user)
        
        return {
            'user_perms': permissions,
            'is_superuser': request.user.is_superuser,
            'module_config': get_module_config(),
            'user_accessible_modules': accessible_modules,
            'has_any_edit_access': any(
                perms.get('edit', False) for perms in permissions.values()
            ),
            'has_any_view_access': any(
                perms.get('view', False) for perms in permissions.values()
            ),
            'accessible_modules': [
                module for module, perms in permissions.items() 
                if perms.get('view', False)
            ],
            'editable_modules': [
                module for module, perms in permissions.items() 
                if perms.get('edit', False)
            ]
        }
    
    return {
        'user_perms': {},
        'is_superuser': False,
        'module_config': get_module_config(),
        'user_accessible_modules': {},
        'has_any_edit_access': False,
        'has_any_view_access': False,
        'accessible_modules': [],
        'editable_modules': []
    }