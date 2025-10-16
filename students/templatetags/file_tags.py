from django import template
import os

register = template.Library()

@register.filter
def file_exists(file_field):
    """Check if file exists on filesystem"""
    if not file_field:
        return False
    try:
        return os.path.exists(file_field.path)
    except (ValueError, AttributeError):
        return False

@register.filter
def safe_file_url(file_field):
    """Return file URL only if file exists"""
    if not file_field:
        return None
    try:
        if os.path.exists(file_field.path):
            return file_field.url
    except (ValueError, AttributeError):
        pass
    return None