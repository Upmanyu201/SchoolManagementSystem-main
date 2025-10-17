# student_fees/api_views.py
"""API views for student fees - modern REST endpoints"""

from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_protect, csrf_exempt, ensure_csrf_cookie
from django.views.decorators.http import require_POST
from django.shortcuts import get_object_or_404
from django.utils.decorators import method_decorator
from django.middleware.csrf import get_token
from students.models import Student
from .services import FeeCalculationService
from .views import get_student_fees, submit_deposit
import logging

logger = logging.getLogger(__name__)


@method_decorator(csrf_exempt, name='dispatch')
class StudentFeesAPIView(APIView):
    """Modern API for getting student fees"""
    
    def get(self, request):
        """Get student fees by admission number"""
        admission_number = request.GET.get('admission_number')
        discount_enabled = request.GET.get('discount_enabled', 'false').lower() == 'true'
        
        if not admission_number:
            return JsonResponse({
                'status': 'error',
                'message': 'Admission number is required'
            }, status=400)
        
        try:
            student = Student.objects.select_related('class_section').get(
                admission_number=admission_number
            )
            
            # Use centralized service
            payable_fees = FeeCalculationService.get_payable_fees(student)
            
            # Format fees for JavaScript (already in correct format)
            formatted_fees = []
            for fee in payable_fees:
                formatted_fees.append({
                    'id': fee['id'],
                    'display_name': fee['fee_type'],
                    'amount': float(fee['amount']),
                    'due_date': fee.get('due_date', ''),
                    'is_overdue': fee.get('is_overdue', False)
                })
            
            return JsonResponse({
                'status': 'success',
                'data': {
                    'student': {
                        'id': student.id,
                        'name': f"{student.first_name} {student.last_name}",
                        'admission_number': student.admission_number,
                        'class': student.class_section.class_name if student.class_section else None
                    },
                    'payable_fees': formatted_fees
                }
            })
            
        except Student.DoesNotExist:
            return JsonResponse({
                'status': 'error',
                'message': 'Student not found'
            }, status=404)
        except Exception as e:
            logger.error(f"API error: {str(e)}")
            return JsonResponse({
                'status': 'error',
                'message': f'Error loading fees: {str(e)}'
            }, status=500)


