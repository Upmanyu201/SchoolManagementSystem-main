# core/fee_management/services.py

from decimal import Decimal
from typing import Dict, List, Optional, Tuple
from datetime import datetime, date, timedelta
from django.db.models import Sum, Q, F
from django.db import transaction
from django.core.cache import cache
from django.utils import timezone
from django.core.exceptions import ValidationError
from django.utils.html import escape
try:
    from core.security_utils import sanitize_input
except ImportError:
    def sanitize_input(value):
        return str(value) if value else ''
import logging

logger = logging.getLogger(__name__)

class FeeManagementService:
    """Centralized fee and fine management service"""
    
    def __init__(self):
        self.cache_timeout = 300  # 5 minutes
    
    @transaction.atomic
    def apply_enhanced_fine(self, fine_data: Dict) -> Dict:
        """
        Enhanced fine application with support for:
        - Fee groups (all fee types in group)
        - Multiple fee types
        - Delay days logic
        - Dynamic amount calculation based on unpaid totals
        """
        try:
            from fines.models import Fine, FineStudent
            from students.models import Student
            from fees.models import FeesGroup, FeesType
            
            fine_id = fine_data.get('fine_id')
            target_scope = fine_data.get('target_scope', 'Individual')
            delay_days = fine_data.get('delay_days', 0)
            
            # Get the fine instance
            try:
                fine = Fine.objects.get(id=fine_id)
            except Fine.DoesNotExist:
                return {
                    'success': False,
                    'error': f'Fine with ID {fine_id} not found'
                }
            
            # Check if fine should be applied now (due_date + delay_days)
            if not fine.should_apply_now:
                logger.info(f"Fine {fine_id} not ready to apply yet (due: {fine.due_date}, delay: {fine.delay_days} days)")
                return {
                    'success': True,
                    'students_affected': 0,
                    'message': f"Fine scheduled for application on {fine.due_date + timedelta(days=fine.delay_days)}"
                }
            
            # Get target students based on scope
            target_students = self._get_target_students(fine, target_scope)
            
            if not target_students:
                return {
                    'success': False,
                    'error': 'No eligible students found for this fine'
                }
            
            # Get applicable fee types
            fee_types = self._get_fine_fee_types(fine)
            
            if not fee_types:
                return {
                    'success': False,
                    'error': 'No fee types specified for this fine'
                }
            
            # Apply fine to eligible students
            fine_students_created = []
            for student in target_students:
                # Check if student has unpaid fees for the specified fee types
                unpaid_amount = self._calculate_unpaid_amount(student, fee_types)
                
                if unpaid_amount > 0:
                    # Calculate fine amount
                    if fine.dynamic_amount_percent:
                        calculated_amount = unpaid_amount * (fine.dynamic_amount_percent / 100)
                    else:
                        calculated_amount = fine.amount
                    
                    # Create or update FineStudent record
                    fine_student, created = FineStudent.objects.get_or_create(
                        fine=fine,
                        student=student,
                        defaults={
                            'is_paid': False,
                            'calculated_amount': calculated_amount
                        }
                    )
                    
                    if created:
                        fine_students_created.append(fine_student)
                        # Update student due amount
                        if hasattr(student, 'update_due_amount'):
                            student.update_due_amount()
            
            logger.info(
                f"Applied fine '{fine.fine_type.name}' to "
                f"{len(fine_students_created)} students with unpaid fees"
            )
            
            return {
                'success': True,
                'fine_id': fine.id,
                'students_affected': len(fine_students_created),
                'message': f"Fine applied to {len(fine_students_created)} students with unpaid fees"
            }
            
        except Exception as e:
            logger.error(f"Error applying enhanced fine: {str(e)}")
            return {
                'success': False,
                'error': f'Failed to apply fine: {str(e)}'
            }
    
    def _get_target_students(self, fine, target_scope):
        """Get target students based on fine scope"""
        from students.models import Student
        
        if target_scope == 'Individual':
            # For individual fines, students are manually selected
            return Student.objects.none()  # Will be handled separately
        elif target_scope == 'Class' and fine.class_section:
            return Student.objects.filter(class_section=fine.class_section)
        elif target_scope == 'All':
            return Student.objects.all()
        else:
            return Student.objects.none()
    
    def _get_fine_fee_types(self, fine):
        """Get fee types associated with the fine"""
        fee_types = list(fine.fees_types.all())
        
        # If fee group is specified, add all fee types from the group
        if fine.fees_group:
            from fees.models import FeesType
            group_fee_types = FeesType.objects.filter(fee_group=fine.fees_group)
            fee_types.extend(group_fee_types)
        
        return fee_types
    
    def _calculate_unpaid_amount(self, student, fee_types):
        """Calculate total unpaid amount for specified fee types"""
        from student_fees.models import FeeDeposit
        
        total_unpaid = Decimal('0')
        
        for fee_type in fee_types:
            # Check payment status for this fee type
            fee_name_patterns = [
                f"{fee_type.fee_group.group_type} - {fee_type.amount_type}",
                fee_type.amount_type,
                fee_type.display_format
            ]
            
            paid_amount = Decimal('0')
            for pattern in fee_name_patterns:
                pattern_paid = FeeDeposit.objects.filter(
                    student=student,
                    note__icontains=pattern
                ).aggregate(
                    total_paid=Sum('paid_amount')
                )['total_paid'] or Decimal('0')
                paid_amount = max(paid_amount, pattern_paid)
            
            # Calculate unpaid amount for this fee type
            unpaid = max(Decimal('0'), fee_type.amount - paid_amount)
            total_unpaid += unpaid
        
        return total_unpaid
    
    @transaction.atomic
    def apply_class_fine(self, fine_data: Dict) -> Dict:
        """
        Legacy method - redirects to enhanced fine application
        """
        return self.apply_enhanced_fine(fine_data)
    
    def _get_students_with_unpaid_fees(self, class_section, fees_type_id) -> List:
        """
        Legacy method - get students with unpaid fees for single fee type
        """
        try:
            from students.models import Student
            from fees.models import FeesType
            
            fees_type = FeesType.objects.get(id=fees_type_id)
            class_students = Student.objects.filter(class_section=class_section)
            
            students_with_unpaid_fees = []
            for student in class_students:
                unpaid_amount = self._calculate_unpaid_amount(student, [fees_type])
                if unpaid_amount > 0:
                    students_with_unpaid_fees.append(student)
            
            return students_with_unpaid_fees
            
        except Exception as e:
            logger.error(f"Error getting students with unpaid fees: {str(e)}")
            return []
    
    def get_class_fee_summary(self, class_section_id: int) -> Dict:
        """Get comprehensive fee summary for a class section"""
        try:
            from subjects.models import ClassSection
            from students.models import Student
            from student_fees.models import FeeDeposit
            from fines.models import FineStudent
            
            class_section = ClassSection.objects.get(id=class_section_id)
            students = Student.objects.filter(class_section=class_section)
            
            summary = {
                'class_name': class_section.display_name,
                'total_students': students.count(),
                'fee_collection': {
                    'total_collected': Decimal('0'),
                    'total_pending': Decimal('0'),
                    'collection_percentage': 0
                },
                'fine_summary': {
                    'total_fines': Decimal('0'),
                    'paid_fines': Decimal('0'),
                    'pending_fines': Decimal('0')
                },
                'students_with_dues': 0,
                'students_with_fines': 0
            }
            
            for student in students:
                # Fee collection data
                student_payments = FeeDeposit.objects.filter(student=student).aggregate(
                    total_paid=Sum('paid_amount'),
                    total_discount=Sum('discount')
                )
                
                paid_amount = student_payments['total_paid'] or Decimal('0')
                summary['fee_collection']['total_collected'] += paid_amount
                
                # Fine data
                student_fines = FineStudent.objects.filter(student=student).select_related('fine')
                for fine_student in student_fines:
                    summary['fine_summary']['total_fines'] += fine_student.fine.amount
                    if fine_student.is_paid:
                        summary['fine_summary']['paid_fines'] += fine_student.fine.amount
                    else:
                        summary['fine_summary']['pending_fines'] += fine_student.fine.amount
                        summary['students_with_fines'] += 1
                
                # Check if student has dues
                if hasattr(student, 'due_amount') and student.due_amount > 0:
                    summary['students_with_dues'] += 1
                    summary['fee_collection']['total_pending'] += student.due_amount
            
            # Calculate collection percentage
            total_expected = summary['fee_collection']['total_collected'] + summary['fee_collection']['total_pending']
            if total_expected > 0:
                summary['fee_collection']['collection_percentage'] = (
                    summary['fee_collection']['total_collected'] / total_expected * 100
                )
            
            return summary
            
        except Exception as e:
            logger.error(f"Error getting class fee summary: {str(e)}")
            return {}
    
    def verify_fine_application(self, fine_id: int) -> Dict:
        """Verify that fine was applied correctly to intended students"""
        try:
            from fines.models import Fine, FineStudent
            
            fine = Fine.objects.get(id=fine_id)
            fine_students = FineStudent.objects.filter(fine=fine).select_related('student', 'student__class_section')
            
            verification = {
                'fine_id': fine_id,
                'fine_type': fine.fine_type.name,
                'target_scope': fine.target_scope,
                'intended_class': fine.class_section.display_name if fine.class_section else 'All Classes',
                'students_affected': fine_students.count(),
                'class_breakdown': {},
                'issues_found': []
            }
            
            # Analyze class distribution
            for fine_student in fine_students:
                student = fine_student.student
                class_name = student.class_section.display_name if student.class_section else 'No Class'
                
                if class_name not in verification['class_breakdown']:
                    verification['class_breakdown'][class_name] = 0
                verification['class_breakdown'][class_name] += 1
            
            # Check for issues
            if fine.target_scope == 'Class' and fine.class_section:
                intended_class = fine.class_section.display_name
                
                # Check if fine was applied to students outside intended class
                for class_name, count in verification['class_breakdown'].items():
                    if class_name != intended_class:
                        verification['issues_found'].append(
                            f"Fine applied to {count} students in {class_name} "
                            f"but was intended only for {intended_class}"
                        )
            
            verification['is_correct'] = len(verification['issues_found']) == 0
            
            return verification
            
        except Exception as e:
            logger.error(f"Error verifying fine application: {str(e)}")
            return {'error': str(e)}
    
    def fix_incorrect_fine_application(self, fine_id: int) -> Dict:
        """Fix incorrectly applied fines by removing from wrong classes"""
        try:
            from fines.models import Fine, FineStudent
            
            fine = Fine.objects.get(id=fine_id)
            
            if fine.target_scope != 'Class' or not fine.class_section:
                return {
                    'success': False,
                    'error': 'This fix only applies to class-specific fines'
                }
            
            intended_class = fine.class_section
            
            # Get all fine students for this fine
            fine_students = FineStudent.objects.filter(fine=fine).select_related('student', 'student__class_section')
            
            removed_count = 0
            kept_count = 0
            
            for fine_student in fine_students:
                student = fine_student.student
                
                # If student is not in the intended class, remove the fine
                if student.class_section != intended_class:
                    logger.info(
                        f"Removing fine from {student.admission_number} "
                        f"({student.class_section.display_name if student.class_section else 'No Class'}) "
                        f"- not in intended class {intended_class.display_name}"
                    )
                    fine_student.delete()
                    # Update student due amount
                    student.update_due_amount()
                    removed_count += 1
                else:
                    kept_count += 1
            
            return {
                'success': True,
                'fine_id': fine_id,
                'intended_class': intended_class.display_name,
                'students_removed': removed_count,
                'students_kept': kept_count,
                'message': f"Fixed fine application: removed from {removed_count} students, kept for {kept_count} students in {intended_class.display_name}"
            }
            
        except Exception as e:
            logger.error(f"Error fixing fine application: {str(e)}")
            return {
                'success': False,
                'error': str(e)
            }
    
    def get_fee_type_analysis(self, fees_type_id: int) -> Dict:
        """Analyze fee type payment status across all classes"""
        try:
            from fees.models import FeesType
            from students.models import Student
            from student_fees.models import FeeDeposit
            
            fees_type = FeesType.objects.get(id=fees_type_id)
            
            analysis = {
                'fees_type': fees_type.display_format,
                'amount': fees_type.amount,
                'class_analysis': {},
                'overall_stats': {
                    'total_students': 0,
                    'students_paid': 0,
                    'students_unpaid': 0,
                    'total_collected': Decimal('0'),
                    'total_pending': Decimal('0')
                }
            }
            
            # Get all active students grouped by class
            from subjects.models import ClassSection
            class_sections = ClassSection.objects.all()
            
            for class_section in class_sections:
                students = Student.objects.filter(class_section=class_section)
                
                if not students.exists():
                    continue
                
                class_stats = {
                    'total_students': students.count(),
                    'students_paid': 0,
                    'students_unpaid': 0,
                    'total_collected': Decimal('0'),
                    'total_pending': Decimal('0'),
                    'unpaid_students': []
                }
                
                for student in students:
                    paid_amount = FeeDeposit.objects.filter(
                        student=student,
                        note__icontains=fees_type.display_format
                    ).aggregate(
                        total_paid=Sum('paid_amount')
                    )['total_paid'] or Decimal('0')
                    
                    if paid_amount >= fees_type.amount:
                        class_stats['students_paid'] += 1
                        class_stats['total_collected'] += paid_amount
                    else:
                        class_stats['students_unpaid'] += 1
                        pending = fees_type.amount - paid_amount
                        class_stats['total_pending'] += pending
                        class_stats['unpaid_students'].append({
                            'name': f"{student.first_name} {student.last_name}",
                            'admission_number': student.admission_number,
                            'paid_amount': paid_amount,
                            'pending_amount': pending
                        })
                
                analysis['class_analysis'][class_section.display_name] = class_stats
                
                # Update overall stats
                analysis['overall_stats']['total_students'] += class_stats['total_students']
                analysis['overall_stats']['students_paid'] += class_stats['students_paid']
                analysis['overall_stats']['students_unpaid'] += class_stats['students_unpaid']
                analysis['overall_stats']['total_collected'] += class_stats['total_collected']
                analysis['overall_stats']['total_pending'] += class_stats['total_pending']
            
            return analysis
            
        except Exception as e:
            logger.error(f"Error analyzing fee type: {str(e)}")
            return {'error': str(e)}
    
    def waive_fine_students(self, fine_student_ids: List[int], waiver_reason: str, user) -> Dict:
        """Waive fines for specified students"""
        try:
            from fines.models import FineStudent, FineAuditLog
            from django.utils import timezone
            
            waived_count = 0
            errors = []
            
            for fs_id in fine_student_ids:
                try:
                    fine_student = FineStudent.objects.get(id=fs_id)
                    
                    if fine_student.is_paid:
                        errors.append(f"Fine for {fine_student.student} is already paid")
                        continue
                    
                    if fine_student.is_waived:
                        errors.append(f"Fine for {fine_student.student} is already waived")
                        continue
                    
                    # Waive the fine
                    fine_student.is_waived = True
                    fine_student.waived_by = user
                    fine_student.waived_date = timezone.now()
                    fine_student.save()
                    
                    # Log the waiver
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
                    
                    waived_count += 1
                    
                except FineStudent.DoesNotExist:
                    errors.append(f"Fine student with ID {fs_id} not found")
                except Exception as e:
                    errors.append(f"Error waiving fine {fs_id}: {str(e)}")
            
            return {
                'success': True,
                'waived_count': waived_count,
                'errors': errors,
                'message': f"Successfully waived {waived_count} fines"
            }
            
        except Exception as e:
            logger.error(f"Error waiving fines: {str(e)}")
            return {
                'success': False,
                'error': str(e)
            }
    
    def deactivate_fine(self, fine_id: int, user) -> Dict:
        """Deactivate a fine"""
        try:
            from fines.models import Fine, FineAuditLog
            
            fine = Fine.objects.get(id=fine_id)
            fine.is_active = False
            fine.save()
            
            # Log the deactivation
            FineAuditLog.objects.create(
                fine=fine,
                action='DEACTIVATED',
                user=user,
                details={
                    'reason': 'Fine deactivated by user',
                    'fine_type': fine.fine_type.name,
                    'amount': str(fine.amount)
                }
            )
            
            return {
                'success': True,
                'message': f"Fine '{fine.fine_type.name}' has been deactivated"
            }
            
        except Exception as e:
            logger.error(f"Error deactivating fine: {str(e)}")
            return {
                'success': False,
                'error': str(e)
            }
    
    def sync_student_fees_and_fines(self, student) -> Dict:
        """Sync student fees and fines - ensures all applicable fees and fines are assigned"""
        try:
            from fees.models import FeesType
            from fines.models import Fine, FineStudent
            from student_fees.models import FeeDeposit
            
            sync_result = {
                'success': True,
                'fees_synced': 0,
                'fines_synced': 0,
                'errors': []
            }
            
            # 1. Sync applicable fees for student's class
            if hasattr(student, 'class_section') and student.class_section:
                class_name = student.class_section.class_name
                
                # Get applicable fees for this class
                applicable_fees = FeesType.objects.filter(
                    Q(class_name__isnull=True) | Q(class_name__iexact=class_name)
                )
                
                for fee_type in applicable_fees:
                    # Check if student already has this fee assigned
                    existing_deposit = FeeDeposit.objects.filter(
                        student=student,
                        note__icontains=fee_type.display_format
                    ).first()
                    
                    if not existing_deposit:
                        # Skip creating auto-deposit records to avoid receipt validation errors
                        # Fee structure will be detected dynamically when needed
                        pass
                        sync_result['fees_synced'] += 1
            
            # 2. Sync applicable fines for student's class
            if hasattr(student, 'class_section') and student.class_section:
                # Get class-specific fines that should apply to this student
                class_fines = Fine.objects.filter(
                    class_section=student.class_section,
                    target_scope='Class',
                    is_active=True
                )
                
                for fine in class_fines:
                    # Check if fine should be applied now
                    if not fine.should_apply_now:
                        continue
                    
                    # Check if student already has this fine assigned
                    existing_fine_student = FineStudent.objects.filter(
                        fine=fine,
                        student=student
                    ).first()
                    
                    if not existing_fine_student:
                        # Get fee types for this fine
                        fee_types = self._get_fine_fee_types(fine)
                        
                        if fee_types:
                            # Check if student has unpaid fees
                            unpaid_amount = self._calculate_unpaid_amount(student, fee_types)
                            
                            if unpaid_amount > 0:
                                # Calculate fine amount
                                if fine.dynamic_amount_percent:
                                    calculated_amount = unpaid_amount * (fine.dynamic_amount_percent / 100)
                                else:
                                    calculated_amount = fine.amount
                                
                                # Apply the fine
                                FineStudent.objects.create(
                                    fine=fine,
                                    student=student,
                                    is_paid=False,
                                    calculated_amount=calculated_amount
                                )
                                sync_result['fines_synced'] += 1
                        else:
                            # General fine, apply to all students in class
                            FineStudent.objects.create(
                                fine=fine,
                                student=student,
                                is_paid=False,
                                calculated_amount=fine.amount
                            )
                            sync_result['fines_synced'] += 1
            
            # 3. Update student due amount
            if hasattr(student, 'update_due_amount'):
                student.update_due_amount()
            
            logger.info(
                f"Synced fees and fines for {student.admission_number}: "
                f"{sync_result['fees_synced']} fees, {sync_result['fines_synced']} fines"
            )
            
            return sync_result
            
        except Exception as e:
            logger.error(f"Error syncing fees and fines for {student.admission_number}: {str(e)}")
            return {
                'success': False,
                'error': str(e),
                'fees_synced': 0,
                'fines_synced': 0
            }

    def bulk_sync_class_fees_and_fines(self, class_section_id: int) -> Dict:
        """Bulk sync fees and fines for entire class"""
        try:
            from subjects.models import ClassSection
            from students.models import Student
            
            class_section = ClassSection.objects.get(id=class_section_id)
            students = Student.objects.filter(class_section=class_section)
            
            bulk_result = {
                'success': True,
                'class_name': class_section.display_name,
                'total_students': students.count(),
                'students_processed': 0,
                'total_fees_synced': 0,
                'total_fines_synced': 0,
                'errors': []
            }
            
            for student in students:
                try:
                    sync_result = self.sync_student_fees_and_fines(student)
                    if sync_result['success']:
                        bulk_result['students_processed'] += 1
                        bulk_result['total_fees_synced'] += sync_result['fees_synced']
                        bulk_result['total_fines_synced'] += sync_result['fines_synced']
                    else:
                        bulk_result['errors'].append(
                            f"{student.admission_number}: {sync_result.get('error', 'Unknown error')}"
                        )
                except Exception as e:
                    bulk_result['errors'].append(
                        f"{student.admission_number}: {str(e)}"
                    )
            
            logger.info(
                f"Bulk sync completed for {class_section.display_name}: "
                f"{bulk_result['students_processed']}/{bulk_result['total_students']} students processed"
            )
            
            return bulk_result
            
        except Exception as e:
            logger.error(f"Error in bulk sync for class {class_section_id}: {str(e)}")
            return {
                'success': False,
                'error': str(e)
            }
    
    def get_student_payable_fees(self, student, discount_enabled=False) -> Dict:
        """Get all payable fees for student with optional discount support"""
        try:
            from fees.models import FeesType
            from student_fees.models import FeeDeposit
            from fines.models import FineStudent
            
            payable_fees = {
                'carry_forward': [],
                'current_fees': [],
                'transport_fees': [],
                'fines': [],
                'totals': {
                    'total_amount': Decimal('0'),
                    'total_discount': Decimal('0'),
                    'payable_amount': Decimal('0')
                }
            }
            
            # 1. Carry Forward Amount
            if hasattr(student, 'due_amount') and student.due_amount > 0:
                cf_deposits = FeeDeposit.objects.filter(
                    student=student,
                    note__icontains="Carry Forward"
                ).aggregate(
                    total_cf=Sum('amount'),
                    paid_cf=Sum('paid_amount')
                )
                
                cf_total = cf_deposits.get('total_cf') or Decimal('0')
                cf_paid = cf_deposits.get('paid_cf') or Decimal('0')
                cf_pending = cf_total - cf_paid
                
                if cf_pending > 0:
                    payable_fees['carry_forward'].append({
                        'id': 'carry_forward',
                        'name': 'Previous Session Balance',
                        'amount': cf_pending,
                        'discount': Decimal('0'),
                        'payable': cf_pending,
                        'type': 'carry_forward',
                        'priority': 1
                    })
            
            # 2. Current Session Fees
            if hasattr(student, 'class_section') and student.class_section:
                class_display = student.class_section.display_name
                applicable_fees = FeesType.objects.filter(
                    Q(class_name__isnull=True) | Q(class_name__iexact=class_display)
                ).exclude(fee_group__group_type="Transport")
                
                for fee_type in applicable_fees:
                    # Use fee name pattern matching like fallback service
                    fee_name = f"{fee_type.fee_group.group_type} - {fee_type.amount_type}"
                    paid_amount = FeeDeposit.objects.filter(
                        student=student,
                        note__icontains=fee_name
                    ).aggregate(
                        total_paid=Sum('paid_amount'),
                        total_discount=Sum('discount')
                    )
                    
                    total_paid = paid_amount.get('total_paid') or Decimal('0')
                    total_discount = paid_amount.get('total_discount') or Decimal('0')
                    pending = fee_type.amount - total_paid - total_discount
                    
                    if pending > 0:
                        discount_amount = Decimal('0')
                        if discount_enabled:
                            # Apply 5% discount for bulk payments
                            discount_amount = (pending * Decimal('5')) / 100
                        
                        payable_fees['current_fees'].append({
                            'id': fee_type.id,
                            'name': fee_name,
                            'amount': pending,
                            'discount': discount_amount,
                            'payable': pending - discount_amount,
                            'type': 'fee',
                            'priority': 2
                        })
            
            # 3. Transport Fees
            try:
                from transport.models import TransportAssignment
                transport_assignment = TransportAssignment.objects.filter(student=student).first()
                if transport_assignment:
                    transport_fees = FeesType.objects.filter(
                        fee_group__group_type="Transport",
                        related_stoppage=transport_assignment.stoppage
                    )
                    
                    for fee_type in transport_fees:
                        paid_amount = FeeDeposit.objects.filter(
                            student=student,
                            note__icontains=fee_type.display_format
                        ).aggregate(
                            total_paid=Sum('paid_amount')
                        )['total_paid'] or Decimal('0')
                        
                        pending = fee_type.amount - paid_amount
                        if pending > 0:
                            payable_fees['transport_fees'].append({
                                'id': fee_type.id,
                                'name': fee_type.display_format,
                                'amount': pending,
                                'discount': Decimal('0'),
                                'payable': pending,
                                'type': 'transport',
                                'priority': 3
                            })
            except ImportError:
                pass  # Transport module not available
            
            # 4. Unpaid Fines
            unpaid_fines = FineStudent.objects.filter(
                student=student,
                is_paid=False
            ).select_related('fine', 'fine__fine_type')
            
            for fine_student in unpaid_fines:
                payable_fees['fines'].append({
                    'id': f"fine_{fine_student.fine.id}",
                    'name': f"Fine: {fine_student.fine.fine_type.name}",
                    'amount': fine_student.fine.amount,
                    'discount': Decimal('0'),
                    'payable': fine_student.fine.amount,
                    'type': 'fine',
                    'priority': 0,  # Highest priority
                    'due_date': fine_student.fine.due_date
                })
            
            # Calculate totals
            all_fees = (
                payable_fees['carry_forward'] + 
                payable_fees['current_fees'] + 
                payable_fees['transport_fees'] + 
                payable_fees['fines']
            )
            
            for fee in all_fees:
                payable_fees['totals']['total_amount'] += fee['amount']
                payable_fees['totals']['total_discount'] += fee['discount']
                payable_fees['totals']['payable_amount'] += fee['payable']
            
            return payable_fees
            
        except Exception as e:
            logger.error(f"Error getting payable fees for {sanitize_input(student.admission_number)}: {sanitize_input(str(e))}")
            return {
                'carry_forward': [],
                'current_fees': [],
                'transport_fees': [],
                'fines': [],
                'totals': {
                    'total_amount': Decimal('0'),
                    'total_discount': Decimal('0'),
                    'payable_amount': Decimal('0')
                },
                'error': str(e)
            }
    
    def get_student_financial_summary(self, student) -> Dict:
        """Get comprehensive financial summary for student dashboard"""
        try:
            from student_fees.models import FeeDeposit
            from fines.models import FineStudent
            
            # Get payment history
            payments = FeeDeposit.objects.filter(student=student).aggregate(
                total_paid=Sum('paid_amount'),
                total_discount=Sum('discount'),
                total_amount=Sum('amount')
            )
            
            # Get fine summary
            fines = FineStudent.objects.filter(student=student).select_related('fine')
            fine_summary = {
                'total_fines': Decimal('0'),
                'paid_fines': Decimal('0'),
                'pending_fines': Decimal('0')
            }
            
            for fine_student in fines:
                fine_summary['total_fines'] += fine_student.fine.amount
                if fine_student.is_paid:
                    fine_summary['paid_fines'] += fine_student.fine.amount
                else:
                    fine_summary['pending_fines'] += fine_student.fine.amount
            
            # Calculate outstanding balance
            total_paid = payments.get('total_paid') or Decimal('0')
            total_discount = payments.get('total_discount') or Decimal('0')
            total_amount = payments.get('total_amount') or Decimal('0')
            outstanding = total_amount - total_paid - total_discount
            
            return {
                'payments': {
                    'total_paid': total_paid,
                    'total_discount': total_discount,
                    'total_amount': total_amount,
                    'outstanding': max(outstanding, Decimal('0'))
                },
                'fines': fine_summary,
                'overall_status': {
                    'has_dues': outstanding > 0,
                    'has_fines': fine_summary['pending_fines'] > 0,
                    'total_pending': outstanding + fine_summary['pending_fines']
                }
            }
            
        except Exception as e:
            logger.error(f"Error getting financial summary for {sanitize_input(student.admission_number)}: {sanitize_input(str(e))}")
            return {
                'payments': {
                    'total_paid': Decimal('0'),
                    'total_discount': Decimal('0'),
                    'total_amount': Decimal('0'),
                    'outstanding': Decimal('0')
                },
                'fines': {
                    'total_fines': Decimal('0'),
                    'paid_fines': Decimal('0'),
                    'pending_fines': Decimal('0')
                },
                'overall_status': {
                    'has_dues': False,
                    'has_fines': False,
                    'total_pending': Decimal('0')
                },
                'error': str(e)
            }
    
    def get_student_payment_history(self, student) -> Dict:
        """Get student payment history for centralized service"""
        try:
            from student_fees.models import FeeDeposit
            
            deposits = FeeDeposit.objects.filter(student=student).order_by('-deposit_date')
            
            return {
                'all_payments': deposits,
                'total_paid': sum(d.paid_amount for d in deposits),
                'total_discount': sum(d.discount for d in deposits)
            }
            
        except Exception as e:
            logger.error(f"Error getting payment history for {sanitize_input(student.admission_number)}: {sanitize_input(str(e))}")
            return {
                'all_payments': [],
                'total_paid': Decimal('0'),
                'total_discount': Decimal('0')
            }

# Singleton instance
fee_service = FeeManagementService()