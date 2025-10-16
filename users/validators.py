from django.core.exceptions import ValidationError
from django.utils.translation import gettext as _
import re

class SchoolPasswordValidator:
    """Custom password validator for school management system"""
    
    def validate(self, password, user=None):
        if len(password) < 8:
            raise ValidationError(_("Password must be at least 8 characters long."))
        
        if not re.search(r'[A-Z]', password):
            raise ValidationError(_("Password must contain at least one uppercase letter."))
        
        if not re.search(r'[a-z]', password):
            raise ValidationError(_("Password must contain at least one lowercase letter."))
        
        if not re.search(r'\d', password):
            raise ValidationError(_("Password must contain at least one digit."))
        
        if not re.search(r'[!@#$%^&*(),.?":{}|<>]', password):
            raise ValidationError(_("Password must contain at least one special character."))
    
    def get_help_text(self):
        return _("Password must be 8+ characters with uppercase, lowercase, digit, and special character.")

class NoPersonalInfoValidator:
    """Prevent using personal information in passwords"""
    
    def validate(self, password, user=None):
        if user:
            personal_info = [
                user.username.lower(),
                user.first_name.lower(),
                user.last_name.lower(),
                user.email.split('@')[0].lower() if user.email else '',
            ]
            
            for info in personal_info:
                if info and len(info) > 2 and info in password.lower():
                    raise ValidationError(_("Password cannot contain personal information."))
    
    def get_help_text(self):
        return _("Password cannot contain your personal information.")