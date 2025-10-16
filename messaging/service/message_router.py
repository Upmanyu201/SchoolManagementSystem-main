from typing import Dict, Any, Optional
from django.conf import settings
try:
    from ..providers.messagecentral_provider import MessageCentralProvider
except ImportError:
    MessageCentralProvider = None
import logging

logger = logging.getLogger(__name__)

class MessageRouter:
    """Routes messages to appropriate providers with fallback"""
    
    def __init__(self):
        self.providers = {}
        self._initialize_providers()
    
    def _initialize_providers(self):
        """Initialize messaging providers"""
        # MessageCentral provider
        messagecentral_config = {
            'customer_id': getattr(settings, 'MESSAGECENTRAL_CUSTOMER_ID', ''),
            'auth_token': getattr(settings, 'MESSAGECENTRAL_AUTH_TOKEN', ''),
            'sender_id': getattr(settings, 'MESSAGECENTRAL_SENDER_ID', 'SCHOOL')
        }
        
        if MessageCentralProvider and messagecentral_config['customer_id'] and messagecentral_config['auth_token']:
            self.providers['messagecentral'] = MessageCentralProvider(messagecentral_config)
    
    def send_sms(self, to: str, message: str, message_type: str = 'custom', 
                 provider: Optional[str] = None) -> Dict[str, Any]:
        """Send SMS with provider fallback"""
        
        # Determine provider
        if not provider:
            provider = getattr(settings, 'DEFAULT_SMS_PROVIDER', 'messagecentral')
        
        # Try primary provider
        if provider in self.providers:
            result = self.providers[provider].send_sms(to, message)
            if result['success']:
                return result
            
            logger.warning(f"Primary provider {provider} failed: {result.get('error')}")
        
        # Try fallback providers if enabled
        if getattr(settings, 'ENABLE_PROVIDER_FALLBACK', True):
            for fallback_provider, provider_instance in self.providers.items():
                if fallback_provider != provider:
                    logger.info(f"Trying fallback provider: {fallback_provider}")
                    result = provider_instance.send_sms(to, message)
                    if result['success']:
                        return result
        
        return {
            'success': False,
            'error': 'All providers failed',
            'provider': 'none'
        }
    
    def send_whatsapp(self, to: str, message: str, message_type: str = 'custom',
                     provider: Optional[str] = None) -> Dict[str, Any]:
        """Send WhatsApp with provider fallback"""
        
        # Determine provider
        if not provider:
            provider = getattr(settings, 'DEFAULT_WHATSAPP_PROVIDER', 'messagecentral')
        
        # Try primary provider
        if provider in self.providers:
            result = self.providers[provider].send_whatsapp(to, message)
            if result['success']:
                return result
            
            logger.warning(f"Primary WhatsApp provider {provider} failed: {result.get('error')}")
        
        # Try fallback providers if enabled
        if getattr(settings, 'ENABLE_PROVIDER_FALLBACK', True):
            for fallback_provider, provider_instance in self.providers.items():
                if fallback_provider != provider:
                    logger.info(f"Trying WhatsApp fallback provider: {fallback_provider}")
                    result = provider_instance.send_whatsapp(to, message)
                    if result['success']:
                        return result
        
        return {
            'success': False,
            'error': 'All WhatsApp providers failed',
            'provider': 'none'
        }

# Global message router instance
message_router = MessageRouter()