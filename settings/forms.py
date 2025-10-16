# settings/forms.py
from django import forms
from django.contrib.auth.forms import PasswordChangeForm
from django.core.validators import MinValueValidator, MaxValueValidator
from .models import SystemSettings, NotificationSettings, MLSettings, UserPreferences
from decimal import Decimal

class SystemSettingsForm(forms.ModelForm):
    """Form for system-wide settings"""
    
    class Meta:
        model = SystemSettings
        fields = [
            'academic_year', 'session_start_date', 'session_end_date',
            'late_fee_enabled', 'late_fee_percentage', 'grace_period_days',
            'bulk_discount_enabled', 'bulk_discount_threshold', 'bulk_discount_percentage',
            'attendance_required_percentage', 'attendance_warning_threshold',
            'sms_enabled', 'whatsapp_enabled', 'auto_fee_reminders', 'reminder_days_before_due',
            'ml_predictions_enabled', 'ml_cache_timeout', 'performance_prediction_threshold',
            'session_timeout_minutes', 'max_login_attempts', 'lockout_duration_minutes',
            'auto_backup_enabled', 'backup_frequency_hours', 'backup_retention_days'
        ]
        widgets = {
            'academic_year': forms.TextInput(attrs={
                'class': 'w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500',
                'placeholder': '2024-25'
            }),
            'session_start_date': forms.DateInput(attrs={
                'type': 'date',
                'class': 'w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500'
            }),
            'session_end_date': forms.DateInput(attrs={
                'type': 'date',
                'class': 'w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500'
            }),
            'late_fee_percentage': forms.NumberInput(attrs={
                'class': 'w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500',
                'step': '0.01',
                'min': '0',
                'max': '100'
            }),
            'grace_period_days': forms.NumberInput(attrs={
                'class': 'w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500',
                'min': '0',
                'max': '30'
            }),
            'bulk_discount_threshold': forms.NumberInput(attrs={
                'class': 'w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500',
                'step': '0.01'
            }),
            'bulk_discount_percentage': forms.NumberInput(attrs={
                'class': 'w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500',
                'step': '0.01',
                'min': '0',
                'max': '50'
            }),
            'attendance_required_percentage': forms.NumberInput(attrs={
                'class': 'w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500',
                'step': '0.01',
                'min': '0',
                'max': '100'
            }),
            'attendance_warning_threshold': forms.NumberInput(attrs={
                'class': 'w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500',
                'step': '0.01',
                'min': '0',
                'max': '100'
            }),
            'reminder_days_before_due': forms.NumberInput(attrs={
                'class': 'w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500',
                'min': '1',
                'max': '30'
            }),
            'ml_cache_timeout': forms.NumberInput(attrs={
                'class': 'w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500',
                'min': '60',
                'max': '3600'
            }),
            'performance_prediction_threshold': forms.NumberInput(attrs={
                'class': 'w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500',
                'step': '0.01',
                'min': '0',
                'max': '1'
            }),
            'session_timeout_minutes': forms.NumberInput(attrs={
                'class': 'w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500',
                'min': '15',
                'max': '480'
            }),
            'max_login_attempts': forms.NumberInput(attrs={
                'class': 'w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500',
                'min': '3',
                'max': '10'
            }),
            'lockout_duration_minutes': forms.NumberInput(attrs={
                'class': 'w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500',
                'min': '5',
                'max': '60'
            }),
            'backup_frequency_hours': forms.NumberInput(attrs={
                'class': 'w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500',
                'min': '1',
                'max': '168'
            }),
            'backup_retention_days': forms.NumberInput(attrs={
                'class': 'w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500',
                'min': '7',
                'max': '365'
            })
        }

