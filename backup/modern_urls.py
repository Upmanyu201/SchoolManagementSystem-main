# Modern URL Configuration - 2025 Standards
from django.urls import path, include
from . import secure_views

app_name = 'backup'

# API v2 endpoints with proper REST structure
api_v2_patterns = [
    # Backup operations
    path('backups/', secure_views.secure_create_backup, name='create_backup'),
    path('backups/history/', secure_views.get_backup_history, name='backup_history'),
    path('backups/jobs/<int:job_id>/', secure_views.get_job_status, name='backup_job_status'),
    
    # Restore operations
    path('restore/upload/', secure_views.secure_restore_upload, name='restore_upload'),
    path('restore/history/<int:backup_id>/', secure_views.secure_restore_history, name='restore_history'),
    path('restore/jobs/<int:job_id>/', secure_views.get_job_status, name='restore_job_status'),
]

urlpatterns = [
    # Modern API endpoints
    path('api/v2/', include(api_v2_patterns)),
    
    # Legacy compatibility (deprecated but functional)
    path('create/', secure_views.secure_create_backup, name='legacy_create_backup'),
    path('restore/', secure_views.secure_restore_upload, name='legacy_restore_upload'),
    path('history/', secure_views.get_backup_history, name='legacy_backup_history'),
]