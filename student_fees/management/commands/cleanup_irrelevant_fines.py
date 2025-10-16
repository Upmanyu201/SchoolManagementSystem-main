"""
Management command to clean up irrelevant fine records for all students
"""
from django.core.management.base import BaseCommand
from students.models import Student
from student_fees.promotion_utils import cleanup_irrelevant_fines_after_promotion

class Command(BaseCommand):
    help = 'Clean up irrelevant fine records for all students based on their current class'

    def add_arguments(self, parser):
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Show what would be cleaned up without actually doing it',
        )

    def handle(self, *args, **options):
        dry_run = options['dry_run']
        
        if dry_run:
            self.stdout.write(self.style.WARNING('DRY RUN MODE - No changes will be made'))
        
        students = Student.objects.select_related('class_section').all()
        total_removed = 0
        
        for student in students:
            if dry_run:
                # Just count what would be removed
                from fines.models import FineStudent
                irrelevant_fines = FineStudent.objects.filter(
                    student=student,
                    is_paid=False,
                    fine__is_active=True,
                    fine__target_scope='Class'
                ).select_related('fine', 'fine__class_section')
                
                count = sum(1 for fs in irrelevant_fines if fs.fine.class_section != student.class_section)
                if count > 0:
                    self.stdout.write(f'Student {student.admission_number}: {count} irrelevant fines would be removed')
                total_removed += count
            else:
                removed = cleanup_irrelevant_fines_after_promotion(student)
                if removed > 0:
                    self.stdout.write(f'Student {student.admission_number}: {removed} irrelevant fines removed')
                total_removed += removed
        
        if dry_run:
            self.stdout.write(self.style.SUCCESS(f'Total fines that would be removed: {total_removed}'))
        else:
            self.stdout.write(self.style.SUCCESS(f'Successfully cleaned up {total_removed} irrelevant fine records'))