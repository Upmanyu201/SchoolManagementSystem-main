from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse, HttpResponse
from django.contrib import messages
from django.views.decorators.csrf import csrf_protect
from django.views.decorators.http import require_POST
from django.core.exceptions import ValidationError
from django.utils.html import escape
from django.utils import timezone
from django.db.models import Sum
from datetime import datetime, timedelta
from django.db.models import Sum, Count, Q, Avg, F, Case, When, Value
from django.core.paginator import Paginator
from django.core.cache import cache
from django.views.decorators.cache import cache_page
from django.views.decorators.vary import vary_on_headers
from decimal import Decimal
import json
import hashlib
from typing import Dict, List, Optional, Any
import logging

logger = logging.getLogger(__name__)

from student_fees.models import FeeDeposit
from fines.models import Fine, FineStudent
from students.models import Student
from users.decorators import module_required
from subjects.models import ClassSection
from fees.models import FeesType
from transport.models import TransportAssignment
from messaging.cross_module_logger import CrossModuleMessageLogger

# Centralized fee service integration
try:
    from core.fee_management import fee_service
    FEE_SERVICE_AVAILABLE = True
except ImportError:
    fee_service = None
    FEE_SERVICE_AVAILABLE = False

# Export utilities removed

# Temporary import handling for services
try:
    from .ml_analytics import ml_analytics
except ImportError:
    ml_analytics = None


def _sanitize_report_filters(get_params: Dict[str, Any]) -> Dict[str, Any]:
    """Sanitize and validate report filter inputs"""
    allowed_keys = {
        'start_date', 'end_date', 'class', 'search', 'payment_mode', 
        'page_size', 'page', 'student_class', 'status'
    }
    
    sanitized = {}
    for key, value in get_params.items():
        if key in allowed_keys and value:
            # Basic sanitization using Django's escape function
            clean_value = escape(str(value).strip()[:100])  # Limit length and escape HTML
            
            # Additional validation for specific fields
            if key in ['start_date', 'end_date']:
                try:
                    datetime.strptime(clean_value, '%Y-%m-%d')
                except ValueError:
                    continue  # Skip invalid dates
            elif key == 'payment_mode':
                if clean_value not in ['Cash', 'Cheque', 'Online', 'UPI']:
                    continue  # Skip invalid payment modes
            elif key in ['page_size', 'page', 'class', 'student_class']:
                try:
                    int(clean_value)
                except ValueError:
                    continue  # Skip invalid numbers
            
            if clean_value:
                sanitized[key] = clean_value
    
    return sanitized

def _validate_numeric_id(id_value: str, field_name: str) -> int:
    """Validate and convert ID to integer"""
    try:
        id_int = int(id_value)
        if id_int <= 0:
            raise ValidationError(f"Invalid {field_name}")
        return id_int
    except (ValueError, TypeError):
        raise ValidationError(f"Invalid {field_name} format")




@login_required
@module_required('reports', 'view')
@cache_page(60 * 5)  # Cache for 5 minutes
@vary_on_headers('User-Agent')
def reports_dashboard(request):
    """Modern analytics dashboard with real-time KPIs"""
    
    # Generate cache key based on user and current hour
    cache_key = f"dashboard_data_{request.user.id}_{timezone.now().hour}"
    dashboard_data = cache.get(cache_key)
    
    if not dashboard_data:
        # Secure aggregations with proper filtering
        total_payments = FeeDeposit.objects.filter(
            student__isnull=False
        ).count()
        
        payment_stats = FeeDeposit.objects.aggregate(
            total_amount=Sum('paid_amount'),
            avg_amount=Avg('paid_amount')
        )
        
        fine_stats = Fine.objects.aggregate(
            total_fines=Count('id'),
            total_amount=Sum('amount')
        )
        
        # Recent activities with proper relations
        recent_payments = FeeDeposit.objects.select_related(
            'student', 'fees_type'
        ).order_by('-deposit_date')[:10]
        
        recent_fines = Fine.objects.select_related(
            'fine_type'
        ).order_by('-applied_date')[:10]
        
        # Calculate collection rate
        collection_rate = 0
        if total_payments > 0:
            paid_count = FeeDeposit.objects.filter(
                paid_amount__gt=0
            ).count()
            collection_rate = (paid_count / total_payments) * 100
        
        dashboard_data = {
            'total_payments': total_payments,
            'total_payment_amount': payment_stats['total_amount'] or 0,
            'avg_payment_amount': payment_stats['avg_amount'] or 0,
            'total_fines': fine_stats['total_fines'] or 0,
            'total_fine_amount': fine_stats['total_amount'] or 0,
            'collection_rate': round(collection_rate, 2),
            'recent_payments': recent_payments,
            'recent_fines': recent_fines,
            'last_updated': timezone.now().isoformat()
        }
        
        # Cache for 5 minutes
        cache.set(cache_key, dashboard_data, 300)
    
    return render(request, 'reports/dashboard.html', dashboard_data)

