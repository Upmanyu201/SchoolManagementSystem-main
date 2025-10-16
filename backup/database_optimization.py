"""
Database optimization for backup operations.
Implements query optimization, connection pooling, and efficient data retrieval.
"""

from django.db import models, connection
from django.db.models import Prefetch, Q
from django.core.cache import cache
from django.apps import apps
from typing import Dict, List, Any, Optional
import time


class QueryOptimizer:
    """Optimize database queries for backup operations."""
    
    def __init__(self):
        self.query_cache = {}
        self.optimization_rules = {
            'select_related_fields': {
                'students.Student': ['student_class', 'student_section'],
                'fees.FeeDeposit': ['student', 'fee_type'],
                'attendance.Attendance': ['student', 'class_session'],
            },
            'prefetch_related_fields': {
                'students.Student': ['fee_deposits', 'attendance_records'],
                'academics.Class': ['students', 'subjects'],
            }
        }
    
    def optimize_queryset(self, model: models.Model) -> models.QuerySet:
        """Optimize queryset for a specific model."""
        model_name = f"{model._meta.app_label}.{model._meta.model_name}"
        
        # Start with base queryset
        queryset = model.objects.all()
        
        # Apply select_related optimization
        select_related = self.optimization_rules['select_related_fields'].get(model_name, [])
        if select_related:
            queryset = queryset.select_related(*select_related)
        
        # Apply prefetch_related optimization
        prefetch_related = self.optimization_rules['prefetch_related_fields'].get(model_name, [])
        if prefetch_related:
            queryset = queryset.prefetch_related(*prefetch_related)
        
        # Apply ordering for consistent results
        if hasattr(model, '_meta') and model._meta.ordering:
            queryset = queryset.order_by(*model._meta.ordering)
        else:
            queryset = queryset.order_by('pk')
        
        return queryset
    
    def get_optimized_models_data(self, model_names: List[str] = None) -> Dict[str, models.QuerySet]:
        """Get optimized querysets for multiple models."""
        models_data = {}
        
        if model_names is None:
            # Get all models
            target_models = apps.get_models()
        else:
            # Get specific models
            target_models = []
            for model_name in model_names:
                try:
                    app_label, model_name_clean = model_name.split('.')
                    model = apps.get_model(app_label, model_name_clean)
                    target_models.append(model)
                except (ValueError, LookupError):
                    continue
        
        for model in target_models:
            if hasattr(model, '_meta') and not model._meta.proxy:
                model_key = f"{model._meta.app_label}.{model._meta.model_name}"
                models_data[model_key] = self.optimize_queryset(model)
        
        return models_data
    
    def analyze_query_performance(self, queryset: models.QuerySet) -> Dict[str, Any]:
        """Analyze query performance."""
        start_time = time.time()
        initial_queries = len(connection.queries)
        
        # Execute query
        count = queryset.count()
        
        end_time = time.time()
        final_queries = len(connection.queries)
        
        return {
            'execution_time': round(end_time - start_time, 4),
            'query_count': final_queries - initial_queries,
            'record_count': count,
            'queries_per_record': round((final_queries - initial_queries) / max(count, 1), 4)
        }


class BatchProcessor:
    """Process database operations in optimized batches."""
    
    def __init__(self, batch_size: int = 1000):
        self.batch_size = batch_size
    
    def process_queryset_in_batches(self, queryset: models.QuerySet, 
                                  processor_func: callable) -> List[Any]:
        """Process queryset in batches to avoid memory issues."""
        results = []
        
        # Use iterator to avoid loading all objects into memory
        batch = []
        for obj in queryset.iterator(chunk_size=self.batch_size):
            batch.append(obj)
            
            if len(batch) >= self.batch_size:
                batch_result = processor_func(batch)
                results.extend(batch_result)
                batch = []
        
        # Process remaining objects
        if batch:
            batch_result = processor_func(batch)
            results.extend(batch_result)
        
        return results
    
    def serialize_batch(self, batch: List[models.Model]) -> List[Dict[str, Any]]:
        """Serialize a batch of model instances efficiently."""
        serialized_batch = []
        
        for obj in batch:
            serialized_obj = {
                'pk': obj.pk,
                'model': f"{obj._meta.app_label}.{obj._meta.model_name}",
                'fields': self._extract_fields(obj)
            }
            serialized_batch.append(serialized_obj)
        
        return serialized_batch
    
    def _extract_fields(self, obj: models.Model) -> Dict[str, Any]:
        """Extract model fields efficiently."""
        fields = {}
        
        for field in obj._meta.fields:
            field_name = field.name
            value = getattr(obj, field_name)
            
            # Handle different field types
            if value is None:
                fields[field_name] = None
            elif isinstance(field, models.DateTimeField) and hasattr(value, 'isoformat'):
                fields[field_name] = value.isoformat()
            elif isinstance(field, models.DateField) and hasattr(value, 'isoformat'):
                fields[field_name] = value.isoformat()
            elif isinstance(field, models.ForeignKey):
                fields[field_name] = value.pk if value else None
            elif isinstance(field, models.DecimalField):
                fields[field_name] = str(value) if value is not None else None
            else:
                fields[field_name] = value
        
        return fields


