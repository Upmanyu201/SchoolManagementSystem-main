# ML Models for School Management System - TDD Implementation
import joblib
import numpy as np
import pandas as pd
from sklearn.ensemble import RandomForestClassifier, RandomForestRegressor
from sklearn.model_selection import train_test_split
from sklearn.metrics import accuracy_score, mean_squared_error
from sklearn.preprocessing import StandardScaler
import logging
import os
from pathlib import Path
from typing import Dict, List, Any
import time

logger = logging.getLogger(__name__)

class StudentPerformancePredictor:
    """ML model for predicting student performance"""
    
    def __init__(self):
        self.model = RandomForestClassifier(
            n_estimators=50,
            max_depth=10,
            random_state=42,
            class_weight='balanced'
        )
        self.scaler = StandardScaler()
        self.is_trained = False
        self.feature_names = ['attendance_rate', 'previous_grade', 'assignment_completion']
        self.model_path = Path('models/student_performance_model.pkl')
        self.scaler_path = Path('models/student_performance_scaler.pkl')
    
    def train(self, training_data: pd.DataFrame) -> Dict[str, float]:
        """Train the performance prediction model"""
        try:
            # Prepare features and target
            X = training_data[self.feature_names].values
            y = training_data['performance_category'].values
            
            # Split data
            X_train, X_test, y_train, y_test = train_test_split(
                X, y, test_size=0.2, random_state=42, stratify=y
            )
            
            # Scale features
            X_train_scaled = self.scaler.fit_transform(X_train)
            X_test_scaled = self.scaler.transform(X_test)
            
            # Train model
            self.model.fit(X_train_scaled, y_train)
            
            # Evaluate model
            train_predictions = self.model.predict(X_train_scaled)
            test_predictions = self.model.predict(X_test_scaled)
            
            train_accuracy = accuracy_score(y_train, train_predictions)
            test_accuracy = accuracy_score(y_test, test_predictions)
            
            self.is_trained = True
            
            # Save model and scaler
            self._save_model()
            
            logger.info(f"Model trained - Train accuracy: {train_accuracy:.3f}, Test accuracy: {test_accuracy:.3f}")
            
            return {
                'train_accuracy': train_accuracy,
                'test_accuracy': test_accuracy,
                'feature_importance': dict(zip(self.feature_names, self.model.feature_importances_))
            }
            
        except Exception as e:
            logger.error(f"Model training failed: {e}")
            raise
    
    def predict(self, features: List[float]) -> np.ndarray:
        """Predict performance probabilities"""
        if not self.is_trained:
            self._load_model()
        
        try:
            # Ensure features are in correct format
            features_array = np.array(features).reshape(1, -1)
            
            # Scale features
            features_scaled = self.scaler.transform(features_array)
            
            # Get prediction probabilities
            probabilities = self.model.predict_proba(features_scaled)[0]
            
            return probabilities
            
        except Exception as e:
            logger.error(f"Prediction failed: {e}")
            # Return neutral probabilities on error
            return np.array([0.33, 0.33, 0.34])
    
    def predict_risk_level(self, features: List[float]) -> Dict[str, Any]:
        """Predict risk level with interpretable output"""
        probabilities = self.predict(features)
        
        # Map probabilities to risk levels
        risk_score = probabilities[0] * 1.0 + probabilities[1] * 0.5 + probabilities[2] * 0.0
        
        if risk_score > 0.7:
            risk_level = 'high'
        elif risk_score > 0.4:
            risk_level = 'medium'
        else:
            risk_level = 'low'
        
        return {
            'risk_level': risk_level,
            'risk_score': float(risk_score),
            'class_probabilities': {
                'poor': float(probabilities[0]),
                'good': float(probabilities[1]),
                'excellent': float(probabilities[2])
            }
        }
    
    def _save_model(self):
        """Save trained model and scaler"""
        try:
            # Create models directory if it doesn't exist
            self.model_path.parent.mkdir(exist_ok=True)
            
            # Save model and scaler
            joblib.dump(self.model, self.model_path)
            joblib.dump(self.scaler, self.scaler_path)
            
            logger.info("Model and scaler saved successfully")
            
        except Exception as e:
            logger.error(f"Failed to save model: {e}")
    
    def _load_model(self):
        """Load trained model and scaler"""
        try:
            if self.model_path.exists() and self.scaler_path.exists():
                self.model = joblib.load(self.model_path)
                self.scaler = joblib.load(self.scaler_path)
                self.is_trained = True
                logger.info("Model and scaler loaded successfully")
            else:
                logger.warning("No trained model found")
                
        except Exception as e:
            logger.error(f"Failed to load model: {e}")