class NotificationSettingsForm(forms.ModelForm):
    """Form for notification settings"""
    
    # Add missing fields for template compatibility
    sms_enabled = forms.BooleanField(required=False, label="Enable SMS Notifications")
    use_tls = forms.BooleanField(required=False, label="Use TLS")
    from_email = forms.EmailField(required=False, label="From Email Address")
    email_username = forms.CharField(required=False, label="Email Username")
    fee_reminders = forms.BooleanField(required=False, label="Fee Payment Reminders")
    attendance_alerts = forms.BooleanField(required=False, label="Attendance Alerts")
    exam_notifications = forms.BooleanField(required=False, label="Exam Notifications")
    general_announcements = forms.BooleanField(required=False, label="General Announcements")
    
    class Meta:
        model = NotificationSettings
        fields = [
            'sms_provider', 'sms_api_key', 'sms_sender_id',
            'whatsapp_api_key', 'whatsapp_phone_number_id',
            'email_enabled', 'smtp_host', 'smtp_port', 'smtp_username', 'smtp_password',
            'fee_reminder_template', 'payment_confirmation_template'
        ]
        widgets = {
            'sms_provider': forms.Select(attrs={
                'class': 'w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500'
            }),
            'sms_api_key': forms.PasswordInput(attrs={
                'class': 'w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500',
                'placeholder': 'Enter SMS API Key'
            }),
            'sms_sender_id': forms.TextInput(attrs={
                'class': 'w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500',
                'placeholder': 'SCHOOL'
            }),
            'whatsapp_api_key': forms.PasswordInput(attrs={
                'class': 'w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500',
                'placeholder': 'Enter WhatsApp API Key'
            }),
            'whatsapp_phone_number_id': forms.TextInput(attrs={
                'class': 'w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500',
                'placeholder': 'Phone Number ID'
            }),
            'smtp_host': forms.TextInput(attrs={
                'class': 'w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500',
                'placeholder': 'smtp.gmail.com'
            }),
            'smtp_port': forms.NumberInput(attrs={
                'class': 'w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500',
                'min': '1',
                'max': '65535'
            }),
            'smtp_username': forms.TextInput(attrs={
                'class': 'w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500',
                'placeholder': 'your-email@gmail.com'
            }),
            'smtp_password': forms.PasswordInput(attrs={
                'class': 'w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500',
                'placeholder': 'App Password'
            }),
            'fee_reminder_template': forms.Textarea(attrs={
                'class': 'w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500',
                'rows': 3,
                'placeholder': 'Use {student_name}, {amount}, {due_date} as placeholders'
            }),
            'payment_confirmation_template': forms.Textarea(attrs={
                'class': 'w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500',
                'rows': 3,
                'placeholder': 'Use {student_name}, {amount}, {receipt_no} as placeholders'
            })
        }
        
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Set initial values for additional fields
        if hasattr(self, 'instance') and self.instance.pk:
            self.fields['sms_enabled'].initial = True
            self.fields['use_tls'].initial = True
            self.fields['from_email'].initial = self.instance.smtp_username
            self.fields['email_username'].initial = self.instance.smtp_username
            self.fields['fee_reminders'].initial = True
            self.fields['attendance_alerts'].initial = True
            self.fields['exam_notifications'].initial = True
            self.fields['general_announcements'].initial = True

class MLSettingsForm(forms.ModelForm):
    """Form for ML configuration"""
    
    class Meta:
        model = MLSettings
        fields = [
            'student_performance_model_enabled', 'dropout_prediction_enabled',
            'payment_delay_prediction_enabled', 'attendance_pattern_analysis_enabled',
            'high_risk_threshold', 'medium_risk_threshold',
            'ml_batch_size', 'ml_cache_duration',
            'real_time_predictions', 'batch_processing_enabled'
        ]
        widgets = {
            'high_risk_threshold': forms.NumberInput(attrs={
                'class': 'w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500',
                'step': '0.01',
                'min': '0',
                'max': '1'
            }),
            'medium_risk_threshold': forms.NumberInput(attrs={
                'class': 'w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500',
                'step': '0.01',
                'min': '0',
                'max': '1'
            }),
            'ml_batch_size': forms.NumberInput(attrs={
                'class': 'w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500',
                'min': '10',
                'max': '1000'
            }),
            'ml_cache_duration': forms.NumberInput(attrs={
                'class': 'w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500',
                'min': '60',
                'max': '3600'
            })
        }

