from django.core.management.base import BaseCommand
from django.core.management import call_command
from datetime import date
import logging

logger = logging.getLogger(__name__)

class Command(BaseCommand):
    help = 'Run daily tasks for fees and fines processing'

    def handle(self, *args, **options):
        today = date.today()
        self.stdout.write(f'Running daily tasks for {today}')
        
        try:
            # Apply due fines
            self.stdout.write('Applying due fines...')
            call_command('apply_due_fines')
            
            # Update student fee amounts
            self.stdout.write('Updating student fee amounts...')
            call_command('apply_due_fees')
            
            self.stdout.write(
                self.style.SUCCESS('Daily tasks completed successfully')
            )
            
        except Exception as e:
            self.stdout.write(
                self.style.ERROR(f'Error running daily tasks: {str(e)}')
            )
            logger.error(f'Daily tasks error: {str(e)}')