from django.shortcuts import render
from django.http import JsonResponse
from django.views.decorators.http import require_POST
from django.views.decorators.csrf import csrf_protect
from django.contrib.auth.decorators import login_required
from django.core.exceptions import ValidationError
from django.utils.html import escape
from django.utils import timezone
from django.db.models import Count, Q
import json
from students.models import Student
from subjects.models import ClassSection
from school_profile.models import SchoolProfile
try:
    from attendance.models import Attendance
except ImportError:
    Attendance = None
from django.contrib import messages
from users.decorators import module_required
import logging

logger = logging.getLogger(__name__)

def _validate_promotion_data(promotions):
    """Validate promotion data structure"""
    if not isinstance(promotions, list):
        return False, "Promotions must be a list"
    
    for promotion in promotions:
        if not isinstance(promotion, dict):
            return False, "Each promotion must be a dictionary"
        
        if 'student_id' not in promotion or 'new_class_id' not in promotion:
            return False, "Missing required fields in promotion data"
    
    return True, "Valid"

@login_required
@module_required('promotion', 'view')
def student_promotion(request):
    """Main promotion page"""
    try:
        school_profile = SchoolProfile.objects.first()
        current_year = school_profile.start_date.year if school_profile else timezone.now().year
        current_session = f"{current_year}-{current_year + 1}"
        next_session = f"{current_year + 1}-{current_year + 2}"
    except Exception as e:
        logger.error(f"Error getting school profile for user {request.user.id}: {str(e)}")
        current_year = timezone.now().year
        current_session = f"{current_year}-{current_year + 1}"
        next_session = f"{current_year + 1}-{current_year + 2}"

    try:
        classes = ClassSection.objects.all().order_by('class_name', 'section_name')
    except Exception as e:
        logger.error(f"Error getting classes for user {request.user.id}: {str(e)}")
        classes = []
    
    context = {
        'current_session': current_session,
        'next_session': next_session,
        'classes': classes,
    }
    return render(request, 'promotion/student_promotion.html', context)

@login_required
@csrf_protect
@require_POST
@module_required('promotion', 'view')
def get_students_by_class(request):
    """Get students by selected class with attendance data"""
    try:
        # Handle both JSON and form data
        if request.content_type == 'application/json':
            try:
                data = json.loads(request.body)
            except json.JSONDecodeError:
                return JsonResponse({'status': 'error', 'message': 'Invalid data format received'})
        else:
            data = request.POST
            
        class_id = data.get('class_id')
        
        if not class_id:
            return JsonResponse({'status': 'error', 'message': 'Please select a class to view students for promotion.'})
        
        # Validate class ID
        try:
            class_id_int = int(class_id)
            if class_id_int < 0:
                raise ValidationError("Invalid class ID")
        except (ValueError, TypeError, ValidationError):
            return JsonResponse({'status': 'error', 'message': 'Invalid class selection'})
        
        try:
            students = Student.objects.filter(
                class_section_id=class_id_int
            ).select_related('class_section').order_by('admission_number')
        except Exception as e:
            logger.error(f"Error getting students for class {class_id} by user {request.user.id}: {str(e)}")
            return JsonResponse({'status': 'error', 'message': 'Unable to load students for this class'})
        
        # Get all classes for promotion dropdown
        try:
            all_classes = ClassSection.objects.all().order_by('class_name', 'section_name')
        except Exception as e:
            logger.error(f"Error getting all classes for user {request.user.id}: {str(e)}")
            all_classes = []
        
        students_data = []
        for student in students:
            try:
                # Calculate attendance percentage
                if Attendance:
                    total_attendance = Attendance.objects.filter(student=student).count()
                    present_days = Attendance.objects.filter(student=student, status='Present').count()
                    attendance_percentage = round((present_days / total_attendance * 100), 2) if total_attendance > 0 else 0
                else:
                    total_attendance = 0
                    present_days = 0
                    attendance_percentage = 0
                
                # Sanitize student data
                students_data.append({
                    'id': student.id,
                    'admission_number': escape(student.admission_number),
                    'name': escape(f"{student.first_name} {student.last_name}"),
                    'current_class': escape(student.class_section.display_name) if student.class_section else 'N/A',
                    'attendance_percentage': attendance_percentage,
                    'present_days': present_days,
                    'total_days': total_attendance
                })
            except Exception as e:
                logger.error(f"Error processing student {student.id} for user {request.user.id}: {str(e)}")
                continue
        
        classes_data = []
        for cls in all_classes:
            try:
                classes_data.append({
                    'id': cls.id,
                    'name': escape(cls.display_name if hasattr(cls, 'display_name') else f"{cls.class_name} - {cls.section_name}")
                })
            except Exception as e:
                logger.error(f"Error processing class {cls.id} for user {request.user.id}: {str(e)}")
                continue
        
        return JsonResponse({
            'status': 'success',
            'students': students_data,
            'classes': classes_data
        })
        
    except Exception as e:
        logger.error(f"Error in get_students_by_class by user {request.user.id}: {str(e)}")
        return JsonResponse({'status': 'error', 'message': 'Sorry, we couldn\'t load the students for this class. Please try again.'})

