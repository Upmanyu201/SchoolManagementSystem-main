from typing import Dict, Any, List
from django.template import Template, Context
from django.conf import settings
import logging

logger = logging.getLogger(__name__)

class MessageTemplateService:
    """Service for rendering message templates"""
    
    def __init__(self):
        self.school_name = getattr(settings, 'SCHOOL_NAME', 'School')
    
    def render_fee_deposit_message(self, student, fee_deposit, recipient_type: str) -> str:
        """Render fee deposit notification message"""
        
        if recipient_type == 'parent':
            template_text = """Dear Parent,
Fee payment of ₹{{ amount }} has been successfully received for {{ student_name }} (Class: {{ class_name }}).
Receipt No: {{ receipt_number }}
Date: {{ payment_date }}
Thank you!
- {{ school_name }}"""
        
        else:  # admin
            template_text = """Fee Deposit Alert:
Student: {{ student_name }} ({{ admission_number }})
Amount: ₹{{ amount }}
Receipt: {{ receipt_number }}
Class: {{ class_name }}
Time: {{ payment_date }}"""
        
        context = {
            'student_name': f"{student.first_name} {student.last_name}",
            'admission_number': student.admission_number,
            'class_name': str(student.student_class) if student.student_class else 'N/A',
            'amount': fee_deposit.amount_paid,
            'receipt_number': fee_deposit.receipt_number,
            'payment_date': fee_deposit.date_of_deposit.strftime('%d/%m/%Y %I:%M %p'),
            'school_name': self.school_name
        }
        
        return self._render_template(template_text, context)
    
    def render_fine_notification(self, fine, students: List, recipient_type: str) -> str:
        """Render fine notification message"""
        
        if recipient_type == 'parent':
            if len(students) == 1:
                student = students[0]
                template_text = """Dear Parent,
A fine of ₹{{ fine_amount }} has been applied to {{ student_name }} for: {{ fine_reason }}
Due Date: {{ due_date }}
Please contact school office for details.
- {{ school_name }}"""
                
                context = {
                    'student_name': f"{student.first_name} {student.last_name}",
                    'fine_amount': fine.amount,
                    'fine_reason': fine.reason,
                    'due_date': fine.due_date.strftime('%d/%m/%Y') if fine.due_date else 'N/A',
                    'school_name': self.school_name
                }
            else:
                template_text = """Dear Parent,
A fine of ₹{{ fine_amount }} has been applied for: {{ fine_reason }}
Due Date: {{ due_date }}
Please contact school office for details.
- {{ school_name }}"""
                
                context = {
                    'fine_amount': fine.amount,
                    'fine_reason': fine.reason,
                    'due_date': fine.due_date.strftime('%d/%m/%Y') if fine.due_date else 'N/A',
                    'school_name': self.school_name
                }
        
        else:  # admin
            template_text = """Fine Applied:
Type: {{ fine_type }}
Students: {{ student_count }} students affected
Amount: ₹{{ fine_amount }} per student
Reason: {{ fine_reason }}
Due Date: {{ due_date }}"""
            
            context = {
                'fine_type': fine.fine_type.name if fine.fine_type else 'General Fine',
                'student_count': len(students),
                'fine_amount': fine.amount,
                'fine_reason': fine.reason,
                'due_date': fine.due_date.strftime('%d/%m/%Y') if fine.due_date else 'N/A'
            }
        
        return self._render_template(template_text, context)
    
    def render_custom_message(self, template_text: str, context: Dict[str, Any]) -> str:
        """Render custom message template"""
        return self._render_template(template_text, context)
    
    def _render_template(self, template_text: str, context: Dict[str, Any]) -> str:
        """Render template with context"""
        try:
            template = Template(template_text)
            return template.render(Context(context))
        except Exception as e:
            logger.error(f"Error rendering template: {str(e)}")
            return template_text  # Return original text if rendering fails

# Global template service instance
template_service = MessageTemplateService()