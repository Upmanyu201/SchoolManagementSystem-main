# core/optimizations.py - Database and query optimizations
from django.db.models import Prefetch, Q
from django.core.cache import cache
from django.db import connection
from functools import wraps

class QueryOptimizer:
    """Database query optimization utilities"""
    
    @staticmethod
    def get_students_optimized(class_id=None, with_fees=False):
        """Optimized student query with selective prefetching"""
        queryset = Student.objects.select_related('class_section')
        
        if class_id:
            queryset = queryset.filter(class_section_id=class_id)
        
        if with_fees:
            queryset = queryset.prefetch_related(
                Prefetch('fee_deposits', 
                        queryset=FeeDeposit.objects.select_related('fees_type'))
            )
        
        return queryset
    
    @staticmethod
    def get_attendance_summary_optimized(class_id, date_range):
        """Optimized attendance summary query"""
        from attendance.models import Attendance
        from django.db.models import Count, Case, When, IntegerField
        
        return Attendance.objects.filter(
            student__class_section_id=class_id,
            date__range=date_range
        ).values('student__id', 'student__first_name', 'student__last_name').annotate(
            total_days=Count('id'),
            present_days=Count(Case(
                When(status='Present', then=1),
                output_field=IntegerField()
            )),
            absent_days=Count(Case(
                When(status='Absent', then=1),
                output_field=IntegerField()
            ))
        )
    
    @staticmethod
    def get_fee_summary_optimized(student_ids):
        """Optimized fee summary for multiple students"""
        from student_fees.models import FeeDeposit
        from django.db.models import Sum
        
        return FeeDeposit.objects.filter(
            student_id__in=student_ids
        ).values('student_id').annotate(
            total_paid=Sum('paid_amount'),
            total_discount=Sum('discount')
        )

class CacheOptimizer:
    """Intelligent caching strategies"""
    
    @staticmethod
    def get_or_set_with_tags(key, compute_func, timeout=300, tags=None):
        """Cache with tagging for selective invalidation"""
        result = cache.get(key)
        
        if result is None:
            result = compute_func()
            cache.set(key, result, timeout)
            
            # Store tags for later invalidation
            if tags:
                for tag in tags:
                    tag_key = f"tag_{tag}"
                    tagged_keys = cache.get(tag_key, set())
                    tagged_keys.add(key)
                    cache.set(tag_key, tagged_keys, timeout)
        
        return result
    
    @staticmethod
    def invalidate_by_tag(tag):
        """Invalidate all cache keys with specific tag"""
        tag_key = f"tag_{tag}"
        tagged_keys = cache.get(tag_key, set())
        
        if tagged_keys:
            cache.delete_many(list(tagged_keys))
            cache.delete(tag_key)

def optimize_queries(func):
    """Decorator to optimize database queries"""
    @wraps(func)
    def wrapper(*args, **kwargs):
        # Enable query optimization
        with connection.cursor() as cursor:
            cursor.execute("PRAGMA optimize")
        
        return func(*args, **kwargs)
    return wrapper