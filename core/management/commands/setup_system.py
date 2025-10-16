from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from fines.models import FineType

User = get_user_model()

class Command(BaseCommand):
    help = 'Setup system user and default fine types'

    def handle(self, *args, **options):
        # Create system user
        system_user, created = User.objects.get_or_create(
            username='system',
            defaults={
                'email': 'system@school.local',
                'is_active': False,
                'is_staff': False,
                'first_name': 'System',
                'last_name': 'User'
            }
        )
        
        if created:
            self.stdout.write(self.style.SUCCESS('Created system user'))
        else:
            self.stdout.write('System user already exists')

        # Create default fine types
        fine_types = [
            {'name': 'Late Fee', 'category': 'Late Fee', 'description': 'Late payment fee'},
            {'name': 'Damage Fee', 'category': 'Damage', 'description': 'Property damage fee'},
            {'name': 'Library Fine', 'category': 'Library', 'description': 'Library book fine'},
            {'name': 'Discipline Fine', 'category': 'Discipline', 'description': 'Disciplinary fine'},
        ]

        for fine_type_data in fine_types:
            fine_type, created = FineType.objects.get_or_create(
                name=fine_type_data['name'],
                defaults=fine_type_data
            )
            if created:
                self.stdout.write(self.style.SUCCESS(f'Created fine type: {fine_type.name}'))

        self.stdout.write(self.style.SUCCESS('System setup completed'))