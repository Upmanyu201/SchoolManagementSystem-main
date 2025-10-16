from abc import ABC, abstractmethod
from typing import Dict, Any

class BaseMessagingProvider(ABC):
    """Base class for messaging providers"""
    
    def __init__(self, config: Dict[str, Any]):
        self.config = config
    
    @abstractmethod
    def send_sms(self, to: str, message: str, **kwargs) -> Dict[str, Any]:
        """Send SMS message"""
        pass
    
    @abstractmethod
    def send_whatsapp(self, to: str, message: str, **kwargs) -> Dict[str, Any]:
        """Send WhatsApp message"""
        pass
    
    @abstractmethod
    def get_delivery_status(self, message_id: str) -> Dict[str, Any]:
        """Get delivery status of a message"""
        pass
    
    @abstractmethod
    def validate_config(self) -> bool:
        """Validate provider configuration"""
        pass