from django.shortcuts import render
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_protect
from django.views.decorators.http import require_POST
from django.contrib.auth.decorators import login_required
from django.core.exceptions import ValidationError
from django.utils.html import escape
from django.utils import timezone
from students.models import Student
from subjects.models import ClassSection
from .models import Attendance
from django.db.models import Count
from datetime import date
from users.decorators import module_required
import logging

logger = logging.getLogger(__name__)

# Optional ML integration
try:
    from core.ml_integrations import ml_service
    ML_AVAILABLE = True
except ImportError:
    ml_service = None
    ML_AVAILABLE = False

import json
import logging

logger = logging.getLogger(__name__)


@login_required
@module_required('attendance', 'view')
def get_students(request, class_section_id):
    """Get students for a specific class section"""
    try:
        # Validate class section ID
        try:
            section_id = int(class_section_id)
            if section_id <= 0:
                raise ValidationError("Invalid class section ID")
        except (ValueError, TypeError):
            return JsonResponse({'error': 'Invalid class section ID format'}, status=400)
        
        students = Student.objects.filter(
            class_section__id=section_id
        ).values('id', 'first_name', 'last_name', 'admission_number')

        # Sanitize student data
        student_list = []
        for student in students:
            student_list.append({
                'id': student['id'],
                'first_name': escape(student['first_name']),
                'last_name': escape(student['last_name']),
                'admission_number': escape(student['admission_number'])
            })
        
        return JsonResponse(student_list, safe=False)
    except Exception as e:
        logger.error(f"Error getting students for class {class_section_id} by user {request.user.id}: {str(e)}")
        return JsonResponse({'error': 'Sorry, we couldn\'t load the students for this class. Please try again.'}, status=500)


@login_required
@module_required('attendance', 'view')
def get_previous_attendance(request):
    try:
        class_section_id = request.GET.get('class_section_id')
        attendance_date = request.GET.get('date')

        if not all([class_section_id, attendance_date]):
            return JsonResponse({'error': 'Please select both a class and date to view attendance records.'}, status=400)
        
        # Validate class section ID
        try:
            section_id = int(class_section_id)
            if section_id <= 0:
                raise ValidationError("Invalid class section ID")
        except (ValueError, TypeError):
            return JsonResponse({'error': 'Invalid class section ID'}, status=400)
        
        # Validate date format
        try:
            from datetime import datetime
            datetime.strptime(attendance_date, '%Y-%m-%d')
        except ValueError:
            return JsonResponse({'error': 'Invalid date format. Please use YYYY-MM-DD.'}, status=400)

        attendance = Attendance.objects.filter(
            student__class_section__id=section_id,
            date=attendance_date
        ).values('student_id', 'status')

        return JsonResponse(list(attendance), safe=False)

    except Exception as e:
        logger.error(f"Error getting previous attendance by user {request.user.id}: {str(e)}")
        return JsonResponse({'error': 'We couldn\'t load the previous attendance data. Please refresh and try again.'}, status=500)


