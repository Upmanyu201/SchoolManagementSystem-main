import requests
import json
import logging
from .base import BaseMessagingProvider

logger = logging.getLogger(__name__)

class MSG91Provider(BaseMessagingProvider):
    """MSG91 SMS Provider using Flow API"""
    
    def __init__(self, config):
        super().__init__(config)
        self.auth_key = config.get('auth_key', '466878AbS44RRkI68b3cabfP1')
        self.flow_url = "https://control.msg91.com/api/v5/flow"
        self.sendhttp_url = "https://api.msg91.com/api/sendhttp.php"
    
    def send_sms(self, to, message, **kwargs):
        """Send SMS via MSG91 Flow API or SendHTTP API"""
        sender_id = kwargs.get('sender_id', 'TXTLCL')
        template_id = kwargs.get('template_id')
        
        # Try Flow API first if template_id provided
        if template_id:
            return self._send_via_flow_api(to, message, template_id, **kwargs)
        else:
            return self._send_via_sendhttp_api(to, message, sender_id)
    
    def _send_via_flow_api(self, to, message, template_id, **kwargs):
        """Send SMS via MSG91 Flow API"""
        try:
            # Clean phone number
            clean_number = ''.join(filter(str.isdigit, to))
            if not clean_number.startswith('91') and len(clean_number) == 10:
                clean_number = '91' + clean_number
            
            payload = {
                "template_id": template_id,
                "short_url": "0",
                "realTimeResponse": "1",
                "recipients": [
                    {
                        "mobiles": clean_number,
                        "VAR1": message  # Use message as variable
                    }
                ]
            }
            
            headers = {
                'accept': 'application/json',
                'authkey': self.auth_key,
                'content-type': 'application/json'
            }
            
            response = requests.post(
                self.flow_url, 
                data=json.dumps(payload), 
                headers=headers, 
                timeout=30
            )
            
            if response.status_code == 200:
                result = response.json()
                if result.get('type') == 'success':
                    return {
                        'success': True,
                        'message_id': result.get('request_id'),
                        'provider': 'msg91_flow'
                    }
                else:
                    return {
                        'success': False,
                        'error': f'MSG91 Flow error: {result.get("message", "Unknown error")}'
                    }
            else:
                return {
                    'success': False,
                    'error': f'MSG91 Flow HTTP {response.status_code}'
                }
                
        except Exception as e:
            logger.error(f"MSG91 Flow API exception: {str(e)}")
            # Fallback to SendHTTP API
            return self._send_via_sendhttp_api(to, message, kwargs.get('sender_id', 'TXTLCL'))
    
    def _send_via_sendhttp_api(self, to, message, sender_id='TXTLCL'):
        """Send SMS via MSG91 SendHTTP API (fallback)"""
        try:
            # Clean phone number
            clean_number = ''.join(filter(str.isdigit, to))
            if not clean_number.startswith('91') and len(clean_number) == 10:
                clean_number = '91' + clean_number
            
            payload = {
                "authkey": self.auth_key,
                "mobiles": clean_number,
                "message": message,
                "sender": sender_id,
                "route": "4"
            }
            
            response = requests.post(self.sendhttp_url, data=payload, timeout=30)
            
            if response.status_code == 200:
                response_text = response.text.strip()
                # MSG91 returns message ID on success, error message starts with "ERROR"
                if response_text and not response_text.startswith('ERROR'):
                    return {
                        'success': True,
                        'message_id': response_text,
                        'provider': 'msg91_sendhttp'
                    }
                else:
                    return {
                        'success': False,
                        'error': f'MSG91 SendHTTP error: {response_text}'
                    }
            else:
                return {
                    'success': False,
                    'error': f'MSG91 SendHTTP HTTP {response.status_code}'
                }
                
        except Exception as e:
            logger.error(f"MSG91 SendHTTP API exception: {str(e)}")
            return {
                'success': False,
                'error': str(e)
            }
    
    def send_whatsapp(self, to, message, **kwargs):
        """WhatsApp not supported by MSG91"""
        return {'success': False, 'error': 'WhatsApp not supported'}
    
    def get_delivery_status(self, message_id):
        """Get delivery status from MSG91"""
        try:
            url = f"https://api.msg91.com/api/v5/sms/status/{message_id}"
            headers = {"authkey": self.auth_key}
            
            response = requests.get(url, headers=headers, timeout=30)
            
            if response.status_code == 200:
                return response.json()
            return None
            
        except Exception as e:
            logger.error(f"MSG91 status check failed: {str(e)}")
            return None
    
    def validate_config(self):
        """Validate MSG91 configuration"""
        return bool(self.auth_key)