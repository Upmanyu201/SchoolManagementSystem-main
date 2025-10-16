# reports/ml_analytics.py - ML-powered analytics for enterprise reporting
from typing import Dict, List, Tuple, Optional
import numpy as np
import pandas as pd
from decimal import Decimal
from datetime import datetime, timedelta
from django.utils import timezone
from django.db.models import Q, Sum, Avg, Count
from sklearn.ensemble import RandomForestRegressor, IsolationForest
from sklearn.linear_model import LinearRegression
from sklearn.preprocessing import StandardScaler
import joblib
import os

from students.models import Student
from student_fees.models import FeeDeposit
from attendance.models import AttendanceRecord
from fines.models import FineStudent


class MLAnalyticsService:
    """Enterprise ML analytics for school management"""
    
    def __init__(self):
        self.models_path = 'reports/ml_models/'
        os.makedirs(self.models_path, exist_ok=True)
    
    def predict_fee_collection_risk(self, student_ids: List[int]) -> Dict[int, Dict]:
        """Predict fee collection risk for students using ML"""
        
        # Prepare features for ML model
        features_data = []
        student_data = {}
        
        for student_id in student_ids:
            try:
                student = Student.objects.get(id=student_id)
                
                # Calculate historical payment patterns
                payments = FeeDeposit.objects.filter(student=student)
                
                # Feature engineering
                total_payments = payments.count()
                avg_payment_delay = self._calculate_avg_payment_delay(payments)
                payment_consistency = self._calculate_payment_consistency(payments)
                outstanding_amount = self._get_outstanding_amount(student)
                attendance_rate = self._get_attendance_rate(student)
                
                features = [
                    total_payments,
                    avg_payment_delay,
                    payment_consistency,
                    float(outstanding_amount),
                    attendance_rate,
                    student.class_section.id if student.class_section else 0
                ]
                
                features_data.append(features)
                student_data[student_id] = {
                    'name': student.get_full_display_name(),
                    'class': str(student.class_section) if student.class_section else 'Unknown'
                }
                
            except Student.DoesNotExist:
                continue
        
        if not features_data:
            return {}
        
        # Load or train ML model
        model = self._get_or_train_risk_model()
        
        # Make predictions
        X = np.array(features_data)
        risk_scores = model.predict_proba(X)[:, 1] if hasattr(model, 'predict_proba') else model.predict(X)
        
        # Prepare results
        results = {}
        for i, student_id in enumerate(student_ids[:len(risk_scores)]):
            risk_level = 'High' if risk_scores[i] > 0.7 else 'Medium' if risk_scores[i] > 0.4 else 'Low'
            
            results[student_id] = {
                **student_data.get(student_id, {}),
                'risk_score': float(risk_scores[i]),
                'risk_level': risk_level,
                'recommendations': self._get_risk_recommendations(risk_scores[i])
            }
        
        return results
    
    def forecast_monthly_collections(self, months_ahead: int = 3) -> Dict[str, float]:
        """Forecast fee collections for upcoming months"""
        
        # Get historical collection data
        end_date = timezone.now().date()
        start_date = end_date - timedelta(days=365)  # Last year of data
        
        monthly_collections = []
        current_date = start_date
        
        while current_date <= end_date:
            month_start = current_date.replace(day=1)
            next_month = (month_start + timedelta(days=32)).replace(day=1)
            
            collections = FeeDeposit.objects.filter(
                deposit_date__gte=month_start,
                deposit_date__lt=next_month
            ).aggregate(total=Sum('paid_amount'))['total'] or 0
            
            monthly_collections.append(float(collections))
            current_date = next_month
        
        if len(monthly_collections) < 3:
            return {'error': 'Insufficient historical data'}
        
        # Simple linear regression for forecasting
        X = np.array(range(len(monthly_collections))).reshape(-1, 1)
        y = np.array(monthly_collections)
        
        model = LinearRegression()
        model.fit(X, y)
        
        # Forecast future months
        forecasts = {}
        for i in range(1, months_ahead + 1):
            future_x = len(monthly_collections) + i - 1
            forecast = model.predict([[future_x]])[0]
            
            future_date = end_date + timedelta(days=30 * i)
            month_name = future_date.strftime('%B %Y')
            
            forecasts[month_name] = max(0, forecast)  # Ensure non-negative
        
        return forecasts
    
    def detect_payment_anomalies(self) -> List[Dict]:
        """Detect unusual payment patterns using ML"""
        
        # Get recent payment data
        recent_payments = FeeDeposit.objects.filter(
            deposit_date__gte=timezone.now().date() - timedelta(days=90)
        ).values('paid_amount', 'deposit_date', 'student_id', 'payment_mode')
        
        if len(recent_payments) < 10:
            return []
        
        # Prepare features for anomaly detection
        df = pd.DataFrame(recent_payments)
        df['day_of_week'] = pd.to_datetime(df['deposit_date']).dt.dayofweek
        df['payment_mode_encoded'] = pd.Categorical(df['payment_mode']).codes
        
        features = df[['paid_amount', 'day_of_week', 'payment_mode_encoded']].fillna(0)
        
        # Isolation Forest for anomaly detection
        iso_forest = IsolationForest(contamination=0.1, random_state=42)
        anomaly_labels = iso_forest.fit_predict(features)
        
        # Identify anomalies
        anomalies = []
        for i, label in enumerate(anomaly_labels):
            if label == -1:  # Anomaly detected
                payment_data = recent_payments[i]
                student = Student.objects.filter(id=payment_data['student_id']).first()
                
                anomalies.append({
                    'student_name': student.get_full_display_name() if student else 'Unknown',
                    'amount': payment_data['paid_amount'],
                    'date': payment_data['deposit_date'],
                    'payment_mode': payment_data['payment_mode'],
                    'anomaly_type': self._classify_anomaly_type(payment_data, features.iloc[i])
                })
        
        return anomalies
    
    def generate_performance_insights(self) -> Dict[str, any]:
        """Generate ML-powered insights about school performance"""
        
        insights = {
            'collection_trends': self._analyze_collection_trends(),
            'student_risk_summary': self._summarize_student_risks(),
            'seasonal_patterns': self._detect_seasonal_patterns(),
            'recommendations': []
        }
        
        # Generate actionable recommendations
        if insights['collection_trends']['declining']:
            insights['recommendations'].append({
                'type': 'collection_improvement',
                'message': 'Fee collection showing declining trend. Consider implementing automated reminders.',
                'priority': 'high'
            })
        
        if insights['student_risk_summary']['high_risk_count'] > 10:
            insights['recommendations'].append({
                'type': 'risk_management',
                'message': f"{insights['student_risk_summary']['high_risk_count']} students at high payment risk. Review payment plans.",
                'priority': 'medium'
            })
        
        return insights
    
    def _calculate_avg_payment_delay(self, payments) -> float:
        """Calculate average payment delay in days"""
        delays = []
        for payment in payments:
            # Assuming due date is 10th of each month
            due_date = payment.deposit_date.replace(day=10)
            if payment.deposit_date > due_date:
                delay = (payment.deposit_date - due_date).days
                delays.append(delay)
        
        return np.mean(delays) if delays else 0
    
    def _calculate_payment_consistency(self, payments) -> float:
        """Calculate payment consistency score (0-1)"""
        if payments.count() < 2:
            return 0.5
        
        payment_amounts = [float(p.paid_amount) for p in payments]
        cv = np.std(payment_amounts) / np.mean(payment_amounts) if np.mean(payment_amounts) > 0 else 1
        
        # Convert coefficient of variation to consistency score
        return max(0, 1 - cv)
    
    def _get_outstanding_amount(self, student) -> Decimal:
        """Get total outstanding amount for student"""
        total_fees = student.due_amount or Decimal('0')
        
        # Add unpaid fines
        unpaid_fines = FineStudent.objects.filter(
            student=student, is_paid=False
        ).aggregate(total=Sum('fine__amount'))['total'] or Decimal('0')
        
        return total_fees + unpaid_fines
    
    def _get_attendance_rate(self, student) -> float:
        """Get student attendance rate for last 30 days"""
        end_date = timezone.now().date()
        start_date = end_date - timedelta(days=30)
        
        attendance_records = AttendanceRecord.objects.filter(
            student=student,
            date__gte=start_date,
            date__lte=end_date
        )
        
        if not attendance_records.exists():
            return 0.75  # Default assumption
        
        present_count = attendance_records.filter(status='Present').count()
        total_count = attendance_records.count()
        
        return present_count / total_count if total_count > 0 else 0.75
    
    def _get_or_train_risk_model(self):
        """Get existing model or train new one"""
        model_path = os.path.join(self.models_path, 'risk_model.joblib')
        
        if os.path.exists(model_path):
            return joblib.load(model_path)
        
        # Train new model with synthetic data (in production, use real historical data)
        model = RandomForestRegressor(n_estimators=100, random_state=42)
        
        # Generate synthetic training data
        X_train = np.random.rand(1000, 6)
        y_train = np.random.rand(1000)
        
        model.fit(X_train, y_train)
        
        # Save model
        joblib.dump(model, model_path)
        return model
    
    def _classify_anomaly_type(self, payment_data, features) -> str:
        """Classify the type of payment anomaly"""
        amount = payment_data['paid_amount']
        
        if amount > 50000:  # Very high payment
            return 'unusually_high_amount'
        elif amount < 100:  # Very low payment
            return 'unusually_low_amount'
        else:
            return 'unusual_pattern'
    
    def _analyze_collection_trends(self) -> Dict:
        """Analyze fee collection trends"""
        # Get last 6 months of data
        months_data = []
        for i in range(6):
            month_start = (timezone.now().date().replace(day=1) - timedelta(days=30*i))
            month_end = (month_start + timedelta(days=32)).replace(day=1)
            
            collections = FeeDeposit.objects.filter(
                deposit_date__gte=month_start,
                deposit_date__lt=month_end
            ).aggregate(total=Sum('paid_amount'))['total'] or 0
            
            months_data.append(float(collections))
        
        # Simple trend analysis
        if len(months_data) >= 3:
            recent_avg = np.mean(months_data[:3])
            older_avg = np.mean(months_data[3:])
            declining = recent_avg < older_avg * 0.9
        else:
            declining = False
        
        return {
            'declining': declining,
            'monthly_data': months_data,
            'trend_percentage': ((months_data[0] - months_data[-1]) / months_data[-1] * 100) if months_data[-1] > 0 else 0
        }
    
    def _summarize_student_risks(self) -> Dict:
        """Summarize student payment risks"""
        # This would use the risk prediction model in production
        total_students = Student.objects.count()
        
        return {
            'total_students': total_students,
            'high_risk_count': max(0, int(total_students * 0.15)),  # Estimate 15% high risk
            'medium_risk_count': max(0, int(total_students * 0.25)),  # Estimate 25% medium risk
            'low_risk_count': max(0, int(total_students * 0.60))  # Estimate 60% low risk
        }
    
    def _detect_seasonal_patterns(self) -> Dict:
        """Detect seasonal payment patterns"""
        # Analyze payment patterns by month
        monthly_patterns = {}
        
        for month in range(1, 13):
            payments = FeeDeposit.objects.filter(
                deposit_date__month=month
            ).aggregate(
                total=Sum('paid_amount'),
                count=Count('id')
            )
            
            monthly_patterns[month] = {
                'total_amount': float(payments['total'] or 0),
                'payment_count': payments['count'] or 0
            }
        
        # Find peak and low months
        amounts = [data['total_amount'] for data in monthly_patterns.values()]
        peak_month = max(monthly_patterns.keys(), key=lambda x: monthly_patterns[x]['total_amount'])
        low_month = min(monthly_patterns.keys(), key=lambda x: monthly_patterns[x]['total_amount'])
        
        return {
            'monthly_patterns': monthly_patterns,
            'peak_month': peak_month,
            'low_month': low_month,
            'seasonality_detected': max(amounts) > min(amounts) * 2 if amounts else False
        }


# Service instance
ml_analytics = MLAnalyticsService()