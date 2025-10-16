"""
Enhanced context managers for backup and restore operations
"""
import os
import json
import tempfile
from contextlib import contextmanager
from django.db import transaction
from django.core.management import call_command
from django.conf import settings
from django.utils import timezone
import logging

logger = logging.getLogger('backup.context_managers')

@contextmanager
def backup_transaction():
    """Context manager for safe backup operations with rollback"""
    savepoint = None
    try:
        with transaction.atomic():
            savepoint = transaction.savepoint()
            yield
            transaction.savepoint_commit(savepoint)
            logger.info("Backup transaction committed successfully")
    except Exception as e:
        if savepoint:
            transaction.savepoint_rollback(savepoint)
            logger.error(f"Backup transaction rolled back due to error: {e}")
        raise

@contextmanager
def restore_transaction():
    """Context manager for safe restore operations with comprehensive rollback"""
    snapshot_file = None
    temp_files = []
    
    try:
        # Create pre-restore snapshot
        snapshot_dir = os.path.join(settings.BASE_DIR, 'backups', 'snapshots')
        os.makedirs(snapshot_dir, exist_ok=True)
        
        snapshot_file = os.path.join(
            snapshot_dir, 
            f'pre_restore_{timezone.now().strftime("%Y%m%d_%H%M%S")}.json'
        )
        
        # Create snapshot of current state
        with open(snapshot_file, 'w', encoding='utf-8') as f:
            call_command('dumpdata', format='json', indent=2, stdout=f)
        
        logger.info(f"Pre-restore snapshot created: {snapshot_file}")
        
        with transaction.atomic():
            yield {
                'snapshot_file': snapshot_file,
                'temp_files': temp_files
            }
            
    except Exception as e:
        logger.error(f"Restore operation failed: {e}")
        
        # Attempt automatic rollback if snapshot exists
        if snapshot_file and os.path.exists(snapshot_file):
            try:
                logger.info("Attempting automatic rollback from snapshot...")
                rollback_from_snapshot(snapshot_file)
                logger.info("Automatic rollback successful")
            except Exception as rollback_error:
                logger.error(f"Automatic rollback failed: {rollback_error}")
        
        raise
    
    finally:
        # Cleanup temporary files
        for temp_file in temp_files:
            try:
                if os.path.exists(temp_file):
                    os.remove(temp_file)
            except Exception:
                pass
        
        # Clean up old snapshots (keep last 5)
        try:
            cleanup_old_snapshots(snapshot_dir)
        except Exception:
            pass

@contextmanager
def secure_file_operation(file_path, mode='r'):
    """Context manager for secure file operations"""
    file_handle = None
    try:
        # Validate file path security
        if not is_safe_path(file_path):
            raise ValueError("Unsafe file path detected")
        
        file_handle = open(file_path, mode, encoding='utf-8' if 'b' not in mode else None)
        yield file_handle
        
    except Exception as e:
        logger.error(f"File operation failed for {file_path}: {e}")
        raise
    finally:
        if file_handle:
            file_handle.close()

@contextmanager
def progress_tracking(operation_id, operation_type, total_steps=5):
    """Context manager for progress tracking"""
    from .progress_tracker import ProgressTracker
    
    progress = ProgressTracker(operation_id, operation_type)
    current_step = 0
    
    try:
        progress.update_progress(current_step, total_steps, "Operation started")
        
        class ProgressUpdater:
            def __init__(self, tracker, total):
                self.tracker = tracker
                self.total = total
                self.current = 0
            
            def step(self, message=""):
                self.current += 1
                self.tracker.update_progress(self.current, self.total, message)
        
        yield ProgressUpdater(progress, total_steps)
        
        progress.complete_operation(True, "Operation completed successfully")
        
    except Exception as e:
        progress.complete_operation(False, f"Operation failed: {str(e)}")
        raise

def rollback_from_snapshot(snapshot_file):
    """Rollback database to snapshot state"""
    if not os.path.exists(snapshot_file):
        raise FileNotFoundError(f"Snapshot file not found: {snapshot_file}")
    
    # Define apps to clear (preserve critical system data)
    ALLOWED_APPS = [
        "core", "school_profile", "teachers", "subjects", "students",
        "transport", "student_fees", "fees", "fines", "attendance",
        "promotion", "reports", "messaging"
    ]
    
    preserve_models = ['users.customuser', 'auth.user', 'auth.group', 'auth.permission']
    
    with transaction.atomic():
        # Use safe merge restore instead of clearing all data
        from .recovery import safe_merge_restore
        safe_merge_restore(snapshot_file)
    
    logger.info(f"Successfully rolled back from snapshot: {snapshot_file}")

