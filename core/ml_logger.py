# core/ml_logger.py - ML-specific logging
import logging
from django.conf import settings

# Create ML-specific logger
ml_logger = logging.getLogger('ml_operations')

class MLLogger:
    @staticmethod
    def log_model_load(model_name, success=True, error=None):
        """Log ML model loading"""
        if success:
            ml_logger.info(f"✅ ML Model loaded: {model_name}")
        else:
            ml_logger.error(f"❌ ML Model failed to load: {model_name} - Error: {error}")
    
    @staticmethod
    def log_prediction(model_name, student_id, result, duration=None):
        """Log ML predictions"""
        ml_logger.info(f"🧠 ML Prediction - Model: {model_name}, Student: {student_id}, Result: {result}, Duration: {duration}ms")
    
    @staticmethod
    def log_service_call(service_name, parameters, success=True):
        """Log ML service calls"""
        if success:
            ml_logger.info(f"🔧 ML Service called: {service_name} with params: {parameters}")
        else:
            ml_logger.warning(f"⚠️ ML Service failed: {service_name} with params: {parameters}")
    
    @staticmethod
    def log_cache_hit(cache_key, model_name):
        """Log ML cache hits"""
        ml_logger.debug(f"💾 ML Cache hit: {cache_key} for model: {model_name}")
    
    @staticmethod
    def log_fallback(service_name, reason):
        """Log ML fallback usage"""
        ml_logger.warning(f"🔄 ML Fallback used for {service_name}: {reason}")

# Quick access functions
def log_ml_model_load(model_name, success=True, error=None):
    MLLogger.log_model_load(model_name, success, error)

def log_ml_prediction(model_name, student_id, result, duration=None):
    MLLogger.log_prediction(model_name, student_id, result, duration)

def log_ml_service_call(service_name, parameters, success=True):
    MLLogger.log_service_call(service_name, parameters, success)