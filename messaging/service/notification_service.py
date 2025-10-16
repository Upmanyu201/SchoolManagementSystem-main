from typing import List, Dict, Any
from django.conf import settings
from django.contrib.auth import get_user_model
try:
    from .message_router import message_router
    from .template_service import template_service
except ImportError:
    # Fallback for development
    message_router = None
    template_service = None
import logging

logger = logging.getLogger(__name__)
User = get_user_model()

class NotificationService:
    """Service for sending automated notifications"""
    
    def __init__(self):
        self.admin_numbers = getattr(settings, 'ADMIN_NOTIFICATION_NUMBERS', [])
    
    def get_admin_numbers(self) -> List[str]:
        """Get admin notification numbers"""
        admin_numbers = []
        
        # From settings
        if self.admin_numbers:
            admin_numbers.extend([num.strip() for num in self.admin_numbers if num.strip()])
        
        # From admin users with mobile numbers
        admin_users = User.objects.filter(
            is_staff=True, 
            mobile_number__isnull=False
        ).exclude(mobile_number='')
        
        for admin in admin_users:
            if admin.mobile_number and admin.mobile_number not in admin_numbers:
                admin_numbers.append(admin.mobile_number)
        
        return admin_numbers
    
    def send_fee_deposit_notifications(self, fee_deposit):
        """Send notifications when fee is deposited"""
        try:
            student = fee_deposit.student
            
            # Notify parent if mobile number exists
            if student.mobile_number:
                parent_message = template_service.render_fee_deposit_message(
                    student, fee_deposit, 'parent'
                )
                
                result = message_router.send_sms(
                    to=student.mobile_number,
                    message=parent_message,
                    message_type='fee_deposit_parent'
                )
                
                # Log the message
                self._log_message(
                    message_type='fee_deposit_parent',
                    recipient=student.mobile_number,
                    content=parent_message,
                    student=student,
                    fee_deposit=fee_deposit,
                    result=result
                )
            
            # Notify admins
            admin_numbers = self.get_admin_numbers()
            if admin_numbers:
                admin_message = template_service.render_fee_deposit_message(
                    student, fee_deposit, 'admin'
                )
                
                for admin_number in admin_numbers:
                    result = message_router.send_sms(
                        to=admin_number,
                        message=admin_message,
                        message_type='fee_deposit_admin'
                    )
                    
                    # Log the message
                    self._log_message(
                        message_type='fee_deposit_admin',
                        recipient=admin_number,
                        content=admin_message,
                        student=student,
                        fee_deposit=fee_deposit,
                        result=result
                    )
            
            logger.info(f"Fee deposit notifications sent for student {student.admission_number}")
            
        except Exception as e:
            logger.error(f"Error sending fee deposit notifications: {str(e)}")
    
    def send_fine_creation_notifications(self, fine, student_ids):
        """Send notifications when fine is created"""
        try:
            from students.models import Student
            students = Student.objects.filter(id__in=student_ids)
            
            # Notify parents of affected students
            for student in students:
                if student.mobile_number:
                    parent_message = template_service.render_fine_notification(
                        fine, [student], 'parent'
                    )
                    
                    result = message_router.send_sms(
                        to=student.mobile_number,
                        message=parent_message,
                        message_type='fine_creation_parent'
                    )
                    
                    # Log the message
                    self._log_message(
                        message_type='fine_creation_parent',
                        recipient=student.mobile_number,
                        content=parent_message,
                        student=student,
                        fine=fine,
                        result=result
                    )
            
            # Notify admins
            admin_numbers = self.get_admin_numbers()
            if admin_numbers:
                admin_message = template_service.render_fine_notification(
                    fine, students, 'admin'
                )
                
                for admin_number in admin_numbers:
                    result = message_router.send_sms(
                        to=admin_number,
                        message=admin_message,
                        message_type='fine_application_admin'
                    )
                    
                    # Log the message
                    self._log_message(
                        message_type='fine_application_admin',
                        recipient=admin_number,
                        content=admin_message,
                        fine=fine,
                        result=result
                    )
            
            logger.info(f"Fine creation notifications sent for {len(students)} students")
            
        except Exception as e:
            logger.error(f"Error sending fine creation notifications: {str(e)}")
    
    def _log_message(self, message_type: str, recipient: str, content: str, 
                    result: Dict[str, Any], student=None, fee_deposit=None, fine=None):
        """Log message to database"""
        try:
            from ..models import MessageLog
            from django.contrib.auth import get_user_model
            
            User = get_user_model()
            
            # Get current user or system user
            try:
                from django.contrib.auth.models import AnonymousUser
                from threading import local
                _thread_locals = local()
                current_user = getattr(_thread_locals, 'user', None)
                if not current_user or isinstance(current_user, AnonymousUser):
                    current_user = User.objects.filter(is_superuser=True).first()
            except:
                current_user = User.objects.filter(is_superuser=True).first()
            
            MessageLog.objects.create(
                message_type=message_type,
                recipient_number=recipient,
                message_content=content,
                provider=result.get('provider', 'unknown'),
                provider_message_id=result.get('message_id'),
                status='sent' if result.get('success') else 'failed',
                student=student,
                fee_deposit=fee_deposit,
                fine=fine,
                sent_by=current_user
            )
            
        except Exception as e:
            logger.error(f"Error logging message: {str(e)}")

# Global notification service instance
notification_service = NotificationService()