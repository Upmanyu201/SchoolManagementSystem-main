# ML Integration for Export System - TDD Implementation
import logging
import time
from typing import Dict, List, Any, Optional
from django.core.cache import cache
from django.conf import settings
import asyncio

logger = logging.getLogger(__name__)

# Import ML service with graceful fallback
try:
    from .ml_service import ml_service
    ML_AVAILABLE = True
except ImportError:
    ml_service = None
    ML_AVAILABLE = False
    logger.warning("ML service not available. Install scikit-learn for ML features.")

class MLExportEnhancer:
    """ML-powered export data enhancement"""
    
    def __init__(self):
        self.cache_timeout = 300  # 5 minutes
        self.max_records_for_ml = 5000  # Performance limit
    
    def is_ml_available(self) -> bool:
        """Check if ML service is available"""
        return ML_AVAILABLE and self.ml_service is not None
    
    async def enhance_student_data(self, data: List[Dict]) -> List[Dict]:
        """Enhance student data with ML predictions"""
        if not self.is_ml_available() or len(data) > self.max_records_for_ml:
            return data
        
        enhanced_data = []
        
        for item in data:
            try:
                enhanced_item = item.copy()
                
                # Add performance prediction
                if 'id' in item or 'student_id' in item:
                    student_id = item.get('id') or item.get('student_id')
                    
                    # Check cache first
                    cache_key = f"ml_student_performance_{student_id}"
                    cached_prediction = cache.get(cache_key)
                    
                    if cached_prediction:
                        prediction = cached_prediction
                    else:
                        prediction = ml_service.predict_student_performance(student_id)
                        cache.set(cache_key, prediction, self.cache_timeout)
                    
                    enhanced_item['ML_Risk_Level'] = prediction.get('risk_level', 'unknown')
                    enhanced_item['ML_Risk_Score'] = prediction.get('risk_score', 0.5)
                    enhanced_item['ML_Recommendations'] = len(prediction.get('recommendations', []))
                
                enhanced_data.append(enhanced_item)
                
            except Exception as e:
                logger.warning(f"ML enhancement failed for item {item.get('id', 'unknown')}: {e}")
                enhanced_data.append(item)  # Return original item on error
        
        return enhanced_data
    
    async def enhance_fee_data(self, data: List[Dict]) -> List[Dict]:
        """Enhance fee data with payment predictions"""
        if not self.is_ml_available() or len(data) > self.max_records_for_ml:
            return data
        
        enhanced_data = []
        
        for item in data:
            try:
                enhanced_item = item.copy()
                
                if 'student_id' in item:
                    student_id = item['student_id']
                    
                    # Predict payment delay
                    cache_key = f"ml_payment_prediction_{student_id}"
                    cached_prediction = cache.get(cache_key)
                    
                    if cached_prediction:
                        prediction = cached_prediction
                    else:
                        prediction = ml_service.predict_payment_delay(student_id)
                        cache.set(cache_key, prediction, self.cache_timeout)
                    
                    enhanced_item['ML_Payment_Risk'] = prediction.get('delay_probability', 0.5)
                    enhanced_item['ML_Expected_Delay'] = prediction.get('expected_delay_days', 0)
                
                enhanced_data.append(enhanced_item)
                
            except Exception as e:
                logger.warning(f"ML fee enhancement failed: {e}")
                enhanced_data.append(item)
        
        return enhanced_data
    
    async def enhance_attendance_data(self, data: List[Dict]) -> List[Dict]:
        """Enhance attendance data with pattern analysis"""
        if not self.is_ml_available() or len(data) > self.max_records_for_ml:
            return data
        
        enhanced_data = []
        
        for item in data:
            try:
                enhanced_item = item.copy()
                
                if 'student_id' in item:
                    student_id = item['student_id']
                    
                    # Analyze attendance patterns
                    cache_key = f"ml_attendance_pattern_{student_id}"
                    cached_analysis = cache.get(cache_key)
                    
                    if cached_analysis:
                        analysis = cached_analysis
                    else:
                        analysis = ml_service.analyze_attendance_patterns(student_id)
                        cache.set(cache_key, analysis, self.cache_timeout)
                    
                    enhanced_item['ML_Attendance_Pattern'] = analysis.get('pattern_type', 'unknown')
                    enhanced_item['ML_Attendance_Trend'] = analysis.get('trend', 'stable')
                    enhanced_item['ML_Risk_Level'] = analysis.get('risk_level', 'low')
                
                enhanced_data.append(enhanced_item)
                
            except Exception as e:
                logger.warning(f"ML attendance enhancement failed: {e}")
                enhanced_data.append(item)
        
        return enhanced_data
    
    async def get_export_insights(self, module: str, data_type: str, data: List[Dict]) -> Dict[str, Any]:
        """Generate ML-powered insights for export data"""
        if not self.is_ml_available() or not data:
            return {'insights_available': False}
        
        try:
            insights = {
                'insights_available': True,
                'total_records': len(data),
                'ml_enhanced': True,
                'generated_at': time.time()
            }
            
            if module == 'students' and data_type == 'student_list':
                # Student-specific insights
                risk_levels = [item.get('ML_Risk_Level', 'unknown') for item in data]
                insights['high_risk_students'] = risk_levels.count('high')
                insights['low_risk_students'] = risk_levels.count('low')
                insights['risk_distribution'] = {
                    'high': risk_levels.count('high'),
                    'medium': risk_levels.count('medium'),
                    'low': risk_levels.count('low')
                }
            
            elif module == 'fees':
                # Fee-specific insights
                payment_risks = [item.get('ML_Payment_Risk', 0.5) for item in data if 'ML_Payment_Risk' in item]
                if payment_risks:
                    insights['avg_payment_risk'] = sum(payment_risks) / len(payment_risks)
                    insights['high_risk_payments'] = len([r for r in payment_risks if r > 0.7])
            
            return insights
            
        except Exception as e:
            logger.error(f"Failed to generate ML insights: {e}")
            return {'insights_available': False, 'error': str(e)}

# Global instances
ml_enhancer = MLExportEnhancer()