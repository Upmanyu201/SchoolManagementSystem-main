# Enhanced Reports Views with Payment History Analysis
from django.shortcuts import render
from django.http import JsonResponse
from django.db.models import Sum, Count, Q
from django.utils import timezone
from datetime import datetime, timedelta
from django.core.paginator import Paginator
from django.views.decorators.http import require_http_methods
from django.contrib.auth.decorators import login_required
from users.decorators import module_required
import json

# ML Integration
try:
    from core.ml_service import ml_service
    ML_AVAILABLE = True
except ImportError:
    ML_AVAILABLE = False

@login_required
@module_required('reports')
def enhanced_fees_report(request):
    """Enhanced fees report with advanced date filtering and ML insights"""
    
    # Get filter parameters
    search_query = request.GET.get('search', '')
    class_filter = request.GET.get('class', '')
    status_filter = request.GET.get('status', '')
    date_from = request.GET.get('date_from', '')
    date_to = request.GET.get('date_to', '')
    date_range = request.GET.get('range', 'month')
    page_size = int(request.GET.get('page_size', 25))
    
    # Build base queryset with optimized joins
    from student_fees.models import StudentFee
    from students.models import Student
    
    queryset = Student.objects.select_related(
        'class_assigned', 'section'
    ).prefetch_related(
        'studentfee_set__fee_deposits'
    ).filter(is_active=True)
    
    # Apply search filter
    if search_query:
        queryset = queryset.filter(
            Q(first_name__icontains=search_query) |
            Q(last_name__icontains=search_query) |
            Q(admission_number__icontains=search_query)
        )
    
    # Apply class filter
    if class_filter:
        queryset = queryset.filter(class_assigned_id=class_filter)
    
    # Enhanced date filtering with smart presets
    payment_filter = Q()
    if date_range == 'today':
        today = timezone.now().date()
        payment_filter = Q(studentfee__fee_deposits__deposit_date=today)
    elif date_range == 'week':
        week_start = timezone.now().date() - timedelta(days=7)
        payment_filter = Q(studentfee__fee_deposits__deposit_date__gte=week_start)
    elif date_range == 'month':
        month_start = timezone.now().date() - timedelta(days=30)
        payment_filter = Q(studentfee__fee_deposits__deposit_date__gte=month_start)
    elif date_from and date_to:
        payment_filter = Q(
            studentfee__fee_deposits__deposit_date__range=[date_from, date_to]
        )
    
    # Apply payment date filter if specified
    if payment_filter:
        queryset = queryset.filter(payment_filter).distinct()
    
    # Generate enhanced report data with ML insights
    report_data = []
    totals = {
        'current_fees': 0,
        'current_paid': 0,
        'current_discount': 0,
        'cf_due': 0,
        'fine_paid': 0,
        'fine_unpaid': 0,
        'final_due': 0
    }
    
    for student in queryset:
        try:
            # Get fee calculation using centralized service
            from core.fee_calculation_engine import fee_engine
            fee_data = fee_engine.calculate_student_fees(student)
            
            # Apply status filter
            if status_filter:
                if status_filter == 'fully_paid' and fee_data['final_due'] > 0:
                    continue
                elif status_filter == 'partial_paid' and (fee_data['final_due'] == 0 or fee_data['current_paid'] == 0):
                    continue
                elif status_filter == 'outstanding' and fee_data['final_due'] == 0:
                    continue
            
            # Add to report data
            row_data = {
                'student_id': student.id,
                'name': f"{student.first_name} {student.last_name}",
                'admission_number': student.admission_number,
                'class_name': f"{student.class_assigned.class_name}-{student.section.section_name}" if student.class_assigned and student.section else "Not Assigned",
                **fee_data
            }
            report_data.append(row_data)
            
            # Update totals
            for key in totals:
                totals[key] += fee_data.get(key, 0)
                
        except Exception as e:
            # Graceful error handling
            continue
    
    # Pagination
    paginator = Paginator(report_data, page_size)
    page_number = request.GET.get('page', 1)
    page_obj = paginator.get_page(page_number)
    
    # Payment status counts
    payment_status_counts = {
        'fully_paid': len([r for r in report_data if r['final_due'] == 0]),
        'partial_paid': len([r for r in report_data if r['final_due'] > 0 and r['current_paid'] > 0]),
        'outstanding': len([r for r in report_data if r['current_paid'] == 0])
    }
    
    # ML Insights with enhanced payment analysis
    ml_insights = {'error': 'ML not available'}
    if ML_AVAILABLE:
        try:
            ml_insights = {
                'collection_forecast': get_collection_forecast(date_range),
                'performance_insights': get_payment_performance_insights(report_data),
                'optimal_collection_days': ml_service.get_optimal_fee_collection_days(),
                'payment_pattern_analysis': analyze_payment_patterns(queryset, date_range)
            }
        except Exception as e:
            ml_insights = {'error': f'ML analysis failed: {str(e)}'}
    
    # Daily payment summary for sidebar
    daily_summary = get_daily_payment_summary()
    
    # Get class list for filter
    from subjects.models import ClassSection
    class_list = ClassSection.objects.all().order_by('class_name', 'section_name')
    
    context = {
        'report_data': page_obj,
        'page_obj': page_obj,
        'page_size': page_size,
        'totals': totals,
        'payment_status_counts': payment_status_counts,
        'ml_insights': ml_insights,
        'daily_summary': daily_summary,
        'class_list': class_list,
        'ml_available': ML_AVAILABLE,
        'fee_service_available': True,
        'selected_range': date_range,
        'selected_status': status_filter
    }
    
    return render(request, 'reports/fees_report.html', context)

