from django.core.management.base import BaseCommand
from fines.tasks import cleanup_old_fines
import logging

logger = logging.getLogger(__name__)

class Command(BaseCommand):
    help = 'Clean up old paid fines and audit logs'

    def add_arguments(self, parser):
        parser.add_argument(
            '--sync',
            action='store_true',
            help='Run synchronously instead of using Celery',
        )

    def handle(self, *args, **options):
        if options['sync']:
            result = cleanup_old_fines()
            self.stdout.write(self.style.SUCCESS(result))
        else:
            task = cleanup_old_fines.delay()
            self.stdout.write(
                self.style.SUCCESS(f'Cleanup task queued: {task.id}')
            )