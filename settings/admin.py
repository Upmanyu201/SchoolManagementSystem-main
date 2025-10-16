# settings/admin.py
from django.contrib import admin
from django.utils.html import format_html
from django.urls import reverse
from django.utils.safestring import mark_safe
from .models import SystemSettings, NotificationSettings, MLSettings, UserPreferences, SystemHealth, AuditLog

@admin.register(SystemSettings)
class SystemSettingsAdmin(admin.ModelAdmin):
    list_display = ['academic_year', 'late_fee_enabled', 'ml_predictions_enabled', 'auto_backup_enabled', 'updated_at', 'updated_by']
    list_filter = ['late_fee_enabled', 'ml_predictions_enabled', 'auto_backup_enabled', 'sms_enabled', 'whatsapp_enabled']
    search_fields = ['academic_year']
    readonly_fields = ['created_at', 'updated_at']
    
    fieldsets = (
        ('Academic Settings', {
            'fields': ('academic_year', 'session_start_date', 'session_end_date')
        }),
        ('Fee Management', {
            'fields': ('late_fee_enabled', 'late_fee_percentage', 'grace_period_days', 
                      'bulk_discount_enabled', 'bulk_discount_threshold', 'bulk_discount_percentage')
        }),
        ('Attendance', {
            'fields': ('attendance_required_percentage', 'attendance_warning_threshold')
        }),
        ('Messaging', {
            'fields': ('sms_enabled', 'whatsapp_enabled', 'auto_fee_reminders', 'reminder_days_before_due')
        }),
        ('Machine Learning', {
            'fields': ('ml_predictions_enabled', 'ml_cache_timeout', 'performance_prediction_threshold')
        }),
        ('Security', {
            'fields': ('session_timeout_minutes', 'max_login_attempts', 'lockout_duration_minutes')
        }),
        ('Backup', {
            'fields': ('auto_backup_enabled', 'backup_frequency_hours', 'backup_retention_days')
        }),
        ('Metadata', {
            'fields': ('created_at', 'updated_at', 'updated_by'),
            'classes': ('collapse',)
        })
    )
    
    def has_add_permission(self, request):
        # Only allow one settings instance
        return not SystemSettings.objects.exists()
    
    def has_delete_permission(self, request, obj=None):
        # Don't allow deletion of settings
        return False

@admin.register(NotificationSettings)
class NotificationSettingsAdmin(admin.ModelAdmin):
    list_display = ['sms_provider', 'email_enabled', 'created_at', 'updated_at']
    list_filter = ['sms_provider', 'email_enabled']
    readonly_fields = ['created_at', 'updated_at']
    
    fieldsets = (
        ('SMS Configuration', {
            'fields': ('sms_provider', 'sms_api_key', 'sms_sender_id')
        }),
        ('WhatsApp Configuration', {
            'fields': ('whatsapp_api_key', 'whatsapp_phone_number_id')
        }),
        ('Email Configuration', {
            'fields': ('email_enabled', 'smtp_host', 'smtp_port', 'smtp_username', 'smtp_password')
        }),
        ('Message Templates', {
            'fields': ('fee_reminder_template', 'payment_confirmation_template')
        }),
        ('Metadata', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        })
    )
    
    def has_add_permission(self, request):
        return not NotificationSettings.objects.exists()
    
    def has_delete_permission(self, request, obj=None):
        return False

@admin.register(MLSettings)
class MLSettingsAdmin(admin.ModelAdmin):
    list_display = ['student_performance_model_enabled', 'dropout_prediction_enabled', 
                   'real_time_predictions', 'batch_processing_enabled', 'updated_at']
    list_filter = ['student_performance_model_enabled', 'dropout_prediction_enabled', 
                  'payment_delay_prediction_enabled', 'attendance_pattern_analysis_enabled',
                  'real_time_predictions', 'batch_processing_enabled']
    readonly_fields = ['created_at', 'updated_at']
    
    fieldsets = (
        ('Model Enablement', {
            'fields': ('student_performance_model_enabled', 'dropout_prediction_enabled',
                      'payment_delay_prediction_enabled', 'attendance_pattern_analysis_enabled')
        }),
        ('Thresholds', {
            'fields': ('high_risk_threshold', 'medium_risk_threshold')
        }),
        ('Performance Settings', {
            'fields': ('ml_batch_size', 'ml_cache_duration')
        }),
        ('Feature Flags', {
            'fields': ('real_time_predictions', 'batch_processing_enabled')
        }),
        ('Metadata', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        })
    )
    
    def has_add_permission(self, request):
        return not MLSettings.objects.exists()
    
    def has_delete_permission(self, request, obj=None):
        return False

