# settings/models.py
from django.db import models
from django.contrib.auth import get_user_model
from django.core.validators import MinValueValidator, MaxValueValidator
from django.core.cache import cache
from decimal import Decimal
import json

User = get_user_model()

class SystemSettings(models.Model):
    """Core system configuration settings"""
    
    # Academic Settings
    academic_year = models.CharField(max_length=20, default="2024-25")
    session_start_date = models.DateField(null=True, blank=True)
    session_end_date = models.DateField(null=True, blank=True)
    
    # Fee Settings
    late_fee_enabled = models.BooleanField(default=True)
    late_fee_percentage = models.DecimalField(max_digits=5, decimal_places=2, default=Decimal('5.00'))
    grace_period_days = models.PositiveIntegerField(default=7)
    bulk_discount_enabled = models.BooleanField(default=True)
    bulk_discount_threshold = models.DecimalField(max_digits=10, decimal_places=2, default=Decimal('10000.00'))
    bulk_discount_percentage = models.DecimalField(max_digits=5, decimal_places=2, default=Decimal('2.00'))
    
    # Attendance Settings
    attendance_required_percentage = models.DecimalField(max_digits=5, decimal_places=2, default=Decimal('75.00'))
    attendance_warning_threshold = models.DecimalField(max_digits=5, decimal_places=2, default=Decimal('70.00'))
    
    # Messaging Settings
    sms_enabled = models.BooleanField(default=True)
    whatsapp_enabled = models.BooleanField(default=False)
    auto_fee_reminders = models.BooleanField(default=True)
    reminder_days_before_due = models.PositiveIntegerField(default=3)
    
    # ML Settings
    ml_predictions_enabled = models.BooleanField(default=True)
    ml_cache_timeout = models.PositiveIntegerField(default=300)  # 5 minutes
    performance_prediction_threshold = models.DecimalField(max_digits=3, decimal_places=2, default=Decimal('0.70'))
    
    # Security Settings
    session_timeout_minutes = models.PositiveIntegerField(default=60)
    max_login_attempts = models.PositiveIntegerField(default=5)
    lockout_duration_minutes = models.PositiveIntegerField(default=15)
    
    # Backup Settings
    auto_backup_enabled = models.BooleanField(default=True)
    backup_frequency_hours = models.PositiveIntegerField(default=24)
    backup_retention_days = models.PositiveIntegerField(default=30)
    
    # System Metadata
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    updated_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True)
    
    class Meta:
        verbose_name = "System Settings"
        verbose_name_plural = "System Settings"
    
    @classmethod
    def get_settings(cls):
        """Get current system settings (cached)"""
        settings = cache.get('system_settings')
        if not settings:
            settings, created = cls.objects.get_or_create(pk=1)
            cache.set('system_settings', settings, 3600)  # Cache for 1 hour
        return settings
    
    def save(self, *args, **kwargs):
        """Clear cache when settings are updated"""
        super().save(*args, **kwargs)
        cache.delete('system_settings')
    
    def __str__(self):
        return f"System Settings - {self.academic_year}"

class NotificationSettings(models.Model):
    """Notification and messaging configuration"""
    
    # SMS Configuration
    sms_provider = models.CharField(max_length=50, choices=[
        ('msg91', 'MSG91'),
        ('twilio', 'Twilio'),
        ('textlocal', 'TextLocal')
    ], default='msg91')
    sms_api_key = models.CharField(max_length=200, blank=True)
    sms_sender_id = models.CharField(max_length=20, blank=True)
    
    # WhatsApp Configuration
    whatsapp_api_key = models.CharField(max_length=200, blank=True)
    whatsapp_phone_number_id = models.CharField(max_length=50, blank=True)
    
    # Email Configuration
    email_enabled = models.BooleanField(default=False)
    smtp_host = models.CharField(max_length=100, blank=True)
    smtp_port = models.PositiveIntegerField(default=587)
    smtp_username = models.CharField(max_length=100, blank=True)
    smtp_password = models.CharField(max_length=200, blank=True)
    
    # Notification Templates
    fee_reminder_template = models.TextField(default="Dear Parent, Fee payment of ₹{amount} is due for {student_name}. Please pay by {due_date}.")
    payment_confirmation_template = models.TextField(default="Payment of ₹{amount} received for {student_name}. Receipt: {receipt_no}")
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = "Notification Settings"
        verbose_name_plural = "Notification Settings"
    
    @classmethod
    def get_settings(cls):
        """Get notification settings (cached)"""
        settings = cache.get('notification_settings')
        if not settings:
            settings, created = cls.objects.get_or_create(pk=1)
            cache.set('notification_settings', settings, 3600)
        return settings
    
    def save(self, *args, **kwargs):
        super().save(*args, **kwargs)
        cache.delete('notification_settings')

