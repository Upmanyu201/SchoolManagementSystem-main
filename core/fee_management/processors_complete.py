# core/fee_management/processors_complete.py
"""
Complete Payment Processing Engine
All payment processing and allocation logic
"""

from decimal import Decimal
from django.db import transaction, models
from django.utils import timezone
from datetime import date
from .validators import FeeValidator
from .exceptions import PaymentProcessingError
from .utils import generate_receipt_number, invalidate_student_cache
import logging

logger = logging.getLogger(__name__)

class PaymentProcessor:
    """Complete payment processing engine"""
    
    @transaction.atomic
    def process_payment(self, student, amount, payment_data):
        """Process payment and allocate to fees/fines"""
        try:
            # Validate inputs
            FeeValidator.validate_student_eligibility(student)
            validated_amount = FeeValidator.validate_payment_amount(amount)
            
            from student_fees.models import FeeDeposit
            from .models import PaymentAllocation
            from .calculators import FeeCalculator
            
            # Generate receipt number
            receipt_no = generate_receipt_number()
            
            # Create fee deposit record
            fee_deposit = FeeDeposit.objects.create(
                student=student,
                amount=validated_amount,
                paid_amount=validated_amount,
                receipt_no=receipt_no,
                payment_mode=payment_data.get('payment_mode', 'Cash'),
                transaction_no=payment_data.get('transaction_no', ''),
                note=payment_data.get('note', '')
            )
            
            # Allocate payment to fees and fines
            remaining_amount = validated_amount
            allocations = []
            
            # Get payment breakdown
            calculator = FeeCalculator()
            breakdown = calculator.get_payment_breakdown(student)
            
            # Priority 1: Pay fines first
            for fine in breakdown['fines']:
                if remaining_amount <= 0:
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
            
            # Priority 2: Pay fees
            for fee in breakdown['fees']:
                if remaining_amount <= 0:
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
            
            # Invalidate cache
            invalidate_student_cache(student.id)
            
            logger.info(f"Payment processed: {receipt_no} for student {student.id}")
            
            return {
                'success': True,
                'fee_deposit': fee_deposit,
                'allocations': allocations,
                'remaining_amount': remaining_amount,
                'receipt_no': receipt_no,
                'message': f'Payment of ₹{validated_amount} processed successfully'
            }
            
        except Exception as e:
            logger.error(f"Payment processing failed: {str(e)}")
            raise PaymentProcessingError(f"Payment processing failed: {str(e)}")
    
    def get_payment_history(self, student, limit=10):
        """Get payment history for student"""
        from student_fees.models import FeeDeposit
        
        payments = FeeDeposit.objects.filter(
            student=student
        ).order_by('-deposit_date')[:limit]
        
        history = []
        for payment in payments:
            try:
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
            except:
                # Handle payments without allocations (legacy data)
                history.append({
                    'payment': payment,
                    'allocations': [],
                    'allocated_to_fees': payment.paid_amount,
                    'allocated_to_fines': Decimal('0')
                })
        
        return history
    
    def reverse_payment(self, fee_deposit):
        """Reverse a payment transaction"""
        try:
            with transaction.atomic():
                # Reverse allocations
                for allocation in fee_deposit.allocations.all():
                    if allocation.student_fee:
                        allocation.student_fee.is_paid = False
                        allocation.student_fee.paid_date = None
                        allocation.student_fee.save()
                    
                    if allocation.applied_fine:
                        allocation.applied_fine.is_paid = False
                        allocation.applied_fine.paid_date = None
                        allocation.applied_fine.save()
                
                # Delete allocations
                fee_deposit.allocations.all().delete()
                
                # Invalidate cache
                invalidate_student_cache(fee_deposit.student.id)
                
                logger.info(f"Payment reversed: {fee_deposit.receipt_no}")
                
                return True
        except Exception as e:
            logger.error(f"Payment reversal failed: {str(e)}")
            return False

class DiscountProcessor:
    """Handle discounts and scholarships"""
    
    def apply_discount(self, student, discount_type, discount_value):
        """Apply discount to student fees"""
        try:
            from .models import StudentFee
            
            unpaid_fees = StudentFee.objects.filter(
                student=student,
                is_paid=False
            )
            
            discount_applied = 0
            
            for fee in unpaid_fees:
                if discount_type == 'percentage':
                    discount_amount = (fee.amount * Decimal(str(discount_value))) / 100
                else:  # fixed amount
                    discount_amount = Decimal(str(discount_value))
                
                # Apply discount (reduce fee amount)
                original_amount = fee.amount
                fee.amount = max(Decimal('0'), fee.amount - discount_amount)
                fee.save()
                
                discount_applied += (original_amount - fee.amount)
            
            # Invalidate cache
            invalidate_student_cache(student.id)
            
            return {
                'success': True,
                'fees_affected': len(unpaid_fees),
                'total_discount': discount_applied,
                'message': f"Discount applied to {len(unpaid_fees)} fees"
            }
            
        except Exception as e:
            logger.error(f"Discount application failed: {str(e)}")
            return {
                'success': False,
                'message': f"Discount application failed: {str(e)}"
            }
    
    def apply_scholarship(self, student, scholarship_percentage):
        """Apply scholarship to all student fees"""
        return self.apply_discount(student, 'percentage', scholarship_percentage)