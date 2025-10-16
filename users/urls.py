from django.urls import path
from django.contrib.auth.views import LoginView, LogoutView
from . import views

app_name = 'users'

urlpatterns = [
    # Authentication
    path('login/', LoginView.as_view(template_name='users/login.html'), name='login'),
    path('logout/', views.logout_view, name='logout'),
    path('register/', views.user_management, name='register'),  # Temporary redirect
    
    # Module Access Control (2025 Industry Standard)
    path('module-access/', views.module_access_view, name='module_access'),
    path('get-user-permissions/', views.get_user_permissions, name='get_user_permissions'),
    path('bulk-permission-update/', views.bulk_permission_update, name='bulk_permission_update'),
    path('reset-permissions/<int:user_id>/', views.reset_user_permissions, name='reset_user_permissions'),
    path('check-module-access/', views.check_module_access, name='check_module_access'),
    
    # User Management
    path('management/', views.user_management, name='user_management'),
    path('add/', views.add_user_view, name='add_user'),
    path('edit/<int:user_id>/', views.edit_user, name='edit_user'),
    path('activity-log/', views.user_activity_log, name='user_activity_log'),
    
    # API Endpoints
    path('api/permissions/<int:user_id>/', views.get_user_permissions, name='api_user_permissions'),
    path('clear-cache/<int:user_id>/', views.clear_user_cache, name='clear_user_cache'),
    path('api/user-status/<int:user_id>/', views.toggle_user_status, name='toggle_user_status'),
]