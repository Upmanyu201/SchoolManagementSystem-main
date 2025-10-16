"""
Management command to set up default backup schedules
"""

from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from backup.models import ScheduledBackup
from backup.scheduler import DEFAULT_SCHEDULES, BackupScheduler

User = get_user_model()


class Command(BaseCommand):
    help = 'Set up default backup schedules'
    
    def add_arguments(self, parser):
        parser.add_argument(
            '--force',
            action='store_true',
            help='Force recreate existing schedules'
        )
        parser.add_argument(
            '--user',
            type=str,
            help='Username to assign as schedule creator'
        )
    
    def handle(self, *args, **options):
        force = options.get('force', False)
        username = options.get('user')
        
        # Get or create system user
        created_by = None
        if username:
            try:
                created_by = User.objects.get(username=username)
            except User.DoesNotExist:
                self.stdout.write(
                    self.style.WARNING(f'User {username} not found, using None')
                )
        
        scheduler = BackupScheduler()
        created_count = 0
        updated_count = 0
        
        for schedule_config in DEFAULT_SCHEDULES:
            name = schedule_config['name']
            
            # Check if schedule exists
            existing = ScheduledBackup.objects.filter(name=name).first()
            
            if existing and not force:
                self.stdout.write(
                    self.style.WARNING(f'Schedule "{name}" already exists, skipping')
                )
                continue
            
            if existing and force:
                # Update existing schedule
                for key, value in schedule_config.items():
                    if key != 'description':  # Don't overwrite description
                        setattr(existing, key, value)
                existing.save()
                
                # Re-register with Celery
                if existing.is_active:
                    scheduler.register_celery_task(existing)
                
                updated_count += 1
                self.stdout.write(
                    self.style.SUCCESS(f'Updated schedule: {name}')
                )
            else:
                # Create new schedule
                schedule = scheduler.create_schedule(
                    name=schedule_config['name'],
                    backup_type=schedule_config['backup_type'],
                    cron_expression=schedule_config['cron_expression'],
                    is_active=True,
                    created_by=created_by
                )
                
                # Add description if provided
                if 'description' in schedule_config:
                    schedule.description = schedule_config['description']
                    schedule.save()
                
                created_count += 1
                self.stdout.write(
                    self.style.SUCCESS(f'Created schedule: {name}')
                )
        
        self.stdout.write(
            self.style.SUCCESS(
                f'Setup complete: {created_count} created, {updated_count} updated'
            )
        )