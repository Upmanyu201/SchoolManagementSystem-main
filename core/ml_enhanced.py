# core/ml_enhanced.py - Enhanced ML integration across all modules
from django.core.cache import cache
from decimal import Decimal
import logging
from .ml_logger import MLLogger
import time

logger = logging.getLogger(__name__)

class MLEnhancedService:
    """Enhanced ML service with fallback and caching"""
    
    @staticmethod
    def get_student_insights(student_id):
        """Get comprehensive ML insights for student"""
        start_time = time.time()
        cache_key = f"ml_student_insights_{student_id}"
        insights = cache.get(cache_key)
        
        if insights:
            MLLogger.log_cache_hit(cache_key, 'student_insights')
            return insights
        
        MLLogger.log_service_call('get_student_insights', {'student_id': student_id})
        
        try:
            from core.ml_integrations import ml_service
            MLLogger.log_model_load('ml_integrations', True)
            
            insights = {
                'performance_risk': ml_service.predict_student_performance(student_id),
                'dropout_risk': ml_service.predict_dropout_risk(student_id),
                'payment_risk': ml_service.predict_payment_delay(student_id),
                'attendance_pattern': ml_service.analyze_attendance_patterns(student_id),
                'recommendations': ml_service.get_student_recommendations(student_id)
            }
            
            duration = (time.time() - start_time) * 1000
            MLLogger.log_prediction('student_insights_ensemble', student_id, 'success', duration)
            
            cache.set(cache_key, insights, 1800)  # 30 minutes
            
        except ImportError as e:
            MLLogger.log_fallback('get_student_insights', f'ML models not available: {e}')
            insights = MLEnhancedService._get_fallback_insights()
        
        return insights
    
    @staticmethod
    def get_fee_optimization_insights():
        """Get fee structure optimization insights"""
        try:
            from core.ml_integrations import ml_service
            return ml_service.optimize_fee_structure()
        except ImportError:
            return {'status': 'ml_unavailable', 'message': 'Install ML dependencies for insights'}
    
    @staticmethod
    def get_attendance_predictions(class_id):
        """Get attendance predictions for class"""
        try:
            from core.ml_integrations import ml_service
            return ml_service.predict_class_attendance(class_id)
        except ImportError:
            return {'prediction': 'unavailable'}
    
    @staticmethod
    def get_promotion_recommendations(student_id):
        """Get promotion recommendations"""
        try:
            from core.ml_integrations import ml_service
            return ml_service.get_promotion_recommendations(student_id)
        except ImportError:
            return {'recommendation': 'manual_review_required'}
    
    @staticmethod
    def _get_fallback_insights():
        """Fallback insights when ML is unavailable"""
        return {
            'performance_risk': {'level': 'unknown', 'score': 0.5},
            'dropout_risk': {'level': 'unknown', 'score': 0.5},
            'payment_risk': {'level': 'unknown', 'score': 0.5},
            'attendance_pattern': {'trend': 'stable'},
            'recommendations': [],
            'status': 'ml_unavailable'
        }

class SmartCaching:
    """Intelligent caching system"""
    
    @staticmethod
    def get_or_compute(key, compute_func, timeout=300, force_refresh=False):
        """Get from cache or compute with intelligent refresh"""
        if not force_refresh:
            cached_value = cache.get(key)
            if cached_value is not None:
                return cached_value
        
        # Compute new value
        try:
            value = compute_func()
            cache.set(key, value, timeout)
            return value
        except Exception as e:
            logger.error(f"Cache computation failed for {key}: {e}")
            return cache.get(key)  # Return stale data if available
    
    @staticmethod
    def invalidate_pattern(pattern):
        """Invalidate cache keys matching pattern"""
        try:
            cache.delete_pattern(pattern)
        except AttributeError:
            # Fallback for cache backends that don't support delete_pattern
            pass