@login_required
@module_required('reports', 'view')
def payment_reports(request):
    """Secure payment reports with advanced filtering"""
    
    # Sanitize and validate inputs
    filters = _sanitize_report_filters(request.GET)
    
    # Build secure queryset
    payments = FeeDeposit.objects.select_related(
        'student__class_section', 'fees_type'
    ).filter(student__isnull=False)
    
    # Apply validated filters
    if filters.get('start_date'):
        try:
            start_date = datetime.strptime(filters['start_date'], '%Y-%m-%d').date()
            payments = payments.filter(deposit_date__gte=start_date)
        except ValueError:
            messages.error(request, 'Please enter a valid start date in the correct format (YYYY-MM-DD).')
    
    if filters.get('end_date'):
        try:
            end_date = datetime.strptime(filters['end_date'], '%Y-%m-%d').date()
            payments = payments.filter(deposit_date__lte=end_date)
        except ValueError:
            messages.error(request, 'Please enter a valid end date in the correct format (YYYY-MM-DD).')
    
    if filters.get('student_class'):
        try:
            class_id = int(filters['student_class'])
            payments = payments.filter(student__class_section_id=class_id)
        except (ValueError, TypeError):
            messages.error(request, 'Invalid class selection')
    
    if filters.get('payment_mode') and filters['payment_mode'] in ['Cash', 'Cheque', 'Online', 'UPI']:
        payments = payments.filter(payment_mode=filters['payment_mode'])
    
    # Export functionality removed
    
    # Pagination for web view
    paginator = Paginator(payments.order_by('-deposit_date'), 25)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    # Enhanced summary statistics with ML insights
    summary_stats = payments.aggregate(
        total_amount=Sum('amount'),
        total_paid=Sum('paid_amount'),
        avg_amount=Avg('paid_amount'),
        payment_count=Count('id')
    )
    
    summary = {
        'total_payments': summary_stats['payment_count'] or 0,
        'total_amount': summary_stats['total_amount'] or 0,
        'total_paid': summary_stats['total_paid'] or 0,
        'avg_amount': summary_stats['avg_amount'] or 0,
        'pending_amount': (summary_stats['total_amount'] or 0) - (summary_stats['total_paid'] or 0),
        'collection_rate': ((summary_stats['total_paid'] or 0) / (summary_stats['total_amount'] or 1)) * 100
    }
    
    # Get ML insights
    ml_insights = {'recommendations': []}
    if ml_analytics:
        try:
            ml_insights = ml_analytics.generate_performance_insights()
        except Exception:
            ml_insights = {'recommendations': []}
    
    context = {
        'page_obj': page_obj,
        'summary': summary,
        'ml_insights': ml_insights,
        'filters': filters,
        'payment_modes': ['Cash', 'Cheque', 'Online', 'UPI'],
        'classes': ClassSection.objects.all().order_by('class_name'),
    }
    
    return render(request, 'reports/payment_reports.html', context)

