from django.shortcuts import render, get_object_or_404, redirect
from django.http import JsonResponse
from .models import Teacher
from .forms import TeacherForm
from django.contrib import messages
from users.decorators import module_required
from core.exports import ExportService
from datetime import datetime

# Optional ML integration
try:
    from core.ml_integrations import ml_service
    ML_AVAILABLE = True
except ImportError:
    ml_service = None
    ML_AVAILABLE = False

@module_required('teachers', 'view')
def teacher_list(request):
    teachers = Teacher.objects.all()
    
    # Handle export requests
    export_format = request.GET.get('export')
    if export_format:
        try:
            data, headers = ExportService.prepare_teacher_data(teachers)
            filename = f"teachers_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
            
            if export_format == 'excel':
                return ExportService.export_to_xlsx(data, filename, headers)
            elif export_format == 'csv':
                return ExportService.export_to_csv(data, filename, headers)
            elif export_format == 'pdf':
                return ExportService.export_to_pdf(data, filename, headers, "Teachers Report")
        except Exception as e:
            messages.error(request, f"Export failed: {str(e)}")
    
    # ML: Analyze teacher performance (optional)
    teacher_performance = []
    if ML_AVAILABLE and ml_service:
        for teacher in teachers[:10]:
            teacher_data = {
                'student_pass_rate': 0.85,
                'attendance_rate': 0.92,
                'years_experience': 5,
                'class_size': 35
            }
            
            analysis = ml_service.analyze_teacher_performance(teacher_data)
            teacher_performance.append({
                'teacher': teacher,
                'performance_score': analysis['performance_score'],
                'category': analysis['category']
            })
    
    context = {
        'teachers': teachers,
        'teacher_performance': teacher_performance,
        'excellent_count': len([t for t in teacher_performance if t['category'] == 'Excellent']) if teacher_performance else 0
    }
    
    return render(request, 'teachers/teacher_list.html', context)

@module_required('teachers', 'edit')
def add_teacher(request):
    if request.method == "POST":
        name = request.POST['name']
        mobile = request.POST['mobile']
        email = request.POST.get('email', '').strip() or None  # Handle optional email
        qualification = request.POST['qualification']
        joining_date = request.POST['joining_date']
        photo = request.FILES.get('photo')
        resume = request.FILES.get('resume')
        joining_letter = request.FILES.get('joining_letter')

        # Duplicate email check only if email is provided
        if email and Teacher.objects.filter(email=email).exists():
            messages.error(request, f'Sorry, the email {email} is already registered. Please use a different email address.')
            return redirect('add_teacher')

        Teacher.objects.create(
            name=name, mobile=mobile, email=email,
            qualification=qualification, joining_date=joining_date,
            photo=photo, resume=resume, joining_letter=joining_letter
        )
        
        # Invalidate dashboard cache after adding teacher
        try:
            from dashboard.views import invalidate_dashboard_cache
            invalidate_dashboard_cache()
        except ImportError:
            pass
            
        messages.success(request, f'Great! {name} has been added to the teaching staff successfully.')
        return redirect('teacher_list')

    return render(request, 'teachers/add_teacher.html')

@module_required('teachers', 'edit')
def edit_teacher(request, teacher_id):
    teacher = get_object_or_404(Teacher, id=teacher_id)

    if request.method == "POST":
        form = TeacherForm(request.POST, request.FILES, instance=teacher)
        if form.is_valid():
            form.save()
            
            # Invalidate dashboard cache after updating teacher
            try:
                from dashboard.views import invalidate_dashboard_cache
                invalidate_dashboard_cache()
            except ImportError:
                pass
                
            return redirect('teacher_list')
    else:
        form = TeacherForm(instance=teacher)

    return render(request, 'teachers/edit_teacher.html', {'form': form})

@module_required('teachers', 'edit')
def delete_teacher(request, id):
    teacher = Teacher.objects.get(id=id)
    teacher.delete()
    
    # Invalidate dashboard cache after deleting teacher
    try:
        from dashboard.views import invalidate_dashboard_cache
        invalidate_dashboard_cache()
    except ImportError:
        pass
        
    messages.success(request, f'{teacher.name} has been removed from the teaching staff successfully.')
    return redirect('teacher_list')