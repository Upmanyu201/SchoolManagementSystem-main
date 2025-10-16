# Dashboard Views with Unified Data Service
from django.shortcuts import render
from django.http import JsonResponse
from django.views.decorators.cache import never_cache
from django.views.decorators.http import require_http_methods
from django.utils import timezone
from datetime import timedelta, date
from django.db.models import Sum
from .unified_data_service import UnifiedDashboardService
import json

# Import models safely
try:
    from students.models import Student
    from teachers.models import Teacher
    from student_fees.models import FeeDeposit
    from subjects.models import Subject
except ImportError:
    Student = None
    Teacher = None
    FeeDeposit = None
    Subject = None

# Cache invalidation function
def invalidate_dashboard_cache():
    """Invalidate dashboard cache when data changes"""
    from django.core.cache import cache
    cache.delete('dashboard_stats')
    cache.set('dashboard_last_update', timezone.now().isoformat(), 3600)

@never_cache
def force_cache_refresh(request):
    """Force refresh dashboard cache - for debugging"""
    invalidate_dashboard_cache()
    return JsonResponse({'success': True, 'message': 'Cache refreshed'})

@never_cache
def dashboard_stats_api(request):
    """API endpoint for real-time dashboard statistics"""
    try:
        from django.core.cache import cache
        
        # Check cache first
        cache_key = 'dashboard_stats'
        cached_data = cache.get(cache_key)
        
        if cached_data is None:
            service = UnifiedDashboardService()
            dashboard_data = service.get_complete_dashboard_data()
            # Cache for 2 minutes
            cache.set(cache_key, dashboard_data, 120)
        else:
            dashboard_data = cached_data
        
        return JsonResponse({
            'success': True,
            'data': dashboard_data,
            'cached': cached_data is not None,
            'timestamp': timezone.now().isoformat()
        })
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)})

@never_cache
def dashboard_view(request):
    """Main dashboard view with unified data service"""
    try:
        # Get all data from unified service
        service = UnifiedDashboardService()
        dashboard_data = service.get_complete_dashboard_data()
        
        # Extract data for template context
        basic_stats = dashboard_data['basic_stats']
        fee_data = dashboard_data['fee_data']
        attendance_data = dashboard_data['attendance_data']
        fines_data = dashboard_data['fines_data']
        alerts = dashboard_data['alerts']
        
        # Get birthday data
        birthday_data = get_birthday_data()
        
        # Get fee overview data
        fee_overview = dashboard_data.get('fee_overview', {})
        
        context = {
            # Basic statistics
            'total_students': basic_stats['total_students'],
            'total_teachers': basic_stats['total_teachers'],
            'total_classes': basic_stats['total_classes'],
            'total_subjects': basic_stats['total_subjects'],
            'new_admissions': basic_stats['new_admissions'],
            'active_teachers': basic_stats['active_teachers'],
            
            # Fee statistics
            'monthly_revenue': fee_data['monthly_revenue'],
            'total_fees_collected': fee_data['total_fees_collected'],
            'pending_fees_count': fee_data['pending_fees_count'],
            'overdue_fees_count': fee_data['overdue_fees_count'],
            
            # Fee Overview data - Fixed variable names to match template
            'total_pending_amount': fee_overview.get('total_pending_amount', 0),
            'total_fines_amount': fines_data.get('total_amount', 0),
            'total_collected_fines': fines_data.get('total_collected_fines', 0),
            'monthly_fines_amount': fines_data.get('monthly_fines_amount', 0),
            'pending_fines_count': fines_data.get('pending_count', 0),
            'overdue_fines_count': fines_data.get('overdue_count', 0),
            
            # Attendance statistics
            'today_attendance_rate': attendance_data['today_attendance_rate'],
            'avg_attendance': attendance_data['monthly_average'],
            'low_attendance_count': attendance_data['low_attendance_count'],
            
            # Alerts
            'alerts': alerts,
            
            # Birthday data
            'today_birthdays': birthday_data.get('today', []),
            'week_birthdays': birthday_data.get('week', []),
            'month_birthdays': birthday_data.get('month', []),
            
            # Additional context for compatibility
            'upcoming_events_count': 3  # Mock data for now
        }
        
        return render(request, 'dashboard.html', context)
        
    except Exception as e:
        # Fallback with minimal data
        context = {
            'total_students': 0,
            'total_teachers': 0,
            'total_classes': 0,
            'total_subjects': 0,
            'monthly_revenue': 0,
            'total_fees_collected': 0,
            'new_admissions': 0,
            'pending_fees_count': 0,
            'overdue_fees_count': 0,
            'today_attendance_rate': 0,
            'avg_attendance': 0,
            'low_attendance_count': 0,
            'active_teachers': 0,
            'alerts': [],
            'upcoming_events_count': 0,
            'today_birthdays': [],
            'week_birthdays': [],
            'month_birthdays': [],
            # Fines fallback data
            'total_fines_amount': 0,
            'total_collected_fines': 0,
            'pending_fines_count': 0,
            'overdue_fines_count': 0,
        }
        return render(request, 'dashboard.html', context)

