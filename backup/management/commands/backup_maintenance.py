"""
Django management command for backup system maintenance.
Usage: python manage.py backup_maintenance [--cleanup] [--health-check] [--metrics]
"""

from django.core.management.base import BaseCommand
from django.utils import timezone
import logging

logger = logging.getLogger('backup.maintenance')

class Command(BaseCommand):
    help = 'Perform backup system maintenance tasks'
    
    def add_arguments(self, parser):
        parser.add_argument(
            '--cleanup',
            action='store_true',
            help='Run backup cleanup (remove old backups)',
        )
        parser.add_argument(
            '--health-check',
            action='store_true',
            help='Run system health check',
        )
        parser.add_argument(
            '--metrics',
            action='store_true',
            help='Display performance metrics',
        )
        parser.add_argument(
            '--all',
            action='store_true',
            help='Run all maintenance tasks',
        )
    
    def handle(self, *args, **options):
        self.stdout.write(
            self.style.SUCCESS(f'Starting backup maintenance at {timezone.now()}')
        )
        
        if options['cleanup'] or options['all']:
            self.run_cleanup()
        
        if options['health_check'] or options['all']:
            self.run_health_check()
        
        if options['metrics'] or options['all']:
            self.show_metrics()
        
        if not any([options['cleanup'], options['health_check'], options['metrics'], options['all']]):
            self.stdout.write(
                self.style.WARNING('No maintenance tasks specified. Use --help for options.')
            )
    
    def run_cleanup(self):
        """Run backup cleanup tasks."""
        try:
            from backup.config import BackupRetentionManager
            
            self.stdout.write('Running backup cleanup...')
            
            # Clean old backups
            result = BackupRetentionManager.cleanup_old_backups()
            self.stdout.write(
                self.style.SUCCESS(
                    f'Cleanup completed: {result["files_removed"]} files, '
                    f'{result["records_removed"]} records removed'
                )
            )
            
            # Enforce backup limits
            BackupRetentionManager.enforce_backup_limits()
            self.stdout.write(self.style.SUCCESS('Backup limits enforced'))
            
            # Clean temporary files
            from backup.security import SecureFileHandler
            SecureFileHandler.cleanup_temp_files()
            self.stdout.write(self.style.SUCCESS('Temporary files cleaned'))
            
        except Exception as e:
            self.stdout.write(
                self.style.ERROR(f'Cleanup failed: {e}')
            )
            logger.error(f'Backup cleanup failed: {e}')
    
    def run_health_check(self):
        """Run system health check."""
        try:
            from backup.monitoring import BackupHealthChecker
            
            self.stdout.write('Running health check...')
            
            health_status = BackupHealthChecker.check_system_health()
            
            # Display results
            overall_status = health_status['overall_status']
            if overall_status == 'healthy':
                self.stdout.write(
                    self.style.SUCCESS(f'System Status: {overall_status.upper()}')
                )
            else:
                self.stdout.write(
                    self.style.ERROR(f'System Status: {overall_status.upper()}')
                )
            
            # Show individual check results
            for check_name, check_result in health_status['checks'].items():
                status_style = self.style.SUCCESS if check_result['status'] else self.style.ERROR
                self.stdout.write(
                    f'  {check_name}: {status_style(check_result["message"])}'
                )
            
        except Exception as e:
            self.stdout.write(
                self.style.ERROR(f'Health check failed: {e}')
            )
            logger.error(f'Health check failed: {e}')
    
    def show_metrics(self):
        """Display performance metrics."""
        try:
            from backup.monitoring import BackupMetrics
            
            self.stdout.write('Performance Metrics (Last 24 hours):')
            
            summary = BackupMetrics.get_performance_summary(hours=24)
            
            self.stdout.write(f'  Total Operations: {summary["total_operations"]}')
            self.stdout.write(f'  Successes: {summary["total_successes"]}')
            self.stdout.write(f'  Failures: {summary["total_failures"]}')
            self.stdout.write(f'  Success Rate: {summary["success_rate"]:.1f}%')
            self.stdout.write(f'  Average Duration: {summary["avg_duration"]:.2f}s')
            self.stdout.write(f'  Average Size: {summary["avg_size"]:.2f} bytes')
            
        except Exception as e:
            self.stdout.write(
                self.style.ERROR(f'Metrics display failed: {e}')
            )
            logger.error(f'Metrics display failed: {e}')