@login_required
@module_required('reports', 'view')
def fine_reports(request):
    """Enhanced fine reports with filtering and export"""
    try:
        # Get and sanitize filter parameters
        filters = _sanitize_report_filters(request.GET)
        start_date = filters.get('start_date')
        end_date = filters.get('end_date')
        fine_type = filters.get('fine_type')
        status = filters.get('status')
        export_type = request.GET.get('export')
        
        # Validate export type
        if export_type and export_type not in ['excel', 'csv', 'pdf']:
            messages.error(request, "Invalid export format selected.")
            export_type = None
        
        # Build queryset
        fines = Fine.objects.select_related('fine_type', 'class_group').prefetch_related('fine_students__student').all()
        
        if start_date:
            fines = fines.filter(applied_date__date__gte=start_date)
        if end_date:
            fines = fines.filter(applied_date__date__lte=end_date)
        if fine_type:
            fines = fines.filter(fine_type__name=fine_type)
        if status == 'paid':
            fines = fines.filter(fine_students__is_paid=True).distinct()
        elif status == 'unpaid':
            fines = fines.filter(fine_students__is_paid=False).distinct()
        
        # Export functionality removed
        
        # Pagination for web view
        paginator = Paginator(fines.order_by('-applied_date'), 25)
        page_number = request.GET.get('page')
        page_obj = paginator.get_page(page_number)
        
        # Summary statistics
        total_fine_amount = fines.aggregate(Sum('amount'))['amount__sum'] or 0
        paid_fines = FineStudent.objects.filter(fine__in=fines, is_paid=True).count()
        unpaid_fines = FineStudent.objects.filter(fine__in=fines, is_paid=False).count()
        
        summary = {
            'total_fines': fines.count(),
            'total_amount': total_fine_amount,
            'paid_fines': paid_fines,
            'unpaid_fines': unpaid_fines,
            'collection_rate': (paid_fines / (paid_fines + unpaid_fines) * 100) if (paid_fines + unpaid_fines) > 0 else 0,
        }
        
        context = {
            'page_obj': page_obj,
            'summary': summary,
            'filters': {
                'start_date': start_date,
                'end_date': end_date,
                'fine_type': fine_type,
                'status': status,
            },
            'fine_types': Fine.objects.values_list('fine_type__name', flat=True).distinct(),
        }
    
        return render(request, 'reports/fine_reports.html', context)
    except Exception as e:
        logger.error(f"Error in fine_reports for user {request.user.id}: {str(e)}")
        messages.error(request, "We're having trouble loading the fine reports. Please try again.")
        return render(request, 'reports/fine_reports.html', {'page_obj': None, 'summary': {}, 'filters': {}, 'fine_types': []})

@login_required
@csrf_protect
@module_required('reports', 'view')
def summary_report(request):
    """Generate comprehensive summary report"""
    try:
        if request.method == 'POST':
            # Sanitize and validate inputs
            start_date = escape(request.POST.get('start_date', '').strip())
            end_date = escape(request.POST.get('end_date', '').strip())
            export_type = request.POST.get('export_type', 'excel')
            
            # Validate export type
            if export_type not in ['excel', 'csv', 'pdf']:
                export_type = 'excel'
            
            # Validate dates
            if start_date and end_date:
                try:
                    datetime.strptime(start_date, '%Y-%m-%d')
                    datetime.strptime(end_date, '%Y-%m-%d')
                    messages.info(request, 'Great! Your summary report is ready to view below.')
                except ValueError:
                    messages.error(request, 'Please enter valid dates in YYYY-MM-DD format.')
            else:
                messages.error(request, 'Please select both start and end dates to generate your report.')
        
        return render(request, 'reports/summary_report.html')
    except Exception as e:
        logger.error(f"Error in summary_report for user {request.user.id}: {str(e)}")
        messages.error(request, "We're having trouble generating the summary report. Please try again.")
        return render(request, 'reports/summary_report.html')

