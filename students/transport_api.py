from django.http import JsonResponse
from django.views.decorators.http import require_http_methods
from .models import Student
import logging

logger = logging.getLogger(__name__)

@require_http_methods(["GET"])
def student_transport_api(request, admission_number):
    """API endpoint for student transport information"""
    try:
        # Get student
        try:
            student = Student.objects.all_statuses().get(admission_number=admission_number)
        except Student.DoesNotExist:
            return JsonResponse({
                'success': False,
                'error': 'Student not found'
            }, status=404)
        
        # Check if student has transport assignment
        transport_info = {
            'assigned': False,
            'route_name': None,
            'stoppage_name': None,
            'assigned_date': None,
            'pickup_time': None,
            'drop_time': None
        }
        
        if hasattr(student, 'transport_assignment') and student.transport_assignment:
            transport_info.update({
                'assigned': True,
                'route_name': getattr(student.transport_assignment.route, 'name', 'Not specified'),
                'stoppage_name': getattr(student.transport_assignment.stoppage, 'name', 'Not specified'),
                'assigned_date': student.transport_assignment.assigned_date.strftime('%d %b %Y') if student.transport_assignment.assigned_date else 'Not specified',
                'pickup_time': getattr(student.transport_assignment.stoppage, 'pickup_time', 'Not specified'),
                'drop_time': getattr(student.transport_assignment.stoppage, 'drop_time', 'Not specified')
            })
        
        return JsonResponse({
            'success': True,
            'transport_info': transport_info
        })
        
    except Exception as e:
        logger.error(f'Error in transport API: {e}')
        return JsonResponse({
            'success': False,
            'error': 'Internal server error'
        }, status=500)