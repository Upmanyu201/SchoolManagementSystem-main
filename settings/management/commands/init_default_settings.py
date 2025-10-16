# settings/management/commands/init_default_settings.py
from django.core.management.base import BaseCommand
from django.db import transaction
from settings.apps import SettingsConfig
import logging

logger = logging.getLogger(__name__)

class Command(BaseCommand):
    help = 'Initialize default system settings safely'
    
    def add_arguments(self, parser):
        parser.add_argument(
            '--force',
            action='store_true',
            help='Force initialization even if settings exist',
        )
    
    def handle(self, *args, **options):
        """Initialize default settings safely after Django is ready"""
        
        self.stdout.write('Initializing default system settings...')
        
        try:
            with transaction.atomic():
                success = SettingsConfig.initialize_default_settings()
                
                if success:
                    self.stdout.write(
                        self.style.SUCCESS('✅ Default settings initialized successfully!')
                    )
                else:
                    self.stdout.write(
                        self.style.WARNING('⚠️ Settings initialization skipped (Django not ready)')
                    )
                    
        except Exception as e:
            self.stdout.write(
                self.style.ERROR(f'❌ Failed to initialize settings: {e}')
            )
            logger.error(f'Settings initialization failed: {e}')
            
        # Also check and report current settings status
        try:
            from settings.models import SystemSettings, NotificationSettings, MLSettings
            
            system_count = SystemSettings.objects.count()
            notification_count = NotificationSettings.objects.count()
            ml_count = MLSettings.objects.count()
            
            self.stdout.write(f'\n📊 Current Settings Status:')
            self.stdout.write(f'   • System Settings: {system_count} records')
            self.stdout.write(f'   • Notification Settings: {notification_count} records')
            self.stdout.write(f'   • ML Settings: {ml_count} records')
            
        except Exception as e:
            self.stdout.write(f'⚠️ Could not check settings status: {e}')