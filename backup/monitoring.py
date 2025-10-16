
"""
Backup System Monitoring and Alerting
Addresses issues #83-85 from additional_issues_report.md
"""

import logging
import time
from django.core.cache import cache
from django.core.mail import send_mail
from django.conf import settings
from django.utils import timezone
from .models import BackupJob, RestoreJob
import json

logger = logging.getLogger('backup.monitoring')

class BackupMetrics:
    """Collect and track backup system metrics."""
    
    @staticmethod
    def record_operation_metric(operation_type, duration, success=True, file_size=0):
        """Record operation metrics."""
        timestamp = int(time.time())
        metric_key = f"backup_metrics_{operation_type}_{timestamp // 3600}"  # Hourly buckets
        
        metrics = cache.get(metric_key, {
            'operations': 0,
            'successes': 0,
            'failures': 0,
            'total_duration': 0,
            'total_size': 0,
            'avg_duration': 0,
            'avg_size': 0
        })
        
        metrics['operations'] += 1
        metrics['total_duration'] += duration
        metrics['total_size'] += file_size
        
        if success:
            metrics['successes'] += 1
        else:
            metrics['failures'] += 1
        
        # Calculate averages
        metrics['avg_duration'] = metrics['total_duration'] / metrics['operations']
        metrics['avg_size'] = metrics['total_size'] / metrics['operations'] if metrics['operations'] > 0 else 0
        
        cache.set(metric_key, metrics, 86400)  # Keep for 24 hours
        
        logger.info(f"Recorded {operation_type} metric: duration={duration:.2f}s, success={success}, size={file_size}")
    
    @staticmethod
    def get_performance_summary(hours=24):
        """Get performance summary for the last N hours."""
        current_hour = int(time.time()) // 3600
        summary = {
            'total_operations': 0,
            'total_successes': 0,
            'total_failures': 0,
            'avg_duration': 0,
            'avg_size': 0,
            'success_rate': 0
        }
        
        total_duration = 0
        total_size = 0
        
        for hour_offset in range(hours):
            hour_key = current_hour - hour_offset
            
            for operation_type in ['backup', 'restore']:
                metric_key = f"backup_metrics_{operation_type}_{hour_key}"
                metrics = cache.get(metric_key, {})
                
                if metrics:
                    summary['total_operations'] += metrics.get('operations', 0)
                    summary['total_successes'] += metrics.get('successes', 0)
                    summary['total_failures'] += metrics.get('failures', 0)
                    total_duration += metrics.get('total_duration', 0)
                    total_size += metrics.get('total_size', 0)
        
        if summary['total_operations'] > 0:
            summary['avg_duration'] = total_duration / summary['total_operations']
            summary['avg_size'] = total_size / summary['total_operations']
            summary['success_rate'] = (summary['total_successes'] / summary['total_operations']) * 100
        
        return summary

class BackupErrorTracker:
    """Track and analyze backup system errors."""
    
    @staticmethod
    def record_error(operation_type, error_message, context=None):
        """Record error with context."""
        error_data = {
            'timestamp': timezone.now().isoformat(),
            'operation_type': operation_type,
            'error_message': str(error_message),
            'context': context or {}
        }
        
        # Store in cache for immediate access
        error_key = f"backup_error_{int(time.time())}"
        cache.set(error_key, error_data, 86400)  # Keep for 24 hours
        
        # Aggregate error counts
        count_key = f"backup_error_count_{operation_type}"
        current_count = cache.get(count_key, 0)
        cache.set(count_key, current_count + 1, 3600)  # Hourly reset
        
        logger.error(f"Backup error recorded: {operation_type} - {error_message}")
        
        # Check if alerting is needed
        BackupAlerting.check_error_threshold(operation_type, current_count + 1)
    
    @staticmethod
    def get_recent_errors(hours=24, limit=50):
        """Get recent errors."""
        current_time = int(time.time())
        start_time = current_time - (hours * 3600)
        
        errors = []
        
        # Scan cache for error keys in time range
        for timestamp in range(start_time, current_time):
            error_key = f"backup_error_{timestamp}"
            error_data = cache.get(error_key)
            if error_data:
                errors.append(error_data)
        
        # Sort by timestamp and limit
        errors.sort(key=lambda x: x['timestamp'], reverse=True)
        return errors[:limit]

