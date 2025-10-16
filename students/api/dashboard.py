from django.http import JsonResponse
from django.contrib.auth.decorators import login_required
from django.shortcuts import get_object_or_404
from django.core.cache import cache
from django.utils import timezone
from django.db.models import Sum, Count, Q
from datetime import timedelta
from students.models import Student
from student_fees.models import FeeDeposit
from attendance.models import Attendance

@login_required
def student_dashboard_api(request, student_id):
    """Consolidated dashboard API endpoint"""
    
    # Get student with proper error handling
    try:
        student = Student.objects.get(id=student_id)
    except Student.DoesNotExist:
        return JsonResponse({
            'success': False,
            'error': 'Student not found',
            'message': 'The requested student does not exist.'
        }, status=404)
    
    # Check cache
    cache_key = f"student_dashboard_{student_id}"
    cached_data = cache.get(cache_key)
    
    if cached_data:
        return JsonResponse(cached_data)
    
    # Calculate financial summary
    fee_deposits = FeeDeposit.objects.filter(student=student)
    total_paid = fee_deposits.aggregate(Sum('paid_amount'))['paid_amount__sum'] or 0
    current_dues = 0  # Simplified for testing
    
    # Calculate attendance
    current_month = timezone.now().replace(day=1)
    next_month = (current_month + timedelta(days=32)).replace(day=1)
    
    attendance_data = Attendance.objects.filter(
        student=student,
        date__gte=current_month.date(),
        date__lt=next_month.date()
    ).aggregate(
        total=Count('id'),
        present=Count('id', filter=Q(status='Present'))
    )
    
    total_days = attendance_data['total'] or 0
    present_days = attendance_data['present'] or 0
    attendance_percentage = (present_days / total_days * 100) if total_days > 0 else 0
    
    # Build response
    response_data = {
        'success': True,
        'timestamp': timezone.now().isoformat(),
        'student_info': {
            'id': student.id,
            'name': f"{student.first_name} {student.last_name}",
            'admission_number': student.admission_number,
            'email': student.email
        },
        'financial_summary': {
            'current_dues': current_dues,
            'total_paid': float(total_paid),
            'last_payment': None
        },
        'attendance_summary': {
            'current_month': {
                'total_days': total_days,
                'present_days': present_days,
                'percentage': round(attendance_percentage, 1)
            }
        },
        'transport_info': {
            'route': None,
            'pickup_point': None
        },
        'recent_activities': [],
        'ml_insights': {
            'status': 'ml_unavailable'
        }
    }
    
    # Cache for 5 minutes
    cache.set(cache_key, response_data, 300)
    
    return JsonResponse(response_data)