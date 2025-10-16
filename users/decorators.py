from functools import wraps
from django.shortcuts import redirect
from django.contrib import messages
from django.http import JsonResponse
from django.core.exceptions import PermissionDenied
from .models import UserModulePermission

def module_required(module_name, permission_type='view'):
    """
    2025 Industry Standard: Async-compatible module access decorator
    
    Usage:
    @module_required('students', 'view')
    @module_required('fees', 'edit')
    """
    def decorator(view_func):
        @wraps(view_func)
        async def async_wrapper(request, *args, **kwargs):
            if not await _check_module_permission(request.user, module_name, permission_type):
                return await _handle_permission_denied(request, module_name, permission_type)
            return await view_func(request, *args, **kwargs)
        
        @wraps(view_func)
        def sync_wrapper(request, *args, **kwargs):
            if not _check_module_permission_sync(request.user, module_name, permission_type):
                return _handle_permission_denied_sync(request, module_name, permission_type)
            return view_func(request, *args, **kwargs)
        
        # Return async wrapper if view is async, sync otherwise
        import asyncio
        if asyncio.iscoroutinefunction(view_func):
            return async_wrapper
        return sync_wrapper
    
    return decorator

async def _check_module_permission(user, module_name, permission_type):
    """Async permission check"""
    if not user.is_authenticated:
        return False
    
    if user.is_superuser:
        return True
    
    permissions = UserModulePermission.get_user_permissions(user)
    return permissions.get(module_name, {}).get(permission_type, False)

def _check_module_permission_sync(user, module_name, permission_type):
    """Sync permission check"""
    if not user.is_authenticated:
        return False
    
    if user.is_superuser:
        return True
    
    permissions = UserModulePermission.get_user_permissions(user)
    return permissions.get(module_name, {}).get(permission_type, False)

async def _handle_permission_denied(request, module_name, permission_type):
    """Async permission denied handler"""
    if not request.user.is_authenticated:
        return redirect('login')
    
    if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        return JsonResponse({
            'error': True,
            'message': f'You don\'t have {permission_type} access to {module_name.title()} module.'
        }, status=403)
    
    messages.error(request, f'Sorry, you don\'t have {permission_type} access to the {module_name.title()} module. Please contact your administrator.')
    return redirect('dashboard')

def _handle_permission_denied_sync(request, module_name, permission_type):
    """Sync permission denied handler"""
    if not request.user.is_authenticated:
        return redirect('login')
    
    if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        return JsonResponse({
            'error': True,
            'message': f'You don\'t have {permission_type} access to {module_name.title()} module.'
        }, status=403)
    
    messages.error(request, f'Sorry, you don\'t have {permission_type} access to the {module_name.title()} module. Please contact your administrator.')
    return redirect('dashboard')

class ModuleAccessMixin:
    """
    2025 Industry Standard: Class-based view mixin for module access
    
    Usage:
    class StudentListView(ModuleAccessMixin, ListView):
        module_name = 'students'
        permission_type = 'view'
    """
    module_name = None
    permission_type = 'view'
    
    def dispatch(self, request, *args, **kwargs):
        if not self.module_name:
            raise ValueError("module_name must be specified")
        
        if not request.user.is_authenticated:
            return redirect('login')
        
        if not _check_module_permission_sync(request.user, self.module_name, self.permission_type):
            return _handle_permission_denied_sync(request, self.module_name, self.permission_type)
        
        return super().dispatch(request, *args, **kwargs)

def superuser_required(view_func):
    """Decorator for superuser-only views"""
    @wraps(view_func)
    def wrapper(request, *args, **kwargs):
        if not request.user.is_superuser:
            messages.error(request, 'This action requires superuser privileges.')
            return redirect('dashboard')
        return view_func(request, *args, **kwargs)
    return wrapper