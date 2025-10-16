# Import from enhanced security module
from .enhanced_security import BackupSecurityManager, SecureLogger, secure_log

# Backward compatibility
__all__ = ['BackupSecurityManager', 'SecureLogger', 'secure_log']