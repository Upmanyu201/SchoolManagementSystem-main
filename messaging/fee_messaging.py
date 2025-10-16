"""
Fee and Fine SMS Messaging Utilities
"""

import logging
from decimal import Decimal
from django.utils import timezone
from .services import MessagingService
from school_profile.models import SchoolProfile
from django.conf import settings

logger = logging.getLogger(__name__)

class FeeMessagingService:
    def __init__(self):
        self.messaging_service = MessagingService()
        self.school_name = self.get_school_name()
    
    def get_school_name(self):
        """Get school name from profile"""
        try:
            profile = SchoolProfile.objects.first()
            return profile.school_name if profile else "School"
        except:
            return "School"
    
    def get_admin_phone(self):
        """Get admin phone number from messaging config"""
        from .models import MessagingConfig
        try:
            config = MessagingConfig.get_active_config()
            if config and config.sender_phone:
                return config.sender_phone.replace('+91', '').replace('+', '')
        except:
            pass
        return getattr(settings, 'ADMIN_FALLBACK_PHONE', '8210434250')
    
    def send_fine_applied_sms(self, student, fine_amount, fine_description, total_outstanding):
        """Send SMS when fine is applied to student"""
        success_count = 0
        
        # Student message (user-friendly conversational format)
        student_message = (
            f"Important Notice: A fine of Rs.{fine_amount} has been applied to "
            f"{student.first_name} {student.last_name}'s account for {fine_description}. "
            f"Total outstanding amount: Rs.{total_outstanding}. Please pay at your earliest convenience. - {self.school_name}"
        )
        
        # Send to student's registered phone number
        if student.mobile_number:
            try:
                result = self.messaging_service.send_sms(student.mobile_number, student_message)
                if result['success']:
                    logger.info(f"Fine notification SMS sent to student {student.admission_number}: {result.get('message_id')}")
                    success_count += 1
                else:
                    logger.warning(f"Fine SMS failed for student {student.admission_number}: {result.get('error')}")
            except Exception as e:
                logger.error(f"Exception sending fine SMS to student: {str(e)}")
        else:
            logger.info(f"No mobile number registered for student {student.admission_number}")
        
        return success_count > 0
    
    def send_fee_reminder_sms(self, student, outstanding_amount, due_date=None):
        """Send fee reminder SMS"""
        if not student.mobile_number:
            logger.warning(f"No mobile number for student {student.admission_number}")
            return False
        
        if due_date:
            message = (
                f"Friendly Reminder: {student.first_name} {student.last_name}'s fees of "
                f"Rs.{outstanding_amount} are overdue since {due_date.strftime('%d-%m-%Y')}. "
                f"Please pay at your earliest convenience to avoid additional charges. - {self.school_name}"
            )
        else:
            message = (
                f"Fee Reminder: {student.first_name} {student.last_name} has outstanding fees of "
                f"Rs.{outstanding_amount}. Please pay at your earliest convenience. - {self.school_name}"
            )
        
        try:
            result = self.messaging_service.send_sms(student.mobile_number, message)
            
            if result['success']:
                logger.info(f"Reminder SMS sent to {student.admission_number}: {result.get('message_id')}")
            else:
                logger.error(f"Reminder SMS failed for {student.admission_number}: {result.get('error')}")
            
            return result['success']
        except Exception as e:
            logger.error(f"Exception sending reminder SMS: {str(e)}")
            return False
    
    def send_payment_confirmation_sms(self, student, paid_amount, payment_date, receipt_no, payment_mode=None, fee_types=None, fine_amount=None, remaining_amount=None):
        """Send enhanced payment confirmation SMS to both parent and admin"""
        success_count = 0
        
        # Build detailed fee breakdown for parent message
        fee_details = ""
        if fee_types and len(fee_types) > 0:
            if len(fee_types) == 1:
                fee_details = f" for {fee_types[0]}"
            elif len(fee_types) <= 3:
                fee_details = f" for {', '.join(fee_types)}"
            else:
                fee_details = f" for {len(fee_types)} fee types"
        
        # Build parent message (user-friendly conversational format)
        parent_message = (
            f"Great! Payment of Rs.{paid_amount} received for {student.first_name} {student.last_name}"
            f"{fee_details} on {payment_date.strftime('%d-%m-%Y')}. Receipt: {receipt_no}."
        )
        
        if fine_amount and fine_amount > 0:
            parent_message += f" Fine payment Rs.{fine_amount} included."
        
        if remaining_amount is not None:
            if remaining_amount > 0:
                parent_message += f" Outstanding balance: Rs.{remaining_amount}."
            else:
                parent_message += " All fees are now up to date!"
        
        parent_message += f" Thank you! - {self.school_name}"
        
        # Build admin summary message
        admin_message = (
            f"Payment Alert: Rs.{paid_amount} received from {student.first_name} {student.last_name} "
            f"({student.admission_number}) on {payment_date.strftime('%d-%m-%Y')}. Receipt: {receipt_no}."
        )
        
        if payment_mode:
            admin_message += f" Mode: {payment_mode}."
        
        if fine_amount and fine_amount > 0:
            admin_message += f" Fine: Rs.{fine_amount}."
        
        if remaining_amount is not None and remaining_amount > 0:
            admin_message += f" Balance: Rs.{remaining_amount}."
        
        admin_message += f" - {self.school_name}"
        
        # Send to student's registered phone number
        if student.mobile_number:
            try:
                result = self.messaging_service.send_sms(student.mobile_number, parent_message)
                if result['success']:
                    logger.info(f"Payment confirmation SMS sent to student {student.admission_number}: {result.get('message_id')}")
                    success_count += 1
                else:
                    logger.warning(f"Payment SMS failed for student {student.admission_number}: {result.get('error')}")
            except Exception as e:
                logger.error(f"Exception sending student SMS: {str(e)}")
        else:
            logger.info(f"No mobile number registered for student {student.admission_number}")
        
        # Send to admin phone (from Basic Configuration)
        admin_phone = self.get_admin_phone()
        if admin_phone:
            try:
                result = self.messaging_service.send_sms(admin_phone, admin_message)
                if result['success']:
                    logger.info(f"Admin payment notification sent to {admin_phone}: {result.get('message_id')}")
                    success_count += 1
                else:
                    logger.error(f"Admin payment notification failed to {admin_phone}: {result.get('error')}")
            except Exception as e:
                logger.error(f"Exception sending admin SMS: {str(e)}")
        else:
            logger.warning("No admin phone number configured in messaging settings")
        
        # Log summary
        if success_count > 0:
            logger.info(f"Payment notifications sent successfully: {success_count} messages")
        else:
            logger.warning(f"No payment notifications sent for receipt {receipt_no}")
        
        return success_count > 0
    
    def calculate_student_remaining_amount(self, student):
        """Calculate remaining amount for student including all fees, fines, and carry forward"""
        from django.db.models import Sum, Q
        from student_fees.models import FeeDeposit
        from fees.models import FeesType
        from fines.models import FineStudent
        from transport.models import TransportAssignment
        
        try:
            # Get applicable fees for student's class
            class_name = student.class_section.class_name if student.class_section else None
            class_display = student.class_section.display_name if student.class_section else None
            
            applicable_fees = FeesType.objects.filter(
                (Q(class_name__isnull=True) | 
                 Q(class_name__iexact=class_name) |
                 Q(class_name__iexact=class_display)) &
                ~Q(group_type="Transport") &
                ~Q(fee_type="Carry Forward")
            ).aggregate(Sum('amount'))['amount__sum'] or Decimal('0')
            
            # Add transport fees if applicable
            assignment = TransportAssignment.objects.filter(student=student).first()
            if assignment and assignment.stoppage:
                transport_fees = FeesType.objects.filter(
                    group_type="Transport",
                    related_stoppage=assignment.stoppage
                ).aggregate(Sum('amount'))['amount__sum'] or Decimal('0')
                applicable_fees += transport_fees
            
            # Get total payments (excluding fine payments)
            total_paid = FeeDeposit.objects.filter(
                student=student
            ).exclude(
                note__icontains="Fine Payment"
            ).aggregate(Sum('paid_amount'))['paid_amount__sum'] or Decimal('0')
            
            # Get unpaid fines
            unpaid_fines = FineStudent.objects.filter(
                student=student,
                is_paid=False
            ).aggregate(Sum('fine__amount'))['fine__amount__sum'] or Decimal('0')
            
            # Calculate remaining: applicable fees + unpaid fines + carry forward - payments
            student_due = Decimal(str(student.due_amount or 0))
            remaining = applicable_fees + unpaid_fines + student_due - total_paid
            
            return max(remaining, Decimal('0'))
        except Exception as e:
            logger.error(f"Error calculating remaining amount for student {student.admission_number}: {str(e)}")
            return Decimal('0')
    
    def format_fee_types_for_message(self, fee_deposits):
        """Format fee types for SMS message"""
        fee_types = []
        for deposit in fee_deposits:
            if deposit.fees_type:
                fee_types.append(f"{deposit.fees_type.group_type} - {deposit.fees_type.amount_type}")
            elif deposit.note and "Fine Payment" in deposit.note:
                fee_types.append("Fine Payment")
            elif deposit.note and "Carry Forward" in deposit.note:
                fee_types.append("Previous Due")
        
        return fee_types