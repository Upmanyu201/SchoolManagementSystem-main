from django.core.management.base import BaseCommand
from django.db import transaction
from decimal import Decimal
from students.models import Student
from student_fees.models import FeeDeposit
from fees.models import FeesType
from fines.models import Fine, FineStudent
from transport.models import TransportAssignment
from django.db.models import Sum, Q

class Command(BaseCommand):
    help = 'Fix fees and fines calculation for all students'

    def add_arguments(self, parser):
        parser.add_argument(
            '--apply',
            action='store_true',
            help='Apply the corrections to database',
        )

    def handle(self, *args, **options):
        self.stdout.write("Starting Fee and Fine Calculation Fix...")
        
        # Step 1: Fix incorrect fines
        self.fix_incorrect_fines()
        
        # Step 2: Calculate all students
        results = self.calculate_all_students()
        
        # Step 3: Show sample results
        self.print_sample_results(results, 20)
        
        # Step 4: Show summary
        self.print_summary(results)
        
        # Step 5: Apply corrections if requested
        if options['apply']:
            self.apply_corrections(results)
            self.stdout.write("All corrections applied successfully!")
        else:
            self.stdout.write("Use --apply flag to save changes to database")

    def get_applicable_fees(self, student):
        """Get all applicable fees for a student"""
        fees = []
        
        # 1. Class-based tuition fees
        tuition_fees = FeesType.objects.filter(
            fee_group__group_type='Tuition Fee',
            class_name=student.class_section.class_name if student.class_section else ''
        )
        fees.extend(tuition_fees)
        
        # 2. General fees
        general_fees = FeesType.objects.filter(
            fee_group__group_type__in=['Admission Fees', 'Exam Fees', 'Development']
        )
        fees.extend(general_fees)
        
        # 3. Transport fees (if assigned)
        transport_assignment = TransportAssignment.objects.filter(student=student).first()
        if transport_assignment:
            transport_fees = FeesType.objects.filter(
                fee_group__group_type='Transport',
                related_stoppage=transport_assignment.stoppage
            )
            fees.extend(transport_fees)
        
        return fees

    def calculate_student_dues(self, student):
        """Calculate correct due amount for a student"""
        # Get applicable fees
        applicable_fees = self.get_applicable_fees(student)
        total_fees = sum(fee.amount for fee in applicable_fees)
        
        # Get total payments
        payments = FeeDeposit.objects.filter(student=student)
        total_paid = payments.aggregate(Sum('paid_amount'))['paid_amount__sum'] or Decimal('0')
        total_discount = payments.aggregate(Sum('discount'))['discount__sum'] or Decimal('0')
        
        # Get unpaid fines
        unpaid_fines = FineStudent.objects.filter(
            student=student, 
            is_paid=False
        ).select_related('fine')
        total_fines = sum(fs.fine.amount for fs in unpaid_fines)
        
        # Calculate due amount
        due_amount = total_fees - total_paid - total_discount + total_fines
        due_amount = max(due_amount, Decimal('0'))  # Cannot be negative
        
        return {
            'student_id': student.id,
            'student_name': student.get_full_display_name(),
            'class_name': student.class_section.class_name if student.class_section else 'Unknown',
            'total_fees': total_fees,
            'total_paid': total_paid,
            'total_discount': total_discount,
            'total_fines': total_fines,
            'calculated_due': due_amount,
            'current_due': student.due_amount,
            'applicable_fees': [f"{fee.fee_type}: Rs{fee.amount}" for fee in applicable_fees],
            'unpaid_fines': [f"{fs.fine.fine_type.name}: Rs{fs.fine.amount}" for fs in unpaid_fines]
        }

    def fix_incorrect_fines(self):
        """Remove incorrectly applied fines"""
        self.stdout.write("Checking for incorrectly applied fines...")
        
        # Fine ID 5 was applied to ALL students - check if they actually have unpaid fees
        fine_5 = Fine.objects.filter(id=5).first()
        if fine_5:
            incorrect_applications = []
            fine_students = FineStudent.objects.filter(fine=fine_5, is_paid=False)
            
            for fs in fine_students:
                student = fs.student
                calc = self.calculate_student_dues(student)
                
                # If student has no actual unpaid fees (excluding this fine), remove the fine
                if calc['total_fees'] <= calc['total_paid'] + calc['total_discount']:
                    incorrect_applications.append(fs)
            
            if incorrect_applications:
                self.stdout.write(f"Found {len(incorrect_applications)} incorrectly applied fines")
                # Remove incorrect fine applications
                for fs in incorrect_applications:
                    fs.delete()
                self.stdout.write("Removed incorrect fine applications")

    def calculate_all_students(self):
        """Calculate dues for all students"""
        students = Student.objects.all().select_related('class_section')
        results = []
        
        self.stdout.write(f"Calculating dues for {students.count()} students...")
        
        for student in students:
            calc = self.calculate_student_dues(student)
            results.append(calc)
        
        return results

    def apply_corrections(self, results):
        """Apply the corrected due amounts to database"""
        self.stdout.write("Applying corrections to database...")
        
        with transaction.atomic():
            corrections_made = 0
            for result in results:
                student = Student.objects.get(id=result['student_id'])
                if student.due_amount != result['calculated_due']:
                    student.due_amount = result['calculated_due']
                    student.save()
                    corrections_made += 1
            
            self.stdout.write(f"Applied corrections to {corrections_made} students")

    def print_sample_results(self, results, limit=20):
        """Print sample results for verification"""
        self.stdout.write(f"\nSample Results (First {limit} students):")
        self.stdout.write("=" * 120)
        self.stdout.write(f"{'Student':<25} {'Class':<8} {'Total Fees':<12} {'Paid':<10} {'Discount':<10} {'Fines':<8} {'Due':<10} {'Current':<10}")
        self.stdout.write("=" * 120)
        
        for i, result in enumerate(results[:limit]):
            self.stdout.write(f"{result['student_name'][:24]:<25} "
                  f"{result['class_name']:<8} "
                  f"Rs{result['total_fees']:<10} "
                  f"Rs{result['total_paid']:<8} "
                  f"Rs{result['total_discount']:<8} "
                  f"Rs{result['total_fines']:<6} "
                  f"Rs{result['calculated_due']:<8} "
                  f"Rs{result['current_due']:<8}")
        
        self.stdout.write("=" * 120)

    def print_summary(self, results):
        """Print calculation summary"""
        if not results:
            return
        
        total_fees = sum(r['total_fees'] for r in results)
        total_paid = sum(r['total_paid'] for r in results)
        total_discount = sum(r['total_discount'] for r in results)
        total_fines = sum(r['total_fines'] for r in results)
        total_due = sum(r['calculated_due'] for r in results)
        
        corrections_needed = sum(1 for r in results if r['calculated_due'] != r['current_due'])
        
        self.stdout.write(f"\nCALCULATION SUMMARY:")
        self.stdout.write(f"Total Students: {len(results)}")
        self.stdout.write(f"Total Fees: Rs{total_fees:,.2f}")
        self.stdout.write(f"Total Paid: Rs{total_paid:,.2f}")
        self.stdout.write(f"Total Discount: Rs{total_discount:,.2f}")
        self.stdout.write(f"Total Fines: Rs{total_fines:,.2f}")
        self.stdout.write(f"Total Due: Rs{total_due:,.2f}")
        self.stdout.write(f"Students needing correction: {corrections_needed}")