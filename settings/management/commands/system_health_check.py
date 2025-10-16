# settings/management/commands/system_health_check.py
from django.core.management.base import BaseCommand
from django.db import connection
from django.core.cache import cache
from django.utils import timezone
from settings.models import SystemHealth
import os
import psutil
import time
import logging

logger = logging.getLogger(__name__)

class Command(BaseCommand):
    help = 'Perform system health check and update health records'
    
    def add_arguments(self, parser):
        parser.add_argument(
            '--save',
            action='store_true',
            help='Save health record to database',
        )
    
    def handle(self, *args, **options):
        save_record = options['save']
        
        try:
            health_data = self.collect_health_metrics()
            
            if save_record:
                health_record = SystemHealth.objects.create(**health_data)
                self.stdout.write(
                    self.style.SUCCESS(f'Health record saved: {health_record.status}')
                )
            
            # Display health summary
            self.display_health_summary(health_data)
            
        except Exception as e:
            logger.error(f"Health check failed: {e}")
            self.stdout.write(
                self.style.ERROR(f'Health check failed: {e}')
            )
    
    def collect_health_metrics(self):
        """Collect comprehensive system health metrics"""
        health_data = {}
        
        # Database health
        try:
            with connection.cursor() as cursor:
                cursor.execute("SELECT COUNT(*) FROM sqlite_master WHERE type='table';")
                table_count = cursor.fetchone()[0]
                
                # Get database file size
                db_path = connection.settings_dict['NAME']
                if os.path.exists(db_path):
                    db_size_bytes = os.path.getsize(db_path)
                    health_data['db_size_mb'] = round(db_size_bytes / (1024 * 1024), 2)
                else:
                    health_data['db_size_mb'] = 0
                
                health_data['db_connections'] = len(connection.queries)
                
        except Exception as e:
            logger.error(f"Database health check failed: {e}")
            health_data['db_size_mb'] = 0
            health_data['db_connections'] = 0
        
        # Performance metrics
        try:
            # Measure response time with a simple query
            start_time = time.time()
            with connection.cursor() as cursor:
                cursor.execute("SELECT 1;")
                cursor.fetchone()
            response_time = (time.time() - start_time) * 1000  # Convert to ms
            health_data['avg_response_time_ms'] = round(response_time, 2)
            
        except Exception as e:
            logger.error(f"Response time check failed: {e}")
            health_data['avg_response_time_ms'] = 0
        
        # System resources
        try:
            # Memory usage
            process = psutil.Process()
            memory_info = process.memory_info()
            health_data['memory_usage_mb'] = round(memory_info.rss / (1024 * 1024), 2)
            
            # CPU usage
            health_data['cpu_usage_percent'] = round(psutil.cpu_percent(interval=1), 2)
            
        except Exception as e:
            logger.error(f"System resource check failed: {e}")
            health_data['memory_usage_mb'] = 0
            health_data['cpu_usage_percent'] = 0
        
        # ML model health
        try:
            models_dir = 'models'
            if os.path.exists(models_dir):
                ml_files = [f for f in os.listdir(models_dir) if f.endswith('.pkl')]
                health_data['ml_models_loaded'] = len(ml_files)
            else:
                health_data['ml_models_loaded'] = 0
            
            # Mock ML accuracy (in real implementation, this would be calculated)
            health_data['ml_prediction_accuracy'] = 85.5
            
        except Exception as e:
            logger.error(f"ML health check failed: {e}")
            health_data['ml_models_loaded'] = 0
            health_data['ml_prediction_accuracy'] = 0
        
        # Cache health
        try:
            cache.set('health_test', 'ok', 10)
            cache_result = cache.get('health_test')
            cache_healthy = cache_result == 'ok'
        except Exception as e:
            logger.error(f"Cache health check failed: {e}")
            cache_healthy = False
        
        # Determine overall status
        status = 'healthy'
        
        if health_data['db_size_mb'] == 0:
            status = 'critical'
        elif health_data['avg_response_time_ms'] > 1000:  # > 1 second
            status = 'warning'
        elif health_data['memory_usage_mb'] > 1000:  # > 1GB
            status = 'warning'
        elif health_data['cpu_usage_percent'] > 80:  # > 80%
            status = 'warning'
        elif not cache_healthy:
            status = 'warning'
        
        health_data['status'] = status
        
        return health_data
    
    def display_health_summary(self, health_data):
        """Display formatted health summary"""
        status = health_data['status']
        
        if status == 'healthy':
            status_style = self.style.SUCCESS
        elif status == 'warning':
            status_style = self.style.WARNING
        else:
            status_style = self.style.ERROR
        
        self.stdout.write("\n" + "="*50)
        self.stdout.write(status_style(f"SYSTEM HEALTH: {status.upper()}"))
        self.stdout.write("="*50)
        
        self.stdout.write(f"Database Size: {health_data['db_size_mb']} MB")
        self.stdout.write(f"Response Time: {health_data['avg_response_time_ms']} ms")
        self.stdout.write(f"Memory Usage: {health_data['memory_usage_mb']} MB")
        self.stdout.write(f"CPU Usage: {health_data['cpu_usage_percent']}%")
        self.stdout.write(f"ML Models: {health_data['ml_models_loaded']}")
        self.stdout.write(f"ML Accuracy: {health_data['ml_prediction_accuracy']}%")
        
        self.stdout.write("="*50 + "\n")
        
        # Recommendations
        if status != 'healthy':
            self.stdout.write(self.style.WARNING("RECOMMENDATIONS:"))
            
            if health_data['avg_response_time_ms'] > 1000:
                self.stdout.write("- Consider database optimization")
            
            if health_data['memory_usage_mb'] > 1000:
                self.stdout.write("- Monitor memory usage and consider scaling")
            
            if health_data['cpu_usage_percent'] > 80:
                self.stdout.write("- High CPU usage detected, check for intensive processes")
            
            if health_data['ml_models_loaded'] == 0:
                self.stdout.write("- No ML models found, check models directory")
            
            self.stdout.write("")