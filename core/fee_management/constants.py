# core/fee_management/constants.py
"""Constants for fee management system"""

from decimal import Decimal

# Payment modes
PAYMENT_MODES = [
    ('Cash', 'Cash'),
    ('Card', 'Card'),
    ('UPI', 'UPI'),
    ('Bank Transfer', 'Bank Transfer'),
    ('Cheque', 'Cheque'),
    ('Online', 'Online'),
]

# Fee frequencies
FEE_FREQUENCIES = [
    ('Monthly', 'Monthly'),
    ('Quarterly', 'Quarterly'),
    ('Half Yearly', 'Half Yearly'),
    ('Yearly', 'Yearly'),
    ('One Time', 'One Time'),
]

# Fine types
FINE_CATEGORIES = [
    ('Late Fee', 'Late Fee'),
    ('Damage', 'Damage'),
    ('Discipline', 'Discipline'),
    ('Library', 'Library'),
    ('Other', 'Other'),
]

# Amount limits
MAX_PAYMENT_AMOUNT = Decimal('999999.99')
MIN_PAYMENT_AMOUNT = Decimal('1.00')
DEFAULT_LATE_FEE_PERCENTAGE = Decimal('5.00')
DEFAULT_LATE_FEE_AMOUNT = Decimal('50.00')

# Cache timeouts (seconds)
CACHE_TIMEOUT_SHORT = 300  # 5 minutes
CACHE_TIMEOUT_MEDIUM = 1800  # 30 minutes
CACHE_TIMEOUT_LONG = 3600  # 1 hour

# Receipt settings
RECEIPT_PREFIX = 'REC'
RECEIPT_NUMBER_LENGTH = 4