class UserPreferencesForm(forms.ModelForm):
    """Form for user preferences"""
    
    # Add missing fields for template compatibility
    timezone = forms.CharField(required=False, label="Timezone", initial="UTC")
    date_format = forms.ChoiceField(
        choices=[('Y-m-d', 'YYYY-MM-DD'), ('d/m/Y', 'DD/MM/YYYY'), ('m/d/Y', 'MM/DD/YYYY')],
        required=False, label="Date Format"
    )
    dashboard_widgets = forms.BooleanField(required=False, label="Show Dashboard Widgets")
    
    class Meta:
        model = UserPreferences
        fields = [
            'theme', 'language', 'dashboard_layout', 'items_per_page',
            'email_notifications', 'sms_notifications', 'desktop_notifications'
        ]
        widgets = {
            'theme': forms.Select(attrs={
                'class': 'w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500'
            }),
            'language': forms.Select(attrs={
                'class': 'w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500'
            }),
            'dashboard_layout': forms.Select(attrs={
                'class': 'w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500'
            }),
            'items_per_page': forms.NumberInput(attrs={
                'class': 'w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500',
                'min': '10',
                'max': '100'
            })
        }
        
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Add styling to additional fields
        self.fields['timezone'].widget.attrs.update({
            'class': 'w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500'
        })
        self.fields['date_format'].widget.attrs.update({
            'class': 'w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500'
        })

class LanguageSettingsForm(forms.Form):
    """Simple language selection form"""
    
    LANGUAGE_CHOICES = [
        ('en', 'English'),
        ('hi', 'हिन्दी (Hindi)')
    ]
    
    language = forms.ChoiceField(
        choices=LANGUAGE_CHOICES,
        widget=forms.RadioSelect(attrs={
            'class': 'language-radio'
        })
    )

class SecuritySettingsForm(forms.Form):
    """Security configuration form"""
    
    enable_two_factor = forms.BooleanField(required=False, label="Enable Two-Factor Authentication")
    force_password_change = forms.BooleanField(required=False, label="Force Password Change on Next Login")
    enable_login_notifications = forms.BooleanField(required=False, label="Email Login Notifications")
    
    session_timeout = forms.IntegerField(
        min_value=15,
        max_value=480,
        initial=60,
        label="Session Timeout (minutes)",
        widget=forms.NumberInput(attrs={
            'class': 'w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500'
        })
    )
    
    max_login_attempts = forms.IntegerField(
        min_value=3,
        max_value=10,
        initial=5,
        label="Maximum Login Attempts",
        widget=forms.NumberInput(attrs={
            'class': 'w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500'
        })
    )

class BackupSettingsForm(forms.Form):
    """Backup configuration form"""
    
    auto_backup_enabled = forms.BooleanField(required=False, label="Enable Automatic Backups")
    backup_frequency = forms.ChoiceField(
        choices=[
            ('daily', 'Daily'),
            ('weekly', 'Weekly'),
            ('monthly', 'Monthly')
        ],
        widget=forms.Select(attrs={
            'class': 'w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500'
        })
    )
    
    retention_days = forms.IntegerField(
        min_value=7,
        max_value=365,
        initial=30,
        label="Backup Retention (days)",
        widget=forms.NumberInput(attrs={
            'class': 'w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500'
        })
    )
    
    include_media_files = forms.BooleanField(required=False, label="Include Media Files in Backup")
    compress_backups = forms.BooleanField(required=False, initial=True, label="Compress Backup Files")

class SystemMaintenanceForm(forms.Form):
    """System maintenance operations"""
    
    # Maintenance Mode Settings
    maintenance_mode = forms.BooleanField(required=False, label="Enable Maintenance Mode")
    maintenance_message = forms.CharField(
        required=False,
        widget=forms.Textarea(attrs={
            'class': 'w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500',
            'rows': 3,
            'placeholder': 'System is under maintenance. Please try again later.'
        }),
        label="Maintenance Message"
    )
    
    # Backup Settings
    auto_backup = forms.BooleanField(required=False, label="Enable Auto Backup")
    backup_frequency = forms.ChoiceField(
        choices=[('daily', 'Daily'), ('weekly', 'Weekly'), ('monthly', 'Monthly')],
        required=False,
        widget=forms.Select(attrs={
            'class': 'w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500'
        })
    )
    
    # System Cleanup
    auto_cleanup = forms.BooleanField(required=False, label="Enable Auto Cleanup")
    log_retention_days = forms.IntegerField(
        required=False,
        initial=30,
        widget=forms.NumberInput(attrs={
            'class': 'w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500',
            'min': '7', 'max': '365'
        })
    )
    
    # Update Settings
    auto_updates = forms.BooleanField(required=False, label="Enable Auto Updates")
    update_channel = forms.ChoiceField(
        choices=[('stable', 'Stable'), ('beta', 'Beta'), ('dev', 'Development')],
        required=False,
        widget=forms.Select(attrs={
            'class': 'w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500'
        })
    )