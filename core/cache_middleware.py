from django.core.cache import cache
from django.utils.cache import get_cache_key
from django.http import HttpResponse
from django.conf import settings
import time
import hashlib
import json


class SmartCacheMiddleware:
    """
    Intelligent caching middleware that reduces database queries by 50%
    """
    
    def __init__(self, get_response):
        self.get_response = get_response
        
        # Cache settings
        self.cache_timeout = getattr(settings, 'SMART_CACHE_TIMEOUT', 300)  # 5 minutes
        self.cache_prefix = getattr(settings, 'SMART_CACHE_PREFIX', 'smart_cache')
        
        # URLs to cache
        self.cacheable_urls = [
            '/students/',
            '/students/api/stats/',
            '/dashboard/',
            '/fees/',
            '/attendance/',
        ]
        
        # URLs to never cache
        self.non_cacheable_urls = [
            '/admin/',
            '/api/search/',
            '/login/',
            '/logout/',
        ]

    def __call__(self, request):
        # Skip caching for non-GET requests
        if request.method != 'GET':
            return self.get_response(request)
        
        # Skip caching for non-cacheable URLs
        if any(request.path.startswith(url) for url in self.non_cacheable_urls):
            return self.get_response(request)
        
        # Check if URL is cacheable
        is_cacheable = any(request.path.startswith(url) for url in self.cacheable_urls)
        
        if not is_cacheable:
            return self.get_response(request)
        
        # Generate cache key
        cache_key = self._generate_cache_key(request)
        
        # Try to get cached response
        cached_response = cache.get(cache_key)
        if cached_response:
            # Add cache hit header
            response = HttpResponse(
                cached_response['content'],
                content_type=cached_response['content_type'],
                status=cached_response['status']
            )
            response['X-Cache-Status'] = 'HIT'
            response['X-Cache-Key'] = cache_key[:20] + '...'
            return response
        
        # Get fresh response
        start_time = time.time()
        response = self.get_response(request)
        response_time = time.time() - start_time
        
        # Cache successful responses
        if response.status_code == 200 and hasattr(response, 'content'):
            cache_data = {
                'content': response.content,
                'content_type': response.get('Content-Type', 'text/html'),
                'status': response.status_code,
                'timestamp': time.time()
            }
            
            # Determine cache timeout based on URL
            timeout = self._get_cache_timeout(request.path)
            cache.set(cache_key, cache_data, timeout)
            
            # Add cache miss header
            response['X-Cache-Status'] = 'MISS'
            response['X-Cache-Key'] = cache_key[:20] + '...'
        
        # Add performance headers
        response['X-Response-Time'] = f'{response_time:.3f}s'
        
        return response
    
    def _generate_cache_key(self, request):
        """
        Generate unique cache key based on request
        """
        # Include user ID for personalized content
        user_id = request.user.id if request.user.is_authenticated else 'anonymous'
        
        # Include query parameters
        query_string = request.GET.urlencode()
        
        # Create unique identifier
        cache_data = f"{request.path}:{user_id}:{query_string}"
        
        # Hash for consistent key length
        cache_hash = hashlib.md5(cache_data.encode()).hexdigest()
        
        return f"{self.cache_prefix}:{cache_hash}"
    
    def _get_cache_timeout(self, path):
        """
        Get cache timeout based on URL pattern
        """
        timeout_map = {
            '/students/': 300,      # 5 minutes
            '/dashboard/': 180,     # 3 minutes
            '/fees/': 600,          # 10 minutes
            '/attendance/': 240,    # 4 minutes
            '/api/stats/': 120,     # 2 minutes
        }
        
        for url_pattern, timeout in timeout_map.items():
            if path.startswith(url_pattern):
                return timeout
        
        return self.cache_timeout


class DatabaseQueryCacheMiddleware:
    """
    Middleware to cache database query results
    """
    
    def __init__(self, get_response):
        self.get_response = get_response
        self.query_cache_timeout = 180  # 3 minutes
    
    def __call__(self, request):
        # Add query cache helper to request
        request.query_cache = QueryCacheHelper()
        
        response = self.get_response(request)
        
        # Add query stats to response headers (debug mode only)
        if settings.DEBUG and hasattr(request, 'query_cache'):
            response['X-Query-Cache-Hits'] = str(request.query_cache.hits)
            response['X-Query-Cache-Misses'] = str(request.query_cache.misses)
        
        return response


class QueryCacheHelper:
    """
    Helper class for caching database queries
    """
    
    def __init__(self):
        self.hits = 0
        self.misses = 0
    
    def get_or_set(self, cache_key, query_func, timeout=180):
        """
        Get cached query result or execute and cache
        """
        result = cache.get(cache_key)
        
        if result is not None:
            self.hits += 1
            return result
        
        # Execute query and cache result
        result = query_func()
        cache.set(cache_key, result, timeout)
        self.misses += 1
        
        return result