class PaymentDelayPredictor:
    """ML model for predicting fee payment delays"""
    
    def __init__(self):
        self.model = RandomForestRegressor(
            n_estimators=30,
            max_depth=8,
            random_state=42
        )
        self.scaler = StandardScaler()
        self.is_trained = False
        self.feature_names = ['amount', 'days_until_due', 'previous_delays', 'parent_income_bracket']
        self.model_path = Path('models/payment_delay_model.pkl')
        self.scaler_path = Path('models/payment_delay_scaler.pkl')
    
    def train(self, training_data: pd.DataFrame) -> Dict[str, float]:
        """Train the payment delay prediction model"""
        try:
            # Prepare features and target
            X = training_data[self.feature_names].values
            y = training_data['delay_days'].values
            
            # Split data
            X_train, X_test, y_train, y_test = train_test_split(
                X, y, test_size=0.2, random_state=42
            )
            
            # Scale features
            X_train_scaled = self.scaler.fit_transform(X_train)
            X_test_scaled = self.scaler.transform(X_test)
            
            # Train model
            self.model.fit(X_train_scaled, y_train)
            
            # Evaluate model
            train_predictions = self.model.predict(X_train_scaled)
            test_predictions = self.model.predict(X_test_scaled)
            
            train_mse = mean_squared_error(y_train, train_predictions)
            test_mse = mean_squared_error(y_test, test_predictions)
            
            self.is_trained = True
            
            # Save model
            self._save_model()
            
            logger.info(f"Payment delay model trained - Train MSE: {train_mse:.3f}, Test MSE: {test_mse:.3f}")
            
            return {
                'train_mse': train_mse,
                'test_mse': test_mse,
                'feature_importance': dict(zip(self.feature_names, self.model.feature_importances_))
            }
            
        except Exception as e:
            logger.error(f"Payment delay model training failed: {e}")
            raise
    
    def predict_delay(self, features: List[float]) -> Dict[str, Any]:
        """Predict payment delay"""
        if not self.is_trained:
            self._load_model()
        
        try:
            # Ensure features are in correct format
            features_array = np.array(features).reshape(1, -1)
            
            # Scale features
            features_scaled = self.scaler.transform(features_array)
            
            # Predict delay days
            predicted_delay = self.model.predict(features_scaled)[0]
            
            # Convert to probability and risk level
            delay_probability = min(max(predicted_delay / 30.0, 0.0), 1.0)  # Normalize to 0-1
            
            return {
                'expected_delay_days': max(0, int(predicted_delay)),
                'delay_probability': float(delay_probability),
                'risk_level': 'high' if delay_probability > 0.7 else 'medium' if delay_probability > 0.3 else 'low'
            }
            
        except Exception as e:
            logger.error(f"Payment delay prediction failed: {e}")
            return {
                'expected_delay_days': 0,
                'delay_probability': 0.5,
                'risk_level': 'medium'
            }
    
    def _save_model(self):
        """Save trained model and scaler"""
        try:
            self.model_path.parent.mkdir(exist_ok=True)
            joblib.dump(self.model, self.model_path)
            joblib.dump(self.scaler, self.scaler_path)
            logger.info("Payment delay model saved successfully")
        except Exception as e:
            logger.error(f"Failed to save payment delay model: {e}")
    
    def _load_model(self):
        """Load trained model and scaler"""
        try:
            if self.model_path.exists() and self.scaler_path.exists():
                self.model = joblib.load(self.model_path)
                self.scaler = joblib.load(self.scaler_path)
                self.is_trained = True
                logger.info("Payment delay model loaded successfully")
            else:
                logger.warning("No trained payment delay model found")
        except Exception as e:
            logger.error(f"Failed to load payment delay model: {e}")

class AttendancePatternAnalyzer:
    """ML model for analyzing attendance patterns"""
    
    def __init__(self):
        from sklearn.cluster import KMeans
        self.model = KMeans(n_clusters=3, random_state=42)  # Low, Medium, High attendance
        self.is_trained = False
        self.model_path = Path('models/attendance_pattern_model.pkl')
    
    def analyze_patterns(self, attendance_data: np.ndarray) -> Dict[str, Any]:
        """Analyze attendance patterns using clustering"""
        try:
            if not self.is_trained:
                self._train_or_load()
            
            # Predict cluster
            cluster = self.model.predict(attendance_data.reshape(1, -1))[0]
            
            # Map cluster to pattern type
            pattern_types = ['irregular', 'consistent', 'excellent']
            pattern_type = pattern_types[cluster]
            
            # Calculate trend
            if len(attendance_data) > 1:
                trend = 'improving' if attendance_data[-1] > attendance_data[0] else 'declining' if attendance_data[-1] < attendance_data[0] else 'stable'
            else:
                trend = 'stable'
            
            # Determine risk level
            avg_attendance = np.mean(attendance_data)
            risk_level = 'high' if avg_attendance < 0.7 else 'medium' if avg_attendance < 0.85 else 'low'
            
            return {
                'pattern_type': pattern_type,
                'trend': trend,
                'risk_level': risk_level,
                'average_attendance': float(avg_attendance),
                'cluster': int(cluster)
            }
            
        except Exception as e:
            logger.error(f"Attendance pattern analysis failed: {e}")
            return {
                'pattern_type': 'unknown',
                'trend': 'stable',
                'risk_level': 'medium',
                'average_attendance': 0.8,
                'cluster': 1
            }
    
    def _train_or_load(self):
        """Train model with synthetic data or load existing model"""
        try:
            if self.model_path.exists():
                self.model = joblib.load(self.model_path)
                self.is_trained = True
                logger.info("Attendance pattern model loaded")
            else:
                # Generate synthetic training data
                np.random.seed(42)
                synthetic_data = np.random.beta(2, 2, (1000, 30))  # 1000 students, 30 days
                
                self.model.fit(synthetic_data)
                self.is_trained = True
                
                # Save model
                self.model_path.parent.mkdir(exist_ok=True)
                joblib.dump(self.model, self.model_path)
                logger.info("Attendance pattern model trained and saved")
                
        except Exception as e:
            logger.error(f"Failed to train/load attendance model: {e}")

# Model instances
student_performance_predictor = StudentPerformancePredictor()
payment_delay_predictor = PaymentDelayPredictor()
attendance_pattern_analyzer = AttendancePatternAnalyzer()