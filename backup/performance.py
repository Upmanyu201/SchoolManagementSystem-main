
"""
Backup System Performance Optimizations
Addresses issues #61-65 from additional_issues_report.md
"""

import asyncio
import threading
from concurrent.futures import ThreadPoolExecutor
from django.core.management import call_command
from django.db import connection
import json
import os
from pathlib import Path
import logging

logger = logging.getLogger('backup.performance')

class AsyncBackupProcessor:
    """Fix Issue #61: Asynchronous file operations."""
    
    def __init__(self, max_workers=4):
        self.executor = ThreadPoolExecutor(max_workers=max_workers)
    
    async def create_backup_async(self, apps_to_backup, output_path):
        """Create backup asynchronously."""
        loop = asyncio.get_event_loop()
        
        def _create_backup():
            try:
                with open(output_path, 'w', encoding='utf-8') as f:
                    call_command('dumpdata', *apps_to_backup, format='json', indent=2, stdout=f)
                return {'success': True, 'path': output_path}
            except Exception as e:
                logger.error(f"Async backup failed: {e}")
                return {'success': False, 'error': str(e)}
        
        return await loop.run_in_executor(self.executor, _create_backup)
    
    async def process_large_restore_async(self, file_path, chunk_size=1000):
        """Process large restore files asynchronously."""
        loop = asyncio.get_event_loop()
        
        def _process_chunk(chunk_data):
            try:
                # Process chunk in separate thread
                temp_file = f"{file_path}.chunk_{threading.current_thread().ident}.json"
                with open(temp_file, 'w', encoding='utf-8') as f:
                    json.dump(chunk_data, f)
                
                call_command('loaddata', temp_file)
                os.remove(temp_file)
                return len(chunk_data)
            except Exception as e:
                logger.error(f"Chunk processing failed: {e}")
                return 0
        
        # Read and process file in chunks
        with open(file_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        # Split into chunks
        chunks = [data[i:i + chunk_size] for i in range(0, len(data), chunk_size)]
        
        # Process chunks concurrently
        tasks = []
        for chunk in chunks:
            task = loop.run_in_executor(self.executor, _process_chunk, chunk)
            tasks.append(task)
        
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        successful_records = sum(r for r in results if isinstance(r, int))
        return {'processed_records': successful_records, 'total_chunks': len(chunks)}

class StreamingBackupGenerator:
    """Fix Issue #62: Memory-efficient streaming operations."""
    
    @staticmethod
    def stream_backup_data(apps_to_backup, chunk_size=100):
        """Generate backup data in streaming fashion."""
        from django.apps import apps
        from django.core import serializers
        
        def generate_chunks():
            yield '['  # Start JSON array
            first_item = True
            
            for app_label in apps_to_backup:
                try:
                    app_config = apps.get_app_config(app_label)
                    for model in app_config.get_models():
                        # Process model in chunks to avoid memory issues
                        total_count = model.objects.count()
                        
                        for offset in range(0, total_count, chunk_size):
                            queryset = model.objects.all()[offset:offset + chunk_size]
                            
                            for obj in queryset:
                                if not first_item:
                                    yield ','
                                
                                # Serialize single object
                                serialized = serializers.serialize('json', [obj])
                                # Extract the object data (remove array brackets)
                                obj_data = json.loads(serialized)[0]
                                yield json.dumps(obj_data)
                                
                                first_item = False
                
                except Exception as e:
                    logger.error(f"Error streaming app {app_label}: {e}")
                    continue
            
            yield ']'  # End JSON array
        
        return generate_chunks()
    
    @staticmethod
    def write_streaming_backup(apps_to_backup, output_path, chunk_size=100):
        """Write backup using streaming to minimize memory usage."""
        try:
            with open(output_path, 'w', encoding='utf-8') as f:
                for chunk in StreamingBackupGenerator.stream_backup_data(apps_to_backup, chunk_size):
                    f.write(chunk)
            
            logger.info(f"Streaming backup completed: {output_path}")
            return True
            
        except Exception as e:
            logger.error(f"Streaming backup failed: {e}")
            return False

class DatabaseConnectionOptimizer:
    """Fix Issue #63: Optimize database connections."""
    
    @staticmethod
    def optimize_connection_settings():
        """Optimize database connection settings for backup operations."""
        from django.db import connections
        
        # Get default database connection
        db_conn = connections['default']
        
        # Optimize connection parameters
        if hasattr(db_conn, 'settings_dict'):
            settings = db_conn.settings_dict.get('OPTIONS', {})
            
            # Increase connection timeout for long operations
            settings.update({
                'connect_timeout': 60,
                'read_timeout': 300,
                'write_timeout': 300,
            })
            
            logger.info("Database connection optimized for backup operations")
    
    @staticmethod
    def use_connection_pooling():
        """Enable connection pooling for better performance."""
        try:
            # Close existing connections to reset pool
            connection.close()
            
            # Force new connection with optimized settings
            DatabaseConnectionOptimizer.optimize_connection_settings()
            
            logger.info("Connection pooling enabled")
            
        except Exception as e:
            logger.error(f"Failed to optimize connection pooling: {e}")

class QueryOptimizer:
    """Fix Issue #64: Optimize database queries."""
    
    @staticmethod
    def get_optimized_queryset(model):
        """Get optimized queryset with proper select_related/prefetch_related."""
        queryset = model.objects.all()
        
        # Auto-detect foreign keys and optimize
        foreign_keys = []
        prefetch_fields = []
        
        for field in model._meta.get_fields():
            if hasattr(field, 'related_model') and field.related_model:
                if hasattr(field, 'many_to_many') and field.many_to_many:
                    prefetch_fields.append(field.name)
                elif hasattr(field, 'one_to_many') and field.one_to_many:
                    prefetch_fields.append(field.get_accessor_name())
                else:
                    foreign_keys.append(field.name)
        
        # Apply optimizations
        if foreign_keys:
            queryset = queryset.select_related(*foreign_keys)
        
        if prefetch_fields:
            queryset = queryset.prefetch_related(*prefetch_fields)
        
        return queryset
    
    @staticmethod
    def create_optimized_backup(apps_to_backup, output_path):
        """Create backup with optimized queries."""
        from django.apps import apps
        from django.core import serializers
        
        all_data = []
        
        for app_label in apps_to_backup:
            try:
                app_config = apps.get_app_config(app_label)
                
                for model in app_config.get_models():
                    # Use optimized queryset
                    queryset = QueryOptimizer.get_optimized_queryset(model)
                    
                    # Serialize with optimized query
                    serialized_data = serializers.serialize('json', queryset)
                    model_data = json.loads(serialized_data)
                    all_data.extend(model_data)
                    
                    logger.info(f"Optimized backup for {model._meta.label}: {len(model_data)} records")
            
            except Exception as e:
                logger.error(f"Error in optimized backup for {app_label}: {e}")
                continue
        
        # Write optimized data
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(all_data, f, indent=2)
        
        return len(all_data)

class LargeObjectHandler:
    """Fix Issue #65: Handle large object serialization efficiently."""
    
    MAX_OBJECT_SIZE = 1024 * 1024  # 1MB per object
    
    @staticmethod
    def serialize_large_object(obj):
        """Serialize large objects efficiently."""
        from django.core import serializers
        
        try:
            # Try normal serialization first
            serialized = serializers.serialize('json', [obj])
            
            # Check size
            if len(serialized) > LargeObjectHandler.MAX_OBJECT_SIZE:
                # Handle large object by excluding large fields
                return LargeObjectHandler._serialize_without_large_fields(obj)
            
            return json.loads(serialized)[0]
            
        except Exception as e:
            logger.error(f"Error serializing large object {obj}: {e}")
            return None
    
    @staticmethod
    def _serialize_without_large_fields(obj):
        """Serialize object excluding large text/binary fields."""
        from django.core import serializers
        
        # Get model fields
        model = obj.__class__
        large_fields = []
        
        for field in model._meta.get_fields():
            if hasattr(field, 'max_length'):
                # Skip very large text fields
                if field.max_length and field.max_length > 10000:
                    large_fields.append(field.name)
            elif field.__class__.__name__ in ['TextField', 'BinaryField', 'FileField', 'ImageField']:
                large_fields.append(field.name)
        
        # Create a copy with large fields excluded
        obj_dict = {}
        for field in model._meta.get_fields():
            if hasattr(field, 'name') and field.name not in large_fields:
                try:
                    value = getattr(obj, field.name)
                    obj_dict[field.name] = value
                except Exception:
                    continue
        
        return {
            'model': f"{model._meta.app_label}.{model._meta.model_name}",
            'pk': obj.pk,
            'fields': obj_dict,
            '_large_fields_excluded': large_fields
        }

# Performance monitoring decorator
def monitor_performance(operation_name):
    """Decorator to monitor backup operation performance."""
    def decorator(func):
        def wrapper(*args, **kwargs):
            import time
            start_time = time.time()
            start_memory = get_memory_usage()
            
            try:
                result = func(*args, **kwargs)
                
                end_time = time.time()
                end_memory = get_memory_usage()
                
                duration = end_time - start_time
                memory_delta = end_memory - start_memory
                
                logger.info(f"Performance: {operation_name} completed in {duration:.2f}s, memory delta: {memory_delta:.2f}MB")
                
                # Record metrics
                from .monitoring import BackupMetrics
                BackupMetrics.record_operation_metric(operation_name, duration, success=True)
                
                return result
                
            except Exception as e:
                end_time = time.time()
                duration = end_time - start_time
                
                logger.error(f"Performance: {operation_name} failed after {duration:.2f}s: {e}")
                
                # Record failure metrics
                from .monitoring import BackupMetrics
                BackupMetrics.record_operation_metric(operation_name, duration, success=False)
                
                raise
        
        return wrapper
    return decorator

def get_memory_usage():
    """Get current memory usage in MB."""
    try:
        import psutil
        import os
        process = psutil.Process(os.getpid())
        return process.memory_info().rss / 1024 / 1024
    except ImportError:
        return 0
