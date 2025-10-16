from django.core.management.base import BaseCommand
from django.db import transaction
from students.models import Student
import logging

logger = logging.getLogger(__name__)

class Command(BaseCommand):
    help = 'Clean up missing student files and broken references'

    def add_arguments(self, parser):
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Show what would be cleaned without making changes',
        )

    def handle(self, *args, **options):
        dry_run = options['dry_run']
        
        self.stdout.write('Checking for missing student files...')
        
        all_students = Student.objects.all()
        total_checked = 0
        missing_files = 0
        cleaned_up = 0
        
        file_fields = ['student_image', 'aadhar_card', 'transfer_certificate']
        
        for student in all_students:
            total_checked += 1
            
            for field_name in file_fields:
                field_value = getattr(student, field_name)
                if field_value:
                    try:
                        # Check if file exists
                        if not field_value.storage.exists(field_value.name):
                            missing_files += 1
                            self.stdout.write(
                                f'Missing {field_name} for {student.admission_number}: {field_value.name}'
                            )
                            
                            if not dry_run:
                                # Clear the broken reference
                                setattr(student, field_name, None)
                                student.save(update_fields=[field_name])
                                cleaned_up += 1
                                
                    except Exception as e:
                        missing_files += 1
                        self.stdout.write(
                            f'Error checking {field_name} for {student.admission_number}: {e}'
                        )
                        
                        if not dry_run:
                            # Clear the broken reference
                            setattr(student, field_name, None)
                            student.save(update_fields=[field_name])
                            cleaned_up += 1
        
        self.stdout.write(f'\nSummary:')
        self.stdout.write(f'Total students checked: {total_checked}')
        self.stdout.write(f'Missing files found: {missing_files}')
        
        if dry_run:
            self.stdout.write(f'Would clean up: {missing_files} broken references')
            self.stdout.write('Run without --dry-run to actually clean up')
        else:
            self.stdout.write(f'Cleaned up: {cleaned_up} broken references')
            self.stdout.write(self.style.SUCCESS('Cleanup completed successfully'))