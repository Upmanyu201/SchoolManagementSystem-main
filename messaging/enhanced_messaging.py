# messaging/enhanced_messaging.py
"""
Enhanced messaging service with user-friendly token-level messaging
Integrates with existing SMS and notification systems
"""

from django.contrib import messages
from django.http import JsonResponse
from .message_tokens import MessageFormatter, ContextualMessaging
from .services import MessagingService
import logging

logger = logging.getLogger(__name__)

class EnhancedMessagingService:
    """Enhanced messaging service with user-friendly messages"""
    
    def __init__(self):
        self.messaging_service = MessagingService()
    
    def send_user_friendly_sms(self, phone_number, message_type, **context):
        """Send SMS with user-friendly formatting"""
        try:
            # Format message using tokens
            message = MessageFormatter.format_sms(message_type, **context)
            
            # Send via existing service
            result = self.messaging_service.send_sms(phone_number, message)
            
            # Return user-friendly response
            if result['success']:
                return {
                    'success': True,
                    'message': 'Message sent successfully!',
                    'technical_id': result.get('message_id')
                }
            else:
                return {
                    'success': False,
                    'message': 'We couldn\'t send the message right now. Please try again.',
                    'technical_error': result.get('error')
                }
                
        except Exception as e:
            logger.error(f"Enhanced messaging error: {e}")
            return {
                'success': False,
                'message': 'Something went wrong while sending the message. Please try again.',
                'technical_error': str(e)
            }
    
    def add_django_message(self, request, message_type, key, **kwargs):
        """Add user-friendly Django message"""
        try:
            if message_type == 'success':
                message = MessageFormatter.format_success(key, **kwargs)
                messages.success(request, message)
            elif message_type == 'error':
                message = MessageFormatter.format_error(key, **kwargs)
                messages.error(request, message)
            elif message_type == 'warning':
                message = MessageFormatter.format_warning(key, **kwargs)
                messages.warning(request, message)
            elif message_type == 'info':
                message = MessageFormatter.format_info(key, **kwargs)
                messages.info(request, message)
        except Exception as e:
            logger.error(f"Django message error: {e}")
            # Fallback to generic message
            messages.info(request, "Action completed.")
    
    def create_api_response(self, success, message_key, **kwargs):
        """Create user-friendly API response"""
        try:
            if success:
                message = MessageFormatter.format_success(message_key, **kwargs)
                return JsonResponse({
                    'success': True,
                    'message': message,
                    'data': kwargs
                })
            else:
                message = MessageFormatter.format_error(message_key, **kwargs)
                return JsonResponse({
                    'success': False,
                    'message': message,
                    'error_code': message_key.upper()
                }, status=400)
        except Exception as e:
            logger.error(f"API response error: {e}")
            return JsonResponse({
                'success': False,
                'message': 'Something went wrong. Please try again.'
            }, status=500)

class FeeMessagingEnhanced:
    """Enhanced fee messaging with user-friendly tokens"""
    
    @staticmethod
    def send_payment_confirmation(student, amount, receipt_no, school_name):
        """Send user-friendly payment confirmation"""
        service = EnhancedMessagingService()
        
        # Get parent's phone number
        phone = student.mobile_number or student.father_mobile or student.mother_mobile
        if not phone:
            return {'success': False, 'message': 'No phone number available for student'}
        
        # Send SMS using tokens
        return service.send_user_friendly_sms(
            phone_number=phone,
            message_type='payment_confirmation',
            student_name=student.first_name,
            amount=amount,
            receipt_no=receipt_no,
            school_name=school_name
        )
    
    @staticmethod
    def send_fee_reminder(student, amount, due_date, school_name):
        """Send user-friendly fee reminder"""
        service = EnhancedMessagingService()
        
        phone = student.mobile_number or student.father_mobile or student.mother_mobile
        if not phone:
            return {'success': False, 'message': 'No phone number available for student'}
        
        return service.send_user_friendly_sms(
            phone_number=phone,
            message_type='fee_reminder',
            student_name=student.first_name,
            amount=amount,
            due_date=due_date,
            school_name=school_name,
            link="school portal"
        )

# Utility functions for easy integration
def add_success_message(request, key, **kwargs):
    """Quick function to add success message"""
    service = EnhancedMessagingService()
    service.add_django_message(request, 'success', key, **kwargs)

def add_error_message(request, key, **kwargs):
    """Quick function to add error message"""
    service = EnhancedMessagingService()
    service.add_django_message(request, 'error', key, **kwargs)

def create_success_response(key, **kwargs):
    """Quick function to create success API response"""
    service = EnhancedMessagingService()
    return service.create_api_response(True, key, **kwargs)

def create_error_response(key, **kwargs):
    """Quick function to create error API response"""
    service = EnhancedMessagingService()
    return service.create_api_response(False, key, **kwargs)