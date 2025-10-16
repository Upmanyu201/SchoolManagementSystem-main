from django.shortcuts import redirect
from django.contrib import messages
from django.urls import resolve, reverse
from django.http import JsonResponse
from .models import UserModulePermission

class ModuleAccessMiddleware:
    """
    2025 Industry Standard: Global module access control middleware
    Automatically protects all app URLs based on module permissions
    """
    
    def __init__(self, get_response):
        self.get_response = get_response
        
        # Define module URL patterns - Updated to match corrected URLs
        self.module_patterns = {
            'students': ['/students/', 'student'],
            'teachers': ['teacher_list', 'teacher'],
            'subjects': ['subjects_management', 'subject'],
            'fees': ['fees:', 'fee'],
            'payments': ['student_fees:', 'payment'],
            'fines': ['fines:', 'fine'],
            'attendance': ['attendance_manage', 'attendance'],
            'transport': ['transport_management', 'transport'],
            'reports': ['fees_report', 'report'],
            'messaging': ['messaging:', 'message'],
            'promotion': ['promotion:', 'promotion_class'],
            'users': ['users:', 'user'],
            'settings': ['language_settings', 'setting'],
            'backup': ['backup:', 'backup_restore'],
            'school_profile': ['school_profile_view', 'profile'],
        }
        
        # Define which URL patterns require edit permissions
        self.edit_patterns = [
            'add', 'create', 'edit', 'update', 'delete', 'remove',
            'save', 'modify', 'change', 'bulk', 'import', 'export'
        ]
        
        # Exempt URLs that don't require module permissions
        self.exempt_urls = [
            'admin:', 'login', 'logout', 'dashboard', 'profile',
            'api/check-module-access', 'get-user-permissions',
            'home', 'index', 'static', 'media'
        ]
    
    def __call__(self, request):
        # Skip middleware for superusers and unauthenticated users
        if not request.user.is_authenticated or request.user.is_superuser:
            return self.get_response(request)
        
        # Check if URL requires module permission
        if self._requires_module_permission(request):
            module_name, permission_type = self._get_required_permission(request)
            
            if not self._has_permission(request.user, module_name, permission_type):
                return self._handle_access_denied(request, module_name, permission_type)
        
        return self.get_response(request)
    
    def _requires_module_permission(self, request):
        """Check if the current URL requires module permission"""
        try:
            resolver_match = resolve(request.path_info)
            url_name = resolver_match.url_name
            namespace = resolver_match.namespace
            
            # Check exempt URLs
            for exempt in self.exempt_urls:
                if exempt in request.path_info or (url_name and exempt in url_name):
                    return False
            
            # Check if URL belongs to a protected module
            full_url = f"{namespace}:{url_name}" if namespace else url_name or ""
            
            for module, patterns in self.module_patterns.items():
                for pattern in patterns:
                    if pattern in full_url or pattern in request.path_info:
                        return True
            
            return False
            
        except Exception:
            return False
    
    def _get_required_permission(self, request):
        """Determine which module and permission type is required"""
        try:
            resolver_match = resolve(request.path_info)
            url_name = resolver_match.url_name or ""
            namespace = resolver_match.namespace or ""
            full_url = f"{namespace}:{url_name}"
            
            # Determine module
            module_name = None
            for module, patterns in self.module_patterns.items():
                for pattern in patterns:
                    if pattern in full_url or pattern in request.path_info:
                        module_name = module
                        break
                if module_name:
                    break
            
            # Determine permission type (view or edit)
            permission_type = 'view'
            
            # Check if it's an edit operation
            for edit_pattern in self.edit_patterns:
                if edit_pattern in url_name.lower() or edit_pattern in request.path_info.lower():
                    permission_type = 'edit'
                    break
            
            # POST, PUT, DELETE requests typically require edit permission
            if request.method in ['POST', 'PUT', 'DELETE', 'PATCH']:
                permission_type = 'edit'
            
            return module_name, permission_type
            
        except Exception:
            return None, 'view'
    
    def _has_permission(self, user, module_name, permission_type):
        """Check if user has the required permission"""
        if not module_name:
            return True
        
        permissions = UserModulePermission.get_user_permissions(user)
        return permissions.get(module_name, {}).get(permission_type, False)
    
    def _handle_access_denied(self, request, module_name, permission_type):
        """Handle access denied scenarios"""
        
        # For AJAX requests, return JSON response
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return JsonResponse({
                'error': True,
                'message': f'You don\'t have {permission_type} access to {module_name.title()} module.',
                'redirect_url': reverse('dashboard')
            }, status=403)
        
        # For regular requests, redirect with message
        messages.error(
            request, 
            f'Sorry, you don\'t have {permission_type} access to the {module_name.title()} module. Please contact your administrator for access.'
        )
        
        return redirect('dashboard')

class SecurityHeadersMiddleware:
    """2025 Security: Add security headers"""
    
    def __init__(self, get_response):
        self.get_response = get_response
    
    def __call__(self, request):
        response = self.get_response(request)
        
        # Add security headers
        response['X-Content-Type-Options'] = 'nosniff'
        response['X-Frame-Options'] = 'DENY'
        response['X-XSS-Protection'] = '1; mode=block'
        response['Referrer-Policy'] = 'strict-origin-when-cross-origin'
        
        # Add CSP for module access pages
        if 'module-access' in request.path:
            response['Content-Security-Policy'] = (
                "default-src 'self'; "
                "script-src 'self' 'unsafe-inline'; "
                "style-src 'self' 'unsafe-inline' https://fonts.googleapis.com; "
                "font-src 'self' https://fonts.gstatic.com;"
            )
        
        return response