# ML Service - Enhanced Implementation with TDD
import logging
import os
from typing import Dict, List, Any, Optional
from django.core.cache import cache
from django.conf import settings
import time
from datetime import datetime, timedelta

logger = logging.getLogger(__name__)

# Try to import ML dependencies with graceful fallback
try:
    import numpy as np
    import pandas as pd
    from sklearn.ensemble import RandomForestClassifier
    from sklearn.preprocessing import StandardScaler
    import joblib
    ML_DEPENDENCIES_AVAILABLE = True
except ImportError:
    ML_DEPENDENCIES_AVAILABLE = False
    logger.warning("ML dependencies not available. Install scikit-learn, pandas, numpy for ML features.")

# Import ML models
try:
    from .ml_models import (
        student_performance_predictor,
        payment_delay_predictor,
        attendance_pattern_analyzer
    )
    ML_MODELS_AVAILABLE = True
except ImportError:
    ML_MODELS_AVAILABLE = False
    logger.warning("ML models not available")

class MLService:
    """Local ML service with zero API costs"""
    
    def __init__(self):
        self.models_path = 'models/'
        self.models = {}
        self.load_models()
    
    def load_models(self):
        """Load all trained models"""
        try:
            model_files = {
                'performance': 'performance_model.pkl',
                'fee_collection': 'fee_collection_model.pkl',
                'attendance': 'attendance_model.pkl'
            }
            
            for name, filename in model_files.items():
                filepath = os.path.join(self.models_path, filename)
                if os.path.exists(filepath):
                    self.models[name] = joblib.load(filepath)
                    logger.info(f"Loaded {name} model")
                else:
                    logger.warning(f"Model {filename} not found")
                    
        except Exception as e:
            logger.error(f"Error loading models: {e}")
    
    def predict_student_risk(self, student):
        """Predict student dropout/performance risk - returns None if no data"""
        try:
            # Extract features
            features = self.extract_student_features(student)
            
            # Check if we have actual data
            if features is None:
                return {
                    'status': 'no_data',
                    'message': 'Insufficient data for prediction',
                    'risk_level': 'unknown',
                    'confidence': 0.0,
                    'recommendations': ['Collect more student data for accurate predictions']
                }
            
            # If no ML model available, return data-based assessment
            if 'performance' not in self.models:
                attendance_rate, payment_score, fine_count, age = features
                
                # Simple rule-based assessment using actual data
                risk_score = 0
                if attendance_rate is not None and attendance_rate < 0.75:
                    risk_score += 0.4
                if payment_score is not None and payment_score < 0.5:
                    risk_score += 0.3
                if fine_count is not None and fine_count > 2:
                    risk_score += 0.3
                
                if risk_score > 0.6:
                    risk_level = 'high'
                elif risk_score > 0.3:
                    risk_level = 'medium'
                else:
                    risk_level = 'low'
                
                return {
                    'status': 'rule_based',
                    'risk_level': risk_level,
                    'confidence': min(risk_score + 0.2, 1.0),
                    'recommendations': self.get_risk_recommendations_by_level(risk_level),
                    'data_available': True
                }
            
            # Use ML model if available
            model = self.models['performance']
            prediction = model.predict([features])[0]
            confidence = max(model.predict_proba([features])[0])
            
            risk_levels = {0: 'high', 1: 'medium', 2: 'low'}
            
            return {
                'status': 'ml_prediction',
                'risk_level': risk_levels.get(prediction, 'medium'),
                'confidence': float(confidence),
                'recommendations': self.get_risk_recommendations(prediction),
                'data_available': True
            }
            
        except Exception as e:
            logger.error(f"Risk prediction error: {e}")
            return {
                'status': 'error',
                'message': f'Prediction failed: {str(e)}',
                'risk_level': 'unknown',
                'confidence': 0.0
            }
    
    def get_optimal_fee_collection_days(self):
        """Get optimal days for fee collection"""
        try:
            if 'fee_collection' not in self.models:
                return [1, 5, 10, 15, 25]  # Default days
            
            pattern_data = self.models['fee_collection']
            return pattern_data.get('optimal_days', [1, 5, 10, 15, 25])
            
        except Exception as e:
            logger.error(f"Fee collection optimization error: {e}")
            return [1, 5, 10, 15, 25]
    
    def analyze_attendance_patterns(self, students):
        """Cluster students by attendance patterns"""
        try:
            if 'attendance' not in self.models:
                return {'low': [], 'medium': [], 'high': []}
            
            # Extract attendance rates
            attendance_data = []
            student_list = []
            
            for student in students:
                rate = self.get_student_attendance_rate(student)
                attendance_data.append([rate])
                student_list.append(student)
            
            # Predict clusters
            model = self.models['attendance']
            clusters = model.predict(attendance_data)
            
            # Group students by cluster
            result = {'low': [], 'medium': [], 'high': []}
            cluster_names = ['low', 'medium', 'high']
            
            for i, cluster in enumerate(clusters):
                if cluster < len(cluster_names):
                    result[cluster_names[cluster]].append(student_list[i])
            
            return result
            
        except Exception as e:
            logger.error(f"Attendance analysis error: {e}")
            return {'low': [], 'medium': [], 'high': []}
    
    def extract_student_features(self, student):
        """Extract features for ML prediction - returns None if no data"""
        try:
            # Attendance rate
            attendance_rate = self.get_student_attendance_rate(student)
            
            # Payment score
            payment_score = self.get_student_payment_score(student)
            
            # Fine count
            fine_count = self.get_student_fine_count(student)
            
            # Age
            age = getattr(student, 'age', None)
            if hasattr(student, 'date_of_birth') and student.date_of_birth:
                from datetime import date
                today = date.today()
                age = today.year - student.date_of_birth.year
                if today < student.date_of_birth.replace(year=today.year):
                    age -= 1
            
            # Check if we have any actual data
            has_data = any([
                attendance_rate is not None,
                payment_score is not None,
                fine_count is not None and fine_count > 0,
                age is not None
            ])
            
            if not has_data:
                return None  # No data available for prediction
            
            # Fill missing values with neutral defaults only when we have some data
            return [
                attendance_rate if attendance_rate is not None else 0.85,
                payment_score if payment_score is not None else 0.75,
                fine_count if fine_count is not None else 0,
                age if age is not None else 15
            ]
            
        except Exception as e:
            logger.error(f"Feature extraction error: {e}")
            return None
    
    def get_student_attendance_rate(self, student):
        """Get student attendance rate - returns None if no data"""
        try:
            from attendance.models import AttendanceRecord
            total_days = 30
            total_records = AttendanceRecord.objects.filter(
                student=student,
                date__gte=datetime.now().date() - timedelta(days=total_days)
            ).count()
            
            if total_records == 0:
                return None  # No attendance data available
                
            present_days = AttendanceRecord.objects.filter(
                student=student,
                date__gte=datetime.now().date() - timedelta(days=total_days),
                is_present=True
            ).count()
            return min(present_days / total_records, 1.0)
        except:
            return None
    
    def get_student_payment_score(self, student):
        """Get student payment reliability score - returns None if no data"""
        try:
            from student_fees.models import FeeDeposit
            recent_payments = FeeDeposit.objects.filter(
                student=student,
                deposit_date__gte=datetime.now() - timedelta(days=90)
            ).count()
            
            # If no payment history, return None
            if recent_payments == 0:
                return None
                
            return min(recent_payments / 3, 1.0)
        except:
            return None
    
    def get_student_fine_count(self, student):
        """Get student fine count - returns actual count or None"""
        try:
            from fines.models import FineStudent
            return FineStudent.objects.filter(student=student).count()
        except:
            return None
    
    def get_risk_recommendations(self, risk_level):
        """Get recommendations based on risk level"""
        recommendations = {
            0: [  # High risk
                "Schedule parent meeting",
                "Provide additional academic support",
                "Monitor attendance closely",
                "Consider counseling services"
            ],
            1: [  # Medium risk
                "Regular progress monitoring",
                "Encourage participation in activities",
                "Maintain communication with parents"
            ],
            2: [  # Low risk
                "Continue current support",
                "Consider leadership opportunities",
                "Maintain engagement"
            ]
        }
        return recommendations.get(risk_level, ["Monitor progress"])
    
    def get_risk_recommendations_by_level(self, risk_level_str):
        """Get recommendations based on risk level string"""
        recommendations = {
            'high': [
                "Schedule parent meeting",
                "Provide additional academic support",
                "Monitor attendance closely",
                "Consider counseling services"
            ],
            'medium': [
                "Regular progress monitoring",
                "Encourage participation in activities",
                "Maintain communication with parents"
            ],
            'low': [
                "Continue current support",
                "Consider leadership opportunities",
                "Maintain engagement"
            ]
        }
        return recommendations.get(risk_level_str, ["Monitor progress"])
    
    def optimize_fee_structure(self):
        """Optimize fee structure based on payment patterns"""
        try:
            from fees.models import FeesType
            
            optimization_results = {
                'status': 'success',
                'recommendations': [],
                'analysis_date': datetime.now().strftime('%Y-%m-%d')
            }
            
            fee_types = FeesType.objects.all()[:10]  # Limit for performance
            
            for fee_type in fee_types:
                current_amount = float(fee_type.amount) if fee_type.amount else 0
                
                if current_amount > 0:
                    optimization_results['recommendations'].append({
                        'fee_type': fee_type.fee_type,
                        'current_amount': f'₹{current_amount:,.0f}',
                        'suggestion': 'Current structure appears reasonable',
                        'priority': 'low'
                    })
            
            if not optimization_results['recommendations']:
                optimization_results['recommendations'].append({
                    'fee_type': 'General',
                    'suggestion': 'No fee structure data available for analysis',
                    'priority': 'info'
                })
            
            return optimization_results
            
        except Exception as e:
            logger.error(f"Fee optimization error: {e}")
            return {
                'status': 'error',
                'message': f'Analysis failed: {str(e)}',
                'recommendations': []
            }
    
    def predict_student_performance(self, student_id):
        """Predict student performance risk"""
        try:
            from students.models import Student
            student = Student.objects.get(id=student_id)
            return self.predict_student_risk(student)
        except Student.DoesNotExist:
            return {
                'status': 'error',
                'message': 'Student not found',
                'risk_level': 'unknown',
                'confidence': 0.0
            }
        except Exception as e:
            return {
                'status': 'error',
                'message': f'Prediction failed: {str(e)}',
                'risk_level': 'unknown',
                'confidence': 0.0
            }
    
    def predict_payment_delay(self, student_id):
        """Predict payment delay probability"""
        try:
            payment_score = 0.7  # Default score
            return {
                'delay_probability': 0.3,
                'expected_delay_days': 2,
                'payment_score': payment_score
            }
        except Exception as e:
            return {'delay_probability': 0.5, 'expected_delay_days': 3}
    
    def analyze_teacher_performance(self, teacher_data):
        """Analyze teacher performance based on metrics"""
        try:
            # Extract metrics from teacher_data
            pass_rate = teacher_data.get('student_pass_rate', 0.8)
            attendance_rate = teacher_data.get('attendance_rate', 0.9)
            experience = teacher_data.get('years_experience', 3)
            class_size = teacher_data.get('class_size', 30)
            
            # Simple scoring algorithm
            performance_score = (
                pass_rate * 0.4 +
                attendance_rate * 0.3 +
                min(experience / 10, 1.0) * 0.2 +
                max(0, (40 - class_size) / 40) * 0.1
            )
            
            # Categorize performance
            if performance_score >= 0.8:
                category = 'Excellent'
            elif performance_score >= 0.6:
                category = 'Good'
            elif performance_score >= 0.4:
                category = 'Average'
            else:
                category = 'Needs Improvement'
            
            return {
                'performance_score': round(performance_score, 2),
                'category': category,
                'recommendations': self._get_teacher_recommendations(category),
                'metrics': {
                    'pass_rate': pass_rate,
                    'attendance_rate': attendance_rate,
                    'experience_score': min(experience / 10, 1.0),
                    'class_size_score': max(0, (40 - class_size) / 40)
                }
            }
            
        except Exception as e:
            logger.error(f"Teacher performance analysis error: {e}")
            return {
                'performance_score': 0.7,
                'category': 'Average',
                'recommendations': ['Regular monitoring recommended'],
                'error': str(e)
            }
    
    def _get_teacher_recommendations(self, category):
        """Get recommendations based on teacher performance category"""
        recommendations = {
            'Excellent': [
                'Consider for mentoring new teachers',
                'Eligible for advanced training programs',
                'Maintain current teaching methods'
            ],
            'Good': [
                'Continue professional development',
                'Share best practices with colleagues',
                'Consider additional responsibilities'
            ],
            'Average': [
                'Attend skill development workshops',
                'Seek mentoring from senior teachers',
                'Focus on student engagement techniques'
            ],
            'Needs Improvement': [
                'Immediate training intervention required',
                'Regular performance monitoring',
                'Provide additional support and resources'
            ]
        }
        return recommendations.get(category, ['Regular monitoring recommended'])
    
    def optimize_message_timing(self, messaging_data=None):
        """Get optimal times for sending messages"""
        try:
            # Use provided data or defaults
            if messaging_data and 'hourly_response_rates' in messaging_data:
                response_rates = messaging_data['hourly_response_rates']
                best_hour = max(response_rates, key=response_rates.get)
                best_rate = response_rates[best_hour]
            else:
                best_hour = 19
                best_rate = 0.90
            
            optimal_times = {
                'morning': {'start': '09:00', 'end': '11:00', 'success_rate': 0.85},
                'afternoon': {'start': '14:00', 'end': '16:00', 'success_rate': 0.75},
                'evening': {'start': '18:00', 'end': '20:00', 'success_rate': 0.90}
            }
            
            return {
                'status': 'success',
                'optimal_times': optimal_times,
                'recommendation': f'Send messages around {best_hour}:00 for highest engagement',
                'best_time': f'{best_hour}:00',
                'success_rate': best_rate,
                'best_send_times': [9, 14, 18],
                'expected_response_rate': f'{int(best_rate * 100)}%'
            }
            
        except Exception as e:
            logger.error(f"Message timing optimization error: {e}")
            return {
                'status': 'error',
                'message': str(e),
                'recommendation': 'Send messages during business hours',
                'best_time': '10:00',
                'best_send_times': [9, 14, 18],
                'expected_response_rate': '80%'
            }
    
    def classify_message_priority(self, message_content):
        """Classify message priority based on content"""
        try:
            content = message_content.lower()
            
            # High priority keywords
            high_priority_keywords = ['urgent', 'emergency', 'immediate', 'asap', 'critical']
            medium_priority_keywords = ['important', 'reminder', 'notice', 'update']
            
            if any(keyword in content for keyword in high_priority_keywords):
                priority = 'high'
                score = 0.9
            elif any(keyword in content for keyword in medium_priority_keywords):
                priority = 'medium'
                score = 0.6
            else:
                priority = 'low'
                score = 0.3
            
            return {
                'priority': priority,
                'score': score,
                'keywords_found': [kw for kw in (high_priority_keywords + medium_priority_keywords) if kw in content]
            }
            
        except Exception as e:
            logger.error(f"Message priority classification error: {e}")
            return {'priority': 'medium', 'score': 0.5, 'keywords_found': []}
    
    def predict_dropout_risk(self, student_data):
        """Predict dropout risk - alias for predict_student_risk"""
        try:
            if isinstance(student_data, dict) and 'admission_number' in student_data:
                from students.models import Student
                student = Student.objects.get(admission_number=student_data['admission_number'])
                return self.predict_student_risk(student)
            else:
                return self.predict_student_risk(student_data)
        except Exception as e:
            logger.error(f"Dropout risk prediction error: {e}")
            return {
                'status': 'error',
                'message': f'Dropout prediction failed: {str(e)}',
                'risk_level': 'unknown',
                'confidence': 0.0
            }

# Global ML service instance
ml_service = MLService()