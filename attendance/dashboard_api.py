from django.http import JsonResponse
from django.views.decorators.http import require_http_methods
from django.db.models import Count, Q
from .models import Attendance
from students.models import Student
import logging

logger = logging.getLogger(__name__)

@require_http_methods(["GET"])
def attendance_report_api(request):
    """API endpoint for attendance report data"""
    try:
        student_id = request.GET.get('student_id')
        
        if not student_id:
            return JsonResponse({
                'success': False,
                'error': 'Student ID is required'
            }, status=400)
        
        # Get student
        try:
            student = Student.objects.all_statuses().get(admission_number=student_id)
        except Student.DoesNotExist:
            return JsonResponse({
                'success': False,
                'error': 'Student not found'
            }, status=404)
        
        # Get attendance data
        attendance_records = Attendance.objects.filter(student=student)
        
        total_days = attendance_records.count()
        present_days = attendance_records.filter(status='present').count()
        absent_days = attendance_records.filter(status='absent').count()
        
        percentage = round((present_days / total_days * 100), 2) if total_days > 0 else 0
        
        return JsonResponse([{
            'student_name': student.name,
            'admission_number': student.admission_number,
            'total_days': total_days,
            'present_days': present_days,
            'absent_days': absent_days,
            'percentage': percentage
        }], safe=False)
        
    except Exception as e:
        logger.error(f'Error in attendance report API: {e}')
        return JsonResponse({
            'success': False,
            'error': 'Internal server error'
        }, status=500)