@login_required
@csrf_protect
@require_POST
@module_required('attendance', 'edit')
def mark_attendance(request):
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            
            # Log attendance marking attempt
            logger.info(f"User {request.user.id} marking attendance")

            class_section_id = data.get('class_section_id')
            attendance_date = data.get('date')
            attendance_data = data.get('attendance', [])

            if not all([class_section_id, attendance_date]):
                return JsonResponse({'error': 'Please select a class and date to mark attendance.'}, status=400)
            
            # Validate class section ID
            try:
                section_id = int(class_section_id)
                if section_id <= 0:
                    raise ValidationError("Invalid class section ID")
            except (ValueError, TypeError):
                return JsonResponse({'error': 'Invalid class section information'}, status=400)
            
            # Validate date format
            try:
                from datetime import datetime
                datetime.strptime(attendance_date, '%Y-%m-%d')
            except ValueError:
                return JsonResponse({'error': 'Invalid date format'}, status=400)
            
            # Validate attendance data
            if not isinstance(attendance_data, list):
                return JsonResponse({'error': 'Invalid attendance data format'}, status=400)

            # Get all students in the class-section
            from subjects.models import ClassSection
            try:
                class_section = ClassSection.objects.get(id=section_id)
            except ClassSection.DoesNotExist:
                return JsonResponse({'error': 'Selected class section not found'}, status=400)
            
            students_in_class = Student.objects.filter(class_section=class_section)

            # Mark all students as absent first
            for student in students_in_class:
                Attendance.objects.update_or_create(
                    student=student,
                    date=attendance_date,
                    defaults={
                        'status': 'Absent'
                    }
                )

            # Mark present students (those in attendance_data)
            for student_id in attendance_data:
                try:
                    # Validate student ID
                    student_id_int = int(student_id)
                    if student_id_int <= 0:
                        continue
                    
                    student = Student.objects.get(id=student_id_int, class_section=class_section)
                    Attendance.objects.update_or_create(
                        student=student,
                        date=attendance_date,
                        defaults={
                            'status': 'Present'
                        }
                    )
                except (Student.DoesNotExist, ValueError, TypeError):
                    continue

            return JsonResponse({'success': True, 'message': 'Perfect! Attendance has been marked successfully for all students.'})

        except json.JSONDecodeError:
            logger.error(f"JSON decode error in mark_attendance by user {request.user.id}")
            return JsonResponse({'error': 'We received invalid data. Please try marking attendance again.'}, status=400)
        except Exception as e:
            logger.error(f"Error marking attendance by user {request.user.id}: {str(e)}")
            return JsonResponse({'error': 'Something went wrong while saving attendance. Please try again.'}, status=500)

    return JsonResponse({'error': 'Invalid request method. Please use the attendance form to mark attendance.'}, status=405)


@login_required
@module_required('attendance', 'view')
def attendance_manage(request):
    """Load attendance management page"""
    try:
        today = timezone.now().date()
        class_sections = []

        # Get unique class-section combinations from students
        from django.db.models import Q
        students = Student.objects.select_related('class_section').all()
        
        # Create a set to avoid duplicates
        unique_combinations = set()
        for student in students:
            if student.class_section:
                # Sanitize class and section names
                class_name = escape(student.class_section.class_name)
                section_name = escape(student.class_section.section_name)
                combination = (student.class_section.id, class_name, section_name)
                unique_combinations.add(combination)
        
        # Convert to list and sort
        for class_section_id, class_name, section_name in sorted(unique_combinations):
            class_sections.append({
                'id': class_section_id,
                'name': f"{class_name} - {section_name}",
                'section_id': class_section_id
            })

        return render(request, 'attendance/attendance_management.html', {
            'class_sections': class_sections,
            'today': today
        })
    except Exception as e:
        logger.error(f"Error in attendance_manage for user {request.user.id}: {str(e)}")
        return render(request, 'attendance/attendance_management.html', {
            'class_sections': [],
            'today': timezone.now().date(),
            'error': 'We\'re having trouble loading the attendance page. Please try again.'
        })


