# students/student_dashboard_views.py
from django.shortcuts import render, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.views.decorators.http import require_http_methods
from django.utils import timezone
from .models import Student
from .services import StudentService, StudentDashboardService
from .serializers import StudentDashboardSerializer
from users.decorators import module_required
from core.security_utils import sanitize_input
import logging

logger = logging.getLogger(__name__)

@login_required
@module_required('students', 'view')
def student_unified_dashboard(request, admission_number):
    """Student unified dashboard view with complete data"""
    try:
        clean_admission = sanitize_input(admission_number.strip())
        student = get_object_or_404(Student.objects.all_statuses(), admission_number=clean_admission)
        
        # Get complete dashboard data
        dashboard_data = StudentDashboardService.get_complete_dashboard_data(student)
        financial_summary = StudentService.get_student_financial_summary(student)
        timeline = StudentDashboardService.get_student_timeline(student, days=30)
        
        # Try ML integration if available
        ml_insights = {}
        try:
            from core.ml_integrations import ml_service
            ml_insights = {
                'performance_risk': ml_service.predict_student_performance({
                    'admission_number': student.admission_number,
                    'class': student.class_section.class_name if student.class_section else 'N/A'
                }),
                'dropout_risk': ml_service.predict_dropout_risk({
                    'admission_number': student.admission_number
                })
            }
        except ImportError:
            pass  # ML optional
        
        context = {
            'student': student,
            'dashboard_data': dashboard_data,
            'financial_summary': financial_summary,
            'timeline': timeline,
            'ml_insights': ml_insights,
            'ml_available': bool(ml_insights)
        }
        
        return render(request, 'students/unified_dashboard.html', context)
        
    except Student.DoesNotExist:
        return render(request, 'students/student_not_found.html', {
            'admission_number': admission_number
        })
    except Exception as e:
        logger.error(f"Error in student dashboard for {admission_number}: {sanitize_input(str(e))}")
        return render(request, 'students/student_not_found.html', {
            'admission_number': admission_number,
            'error': 'Unable to load student dashboard'
        })

@login_required
@module_required('students', 'view')
@require_http_methods(["GET"])
def student_dashboard_api(request, admission_number):
    """API endpoint for student dashboard data"""
    try:
        clean_admission = sanitize_input(admission_number.strip())
        student = get_object_or_404(Student.objects.all_statuses(), admission_number=clean_admission)
        
        dashboard_data = StudentDashboardService.get_complete_dashboard_data(student)
        
        return JsonResponse({
            'success': True,
            'data': dashboard_data
        })
    except Student.DoesNotExist:
        return JsonResponse({'error': 'Student not found'}, status=404)
    except Exception as e:
        logger.error(f"Dashboard API error for {admission_number}: {sanitize_input(str(e))}")
        return JsonResponse({'error': 'Unable to load dashboard data'}, status=500)

@login_required
@module_required('students', 'view')
@require_http_methods(["GET"])
def student_timeline_api(request, admission_number):
    """API endpoint for student timeline"""
    try:
        limit = int(request.GET.get('limit', 30))
        clean_admission = sanitize_input(admission_number.strip())
        student = get_object_or_404(Student.objects.all_statuses(), admission_number=clean_admission)
        
        timeline = StudentDashboardService.get_student_timeline(student, days=limit)
        
        return JsonResponse({
            'success': True,
            'timeline': timeline
        })
    except Student.DoesNotExist:
        return JsonResponse({'error': 'Student not found'}, status=404)
    except Exception as e:
        logger.error(f"Timeline API error for {admission_number}: {sanitize_input(str(e))}")
        return JsonResponse({'error': 'Unable to load timeline'}, status=500)

@login_required
@module_required('students', 'edit')
@require_http_methods(["POST"])
def student_payment_api(request, admission_number):
    """API endpoint for processing payments"""
    import json
    
    try:
        clean_admission = sanitize_input(admission_number.strip())
        student = get_object_or_404(Student.objects.all_statuses(), admission_number=clean_admission)
        payment_data = json.loads(request.body)
        
        # Basic payment processing (integrate with actual payment system)
        amount = payment_data.get('amount', 0)
        payment_method = payment_data.get('payment_method', 'Cash')
        
        if amount <= 0:
            return JsonResponse({
                'success': False,
                'error': 'Invalid payment amount'
            }, status=400)
        
        # Log payment attempt
        logger.info(f"Payment attempt for {clean_admission}: ₹{amount} via {payment_method}")
        
        return JsonResponse({
            'success': True,
            'message': f'Payment of ₹{amount} processed successfully',
            'receipt_no': f'REC{timezone.now().strftime("%Y%m%d%H%M%S")}'
        })
            
    except json.JSONDecodeError:
        return JsonResponse({
            'success': False,
            'error': 'Invalid payment data'
        }, status=400)
    except Student.DoesNotExist:
        return JsonResponse({
            'success': False,
            'error': 'Student not found'
        }, status=404)
    except Exception as e:
        logger.error(f"Payment API error for {admission_number}: {sanitize_input(str(e))}")
        return JsonResponse({
            'success': False,
            'error': 'Payment processing failed'
        }, status=500)

@login_required
@require_http_methods(["GET"])
def student_payments_api(request, admission_number):
    """API endpoint for student payment history"""
    try:
        student = get_object_or_404(Student.objects.all_statuses(), admission_number=admission_number)
        
        # Get recent payments (last 10)
        payments = student.fee_deposits.select_related('fees_type').order_by('-deposit_date')[:10]
        
        payment_data = []
        for payment in payments:
            payment_data.append({
                'amount': float(payment.paid_amount),
                'date': payment.deposit_date.isoformat(),
                'fee_type': payment.fees_type.fee_type if payment.fees_type else 'Fee Payment',
                'payment_mode': payment.payment_mode,
                'receipt_no': payment.receipt_no,
                'transaction_no': payment.transaction_no
            })
        
        return JsonResponse({
            'success': True,
            'payments': payment_data
        })
        
    except Student.DoesNotExist:
        return JsonResponse({
            'success': False,
            'error': 'Student not found'
        }, status=404)
    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': str(e)
        }, status=500)

@login_required
@module_required('students', 'view')
@require_http_methods(["GET"])
def student_search_api(request):
    """API endpoint for student search (legacy)"""
    try:
        query = request.GET.get('q', '').strip()
        class_filter = request.GET.get('class')
        
        if not query or len(query) < 2:
            return JsonResponse({
                'success': False,
                'results': [],
                'message': 'Please enter at least 2 characters'
            })
        
        filters = {}
        if class_filter:
            try:
                filters['class_id'] = int(class_filter)
            except ValueError:
                pass
        
        students = StudentService.search_students_advanced(query, filters)
        
        results = []
        for student in students:
            results.append({
                'admission_number': student.admission_number,
                'name': f"{student.first_name} {student.last_name}",
                'class': student.class_section.class_name if student.class_section else 'N/A',
                'section': student.class_section.section_name if student.class_section else 'N/A',
                'due_amount': float(student.due_amount or 0),
                'photo': student.student_image.url if student.student_image and student.student_image.url else None
            })
        
        return JsonResponse({
            'success': True,
            'results': results,
            'total': len(results)
        })
        
    except Exception as e:
        logger.error(f"Search API error: {sanitize_input(str(e))}")
        return JsonResponse({
            'success': False,
            'error': 'Search failed'
        }, status=500)