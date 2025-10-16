from django.core.management.base import BaseCommand
from django.db import transaction, connection
from student_fees.models import FeeDeposit
from students.models import Student

class Command(BaseCommand):
    help = 'Clear all payment records and reset carry forward amounts to 0.00'

    def handle(self, *args, **options):
        cursor = connection.cursor()
        
        # Count records before deletion
        fee_deposit_count = FeeDeposit.objects.count()
        
        # Direct SQL deletion to ensure it works
        cursor.execute("DELETE FROM student_fees_feedeposit")
        
        # Clear fee_management tables if they exist
        try:
            cursor.execute("DELETE FROM fee_management_paymentallocation")
            cursor.execute("DELETE FROM fee_management_studentfee")
            cursor.execute("DELETE FROM fee_management_appliedfine")
        except:
            pass
        
        # Reset due_amount to 0.00 for all students
        cursor.execute("UPDATE students_student SET due_amount = 0.00")
        
        # Commit changes
        connection.commit()
        
        # Verify deletion
        remaining_count = FeeDeposit.objects.count()
        
        self.stdout.write(
            self.style.SUCCESS(
                f'Successfully cleared {fee_deposit_count} payment records '
                f'(remaining: {remaining_count}) and reset carry forward amounts.'
            )
        )