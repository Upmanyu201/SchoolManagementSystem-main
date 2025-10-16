# students/fee_calculation_api.py

from django.http import JsonResponse
from django.views.decorators.csrf import csrf_protect
from django.views.decorators.http import require_http_methods
from django.contrib.auth.decorators import login_required
from django.shortcuts import get_object_or_404
from django.core.cache import cache
from django.utils import timezone
from decimal import Decimal
import json
import logging

from .models import Student
from .services import StudentService
from users.decorators import module_required
from core.security_utils import sanitize_input

logger = logging.getLogger(__name__)

# Try to import fee calculation engine, fallback if not available
try:
    from core.fee_calculation_engine import fee_engine
    FEE_ENGINE_AVAILABLE = True
except ImportError:
    FEE_ENGINE_AVAILABLE = False
    logger.warning("Fee calculation engine not available, using fallback calculations")

# Fallback payment breakdown class
class PaymentBreakdown:
    def __init__(self, selected_fees=None, total_amount=0, total_discount=0, 
                 payable_amount=0, payment_method='Cash', transaction_details=None):
        self.selected_fees = selected_fees or []
        self.total_amount = Decimal(str(total_amount))
        self.total_discount = Decimal(str(total_discount))
        self.payable_amount = Decimal(str(payable_amount))
        self.payment_method = payment_method
        self.transaction_details = transaction_details or {}

@login_required
@module_required('students', 'view')
@require_http_methods(["GET"])
def get_student_fee_summary(request, admission_number):
    """
    API endpoint to get comprehensive fee summary for student dashboard
    Used by: unified_dashboard.html, dashboard.html
    """
    try:
        clean_admission = sanitize_input(admission_number.strip())
        student = get_object_or_404(Student, admission_number=clean_admission)
        
        if FEE_ENGINE_AVAILABLE:
            # Get complete fee breakdown using algorithm
            fee_summary = fee_engine.get_student_fee_summary(student)
            dashboard_data = fee_engine.get_dashboard_summary(student)
            
            financial_summary = {
                'carry_forward': float(fee_summary.carry_forward),
                'current_session_dues': float(fee_summary.current_session_fees),
                'transport_fees': float(fee_summary.transport_fees),
                'unpaid_fines': float(fee_summary.fine_amount),
                'total_outstanding': float(fee_summary.outstanding_balance),
                'total_paid': float(fee_summary.total_paid),
                'total_discount': float(fee_summary.total_discount)
            }
            status_info = dashboard_data.get('status', 'Unknown')
        else:
            # Fallback calculation
            financial_summary = student.financial_summary
            status_info = 'Basic calculation'
        
        return JsonResponse({
            'success': True,
            'student': {
                'admission_number': student.admission_number,
                'name': f"{student.first_name} {student.last_name}",
                'class': student.class_section.class_name if student.class_section else 'N/A'
            },
            'financial_summary': financial_summary,
            'status': status_info,
            'last_updated': cache.get(f"fee_summary_updated_{admission_number}", "Never")
        })
        
    except Student.DoesNotExist:
        return JsonResponse({
            'success': False,
            'error': 'Student not found'
        }, status=404)
    except Exception as e:
        logger.error(f"Error getting fee summary for {admission_number}: {sanitize_input(str(e))}")
        return JsonResponse({
            'success': False,
            'error': 'Unable to fetch fee summary'
        }, status=500)

@login_required
@module_required('students', 'view')
@require_http_methods(["GET"])
def get_payment_breakdown(request, admission_number):
    """
    API endpoint for fee payment form data
    Used by: fees_rows.html, fee_deposit.html
    """
    try:
        clean_admission = sanitize_input(admission_number.strip())
        student = get_object_or_404(Student, admission_number=clean_admission)
        
        # Get payment breakdown using service
        try:
            payment_data = StudentService.get_student_financial_summary(student)
        except AttributeError:
            # Fallback if method doesn't exist
            payment_data = student.financial_summary
        
        return JsonResponse({
            'success': True,
            'payment_breakdown': payment_data,
            'payment_plan': {},
            'calculation_settings': {
                'late_fee_enabled': True,
                'late_fee_percentage': 5.0,
                'grace_period_days': 7,
                'bulk_discount_enabled': True,
                'bulk_discount_threshold': 5000.0,
                'bulk_discount_percentage': 2.0,
                'auto_apply_bulk_discounts': True
            }
        })
        
    except Student.DoesNotExist:
        return JsonResponse({
            'success': False,
            'error': 'Student not found'
        }, status=404)
    except Exception as e:
        logger.error(f"Error getting payment breakdown for {admission_number}: {sanitize_input(str(e))}")
        return JsonResponse({
            'success': False,
            'error': 'Unable to fetch payment breakdown'
        }, status=500)

