# Modern Backup Management Command - 2025 Standards
from django.core.management.base import BaseCommand, CommandError
from django.core.management import call_command
from django.conf import settings
from django.utils import timezone
from pathlib import Path
import json
import os
import logging

logger = logging.getLogger('backup.management')

class Command(BaseCommand):
    """
    Management command for backup operations
    
    Usage:
        python manage.py backup_system create --type=full --name=daily_backup
        python manage.py backup_system restore --file=backup.json --mode=merge
        python manage.py backup_system cleanup --days=30
        python manage.py backup_system list
    """
    
    help = 'Manage backup and restore operations'
    
    def add_arguments(self, parser):
        subparsers = parser.add_subparsers(dest='action', help='Available actions')
        
        # Create backup command
        create_parser = subparsers.add_parser('create', help='Create a new backup')
        create_parser.add_argument(
            '--type',
            choices=['full', 'students', 'financial', 'teachers'],
            default='full',
            help='Type of backup to create'
        )
        create_parser.add_argument(
            '--name',
            type=str,
            help='Custom name for the backup (optional)'
        )
        create_parser.add_argument(
            '--output-dir',
            type=str,
            help='Output directory for backup file'
        )
        
        # Restore backup command
        restore_parser = subparsers.add_parser('restore', help='Restore from backup')
        restore_parser.add_argument(
            '--file',
            type=str,
            required=True,
            help='Path to backup file'
        )
        restore_parser.add_argument(
            '--mode',
            choices=['merge', 'replace'],
            default='merge',
            help='Restore mode'
        )
        restore_parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Validate backup without applying changes'
        )
        
        # Cleanup command
        cleanup_parser = subparsers.add_parser('cleanup', help='Clean up old backups')
        cleanup_parser.add_argument(
            '--days',
            type=int,
            default=30,
            help='Delete backups older than N days'
        )
        cleanup_parser.add_argument(
            '--confirm',
            action='store_true',
            help='Skip confirmation prompt'
        )
        
        # List backups command
        list_parser = subparsers.add_parser('list', help='List available backups')
        list_parser.add_argument(
            '--limit',
            type=int,
            default=20,
            help='Number of backups to show'
        )
        
        # Status command
        status_parser = subparsers.add_parser('status', help='Show backup system status')
        
        # Verify command
        verify_parser = subparsers.add_parser('verify', help='Verify backup file integrity')
        verify_parser.add_argument(
            '--file',
            type=str,
            required=True,
            help='Path to backup file to verify'
        )
    
    def handle(self, *args, **options):
        action = options.get('action')
        
        if not action:
            self.print_help('manage.py', 'backup_system')
            return
        
        try:
            if action == 'create':
                self.handle_create(options)
            elif action == 'restore':
                self.handle_restore(options)
            elif action == 'cleanup':
                self.handle_cleanup(options)
            elif action == 'list':
                self.handle_list(options)
            elif action == 'status':
                self.handle_status(options)
            elif action == 'verify':
                self.handle_verify(options)
            else:
                raise CommandError(f"Unknown action: {action}")
                
        except Exception as e:
            logger.error(f"Backup command failed: {e}")
            raise CommandError(f"Operation failed: {e}")
    
    def handle_create(self, options):
        """Handle backup creation"""
        backup_type = options['type']
        custom_name = options.get('name', '')
        output_dir = options.get('output_dir')
        
        self.stdout.write(f"Creating {backup_type} backup...")
        
        # Determine output directory
        if output_dir:
            backup_dir = Path(output_dir)
        else:
            backup_dir = Path(settings.BASE_DIR) / 'backups'
        
        backup_dir.mkdir(exist_ok=True)
        
        # Generate filename
        timestamp = timezone.now().strftime('%Y%m%d_%H%M%S')
        if custom_name:
            filename = f"{custom_name}_{timestamp}.json"
        else:
            filename = f"{backup_type}_backup_{timestamp}.json"
        
        from django.utils._os import safe_join
        backup_path = Path(safe_join(str(backup_dir), filename))
        
        # Define apps to backup
        apps_map = {
            'full': ['core', 'school_profile', 'teachers', 'subjects', 'students', 
                    'transport', 'student_fees', 'fees', 'fines', 'attendance'],
            'students': ['students', 'student_fees', 'attendance'],
            'financial': ['fees', 'student_fees', 'fines'],
            'teachers': ['teachers', 'subjects']
        }
        
        apps_to_backup = apps_map.get(backup_type, apps_map['full'])
        
        # Create backup
        with open(backup_path, 'w', encoding='utf-8') as f:
            call_command('dumpdata', *apps_to_backup, format='json', indent=2, stdout=f)
        
        # Get file size
        file_size = backup_path.stat().st_size
        size_mb = file_size / (1024 * 1024)
        
        # Create history record
        from backup.models import BackupHistory
        BackupHistory.objects.create(
            file_name=filename,
            operation_type='backup'
        )
        
        self.stdout.write(
            self.style.SUCCESS(
                f"Backup created successfully!\n"
                f"File: {backup_path}\n"
                f"Size: {size_mb:.2f} MB\n"
                f"Apps: {', '.join(apps_to_backup)}"
            )
        )
    
    def handle_restore(self, options):
        """Handle backup restoration"""
        file_path = Path(options['file'])
        mode = options['mode']
        dry_run = options.get('dry_run', False)
        
        if not file_path.exists():
            raise CommandError(f"Backup file not found: {file_path}")
        
        self.stdout.write(f"{'Validating' if dry_run else 'Restoring'} backup from {file_path}...")
        
        # Validate JSON structure
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            if not isinstance(data, list):
                raise CommandError("Invalid backup format: expected JSON array")
            
            self.stdout.write(f"Backup contains {len(data)} records")
            
        except json.JSONDecodeError as e:
            raise CommandError(f"Invalid JSON format: {e}")
        
        if dry_run:
            self.stdout.write(self.style.SUCCESS("Backup validation completed successfully"))
            return
        
        # Confirm dangerous operations
        if mode == 'replace':
            confirm = input("WARNING: Replace mode will delete existing data. Continue? (yes/no): ")
            if confirm.lower() != 'yes':
                self.stdout.write("Operation cancelled")
                return
        
        # Perform restore
        from backup.modern_restore_engine import ModernRestoreEngine
        
        engine = ModernRestoreEngine()
        result = engine.restore_backup(str(file_path), mode)
        
        # Create history record
        from backup.models import BackupHistory
        BackupHistory.objects.create(
            file_name=file_path.name,
            operation_type='restore'
        )
        
        self.stdout.write(
            self.style.SUCCESS(
                f"Restore completed successfully!\n"
                f"Created: {result.created}\n"
                f"Updated: {result.updated}\n"
                f"Skipped: {result.skipped}\n"
                f"Errors: {len(result.errors)}"
            )
        )
        
        if result.errors:
            self.stdout.write(self.style.WARNING("Errors encountered:"))
            for error in result.errors[:5]:  # Show first 5 errors
                self.stdout.write(f"  - {error}")
    
    def handle_cleanup(self, options):
        """Handle cleanup of old backups"""
        days_old = options['days']
        confirm = options.get('confirm', False)
        
        cutoff_date = timezone.now() - timezone.timedelta(days=days_old)
        
        from backup.models import BackupHistory
        old_backups = BackupHistory.objects.filter(
            date__lt=cutoff_date,
            operation_type='backup'
        )
        
        count = old_backups.count()
        
        if count == 0:
            self.stdout.write("No old backups found to clean up")
            return
        
        if not confirm:
            response = input(f"Delete {count} backups older than {days_old} days? (yes/no): ")
            if response.lower() != 'yes':
                self.stdout.write("Cleanup cancelled")
                return
        
        # Delete files and records
        backup_dir = Path(settings.BASE_DIR) / 'backups'
        deleted_count = 0
        freed_space = 0
        
        for backup in old_backups:
            file_path = backup_dir / backup.file_name
            if file_path.exists():
                file_size = file_path.stat().st_size
                file_path.unlink()
                freed_space += file_size
                deleted_count += 1
            
            backup.delete()
        
        freed_mb = freed_space / (1024 * 1024)
        
        self.stdout.write(
            self.style.SUCCESS(
                f"Cleanup completed!\n"
                f"Deleted: {deleted_count} files\n"
                f"Freed space: {freed_mb:.2f} MB"
            )
        )
    
    def handle_list(self, options):
        """Handle listing backups"""
        limit = options['limit']
        
        from backup.models import BackupHistory
        backups = BackupHistory.objects.all().order_by('-date')[:limit]
        
        if not backups:
            self.stdout.write("No backups found")
            return
        
        self.stdout.write(f"{'ID':<5} {'File Name':<40} {'Date':<20} {'Type':<10}")
        self.stdout.write("-" * 80)
        
        for backup in backups:
            self.stdout.write(
                f"{backup.id:<5} {backup.file_name:<40} "
                f"{backup.date.strftime('%Y-%m-%d %H:%M'):<20} {backup.operation_type:<10}"
            )
    
    def handle_status(self, options):
        """Handle status display"""
        from backup.models import BackupHistory, BackupJob, RestoreJob
        import shutil
        
        # Get statistics
        total_backups = BackupHistory.objects.filter(operation_type='backup').count()
        total_restores = BackupHistory.objects.filter(operation_type='restore').count()
        last_backup = BackupHistory.objects.filter(operation_type='backup').order_by('-date').first()
        
        # Get disk usage
        backup_dir = Path(settings.BASE_DIR) / 'backups'
        if backup_dir.exists():
            total, used, free = shutil.disk_usage(backup_dir)
            storage_info = f"{used / (1024**3):.2f} GB used, {free / (1024**3):.2f} GB free"
        else:
            storage_info = "Backup directory not found"
        
        # Get recent jobs
        recent_backup_jobs = BackupJob.objects.order_by('-created_at')[:5]
        recent_restore_jobs = RestoreJob.objects.order_by('-created_at')[:5]
        
        self.stdout.write(self.style.SUCCESS("Backup System Status"))
        self.stdout.write("=" * 50)
        self.stdout.write(f"Total Backups: {total_backups}")
        self.stdout.write(f"Total Restores: {total_restores}")
        self.stdout.write(f"Last Backup: {last_backup.date if last_backup else 'Never'}")
        self.stdout.write(f"Storage: {storage_info}")
        
        if recent_backup_jobs:
            self.stdout.write("\nRecent Backup Jobs:")
            for job in recent_backup_jobs:
                self.stdout.write(f"  {job.id}: {job.status} ({job.created_at.strftime('%Y-%m-%d %H:%M')})")
        
        if recent_restore_jobs:
            self.stdout.write("\nRecent Restore Jobs:")
            for job in recent_restore_jobs:
                self.stdout.write(f"  {job.id}: {job.status} ({job.created_at.strftime('%Y-%m-%d %H:%M')})")
    
    def handle_verify(self, options):
        """Handle backup file verification"""
        file_path = Path(options['file'])
        
        if not file_path.exists():
            raise CommandError(f"Backup file not found: {file_path}")
        
        self.stdout.write(f"Verifying backup file: {file_path}")
        
        try:
            # Check JSON structure
            with open(file_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            if not isinstance(data, list):
                raise CommandError("Invalid backup format: expected JSON array")
            
            # Analyze content
            models = {}
            for item in data:
                if isinstance(item, dict) and 'model' in item:
                    model = item['model']
                    models[model] = models.get(model, 0) + 1
            
            # Calculate file info
            file_size = file_path.stat().st_size
            size_mb = file_size / (1024 * 1024)
            
            self.stdout.write(self.style.SUCCESS("Backup verification completed!"))
            self.stdout.write(f"File size: {size_mb:.2f} MB")
            self.stdout.write(f"Total records: {len(data)}")
            self.stdout.write("Models found:")
            
            for model, count in sorted(models.items()):
                self.stdout.write(f"  {model}: {count} records")
                
        except json.JSONDecodeError as e:
            raise CommandError(f"Invalid JSON format: {e}")
        except Exception as e:
            raise CommandError(f"Verification failed: {e}")