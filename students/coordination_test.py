from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from .models import Student

@login_required
def coordination_test(request):
    """Test frontend-backend coordination"""
    
    # Backend data
    students = Student.objects.all()[:5]
    total_count = Student.objects.count()
    
    # Create simple context
    context = {
        'students': students,
        'total_count': total_count,
        'backend_working': True,
        'test_data': {
            'message': 'Backend is working',
            'timestamp': '2024-01-01 12:00:00'
        }
    }
    
    return render(request, 'students/coordination_test.html', context)

@login_required
def coordination_api(request):
    """API test for frontend-backend coordination"""
    
    try:
        students = Student.objects.all()[:3]
        student_data = []
        
        for student in students:
            student_data.append({
                'admission_number': student.admission_number,
                'name': f"{student.first_name} {student.last_name}",
                'class': str(student.class_section) if student.class_section else 'N/A'
            })
        
        return JsonResponse({
            'success': True,
            'total_students': Student.objects.count(),
            'sample_students': student_data,
            'backend_status': 'working'
        })
        
    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': str(e),
            'backend_status': 'error'
        })