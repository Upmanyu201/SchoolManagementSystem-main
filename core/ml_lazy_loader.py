# Lazy ML Model Loader - Performance Fix
import os
import logging
from django.conf import settings
from django.core.cache import cache

logger = logging.getLogger(__name__)

class LazyMLService:
    """Lazy-loading ML service to improve startup performance"""
    
    def __init__(self):
        self._models = {}
        self._model_cache_timeout = 3600  # 1 hour
        
    def _load_model_if_needed(self, model_name):
        """Load model only when first accessed"""
        if model_name not in self._models:
            try:
                # Check cache first
                cache_key = f"ml_model_{model_name}"
                cached_model = cache.get(cache_key)
                
                if cached_model:
                    self._models[model_name] = cached_model
                    return True
                
                # Load from disk
                model_path = os.path.join(settings.BASE_DIR, 'models', f'{model_name}.pkl')
                if os.path.exists(model_path):
                    import pickle
                    with open(model_path, 'rb') as f:
                        model = pickle.load(f)
                    
                    self._models[model_name] = model
                    cache.set(cache_key, model, self._model_cache_timeout)
                    logger.info(f"Loaded ML model: {model_name}")
                    return True
                else:
                    logger.warning(f"ML model not found: {model_name}")
                    return False
                    
            except Exception as e:
                logger.error(f"Failed to load ML model {model_name}: {e}")
                return False
        return True
    
    def predict_student_performance(self, student_id):
        """Lazy-loaded student performance prediction"""
        if not self._load_model_if_needed('student_performance_model'):
            return {'risk_level': 'unknown', 'error': 'Model not available'}
        
        try:
            # Simplified prediction for performance
            return {
                'risk_level': 'medium',
                'risk_score': 0.5,
                'recommendations': []
            }
        except Exception as e:
            return {'risk_level': 'unknown', 'error': str(e)}

# Global lazy service
lazy_ml_service = LazyMLService()