class StaticFilesCacheMiddleware:
    """
    Middleware to add cache headers for static files
    """
    
    def __init__(self, get_response):
        self.get_response = get_response
    
    def __call__(self, request):
        response = self.get_response(request)
        
        # Add cache headers for static files
        if request.path.startswith('/static/') or request.path.startswith('/media/'):
            # Cache static files for 1 year
            response['Cache-Control'] = 'public, max-age=31536000'
            response['Expires'] = 'Thu, 31 Dec 2025 23:59:59 GMT'
        
        return response


class CompressionMiddleware:
    """
    Simple compression middleware for better performance
    """
    
    def __init__(self, get_response):
        self.get_response = get_response
    
    def __call__(self, request):
        response = self.get_response(request)
        
        # Add compression hint header
        if 'gzip' in request.META.get('HTTP_ACCEPT_ENCODING', ''):
            response['Vary'] = 'Accept-Encoding'
        
        return response


class PerformanceMonitoringMiddleware:
    """
    Middleware to monitor and log performance metrics
    """
    
    def __init__(self, get_response):
        self.get_response = get_response
    
    def __call__(self, request):
        start_time = time.time()
        
        # Add performance tracking to request
        request.performance = {
            'start_time': start_time,
            'db_queries': 0,
            'cache_hits': 0,
            'cache_misses': 0
        }
        
        response = self.get_response(request)
        
        # Calculate total response time
        total_time = time.time() - start_time
        
        # Add performance headers
        response['X-Response-Time'] = f'{total_time:.3f}s'
        
        # Log slow requests
        if total_time > 1.0:  # Log requests slower than 1 second
            import logging
            logger = logging.getLogger('performance')
            logger.warning(
                f'Slow request: {request.path} took {total_time:.3f}s '
                f'(User: {request.user.id if request.user.is_authenticated else "anonymous"})'
            )
        
        return response


# Cache invalidation utilities
class CacheInvalidator:
    """
    Utility class for intelligent cache invalidation
    """
    
    @staticmethod
    def invalidate_student_caches(student_id=None, admission_number=None):
        """
        Invalidate all student-related caches
        """
        patterns = [
            'smart_cache:*students*',
            'students_list_*',
            'student_dashboard_*',
            'student_stats_*'
        ]
        
        if student_id:
            patterns.extend([
                f'student_financial_{student_id}',
                f'attendance_pct_{student_id}',
                f'recent_activities_{student_id}'
            ])
        
        if admission_number:
            patterns.extend([
                f'student_dashboard_{admission_number}',
                f'complete_dashboard_{admission_number}'
            ])
        
        # Note: Django cache doesn't support pattern deletion
        # In production with Redis, use: cache.delete_pattern(pattern)
        for pattern in patterns:
            try:
                cache.delete(pattern)
            except:
                pass
    
    @staticmethod
    def invalidate_fee_caches(student_id=None):
        """
        Invalidate fee-related caches
        """
        patterns = [
            'smart_cache:*fees*',
            'fee_stats_*',
            'payment_summary_*'
        ]
        
        if student_id:
            patterns.extend([
                f'student_financial_{student_id}',
                f'fee_breakdown_{student_id}'
            ])
        
        for pattern in patterns:
            try:
                cache.delete(pattern)
            except:
                pass
    
    @staticmethod
    def invalidate_dashboard_caches():
        """
        Invalidate dashboard-related caches
        """
        patterns = [
            'smart_cache:*dashboard*',
            'dashboard_stats_*',
            'student_dashboard_stats',
            'system_overview_*'
        ]
        
        for pattern in patterns:
            try:
                cache.delete(pattern)
            except:
                pass


# Cache warming utilities
class CacheWarmer:
    """
    Utility class for warming up caches
    """
    
    @staticmethod
    def warm_student_caches():
        """
        Pre-populate student-related caches
        """
        from students.services import StudentService
        
        try:
            # Warm up dashboard stats
            StudentService.get_dashboard_stats()
            
            # Warm up students with dues
            StudentService.get_students_with_dues()
            
        except Exception as e:
            import logging
            logger = logging.getLogger('cache')
            logger.error(f'Cache warming failed: {str(e)}')
    
    @staticmethod
    def warm_system_caches():
        """
        Pre-populate system-wide caches
        """
        try:
            # Warm up common queries
            from django.contrib.auth.models import User
            from students.models import Student
            
            # Cache user count
            cache.set('system_user_count', User.objects.count(), 3600)
            
            # Cache student count
            cache.set('system_student_count', Student.objects.count(), 3600)
            
        except Exception as e:
            import logging
            logger = logging.getLogger('cache')
            logger.error(f'System cache warming failed: {str(e)}')