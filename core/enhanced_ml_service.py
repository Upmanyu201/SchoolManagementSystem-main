# Enhanced ML Service for Payment History Analysis
import logging
from datetime import datetime, timedelta
from django.db.models import Count, Sum, Avg
from django.utils import timezone

logger = logging.getLogger(__name__)

class EnhancedMLService:
    """Enhanced ML service with payment history analysis"""
    
    def analyze_payment_day_patterns(self):
        """Analyze actual payment patterns from database"""
        try:
            from student_fees.models import FeeDeposit
            
            # Get payment data from last 90 days
            end_date = datetime.now().date()
            start_date = end_date - timedelta(days=90)
            
            # Analyze payment frequency by day of month
            payment_days = FeeDeposit.objects.filter(
                deposit_date__range=[start_date, end_date],
                status='success'
            ).extra(
                select={'day': 'EXTRACT(day FROM deposit_date)'}
            ).values('day').annotate(
                payment_count=Count('id')
            ).order_by('-payment_count')[:10]
            
            if payment_days:
                optimal_days = [int(p['day']) for p in payment_days]
                return optimal_days[:5]  # Top 5 days
            else:
                return [1, 5, 10, 15, 25]  # Default fallback
                
        except Exception as e:
            logger.error(f"Payment pattern analysis error: {e}")
            return [1, 5, 10, 15, 25]
    
    def get_payment_success_forecast(self, days_ahead=30):
        """Forecast payment success rates for upcoming days"""
        try:
            from student_fees.models import FeeDeposit
            
            # Analyze historical success rates
            end_date = datetime.now().date()
            start_date = end_date - timedelta(days=90)
            
            total_attempts = FeeDeposit.objects.filter(
                deposit_date__range=[start_date, end_date]
            ).count()
            
            successful_payments = FeeDeposit.objects.filter(
                deposit_date__range=[start_date, end_date],
                status='success'
            ).count()
            
            success_rate = (successful_payments / total_attempts) if total_attempts > 0 else 0.85
            
            # Generate forecast
            forecast = {
                'current_success_rate': round(success_rate, 2),
                'predicted_collections': [],
                'optimal_reminder_days': [3, 7, 14]  # Days before due date
            }
            
            # Predict next 30 days
            for i in range(1, days_ahead + 1):
                future_date = end_date + timedelta(days=i)
                predicted_amount = self.predict_daily_collection(future_date, success_rate)
                
                forecast['predicted_collections'].append({
                    'date': future_date.strftime('%Y-%m-%d'),
                    'predicted_amount': predicted_amount,
                    'confidence': min(success_rate + 0.1, 0.95)
                })
            
            return forecast
            
        except Exception as e:
            logger.error(f"Payment forecast error: {e}")
            return {
                'current_success_rate': 0.85,
                'predicted_collections': [],
                'optimal_reminder_days': [3, 7, 14]
            }
    
    def predict_daily_collection(self, target_date, base_success_rate):
        """Predict collection amount for a specific date"""
        try:
            from student_fees.models import FeeDeposit
            
            # Get historical average for same day of week
            weekday = target_date.weekday()
            
            avg_amount = FeeDeposit.objects.filter(
                deposit_date__week_day=weekday + 2,  # Django week_day is 1-7, Monday=2
                status='success'
            ).aggregate(avg_amount=Avg('amount_paid'))['avg_amount'] or 5000
            
            # Apply success rate and seasonal adjustments
            predicted = avg_amount * base_success_rate
            
            # Adjust for month-end patterns (higher collections)
            if target_date.day >= 25:
                predicted *= 1.2
            elif target_date.day <= 5:
                predicted *= 1.1
            
            return round(predicted, 2)
            
        except Exception as e:
            logger.error(f"Daily collection prediction error: {e}")
            return 5000.0
    
    def analyze_successful_payment_patterns(self, date_range='month'):
        """Analyze patterns in successful payments"""
        try:
            from student_fees.models import FeeDeposit
            
            # Determine date range
            end_date = timezone.now().date()
            if date_range == 'today':
                start_date = end_date
            elif date_range == 'week':
                start_date = end_date - timedelta(days=7)
            elif date_range == 'month':
                start_date = end_date - timedelta(days=30)
            else:
                start_date = end_date - timedelta(days=90)
            
            # Get successful payments
            successful_payments = FeeDeposit.objects.filter(
                deposit_date__range=[start_date, end_date],
                status='success'
            )
            
            # Analyze patterns
            total_amount = successful_payments.aggregate(
                total=Sum('amount_paid')
            )['total'] or 0
            
            total_count = successful_payments.count()
            
            # Day-wise analysis
            day_wise = successful_payments.extra(
                select={'weekday': 'EXTRACT(dow FROM deposit_date)'}
            ).values('weekday').annotate(
                count=Count('id'),
                amount=Sum('amount_paid')
            ).order_by('weekday')
            
            # Time-wise analysis (hour of day)
            hour_wise = successful_payments.extra(
                select={'hour': 'EXTRACT(hour FROM created_at)'}
            ).values('hour').annotate(
                count=Count('id')
            ).order_by('hour')
            
            # Payment method analysis
            method_wise = successful_payments.values('payment_method').annotate(
                count=Count('id'),
                amount=Sum('amount_paid')
            ).order_by('-amount')
            
            return {
                'total_successful_amount': total_amount,
                'total_successful_count': total_count,
                'average_payment': total_amount / total_count if total_count > 0 else 0,
                'day_wise_pattern': list(day_wise),
                'hour_wise_pattern': list(hour_wise),
                'method_wise_pattern': list(method_wise),
                'success_insights': self.generate_success_insights(day_wise, hour_wise)
            }
            
        except Exception as e:
            logger.error(f"Successful payment pattern analysis error: {e}")
            return {
                'total_successful_amount': 0,
                'total_successful_count': 0,
                'average_payment': 0,
                'success_insights': ['Analysis temporarily unavailable']
            }
    
    def generate_success_insights(self, day_wise, hour_wise):
        """Generate insights from successful payment patterns"""
        insights = []
        
        try:
            # Find best day
            if day_wise:
                best_day = max(day_wise, key=lambda x: x['amount'])
                day_names = ['Sunday', 'Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday']
                insights.append(f"Highest collections on {day_names[best_day['weekday']]}")
            
            # Find best hour
            if hour_wise:
                best_hour = max(hour_wise, key=lambda x: x['count'])
                insights.append(f"Peak payment time: {best_hour['hour']}:00")
            
            # General insights
            insights.append("Send reminders 2-3 days before due dates for better success rates")
            
        except Exception as e:
            logger.error(f"Insight generation error: {e}")
            insights = ["Payment pattern analysis available"]
        
        return insights

# Global enhanced ML service instance
enhanced_ml_service = EnhancedMLService()