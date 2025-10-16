# Real-time Dashboard Update Service
from django.core.cache import cache
from django.db.models.signals import post_save, post_delete
from django.dispatch import receiver
from django.utils import timezone
from datetime import timedelta
import json
import logging

logger = logging.getLogger(__name__)

class DashboardUpdateService:
    """Service for managing real-time dashboard updates"""
    
    CACHE_KEYS = {
        'dashboard_stats': 'dashboard:stats',
        'last_update': 'dashboard:last_update',
        'student_count': 'dashboard:student_count',
        'teacher_count': 'dashboard:teacher_count',
        'fee_stats': 'dashboard:fee_stats',
        'attendance_stats': 'dashboard:attendance_stats'
    }
    
    @classmethod
    def invalidate_cache(cls, cache_key=None):
        """Invalidate specific cache or all dashboard cache"""
        if cache_key:
            cache.delete(cls.CACHE_KEYS.get(cache_key, cache_key))
        else:
            # Clear all dashboard cache
            for key in cls.CACHE_KEYS.values():
                cache.delete(key)
        
        # Update last modification time
        cache.set(cls.CACHE_KEYS['last_update'], timezone.now().isoformat(), 3600)
        logger.info(f"Dashboard cache invalidated: {cache_key or 'all'}")
    
    @classmethod
    def get_cached_stats(cls, key, calculator_func, timeout=300):
        """Get cached statistics or calculate and cache"""
        cache_key = cls.CACHE_KEYS.get(key, key)
        stats = cache.get(cache_key)
        
        if stats is None:
            stats = calculator_func()
            cache.set(cache_key, stats, timeout)
            logger.debug(f"Calculated and cached stats for {key}")
        
        return stats
    
    @classmethod
    def update_student_stats(cls):
        """Update student-related statistics"""
        cls.invalidate_cache('student_count')
        cls.invalidate_cache('dashboard_stats')
    
    @classmethod
    def update_teacher_stats(cls):
        """Update teacher-related statistics"""
        cls.invalidate_cache('teacher_count')
        cls.invalidate_cache('dashboard_stats')
    
    @classmethod
    def update_fee_stats(cls):
        """Update fee-related statistics"""
        cls.invalidate_cache('fee_stats')
        cls.invalidate_cache('dashboard_stats')
    
    @classmethod
    def update_attendance_stats(cls):
        """Update attendance-related statistics"""
        cls.invalidate_cache('attendance_stats')
        cls.invalidate_cache('dashboard_stats')

# Signal handlers for automatic cache invalidation
@receiver(post_save, sender='students.Student')
@receiver(post_delete, sender='students.Student')
def handle_student_change(sender, **kwargs):
    """Handle student model changes"""
    DashboardUpdateService.update_student_stats()

@receiver(post_save, sender='teachers.Teacher')
@receiver(post_delete, sender='teachers.Teacher')
def handle_teacher_change(sender, **kwargs):
    """Handle teacher model changes"""
    DashboardUpdateService.update_teacher_stats()

@receiver(post_save, sender='student_fees.FeeDeposit')
@receiver(post_delete, sender='student_fees.FeeDeposit')
def handle_fee_change(sender, **kwargs):
    """Handle fee deposit changes"""
    DashboardUpdateService.update_fee_stats()

@receiver(post_save, sender='attendance.Attendance')
@receiver(post_delete, sender='attendance.Attendance')
def handle_attendance_change(sender, **kwargs):
    """Handle attendance changes"""
    DashboardUpdateService.update_attendance_stats()

# Enhanced Unified Dashboard Service with caching
class CachedUnifiedDashboardService:
    """Enhanced dashboard service with intelligent caching"""
    
    def __init__(self):
        self.update_service = DashboardUpdateService()
        self.current_date = timezone.now().date()
    
    def get_complete_dashboard_data(self):
        """Get complete dashboard data with caching"""
        return self.update_service.get_cached_stats(
            'dashboard_stats',
            self._calculate_dashboard_data,
            timeout=300  # 5 minutes
        )
    
    def _calculate_dashboard_data(self):
        """Calculate fresh dashboard data"""
        from .unified_data_service import UnifiedDashboardService
        
        service = UnifiedDashboardService()
        data = service.get_complete_dashboard_data()
        
        # Add cache metadata
        data['cache_info'] = {
            'generated_at': timezone.now().isoformat(),
            'expires_in': 300
        }
        
        return data
    
    def get_real_time_updates(self):
        """Get data for real-time updates"""
        last_update = cache.get(self.update_service.CACHE_KEYS['last_update'])
        
        return {
            'last_update': last_update,
            'has_updates': last_update is not None,
            'timestamp': timezone.now().isoformat()
        }