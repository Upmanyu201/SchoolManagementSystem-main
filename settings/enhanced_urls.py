# settings/enhanced_urls.py
from django.urls import path
from . import enhanced_views as views

app_name = 'settings'

urlpatterns = [
    # Main dashboard
    path('', views.settings_dashboard, name='dashboard'),
    
    # Language settings
    path('language/', views.language_settings, name='language'),
    
    # System configuration
    path('system/', views.system_settings, name='system'),
    
    # Notification settings
    path('notifications/', views.notification_settings, name='notifications'),
    path('test-notification/', views.test_notification, name='test_notification'),
    
    # ML configuration
    path('ml/', views.ml_settings, name='ml'),
    
    # User preferences
    path('preferences/', views.user_preferences, name='preferences'),
    
    # Security settings
    path('security/', views.security_settings, name='security'),
    
    # Backup settings
    path('backup/', views.backup_settings, name='backup'),
    
    # System maintenance
    path('maintenance/', views.system_maintenance, name='maintenance'),
    
    # System health
    path('health/', views.system_health, name='health'),
    path('api/status/', views.api_system_status, name='api_status'),
]