@admin.register(UserPreferences)
class UserPreferencesAdmin(admin.ModelAdmin):
    list_display = ['user', 'theme', 'language', 'dashboard_layout', 'items_per_page', 'updated_at']
    list_filter = ['theme', 'language', 'dashboard_layout', 'email_notifications', 'sms_notifications']
    search_fields = ['user__username', 'user__email', 'user__first_name', 'user__last_name']
    readonly_fields = ['created_at', 'updated_at']
    
    fieldsets = (
        ('User', {
            'fields': ('user',)
        }),
        ('UI Preferences', {
            'fields': ('theme', 'language', 'dashboard_layout', 'items_per_page')
        }),
        ('Notification Preferences', {
            'fields': ('email_notifications', 'sms_notifications', 'desktop_notifications')
        }),
        ('Module Settings', {
            'fields': ('module_settings',),
            'classes': ('collapse',)
        }),
        ('Metadata', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        })
    )

@admin.register(SystemHealth)
class SystemHealthAdmin(admin.ModelAdmin):
    list_display = ['timestamp', 'status', 'db_size_mb', 'avg_response_time_ms', 
                   'memory_usage_mb', 'cpu_usage_percent', 'ml_models_loaded']
    list_filter = ['status', 'timestamp']
    readonly_fields = ['timestamp']
    date_hierarchy = 'timestamp'
    
    fieldsets = (
        ('System Status', {
            'fields': ('status', 'timestamp')
        }),
        ('Database Health', {
            'fields': ('db_size_mb', 'db_connections')
        }),
        ('Performance Metrics', {
            'fields': ('avg_response_time_ms', 'memory_usage_mb', 'cpu_usage_percent')
        }),
        ('ML Model Health', {
            'fields': ('ml_models_loaded', 'ml_prediction_accuracy')
        }),
        ('Last Operations', {
            'fields': ('last_backup', 'last_ml_training'),
            'classes': ('collapse',)
        })
    )
    
    def has_add_permission(self, request):
        # Health records are auto-generated
        return False
    
    def has_change_permission(self, request, obj=None):
        # Health records are read-only
        return False

@admin.register(AuditLog)
class AuditLogAdmin(admin.ModelAdmin):
    list_display = ['timestamp', 'user', 'action', 'model_name', 'object_id', 'ip_address']
    list_filter = ['action', 'model_name', 'timestamp']
    search_fields = ['user__username', 'action', 'model_name', 'ip_address']
    readonly_fields = ['timestamp', 'user', 'action', 'model_name', 'object_id', 'changes', 'ip_address']
    date_hierarchy = 'timestamp'
    
    fieldsets = (
        ('Action Details', {
            'fields': ('timestamp', 'user', 'action', 'model_name', 'object_id')
        }),
        ('Changes', {
            'fields': ('changes',),
            'classes': ('collapse',)
        }),
        ('Request Info', {
            'fields': ('ip_address',),
            'classes': ('collapse',)
        })
    )
    
    def has_add_permission(self, request):
        # Audit logs are auto-generated
        return False
    
    def has_change_permission(self, request, obj=None):
        # Audit logs are read-only
        return False
    
    def has_delete_permission(self, request, obj=None):
        # Only superusers can delete audit logs
        return request.user.is_superuser

# Custom admin site configuration
admin.site.site_header = "School Management System - Settings"
admin.site.site_title = "Settings Admin"
admin.site.index_title = "System Configuration"