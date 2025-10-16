# core/validators.py - Enhanced validation system
from django.core.exceptions import ValidationError
from django.core.validators import RegexValidator
import re
from decimal import Decimal

def validate_phone_number(value):
    """Validate Indian mobile number"""
    cleaned = re.sub(r'[^\d]', '', str(value))
    if len(cleaned) != 10:
        raise ValidationError("Phone number must be exactly 10 digits")
    if not cleaned.startswith(('6', '7', '8', '9')):
        raise ValidationError("Invalid phone number format")
    return cleaned

def validate_aadhaar_number(value):
    """Validate Aadhaar number"""
    if not value:
        return value
    cleaned = re.sub(r'[^\d]', '', str(value))
    if len(cleaned) != 12:
        raise ValidationError("Aadhaar number must be exactly 12 digits")
    if cleaned == '000000000000' or len(set(cleaned)) == 1:
        raise ValidationError("Invalid Aadhaar number")
    return cleaned

def validate_admission_number(value):
    """Validate admission number"""
    if not value or len(str(value)) < 3:
        raise ValidationError("Admission number must be at least 3 characters")
    if not re.match(r'^[A-Z0-9]+$', str(value).upper()):
        raise ValidationError("Admission number can only contain letters and numbers")
    return str(value).upper()

def validate_file_size(file):
    """Validate file size (max 10MB)"""
    if file and file.size > 10 * 1024 * 1024:
        raise ValidationError("File size must be less than 10MB")
    return file

def validate_file_extension(file):
    """Validate file extension"""
    if file and hasattr(file, 'name'):
        allowed_extensions = ['.pdf', '.jpg', '.jpeg', '.png', '.doc', '.docx']
        ext = file.name.lower().split('.')[-1] if '.' in file.name else ''
        if f'.{ext}' not in allowed_extensions:
            raise ValidationError(f"File type not allowed. Allowed: {', '.join(allowed_extensions)}")
    return file

class EnhancedValidators:
    @staticmethod
    def validate_admission_number(value):
        return validate_admission_number(value)
    
    @staticmethod
    def validate_phone_number(value):
        return validate_phone_number(value)
    
    @staticmethod
    def validate_amount(value):
        """Enhanced amount validation"""
        if value < 0:
            raise ValidationError("Amount cannot be negative")
        if value > Decimal('999999.99'):
            raise ValidationError("Amount too large")
        return value
    
    @staticmethod
    def validate_percentage(value):
        """Enhanced percentage validation"""
        if not 0 <= value <= 100:
            raise ValidationError("Percentage must be between 0 and 100")
        return value

# Aliases for backward compatibility
validate_amount = EnhancedValidators.validate_amount
validate_percentage = EnhancedValidators.validate_percentage