class BackupAlerting:
    """Backup system alerting."""
    
    ERROR_THRESHOLD = 5  # Alert after 5 errors per hour
    FAILURE_RATE_THRESHOLD = 50  # Alert if failure rate > 50%
    
    @staticmethod
    def check_error_threshold(operation_type, error_count):
        """Check if error threshold exceeded."""
        if error_count >= BackupAlerting.ERROR_THRESHOLD:
            BackupAlerting.send_error_alert(operation_type, error_count)
    
    @staticmethod
    def check_failure_rate():
        """Check overall failure rate."""
        summary = BackupMetrics.get_performance_summary(hours=1)
        
        if (summary['total_operations'] > 0 and 
            (100 - summary['success_rate']) > BackupAlerting.FAILURE_RATE_THRESHOLD):
            BackupAlerting.send_failure_rate_alert(summary)
    
    @staticmethod
    def send_error_alert(operation_type, error_count):
        """Send error threshold alert."""
        subject = f"Backup System Alert: High Error Rate - {operation_type}"
        message = f"""
        The backup system has recorded {error_count} errors for {operation_type} operations in the last hour.
        
        This exceeds the threshold of {BackupAlerting.ERROR_THRESHOLD} errors per hour.
        
        Please check the backup system logs for details.
        
        Time: {timezone.now()}
        """
        
        BackupAlerting._send_alert_email(subject, message)
    
    @staticmethod
    def send_failure_rate_alert(summary):
        """Send failure rate alert."""
        failure_rate = 100 - summary['success_rate']
        subject = f"Backup System Alert: High Failure Rate ({failure_rate:.1f}%)"
        message = f"""
        The backup system failure rate is {failure_rate:.1f}% in the last hour.
        
        Summary:
        - Total Operations: {summary['total_operations']}
        - Successes: {summary['total_successes']}
        - Failures: {summary['total_failures']}
        - Success Rate: {summary['success_rate']:.1f}%
        
        Please investigate the backup system immediately.
        
        Time: {timezone.now()}
        """
        
        BackupAlerting._send_alert_email(subject, message)
    
    @staticmethod
    def _send_alert_email(subject, message):
        """Send alert email to administrators."""
        try:
            admin_emails = [admin[1] for admin in getattr(settings, 'ADMINS', [])]
            if admin_emails:
                send_mail(
                    subject=subject,
                    message=message,
                    from_email=getattr(settings, 'DEFAULT_FROM_EMAIL', 'noreply@school.com'),
                    recipient_list=admin_emails,
                    fail_silently=False
                )
                logger.info(f"Alert email sent: {subject}")
            else:
                logger.warning("No admin emails configured for alerts")
        except Exception as e:
            logger.error(f"Failed to send alert email: {e}")

class BackupHealthChecker:
    """Fix Issue #75: Health check system."""
    
    @staticmethod
    def check_system_health():
        """Comprehensive system health check."""
        health_status = {
            'timestamp': timezone.now().isoformat(),
            'overall_status': 'healthy',
            'checks': {}
        }
        
        # Check backup directory
        health_status['checks']['backup_directory'] = BackupHealthChecker._check_backup_directory()
        
        # Check recent backup success
        health_status['checks']['recent_backups'] = BackupHealthChecker._check_recent_backups()
        
        # Check disk space
        health_status['checks']['disk_space'] = BackupHealthChecker._check_disk_space()
        
        # Check database connectivity
        health_status['checks']['database'] = BackupHealthChecker._check_database()
        
        # Determine overall status
        failed_checks = [check for check in health_status['checks'].values() if not check['status']]
        if failed_checks:
            health_status['overall_status'] = 'unhealthy'
        
        return health_status
    
    @staticmethod
    def _check_backup_directory():
        """Check backup directory accessibility."""
        try:
            backup_dir = Path(settings.BASE_DIR) / 'backups'
            backup_dir.mkdir(exist_ok=True)
            
            # Test write access
            test_file = backup_dir / 'health_check.tmp'
            test_file.write_text('health check')
            test_file.unlink()
            
            return {'status': True, 'message': 'Backup directory accessible'}
        except Exception as e:
            return {'status': False, 'message': f'Backup directory error: {e}'}
    
    @staticmethod
    def _check_recent_backups():
        """Check if recent backups were successful."""
        try:
            recent_backup = BackupJob.objects.filter(
                created_at__gte=timezone.now() - timezone.timedelta(days=1)
            ).order_by('-created_at').first()
            
            if not recent_backup:
                return {'status': False, 'message': 'No backups in last 24 hours'}
            
            if recent_backup.status != 'success':
                return {'status': False, 'message': f'Last backup failed: {recent_backup.status}'}
            
            return {'status': True, 'message': 'Recent backups successful'}
        except Exception as e:
            return {'status': False, 'message': f'Error checking recent backups: {e}'}
    
    @staticmethod
    def _check_disk_space():
        """Check available disk space."""
        try:
            import shutil
            backup_dir = Path(settings.BASE_DIR) / 'backups'
            total, used, free = shutil.disk_usage(backup_dir)
            
            free_percent = (free / total) * 100
            
            if free_percent < 10:
                return {'status': False, 'message': f'Low disk space: {free_percent:.1f}% free'}
            
            return {'status': True, 'message': f'Disk space OK: {free_percent:.1f}% free'}
        except Exception as e:
            return {'status': False, 'message': f'Error checking disk space: {e}'}
    
    @staticmethod
    def _check_database():
        """Check database connectivity."""
        try:
            from django.db import connection
            with connection.cursor() as cursor:
                cursor.execute("SELECT 1")
            return {'status': True, 'message': 'Database connection OK'}
        except Exception as e:
            return {'status': False, 'message': f'Database error: {e}'}

# Monitoring middleware
class BackupMonitoringMiddleware:
    """Middleware to track backup operations."""
    
    def __init__(self, get_response):
        self.get_response = get_response
    
    def __call__(self, request):
        # Check if this is a backup-related request
        if '/backup/' in request.path:
            start_time = time.time()
            
            response = self.get_response(request)
            
            duration = time.time() - start_time
            
            # Record metrics for backup operations
            if response.status_code < 400:
                BackupMetrics.record_operation_metric('api_call', duration, success=True)
            else:
                BackupMetrics.record_operation_metric('api_call', duration, success=False)
                BackupErrorTracker.record_error('api_call', f'HTTP {response.status_code}', {
                    'path': request.path,
                    'method': request.method,
                    'user': str(request.user) if hasattr(request, 'user') else 'anonymous'
                })
            
            return response
        
        return self.get_response(request)
