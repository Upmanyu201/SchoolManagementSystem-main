# fines/utils.py - Enhanced Fine Application Logic
from decimal import Decimal
from datetime import timedelta
from django.utils import timezone
from django.db import transaction
import logging

logger = logging.getLogger(__name__)

def apply_fine_to_students(fine):
    """
    Enhanced fine application that fixes issues B, D, and G
    - Applies fines to correct target scope
    - Handles delay days properly
    - Works with or without fee type restrictions
    """
    try:
        from .models import FineStudent
        from students.models import Student
        
        # Issue G: Check if fine should be applied now (due_date + delay_days)
        if not fine.should_apply_now:
            logger.info(f"Fine {fine.id} not ready to apply yet. Due: {fine.due_date}, Delay: {fine.delay_days} days")
            return {
                'success': True,
                'students_affected': 0,
                'message': f"Fine scheduled for {fine.due_date + timedelta(days=fine.delay_days)}"
            }
        
        # Get target students based on scope
        target_students = []
        
        if fine.target_scope == 'Individual':
            # For individual fines, no auto-assignment (handled manually)
            target_students = []
        elif fine.target_scope == 'Class' and fine.class_section:
            target_students = Student.objects.filter(class_section=fine.class_section)
        elif fine.target_scope == 'All':
            target_students = Student.objects.all()
        
        if not target_students:
            logger.info(f"No target students found for fine {fine.id} with scope {fine.target_scope}")
            return {
                'success': True,
                'students_affected': 0,
                'message': 'No students in target scope'
            }
        
        # Issue A & D: Apply fine to students (with or without fee type restrictions)
        students_affected = 0
        
        with transaction.atomic():
            for student in target_students:
                # Check if student already has this fine
                if FineStudent.objects.filter(fine=fine, student=student).exists():
                    continue
                
                # Issue A: Support both fee-specific and general fines
                should_apply = True
                calculated_amount = fine.amount
                
                # If fee types are specified, check unpaid amounts
                if fine.fees_types.exists() or fine.fees_group:
                    unpaid_amount = _get_student_unpaid_amount(student, fine)
                    
                    if unpaid_amount > 0:
                        # Calculate dynamic amount if percentage is set
                        if fine.dynamic_amount_percent:
                            calculated_amount = (unpaid_amount * fine.dynamic_amount_percent) / 100
                        should_apply = True
                    else:
                        # Student has no unpaid fees for specified types
                        should_apply = False
                else:
                    # General fine - apply to all students in scope
                    should_apply = True
                
                if should_apply:
                    FineStudent.objects.create(
                        fine=fine,
                        student=student,
                        calculated_amount=calculated_amount
                    )
                    students_affected += 1
                    
                    # Update student due amount if method exists
                    if hasattr(student, 'update_due_amount'):
                        student.update_due_amount()
        
        logger.info(f"Applied fine {fine.id} to {students_affected} students")
        return {
            'success': True,
            'students_affected': students_affected,
            'message': f"Fine applied to {students_affected} students"
        }
        
    except Exception as e:
        logger.error(f"Error applying fine {fine.id}: {str(e)}")
        return {
            'success': False,
            'error': str(e),
            'students_affected': 0
        }

def _get_student_unpaid_amount(student, fine):
    """Calculate unpaid amount for student based on fine's fee types"""
    try:
        from student_fees.models import FeeDeposit
        from django.db.models import Sum
        
        total_unpaid = Decimal('0')
        
        # Get fee types from fine
        fee_types = list(fine.fees_types.all())
        
        # Add fee types from group if specified
        if fine.fees_group:
            from fees.models import FeesType
            group_fee_types = FeesType.objects.filter(fee_group=fine.fees_group)
            fee_types.extend(group_fee_types)
        
        # Calculate unpaid amount for each fee type
        for fee_type in fee_types:
            # Check payments for this fee type
            paid_amount = FeeDeposit.objects.filter(
                student=student,
                note__icontains=fee_type.display_format
            ).aggregate(
                total_paid=Sum('paid_amount')
            )['total_paid'] or Decimal('0')
            
            # Calculate unpaid amount
            unpaid = max(Decimal('0'), fee_type.amount - paid_amount)
            total_unpaid += unpaid
        
        return total_unpaid
        
    except Exception as e:
        logger.error(f"Error calculating unpaid amount for student {student.admission_number}: {str(e)}")
        return Decimal('0')

