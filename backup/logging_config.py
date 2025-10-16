"""Enhanced logging configuration for backup operations"""
import logging
import os
from django.conf import settings

def setup_backup_logging():
    """Configure comprehensive backup logging"""
    
    # Create logs directory
    log_dir = os.path.join(settings.BASE_DIR, 'logs')
    os.makedirs(log_dir, exist_ok=True)
    
    # Backup operations logger
    backup_logger = logging.getLogger('backup.operations')
    backup_logger.setLevel(logging.DEBUG)
    
    # Create handlers
    backup_handler = logging.FileHandler(os.path.join(log_dir, 'backup_operations.log'))
    backup_handler.setLevel(logging.DEBUG)
    
    error_handler = logging.FileHandler(os.path.join(log_dir, 'backup_errors.log'))
    error_handler.setLevel(logging.ERROR)
    
    # Create formatters
    detailed_formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(funcName)s:%(lineno)d - %(message)s'
    )
    
    backup_handler.setFormatter(detailed_formatter)
    error_handler.setFormatter(detailed_formatter)
    
    # Add handlers to logger
    backup_logger.addHandler(backup_handler)
    backup_logger.addHandler(error_handler)
    
    return backup_logger

class BackupOperationLogger:
    """Enhanced logging for backup operations"""
    
    def __init__(self, operation_type, job_id=None):
        self.logger = logging.getLogger('backup.operations')
        self.operation_type = operation_type
        self.job_id = job_id
        self.operation_id = f"{operation_type}_{job_id or 'unknown'}"
    
    def log_start(self, details=None):
        """Log operation start"""
        msg = f"[{self.operation_id}] Starting {self.operation_type}"
        if details:
            msg += f" - {details}"
        self.logger.info(msg)
    
    def log_progress(self, step, details=None):
        """Log operation progress"""
        msg = f"[{self.operation_id}] {step}"
        if details:
            msg += f" - {details}"
        self.logger.info(msg)
    
    def log_success(self, details=None):
        """Log successful completion"""
        msg = f"[{self.operation_id}] {self.operation_type} completed successfully"
        if details:
            msg += f" - {details}"
        self.logger.info(msg)
    
    def log_error(self, error, details=None):
        """Log error with context"""
        msg = f"[{self.operation_id}] {self.operation_type} failed: {error}"
        if details:
            msg += f" - {details}"
        self.logger.error(msg, exc_info=True)
    
    def log_warning(self, warning, details=None):
        """Log warning"""
        msg = f"[{self.operation_id}] Warning: {warning}"
        if details:
            msg += f" - {details}"
        self.logger.warning(msg)