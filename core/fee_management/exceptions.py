# core/fee_management/exceptions.py
"""Custom exceptions for fee management"""

class FeeManagementError(Exception):
    """Base exception for fee management operations"""
    pass

class PaymentProcessingError(FeeManagementError):
    """Raised when payment processing fails"""
    pass

class InsufficientPaymentError(FeeManagementError):
    """Raised when payment amount is insufficient"""
    pass

class FeeCalculationError(FeeManagementError):
    """Raised when fee calculation fails"""
    pass

class FineApplicationError(FeeManagementError):
    """Raised when fine application fails"""
    pass

class StudentNotEligibleError(FeeManagementError):
    """Raised when student is not eligible for fee operations"""
    pass

class DuplicateReceiptError(FeeManagementError):
    """Raised when receipt number already exists"""
    pass