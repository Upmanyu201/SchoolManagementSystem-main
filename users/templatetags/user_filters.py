from django import template

register = template.Library()

@register.filter
def lookup(obj, key):
    """Template filter to get attribute dynamically"""
    if hasattr(obj, key):
        return getattr(obj, key)
    return False