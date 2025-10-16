# Cross-Module Message Logger
# Allows other modules to log their messages in the central messaging history

from django.contrib.auth import get_user_model
from .models import MessageLog, MessageRecipient
from students.models import Student
from teachers.models import Teacher
import logging

User = get_user_model()
logger = logging.getLogger(__name__)

class CrossModuleMessageLogger:
    """
    Centralized message logging service for all modules
    """
    
    @staticmethod
    def log_message(
        sender_user,
        source_module,
        message_content,
        recipients_data,
        message_type='SMS',
        recipient_type='INDIVIDUAL',
        class_section=None,
        status='SENT'
    ):
        """
        Log a message from any module to the central messaging history
        
        Args:
            sender_user: User who sent the message
            source_module: Module that sent the message ('student_fees', 'reports', etc.)
            message_content: The actual message content
            recipients_data: List of recipient dictionaries with keys: name, phone, type, id
            message_type: 'SMS' or 'WHATSAPP'
            recipient_type: 'INDIVIDUAL', 'ALL_STUDENTS', etc.
            class_section: ClassSection object if applicable
            status: 'SENT', 'FAILED', 'PENDING'
        
        Returns:
            MessageLog object
        """
        try:
            # Create main message log
            message_log = MessageLog.objects.create(
                sender=sender_user,
                source_module=source_module,
                message_type=message_type,
                recipient_type=recipient_type,
                message_content=message_content,
                total_recipients=len(recipients_data),
                successful_sends=len([r for r in recipients_data if r.get('status', 'SENT') == 'SENT']),
                failed_sends=len([r for r in recipients_data if r.get('status', 'SENT') == 'FAILED']),
                status=status,
                class_section_filter=class_section
            )
            
            # Create individual recipient records
            for recipient in recipients_data:
                student_obj = None
                teacher_obj = None
                
                # Try to get student/teacher objects
                if recipient.get('type') == 'student' and recipient.get('id'):
                    try:
                        student_obj = Student.objects.get(id=recipient['id'])
                    except Student.DoesNotExist:
                        pass
                elif recipient.get('type') == 'teacher' and recipient.get('id'):
                    try:
                        teacher_obj = Teacher.objects.get(id=recipient['id'])
                    except Teacher.DoesNotExist:
                        pass
                
                MessageRecipient.objects.create(
                    message_log=message_log,
                    student=student_obj,
                    teacher=teacher_obj,
                    phone_number=recipient.get('phone', ''),
                    name=recipient.get('name', ''),
                    role=recipient.get('type', 'Student').title(),
                    status=recipient.get('status', 'SENT'),
                    error_message=recipient.get('error', '')
                )
            
            logger.info(f"Message logged from {source_module}: {len(recipients_data)} recipients")
            return message_log
            
        except Exception as e:
            logger.error(f"Error logging message from {source_module}: {str(e)}")
            return None
    
    @staticmethod
    def log_fee_payment_notification(user, student, message_content, phone, status='SENT'):
        """
        Convenience method for logging fee payment notifications
        """
        recipients_data = [{
            'name': student.get_full_display_name(),
            'phone': phone,
            'type': 'student',
            'id': student.id,
            'status': status
        }]
        
        return CrossModuleMessageLogger.log_message(
            sender_user=user,
            source_module='student_fees',
            message_content=message_content,
            recipients_data=recipients_data,
            recipient_type='INDIVIDUAL'
        )
    
    @staticmethod
    def log_report_notification(user, recipients_data, message_content, status='SENT'):
        """
        Convenience method for logging report notifications
        """
        return CrossModuleMessageLogger.log_message(
            sender_user=user,
            source_module='reports',
            message_content=message_content,
            recipients_data=recipients_data,
            recipient_type='ALL_STUDENTS' if len(recipients_data) > 1 else 'INDIVIDUAL'
        )
    
    @staticmethod
    def log_attendance_alert(user, student, message_content, phone, status='SENT'):
        """
        Convenience method for logging attendance alerts
        """
        recipients_data = [{
            'name': student.get_full_display_name(),
            'phone': phone,
            'type': 'student',
            'id': student.id,
            'status': status
        }]
        
        return CrossModuleMessageLogger.log_message(
            sender_user=user,
            source_module='attendance',
            message_content=message_content,
            recipients_data=recipients_data,
            recipient_type='INDIVIDUAL'
        )
    
    @staticmethod
    def log_transport_notification(user, recipients_data, message_content, status='SENT'):
        """
        Convenience method for logging transport notifications
        """
        return CrossModuleMessageLogger.log_message(
            sender_user=user,
            source_module='transport',
            message_content=message_content,
            recipients_data=recipients_data,
            recipient_type='ALL_STUDENTS' if len(recipients_data) > 1 else 'INDIVIDUAL'
        )
    
    @staticmethod
    def log_fine_notification(user, student, message_content, phone, status='SENT'):
        """
        Convenience method for logging fine notifications
        """
        recipients_data = [{
            'name': student.get_full_display_name(),
            'phone': phone,
            'type': 'student',
            'id': student.id,
            'status': status
        }]
        
        return CrossModuleMessageLogger.log_message(
            sender_user=user,
            source_module='fines',
            message_content=message_content,
            recipients_data=recipients_data,
            recipient_type='INDIVIDUAL'
        )