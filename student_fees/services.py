# student_fees/services.py
"""Centralized fee calculation and processing services"""

from core.fee_management.calculators import AtomicFeeCalculator
from decimal import Decimal
from typing import Dict, List
from django.db.models import Sum
import logging

logger = logging.getLogger(__name__)


class FeeCalculationService:
    """Service using AtomicFeeCalculator"""
    
    @staticmethod
    def get_applicable_fees(student) -> List:
        """Get applicable fees using AtomicFeeCalculator"""
        return AtomicFeeCalculator.get_applicable_fees(student)
    
    @staticmethod
    def calculate_student_balance(student) -> Dict:
        """Calculate balance using AtomicFeeCalculator"""
        return AtomicFeeCalculator.calculate_student_balance(student)
    
    @staticmethod
    def _calculate_fine_balance(student) -> Dict:
        """Optimized fine calculation"""
        try:
            from fines.models import FineStudent
            
            fine_records = FineStudent.objects.filter(
                student=student
            ).select_related('fine', 'fine__fine_type', 'fine__class_section')
            
            # Filter relevant fines
            relevant_fines = []
            for fs in fine_records:
                fine = fs.fine
                if (fine.target_scope == 'Individual' or 
                    fine.target_scope == 'All' or 
                    (fine.target_scope == 'Class' and fine.class_section == student.class_section)):
                    relevant_fines.append(fs)
            
            paid_amount = sum(fs.fine.amount for fs in relevant_fines if fs.is_paid)
            unpaid_amount = sum(fs.fine.amount for fs in relevant_fines if not fs.is_paid)
            
            return {
                'paid': float(paid_amount),
                'unpaid': float(unpaid_amount),
                'balance': float(unpaid_amount)
            }
        except Exception as e:
            logger.error(f"Fine calculation error: {str(e)}")
            return {'paid': 0.0, 'unpaid': 0.0, 'balance': 0.0}
    
    @staticmethod
    def get_payable_fees(student, discount_enabled=False) -> List[Dict]:
        """Get payable fees using AtomicFeeCalculator"""
        return AtomicFeeCalculator.get_payable_fees(student, discount_enabled)
    
    @staticmethod
    def _add_payable_fines(student, payable_fees: List[Dict]):
        """Add unpaid fines to payable fees list"""
        try:
            from fines.models import FineStudent
            from datetime import date
            
            today = date.today()
            unpaid_fines = FineStudent.objects.filter(
                student=student,
                is_paid=False,
                fine__due_date__lte=today
            ).select_related('fine', 'fine__fine_type', 'fine__class_section')
            
            for fs in unpaid_fines:
                fine = fs.fine
                # Check relevance
                if (fine.target_scope == 'Individual' or 
                    fine.target_scope == 'All' or 
                    (fine.target_scope == 'Class' and fine.class_section == student.class_section)):
                    
                    display_name = f"Fine: {fine.fine_type.name} - {fine.reason[:50]}"
                    payable_fees.append({
                        'id': f"fine_{fine.id}",
                        'type': 'fine',  # Add type field for template recognition
                        'fee_type': 'Fine',
                        'display_name': display_name,
                        'amount': float(fine.amount),
                        'is_overdue': True,
                        'due_date': fine.due_date.strftime('%Y-%m-%d') if fine.due_date else ''
                    })
        except Exception as e:
            logger.error(f"Fine processing error: {str(e)}")


class PaymentProcessingService:
    """Service for processing payments using AtomicFeeCalculator"""
    
    @staticmethod
    def process_payment(student, payment_data: Dict) -> Dict:
        """Process payment using AtomicFeeCalculator"""
        return AtomicFeeCalculator.process_payment(student, payment_data)


class FeeReportingService:
    """Service for fee reporting and history"""
    
    @staticmethod
    def get_student_payment_history(student) -> Dict:
        """Get comprehensive payment history for student"""
        from .models import FeeDeposit
        
        deposits = FeeDeposit.objects.filter(student=student).order_by('-deposit_date')
        regular_deposits = deposits.exclude(note__icontains="Carry Forward").exclude(note__icontains="Fine Payment")
        cf_deposits = deposits.filter(note__icontains="Carry Forward")
        fine_deposits = deposits.filter(note__icontains="Fine Payment")
        
        total_paid = deposits.aggregate(Sum('paid_amount'))['paid_amount__sum'] or Decimal('0')
        total_discount = deposits.aggregate(Sum('discount'))['discount__sum'] or Decimal('0')
        
        return {
            'all_payments': deposits,
            'regular_payments': regular_deposits,
            'carry_forward_payments': cf_deposits,
            'fine_payments': fine_deposits,
            'total_paid': total_paid,
            'total_discount': total_discount
        }
    
    @staticmethod
    def get_receipt_data(receipt_no: str) -> Dict:
        """Get receipt data for printing"""
        from .models import FeeDeposit
        
        deposits = FeeDeposit.objects.filter(receipt_no=receipt_no)
        if not deposits.exists():
            raise ValueError(f"Receipt {receipt_no} not found")
        
        first_deposit = deposits.first()
        total_amount = deposits.aggregate(Sum('amount'))['amount__sum'] or Decimal('0')
        total_discount = deposits.aggregate(Sum('discount'))['discount__sum'] or Decimal('0')
        total_paid = deposits.aggregate(Sum('paid_amount'))['paid_amount__sum'] or Decimal('0')
        
        return {
            'receipt_no': receipt_no,
            'student': first_deposit.student,
            'deposits': deposits,
            'deposit_date': first_deposit.deposit_date,
            'total_amount': total_amount,
            'total_discount': total_discount,
            'total_paid': total_paid
        }