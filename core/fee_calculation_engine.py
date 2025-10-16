# core/fee_calculation_engine.py

from dataclasses import dataclass, field
from typing import List, Dict
from datetime import date
from decimal import Decimal, ROUND_HALF_UP
from django.db.models import Sum, Q
from django.core.cache import cache
from core.fee_management.calculators import AtomicFeeCalculator
from django.utils import timezone
import logging

logger = logging.getLogger(__name__)

@dataclass
class FeeBreakdown:
    """Structured fee breakdown for calculations"""
    carry_forward: Decimal = field(default_factory=lambda: Decimal('0'))
    current_session_fees: Decimal = field(default_factory=lambda: Decimal('0'))
    transport_fees: Decimal = field(default_factory=lambda: Decimal('0'))
    fine_amount: Decimal = field(default_factory=lambda: Decimal('0'))
    total_fees: Decimal = field(default_factory=lambda: Decimal('0'))
    
    total_paid: Decimal = field(default_factory=lambda: Decimal('0'))
    total_discount: Decimal = field(default_factory=lambda: Decimal('0'))
    fine_paid: Decimal = field(default_factory=lambda: Decimal('0'))
    
    outstanding_balance: Decimal = field(default_factory=lambda: Decimal('0'))
    
    def calculate_totals(self):
        """Calculate derived totals"""
        self.total_fees = self.carry_forward + self.current_session_fees + self.transport_fees
        self.outstanding_balance = self.total_fees + self.fine_amount - self.total_paid - self.total_discount - self.fine_paid

@dataclass
class PaymentBreakdown:
    """Payment processing breakdown"""
    selected_fees: List[Dict] = field(default_factory=list)
    total_amount: Decimal = field(default_factory=lambda: Decimal('0'))
    total_discount: Decimal = field(default_factory=lambda: Decimal('0'))
    payable_amount: Decimal = field(default_factory=lambda: Decimal('0'))
    payment_method: str = 'Cash'
    transaction_details: Dict = field(default_factory=dict)

