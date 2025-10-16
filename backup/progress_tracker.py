"""Real-time progress tracking for backup/restore operations"""
from django.core.cache import cache
from django.utils import timezone
import json

class ProgressTracker:
    """Track and report progress of backup/restore operations"""
    
    def __init__(self, operation_id, operation_type):
        self.operation_id = operation_id
        self.operation_type = operation_type
        self.cache_key = f"progress_{operation_type}_{operation_id}"
        self.start_time = timezone.now()
    
    def update_progress(self, current_step, total_steps, message="", details=None):
        """Update operation progress"""
        progress_data = {
            'operation_id': self.operation_id,
            'operation_type': self.operation_type,
            'current_step': current_step,
            'total_steps': total_steps,
            'percentage': round((current_step / total_steps) * 100, 1) if total_steps > 0 else 0,
            'message': message,
            'details': details or {},
            'start_time': self.start_time.isoformat(),
            'last_update': timezone.now().isoformat(),
            'status': 'running'
        }
        
        cache.set(self.cache_key, progress_data, timeout=3600)  # 1 hour
        return progress_data
    
    def complete_operation(self, success=True, message="", final_details=None):
        """Mark operation as completed"""
        progress_data = cache.get(self.cache_key, {})
        progress_data.update({
            'status': 'completed' if success else 'failed',
            'percentage': 100 if success else progress_data.get('percentage', 0),
            'message': message,
            'details': final_details or progress_data.get('details', {}),
            'end_time': timezone.now().isoformat(),
            'duration_seconds': (timezone.now() - self.start_time).total_seconds()
        })
        
        cache.set(self.cache_key, progress_data, timeout=3600)
        return progress_data
    
    @staticmethod
    def get_progress(operation_id, operation_type):
        """Get current progress for an operation"""
        cache_key = f"progress_{operation_type}_{operation_id}"
        return cache.get(cache_key)
    
    @staticmethod
    def cleanup_old_progress():
        """Clean up old progress entries"""
        # This would need cache pattern matching which isn't available in basic Django cache
        # Implementation depends on cache backend
        pass

# Enhanced restore function with progress tracking
def restore_with_progress_tracking(backup_file_path, restore_job_id):
    """Restore with real-time progress updates"""
    from .recovery import safe_restore_operation
    from .logging_config import BackupOperationLogger
    
    progress = ProgressTracker(restore_job_id, 'restore')
    logger = BackupOperationLogger('restore', restore_job_id)
    
    try:
        logger.log_start(f"Starting restore from {backup_file_path}")
        progress.update_progress(0, 5, "Initializing restore operation")
        
        with safe_restore_operation() as snapshot_file:
            progress.update_progress(1, 5, "Created pre-restore snapshot")
            logger.log_progress("Snapshot created", snapshot_file)
            
            # Validate backup file
            progress.update_progress(2, 5, "Validating backup file")
            with open(backup_file_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            if not isinstance(data, list):
                raise ValueError("Invalid backup format")
            
            logger.log_progress("Backup file validated", f"{len(data)} records found")
            
            # Clear existing data
            progress.update_progress(3, 5, "Clearing existing data")
            clear_apps_data(ALLOWED_APPS)
            logger.log_progress("Existing data cleared")
            
            # Restore data
            progress.update_progress(4, 5, "Restoring data from backup")
            clean_and_restore_data(backup_file_path)
            logger.log_progress("Data restoration completed")
            
            # Complete
            progress.complete_operation(True, "Restore completed successfully", {
                'records_restored': len(data),
                'snapshot_file': snapshot_file
            })
            logger.log_success(f"Restored {len(data)} records")
            
            return {"status": "success", "message": "Restore completed successfully"}
    
    except Exception as e:
        progress.complete_operation(False, f"Restore failed: {str(e)}")
        logger.log_error(e)
        raise