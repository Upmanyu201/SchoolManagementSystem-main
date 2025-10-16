from django.core.management.base import BaseCommand
from fines.tasks import send_fine_reminders
import logging

logger = logging.getLogger(__name__)

class Command(BaseCommand):
    help = 'Send SMS reminders for unpaid fines'

    def add_arguments(self, parser):
        parser.add_argument(
            '--sync',
            action='store_true',
            help='Run synchronously instead of using Celery',
        )

    def handle(self, *args, **options):
        if options['sync']:
            result = send_fine_reminders()
            self.stdout.write(self.style.SUCCESS(result))
        else:
            task = send_fine_reminders.delay()
            self.stdout.write(
                self.style.SUCCESS(f'Fine reminder task queued: {task.id}')
            )