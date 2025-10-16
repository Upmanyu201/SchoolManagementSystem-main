# settings/management/commands/init_settings.py
from django.core.management.base import BaseCommand
from django.db import transaction
from settings.models import SystemSettings, NotificationSettings, MLSettings
import logging

logger = logging.getLogger(__name__)

class Command(BaseCommand):
    help = 'Initialize default system settings'
    
    def add_arguments(self, parser):
        parser.add_argument(
            '--force',
            action='store_true',
            help='Force reset all settings to defaults',
        )
    
    def handle(self, *args, **options):
        force = options['force']
        
        try:
            with transaction.atomic():
                # Initialize System Settings
                if force or not SystemSettings.objects.exists():
                    if force:
                        SystemSettings.objects.all().delete()
                    
                    system_settings = SystemSettings.objects.create(
                        academic_year="2024-25",
                        late_fee_enabled=True,
                        late_fee_percentage=5.00,
                        grace_period_days=7,
                        bulk_discount_enabled=True,
                        bulk_discount_threshold=10000.00,
                        bulk_discount_percentage=2.00,
                        attendance_required_percentage=75.00,
                        attendance_warning_threshold=70.00,
                        sms_enabled=True,
                        whatsapp_enabled=False,
                        auto_fee_reminders=True,
                        reminder_days_before_due=3,
                        ml_predictions_enabled=True,
                        ml_cache_timeout=300,
                        performance_prediction_threshold=0.70,
                        session_timeout_minutes=60,
                        max_login_attempts=5,
                        lockout_duration_minutes=15,
                        auto_backup_enabled=True,
                        backup_frequency_hours=24,
                        backup_retention_days=30
                    )
                    self.stdout.write(
                        self.style.SUCCESS(f'System settings initialized: {system_settings.academic_year}')
                    )
                else:
                    self.stdout.write(
                        self.style.WARNING('System settings already exist. Use --force to reset.')
                    )
                
                # Initialize Notification Settings
                if force or not NotificationSettings.objects.exists():
                    if force:
                        NotificationSettings.objects.all().delete()
                    
                    notification_settings = NotificationSettings.objects.create(
                        sms_provider='msg91',
                        email_enabled=False,
                        smtp_port=587,
                        fee_reminder_template="Dear Parent, Fee payment of ₹{amount} is due for {student_name}. Please pay by {due_date}.",
                        payment_confirmation_template="Payment of ₹{amount} received for {student_name}. Receipt: {receipt_no}"
                    )
                    self.stdout.write(
                        self.style.SUCCESS(f'Notification settings initialized: {notification_settings.sms_provider}')
                    )
                else:
                    self.stdout.write(
                        self.style.WARNING('Notification settings already exist. Use --force to reset.')
                    )
                
                # Initialize ML Settings
                if force or not MLSettings.objects.exists():
                    if force:
                        MLSettings.objects.all().delete()
                    
                    ml_settings = MLSettings.objects.create(
                        student_performance_model_enabled=True,
                        dropout_prediction_enabled=True,
                        payment_delay_prediction_enabled=True,
                        attendance_pattern_analysis_enabled=True,
                        high_risk_threshold=0.70,
                        medium_risk_threshold=0.50,
                        ml_batch_size=100,
                        ml_cache_duration=300,
                        real_time_predictions=False,
                        batch_processing_enabled=True
                    )
                    self.stdout.write(
                        self.style.SUCCESS(f'ML settings initialized: {ml_settings.ml_batch_size} batch size')
                    )
                else:
                    self.stdout.write(
                        self.style.WARNING('ML settings already exist. Use --force to reset.')
                    )
                
                self.stdout.write(
                    self.style.SUCCESS('Settings initialization completed successfully!')
                )
                
        except Exception as e:
            logger.error(f"Settings initialization failed: {e}")
            self.stdout.write(
                self.style.ERROR(f'Settings initialization failed: {e}')
            )