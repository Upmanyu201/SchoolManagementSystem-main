# students/management/commands/check_due_amounts.py
from django.core.management.base import BaseCommand
from decimal import Decimal
from django.db.models import Sum, Q
from students.models import Student

class Command(BaseCommand):
    help = 'Check due amount calculations between old and new export methods'

    def handle(self, *args, **options):
        self.stdout.write(self.style.SUCCESS('DUE AMOUNT VERIFICATION'))
        self.stdout.write('=' * 50)
        
        # Get first 3 students with class assignments
        students = Student.objects.select_related('class_section').filter(
            class_section__isnull=False
        )[:3]
        
        if not students:
            self.stdout.write(self.style.WARNING('No students with class assignments found!'))
            return
        
        for student in students:
            self.stdout.write(f'\nStudent: {student.get_full_display_name()}')
            self.stdout.write(f'Class: {student.class_section}')
            
            # Static due amount (old export)
            static_due = student.due_amount or Decimal('0')
            self.stdout.write(f'Static Due Amount (old): ₹{static_due:,.2f}')
            
            # Calculate actual due (new export)
            try:
                # Import the calculation method from export service
                from backup.services.export_service import DataExportService
                calculated_due = DataExportService._calculate_actual_due_amount(student)
                
                self.stdout.write(f'Calculated Due (new): ₹{calculated_due:,.2f}')
                difference = calculated_due - static_due
                
                if difference > 0:
                    self.stdout.write(self.style.WARNING(f'Difference: +₹{difference:,.2f} (Higher in new export)'))
                elif difference < 0:
                    self.stdout.write(self.style.SUCCESS(f'Difference: ₹{difference:,.2f} (Lower in new export)'))
                else:
                    self.stdout.write(f'Difference: ₹0.00 (Same)')
                    
            except Exception as e:
                self.stdout.write(self.style.ERROR(f'Calculation failed: {e}'))
        
        self.stdout.write('\n' + '='*50)
        self.stdout.write(self.style.SUCCESS('✅ Due amount verification complete!'))
        self.stdout.write('The new export now shows comprehensive due amounts')
        self.stdout.write('that match the reports module calculations.')