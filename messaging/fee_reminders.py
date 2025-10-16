"""
Fee Reminder Management System
"""

import logging
from datetime import date, timedelta
from django.db.models import Sum, Q
from django.utils import timezone
from students.models import Student
from student_fees.models import FeeDeposit
from fees.models import FeesType
from fines.models import FineStudent
from .fee_messaging import FeeMessagingService

logger = logging.getLogger(__name__)

class FeeReminderService:
    def __init__(self):
        self.messaging_service = FeeMessagingService()
    
    def get_overdue_students(self, days_overdue=7):
        """Get students with overdue fees"""
        overdue_date = date.today() - timedelta(days=days_overdue)
        overdue_students = []
        
        for student in Student.objects.all():
            # Calculate outstanding amount
            outstanding = self.calculate_outstanding_amount(student)
            
            if outstanding > 0:
                # Check if student has any payments in last X days
                recent_payments = FeeDeposit.objects.filter(
                    student=student,
                    deposit_date__date__gte=overdue_date
                ).exists()
                
                if not recent_payments:
                    overdue_students.append({
                        'student': student,
                        'outstanding_amount': outstanding,
                        'days_overdue': days_overdue
                    })
        
        return overdue_students
    
    def calculate_outstanding_amount(self, student):
        """Calculate total outstanding amount for student"""
        # Get applicable fees
        applicable_fees = FeesType.objects.filter(
            Q(class_name__isnull=True) | Q(class_name__iexact=student.student_class.name)
        ).exclude(fee_type="Carry Forward")
        
        total_fees = sum(fee.amount for fee in applicable_fees)
        
        # Get total payments
        total_paid = FeeDeposit.objects.filter(
            student=student
        ).aggregate(Sum('paid_amount'))['paid_amount__sum'] or 0
        
        # Get unpaid fines
        unpaid_fines = FineStudent.objects.filter(
            student=student,
            is_paid=False
        ).aggregate(Sum('fine__amount'))['fine__amount__sum'] or 0
        
        # Add carry forward amount
        cf_amount = student.due_amount or 0
        
        outstanding = total_fees + unpaid_fines + cf_amount - total_paid
        return max(outstanding, 0)
    
    def send_fee_reminders(self, days_overdue=7):
        """Send fee reminder SMS to overdue students"""
        overdue_students = self.get_overdue_students(days_overdue)
        sent_count = 0
        failed_count = 0
        
        for student_data in overdue_students:
            student = student_data['student']
            outstanding = student_data['outstanding_amount']
            
            # Calculate due date (approximate)
            due_date = date.today() - timedelta(days=days_overdue)
            
            success = self.messaging_service.send_fee_reminder_sms(
                student=student,
                outstanding_amount=outstanding,
                due_date=due_date
            )
            
            if success:
                sent_count += 1
            else:
                failed_count += 1
        
        logger.info(f"Fee reminders sent: {sent_count} successful, {failed_count} failed")
        return {
            'sent': sent_count,
            'failed': failed_count,
            'total_overdue': len(overdue_students)
        }
    
    def send_bulk_fee_reminders(self, student_ids=None, custom_message=None):
        """Send bulk fee reminders to specific students"""
        if student_ids:
            students = Student.objects.filter(id__in=student_ids)
        else:
            students = Student.objects.all()
        
        sent_count = 0
        failed_count = 0
        
        for student in students:
            outstanding = self.calculate_outstanding_amount(student)
            
            if outstanding > 0:
                if custom_message:
                    # Send custom message
                    result = self.messaging_service.messaging_service.send_sms(
                        student.mobile_number, 
                        custom_message
                    )
                    success = result['success']
                else:
                    # Send standard reminder
                    success = self.messaging_service.send_fee_reminder_sms(
                        student=student,
                        outstanding_amount=outstanding,
                        due_date=date.today()
                    )
                
                if success:
                    sent_count += 1
                else:
                    failed_count += 1
        
        return {
            'sent': sent_count,
            'failed': failed_count,
            'total_students': students.count()
        }