# core/fee_management/processors.py
"""
Centralized Payment Processing Engine
All payment processing and allocation logic
"""

from decimal import Decimal
from django.db import transaction
from django.utils import timezone
from django.core.exceptions import ValidationError
from django.utils.html import escape
from core.security_utils import sanitize_input, generate_secure_filename
from datetime import date
import os
import logging

logger = logging.getLogger(__name__)

class PaymentProcessor:
    """Main payment processing engine"""
    
    @transaction.atomic
    def process_payment(self, student, amount, payment_data):
        """Process payment and allocate to fees/fines with security validation"""
        from student_fees.models import FeeDeposit
        from .models import PaymentAllocation
        from .calculators import FeeCalculator
        
        # Validate inputs
        if not student or not amount:
            raise ValidationError("Invalid student or amount")
        
        # Sanitize payment data
        safe_payment_data = {
            'payment_mode': sanitize_input(payment_data.get('payment_mode', 'Cash'))[:20],
            'transaction_no': sanitize_input(payment_data.get('transaction_no', ''))[:50],
            'note': sanitize_input(payment_data.get('note', ''))[:200]
        }
        
        # Validate amount
        try:
            amount = Decimal(str(amount))
            if amount < 0 or amount > Decimal('999999.99'):
                raise ValidationError("Invalid payment amount")
        except (ValueError, TypeError):
            raise ValidationError("Invalid amount format")
        
        # Create fee deposit record with sanitized data
        fee_deposit = FeeDeposit.objects.create(
            student=student,
            amount=amount,
            paid_amount=amount,
            receipt_no=self._generate_receipt_number(),
            payment_mode=safe_payment_data['payment_mode'],
            transaction_no=safe_payment_data['transaction_no'],
            note=safe_payment_data['note']
        )
        
        # Allocate payment to fees and fines
        remaining_amount = Decimal(str(amount))
        allocations = []
        
        # Get payment breakdown
        calculator = FeeCalculator()
        breakdown = calculator.get_payment_breakdown(student)
        
        # First, pay fines (higher priority)
        for fine in breakdown['fines']:
            if remaining_amount < 0:
                break
                
            allocation_amount = min(remaining_amount, fine.amount)
            
            # Create allocation record
            allocation = PaymentAllocation.objects.create(
                fee_deposit=fee_deposit,
                applied_fine=fine,
                allocated_amount=allocation_amount
            )
            allocations.append(allocation)
            
            # Update fine status
            if allocation_amount >= fine.amount:
                fine.is_paid = True
                fine.paid_date = date.today()
                fine.save()
            
            remaining_amount -= allocation_amount
        
        # Then, pay fees
        for fee in breakdown['fees']:
            if remaining_amount < 0:
                break
                
            allocation_amount = min(remaining_amount, fee.amount)
            
            # Create allocation record
            allocation = PaymentAllocation.objects.create(
                fee_deposit=fee_deposit,
                student_fee=fee,
                allocated_amount=allocation_amount
            )
            allocations.append(allocation)
            
            # Update fee status
            if allocation_amount >= fee.amount:
                fee.is_paid = True
                fee.paid_date = date.today()
                fee.save()
            
            remaining_amount -= allocation_amount
        
        # Update student's due amount (if method exists)
        if hasattr(student, 'update_due_amount'):
            student.update_due_amount()
        
        return {
            'success': True,
            'fee_deposit': fee_deposit,
            'allocations': allocations,
            'remaining_amount': remaining_amount,
            'message': f'Payment of ₹{escape(str(amount))} processed successfully'
        }
    
    def _generate_receipt_number(self):
        """Generate secure unique receipt number"""
        from student_fees.models import FeeDeposit
        import uuid
        
        try:
            # Get current year
            year = timezone.now().year
            
            # Get next sequence number with error handling
            last_receipt = FeeDeposit.objects.filter(
                receipt_no__startswith=f'REC{year}'
            ).order_by('-id').first()
            
            if last_receipt:
                try:
                    last_num = int(last_receipt.receipt_no[-4:])
                    next_num = last_num + 1
                except (ValueError, IndexError):
                    next_num = 1
            else:
                next_num = 1
            
            # Add UUID for additional uniqueness and security
            unique_suffix = uuid.uuid4().hex[:4].upper()
            return f'REC{year}{next_num:04d}{unique_suffix}'
            
        except Exception as e:
            logger.error(f"Error generating receipt number: {sanitize_input(str(e))}")
            # Fallback to UUID-based receipt number
            return f'REC{timezone.now().year}{uuid.uuid4().hex[:8].upper()}'
    
    def get_payment_history(self, student, limit=10):
        """Get payment history for student"""
        from student_fees.models import FeeDeposit
        
        payments = FeeDeposit.objects.filter(
            student=student
        ).order_by('-deposit_date')[:limit]
        
        history = []
        for payment in payments:
            allocations = payment.allocations.all()
            
            history.append({
                'payment': payment,
                'allocations': allocations,
                'allocated_to_fees': sum(
                    alloc.allocated_amount for alloc in allocations 
                    if alloc.student_fee
                ),
                'allocated_to_fines': sum(
                    alloc.allocated_amount for alloc in allocations 
                    if alloc.applied_fine
                )
            })
        
        return history
    
    def calculate_refund(self, fee_deposit):
        """Calculate refund amount if needed"""
        total_allocated = fee_deposit.allocations.aggregate(
            total=models.Sum('allocated_amount')
        )['total'] or Decimal('0')
        
        return fee_deposit.paid_amount - total_allocated

class DiscountProcessor:
    """Handle discounts and scholarships"""
    
    def apply_discount(self, student, discount_type, discount_value):
        """Apply discount to student fees"""
        from .models import StudentFee
        
        unpaid_fees = StudentFee.objects.filter(
            student=student,
            is_paid=False
        )
        
        for fee in unpaid_fees:
            if discount_type == 'percentage':
                discount_amount = (fee.amount * Decimal(str(discount_value))) / 100
            else:  # fixed amount
                discount_amount = Decimal(str(discount_value))
            
            # Apply discount (reduce fee amount)
            fee.amount = max(Decimal('0'), fee.amount - discount_amount)
            fee.save()
        
        return f"Discount applied to {sanitize_input(str(len(unpaid_fees)))} fees"
    
    def apply_scholarship(self, student, scholarship_percentage):
        """Apply scholarship to all student fees"""
        return self.apply_discount(student, 'percentage', scholarship_percentage)