@login_required
@module_required('reports', 'view')
def fees_report(request):
    """Comprehensive fees report with proper student-wise aggregation"""
    from decimal import Decimal
    from django.db.models import Sum, Q
    from subjects.models import ClassSection
    from fees.models import FeesType
    from fines.models import FineStudent
    from transport.models import TransportAssignment
    from django.core.paginator import Paginator
    
    """Modern comprehensive fees report with ML insights"""
    
    # Sanitize and validate inputs
    filters = _sanitize_report_filters(request.GET)
    
    try:
        page_size = min(int(filters.get('page_size', 25)), 100)  # Max 100 per page
    except (ValueError, TypeError):
        page_size = 25
    
    # Build secure student query
    students_query = Q()
    if filters.get('class'):
        try:
            class_id = int(filters['class'])
            students_query &= Q(class_section_id=class_id)
        except (ValueError, TypeError):
            messages.error(request, 'Please select a valid class from the dropdown.')
    
    if filters.get('search'):
        search_term = filters['search'][:50]  # Limit search length
        students_query &= (
            Q(first_name__icontains=search_term) | 
            Q(last_name__icontains=search_term) |
            Q(admission_number__icontains=search_term)
        )
    
    students = Student.objects.all_statuses().filter(students_query).select_related(
        'class_section'
    ).order_by('class_section__class_name', 'first_name')
    
    # Export functionality removed
    
    # Prepare comprehensive report data
    report_data = []
    totals = {
        'current_fees': Decimal('0'),
        'current_paid': Decimal('0'), 
        'current_discount': Decimal('0'),
        'cf_due': Decimal('0'),
        'cf_paid': Decimal('0'),
        'cf_discount': Decimal('0'),
        'fine_unpaid': Decimal('0'),
        'fine_paid': Decimal('0'),
        'final_due': Decimal('0')
    }
    
    # Payment status counters
    payment_status_counts = {
        'fully_paid': 0,
        'partial_paid': 0,
        'outstanding': 0
    }
    
    for student in students:
        # Get applicable current session fees - Fix class name matching
        class_name = student.class_section.class_name if student.class_section else ''
        class_display = student.class_section.display_name if student.class_section else ''
        
        applicable_fees = FeesType.objects.filter(
            Q(class_name__isnull=True) | 
            Q(class_name__iexact=class_name) |
            Q(class_name__iexact=class_display)
        ).exclude(fee_group__group_type="Transport")
        
        # Add transport fees if assigned
        transport_assignment = TransportAssignment.objects.filter(student=student).first()
        if transport_assignment and transport_assignment.stoppage:
            transport_fees = FeesType.objects.filter(
                fee_group__group_type="Transport",
                related_stoppage=transport_assignment.stoppage
            )
            applicable_fees = list(applicable_fees) + list(transport_fees)
        
        # Calculate current session fees
        current_fees = sum(fee.amount for fee in applicable_fees)
        
        # Carry Forward amounts
        cf_due_original = student.due_amount or Decimal('0')
        
        # Total fees = Current session fees + Carry forward due
        total_fees = current_fees + cf_due_original
        
        # Get ALL payments (fees + CF, excluding fines)
        fee_payments = FeeDeposit.objects.filter(
            student=student
        ).exclude(note__icontains="Fine Payment")
        
        total_fee_paid = fee_payments.aggregate(Sum('paid_amount'))['paid_amount__sum'] or Decimal('0')
        total_fee_discount = fee_payments.aggregate(Sum('discount'))['discount__sum'] or Decimal('0')
        
        # Separate CF payments for display
        cf_payments = fee_payments.filter(
            Q(note__icontains="Carry Forward") | Q(payment_source="carry_forward")
        )
        cf_paid = cf_payments.aggregate(Sum('paid_amount'))['paid_amount__sum'] or Decimal('0')
        cf_discount = cf_payments.aggregate(Sum('discount'))['discount__sum'] or Decimal('0')
        
        # Current session payments only - FIXED: Separate current from CF
        current_session_payments = fee_payments.exclude(
            Q(note__icontains="Carry Forward") | Q(payment_source="carry_forward")
        )
        current_paid = current_session_payments.aggregate(Sum('paid_amount'))['paid_amount__sum'] or Decimal('0')
        current_discount = current_session_payments.aggregate(Sum('discount'))['discount__sum'] or Decimal('0')
        
        # Remaining CF due
        cf_due = max(cf_due_original - cf_paid - cf_discount, Decimal('0'))
        
        # Fine amounts
        unpaid_fines = FineStudent.objects.filter(
            student=student, 
            is_paid=False
        ).select_related('fine')
        
        paid_fines = FineStudent.objects.filter(
            student=student, 
            is_paid=True
        ).select_related('fine')
        
        fine_unpaid = sum(fs.fine.amount for fs in unpaid_fines)
        fine_paid = sum(fs.fine.amount for fs in paid_fines)
        
        # Calculate final due: Total fees - Total paid - Total discount + Unpaid fines
        # Match student_fee_preview calculation logic
        final_due = max(total_fees - total_fee_paid - total_fee_discount + fine_unpaid, Decimal('0'))
        
        # Determine payment status
        payment_status = 'outstanding'  # Default
        if final_due <= 0:
            payment_status = 'fully_paid'
        elif current_paid > 0 or cf_paid > 0:
            payment_status = 'partial_paid'
        
        # Count payment statuses for all students (not just those with fee activity)
        payment_status_counts[payment_status] += 1
        
        class_section = f"{student.class_section.class_name} - {student.class_section.section_name}" if student.class_section else 'Unknown'
        
        row = {
            'student_id': student.id,
            'name': student.get_full_display_name(),
            'admission_number': student.admission_number,
            'class_name': class_section,
            'current_fees': total_fees,  # Show total fees (current + CF)
            'current_paid': current_paid,  # Show ONLY current session payments (NOT CF)
            'current_discount': total_fee_discount,
            'cf_due': cf_due,
            'cf_paid': cf_paid,
            'cf_discount': cf_discount,
            'fine_unpaid': fine_unpaid,
            'fine_paid': fine_paid,
            'final_due': max(final_due, Decimal('0')),
            'payment_status': payment_status,
        }
        
        # Apply payment status filter if requested
        status_filter = filters.get('status')
        include_row = False
        
        if not status_filter:
            # Show all students with fee activity
            include_row = (current_fees > 0 or current_paid > 0 or cf_due > 0 or 
                          fine_unpaid > 0 or fine_paid > 0)
        elif status_filter == 'fully_paid':
            # Show all students with no dues (including those with no fee activity)
            include_row = (final_due <= 0)
        elif status_filter == 'outstanding':
            # Show students with any outstanding amount
            include_row = (final_due > 0)
        elif status_filter == 'partial_paid':
            # Show students with partial payments
            include_row = (payment_status == 'partial_paid')
        
        if include_row:
            report_data.append(row)
            
            # Update totals
            totals['current_fees'] += total_fees  # Use total fees (current + CF)
            totals['current_paid'] += current_paid  # Use ONLY current session payments
            totals['current_discount'] += total_fee_discount
            totals['cf_due'] += cf_due
            totals['cf_paid'] += cf_paid
            totals['cf_discount'] += cf_discount
            totals['fine_unpaid'] += fine_unpaid
            totals['fine_paid'] += fine_paid
            totals['final_due'] += row['final_due']
    
    # Pagination
    paginator = Paginator(report_data, page_size)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    # Use centralized fee service for enhanced calculations if available
    if FEE_SERVICE_AVAILABLE and fee_service:
        try:
            # Get enhanced fee insights from centralized service
            for i, row in enumerate(report_data):
                student = Student.objects.get(id=row['student_id'])
                fee_breakdown = fee_service.get_payment_breakdown(student)
                if fee_breakdown:
                    # Update with more accurate data from service
                    report_data[i].update({
                        'service_calculated': True,
                        'accurate_due': fee_breakdown.get('total_due', row['final_due'])
                    })
        except Exception as e:
            logger.error(f"Fee service enhancement error: {e}")
    
    # Get ML-powered insights
    ml_insights = {'error': 'ML analytics not available'}
    if ml_analytics:
        try:
            # Get risk predictions for current students
            student_ids = [row['student_id'] for row in report_data[:50]]  # Limit for performance
            risk_predictions = ml_analytics.predict_fee_collection_risk(student_ids)
            
            # Get collection forecasts
            collection_forecast = ml_analytics.forecast_monthly_collections(3)
            
            ml_insights = {
                'risk_predictions': risk_predictions,
                'collection_forecast': collection_forecast,
                'performance_insights': ml_analytics.generate_performance_insights()
            }
        except Exception as e:
            ml_insights = {'error': str(e)}
    
    # Get class list for dropdown
    class_list = ClassSection.objects.all().order_by('class_name', 'section_name')
    
    # Get daily payment summary with real data
    daily_summary = get_daily_payment_summary()
    
    context = {
        'report_data': page_obj,
        'page_obj': page_obj,
        'totals': totals,
        'class_list': class_list,
        'page_size': page_size,
        'report_date': timezone.now().date(),
        'ml_insights': ml_insights,
        'filters': filters,
        'payment_status_counts': payment_status_counts,
        'fee_service_available': FEE_SERVICE_AVAILABLE,
        'daily_summary': daily_summary
    }
    
    return render(request, 'reports/fees_report.html', context)

