from django.http import JsonResponse
from django.views.decorators.csrf import csrf_protect
from django.views.decorators.http import require_http_methods
from django.contrib.auth.decorators import login_required
from django.core.paginator import Paginator
from django.db.models import Q
from decimal import Decimal
import json

from .models import Student
from .services import StudentService, StudentDashboardService
from users.decorators import module_required
from core.security_utils import sanitize_input, log_security_event, check_rate_limit


@login_required
@module_required('students', 'view')
@require_http_methods(["GET"])
def search_students_api(request):
    """AJAX endpoint for student search with rate limiting"""
    if check_rate_limit(request.user, 'student_search', limit=30, window_minutes=1):
        return JsonResponse({'error': 'Too many search requests. Please wait a moment.'}, status=429)
    
    try:
        query = request.GET.get('q', '').strip()
        class_filter = request.GET.get('class_id')
        page = int(request.GET.get('page', 1))
        
        if not query or len(query) < 2:
            return JsonResponse({'results': [], 'total': 0, 'message': 'Please enter at least 2 characters to search'})
        
        filters = {}
        if class_filter:
            try:
                filters['class_id'] = int(class_filter)
            except ValueError:
                pass
        
        students = StudentService.search_students_advanced(query, filters)
        paginator = Paginator(students, 10)
        page_obj = paginator.get_page(page)
        
        results = []
        for student in page_obj:
            results.append({
                'id': student.id,
                'admission_number': student.admission_number,
                'name': f"{student.first_name} {student.last_name}",
                'class': student.class_section.class_name if student.class_section else 'N/A',
                'section': student.class_section.section_name if student.class_section else 'N/A',
                'mobile': student.mobile_number,
                'email': student.email,
                'due_amount': str(student.due_amount or 0),
                'url': f"/students/edit/{student.id}/"
            })
        
        return JsonResponse({
            'results': results,
            'total': paginator.count,
            'page': page,
            'total_pages': paginator.num_pages,
            'has_next': page_obj.has_next(),
            'has_previous': page_obj.has_previous()
        })
        
    except Exception as e:
        return JsonResponse({'error': 'Search failed. Please try again.', 'details': sanitize_input(str(e))}, status=500)


@login_required
@module_required('students', 'view')
@require_http_methods(["GET"])
def student_dashboard_api(request, admission_number):
    """API endpoint for student dashboard data"""
    try:
        clean_admission = sanitize_input(admission_number.strip())
        
        if not clean_admission:
            return JsonResponse({'error': 'Invalid admission number'}, status=400)
        
        try:
            student = Student.objects.get_with_complete_data(clean_admission)
        except Student.DoesNotExist:
            return JsonResponse({'error': 'Student not found'}, status=404)
        
        dashboard_data = StudentDashboardService.get_complete_dashboard_data(student)
        financial_summary = StudentService.get_student_financial_summary(student)
        dashboard_data['financial_detailed'] = financial_summary
        
        timeline = StudentDashboardService.get_student_timeline(student, days=30)
        dashboard_data['timeline'] = timeline
        
        return JsonResponse({'success': True, 'data': dashboard_data})
        
    except Exception as e:
        return JsonResponse({'error': 'Failed to load dashboard data', 'details': sanitize_input(str(e))}, status=500)


@login_required
@module_required('students', 'view')
@require_http_methods(["GET"])
def students_stats_api(request):
    """API endpoint for student statistics"""
    try:
        stats = StudentService.get_dashboard_stats()
        students_with_dues = StudentService.get_students_with_dues(Decimal('100'))
        
        dues_data = []
        for student in students_with_dues[:10]:
            dues_data.append({
                'admission_number': student.admission_number,
                'name': f"{student.first_name} {student.last_name}",
                'class': student.class_section.class_name if student.class_section else 'N/A',
                'due_amount': str(student.due_amount),
                'mobile': student.mobile_number
            })
        
        return JsonResponse({
            'success': True,
            'stats': stats,
            'top_dues': dues_data,
            'total_with_dues': len(students_with_dues)
        })
        
    except Exception as e:
        return JsonResponse({'error': 'Failed to load statistics', 'details': sanitize_input(str(e))}, status=500)


