# settings/apps.py
from django.apps import AppConfig

class SettingsConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'settings'
    verbose_name = 'System Settings'
    
    def ready(self):
        """Initialize settings when app is ready"""
        try:
            # Import signals only - no database access
            from . import signals
            
        except Exception as e:
            # Don't break app startup if settings initialization fails
            import logging
            logger = logging.getLogger(__name__)
            logger.warning(f"Settings signals import failed: {e}")
    
    @classmethod
    def initialize_default_settings(cls):
        """Create default settings if they don't exist - call this from management command"""
        try:
            from django.apps import apps
            
            # Only run if Django is fully initialized
            if not apps.ready:
                return False
            
            from .models import SystemSettings, NotificationSettings, MLSettings
            
            # Create default system settings
            if not SystemSettings.objects.exists():
                SystemSettings.objects.create()
            
            # Create default notification settings
            if not NotificationSettings.objects.exists():
                NotificationSettings.objects.create()
            
            # Create default ML settings
            if not MLSettings.objects.exists():
                MLSettings.objects.create()
            
            return True
                
        except Exception as e:
            import logging
            logger = logging.getLogger(__name__)
            logger.error(f"Failed to initialize default settings: {e}")
            return False