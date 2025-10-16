# students/dashboard_views.py

from django.shortcuts import render, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.views.decorators.http import require_http_methods
from django.contrib import messages
from students.models import Student
from students.services import StudentDashboardService
from core.fee_calculation_engine import fee_engine
import logging

logger = logging.getLogger(__name__)

@login_required
def student_dashboard(request, admission_number):
    """Enhanced student dashboard with complete fee integration"""
    try:
        student = get_object_or_404(Student, admission_number=admission_number)
        
        # Get complete dashboard data using service
        dashboard_data = StudentDashboardService.get_complete_dashboard_data(student)
        
        context = {
            'student': student,
            'dashboard_data': dashboard_data,
            'title': f'Dashboard - {student.get_full_display_name()}'
        }
        
        return render(request, 'students/dashboard.html', context)
        
    except Exception as e:
        logger.error(f'Error loading dashboard for {admission_number}: {str(e)}')
        messages.error(request, 'Error loading student dashboard')
        return render(request, 'students/dashboard_error.html')

@login_required
def student_financial_overview(request, admission_number):
    """Detailed financial overview page"""
    try:
        student = get_object_or_404(Student, admission_number=admission_number)
        
        # Get detailed fee breakdown
        fee_summary = fee_engine.get_student_fee_summary(student)
        dashboard_summary = fee_engine.get_dashboard_summary(student)
        
        # Get payment history
        from student_fees.models import FeeDeposit
        payment_history = FeeDeposit.objects.filter(
            student=student
        ).select_related('fees_type', 'fees_group').order_by('-deposit_date')[:20]
        
        # Get unpaid fines
        unpaid_fines = []
        try:
            from fines.models import FineStudent
            unpaid_fines = FineStudent.objects.filter(
                student=student,
                is_paid=False
            ).select_related('fine', 'fine__fine_type')
        except ImportError:
            pass
        
        context = {
            'student': student,
            'fee_breakdown': fee_summary,
            'financial_overview': dashboard_summary['financial_overview'],
            'payment_history': payment_history,
            'unpaid_fines': unpaid_fines,
            'title': f'Financial Overview - {student.get_full_display_name()}'
        }
        
        return render(request, 'students/financial_overview.html', context)
        
    except Exception as e:
        logger.error(f'Error loading financial overview for {admission_number}: {str(e)}')
        messages.error(request, 'Error loading financial overview')
        return render(request, 'students/dashboard_error.html')

# API Endpoints for Dashboard
@login_required
@require_http_methods(["GET"])
def dashboard_api(request, admission_number):
    """API endpoint for dashboard data"""
    try:
        student = get_object_or_404(Student, admission_number=admission_number)
        dashboard_data = StudentDashboardService.get_complete_dashboard_data(student)
        
        return JsonResponse({
            'success': True,
            'data': dashboard_data
        })
        
    except Exception as e:
        logger.error(f'Error in dashboard API for {admission_number}: {str(e)}')
        return JsonResponse({
            'success': False,
            'error': str(e)
        }, status=500)

@login_required
@require_http_methods(["GET"])
def financial_summary_api(request, admission_number):
    """API endpoint for financial summary"""
    try:
        student = get_object_or_404(Student, admission_number=admission_number)
        summary = fee_engine.get_dashboard_summary(student)
        
        return JsonResponse({
            'success': True,
            'data': summary
        })
        
    except Exception as e:
        logger.error(f'Error in financial summary API for {admission_number}: {str(e)}')
        return JsonResponse({
            'success': False,
            'error': str(e)
        }, status=500)

@login_required
@require_http_methods(["POST"])
def refresh_financial_data(request, admission_number):
    """Refresh and recalculate financial data"""
    try:
        student = get_object_or_404(Student, admission_number=admission_number)
        
        # Update financial status
        StudentDashboardService.update_student_financial_status(student)
        
        # Get updated data
        updated_data = StudentDashboardService.get_complete_dashboard_data(student)
        
        return JsonResponse({
            'success': True,
            'message': 'Financial data refreshed successfully',
            'data': updated_data
        })
        
    except Exception as e:
        logger.error(f'Error refreshing financial data for {admission_number}: {str(e)}')
        return JsonResponse({
            'success': False,
            'error': str(e)
        }, status=500)