@login_required
@csrf_protect
@module_required('students', 'edit')
@require_http_methods(["POST"])
def bulk_update_dues_api(request):
    """API endpoint for bulk updating due amounts"""
    try:
        data = json.loads(request.body)
        student_ids = data.get('student_ids', [])
        amount = data.get('amount')
        
        if not student_ids or not isinstance(student_ids, list):
            return JsonResponse({'error': 'Invalid student IDs'}, status=400)
        
        try:
            amount = Decimal(str(amount))
        except (ValueError, TypeError):
            return JsonResponse({'error': 'Invalid amount'}, status=400)
        
        if amount < 0:
            return JsonResponse({'error': 'Amount cannot be negative'}, status=400)
        
        valid_ids = []
        for sid in student_ids:
            try:
                valid_ids.append(int(sid))
            except (ValueError, TypeError):
                continue
        
        if not valid_ids:
            return JsonResponse({'error': 'No valid student IDs provided'}, status=400)
        
        updated_count = StudentService.bulk_update_due_amounts(valid_ids, amount, request.user)
        
        return JsonResponse({
            'success': True,
            'updated_count': updated_count,
            'message': f'Successfully updated due amounts for {updated_count} students'
        })
        
    except json.JSONDecodeError:
        return JsonResponse({'error': 'Invalid JSON data'}, status=400)
    except Exception as e:
        return JsonResponse({'error': 'Bulk update failed', 'details': sanitize_input(str(e))}, status=500)


@login_required
@module_required('students', 'view')
@require_http_methods(["GET"])
def validate_admission_number_api(request):
    """API endpoint to validate admission number uniqueness"""
    try:
        admission_number = request.GET.get('admission_number', '').strip()
        student_id = request.GET.get('student_id')
        
        if not admission_number:
            return JsonResponse({'valid': False, 'message': 'Admission number is required'})
        
        clean_admission = sanitize_input(admission_number.upper())
        
        import re
        if not re.match(r'^[A-Z0-9]{3,20}$', clean_admission):
            return JsonResponse({'valid': False, 'message': 'Admission number must be 3-20 alphanumeric characters'})
        
        existing = Student.objects.filter(admission_number=clean_admission)
        
        if student_id:
            try:
                existing = existing.exclude(id=int(student_id))
            except (ValueError, TypeError):
                pass
        
        if existing.exists():
            return JsonResponse({'valid': False, 'message': 'This admission number is already taken'})
        
        return JsonResponse({'valid': True, 'message': 'Admission number is available'})
        
    except Exception as e:
        return JsonResponse({'valid': False, 'message': 'Validation failed. Please try again.'}, status=500)


@login_required
@module_required('students', 'view')
@require_http_methods(["GET"])
def student_quick_info_api(request, student_id):
    """API endpoint for quick student information"""
    try:
        student_id = int(student_id)
        
        student = Student.objects.select_related('class_section').only(
            'id', 'admission_number', 'first_name', 'last_name',
            'mobile_number', 'email', 'student_image', 'due_amount',
            'class_section__class_name', 'class_section__section_name'
        ).get(id=student_id)
        
        financial = student.financial_summary
        
        return JsonResponse({
            'success': True,
            'data': {
                'id': student.id,
                'admission_number': student.admission_number,
                'name': f"{student.first_name} {student.last_name}",
                'class': student.class_section.class_name if student.class_section else 'N/A',
                'section': student.class_section.section_name if student.class_section else 'N/A',
                'mobile': student.mobile_number,
                'email': student.email,
                'photo': student.student_image.url if student.student_image and student.student_image.url else None,
                'due_amount': str(student.due_amount or 0),
                'total_outstanding': str(financial.get('total_outstanding', 0)),
                'attendance_percentage': student.attendance_percentage
            }
        })
        
    except Student.DoesNotExist:
        return JsonResponse({'error': 'Student not found'}, status=404)
    except (ValueError, TypeError):
        return JsonResponse({'error': 'Invalid student ID'}, status=400)
    except Exception as e:
        return JsonResponse({'error': 'Failed to load student information', 'details': sanitize_input(str(e))}, status=500)


@login_required
@module_required('students', 'view')
@require_http_methods(["GET"])
def student_payments_api(request, admission_number):
    """Legacy API for student payments"""
    try:
        student = Student.objects.get(admission_number=admission_number)
        payments = student.fee_deposits.all()[:10]
        
        data = [{
            'date': p.deposit_date.strftime('%Y-%m-%d'),
            'amount': str(p.paid_amount),
            'receipt': p.receipt_no
        } for p in payments]
        
        return JsonResponse({'payments': data})
    except Student.DoesNotExist:
        return JsonResponse({'error': 'Student not found'}, status=404)
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)


@login_required
@module_required('students', 'view')
@require_http_methods(["GET"])
def student_transport_api(request, admission_number):
    """Legacy API for student transport"""
    try:
        student = Student.objects.get(admission_number=admission_number)
        return JsonResponse({
            'transport': {
                'route': 'Not assigned',
                'stop': 'Not assigned',
                'fee': '0'
            }
        })
    except Student.DoesNotExist:
        return JsonResponse({'error': 'Student not found'}, status=404)
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)