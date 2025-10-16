from django.core.management.base import BaseCommand
from django.conf import settings
import os
import shutil
import logging

logger = logging.getLogger(__name__)

class Command(BaseCommand):
    help = 'Clear all uploaded media files'

    def add_arguments(self, parser):
        parser.add_argument(
            '--confirm',
            action='store_true',
            help='Confirm media files deletion',
        )

    def handle(self, *args, **options):
        if not options['confirm']:
            self.stdout.write(
                self.style.WARNING(
                    'This will delete ALL uploaded media files!\n'
                    'Run with --confirm to proceed: python manage.py clear_media_files --confirm'
                )
            )
            return

        try:
            media_root = settings.MEDIA_ROOT
            if not os.path.exists(media_root):
                self.stdout.write('No media directory found.')
                return

            # Directories to clear
            dirs_to_clear = [
                'students',
                'teacher_photos', 
                'teacher_resumes',
                'teacher_letters',
                'profile_pics',
                'uploads',
                'reports'
            ]

            total_deleted = 0
            for dir_name in dirs_to_clear:
                dir_path = os.path.join(media_root, dir_name)
                if os.path.exists(dir_path):
                    # Count files before deletion
                    file_count = sum([len(files) for r, d, files in os.walk(dir_path)])
                    
                    # Remove directory contents
                    shutil.rmtree(dir_path)
                    
                    # Recreate empty directory
                    os.makedirs(dir_path, exist_ok=True)
                    
                    total_deleted += file_count
                    self.stdout.write(f'Cleared {file_count} files from {dir_name}/')

            self.stdout.write(
                self.style.SUCCESS(
                    f'Successfully cleared {total_deleted} media files!'
                )
            )

        except Exception as e:
            logger.error(f"Error clearing media files: {str(e)}")
            self.stdout.write(
                self.style.ERROR(f'Error clearing media files: {str(e)}')
            )