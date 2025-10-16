from django.core.management.base import BaseCommand
from django.utils import timezone
from datetime import date
from fees.models import FeesType
from students.models import Student
import logging

logger = logging.getLogger(__name__)

class Command(BaseCommand):
    help = 'Apply due fees to student accounts'

    def handle(self, *args, **options):
        today = date.today()
        
        # Get all active fees that should be applied
        due_fees = FeesType.objects.filter(
            is_active=True
        )
        
        updated_count = 0
        
        # Update all student due amounts to reflect current fees
        students = Student.objects.all()
        
        for student in students:
            student.update_due_amount()
            updated_count += 1
        
        self.stdout.write(
            self.style.SUCCESS(f'Updated due amounts for {updated_count} students')
        )