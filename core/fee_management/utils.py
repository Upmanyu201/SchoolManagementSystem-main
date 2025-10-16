# core/fee_management/utils.py
"""Utility functions for fee management"""

from decimal import Decimal
from django.utils import timezone
from django.core.cache import cache
from .constants import RECEIPT_PREFIX, RECEIPT_NUMBER_LENGTH
import logging

logger = logging.getLogger(__name__)

def generate_receipt_number():
    """Generate unique receipt number"""
    year = timezone.now().year
    
    # Get next sequence from cache or database
    cache_key = f'receipt_sequence_{year}'
    sequence = cache.get(cache_key, 0)
    sequence += 1
    
    # Cache for 1 hour
    cache.set(cache_key, sequence, 3600)
    
    return f'{RECEIPT_PREFIX}{year}{sequence:0{RECEIPT_NUMBER_LENGTH}d}'

def format_currency(amount):
    """Format amount as currency"""
    if amount is None:
        return '₹0.00'
    return f'₹{Decimal(str(amount)):,.2f}'

def parse_currency(amount_str):
    """Parse currency string to Decimal"""
    if not amount_str:
        return Decimal('0')
    
    # Remove currency symbols and commas
    clean_amount = str(amount_str).replace('₹', '').replace(',', '').strip()
    
    try:
        return Decimal(clean_amount)
    except:
        return Decimal('0')

def calculate_percentage(amount, percentage):
    """Calculate percentage of amount"""
    if not amount or not percentage:
        return Decimal('0')
    
    return (Decimal(str(amount)) * Decimal(str(percentage))) / 100

def get_academic_year():
    """Get current academic year"""
    now = timezone.now()
    if now.month >= 4:  # April onwards is new academic year
        return f'{now.year}-{str(now.year + 1)[2:]}'
    else:
        return f'{now.year - 1}-{str(now.year)[2:]}'

def invalidate_student_cache(student_id):
    """Invalidate all cache entries for a student"""
    cache_patterns = [
        f'balance_{student_id}*',
        f'applicable_fees_{student_id}',
        f'payment_history_{student_id}*',
        f'student_fees_{student_id}*'
    ]
    
    for pattern in cache_patterns:
        try:
            cache.delete_pattern(pattern)
        except:
            # Fallback for cache backends that don't support delete_pattern
            pass
    
    logger.info(f"Cache invalidated for student {student_id}")

def safe_decimal_operation(operation, *args, default=Decimal('0')):
    """Safely perform decimal operations"""
    try:
        return operation(*[Decimal(str(arg)) for arg in args])
    except:
        return default