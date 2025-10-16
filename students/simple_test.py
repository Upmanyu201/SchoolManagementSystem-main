from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from .models import Student

@login_required
def simple_student_list(request):
    """Minimal student list for testing"""
    students = Student.objects.all()[:10]
    return render(request, 'students/simple_test.html', {'students': students})