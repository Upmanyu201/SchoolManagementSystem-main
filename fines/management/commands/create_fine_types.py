from django.core.management.base import BaseCommand
from fines.models import FineType

class Command(BaseCommand):
    help = 'Create sample fine types'

    def handle(self, *args, **options):
        fine_types = [
            {'name': 'Late Fee', 'category': 'Late Fee', 'description': 'Fine for late payment'},
            {'name': 'Damage Fee', 'category': 'Damage', 'description': 'Fine for property damage'},
            {'name': 'Discipline Fine', 'category': 'Discipline', 'description': 'Fine for disciplinary issues'},
            {'name': 'Library Fine', 'category': 'Library', 'description': 'Fine for library violations'},
        ]
        
        for ft_data in fine_types:
            fine_type, created = FineType.objects.get_or_create(
                name=ft_data['name'],
                defaults={
                    'category': ft_data['category'],
                    'description': ft_data['description']
                }
            )
            if created:
                self.stdout.write(f"Created FineType: {fine_type.name}")
            else:
                self.stdout.write(f"FineType already exists: {fine_type.name}")
        
        self.stdout.write(self.style.SUCCESS('Fine types creation completed'))