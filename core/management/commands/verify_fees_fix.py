from django.core.management.base import BaseCommand
from students.models import Student
from student_fees.models import FeeDeposit
from fines.models import FineStudent
from django.db.models import Sum

class Command(BaseCommand):
    help = 'Verify the fees calculation fix'

    def handle(self, *args, **options):
        self.stdout.write("Verifying Fee Calculation Fix...")
        
        # Check a few specific students
        test_students = [
            'GVIS00001',  # SURBHI KUMARI
            'GVIS00002',  # ARYAN KUMAR  
            'demo',       # Student 108 with payments
        ]
        
        self.stdout.write("\nDetailed Verification for Key Students:")
        self.stdout.write("=" * 80)
        
        for admission_no in test_students:
            try:
                student = Student.objects.get(admission_number=admission_no)
                self.verify_student(student)
            except Student.DoesNotExist:
                self.stdout.write(f"Student {admission_no} not found")
        
        # Overall statistics
        self.print_overall_stats()

    def verify_student(self, student):
        # Get payments
        payments = FeeDeposit.objects.filter(student=student)
        total_paid = payments.aggregate(Sum('paid_amount'))['paid_amount__sum'] or 0
        total_discount = payments.aggregate(Sum('discount'))['discount__sum'] or 0
        
        # Get fines
        unpaid_fines = FineStudent.objects.filter(student=student, is_paid=False)
        total_fines = sum(fs.fine.amount for fs in unpaid_fines)
        
        self.stdout.write(f"\nStudent: {student.get_full_display_name()}")
        self.stdout.write(f"Class: {student.student_class.name}")
        self.stdout.write(f"Current Due Amount: Rs{student.due_amount}")
        self.stdout.write(f"Total Paid: Rs{total_paid}")
        self.stdout.write(f"Total Discount: Rs{total_discount}")
        self.stdout.write(f"Unpaid Fines: Rs{total_fines}")
        
        if payments.exists():
            self.stdout.write("Payment Details:")
            for payment in payments:
                self.stdout.write(f"  - {payment.fees_type.fee_type if payment.fees_type else 'General'}: Rs{payment.paid_amount}")

    def print_overall_stats(self):
        self.stdout.write("\n" + "=" * 80)
        self.stdout.write("OVERALL STATISTICS AFTER FIX:")
        
        students = Student.objects.all()
        total_students = students.count()
        
        # Due amount distribution
        zero_due = students.filter(due_amount=0).count()
        small_due = students.filter(due_amount__gt=0, due_amount__lte=100).count()
        medium_due = students.filter(due_amount__gt=100, due_amount__lte=5000).count()
        large_due = students.filter(due_amount__gt=5000).count()
        
        total_due = sum(s.due_amount for s in students)
        
        self.stdout.write(f"Total Students: {total_students}")
        self.stdout.write(f"Students with Rs0 due: {zero_due}")
        self.stdout.write(f"Students with Rs1-100 due: {small_due}")
        self.stdout.write(f"Students with Rs101-5000 due: {medium_due}")
        self.stdout.write(f"Students with Rs5000+ due: {large_due}")
        self.stdout.write(f"Total Due Amount: Rs{total_due:,.2f}")
        
        # Check if the fix worked
        if medium_due + large_due > 90:  # Most students should have significant dues (>Rs100)
            self.stdout.write("SUCCESS: Fee calculation fix appears to be working correctly!")
            self.stdout.write(f"- {medium_due} students have dues between Rs101-5000")
            self.stdout.write(f"- {large_due} students have dues above Rs5000")
            self.stdout.write(f"- Only {zero_due} student has Rs0 due (likely paid all fees)")
        else:
            self.stdout.write("WARNING: Most students still have low due amounts - fix may not be complete")