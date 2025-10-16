# C:\xampp\htdocs\school_management\dashboard\views.py
from django.shortcuts import render
from students.models import Student
from teachers.models import Teacher
from student_fees.models import FeeDeposit
from core.models import AcademicClass
from subjects.models import Subject
from django.db.models import Sum, Count, Q
from django.http import JsonResponse
from datetime import datetime, timedelta
from django.utils import timezone

def get_fees_data(request):
    """API endpoint for fee collection data"""
    try:
        # Get fee collection data for the last 30 days
        thirty_days_ago = timezone.now() - timedelta(days=30)
        fees_data = FeeDeposit.objects.filter(
            created_at__gte=thirty_days_ago
        ).values('created_at__date').annotate(
            total=Sum('paid_amount')
        ).order_by('created_at__date')
        
        return JsonResponse({
            'success': True,
            'data': list(fees_data)
        })
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)})

def get_attendance_data(request):
    """API endpoint for attendance data"""
    try:
        # Calculate today's attendance rate
        today = timezone.now().date()
        total_students = Student.objects.count()
        
        # This would need actual attendance model integration
        # For now, return mock data
        attendance_rate = 85  # Mock data
        
        return JsonResponse({
            'success': True,
            'attendance_rate': attendance_rate,
            'total_students': total_students
        })
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)})

def get_students_data(request):
    """API endpoint for student statistics"""
    try:
        total_students = Student.objects.count()
        new_admissions = Student.objects.filter(
            date_of_admission__gte=timezone.now() - timedelta(days=30)
        ).count()
        
        return JsonResponse({
            'success': True,
            'total_students': total_students,
            'new_admissions': new_admissions
        })
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)})

def dashboard_stats_api(request):
    """API endpoint for real-time dashboard statistics"""
    try:
        # Basic counts
        total_students = Student.objects.count()
        total_teachers = Teacher.objects.count()
        total_classes = AcademicClass.objects.count()
        total_subjects = Subject.objects.count()
        
        # Fee statistics
        total_fees_collected = FeeDeposit.objects.aggregate(
            total=Sum('paid_amount')
        )['total'] or 0
        
        monthly_revenue = FeeDeposit.objects.filter(
            created_at__gte=timezone.now() - timedelta(days=30)
        ).aggregate(total=Sum('paid_amount'))['total'] or 0
        
        # Recent admissions
        new_admissions = Student.objects.filter(
            date_of_admission__gte=timezone.now() - timedelta(days=30)
        ).count()
        
        return JsonResponse({
            'success': True,
            'stats': {
                'total_students': total_students,
                'total_teachers': total_teachers,
                'total_classes': total_classes,
                'total_subjects': total_subjects,
                'total_fees_collected': float(total_fees_collected),
                'monthly_revenue': float(monthly_revenue),
                'new_admissions': new_admissions,
            }
        })
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)})

def dashboard_view(request):
    """Main dashboard view with comprehensive statistics"""
    try:
        # Basic counts
        total_students = Student.objects.count()
        total_teachers = Teacher.objects.count()
        total_classes = AcademicClass.objects.count()
        total_subjects = Subject.objects.count()
        
        # Fee statistics
        total_fees_collected = FeeDeposit.objects.aggregate(
            total=Sum('paid_amount')
        )['total'] or 0
        
        monthly_revenue = FeeDeposit.objects.filter(
            created_at__gte=timezone.now() - timedelta(days=30)
        ).aggregate(total=Sum('paid_amount'))['total'] or 0
        
        # Recent admissions (last 30 days)
        new_admissions = Student.objects.filter(
            date_of_admission__gte=timezone.now() - timedelta(days=30)
        ).count()
        
        # Pending fees count (students with no recent payments)
        thirty_days_ago = timezone.now() - timedelta(days=30)
        students_with_recent_payments = FeeDeposit.objects.filter(
            created_at__gte=thirty_days_ago
        ).values_list('student_id', flat=True).distinct()
        
        pending_fees_count = Student.objects.exclude(
            id__in=students_with_recent_payments
        ).count()
        
        # Mock data for features that need additional models
        today_attendance_rate = 85  # Would need attendance model
        avg_attendance = 82  # Would need attendance model
        active_teachers = total_teachers  # All teachers considered active
        overdue_fees_count = pending_fees_count // 2  # Mock calculation
        low_attendance_count = total_students // 10  # Mock calculation
        upcoming_events_count = 3  # Mock data
        
        context = {
            'total_students': total_students,
            'total_teachers': total_teachers,
            'total_classes': total_classes,
            'total_subjects': total_subjects,
            'total_fees_collected': total_fees_collected,
            'monthly_revenue': monthly_revenue,
            'new_admissions': new_admissions,
            'pending_fees_count': pending_fees_count,
            'today_attendance_rate': today_attendance_rate,
            'avg_attendance': avg_attendance,
            'active_teachers': active_teachers,
            'overdue_fees_count': overdue_fees_count,
            'low_attendance_count': low_attendance_count,
            'upcoming_events_count': upcoming_events_count,
        }
        
        return render(request, 'dashboard.html', context)
        
    except Exception as e:
        # Fallback with basic data in case of errors
        context = {
            'total_students': Student.objects.count(),
            'total_teachers': Teacher.objects.count(),
            'total_classes': AcademicClass.objects.count(),
            'total_subjects': Subject.objects.count(),
            'total_fees_collected': 0,
            'monthly_revenue': 0,
            'new_admissions': 0,
            'pending_fees_count': 0,
            'today_attendance_rate': 0,
            'avg_attendance': 0,
            'active_teachers': 0,
            'overdue_fees_count': 0,
            'low_attendance_count': 0,
            'upcoming_events_count': 0,
        }
        return render(request, 'dashboard.html', context)