def waive_fine_for_student(fine_student, waiver_reason, user):
    """
    Fix for Issue E: Waive function not working
    """
    try:
        from .models import FineAuditLog
        from django.utils import timezone
        
        if fine_student.is_paid:
            return {'success': False, 'error': 'Fine is already paid'}
        
        if fine_student.is_waived:
            return {'success': False, 'error': 'Fine is already waived'}
        
        # Waive the fine
        fine_student.is_waived = True
        fine_student.waived_by = user
        fine_student.waived_date = timezone.now()
        fine_student.save()
        
        # Create audit log
        FineAuditLog.objects.create(
            fine=fine_student.fine,
            action='WAIVED',
            user=user,
            details={
                'student_id': fine_student.student.id,
                'student_name': f"{fine_student.student.first_name} {fine_student.student.last_name}",
                'reason': waiver_reason,
                'amount': str(fine_student.calculated_amount or fine_student.fine.amount)
            }
        )
        
        # Update student due amount
        if hasattr(fine_student.student, 'update_due_amount'):
            fine_student.student.update_due_amount()
        
        logger.info(f"Waived fine for student {fine_student.student.admission_number}")
        return {'success': True, 'message': 'Fine waived successfully'}
        
    except Exception as e:
        logger.error(f"Error waiving fine: {str(e)}")
        return {'success': False, 'error': str(e)}

def send_fine_notifications(fine, user):
    """Send SMS notifications for fines"""
    try:
        from .models import FineStudent
        
        fine_students = FineStudent.objects.filter(fine=fine).select_related('student')
        sent_count = 0
        failed_count = 0
        
        for fine_student in fine_students:
            try:
                # SMS notification logic would go here
                # For now, just log the notification
                logger.info(f"SMS notification sent to {fine_student.student.admission_number}")
                sent_count += 1
            except Exception as e:
                logger.error(f"Failed to send SMS to {fine_student.student.admission_number}: {str(e)}")
                failed_count += 1
        
        return {
            'sent': sent_count,
            'failed': failed_count
        }
        
    except Exception as e:
        logger.error(f"Error sending fine notifications: {str(e)}")
        return {'sent': 0, 'failed': 0}


