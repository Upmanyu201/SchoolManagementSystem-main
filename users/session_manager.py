from django.contrib.sessions.models import Session
from django.contrib.auth.signals import user_logged_in, user_logged_out
from django.dispatch import receiver
from django.core.cache import cache
from django.utils import timezone
import json
import uuid

class UserSessionManager:
    """Advanced 2025 session management with JWT-like tokens"""
    
    @staticmethod
    def create_user_session(user, request):
        """Create secure user session with permissions"""
        session_token = str(uuid.uuid4())
        
        # Get user permissions
        permissions = {}
        if user.is_superuser:
            # Superuser gets all permissions
            from .models import MODULE_CHOICES
            for module_code, _ in MODULE_CHOICES:
                permissions[module_code] = {'can_view': True, 'can_edit': True}
        else:
            # Regular user permissions
            for perm in user.module_permissions.all():
                permissions[perm.module] = {
                    'can_view': perm.can_view,
                    'can_edit': perm.can_edit
                }
        
        # Session data
        session_data = {
            'user_id': user.id,
            'username': user.username,
            'role': 'superuser' if user.is_superuser else user.role,
            'permissions': permissions,
            'login_time': timezone.now().isoformat(),
            'ip_address': request.META.get('REMOTE_ADDR'),
            'user_agent': request.META.get('HTTP_USER_AGENT', '')[:200],
        }
        
        # Store in cache and session
        cache_key = f"user_session_{user.id}"
        cache.set(cache_key, session_data, 86400)  # 24 hours
        
        # Store session token in Django session
        request.session['user_session_token'] = session_token
        request.session['user_permissions'] = permissions
        request.session.set_expiry(86400)  # 24 hours
        
        return session_token
    
    @staticmethod
    def get_user_permissions(user):
        """Get user permissions from cache or database"""
        cache_key = f"user_session_{user.id}"
        session_data = cache.get(cache_key)
        
        if session_data:
            return session_data.get('permissions', {})
        
        # Fallback to database
        permissions = {}
        if user.is_superuser:
            from .models import MODULE_CHOICES
            for module_code, _ in MODULE_CHOICES:
                permissions[module_code] = {'can_view': True, 'can_edit': True}
        else:
            for perm in user.module_permissions.all():
                permissions[perm.module] = {
                    'can_view': perm.can_view,
                    'can_edit': perm.can_edit
                }
        
        return permissions
    
    @staticmethod
    def invalidate_user_session(user):
        """Invalidate user session and clear cache"""
        cache_key = f"user_session_{user.id}"
        cache.delete(cache_key)
        
        # Clear permission cache
        cache.delete(f"user_permissions_{user.id}")
        cache.delete(f"user_modules_{user.id}")
    
    @staticmethod
    def check_module_permission(user, module, action='view'):
        """Check if user has permission for specific module and action"""
        permissions = UserSessionManager.get_user_permissions(user)
        
        if module not in permissions:
            return False
            
        if action == 'view':
            return permissions[module].get('can_view', False)
        elif action == 'edit':
            return permissions[module].get('can_edit', False)
            
        return False

@receiver(user_logged_in)
def on_user_login(sender, request, user, **kwargs):
    """Create session when user logs in"""
    UserSessionManager.create_user_session(user, request)

@receiver(user_logged_out)
def on_user_logout(sender, request, user, **kwargs):
    """Clean up session when user logs out"""
    if user:
        UserSessionManager.invalidate_user_session(user)