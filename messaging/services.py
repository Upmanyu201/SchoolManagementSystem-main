import requests
import logging
from .models import MSG91Config, MessageLog
from .message_tokens import MessageFormatter, ContextualMessaging

logger = logging.getLogger(__name__)

class MessagingService:
    def __init__(self):
        self.config = MSG91Config.get_active_config()
    
    def send_sms(self, phone_number, message):
        """Send SMS via MSG91 with user-friendly messaging"""
        msg91_service = MSG91Service()
        result = msg91_service.send_sms(phone_number, message)
        
        # Log with user-friendly message
        if result['success']:
            logger.info(f"Message sent successfully to {phone_number}")
        else:
            logger.error(f"Failed to send message to {phone_number}: {result.get('error', 'Unknown error')}")
        
        return result
    
    def send_bulk_sms(self, recipients, message, message_log):
        """Send bulk SMS"""
        msg91_service = MSG91Service()
        successful = 0
        failed = 0
        
        for recipient in recipients:
            result = msg91_service.send_sms(recipient['phone'], message)
            if result['success']:
                successful += 1
            else:
                failed += 1
        
        message_log.successful_sends = successful
        message_log.failed_sends = failed
        message_log.status = 'SENT' if successful > 0 else 'FAILED'
        message_log.save()
        
        return {'successful': successful, 'failed': failed}

class SMSService:
    """Simplified SMS service for quick messaging"""
    
    @staticmethod
    def send_sms(phone_number, message):
        """Send SMS using MSG91 service"""
        msg91_service = MSG91Service()
        return msg91_service.send_sms(phone_number, message)

class MSG91Service:
    def __init__(self):
        self.config = MSG91Config.get_active_config()
        # Use provided auth key as default
        self.auth_key = '466878AbS44RRkI68b3cabfP1'
        self.sender_id = 'TXTLCL'
        
        if self.config:
            self.auth_key = self.config.auth_key
            self.sender_id = self.config.sender_id
    
    def send_sms(self, phone_number, message, sender=None):
        """Send SMS via MSG91"""
        try:
            # Clean phone number
            clean_number = ''.join(filter(str.isdigit, phone_number))
            if not clean_number.startswith('91') and len(clean_number) == 10:
                clean_number = '91' + clean_number
            
            payload = {
                "authkey": self.auth_key,
                "mobiles": clean_number,
                "message": message,
                "sender": sender or self.sender_id,
                "route": "4"
            }
            
            response = requests.post(
                "https://api.msg91.com/api/sendhttp.php",
                data=payload,
                timeout=30
            )
            
            if response.status_code == 200:
                response_text = response.text.strip()
                if response_text and not response_text.startswith('ERROR'):
                    return {
                        'success': True,
                        'message_id': response_text,
                        'user_message': 'Message sent successfully!'
                    }
                else:
                    return {
                        'success': False,
                        'error': response_text,
                        'user_message': 'Message could not be sent. Please try again.'
                    }
            else:
                return {
                    'success': False,
                    'error': f'HTTP {response.status_code}',
                    'user_message': 'Network error. Please check your connection and try again.'
                }
                
        except Exception as e:
            logger.error(f"MSG91 SMS error: {e}")
            return {
                'success': False,
                'error': str(e),
                'user_message': 'We\'re having trouble sending messages right now. Please try again in a moment.'
            }
    
    def log_message(self, sender, phone, name, message, result, student=None):
        """Log message to database"""
        return MessageLog.objects.create(
            sender=sender,
            recipient_phone=phone,
            recipient_name=name,
            message_content=message,
            status='SENT' if result['success'] else 'FAILED',
            msg91_message_id=result.get('message_id', ''),
            error_message=result.get('error', ''),
            student=student
        )