@never_cache
def check_dashboard_updates(request):
    """Check for dashboard updates"""
    try:
        from django.core.cache import cache
        last_update = cache.get('dashboard_last_update')
        client_last_update = request.GET.get('last_update')
        
        has_updates = False
        if client_last_update and last_update:
            try:
                from datetime import datetime
                client_time = datetime.fromisoformat(client_last_update.replace('Z', '+00:00'))
                server_time = datetime.fromisoformat(last_update)
                has_updates = server_time > client_time
            except (ValueError, TypeError):
                has_updates = True
        
        return JsonResponse({
            'success': True,
            'has_updates': has_updates or last_update is not None,
            'last_update': last_update,
            'timestamp': timezone.now().isoformat()
        })
    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': 'Failed to check for updates'
        }, status=500)

# Add URL for force refresh
# /dashboard/force-refresh/

def get_birthday_data():
    """Get birthday data for dashboard - works for all current and future students"""
    if not Student:
        return {'today': [], 'week': [], 'month': []}
    
    today = date.today()
    
    def calculate_age(birth_date):
        """Calculate current age"""
        age = today.year - birth_date.year
        if today < birth_date.replace(year=today.year):
            age -= 1
        return age
    
    def days_until_birthday(birth_date):
        """Calculate days until next birthday"""
        try:
            # This year's birthday
            this_year_birthday = birth_date.replace(year=today.year)
            
            # If birthday already passed this year, use next year
            if this_year_birthday < today:
                this_year_birthday = birth_date.replace(year=today.year + 1)
            
            return (this_year_birthday - today).days
        except ValueError:
            # Handle leap year edge case (Feb 29)
            if birth_date.month == 2 and birth_date.day == 29:
                this_year_birthday = date(today.year, 2, 28)
                if this_year_birthday < today:
                    this_year_birthday = date(today.year + 1, 2, 28)
                return (this_year_birthday - today).days
            return 365  # Fallback
    
    def format_student(student):
        """Format student data for birthday display"""
        try:
            birth_date = student.date_of_birth
            age = calculate_age(birth_date)
            days_left = days_until_birthday(birth_date)
            
            return {
                'id': student.id,
                'name': f"{student.first_name} {student.last_name}",
                'class': student.class_section.display_name if student.class_section else 'N/A',
                'age': age,
                'date': birth_date.strftime('%b %d'),
                'daysLeft': days_left
            }
        except Exception:
            return None
    
    try:
        # Get all students with valid birth dates
        all_students = Student.objects.filter(
            date_of_birth__isnull=False
        ).select_related('class_section')
        

        
        today_birthdays = []
        week_birthdays = []
        month_birthdays = []
        
        for student in all_students:
            formatted_student = format_student(student)
            if not formatted_student:
                continue
                
            days_left = formatted_student['daysLeft']

            
            # Categorize by days until birthday
            if days_left == 0:
                today_birthdays.append(formatted_student)
            elif 1 <= days_left <= 7:
                week_birthdays.append(formatted_student)
            elif 8 <= days_left <= 30:
                month_birthdays.append(formatted_student)
        
        # Sort by days remaining
        week_birthdays.sort(key=lambda x: x['daysLeft'])
        month_birthdays.sort(key=lambda x: x['daysLeft'])
        

        
        return {
            'today': today_birthdays[:10],
            'week': week_birthdays[:15],
            'month': month_birthdays[:20]
        }
        
    except Exception:
        return {'today': [], 'week': [], 'month': []}