def get_daily_payment_summary():
    """Get comprehensive daily payment summary with ML insights"""
    from django.utils import timezone
    from datetime import datetime, timedelta
    import random
    
    now = timezone.now()
    today = now.date()
    yesterday = today - timedelta(days=1)
    week_start = today - timedelta(days=today.weekday())
    last_week_start = week_start - timedelta(days=7)
    month_start = today.replace(day=1)
    last_month = (month_start - timedelta(days=1)).replace(day=1)
    
    # Current period data
    today_data = FeeDeposit.objects.filter(deposit_date__date=today).aggregate(
        amount=Sum('paid_amount'), count=Count('id')
    )
    week_data = FeeDeposit.objects.filter(
        deposit_date__date__gte=week_start, deposit_date__date__lte=today
    ).aggregate(amount=Sum('paid_amount'), count=Count('id'))
    month_data = FeeDeposit.objects.filter(
        deposit_date__date__gte=month_start, deposit_date__date__lte=today
    ).aggregate(amount=Sum('paid_amount'), count=Count('id'))
    
    # Previous period data for growth calculation
    yesterday_data = FeeDeposit.objects.filter(deposit_date__date=yesterday).aggregate(
        amount=Sum('paid_amount'), count=Count('id')
    )
    last_week_data = FeeDeposit.objects.filter(
        deposit_date__date__gte=last_week_start, deposit_date__date__lt=week_start
    ).aggregate(amount=Sum('paid_amount'), count=Count('id'))
    last_month_data = FeeDeposit.objects.filter(
        deposit_date__date__gte=last_month, deposit_date__date__lt=month_start
    ).aggregate(amount=Sum('paid_amount'), count=Count('id'))
    
    # Calculate growth percentages
    def calc_growth(current, previous):
        if not previous or previous == 0:
            return 100 if current > 0 else 0
        return round(((current - previous) / previous) * 100, 1)
    
    today_amount = today_data['amount'] or 0
    week_amount = week_data['amount'] or 0
    month_amount = month_data['amount'] or 0
    
    daily_growth = calc_growth(today_amount, yesterday_data['amount'] or 0)
    weekly_growth = calc_growth(week_amount, last_week_data['amount'] or 0)
    monthly_growth = calc_growth(month_amount, last_month_data['amount'] or 0)
    
    # Payment velocity (payments per hour today)
    current_hour = now.hour
    velocity = round((today_data['count'] or 0) / max(current_hour, 1), 1)
    
    # Dynamic risk alerts based on actual data
    risk_alerts = []
    if today_amount == 0 and current_hour > 10:
        risk_alerts.append("⚠️ No payments received today after 10 AM")
    if weekly_growth < -20:
        risk_alerts.append(f"📉 Weekly collections down {abs(weekly_growth)}%")
    if velocity < 0.5 and current_hour > 12:
        risk_alerts.append("🐌 Low payment velocity detected")
    
    # Dynamic recommendations
    recommendations = []
    if today_amount == 0:
        recommendations.append("Send payment reminders to outstanding students")
    if weekly_growth > 20:
        recommendations.append("Excellent week! Consider fee structure optimization")
    if velocity > 2:
        recommendations.append("High payment activity - monitor system performance")
    
    # Prediction for tomorrow (simple trend-based)
    recent_days = FeeDeposit.objects.filter(
        deposit_date__date__gte=today - timedelta(days=7)
    ).values('deposit_date__date').annotate(
        daily_amount=Sum('paid_amount')
    ).order_by('deposit_date__date')
    
    avg_daily = sum(day['daily_amount'] or 0 for day in recent_days) / max(len(recent_days), 1)
    # Convert to float to avoid Decimal/float mixing
    tomorrow_prediction = round(float(avg_daily) * (1 + (float(weekly_growth) / 100)), 0)
    
    return {
        'today_amount': today_amount,
        'today_count': today_data['count'] or 0,
        'week_amount': week_amount,
        'week_count': week_data['count'] or 0,
        'month_amount': month_amount,
        'month_count': month_data['count'] or 0,
        'daily_growth': daily_growth,
        'weekly_growth': weekly_growth,
        'monthly_growth': monthly_growth,
        'payment_velocity': velocity,
        'risk_alerts': risk_alerts,
        'recommendations': recommendations,
        'tomorrow_prediction': tomorrow_prediction,
        'trend_direction': 'up' if weekly_growth > 0 else 'down',
        'performance_status': 'excellent' if weekly_growth > 10 else 'good' if weekly_growth > 0 else 'needs_attention'
    }
    
    return render(request, 'reports/fees_report.html', context)