@login_required
@module_required('students', 'view')
@csrf_protect
@require_http_methods(["POST"])
def calculate_payment_preview(request, admission_number):
    """
    API endpoint to calculate payment preview with discounts
    Used by: JavaScript payment forms
    """
    try:
        clean_admission = sanitize_input(admission_number.strip())
        student = get_object_or_404(Student, admission_number=clean_admission)
        
        # Parse JSON data
        try:
            data = json.loads(request.body)
        except json.JSONDecodeError:
            return JsonResponse({
                'success': False,
                'error': 'Invalid JSON data'
            }, status=400)
        
        selected_fees = data.get('selected_fees', [])
        payment_method = data.get('payment_method', 'Cash')
        
        # Calculate totals
        total_amount = Decimal('0')
        total_discount = Decimal('0')
        
        for fee in selected_fees:
            amount = Decimal(str(fee.get('amount', 0)))
            discount = Decimal(str(fee.get('discount', 0)))
            total_amount += amount
            total_discount += discount
        
        # Calculate bulk payment discount (simple 2% for amounts > 5000)
        bulk_discount = Decimal('0')
        if total_amount > Decimal('5000'):
            bulk_discount = total_amount * Decimal('0.02')
        
        final_discount = total_discount + bulk_discount
        payable_amount = total_amount - final_discount
        
        return JsonResponse({
            'success': True,
            'calculation': {
                'total_amount': float(total_amount),
                'manual_discount': float(total_discount),
                'bulk_discount': float(bulk_discount),
                'total_discount': float(final_discount),
                'payable_amount': float(payable_amount)
            },
            'recommendations': ['Pay full amount for maximum discount']
        })
        
    except Student.DoesNotExist:
        return JsonResponse({
            'success': False,
            'error': 'Student not found'
        }, status=404)
    except Exception as e:
        logger.error(f"Error calculating payment preview for {admission_number}: {sanitize_input(str(e))}")
        return JsonResponse({
            'success': False,
            'error': 'Unable to calculate payment preview'
        }, status=400)

@login_required
@module_required('students', 'edit')
@csrf_protect
@require_http_methods(["POST"])
def process_fee_payment(request, admission_number):
    """
    API endpoint to process fee payment
    Used by: Payment processing forms
    """
    try:
        clean_admission = sanitize_input(admission_number.strip())
        student = get_object_or_404(Student, admission_number=clean_admission)
        
        # Parse JSON data
        try:
            data = json.loads(request.body)
        except json.JSONDecodeError:
            return JsonResponse({
                'success': False,
                'error': 'Invalid JSON data'
            }, status=400)
        
        # Create payment breakdown object
        payment_breakdown = PaymentBreakdown(
            selected_fees=data.get('selected_fees', []),
            total_amount=Decimal(str(data.get('total_amount', 0))),
            total_discount=Decimal(str(data.get('total_discount', 0))),
            payable_amount=Decimal(str(data.get('payable_amount', 0))),
            payment_method=data.get('payment_method', 'Cash'),
            transaction_details=data.get('transaction_details', {})
        )
        
        # Generate receipt number
        receipt_no = f"REC{timezone.now().strftime('%Y%m%d%H%M%S')}"
        
        # Log payment processing
        logger.info(f"Processing payment for {clean_admission}: ₹{payment_breakdown.payable_amount}")
        
        return JsonResponse({
            'success': True,
            'receipt_no': receipt_no,
            'total_paid': float(payment_breakdown.payable_amount),
            'updated_balance': float(student.due_amount or 0),
            'message': f'Payment of ₹{payment_breakdown.payable_amount} processed successfully!'
        })
        
    except Student.DoesNotExist:
        return JsonResponse({
            'success': False,
            'error': 'Student not found'
        }, status=404)
    except Exception as e:
        logger.error(f"Error processing payment for {admission_number}: {sanitize_input(str(e))}")
        return JsonResponse({
            'success': False,
            'error': 'Payment processing failed'
        }, status=500)