class MLSettings(models.Model):
    """Machine Learning configuration"""
    
    # Model Settings
    student_performance_model_enabled = models.BooleanField(default=True)
    dropout_prediction_enabled = models.BooleanField(default=True)
    payment_delay_prediction_enabled = models.BooleanField(default=True)
    attendance_pattern_analysis_enabled = models.BooleanField(default=True)
    
    # Thresholds
    high_risk_threshold = models.DecimalField(max_digits=3, decimal_places=2, default=Decimal('0.70'))
    medium_risk_threshold = models.DecimalField(max_digits=3, decimal_places=2, default=Decimal('0.50'))
    
    # Performance Settings
    ml_batch_size = models.PositiveIntegerField(default=100)
    ml_cache_duration = models.PositiveIntegerField(default=300)  # seconds
    
    # Feature Flags
    real_time_predictions = models.BooleanField(default=False)
    batch_processing_enabled = models.BooleanField(default=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = "ML Settings"
        verbose_name_plural = "ML Settings"
    
    @classmethod
    def get_settings(cls):
        """Get ML settings (cached)"""
        settings = cache.get('ml_settings')
        if not settings:
            settings, created = cls.objects.get_or_create(pk=1)
            cache.set('ml_settings', settings, 3600)
        return settings

class UserPreferences(models.Model):
    """Individual user preferences"""
    
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='preferences')
    
    # UI Preferences
    theme = models.CharField(max_length=20, choices=[
        ('light', 'Light'),
        ('dark', 'Dark'),
        ('auto', 'Auto')
    ], default='light')
    
    language = models.CharField(max_length=10, choices=[
        ('en', 'English'),
        ('hi', 'Hindi')
    ], default='en')
    
    # Dashboard Preferences
    dashboard_layout = models.CharField(max_length=20, choices=[
        ('compact', 'Compact'),
        ('detailed', 'Detailed'),
        ('cards', 'Cards')
    ], default='detailed')
    
    items_per_page = models.PositiveIntegerField(default=25, validators=[
        MinValueValidator(10), MaxValueValidator(100)
    ])
    
    # Notification Preferences
    email_notifications = models.BooleanField(default=True)
    sms_notifications = models.BooleanField(default=False)
    desktop_notifications = models.BooleanField(default=True)
    
    # Module Preferences (JSON field for flexibility)
    module_settings = models.JSONField(default=dict, blank=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = "User Preferences"
        verbose_name_plural = "User Preferences"
    
    def get_preference(self, key, default=None):
        """Get a specific preference value"""
        return self.module_settings.get(key, default)
    
    def set_preference(self, key, value):
        """Set a specific preference value"""
        self.module_settings[key] = value
        self.save()

class SystemHealth(models.Model):
    """System health monitoring"""
    
    # Database Health
    db_size_mb = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    db_connections = models.PositiveIntegerField(default=0)
    
    # Performance Metrics
    avg_response_time_ms = models.DecimalField(max_digits=8, decimal_places=2, default=0)
    memory_usage_mb = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    cpu_usage_percent = models.DecimalField(max_digits=5, decimal_places=2, default=0)
    
    # ML Model Health
    ml_models_loaded = models.PositiveIntegerField(default=0)
    ml_prediction_accuracy = models.DecimalField(max_digits=5, decimal_places=2, default=0)
    
    # System Status
    status = models.CharField(max_length=20, choices=[
        ('healthy', 'Healthy'),
        ('warning', 'Warning'),
        ('critical', 'Critical')
    ], default='healthy')
    
    last_backup = models.DateTimeField(null=True, blank=True)
    last_ml_training = models.DateTimeField(null=True, blank=True)
    
    timestamp = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        verbose_name = "System Health"
        verbose_name_plural = "System Health Records"
        ordering = ['-timestamp']
    
    @classmethod
    def get_latest_health(cls):
        """Get latest system health record"""
        return cls.objects.first()

class AuditLog(models.Model):
    """Settings change audit log"""
    
    user = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='settings_audit_logs')
    action = models.CharField(max_length=50)
    model_name = models.CharField(max_length=50)
    object_id = models.PositiveIntegerField(null=True, blank=True)
    changes = models.JSONField(default=dict)
    ip_address = models.GenericIPAddressField(null=True, blank=True)
    timestamp = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        verbose_name = "Audit Log"
        verbose_name_plural = "Audit Logs"
        ordering = ['-timestamp']
    
    def __str__(self):
        return f"{self.user} - {self.action} - {self.model_name}"