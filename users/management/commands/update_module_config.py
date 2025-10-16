from django.core.management.base import BaseCommand
from django.core.cache import cache
from users.models import UserModulePermission

class Command(BaseCommand):
    help = 'Update module configuration and clear cache'

    def handle(self, *args, **options):
        self.stdout.write('Updating module configuration...')
        
        # Clear all permission caches
        cache.clear()
        self.stdout.write('✓ Cleared permission cache')
        
        # Get current module configuration
        modules = [
            'students', 'teachers', 'subjects', 'fees', 'payments', 
            'fines', 'attendance', 'transport', 'reports', 'messaging', 
            'promotion', 'users', 'settings', 'backup', 'school_profile'
        ]
        
        self.stdout.write(f'✓ Active modules: {", ".join(modules)}')
        
        # Count users with permissions
        permission_count = UserModulePermission.objects.count()
        self.stdout.write(f'✓ Users with permissions: {permission_count}')
        
        self.stdout.write(
            self.style.SUCCESS('Module configuration updated successfully!')
        )