@module_required('attendance', 'view')
def attendance_report(request):
    """Display attendance report page and provide report data on AJAX requests"""
    if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        # Handle class details request
        class_name = request.GET.get('class_name')
        single_date = request.GET.get('date')
        
        if class_name and single_date:
            try:
                report_date = date.fromisoformat(single_date)
                # Find ClassSection by class name
                try:
                    cls = ClassSection.objects.get(class_name=class_name)
                except ClassSection.DoesNotExist:
                    # Try to find by combined name
                    cls = ClassSection.objects.filter(class_name__icontains=class_name.split(' - ')[0]).first()
                
                students_data = []
                students = Student.objects.filter(class_section=cls) if cls else []
                
                for student in students:
                    attendance = Attendance.objects.filter(
                        student=student,
                        date=report_date
                    ).first()
                    
                    students_data.append({
                        'name': f"{student.first_name} {student.last_name}",
                        'status': attendance.status if attendance else 'No Record'
                    })
                
                return JsonResponse({'students': students_data})
            except (ValueError, ClassSection.DoesNotExist):
                return JsonResponse({'error': 'We couldn\'t find attendance data for the selected class and date.'}, status=400)
        
        # Handle single date report (professional format)
        report_date_str = request.GET.get('date')
        
        if report_date_str:
            try:
                report_date = date.fromisoformat(report_date_str)
            except ValueError:
                return JsonResponse({'error': 'Please enter a valid date in the correct format.'}, status=400)

            report_data = []
            class_sections = ClassSection.objects.all().order_by('class_name')

            for cls in class_sections:
                total_students = Student.objects.filter(class_section=cls).count()
                
                if total_students == 0:
                    continue
                
                present_count = Attendance.objects.filter(
                    student__class_section=cls,
                    date=report_date,
                    status='Present'
                ).count()
                
                absent_count = Attendance.objects.filter(
                    student__class_section=cls,
                    date=report_date,
                    status='Absent'
                ).count()

                report_data.append({
                    'class_name': f"{cls.class_name} - {cls.section_name}",
                    'total_students': total_students,
                    'present': present_count,
                    'absent': absent_count,
                })

            return JsonResponse({'report': report_data})
        
        # Handle legacy date range report
        from_date_str = request.GET.get('from_date')
        to_date_str = request.GET.get('to_date')
        
        if from_date_str and to_date_str:
            try:
                from_date = date.fromisoformat(from_date_str)
                to_date = date.fromisoformat(to_date_str)
            except ValueError:
                return JsonResponse({'error': 'Please enter valid dates in the correct format.'}, status=400)

            report_data = []
            class_sections = ClassSection.objects.all()

            for cls in class_sections:
                total_students = Student.objects.filter(class_section=cls).count()
                present_count = Attendance.objects.filter(
                    student__class_section=cls,
                    date__range=[from_date, to_date],
                    status='Present'
                ).count()
                absent_count = Attendance.objects.filter(
                    student__class_section=cls,
                    date__range=[from_date, to_date],
                    status='Absent'
                ).count()

                report_data.append({
                    'class_name': f"{cls.class_name} - {cls.section_name}",
                    'total_students': total_students,
                    'present': present_count,
                    'absent': absent_count,
                })

            return JsonResponse({'report': report_data})
        
        return JsonResponse({'error': 'Please select a date to generate the attendance report.'}, status=400)

        return JsonResponse({'report': report_data})
    else:
        return render(request, 'attendance/professional_attendance_report.html')

@module_required('attendance', 'view')
def professional_attendance_report(request):
    """Professional attendance report view with ML insights"""
    # ML: Analyze attendance patterns
    from datetime import datetime, timedelta
    
    # Get recent attendance data for ML analysis
    end_date = datetime.now().date()
    start_date = end_date - timedelta(days=30)
    
    attendance_records = Attendance.objects.filter(
        date__range=[start_date, end_date]
    ).values('date', 'status')
    
    # Calculate daily attendance rates
    daily_rates = []
    current_date = start_date
    while current_date <= end_date:
        total_records = Attendance.objects.filter(date=current_date).count()
        present_records = Attendance.objects.filter(date=current_date, status='Present').count()
        
        if total_records > 0:
            rate = present_records / total_records
        else:
            rate = 0.8  # Default rate if no data
        
        daily_rates.append(rate)
        current_date += timedelta(days=1)
    
    # Get students with low attendance
    low_attendance_students = []
    students = Student.objects.all()[:10]  # Limit for performance
    
    for student in students:
        student_attendance = Attendance.objects.filter(
            student=student,
            date__range=[start_date, end_date]
        )
        
        total_days = student_attendance.count()
        present_days = student_attendance.filter(status='Present').count()
        
        if total_days > 0 and (present_days / total_days) < 0.75:
            low_attendance_students.append(f"{student.first_name} {student.last_name}")
    
    # ML Analysis (optional)
    ml_analysis = None
    if ML_AVAILABLE and ml_service:
        attendance_data = {
            'daily_rates': daily_rates,
            'low_attendance_students': low_attendance_students
        }
        ml_analysis = ml_service.analyze_attendance_patterns(attendance_data)
    
    context = {
        'ml_analysis': ml_analysis,
        'current_rate': ml_analysis['current_rate'] if ml_analysis else round(sum(daily_rates) / len(daily_rates) * 100, 1) if daily_rates else 0,
        'trend': ml_analysis['trend'] if ml_analysis else 'Stable',
        'predicted_rate': ml_analysis['predicted_next_week'] if ml_analysis else round(sum(daily_rates) / len(daily_rates) * 100, 1) if daily_rates else 0,
        'at_risk_students': ml_analysis['at_risk_students'] if ml_analysis else low_attendance_students
    }
    
    return render(request, 'attendance/professional_attendance_report.html', context)