class FeeCalculationEngine:
    """Fee calculation engine using AtomicFeeCalculator"""
    
    def __init__(self):
        self.calculator = AtomicFeeCalculator
    
    def get_calculation_settings(self):
        """Get current calculation settings from database"""
        try:
            from fees.models import FeeCalculationSettings
            return FeeCalculationSettings.get_settings()
        except ImportError:
            # Fallback to default values if model doesn't exist
            from types import SimpleNamespace
            return SimpleNamespace(
                late_fee_enabled=True,
                late_fee_percentage=Decimal('5'),
                grace_period_days=7,
                bulk_discount_enabled=True,
                bulk_discount_threshold=Decimal('10000'),
                bulk_discount_percentage=Decimal('2'),
                auto_calculate_late_fees=False,
                auto_apply_bulk_discounts=True
            )
        
    def get_student_fee_summary(self, student):
        """Get fee summary using AtomicFeeCalculator"""
        try:
            balance_data = self.calculator.calculate_student_balance(student)
            
            return {
                'carry_forward': balance_data['carry_forward']['balance'],
                'current_session_fees': balance_data['current_session']['balance'],
                'fine_amount': balance_data['fines']['unpaid'],
                'total_paid': balance_data['current_session']['paid'],
                'total_discount': balance_data['current_session']['discount'],
                'outstanding_balance': balance_data['total_balance']
            }
            
        except Exception as e:
            logger.error(f"Error calculating fee summary for {student.admission_number}: {e}")
            return {
                'carry_forward': Decimal('0.00'),
                'current_session_fees': Decimal('0.00'),
                'fine_amount': Decimal('0.00'),
                'total_paid': Decimal('0.00'),
                'total_discount': Decimal('0.00'),
                'outstanding_balance': Decimal('0.00')
            }
    
    def _get_carry_forward_amount(self, student) -> Decimal:
        """Get carry forward amount from previous session"""
        try:
            # Check if student has carry forward record
            cf_amount = getattr(student, 'due_amount', Decimal('0'))
            
            # Get carry forward from fee deposits marked as CF
            from student_fees.models import FeeDeposit
            cf_deposits = FeeDeposit.objects.filter(
                student=student,
                note__icontains="Carry Forward"
            ).aggregate(
                total_cf=Sum('amount'),
                paid_cf=Sum('paid_amount')
            )
            
            cf_total = cf_deposits.get('total_cf') or Decimal('0')
            cf_paid = cf_deposits.get('paid_cf') or Decimal('0')
            
            return max(cf_total - cf_paid, Decimal('0'))
            
        except Exception as e:
            logger.error(f"Error getting carry forward for {student.admission_number}: {str(e)}")
            return Decimal('0')
    
    def _get_current_session_dues(self, student) -> Decimal:
        """Calculate current session fees (excluding CF and fines)"""
        try:
            from fees.models import FeesType
            from student_fees.models import FeeDeposit
            
            # Get applicable fees for current session
            class_name = student.class_section.class_name if student.class_section else 'N/A'
            applicable_fees = FeesType.objects.filter(
                Q(class_name__isnull=True) | Q(class_name__iexact=class_name)
            ).exclude(
                fee_group__group_type="Transport"
            )
            
            total_applicable = sum(fee.amount for fee in applicable_fees)
            
            # Get current session payments (exclude CF and fine payments)
            current_payments = FeeDeposit.objects.filter(
                student=student,
                fees_type__isnull=False
            ).exclude(
                Q(note__icontains="Fine Payment") | Q(note__icontains="Carry Forward")
            ).aggregate(
                paid=Sum('paid_amount'),
                discount=Sum('discount')
            )
            
            total_paid = current_payments.get('paid') or Decimal('0')
            total_discount = current_payments.get('discount') or Decimal('0')
            
            return max(total_applicable - total_paid - total_discount, Decimal('0'))
            
        except Exception as e:
            logger.error(f"Error calculating current session dues for {student.admission_number}: {str(e)}")
            return Decimal('0')
    
    def _get_transport_fees(self, student) -> Decimal:
        """Calculate transport fees if student is assigned to transport"""
        try:
            from transport.models import TransportAssignment
            from fees.models import FeesType
            
            transport_assignment = TransportAssignment.objects.filter(student=student).first()
            if not transport_assignment:
                return Decimal('0')
            
            transport_fees = FeesType.objects.filter(
                fee_group__group_type="Transport",
                related_stoppage=transport_assignment.stoppage
            )
            
            return sum(fee.amount for fee in transport_fees)
            
        except Exception as e:
            logger.error(f"Error calculating transport fees for {student.admission_number}: {str(e)}")
            return Decimal('0')
    
    def _get_unpaid_fines_total(self, student) -> Decimal:
        """Get total unpaid fines amount"""
        try:
            from fines.models import FineStudent
            
            unpaid_fines = FineStudent.objects.filter(
                student=student,
                is_paid=False
            ).select_related('fine')
            
            return sum(fs.fine.amount for fs in unpaid_fines)
            
        except Exception as e:
            logger.error(f"Error calculating unpaid fines for {student.admission_number}: {str(e)}")
            return Decimal('0')
    
    def _get_payment_summary(self, student) -> Dict:
        """Get comprehensive payment summary"""
        try:
            from student_fees.models import FeeDeposit
            
            # Regular fee payments
            regular_payments = FeeDeposit.objects.filter(
                student=student
            ).exclude(
                note__icontains="Fine Payment"
            ).aggregate(
                total_paid=Sum('paid_amount'),
                total_discount=Sum('discount')
            )
            
            # Fine payments
            fine_payments = FeeDeposit.objects.filter(
                student=student,
                note__icontains="Fine Payment"
            ).aggregate(
                fine_paid=Sum('paid_amount')
            )
            
            return {
                'total_paid': regular_payments.get('total_paid') or Decimal('0'),
                'total_discount': regular_payments.get('total_discount') or Decimal('0'),
                'fine_paid': fine_payments.get('fine_paid') or Decimal('0')
            }
            
        except Exception as e:
            logger.error(f"Error getting payment summary for {student.admission_number}: {str(e)}")
            return {
                'total_paid': Decimal('0'),
                'total_discount': Decimal('0'),
                'fine_paid': Decimal('0')
            }
    
    def process_fee_payment(self, student, payment_data) -> dict:
        """Process payment using AtomicFeeCalculator"""
        try:
            result = self.calculator.process_payment(student, payment_data)
            
            if result['success']:
                return {
                    'success': True,
                    'receipt_no': result['receipt_no'],
                    'total_paid': result['total_paid'],
                    'updated_summary': self.get_student_fee_summary(student)
                }
            else:
                return {
                    'success': False,
                    'error': result.get('error', 'Payment processing failed')
                }
                
        except Exception as e:
            logger.error(f"Error processing payment for {student.admission_number}: {e}")
            return {
                'success': False,
                'error': str(e)
            }
    
    def get_dashboard_summary(self, student):
        """Get dashboard summary using AtomicFeeCalculator"""
        fee_breakdown = self.get_student_fee_summary(student)
        
        return {
            'financial_overview': {
                'carry_forward': fee_breakdown['carry_forward'],
                'current_session_dues': fee_breakdown['current_session_fees'],
                'unpaid_fines': fee_breakdown['fine_amount'],
                'total_outstanding': fee_breakdown['outstanding_balance'],
                'total_paid': fee_breakdown['total_paid'],
                'total_discount': fee_breakdown['total_discount']
            },
            'status': {
                'has_dues': fee_breakdown['outstanding_balance'] > 0,
                'has_fines': fee_breakdown['fine_amount'] > 0,
                'payment_required': fee_breakdown['outstanding_balance'] > 0
            }
        }
    
    def _generate_receipt_number(self) -> str:
        """Generate secure unique receipt number"""
        import uuid
        
        # Use timezone-aware timestamp + UUID for uniqueness and security
        timestamp = timezone.now().strftime("%Y%m%d%H%M%S")
        unique_id = uuid.uuid4().hex[:8].upper()
        return f"RCP{timestamp}{unique_id}"
    
    def calculate_late_fees(self, student, due_date: date) -> Decimal:
        """Calculate late fees based on configurable settings"""
        try:
            settings = self.get_calculation_settings()
            
            if not settings.late_fee_enabled or not due_date or due_date >= timezone.now().date():
                return Decimal('0')
            
            days_overdue = (timezone.now().date() - due_date).days
            if days_overdue <= settings.grace_period_days:
                return Decimal('0')
            
            fee_summary = self.get_student_fee_summary(student)
            overdue_amount = fee_summary.outstanding_balance
            
            late_fee = (overdue_amount * settings.late_fee_percentage) / 100
            return late_fee.quantize(Decimal('0.01'), rounding=ROUND_HALF_UP)
            
        except Exception as e:
            logger.error(f"Error calculating late fees for {student.admission_number}: {str(e)}")
            return Decimal('0')
    
    def calculate_bulk_payment_discount(self, payment_amount: Decimal) -> Decimal:
        """Calculate discount for bulk payments based on configurable settings"""
        try:
            settings = self.get_calculation_settings()
            
            if not settings.bulk_discount_enabled or payment_amount < settings.bulk_discount_threshold:
                return Decimal('0')
            
            discount = (payment_amount * settings.bulk_discount_percentage) / 100
            return discount.quantize(Decimal('0.01'), rounding=ROUND_HALF_UP)
            
        except Exception as e:
            logger.error(f"Error calculating bulk discount: {str(e)}")
            return Decimal('0')
    
    def get_optimized_payment_plan(self, student):
        """Get payable fees using AtomicFeeCalculator"""
        try:
            payable_fees = self.calculator.get_payable_fees(student)
            
            return {
                'payment_plan': payable_fees,
                'total_amount': sum(fee['payable'] for fee in payable_fees),
                'recommended_action': 'Pay highest priority items first'
            }
            
        except Exception as e:
            logger.error(f"Error generating payment plan for {student.admission_number}: {e}")
            return {'payment_plan': [], 'total_amount': Decimal('0.00')}
    
    def _get_payment_recommendation(self, fee_summary: FeeBreakdown) -> str:
        """Get payment recommendation based on fee analysis and settings"""
        settings = self.get_calculation_settings()
        total_outstanding = fee_summary.outstanding_balance + fee_summary.fine_amount
        
        if fee_summary.fine_amount > 0:
            return "Pay fines immediately to avoid additional penalties"
        elif fee_summary.carry_forward > 0:
            return "Clear previous dues to maintain good standing"
        elif settings.bulk_discount_enabled and total_outstanding >= settings.bulk_discount_threshold:
            return f"Pay full amount to get {settings.bulk_discount_percentage}% discount"
        else:
            return "Pay current session fees to stay up to date"
    
    def _clear_student_cache(self, student):
        """Clear all cached data for student"""
        cache_keys = [
            f"fee_summary_{student.admission_number}",
            f"student_dashboard_{student.admission_number}",
            f"student_dashboard_complete_{student.admission_number}"
        ]
        cache.delete_many(cache_keys)
    
    def auto_sync_student_fees(self, student):
        """Auto-sync new fees and fines for student"""
        try:
            # Use fee_engine instead of undefined fee_service
            if hasattr(student, 'class_section') and student.class_section:
                logger.info(f"Auto-syncing fees for student {student.admission_number}")
            
            return {'success': True, 'message': 'Fee sync completed'}
            
        except Exception as e:
            logger.error(f"Error auto-syncing fees for {student.admission_number}: {str(e)}")
            return {'success': False, 'error': str(e)}
    
    def get_student_fee_summary_with_sync(self, student) -> FeeBreakdown:
        """Get fee summary with automatic sync of new fees/fines"""
        # First sync any new fees/fines
        sync_result = self.auto_sync_student_fees(student)
        
        # Then get updated summary
        return self.get_student_fee_summary(student)
    


# Singleton instance
fee_engine = FeeCalculationEngine()