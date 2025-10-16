# settings/signals.py
from django.db.models.signals import post_save, post_delete
from django.dispatch import receiver
from django.contrib.auth import get_user_model
from django.core.cache import cache
from .models import SystemSettings, NotificationSettings, MLSettings, UserPreferences, AuditLog
import logging

logger = logging.getLogger(__name__)
User = get_user_model()

@receiver(post_save, sender=SystemSettings)
def clear_settings_cache(sender, instance, **kwargs):
    """Clear cache when system settings are updated"""
    cache.delete('system_settings')
    logger.info("System settings cache cleared")

@receiver(post_save, sender=NotificationSettings)
def clear_notification_cache(sender, instance, **kwargs):
    """Clear cache when notification settings are updated"""
    cache.delete('notification_settings')
    logger.info("Notification settings cache cleared")

@receiver(post_save, sender=MLSettings)
def clear_ml_cache(sender, instance, **kwargs):
    """Clear cache when ML settings are updated"""
    cache.delete('ml_settings')
    logger.info("ML settings cache cleared")

@receiver(post_save, sender=User)
def create_user_preferences(sender, instance, created, **kwargs):
    """Create user preferences when a new user is created"""
    if created:
        try:
            UserPreferences.objects.create(user=instance)
            logger.info(f"User preferences created for {instance.username}")
        except Exception as e:
            logger.error(f"Failed to create user preferences for {instance.username}: {e}")

@receiver(post_save, sender=SystemSettings)
@receiver(post_save, sender=NotificationSettings)
@receiver(post_save, sender=MLSettings)
def log_settings_change(sender, instance, created, **kwargs):
    """Log settings changes for audit trail"""
    try:
        action = 'CREATE' if created else 'UPDATE'
        AuditLog.objects.create(
            action=action,
            model_name=sender.__name__,
            object_id=instance.id,
            changes={'model': sender.__name__, 'action': action}
        )
        logger.info(f"Settings change logged: {sender.__name__} {action}")
    except Exception as e:
        logger.error(f"Failed to log settings change: {e}")

@receiver(post_save, sender=SystemSettings)
def update_django_settings(sender, instance, **kwargs):
    """Update Django settings based on system settings"""
    try:
        from django.conf import settings
        
        # Update session timeout
        if hasattr(settings, 'SESSION_COOKIE_AGE'):
            settings.SESSION_COOKIE_AGE = instance.session_timeout_minutes * 60
        
        # Update cache timeout for ML
        if hasattr(settings, 'CACHES'):
            for cache_config in settings.CACHES.values():
                if 'TIMEOUT' in cache_config:
                    cache_config['TIMEOUT'] = instance.ml_cache_timeout
        
        logger.info("Django settings updated from system settings")
        
    except Exception as e:
        logger.error(f"Failed to update Django settings: {e}")

@receiver(post_save, sender=MLSettings)
def update_ml_configuration(sender, instance, **kwargs):
    """Update ML service configuration when ML settings change"""
    try:
        from core.ml_integrations import ML_AVAILABLE
        
        if ML_AVAILABLE:
            # Update ML service configuration
            cache.set('ml_config_updated', True, 60)
            logger.info("ML configuration update signal sent")
        
    except ImportError:
        logger.warning("ML service not available for configuration update")
    except Exception as e:
        logger.error(f"Failed to update ML configuration: {e}")

@receiver(post_save, sender=NotificationSettings)
def validate_notification_config(sender, instance, **kwargs):
    """Validate notification configuration when settings change"""
    try:
        # Validate SMS configuration
        if instance.sms_api_key and not instance.sms_sender_id:
            logger.warning("SMS API key provided but sender ID missing")
        
        # Validate WhatsApp configuration
        if instance.whatsapp_api_key and not instance.whatsapp_phone_number_id:
            logger.warning("WhatsApp API key provided but phone number ID missing")
        
        # Validate email configuration
        if instance.email_enabled and not instance.smtp_host:
            logger.warning("Email enabled but SMTP host not configured")
        
        logger.info("Notification configuration validated")
        
    except Exception as e:
        logger.error(f"Failed to validate notification configuration: {e}")

@receiver(post_delete, sender=AuditLog)
def log_audit_deletion(sender, instance, **kwargs):
    """Log when audit logs are deleted"""
    logger.warning(f"Audit log deleted: {instance.action} on {instance.model_name} at {instance.timestamp}")

# Signal to update fee calculation engine when settings change
@receiver(post_save, sender=SystemSettings)
def update_fee_engine_settings(sender, instance, **kwargs):
    """Update fee calculation engine when fee settings change"""
    try:
        from core.fee_calculation_engine import fee_engine
        
        # Clear fee calculation cache
        cache.delete_pattern('fee_summary_*')
        cache.delete_pattern('student_dashboard_*')
        
        logger.info("Fee calculation engine settings updated")
        
    except ImportError:
        logger.warning("Fee calculation engine not available")
    except Exception as e:
        logger.error(f"Failed to update fee engine settings: {e}")

# Signal to update messaging service when notification settings change
@receiver(post_save, sender=NotificationSettings)
def update_messaging_service(sender, instance, **kwargs):
    """Update messaging service configuration"""
    try:
        from messaging.services import NotificationService
        
        # Trigger configuration reload
        cache.set('messaging_config_updated', True, 60)
        
        logger.info("Messaging service configuration update triggered")
        
    except ImportError:
        logger.warning("Messaging service not available")
    except Exception as e:
        logger.error(f"Failed to update messaging service: {e}")