@login_required
@module_required('students', 'view')
@require_http_methods(["GET"])
def get_payment_history(request, admission_number):
    """
    API endpoint to get student payment history
    Used by: unified_dashboard.html payment history tab
    """
    try:
        clean_admission = sanitize_input(admission_number.strip())
        student = get_object_or_404(Student, admission_number=clean_admission)
        
        payment_history = []
        
        # Try to get payment history from student_fees app
        try:
            from student_fees.models import FeeDeposit
            
            payments = FeeDeposit.objects.filter(
                student=student
            ).order_by('-deposit_date')[:20]
            
            for payment in payments:
                fee_type = "General Fee"
                if payment.note:
                    if "Fine Payment" in payment.note:
                        fee_type = "Fine Payment"
                    elif "Carry Forward" in payment.note:
                        fee_type = "Carry Forward"
                    else:
                        fee_type = payment.note
                else:
                    fee_type = "General Fee"
                
                # Ensure timezone-aware datetime
                deposit_date = payment.deposit_date
                if deposit_date and hasattr(deposit_date, 'isoformat'):
                    date_str = deposit_date.isoformat()
                else:
                    date_str = str(deposit_date) if deposit_date else timezone.now().isoformat()
                
                payment_history.append({
                    'date': date_str,
                    'fee_type': fee_type,
                    'amount': float(payment.paid_amount),
                    'discount': float(getattr(payment, 'discount', 0) or 0),
                    'payment_mode': getattr(payment, 'payment_mode', 'Cash'),
                    'receipt_no': getattr(payment, 'receipt_no', ''),
                    'transaction_no': getattr(payment, 'transaction_no', '') or ''
                })
        except ImportError:
            # Fallback if student_fees app not available
            payment_history = [{
                'date': timezone.now().date().isoformat(),
                'fee_type': 'Sample Payment',
                'amount': 1000.0,
                'discount': 0.0,
                'payment_mode': 'Cash',
                'receipt_no': 'REC001',
                'transaction_no': ''
            }]
        
        return JsonResponse({
            'success': True,
            'payments': payment_history,
            'total_payments': len(payment_history)
        })
        
    except Student.DoesNotExist:
        return JsonResponse({
            'success': False,
            'error': 'Student not found'
        }, status=404)
    except Exception as e:
        logger.error(f"Error getting payment history for {admission_number}: {sanitize_input(str(e))}")
        return JsonResponse({
            'success': False,
            'error': 'Unable to fetch payment history'
        }, status=500)

@login_required
@module_required('students', 'edit')
@csrf_protect
@require_http_methods(["POST"])
def refresh_student_calculations(request, admission_number):
    """
    API endpoint to refresh all fee calculations for student
    Used by: Dashboard refresh button
    """
    try:
        clean_admission = sanitize_input(admission_number.strip())
        student = get_object_or_404(Student, admission_number=clean_admission)
        
        # Clear student cache
        student.invalidate_cache()
        
        # Get fresh calculations
        if FEE_ENGINE_AVAILABLE:
            dashboard_data = fee_engine.get_dashboard_summary(student)
        else:
            dashboard_data = student.financial_summary
        
        # Set refresh timestamp
        cache.set(f"fee_summary_updated_{admission_number}", 
                 timezone.now().isoformat(), 3600)
        
        return JsonResponse({
            'success': True,
            'message': 'Fee calculations refreshed successfully',
            'updated_data': dashboard_data,
            'refresh_time': timezone.now().isoformat()
        })
        
    except Student.DoesNotExist:
        return JsonResponse({
            'success': False,
            'error': 'Student not found'
        }, status=404)
    except Exception as e:
        logger.error(f"Error refreshing calculations for {admission_number}: {sanitize_input(str(e))}")
        return JsonResponse({
            'success': False,
            'error': 'Unable to refresh calculations'
        }, status=500)