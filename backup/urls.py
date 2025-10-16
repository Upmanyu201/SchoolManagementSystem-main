# Modern Backup URLs - 2025 Standards
from django.urls import path, include
from . import views
from . import secure_views

app_name = 'backup'

# API endpoints for modern frontend
api_patterns = [
    path('create/', secure_views.secure_create_backup, name='api_create_backup'),
    path('restore/upload/', secure_views.secure_restore_upload, name='api_restore_upload'),
    path('restore/analyze/', secure_views.restore_analyze, name='api_restore_analyze'),
    path('restore/history/<int:backup_id>/', secure_views.secure_restore_history, name='api_restore_history'),
    path('history/', secure_views.get_backup_history, name='api_backup_history'),
    path('status/<int:job_id>/', secure_views.get_job_status, name='api_job_status'),
    path('download/<int:backup_id>/', views.download_backup, name='api_download_backup'),
    path('delete/<int:backup_id>/', views.delete_backup, name='api_delete_backup'),
    path('export/history/', views.export_history, name='api_export_history'),
    # Export System URLs
    path('export/modules/', views.get_export_modules, name='api_export_modules'),
    path('export/<str:module_name>/<str:format_type>/', views.export_module_data, name='api_export_data'),
]

urlpatterns = [
    # Main backup page
    path('', views.backup_restore_page, name='backup_restore'),
    path('modern/', secure_views.backup_main_page, name='modern_backup'),
    
    # API endpoints
    path('api/', include(api_patterns)),
    
    # Legacy compatibility endpoints
    path('create/', secure_views.secure_create_backup, name='create_backup'),
    path('restore/upload/', secure_views.secure_restore_upload, name='restore_upload'),
    path('restore/analyze/', secure_views.restore_analyze, name='restore_analyze'),
    path('restore/history/<int:backup_id>/', secure_views.secure_restore_history, name='restore_history'),
    path('history/', secure_views.get_backup_history, name='backup_history'),
    
    # Direct download/delete endpoints
    path('download/<int:backup_id>/', views.download_backup, name='download_backup'),
    path('delete/<int:backup_id>/', views.delete_backup, name='delete_backup'),
    
    # Additional utility endpoints
    path('status/', views.system_status, name='system_status'),
    path('cleanup/', views.cleanup_old_backups, name='cleanup_backups'),
]