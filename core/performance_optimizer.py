# Performance Optimizer - Quick Fixes
from django.db import connection
from django.core.cache import cache
import logging

logger = logging.getLogger(__name__)

class PerformanceOptimizer:
    """Quick performance optimizations"""
    
    @staticmethod
    def optimize_database():
        """Apply SQLite optimizations"""
        with connection.cursor() as cursor:
            # SQLite performance settings
            cursor.execute("PRAGMA journal_mode = WAL;")
            cursor.execute("PRAGMA synchronous = NORMAL;")
            cursor.execute("PRAGMA cache_size = 10000;")
            cursor.execute("PRAGMA temp_store = MEMORY;")
            cursor.execute("PRAGMA mmap_size = 268435456;")  # 256MB
            logger.info("Applied SQLite performance optimizations")
    
    @staticmethod
    def clear_old_cache():
        """Clear old cache entries"""
        try:
            cache.clear()
            logger.info("Cache cleared successfully")
        except Exception as e:
            logger.error(f"Cache clear failed: {e}")
    
    @staticmethod
    def get_db_stats():
        """Get database performance stats"""
        with connection.cursor() as cursor:
            cursor.execute("SELECT COUNT(*) FROM sqlite_master WHERE type='table';")
            table_count = cursor.fetchone()[0]
            
            cursor.execute("PRAGMA page_count;")
            page_count = cursor.fetchone()[0]
            
            cursor.execute("PRAGMA page_size;")
            page_size = cursor.fetchone()[0]
            
            db_size_mb = (page_count * page_size) / (1024 * 1024)
            
            return {
                'tables': table_count,
                'size_mb': round(db_size_mb, 2),
                'pages': page_count
            }

# Apply optimizations on import
optimizer = PerformanceOptimizer()
try:
    optimizer.optimize_database()
except Exception as e:
    logger.warning(f"Database optimization failed: {e}")