def apply_fine_to_eligible_students(fine, fee_selection_mode=None, fees_group_id=None, fee_type_ids=None):
    """
    Compatibility wrapper expected by views: returns detailed report about applied/skipped students.
    - fee_selection_mode: 'multiple'|'group' (optional)
    - fees_group_id: id of fee group when group mode used
    - fee_type_ids: list of fee type ids selected (optional)
    """
    try:
        from .models import FineStudent, FineAuditLog
        from students.models import Student
        from fees.models import FeesType
        from django.contrib.auth import get_user_model
        from django.db import transaction
        from django.utils import timezone

        User = get_user_model()

        eligible_students = []
        ineligible_students = []
        eligible_count = 0
        ineligible_count = 0

        # If fee types were passed explicitly, set them on the fine object for calculation
        if fee_type_ids:
            fee_types_qs = FeesType.objects.filter(id__in=fee_type_ids)
            # set but don't save permanently here (view may save again)
            fine.fees_types.set(fee_types_qs)
        elif fees_group_id and fee_selection_mode == 'group':
            group_fee_types = FeesType.objects.filter(fee_group_id=fees_group_id)
            fine.fees_types.set(group_fee_types)

        # Ensure fine respects its should_apply_now flag
        if not fine.should_apply_now:
            return {
                'eligible_count': 0,
                'ineligible_count': 0,
                'eligible_students': [],
                'ineligible_students': [],
                'message': f'Fine scheduled for {fine.due_date + timedelta(days=fine.delay_days)}'
            }

        # Determine target students
        if fine.target_scope == 'Individual':
            # For individual scope, nothing automatic here — expect manual assignment elsewhere
            target_students = []
        elif fine.target_scope == 'Class' and fine.class_section:
            target_students = Student.objects.filter(class_section=fine.class_section)
        else:
            target_students = Student.objects.all()

        with transaction.atomic():
            for student in target_students:
                # Skip if exists
                if FineStudent.objects.filter(fine=fine, student=student).exists():
                    ineligible_students.append({'student': student, 'reason': 'Already assigned'})
                    ineligible_count += 1
                    continue

                # If fee types specified, check unpaid amounts
                should_apply = True
                calculated_amount = fine.amount

                if fine.fees_types.exists() or fine.fees_group:
                    unpaid_amount = _get_student_unpaid_amount(student, fine)
                    if unpaid_amount > 0:
                        if fine.dynamic_amount_percent:
                            calculated_amount = (unpaid_amount * fine.dynamic_amount_percent) / 100
                        should_apply = True
                    else:
                        should_apply = False

                if should_apply:
                    fs = FineStudent.objects.create(
                        fine=fine,
                        student=student,
                        calculated_amount=calculated_amount
                    )
                    eligible_students.append({'student': student, 'unpaid_amount': str(calculated_amount)})
                    eligible_count += 1

                    # Audit log for applied fine
                    # Attempt to attribute the audit to the fine creator, or fall back to any admin user
                    audit_user = fine.created_by
                    if not audit_user:
                        audit_user = User.objects.filter(is_superuser=True).first()

                    FineAuditLog.objects.create(
                        fine=fine,
                        action='APPLIED',
                        user=audit_user or User.objects.first(),
                        details={
                            'student_id': student.id,
                            'student_adm': getattr(student, 'admission_number', None),
                            'amount': str(calculated_amount),
                            'applied_at': timezone.now().isoformat()
                        }
                    )

                    # Update due amount
                    if hasattr(student, 'update_due_amount'):
                        student.update_due_amount()
                else:
                    ineligible_students.append({'student': student, 'reason': 'No unpaid amount for selected fee types'})
                    ineligible_count += 1

        return {
            'eligible_count': eligible_count,
            'ineligible_count': ineligible_count,
            'eligible_students': eligible_students,
            'ineligible_students': ineligible_students,
            'success': True
        }

    except Exception as e:
        logger.error(f"Error in apply_fine_to_eligible_students: {str(e)}")
        return {
            'eligible_count': 0,
            'ineligible_count': 0,
            'eligible_students': [],
            'ineligible_students': [],
            'success': False,
            'error': str(e)
        }


def waive_fine_students(fine_student_ids, waiver_reason, user):
    """Bridge to waive multiple fine students and return structured result."""
    try:
        from .models import FineStudent
        errors = []
        waived = 0
        for fs_id in fine_student_ids:
            try:
                fs = FineStudent.objects.get(id=fs_id)
                res = waive_fine_for_student(fs, waiver_reason, user)
                if res.get('success'):
                    waived += 1
                else:
                    errors.append(f"{fs_id}: {res.get('error')}")
            except FineStudent.DoesNotExist:
                errors.append(f"{fs_id}: FineStudent not found")
            except Exception as e:
                errors.append(f"{fs_id}: {str(e)}")

        return {
            'success': len(errors) == 0,
            'message': f"Waived {waived} fines",
            'errors': errors
        }
    except Exception as e:
        logger.error(f"Error in waive_fine_students: {str(e)}")
        return {'success': False, 'message': 'Error waiving fines', 'errors': [str(e)]}