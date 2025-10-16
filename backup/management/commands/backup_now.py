from django.core.management.base import BaseCommand
from django.utils import timezone
from django.conf import settings
from django.core.management import call_command
import os
from backup.views import backups_dir, compute_checksum_and_size
from backup.models import BackupJob

class Command(BaseCommand):
    help = 'Create a backup now (optionally by type) and record a BackupJob.'

    def add_arguments(self, parser):
        parser.add_argument('--type', dest='backup_type', default='full', help='Backup type: full|students|financial|teachers')
        parser.add_argument('--name', dest='backup_name', default='', help='Custom name prefix for the backup file')

    def handle(self, *args, **options):
        backup_type = options['backup_type']
        name = options['backup_name'].strip()
        now = timezone.now()
        file_name = f"{name + '_' if name else ''}full_backup_{now.strftime('%Y%m%d_%H%M%S')}.json"
        bdir = backups_dir()
        os.makedirs(bdir, exist_ok=True)
        path = os.path.join(bdir, file_name)

        apps_map = {
            'full': [
                "core","school_profile","teachers","subjects","students","transport","student_fees","fees","fines","attendance","promotion","reports"
            ],
            'students': ['students', 'student_fees', 'fines', 'core'],
            'financial': ['fees', 'student_fees', 'fines', 'reports'],
            'teachers': ['teachers', 'subjects', 'attendance', 'core']
        }
        apps = apps_map.get(backup_type, apps_map['full'])
        with open(path, 'w', encoding='utf-8') as f:
            call_command('dumpdata', *apps, format='json', indent=2, stdout=f)
        checksum, size = compute_checksum_and_size(path)
        job = BackupJob.objects.create(
            status='success',
            file_path=path,
            format='json',
            checksum=checksum,
            size_bytes=size,
            report_json={
                'created_at': now.strftime('%d/%m/%Y: %H:%M:%S'),
                'message': 'Backup created via management command',
                'apps': apps
            }
        )
        self.stdout.write(self.style.SUCCESS(f"Backup created: {path} (job id {job.id})"))