class ConnectionPoolManager:
    """Manage database connections efficiently."""
    
    def __init__(self):
        self.connection_stats = {
            'active_connections': 0,
            'total_queries': 0,
            'avg_query_time': 0
        }
    
    def get_connection_info(self) -> Dict[str, Any]:
        """Get current connection information."""
        return {
            'queries_count': len(connection.queries),
            'connection_stats': self.connection_stats,
            'vendor': connection.vendor,
            'settings': {
                'conn_max_age': getattr(connection.settings_dict, 'CONN_MAX_AGE', 0),
                'autocommit': connection.get_autocommit(),
            }
        }
    
    def optimize_connection_settings(self) -> Dict[str, Any]:
        """Optimize database connection settings for backup operations."""
        optimizations = []
        
        # Check connection pooling
        if connection.settings_dict.get('CONN_MAX_AGE', 0) == 0:
            optimizations.append({
                'setting': 'CONN_MAX_AGE',
                'recommendation': 'Set to 600 for connection reuse',
                'impact': 'Reduces connection overhead'
            })
        
        # Check for read-only operations
        if connection.vendor == 'postgresql':
            optimizations.append({
                'setting': 'default_transaction_isolation',
                'recommendation': 'Use READ COMMITTED for backups',
                'impact': 'Improves read performance'
            })
        
        return {
            'current_settings': self.get_connection_info(),
            'optimizations': optimizations
        }


class CacheOptimizer:
    """Optimize caching for backup operations."""
    
    def __init__(self, cache_timeout: int = 300):
        self.cache_timeout = cache_timeout
        self.cache_prefix = 'backup_opt_'
    
    def cache_model_metadata(self, model: models.Model) -> str:
        """Cache model metadata for faster access."""
        cache_key = f"{self.cache_prefix}meta_{model._meta.label}"
        
        metadata = cache.get(cache_key)
        if metadata is None:
            metadata = {
                'app_label': model._meta.app_label,
                'model_name': model._meta.model_name,
                'fields': [f.name for f in model._meta.fields],
                'field_types': {f.name: f.__class__.__name__ for f in model._meta.fields},
                'relations': [f.name for f in model._meta.fields if f.is_relation]
            }
            cache.set(cache_key, metadata, self.cache_timeout)
        
        return cache_key
    
    def get_cached_model_count(self, model: models.Model) -> Optional[int]:
        """Get cached model count."""
        cache_key = f"{self.cache_prefix}count_{model._meta.label}"
        return cache.get(cache_key)
    
    def cache_model_count(self, model: models.Model, count: int):
        """Cache model count."""
        cache_key = f"{self.cache_prefix}count_{model._meta.label}"
        cache.set(cache_key, count, self.cache_timeout)
    
    def clear_backup_cache(self):
        """Clear all backup-related cache."""
        # Note: This is a simplified version. In production, use cache versioning
        cache.delete_many([
            key for key in cache._cache.keys() 
            if key.startswith(self.cache_prefix)
        ])


class DatabaseOptimizer:
    """Main database optimization coordinator."""
    
    def __init__(self):
        self.query_optimizer = QueryOptimizer()
        self.batch_processor = BatchProcessor()
        self.connection_manager = ConnectionPoolManager()
        self.cache_optimizer = CacheOptimizer()
    
    def prepare_optimized_backup_data(self, model_names: List[str] = None) -> Dict[str, Any]:
        """Prepare optimized data for backup operations."""
        # Get optimized querysets
        models_data = self.query_optimizer.get_optimized_models_data(model_names)
        
        # Analyze performance
        performance_analysis = {}
        for model_name, queryset in models_data.items():
            performance_analysis[model_name] = self.query_optimizer.analyze_query_performance(queryset)
        
        # Cache model metadata
        for model_name, queryset in models_data.items():
            model = queryset.model
            self.cache_optimizer.cache_model_metadata(model)
            
            # Cache count for progress tracking
            count = queryset.count()
            self.cache_optimizer.cache_model_count(model, count)
        
        return {
            'models_data': models_data,
            'performance_analysis': performance_analysis,
            'connection_info': self.connection_manager.get_connection_info(),
            'optimization_recommendations': self.connection_manager.optimize_connection_settings()
        }
    
    def get_optimization_report(self) -> Dict[str, Any]:
        """Generate comprehensive optimization report."""
        return {
            'timestamp': time.time(),
            'database_vendor': connection.vendor,
            'connection_info': self.connection_manager.get_connection_info(),
            'cache_status': {
                'backend': cache.__class__.__name__,
                'timeout': self.cache_optimizer.cache_timeout
            },
            'optimization_settings': {
                'batch_size': self.batch_processor.batch_size,
                'query_optimizations': len(self.query_optimizer.optimization_rules['select_related_fields'])
            }
        }