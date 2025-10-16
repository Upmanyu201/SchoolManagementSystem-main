# core/fee_management/validators.py
"""Centralized validation for fee operations"""

from decimal import Decimal
from django.core.exceptions import ValidationError
from django.utils import timezone
from datetime import date

class FeeValidator:
    """Validate fee-related operations"""
    
    @staticmethod
    def validate_payment_amount(amount):
        """Validate payment amount"""
        try:
            amount = Decimal(str(amount))
            if amount <= 0:
                raise ValidationError("Payment amount must be greater than zero")
            if amount > Decimal('999999.99'):
                raise ValidationError("Payment amount is too large")
            return amount
        except (ValueError, TypeError):
            raise ValidationError("Invalid payment amount format")
    
    @staticmethod
    def validate_student_eligibility(student):
        """Validate if student can make payments"""
        if not student.is_active:
            raise ValidationError("Cannot process payment for inactive student")
        if not student.class_section:
            raise ValidationError("Student must be assigned to a class")
        return True
    
    @staticmethod
    def validate_receipt_number(receipt_no):
        """Validate receipt number format"""
        if not receipt_no or len(receipt_no) > 50:
            raise ValidationError("Invalid receipt number")
        return receipt_no.strip()

class FineValidator:
    """Validate fine-related operations"""
    
    @staticmethod
    def validate_fine_amount(amount, fee_amount=None):
        """Validate fine amount"""
        try:
            amount = Decimal(str(amount))
            if amount < 0:
                raise ValidationError("Fine amount cannot be negative")
            if fee_amount and amount > fee_amount * 2:
                raise ValidationError("Fine amount cannot exceed 200% of original fee")
            return amount
        except (ValueError, TypeError):
            raise ValidationError("Invalid fine amount format")
    
    @staticmethod
    def validate_due_date(due_date):
        """Validate due date"""
        if due_date < date.today():
            raise ValidationError("Due date cannot be in the past")
        return due_date