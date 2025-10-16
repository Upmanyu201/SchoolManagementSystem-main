"""
Backup app configuration
"""

from django.apps import AppConfig


class BackupConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'backup'
    verbose_name = 'Backup System'
    
    def ready(self):
        """Initialize backup system when app is ready"""
        # Import signal handlers
        try:
            from . import signals
        except ImportError:
            pass
        
        # Initialize Phase 4 components
        self.initialize_phase4_components()
    
    def initialize_phase4_components(self):
        """Initialize Phase 4 advanced components"""
        try:
            # Initialize monitoring
            from .monitoring import BackupMonitor
            monitor = BackupMonitor()
            
            # Initialize scheduler if Celery is available
            try:
                from .scheduler import BackupScheduler
                scheduler = BackupScheduler()
            except ImportError:
                pass  # Celery not available
                
        except Exception:
            pass  # Phase 4 components not fully configured