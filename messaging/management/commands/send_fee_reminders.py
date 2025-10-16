"""
Django management command to send fee reminders
Usage: python manage.py send_fee_reminders --days 7
"""

from django.core.management.base import BaseCommand
from messaging.fee_reminders import FeeReminderService

class Command(BaseCommand):
    help = 'Send fee reminder SMS to students with overdue payments'
    
    def add_arguments(self, parser):
        parser.add_argument(
            '--days',
            type=int,
            default=7,
            help='Number of days overdue (default: 7)'
        )
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Show what would be sent without actually sending SMS'
        )
    
    def handle(self, *args, **options):
        days_overdue = options['days']
        dry_run = options['dry_run']
        
        reminder_service = FeeReminderService()
        
        if dry_run:
            overdue_students = reminder_service.get_overdue_students(days_overdue)
            self.stdout.write(
                self.style.SUCCESS(
                    f'Found {len(overdue_students)} students with overdue fees (>{days_overdue} days)'
                )
            )
            for student_data in overdue_students:
                student = student_data['student']
                amount = student_data['outstanding_amount']
                self.stdout.write(
                    f'- {student.get_full_display_name()}: ₹{amount}'
                )
        else:
            result = reminder_service.send_fee_reminders(days_overdue)
            self.stdout.write(
                self.style.SUCCESS(
                    f'Fee reminders sent: {result["sent"]} successful, '
                    f'{result["failed"]} failed out of {result["total_overdue"]} overdue students'
                )
            )