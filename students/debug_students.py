# Quick diagnostic script for students
from django.http import JsonResponse
from django.contrib.auth.decorators import login_required
from .models import Student

@login_required
def debug_students_count(request):
    """Simple diagnostic to check students in database"""
    try:
        total_students = Student.objects.count()
        first_5_students = list(Student.objects.all()[:5].values(
            'id', 'admission_number', 'first_name', 'last_name'
        ))
        
        return JsonResponse({
            'total_students': total_students,
            'first_5_students': first_5_students,
            'database_accessible': True
        })
    except Exception as e:
        return JsonResponse({
            'error': str(e),
            'database_accessible': False
        })