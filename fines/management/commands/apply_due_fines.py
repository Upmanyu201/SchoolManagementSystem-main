from django.core.management.base import BaseCommand
from django.utils import timezone
from datetime import date
from fines.tasks import process_due_fines
import logging

logger = logging.getLogger(__name__)

class Command(BaseCommand):
    help = 'Apply due fines to student accounts (uses Celery task)'

    def add_arguments(self, parser):
        parser.add_argument(
            '--sync',
            action='store_true',
            help='Run synchronously instead of using Celery',
        )

    def handle(self, *args, **options):
        if options['sync']:
            # Run synchronously for testing
            result = process_due_fines()
            self.stdout.write(self.style.SUCCESS(result))
        else:
            # Use Celery task
            task = process_due_fines.delay()
            self.stdout.write(
                self.style.SUCCESS(f'Fine processing task queued: {task.id}')
            )