@csrf_exempt
def process_payment_api(request):
    """Function-based API for processing payments"""
    if request.method != 'POST':
        return JsonResponse({'status': 'error', 'message': 'Method not allowed'}, status=405)
    
    try:
        import json
        # Handle both JSON and form data
        if request.content_type == 'application/json':
            data = json.loads(request.body)
        else:
            data = request.POST.dict()
        
        student_id = data.get('student_id')
        selected_fees = data.get('selected_fees', [])
        payment_mode = data.get('payment_mode', 'Cash')
        transaction_no = data.get('transaction_no', '')
        payment_source = data.get('payment_source', '')
        
        if not student_id or not selected_fees:
            return JsonResponse({
                'status': 'error',
                'message': 'Student ID and selected fees are required'
            }, status=400)
        
        # Debug log the received data
        logger.info(f"Payment API received data: {data}")
        logger.info(f"Selected fees: {selected_fees}")
        
        # Get student
        from students.models import Student
        from .models import FeeDeposit
        from fees.models import FeesType
        from fines.models import Fine, FineStudent
        from .utils import generate_receipt_no
        from django.utils import timezone as django_timezone
        from decimal import Decimal
        from django.db import transaction
        
        try:
            student = Student.objects.get(id=student_id)
        except Student.DoesNotExist:
            return JsonResponse({
                'status': 'error',
                'message': 'Student not found'
            }, status=404)
        
        # Process payment - handle the correct data format from JavaScript
        total_amount = Decimal('0')
        payment_items = []
        
        if isinstance(selected_fees, list) and len(selected_fees) > 0:
            for fee in selected_fees:
                if isinstance(fee, dict):
                    amount = Decimal(str(fee.get('amount', 0)))
                    discount = Decimal(str(fee.get('discount', 0)))
                    fee_id = fee.get('id')
                    
                    if amount > 0:
                        payment_items.append({
                            'fee_id': fee_id,
                            'amount': amount,
                            'discount': discount,
                            'paid_amount': amount - discount
                        })
                        total_amount += amount - discount
                        logger.info(f"Processing fee: id={fee_id}, amount={amount}, discount={discount}, payable={amount-discount}")
        
        if total_amount < 0:
            logger.warning(f"No valid fees found. Data received: {data}")
            return JsonResponse({
                'status': 'error',
                'message': 'No valid fees selected for payment'
            }, status=400)
        
        # Generate receipt number and save to database
        receipt_no = generate_receipt_no()
        
        try:
            with transaction.atomic():
                # Create FeeDeposit records
                for item in payment_items:
                    fee_id = item['fee_id']
                    amount = item['amount']
                    discount = item['discount']
                    paid_amount = item['paid_amount']
                    
                    if paid_amount < 0:
                        continue
                    
                    # Create deposit based on fee type
                    deposit_data = {
                        'student': student,
                        'amount': amount,
                        'discount': discount,
                        'paid_amount': paid_amount,
                        'receipt_no': receipt_no,
                        'payment_mode': payment_mode,
                        'transaction_no': transaction_no,
                        'payment_source': payment_source,
                        'deposit_date': django_timezone.now()
                    }
                    
                    if fee_id == 'carry_forward':
                        deposit_data.update({
                            'note': 'Carry Forward Payment'
                        })
                    elif str(fee_id).startswith('fine_'):
                        fine_id = fee_id.replace('fine_', '')
                        try:
                            fine = Fine.objects.get(id=fine_id)
                            deposit_data.update({
                                'note': f'Fine Payment: {fine.fine_type.name}'
                            })
                            # Mark fine as paid
                            FineStudent.objects.filter(fine=fine, student=student).update(
                                is_paid=True,
                                payment_date=django_timezone.now().date()
                            )
                        except Fine.DoesNotExist:
                            continue
                    else:
                        try:
                            fee = FeesType.objects.get(id=fee_id)
                            deposit_data['note'] = f'Fee Payment: {fee.fee_group.group_type} - {fee.amount_type}'
                        except FeesType.DoesNotExist:
                            deposit_data['note'] = f'Fee Payment: {fee_id}'
                    
                    FeeDeposit.objects.create(**deposit_data)
                
                logger.info(f"Processed payment: amount={total_amount}, receipt={receipt_no}, fees_count={len(payment_items)}")
                
                # Invalidate dashboard cache after successful payment
                try:
                    from django.core.cache import cache
                    cache.delete('dashboard_stats')
                    cache.set('dashboard_last_update', django_timezone.now().isoformat(), 3600)
                    logger.info("Dashboard cache invalidated after payment")
                except Exception as cache_error:
                    logger.warning(f"Failed to invalidate cache: {cache_error}")
        
        except Exception as e:
            logger.error(f"Error saving payment: {str(e)}")
            return JsonResponse({
                'status': 'error',
                'message': 'Failed to save payment data'
            }, status=500)
        
        return JsonResponse({
            'status': 'success',
            'message': f'Payment of ₹{total_amount:.2f} processed successfully!',
            'data': {
                'receipt_no': receipt_no,
                'amount': total_amount,
                'payment_mode': payment_mode,
                'selected_fees': selected_fees  # Include for debugging
            }
        })
        
    except Exception as e:
        logger.error(f"Payment API error: {str(e)}")
        return JsonResponse({
            'status': 'error',
            'message': f'Payment processing failed: {str(e)}'
        }, status=500)


class StudentBalanceAPIView(APIView):
    """API for getting student balance information"""
    
    def get(self, request, student_id):
        """Get student balance breakdown"""
        try:
            student = get_object_or_404(Student, pk=student_id)
            balance_info = FeeCalculationService.calculate_student_balance(student)
            
            return Response({
                'student_id': student_id,
                'balance_info': balance_info
            })
            
        except Exception as e:
            logger.error(f"Balance API error: {str(e)}")
            return Response({
                'error': 'Failed to get balance information'
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


# Legacy AJAX endpoints for backward compatibility
def get_student_fees_ajax(request):
    """Legacy AJAX endpoint - delegates to main view"""
    return get_student_fees(request)


@require_POST
@csrf_protect
def submit_deposit_ajax(request):
    """Legacy AJAX endpoint - delegates to main view"""
    return submit_deposit(request)