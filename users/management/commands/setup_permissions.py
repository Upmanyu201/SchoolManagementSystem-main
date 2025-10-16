from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from users.models import UserModulePermission

User = get_user_model()

class Command(BaseCommand):
    help = 'Setup initial module permissions for all users'

    def add_arguments(self, parser):
        parser.add_argument(
            '--grant-all',
            action='store_true',
            help='Grant all permissions to all non-superuser users',
        )
        parser.add_argument(
            '--user',
            type=str,
            help='Grant permissions to specific user (username)',
        )

    def handle(self, *args, **options):
        self.stdout.write('Setting up module permissions...')
        
        # Get all users (excluding superusers)
        if options['user']:
            try:
                users = [User.objects.get(username=options['user'])]
                self.stdout.write(f"Processing user: {options['user']}")
            except User.DoesNotExist:
                self.stdout.write(
                    self.style.ERROR(f"User '{options['user']}' not found")
                )
                return
        else:
            users = User.objects.filter(is_superuser=False)
            self.stdout.write(f"Processing {users.count()} non-superuser accounts")

        created_count = 0
        updated_count = 0

        for user in users:
            permission, created = UserModulePermission.objects.get_or_create(
                user=user,
                defaults=self._get_default_permissions(options['grant_all'])
            )
            
            if created:
                created_count += 1
                self.stdout.write(f"Created permissions for: {user.username}")
            else:
                if options['grant_all']:
                    # Update existing permissions
                    self._update_permissions(permission, grant_all=True)
                    updated_count += 1
                    self.stdout.write(f"Updated permissions for: {user.username}")

        self.stdout.write(
            self.style.SUCCESS(
                f'Successfully processed permissions: '
                f'{created_count} created, {updated_count} updated'
            )
        )

    def _get_default_permissions(self, grant_all=False):
        """Get default permission settings"""
        if grant_all:
            return {
                # Core Academic Modules
                'students_view': True,
                'students_edit': True,
                'teachers_view': True,
                'teachers_edit': True,
                'subjects_view': True,
                'subjects_edit': True,
                
                # Financial Modules
                'fees_view': True,
                'fees_edit': True,
                'payments_view': True,
                'payments_edit': True,
                'fines_view': True,
                'fines_edit': True,
                
                # Academic Operations
                'attendance_view': True,
                'attendance_edit': True,
                'promotion_view': True,
                'promotion_edit': True,
                
                # Administrative
                'transport_view': True,
                'transport_edit': True,
                'reports_view': True,
                'reports_edit': False,  # Reports usually view-only
                'messaging_view': True,
                'messaging_edit': True,
                
                # System (restricted by default)
                'users_view': False,
                'users_edit': False,
                'settings_view': False,
                'settings_edit': False,
                'backup_view': False,
                'backup_edit': False,
                'school_profile_view': True,
                'school_profile_edit': False,
            }
        else:
            # Default: minimal permissions
            return {
                # Basic view access only
                'students_view': True,
                'students_edit': False,
                'teachers_view': True,
                'teachers_edit': False,
                'subjects_view': True,
                'subjects_edit': False,
                
                # Financial - view only
                'fees_view': True,
                'fees_edit': False,
                'payments_view': True,
                'payments_edit': False,
                'fines_view': True,
                'fines_edit': False,
                
                # Academic - view only
                'attendance_view': True,
                'attendance_edit': False,
                'promotion_view': False,
                'promotion_edit': False,
                
                # Administrative - limited
                'transport_view': True,
                'transport_edit': False,
                'reports_view': True,
                'reports_edit': False,
                'messaging_view': False,
                'messaging_edit': False,
                
                # System - no access
                'users_view': False,
                'users_edit': False,
                'settings_view': False,
                'settings_edit': False,
                'backup_view': False,
                'backup_edit': False,
                'school_profile_view': True,
                'school_profile_edit': False,
            }

    def _update_permissions(self, permission, grant_all=False):
        """Update existing permission object"""
        defaults = self._get_default_permissions(grant_all)
        
        for field, value in defaults.items():
            setattr(permission, field, value)
        
        permission.save()