# Export functionality removed

# Export functionality removed

# Export functionality removed

@login_required
@csrf_protect
@require_POST
def send_fee_reminder(request):
    """Send fee reminder SMS via MSG91"""
    try:
        data = json.loads(request.body)
    except json.JSONDecodeError:
        return JsonResponse({
            'success': False, 
            'message': 'Invalid data format received'
        })
    
    student_id = data.get('student_id')
    
    if not student_id:
        return JsonResponse({
            'success': False, 
            'message': 'Please select a student to send the fee reminder to.'
        })
    
    # Validate student ID
    try:
        student_id_int = _validate_numeric_id(student_id, "Student ID")
    except ValidationError:
        return JsonResponse({
            'success': False, 
            'message': 'Invalid student information'
        })
    
    try:
        from students.models import Student
        student = get_object_or_404(Student, id=student_id_int)
        
        if not student.mobile_number or len(student.mobile_number.strip()) < 10:
            return JsonResponse({
                'success': False, 
                'message': 'We couldn\'t find a valid mobile number for this student. Please update their contact information.'
            })
        
        # Sanitize student name for message
        student_name = escape(student.first_name)
        message = f"Dear {student_name}, your school fees are pending. Please pay at your earliest convenience. - School"
        
        # Log the reminder attempt
        logger.info(f"User {request.user.id} sending fee reminder to student {student_id_int}")
        
        # Actually send SMS using messaging service
        try:
            from messaging.services import SMSService
            sms_result = SMSService.send_sms(student.mobile_number, message)
            
            if sms_result['success']:
                # Log successful send to central messaging history
                try:
                    CrossModuleMessageLogger.log_report_notification(
                        user=request.user,
                        recipients_data=[{
                            'name': student.get_full_display_name(),
                            'phone': student.mobile_number,
                            'type': 'student',
                            'id': student.id,
                            'status': 'SENT'
                        }],
                        message_content=message,
                        status='SENT'
                    )
                except Exception as log_error:
                    logger.warning(f"Failed to log fee reminder to messaging history: {log_error}")
                
                return JsonResponse({
                    'success': True, 
                    'message': f'Perfect! Fee reminder has been sent successfully to {student_name} at {student.mobile_number}.'
                })
            else:
                # Log failed send
                try:
                    CrossModuleMessageLogger.log_report_notification(
                        user=request.user,
                        recipients_data=[{
                            'name': student.get_full_display_name(),
                            'phone': student.mobile_number,
                            'type': 'student',
                            'id': student.id,
                            'status': 'FAILED'
                        }],
                        message_content=message,
                        status='FAILED'
                    )
                except Exception as log_error:
                    logger.warning(f"Failed to log fee reminder to messaging history: {log_error}")
                
                return JsonResponse({
                    'success': False, 
                    'message': f'Could not send reminder to {student_name}. {sms_result.get("user_message", "Please try again later.")}'  
                })
                
        except ImportError:
            # Fallback if messaging service not available
            logger.warning("Messaging service not available, logging only")
            try:
                CrossModuleMessageLogger.log_report_notification(
                    user=request.user,
                    recipients_data=[{
                        'name': student.get_full_display_name(),
                        'phone': student.mobile_number,
                        'type': 'student',
                        'id': student.id,
                        'status': 'LOGGED_ONLY'
                    }],
                    message_content=message,
                    status='LOGGED_ONLY'
                )
            except Exception as log_error:
                logger.warning(f"Failed to log fee reminder to messaging history: {log_error}")
            
            return JsonResponse({
                'success': True, 
                'message': f'Fee reminder for {student_name} has been logged. SMS service is currently unavailable.'
            })
            
    except Exception as e:
        logger.error(f"Error sending fee reminder by user {request.user.id}: {str(e)}")
        return JsonResponse({
            'success': False, 
            'message': 'Something went wrong while sending the fee reminder. Please try again.'
        })

@login_required
@module_required('reports', 'view')
def dashboard_api_data(request):
    """API endpoint for real-time dashboard updates"""
    try:
        # Validate request method
        if request.method not in ['GET', 'POST']:
            return JsonResponse({
                'success': False, 
                'error': 'Invalid request method'
            }, status=405)
        
        # Get basic stats with proper error handling
        from student_fees.models import FeeDeposit
        from students.models import Student
        
        total_students = Student.objects.count()
        total_collected = FeeDeposit.objects.aggregate(
            total=Sum('paid_amount')
        )['total'] or 0
        
        # Log API access
        logger.info(f"Dashboard API accessed by user {request.user.id}")
        
        return JsonResponse({
            'success': True,
            'data': {
                'total_students': total_students,
                'total_collected': float(total_collected),
                'last_updated': timezone.now().isoformat()
            }
        })
    except Exception as e:
        logger.error(f"Error in dashboard_api_data for user {request.user.id}: {str(e)}")
        return JsonResponse({
            'success': False, 
            'error': 'We couldn\'t load the dashboard data right now. Please refresh the page.'
        }, status=500)