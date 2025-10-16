from django.core.management.base import BaseCommand
from django.db import transaction
from django.apps import apps
from django.contrib.auth import get_user_model
import logging

logger = logging.getLogger(__name__)

class Command(BaseCommand):
    help = 'Clear all data from the application while preserving database structure'

    def add_arguments(self, parser):
        parser.add_argument(
            '--confirm',
            action='store_true',
            help='Confirm data deletion',
        )

    def handle(self, *args, **options):
        if not options['confirm']:
            self.stdout.write(
                self.style.WARNING(
                    'This will delete ALL data from the application!\n'
                    'Run with --confirm to proceed: python manage.py clear_all_data --confirm'
                )
            )
            return

        try:
            with transaction.atomic():
                # Get all models
                models_to_clear = []
                
                # Core application models
                for app_config in apps.get_app_configs():
                    if app_config.name in [
                        'students', 'teachers', 'fees', 'student_fees', 
                        'attendance', 'transport', 'messaging', 'subjects',
                        'fines', 'reports', 'promotion', 'backup'
                    ]:
                        for model in app_config.get_models():
                            models_to_clear.append(model)

                # Clear data from each model
                total_deleted = 0
                for model in models_to_clear:
                    count = model.objects.count()
                    if count > 0:
                        model.objects.all().delete()
                        total_deleted += count
                        self.stdout.write(f'Cleared {count} records from {model.__name__}')

                # Clear user data except superusers
                User = get_user_model()
                regular_users = User.objects.filter(is_superuser=False)
                user_count = regular_users.count()
                if user_count > 0:
                    regular_users.delete()
                    total_deleted += user_count
                    self.stdout.write(f'Cleared {user_count} regular user accounts')

                self.stdout.write(
                    self.style.SUCCESS(
                        f'Successfully cleared {total_deleted} total records from the application!'
                    )
                )

        except Exception as e:
            logger.error(f"Error clearing data: {str(e)}")
            self.stdout.write(
                self.style.ERROR(f'Error clearing data: {str(e)}')
            )