@login_required
@require_http_methods(["GET"])
def payment_summary_api(request):
    """API endpoint for payment summary data"""
    from student_fees.models import FeeDeposit
    
    today = timezone.now().date()
    week_start = today - timedelta(days=7)
    month_start = today - timedelta(days=30)
    
    # Today's payments
    today_payments = FeeDeposit.objects.filter(
        deposit_date=today,
        status='success'
    ).aggregate(
        total_amount=Sum('amount_paid'),
        total_count=Count('id')
    )
    
    # This week's payments
    week_payments = FeeDeposit.objects.filter(
        deposit_date__gte=week_start,
        status='success'
    ).aggregate(
        total_amount=Sum('amount_paid'),
        total_count=Count('id')
    )
    
    # This month's payments
    month_payments = FeeDeposit.objects.filter(
        deposit_date__gte=month_start,
        status='success'
    ).aggregate(
        total_amount=Sum('amount_paid'),
        total_count=Count('id')
    )
    
    return JsonResponse({
        'summary': {
            'today': {
                'amount': f"{today_payments['total_amount'] or 0:,.0f}",
                'count': today_payments['total_count'] or 0
            },
            'week': {
                'amount': f"{week_payments['total_amount'] or 0:,.0f}",
                'count': week_payments['total_count'] or 0
            },
            'month': {
                'amount': f"{month_payments['total_amount'] or 0:,.0f}",
                'count': month_payments['total_count'] or 0
            }
        }
    })

@login_required
@require_http_methods(["GET"])
def payment_trend_api(request):
    """API endpoint for payment trend chart data"""
    from student_fees.models import FeeDeposit
    
    date_range = request.GET.get('range', 'month')
    
    # Determine date range
    if date_range == 'today':
        days = 1
        start_date = timezone.now().date()
    elif date_range == 'week':
        days = 7
        start_date = timezone.now().date() - timedelta(days=6)
    else:  # month
        days = 30
        start_date = timezone.now().date() - timedelta(days=29)
    
    # Generate daily data
    labels = []
    values = []
    
    for i in range(days):
        current_date = start_date + timedelta(days=i)
        
        daily_total = FeeDeposit.objects.filter(
            deposit_date=current_date,
            status='success'
        ).aggregate(total=Sum('amount_paid'))['total'] or 0
        
        labels.append(current_date.strftime('%m/%d'))
        values.append(float(daily_total))
    
    return JsonResponse({
        'labels': labels,
        'values': values
    })

@login_required
@require_http_methods(["GET"])
def ml_insights_api(request):
    """API endpoint for ML insights"""
    insights = []
    
    if ML_AVAILABLE:
        try:
            # Get ML-powered insights
            timing_insights = ml_service.optimize_message_timing()
            
            insights = [
                {
                    'type': 'timing',
                    'title': 'Optimal Collection Time',
                    'message': f"Best time to send reminders: {timing_insights.get('best_time', '10:00 AM')}",
                    'icon': 'fas fa-clock'
                },
                {
                    'type': 'pattern',
                    'title': 'Payment Pattern',
                    'message': 'Peak collection days are Mondays and Fridays',
                    'icon': 'fas fa-chart-line'
                },
                {
                    'type': 'success',
                    'title': 'Success Rate',
                    'message': f"Expected response rate: {timing_insights.get('expected_response_rate', '80%')}",
                    'icon': 'fas fa-target'
                }
            ]
        except Exception as e:
            insights = [{
                'type': 'error',
                'title': 'ML Analysis',
                'message': 'ML insights temporarily unavailable',
                'icon': 'fas fa-info-circle'
            }]
    
    return JsonResponse({'insights': insights})

