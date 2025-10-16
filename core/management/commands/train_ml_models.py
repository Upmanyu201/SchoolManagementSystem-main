# Management command to train ML models - TDD Implementation
from django.core.management.base import BaseCommand, CommandError
from django.db import transaction
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import logging

logger = logging.getLogger(__name__)

class Command(BaseCommand):
    help = 'Train ML models for school management system'
    
    def add_arguments(self, parser):
        parser.add_argument(
            '--model',
            type=str,
            choices=['all', 'performance', 'payment', 'attendance'],
            default='all',
            help='Specify which model to train'
        )
        parser.add_argument(
            '--use-synthetic',
            action='store_true',
            help='Use synthetic data for training (useful for testing)'
        )
        parser.add_argument(
            '--min-samples',
            type=int,
            default=100,
            help='Minimum number of samples required for training'
        )
    
    def handle(self, *args, **options):
        """Main command handler"""
        self.stdout.write(
            self.style.SUCCESS('Starting ML model training...')
        )
        
        try:
            if options['model'] in ['all', 'performance']:
                self.train_performance_model(options)
            
            if options['model'] in ['all', 'payment']:
                self.train_payment_model(options)
            
            if options['model'] in ['all', 'attendance']:
                self.train_attendance_model(options)
            
            self.stdout.write(
                self.style.SUCCESS('ML model training completed successfully!')
            )
            
        except Exception as e:
            logger.error(f"ML model training failed: {e}")
            raise CommandError(f'Training failed: {e}')
    
    def train_performance_model(self, options):
        """Train student performance prediction model"""
        self.stdout.write('Training student performance model...')
        
        try:
            from core.ml_models import student_performance_predictor
            
            if options['use_synthetic']:
                training_data = self.generate_synthetic_performance_data(1000)
            else:
                training_data = self.prepare_performance_data()
            
            if len(training_data) < options['min_samples']:
                if not options['use_synthetic']:
                    self.stdout.write(
                        self.style.WARNING(
                            f'Insufficient data ({len(training_data)} samples). '
                            f'Using synthetic data for training.'
                        )
                    )
                    training_data = self.generate_synthetic_performance_data(1000)
                else:
                    raise CommandError(f'Insufficient training data: {len(training_data)} samples')
            
            # Train model
            results = student_performance_predictor.train(training_data)
            
            self.stdout.write(
                self.style.SUCCESS(
                    f'Performance model trained successfully! '
                    f'Test accuracy: {results["test_accuracy"]:.3f}'
                )
            )
            
            # Display feature importance
            self.stdout.write('Feature importance:')
            for feature, importance in results['feature_importance'].items():
                self.stdout.write(f'  {feature}: {importance:.3f}')
                
        except Exception as e:
            logger.error(f"Performance model training failed: {e}")
            raise CommandError(f'Performance model training failed: {e}')
    
    def train_payment_model(self, options):
        """Train payment delay prediction model"""
        self.stdout.write('Training payment delay model...')
        
        try:
            from core.ml_models import payment_delay_predictor
            
            if options['use_synthetic']:
                training_data = self.generate_synthetic_payment_data(800)
            else:
                training_data = self.prepare_payment_data()
            
            if len(training_data) < options['min_samples']:
                if not options['use_synthetic']:
                    self.stdout.write(
                        self.style.WARNING(
                            'Insufficient payment data. Using synthetic data for training.'
                        )
                    )
                    training_data = self.generate_synthetic_payment_data(800)
                else:
                    raise CommandError(f'Insufficient payment training data: {len(training_data)} samples')
            
            # Train model
            results = payment_delay_predictor.train(training_data)
            
            self.stdout.write(
                self.style.SUCCESS(
                    f'Payment delay model trained successfully! '
                    f'Test MSE: {results["test_mse"]:.3f}'
                )
            )
            
        except Exception as e:
            logger.error(f"Payment model training failed: {e}")
            raise CommandError(f'Payment model training failed: {e}')
    
    def train_attendance_model(self, options):
        """Train attendance pattern analysis model"""
        self.stdout.write('Training attendance pattern model...')
        
        try:
            from core.ml_models import attendance_pattern_analyzer
            
            # Attendance model uses unsupervised learning, so we just initialize it
            attendance_pattern_analyzer._train_or_load()
            
            self.stdout.write(
                self.style.SUCCESS('Attendance pattern model trained successfully!')
            )
            
        except Exception as e:
            logger.error(f"Attendance model training failed: {e}")
            raise CommandError(f'Attendance model training failed: {e}')
    
    def prepare_performance_data(self):
        """Prepare real student performance data for training"""
        try:
            from students.models import Student
            from django.db.models import Avg, Count
            
            # Get students with sufficient data
            students = Student.objects.annotate(
                avg_attendance=Avg('attendance_records__present'),
                total_records=Count('attendance_records')
            ).filter(total_records__gte=10)
            
            data = []
            for student in students:
                # Calculate features
                attendance_rate = student.avg_attendance or 0.8
                previous_grade = getattr(student, 'last_grade', 75)  # Default grade
                assignment_completion = 0.85  # Default completion rate
                
                # Determine performance category based on available data
                if hasattr(student, 'current_grade'):
                    if student.current_grade >= 85:
                        performance_category = 2  # Excellent
                    elif student.current_grade >= 70:
                        performance_category = 1  # Good
                    else:
                        performance_category = 0  # Poor
                else:
                    # Use attendance as proxy for performance
                    if attendance_rate >= 0.9:
                        performance_category = 2
                    elif attendance_rate >= 0.75:
                        performance_category = 1
                    else:
                        performance_category = 0
                
                data.append({
                    'attendance_rate': attendance_rate,
                    'previous_grade': previous_grade,
                    'assignment_completion': assignment_completion,
                    'performance_category': performance_category
                })
            
            return pd.DataFrame(data)
            
        except Exception as e:
            logger.warning(f"Could not prepare real performance data: {e}")
            return pd.DataFrame()
    
    def prepare_payment_data(self):
        """Prepare real payment data for training"""
        try:
            from student_fees.models import FeePayment
            from django.utils import timezone
            
            # Get payment records from last year
            cutoff_date = timezone.now() - timedelta(days=365)
            payments = FeePayment.objects.filter(
                created_at__gte=cutoff_date
            ).select_related('student')
            
            data = []
            for payment in payments:
                # Calculate delay days
                if hasattr(payment, 'due_date') and payment.due_date:
                    delay_days = max(0, (payment.created_at.date() - payment.due_date).days)
                else:
                    delay_days = 0
                
                # Extract features
                amount = float(payment.amount)
                days_until_due = 30  # Default
                previous_delays = 0  # Would need to calculate from history
                parent_income_bracket = 2  # Default middle income
                
                data.append({
                    'amount': amount,
                    'days_until_due': days_until_due,
                    'previous_delays': previous_delays,
                    'parent_income_bracket': parent_income_bracket,
                    'delay_days': delay_days
                })
            
            return pd.DataFrame(data)
            
        except Exception as e:
            logger.warning(f"Could not prepare real payment data: {e}")
            return pd.DataFrame()
    
    def generate_synthetic_performance_data(self, n_samples=1000):
        """Generate synthetic student performance data for training"""
        np.random.seed(42)
        
        data = []
        for _ in range(n_samples):
            # Generate correlated features
            attendance_rate = np.random.beta(2, 1)  # Skewed towards higher attendance
            previous_grade = np.random.normal(75, 15)
            previous_grade = np.clip(previous_grade, 0, 100)
            
            # Assignment completion correlated with attendance
            assignment_completion = attendance_rate * 0.8 + np.random.normal(0, 0.1)
            assignment_completion = np.clip(assignment_completion, 0, 1)
            
            # Performance category based on weighted features
            performance_score = (
                attendance_rate * 0.4 + 
                (previous_grade / 100) * 0.4 + 
                assignment_completion * 0.2 +
                np.random.normal(0, 0.1)
            )
            
            if performance_score >= 0.8:
                performance_category = 2  # Excellent
            elif performance_score >= 0.6:
                performance_category = 1  # Good
            else:
                performance_category = 0  # Poor
            
            data.append({
                'attendance_rate': attendance_rate,
                'previous_grade': previous_grade,
                'assignment_completion': assignment_completion,
                'performance_category': performance_category
            })
        
        return pd.DataFrame(data)
    
    def generate_synthetic_payment_data(self, n_samples=800):
        """Generate synthetic payment delay data for training"""
        np.random.seed(42)
        
        data = []
        for _ in range(n_samples):
            # Generate features
            amount = np.random.uniform(1000, 10000)
            days_until_due = np.random.randint(1, 60)
            previous_delays = np.random.poisson(2)  # Average 2 previous delays
            parent_income_bracket = np.random.choice([1, 2, 3], p=[0.3, 0.5, 0.2])  # Low, Medium, High
            
            # Calculate delay based on features
            delay_factor = (
                (amount / 5000) * 0.3 +  # Higher amount = more delay
                (30 - days_until_due) / 30 * 0.2 +  # Less time = more delay
                previous_delays * 0.3 +  # More previous delays = more delay
                (4 - parent_income_bracket) / 3 * 0.2  # Lower income = more delay
            )
            
            # Add noise and convert to days
            delay_days = max(0, delay_factor * 20 + np.random.normal(0, 5))
            
            data.append({
                'amount': amount,
                'days_until_due': days_until_due,
                'previous_delays': previous_delays,
                'parent_income_bracket': parent_income_bracket,
                'delay_days': delay_days
            })
        
        return pd.DataFrame(data)