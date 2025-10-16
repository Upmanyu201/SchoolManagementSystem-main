from decimal import Decimal
from django.db.models import Sum
from fees.models import FeesType
from fines.models import FineStudent
from transport.models import TransportAssignment

def calculate_student_due_amount(student):
    """Calculate the correct due amount for a student"""
    # Get applicable fees
    applicable_fees = []
    
    # 1. Class-based tuition fees
    tuition_fees = FeesType.objects.filter(
        fee_group__group_type='Tuition Fee',
        class_name=student.student_class.name
    )
    applicable_fees.extend(tuition_fees)
    
    # 2. General fees
    general_fees = FeesType.objects.filter(
        fee_group__group_type__in=['Admission Fees', 'Exam Fees', 'Development']
    )
    applicable_fees.extend(general_fees)
    
    # 3. Transport fees (if assigned)
    transport_assignment = TransportAssignment.objects.filter(student=student).first()
    if transport_assignment:
        transport_fees = FeesType.objects.filter(
            fee_group__group_type='Transport',
            related_stoppage=transport_assignment.stoppage
        )
        applicable_fees.extend(transport_fees)
    
    # Calculate total fees
    total_fees = sum(fee.amount for fee in applicable_fees)
    
    # Get total payments and discounts
    from student_fees.models import FeeDeposit
    payments = FeeDeposit.objects.filter(student=student)
    total_paid = payments.aggregate(Sum('paid_amount'))['paid_amount__sum'] or Decimal('0')
    total_discount = payments.aggregate(Sum('discount'))['discount__sum'] or Decimal('0')
    
    # Get unpaid fines
    unpaid_fines = FineStudent.objects.filter(student=student, is_paid=False, fine__is_active=True)
    total_fines = sum(fs.fine.amount for fs in unpaid_fines)
    
    # Calculate due amount
    due_amount = total_fees - total_paid - total_discount + total_fines
    return max(due_amount, Decimal('0'))  # Cannot be negative

def get_student_fee_breakdown(student):
    """Get detailed fee breakdown for a student"""
    from student_fees.models import FeeDeposit
    
    # Get applicable fees
    applicable_fees = []
    
    # Class-based tuition fees
    tuition_fees = FeesType.objects.filter(
        fee_group__group_type='Tuition Fee',
        class_name=student.student_class.name
    )
    applicable_fees.extend(tuition_fees)
    
    # General fees
    general_fees = FeesType.objects.filter(
        fee_group__group_type__in=['Admission Fees', 'Exam Fees', 'Development']
    )
    applicable_fees.extend(general_fees)
    
    # Transport fees
    transport_assignment = TransportAssignment.objects.filter(student=student).first()
    if transport_assignment:
        transport_fees = FeesType.objects.filter(
            fee_group__group_type='Transport',
            related_stoppage=transport_assignment.stoppage
        )
        applicable_fees.extend(transport_fees)
    
    # Get payments
    payments = FeeDeposit.objects.filter(student=student)
    total_paid = payments.aggregate(Sum('paid_amount'))['paid_amount__sum'] or Decimal('0')
    total_discount = payments.aggregate(Sum('discount'))['discount__sum'] or Decimal('0')
    
    # Get fines
    unpaid_fines = FineStudent.objects.filter(student=student, is_paid=False, fine__is_active=True)
    total_fines = sum(fs.fine.amount for fs in unpaid_fines)
    
    return {
        'applicable_fees': applicable_fees,
        'total_fees': sum(fee.amount for fee in applicable_fees),
        'total_paid': total_paid,
        'total_discount': total_discount,
        'total_fines': total_fines,
        'due_amount': calculate_student_due_amount(student),
        'payments': payments,
        'unpaid_fines': unpaid_fines
    }
def generate_receipt_no():
    """Generate unique receipt number: REC-4DigitRandomUniqueCombinations"""
    from student_fees.models import FeeDeposit
    import random
    import time
    
    max_attempts = 50
    
    for attempt in range(max_attempts):
        # Generate 4-digit random number
        random_digits = random.randint(1000, 9999)
        receipt_no = f"REC-{random_digits}"
        
        # Check uniqueness
        if not FeeDeposit.objects.filter(receipt_no=receipt_no).exists():
            return receipt_no
            
        # Small delay to avoid collision
        time.sleep(random.uniform(0.001, 0.01))
    
    # Fallback: Use timestamp-based 4 digits if all random attempts fail
    timestamp_digits = str(int(time.time()))[-4:]  # Last 4 digits of timestamp
    fallback_receipt = f"REC-{timestamp_digits}"
    
    return fallback_receipt