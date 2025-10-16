from django.core.management.base import BaseCommand
from django.contrib.auth.models import User
from users.models import UserModulePermission

class Command(BaseCommand):
    """2025 Industry Standard: Management command to setup module permissions"""
    
    help = 'Setup module permissions for existing users and create default permission templates'
    
    def add_arguments(self, parser):
        parser.add_argument(
            '--create-defaults',
            action='store_true',
            help='Create default permission objects for all non-superuser accounts',
        )
        parser.add_argument(
            '--reset-all',
            action='store_true',
            help='Reset all existing permissions (dangerous)',
        )
        parser.add_argument(
            '--template',
            type=str,
            choices=['teacher', 'accountant', 'admin_staff'],
            help='Apply permission template to all users',
        )
    
    def handle(self, *args, **options):
        if options['reset_all']:
            self.reset_all_permissions()
        
        if options['create_defaults']:
            self.create_default_permissions()
        
        if options['template']:
            self.apply_template(options['template'])
    
    def reset_all_permissions(self):
        """Reset all module permissions"""
        count = UserModulePermission.objects.count()
        UserModulePermission.objects.all().delete()
        self.stdout.write(
            self.style.WARNING(f'Reset {count} permission records')
        )
    
    def create_default_permissions(self):
        """Create default permission objects for users without them"""
        users_without_permissions = User.objects.filter(
            is_superuser=False,
            is_active=True,
            module_permissions__isnull=True
        )
        
        created_count = 0
        for user in users_without_permissions:
            UserModulePermission.objects.create(user=user)
            created_count += 1
        
        self.stdout.write(
            self.style.SUCCESS(f'Created default permissions for {created_count} users')
        )
    
    def apply_template(self, template_name):
        """Apply permission template to all users"""
        templates = {
            'teacher': {
                'students_view': True,
                'attendance_view': True,
                'attendance_edit': True,
                'exams_view': True,
                'results_view': True,
                'results_edit': True,
            },
            'accountant': {
                'fees_view': True,
                'fees_edit': True,
                'payments_view': True,
                'payments_edit': True,
                'reports_view': True,
            },
            'admin_staff': {
                'students_view': True,
                'students_edit': True,
                'teachers_view': True,
                'classes_view': True,
                'transport_view': True,
                'transport_edit': True,
                'reports_view': True,
            }
        }
        
        if template_name not in templates:
            self.stdout.write(
                self.style.ERROR(f'Unknown template: {template_name}')
            )
            return
        
        template_data = templates[template_name]
        updated_count = 0
        
        for permission in UserModulePermission.objects.all():
            for field, value in template_data.items():
                setattr(permission, field, value)
            permission.save()
            updated_count += 1
        
        self.stdout.write(
            self.style.SUCCESS(f'Applied {template_name} template to {updated_count} users')
        )