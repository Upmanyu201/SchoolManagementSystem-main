# core/performance.py - Performance optimization utilities
from django.core.cache import cache
from django.db import connection
from functools import wraps
import time
import logging

logger = logging.getLogger(__name__)

class PerformanceOptimizer:
    @staticmethod
    def cache_result(timeout=300, key_prefix=''):
        """Decorator for caching function results"""
        def decorator(func):
            @wraps(func)
            def wrapper(*args, **kwargs):
                # Generate cache key
                cache_key = f"{key_prefix}_{func.__name__}_{hash(str(args) + str(kwargs))}"
                
                # Try to get from cache
                result = cache.get(cache_key)
                if result is not None:
                    return result
                
                # Execute function and cache result
                result = func(*args, **kwargs)
                cache.set(cache_key, result, timeout)
                return result
            return wrapper
        return decorator
    
    @staticmethod
    def monitor_queries(func):
        """Decorator to monitor database queries"""
        @wraps(func)
        def wrapper(*args, **kwargs):
            initial_queries = len(connection.queries)
            start_time = time.time()
            
            result = func(*args, **kwargs)
            
            end_time = time.time()
            query_count = len(connection.queries) - initial_queries
            
            if query_count > 10:  # Alert if too many queries
                logger.warning(f"{func.__name__} executed {query_count} queries in {end_time - start_time:.3f}s")
            
            return result
        return wrapper
    
    @staticmethod
    def batch_operations(items, batch_size=100):
        """Utility for batch processing"""
        for i in range(0, len(items), batch_size):
            yield items[i:i + batch_size]

# Quick decorators
cache_for_5min = PerformanceOptimizer.cache_result(300)
cache_for_1hour = PerformanceOptimizer.cache_result(3600)
monitor_db = PerformanceOptimizer.monitor_queries