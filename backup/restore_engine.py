# Compatibility layer for restore engine
from .modern_restore_engine import ModernRestoreEngine

# Backward compatibility
SchoolDataRestoreEngine = ModernRestoreEngine

# Export for imports
__all__ = ['SchoolDataRestoreEngine', 'ModernRestoreEngine']