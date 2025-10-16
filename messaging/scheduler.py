"""
Message Scheduler Service
Production-ready scheduled messaging for School Management System
"""

import logging
from datetime import datetime, timedelta
from django.utils import timezone
from django.db import models
from .services import MessagingService
from .models import MessageLog, MessageRecipient

logger = logging.getLogger(__name__)

class ScheduledMessage(models.Model):
    """Model for scheduled messages"""
    sender = models.ForeignKey('users.CustomUser', on_delete=models.CASCADE)
    recipient_phone = models.CharField(max_length=20)
    recipient_name = models.CharField(max_length=100)
    message_content = models.TextField()
    message_type = models.CharField(max_length=10, choices=[('SMS', 'SMS'), ('WHATSAPP', 'WhatsApp')])
    scheduled_time = models.DateTimeField()
    status = models.CharField(max_length=20, default='PENDING', choices=[
        ('PENDING', 'Pending'),
        ('SENT', 'Sent'),
        ('FAILED', 'Failed'),
        ('CANCELLED', 'Cancelled')
    ])
    created_at = models.DateTimeField(auto_now_add=True)
    sent_at = models.DateTimeField(null=True, blank=True)
    error_message = models.TextField(blank=True)
    
    class Meta:
        app_label = 'messaging'

class MessageScheduler:
    """Service for scheduling and sending messages"""
    
    def __init__(self):
        self.messaging_service = MessagingService()
    
    def schedule_message(self, sender, recipient_phone, recipient_name, message_content, 
                        message_type, scheduled_time):
        """Schedule a message for future delivery"""
        try:
            # Validate scheduled time is in future
            if scheduled_time <= timezone.now():
                return {'success': False, 'error': 'Scheduled time must be in the future'}
            
            # Create scheduled message
            scheduled_msg = ScheduledMessage.objects.create(
                sender=sender,
                recipient_phone=recipient_phone,
                recipient_name=recipient_name,
                message_content=message_content,
                message_type=message_type,
                scheduled_time=scheduled_time
            )
            
            logger.info(f"Message scheduled: ID {scheduled_msg.id} for {scheduled_time}")
            
            return {
                'success': True,
                'scheduled_id': scheduled_msg.id,
                'scheduled_time': scheduled_time
            }
            
        except Exception as e:
            logger.error(f"Error scheduling message: {e}")
            return {'success': False, 'error': str(e)}
    
    def send_scheduled_messages(self):
        """Send all pending scheduled messages that are due"""
        now = timezone.now()
        
        # Get all pending messages that are due
        due_messages = ScheduledMessage.objects.filter(
            status='PENDING',
            scheduled_time__lte=now
        )
        
        sent_count = 0
        failed_count = 0
        
        for scheduled_msg in due_messages:
            try:
                # Send the message
                if scheduled_msg.message_type == 'SMS':
                    result = self.messaging_service.send_sms(
                        scheduled_msg.recipient_phone,
                        scheduled_msg.message_content
                    )
                else:  # WhatsApp
                    result = self.messaging_service.send_whatsapp_cloud_api(
                        scheduled_msg.recipient_phone,
                        scheduled_msg.message_content
                    )
                
                # Update scheduled message status
                if result['success']:
                    scheduled_msg.status = 'SENT'
                    scheduled_msg.sent_at = now
                    sent_count += 1
                    
                    # Create message log
                    message_log = MessageLog.objects.create(
                        sender=scheduled_msg.sender,
                        message_type=scheduled_msg.message_type,
                        recipient_type='SCHEDULED',
                        message_content=scheduled_msg.message_content,
                        total_recipients=1,
                        successful_sends=1,
                        failed_sends=0,
                        status='SENT'
                    )
                    
                    MessageRecipient.objects.create(
                        message_log=message_log,
                        phone_number=scheduled_msg.recipient_phone,
                        name=scheduled_msg.recipient_name,
                        role='SCHEDULED',
                        status='SENT'
                    )
                    
                    logger.info(f"Scheduled message {scheduled_msg.id} sent successfully")
                    
                else:
                    scheduled_msg.status = 'FAILED'
                    scheduled_msg.error_message = result.get('error', 'Unknown error')
                    failed_count += 1
                    
                    logger.error(f"Scheduled message {scheduled_msg.id} failed: {result.get('error')}")
                
                scheduled_msg.save()
                
            except Exception as e:
                scheduled_msg.status = 'FAILED'
                scheduled_msg.error_message = str(e)
                scheduled_msg.save()
                failed_count += 1
                
                logger.error(f"Error sending scheduled message {scheduled_msg.id}: {e}")
        
        logger.info(f"Scheduled messages processed: {sent_count} sent, {failed_count} failed")
        
        return {
            'processed': len(due_messages),
            'sent': sent_count,
            'failed': failed_count
        }
    
    def cancel_scheduled_message(self, scheduled_id, user):
        """Cancel a scheduled message"""
        try:
            scheduled_msg = ScheduledMessage.objects.get(
                id=scheduled_id,
                sender=user,
                status='PENDING'
            )
            
            scheduled_msg.status = 'CANCELLED'
            scheduled_msg.save()
            
            logger.info(f"Scheduled message {scheduled_id} cancelled by {user.username}")
            
            return {'success': True}
            
        except ScheduledMessage.DoesNotExist:
            return {'success': False, 'error': 'Scheduled message not found or already processed'}
        except Exception as e:
            logger.error(f"Error cancelling scheduled message {scheduled_id}: {e}")
            return {'success': False, 'error': str(e)}
    
    def get_user_scheduled_messages(self, user):
        """Get all scheduled messages for a user"""
        return ScheduledMessage.objects.filter(sender=user).order_by('-created_at')
    
    def parse_schedule_time(self, date_str, time_str):
        """Parse date and time strings into datetime object"""
        try:
            # Expected format: YYYY-MM-DD for date, HH:MM for time
            datetime_str = f"{date_str} {time_str}"
            scheduled_time = datetime.strptime(datetime_str, "%Y-%m-%d %H:%M")
            
            # Make timezone aware
            scheduled_time = timezone.make_aware(scheduled_time)
            
            return scheduled_time
            
        except ValueError as e:
            raise ValueError(f"Invalid date/time format: {e}")

# Utility function for management commands
def process_scheduled_messages():
    """Process scheduled messages - can be called from management command"""
    scheduler = MessageScheduler()
    return scheduler.send_scheduled_messages()