@login_required
@csrf_protect
@require_POST
@module_required('promotion', 'edit')
def promote_students(request):
    """Promote selected students to new classes"""
    try:
        # Handle both JSON and form data
        if request.content_type == 'application/json':
            try:
                data = json.loads(request.body)
            except json.JSONDecodeError:
                return JsonResponse({'status': 'error', 'message': 'Invalid data format received'})
        else:
            data = request.POST
            
        promotions = data.get('promotions', [])
        
        if not promotions or not isinstance(promotions, list):
            return JsonResponse({'status': 'error', 'message': 'Please select at least one student to promote to the next class.'})
        
        # Validate promotions data
        if len(promotions) > 100:  # Limit bulk operations
            return JsonResponse({'status': 'error', 'message': 'Too many students selected. Please promote in smaller batches.'})
        
        promoted_count = 0
        errors = []
        
        # Log promotion attempt
        logger.info(f"User {request.user.id} attempting to promote {len(promotions)} students")
        
        for promotion in promotions:
            if not isinstance(promotion, dict):
                errors.append("Invalid promotion data format")
                continue
                
            student_id = promotion.get('student_id')
            new_class_id = promotion.get('new_class_id')
            
            # Validate IDs
            try:
                student_id_int = int(student_id)
                new_class_id_int = int(new_class_id)
                if student_id_int < 0 or new_class_id_int < 0:
                    raise ValidationError("Invalid ID")
            except (ValueError, TypeError, ValidationError):
                errors.append(f"Invalid student or class information")
                continue
            
            try:
                student = Student.objects.get(id=student_id_int)
                new_class = ClassSection.objects.get(id=new_class_id_int)
                
                # Update student class
                old_class = student.class_section
                student.class_section = new_class
                student.save()
                
                promoted_count += 1
                
            except Student.DoesNotExist:
                errors.append(f"We couldn\'t find the student with ID {student_id}")
            except ClassSection.DoesNotExist:
                errors.append(f"The selected class is no longer available")
            except Exception as e:
                logger.error(f"Error promoting student {student_id} by user {request.user.id}: {str(e)}")
                errors.append(f"We couldn\'t promote student {student_id} due to an error")
        
        if errors:
            return JsonResponse({
                'status': 'partial',
                'message': f"Great! {promoted_count} students have been promoted successfully. However, {len(errors)} students couldn\'t be promoted.",
                'errors': errors
            })
        
        return JsonResponse({
            'status': 'success',
            'message': f"Excellent! All {promoted_count} students have been promoted successfully to their new classes."
        })
        
    except Exception as e:
        logger.error(f"Error in promote_students by user {request.user.id}: {str(e)}")
        return JsonResponse({'status': 'error', 'message': 'Something went wrong while promoting students. Please try again.'})