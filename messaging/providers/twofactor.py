import requests
import logging
from .base import BaseMessagingProvider

logger = logging.getLogger(__name__)

class TwoFactorProvider(BaseMessagingProvider):
    """2Factor SMS Provider"""
    
    def __init__(self, config):
        super().__init__(config)
        self.api_key = config.get('api_key')
        self.base_url = "https://2factor.in/API/V1"
    
    def send_sms(self, to, message, **kwargs):
        """Send SMS via 2Factor"""
        sender_id = kwargs.get('sender_id', 'SCHOOL')
        try:
            # Clean phone number
            clean_number = ''.join(filter(str.isdigit, to))
            if clean_number.startswith('91'):
                clean_number = clean_number[2:]  # Remove country code for 2Factor
            
            url = f"{self.base_url}/{self.api_key}/SMS/{clean_number}/{message}"
            
            response = requests.get(url, timeout=30)
            
            if response.status_code == 200:
                result = response.json()
                if result.get('Status') == 'Success':
                    return {
                        'success': True,
                        'message_id': result.get('Details'),
                        'provider': '2factor'
                    }
                else:
                    return {
                        'success': False,
                        'error': result.get('Details', 'Unknown error')
                    }
            else:
                logger.error(f"2Factor SMS failed: {response.status_code} - {response.text}")
                return {
                    'success': False,
                    'error': f"2Factor error: {response.status_code}"
                }
                
        except Exception as e:
            logger.error(f"2Factor SMS exception: {str(e)}")
            return {
                'success': False,
                'error': str(e)
            }
    
    def send_whatsapp(self, to, message, **kwargs):
        """WhatsApp not supported by 2Factor"""
        return {'success': False, 'error': 'WhatsApp not supported'}
    
    def get_delivery_status(self, message_id):
        """2Factor doesn't provide delivery status API"""
        return {'status': 'unknown'}
    
    def validate_config(self):
        """Validate 2Factor configuration"""
        return bool(self.api_key)
    
    def send_otp(self, phone_number, template_name="SCHOOL_OTP"):
        """Send OTP via 2Factor"""
        try:
            clean_number = ''.join(filter(str.isdigit, phone_number))
            if clean_number.startswith('91'):
                clean_number = clean_number[2:]
            
            url = f"{self.base_url}/{self.api_key}/SMS/{clean_number}/AUTOGEN/{template_name}"
            
            response = requests.get(url, timeout=30)
            
            if response.status_code == 200:
                result = response.json()
                if result.get('Status') == 'Success':
                    return {
                        'success': True,
                        'session_id': result.get('Details'),
                        'provider': '2factor'
                    }
            
            return {
                'success': False,
                'error': 'Failed to send OTP'
            }
            
        except Exception as e:
            logger.error(f"2Factor OTP exception: {str(e)}")
            return {
                'success': False,
                'error': str(e)
            }
    
    def verify_otp(self, session_id, otp):
        """Verify OTP via 2Factor"""
        try:
            url = f"{self.base_url}/{self.api_key}/SMS/VERIFY/{session_id}/{otp}"
            
            response = requests.get(url, timeout=30)
            
            if response.status_code == 200:
                result = response.json()
                return {
                    'success': result.get('Status') == 'Success',
                    'details': result.get('Details')
                }
            
            return {
                'success': False,
                'error': 'Verification failed'
            }
            
        except Exception as e:
            logger.error(f"2Factor OTP verification exception: {str(e)}")
            return {
                'success': False,
                'error': str(e)
            }