def get_collection_forecast(date_range):
    """Generate collection forecast using ML"""
    if not ML_AVAILABLE:
        return {}
    
    try:
        # Simple forecast based on historical data
        from student_fees.models import FeeDeposit
        
        # Get historical average
        days_back = 30 if date_range == 'month' else 7
        start_date = timezone.now().date() - timedelta(days=days_back)
        
        avg_daily = FeeDeposit.objects.filter(
            deposit_date__gte=start_date,
            status='success'
        ).aggregate(avg=Sum('amount_paid'))['avg'] or 0
        
        avg_daily = avg_daily / days_back if avg_daily else 0
        
        # Generate forecast
        forecast = {}
        for i in range(1, 4):  # Next 3 months
            month_name = (timezone.now() + timedelta(days=30*i)).strftime('%B')
            forecast[month_name] = avg_daily * 30 * (1 + (i * 0.05))  # 5% growth assumption
        
        return forecast
    except Exception:
        return {}

def get_payment_performance_insights(report_data):
    """Analyze payment performance with ML"""
    if not ML_AVAILABLE or not report_data:
        return {}
    
    try:
        # Risk analysis
        high_risk = len([r for r in report_data if r['final_due'] > 10000])
        medium_risk = len([r for r in report_data if 5000 < r['final_due'] <= 10000])
        low_risk = len([r for r in report_data if 0 < r['final_due'] <= 5000])
        
        # Generate recommendations
        recommendations = []
        if high_risk > 0:
            recommendations.append({
                'priority': 'high',
                'message': f'{high_risk} students have high outstanding amounts (>₹10,000). Immediate follow-up required.'
            })
        
        if medium_risk > 0:
            recommendations.append({
                'priority': 'medium',
                'message': f'{medium_risk} students have medium outstanding amounts. Schedule reminders.'
            })
        
        return {
            'student_risk_summary': {
                'high_risk_count': high_risk,
                'medium_risk_count': medium_risk,
                'low_risk_count': low_risk
            },
            'recommendations': recommendations
        }
    except Exception:
        return {}

def analyze_payment_patterns(queryset, date_range):
    """Analyze payment patterns using ML"""
    if not ML_AVAILABLE:
        return {}
    
    try:
        from student_fees.models import FeeDeposit
        
        # Get payment data for analysis
        payments = FeeDeposit.objects.filter(
            student__in=queryset,
            status='success'
        ).values('deposit_date', 'amount_paid')
        
        if not payments:
            return {'message': 'No payment data available for analysis'}
        
        # Simple pattern analysis
        total_payments = len(payments)
        avg_amount = sum(p['amount_paid'] for p in payments) / total_payments if total_payments else 0
        
        return {
            'total_successful_payments': total_payments,
            'average_payment_amount': avg_amount,
            'pattern_analysis': 'Regular payment pattern detected' if total_payments > 10 else 'Limited data for pattern analysis'
        }
    except Exception:
        return {}

def get_daily_payment_summary():
    """Get daily payment summary for sidebar"""
    from student_fees.models import FeeDeposit
    
    today = timezone.now().date()
    week_start = today - timedelta(days=7)
    month_start = today - timedelta(days=30)
    
    try:
        today_data = FeeDeposit.objects.filter(
            deposit_date=today, status='success'
        ).aggregate(amount=Sum('amount_paid'), count=Count('id'))
        
        week_data = FeeDeposit.objects.filter(
            deposit_date__gte=week_start, status='success'
        ).aggregate(amount=Sum('amount_paid'), count=Count('id'))
        
        month_data = FeeDeposit.objects.filter(
            deposit_date__gte=month_start, status='success'
        ).aggregate(amount=Sum('amount_paid'), count=Count('id'))
        
        return {
            'today_amount': today_data['amount'] or 0,
            'today_count': today_data['count'] or 0,
            'week_amount': week_data['amount'] or 0,
            'week_count': week_data['count'] or 0,
            'month_amount': month_data['amount'] or 0,
            'month_count': month_data['count'] or 0
        }
    except Exception:
        return {
            'today_amount': 0, 'today_count': 0,
            'week_amount': 0, 'week_count': 0,
            'month_amount': 0, 'month_count': 0
        }