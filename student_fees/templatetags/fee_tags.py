from django import template
from student_fees.utils import get_student_fee_breakdown

register = template.Library()

@register.simple_tag
def get_student_due(student):
    """Template tag to get student's current due amount"""
    return student.due_amount

@register.simple_tag
def get_student_fees(student):
    """Template tag to get student's fee breakdown"""
    return get_student_fee_breakdown(student)

@register.filter
def currency(value):
    """Format currency values"""
    try:
        return f"Rs{float(value):,.2f}"
    except (ValueError, TypeError):
        return "Rs0.00"