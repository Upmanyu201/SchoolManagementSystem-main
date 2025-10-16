# Security utilities for backup system
import html
import re
import logging

logger = logging.getLogger('backup.security')

def sanitize_for_logging(message):
    """Sanitize input for safe logging"""
    if not isinstance(message, str):
        message = str(message)
    
    # Remove newlines and carriage returns
    message = re.sub(r'[\r\n]', ' ', message)
    
    # HTML escape to prevent XSS in log viewers
    message = html.escape(message)
    
    # Limit length to prevent log flooding
    if len(message) > 500:
        message = message[:497] + "..."
    
    return message

def safe_log_info(logger, message, *args):
    """Safely log info message with sanitized input"""
    sanitized_message = sanitize_for_logging(message)
    sanitized_args = [sanitize_for_logging(str(arg)) for arg in args]
    logger.info(sanitized_message, *sanitized_args)

def safe_log_error(logger, message, *args):
    """Safely log error message with sanitized input"""
    sanitized_message = sanitize_for_logging(message)
    sanitized_args = [sanitize_for_logging(str(arg)) for arg in args]
    logger.error(sanitized_message, *sanitized_args)

def safe_log_warning(logger, message, *args):
    """Safely log warning message with sanitized input"""
    sanitized_message = sanitize_for_logging(message)
    sanitized_args = [sanitize_for_logging(str(arg)) for arg in args]
    logger.warning(sanitized_message, *sanitized_args)