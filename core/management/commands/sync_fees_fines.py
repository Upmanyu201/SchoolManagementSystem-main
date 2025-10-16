from django.core.management.base import BaseCommand
from django.db import transaction
from core.fee_management.services import fee_service
from students.models import Student
import logging

logger = logging.getLogger(__name__)

class Command(BaseCommand):
    help = 'Auto-detect and apply new fees and fines to students'

    def add_arguments(self, parser):
        parser.add_argument(
            '--student-id',
            type=int,
            help='Sync fees/fines for specific student ID'
        )
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Show what would be applied without making changes'
        )

    def handle(self, *args, **options):
        student_id = options.get('student_id')
        dry_run = options.get('dry_run')
        
        self.stdout.write(
            self.style.SUCCESS('Starting fee and fine synchronization...')
        )
        
        try:
            if student_id:
                student = Student.objects.get(id=student_id)
                students = [student]
                self.stdout.write(f'Processing student: {student.admission_number}')
            else:
                students = Student.objects.all()
                self.stdout.write(f'Processing {students.count()} students')
            
            if dry_run:
                self.stdout.write(self.style.WARNING('DRY RUN MODE - No changes will be made'))
                return
            
            total_applied = 0
            
            with transaction.atomic():
                for student in students:
                    if fee_service:
                        result = fee_service.sync_all_fees_and_fines(student)
                        
                        if result['success']:
                            applied_count = result['total_applied']
                            total_applied += applied_count
                            
                            if applied_count > 0:
                                self.stdout.write(
                                    f'Applied {applied_count} items to {student.admission_number}'
                                )
                    else:
                        self.stdout.write(
                            self.style.ERROR('Fee service not available')
                        )
                        return
            
            self.stdout.write(
                self.style.SUCCESS(
                    f'Successfully applied {total_applied} fees/fines across all students'
                )
            )
            
        except Student.DoesNotExist:
            self.stdout.write(
                self.style.ERROR(f'Student with ID {student_id} not found')
            )
        except Exception as e:
            self.stdout.write(
                self.style.ERROR(f'Error during synchronization: {str(e)}')
            )