def is_safe_path(file_path):
    """Check if file path is safe (no directory traversal)"""
    try:
        backup_dir = os.path.join(settings.BASE_DIR, 'backups')
        abs_backup_dir = os.path.abspath(backup_dir)
        abs_file_path = os.path.abspath(file_path)
        
        # Check if file is within backup directory
        return abs_file_path.startswith(abs_backup_dir)
    except Exception:
        return False

def cleanup_old_snapshots(snapshot_dir, keep_count=5):
    """Clean up old snapshot files, keeping only the most recent ones"""
    if not os.path.exists(snapshot_dir):
        return
    
    try:
        snapshots = [
            f for f in os.listdir(snapshot_dir) 
            if f.startswith('pre_restore_') and f.endswith('.json')
        ]
        
        # Sort by modification time (newest first)
        snapshots.sort(key=lambda x: os.path.getmtime(os.path.join(snapshot_dir, x)), reverse=True)
        
        # Remove old snapshots
        for old_snapshot in snapshots[keep_count:]:
            try:
                os.remove(os.path.join(snapshot_dir, old_snapshot))
                logger.debug(f"Removed old snapshot: {old_snapshot}")
            except Exception as e:
                logger.warning(f"Could not remove old snapshot {old_snapshot}: {e}")
                
    except Exception as e:
        logger.error(f"Error during snapshot cleanup: {e}")

# Enhanced restore context manager that integrates with existing system
@contextmanager
def enhanced_restore_operation(create_snapshot=True, operation_id=None):
    """
    Enhanced context manager for restore operations with comprehensive safety features
    """
    from .logging_config import BackupOperationLogger
    from .progress_tracker import ProgressTracker
    
    snapshot_file = None
    progress = None
    logger_instance = None
    
    try:
        # Initialize logging and progress tracking
        if operation_id:
            progress = ProgressTracker(operation_id, 'restore')
            logger_instance = BackupOperationLogger('restore', operation_id)
            logger_instance.log_start("Enhanced restore operation initiated")
        
        # Create snapshot if requested
        if create_snapshot:
            if progress:
                progress.update_progress(0, 5, "Creating pre-restore snapshot")
            
            snapshot_dir = os.path.join(settings.BASE_DIR, 'backups', 'snapshots')
            os.makedirs(snapshot_dir, exist_ok=True)
            
            snapshot_file = os.path.join(
                snapshot_dir,
                f'pre_restore_{timezone.now().strftime("%Y%m%d_%H%M%S")}.json'
            )
            
            with open(snapshot_file, 'w', encoding='utf-8') as f:
                call_command('dumpdata', format='json', indent=2, stdout=f)
            
            if logger_instance:
                logger_instance.log_progress("Snapshot created", snapshot_file)
        
        # Yield control to the calling code
        yield {
            'snapshot_file': snapshot_file,
            'progress': progress,
            'logger': logger_instance
        }
        
        if progress:
            progress.complete_operation(True, "Restore operation completed successfully")
        if logger_instance:
            logger_instance.log_success("Enhanced restore operation completed")
            
    except Exception as e:
        # Handle errors with automatic rollback
        if logger_instance:
            logger_instance.log_error(e, "Enhanced restore operation failed")
        
        if progress:
            progress.complete_operation(False, f"Restore operation failed: {str(e)}")
        
        # Attempt rollback if snapshot exists
        if snapshot_file and os.path.exists(snapshot_file):
            try:
                if logger_instance:
                    logger_instance.log_progress("Attempting automatic rollback")
                
                rollback_from_snapshot(snapshot_file)
                
                if logger_instance:
                    logger_instance.log_progress("Automatic rollback successful")
                    
            except Exception as rollback_error:
                if logger_instance:
                    logger_instance.log_error(rollback_error, "Automatic rollback failed")
        
        raise
    
    finally:
        # Cleanup old snapshots
        try:
            snapshot_dir = os.path.join(settings.BASE_DIR, 'backups', 'snapshots')
            cleanup_old_snapshots(snapshot_dir)
        except Exception:
            pass