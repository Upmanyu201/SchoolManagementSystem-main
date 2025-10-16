import os
from celery import Celery
from django.conf import settings

# Set the default Django settings module for the 'celery' program.
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'school_management.settings')

app = Celery('school_management')

# Using a string here means the worker doesn't have to serialize
# the configuration object to child processes.
app.config_from_object('django.conf:settings', namespace='CELERY')

# Load task modules from all registered Django apps.
app.autodiscover_tasks()

# Celery Beat Schedule for automated tasks
app.conf.beat_schedule = {
    'process-due-fines': {
        'task': 'fines.tasks.process_due_fines',
        'schedule': 60.0 * 60 * 24,  # Run daily at midnight
    },
    'send-fine-reminders': {
        'task': 'fines.tasks.send_fine_reminders',
        'schedule': 60.0 * 60 * 24 * 3,  # Run every 3 days
    },
    'cleanup-old-fines': {
        'task': 'fines.tasks.cleanup_old_fines',
        'schedule': 60.0 * 60 * 24 * 7,  # Run weekly
    },
}

app.conf.timezone = 'UTC'

@app.task(bind=True)
def debug_task(self):
    print(f'Request: {self.request!r}')