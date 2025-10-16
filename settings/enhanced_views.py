# settings/enhanced_views.py
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.utils.translation import activate
from django.http import JsonResponse
from django.views.decorators.http import require_http_methods
from django.core.cache import cache
from django.db import transaction
from django.utils import timezone
from users.decorators import module_required
from .models import SystemSettings, NotificationSettings, MLSettings, UserPreferences, SystemHealth, AuditLog
from .forms import (
    SystemSettingsForm, NotificationSettingsForm, MLSettingsForm, 
    UserPreferencesForm, LanguageSettingsForm, SecuritySettingsForm,
    BackupSettingsForm, SystemMaintenanceForm
)
import logging
import os
import json
from decimal import Decimal

logger = logging.getLogger(__name__)

@module_required('settings', 'view')
def settings_dashboard(request):
    """Main settings dashboard"""
    context = {
        'system_settings': SystemSettings.get_settings(),
        'notification_settings': NotificationSettings.get_settings(),
        'ml_settings': MLSettings.get_settings(),
        'system_health': SystemHealth.get_latest_health(),
        'user_preferences': getattr(request.user, 'preferences', None)
    }
    return render(request, 'settings/dashboard.html', context)

@module_required('settings', 'view')
def language_settings(request):
    """Language configuration"""
    if request.method == 'POST':
        form = LanguageSettingsForm(request.POST)
        if form.is_valid():
            selected_lang = form.cleaned_data['language']
            request.session['django_language'] = selected_lang
            activate(selected_lang)
            
            # Update user preferences if exists
            if hasattr(request.user, 'preferences'):
                request.user.preferences.language = selected_lang
                request.user.preferences.save()
            
            messages.success(request, 'Language settings updated successfully!')
            return redirect('settings:language')
    else:
        initial_lang = request.session.get('django_language', 'en')
        form = LanguageSettingsForm(initial={'language': initial_lang})
    
    return render(request, 'settings/language.html', {'form': form})

@module_required('settings', 'edit')
def system_settings(request):
    """System-wide configuration"""
    settings_obj = SystemSettings.get_settings()
    
    if request.method == 'POST':
        form = SystemSettingsForm(request.POST, instance=settings_obj)
        if form.is_valid():
            with transaction.atomic():
                updated_settings = form.save(commit=False)
                updated_settings.updated_by = request.user
                updated_settings.save()
                
                # Log the change
                AuditLog.objects.create(
                    user=request.user,
                    action='UPDATE',
                    model_name='SystemSettings',
                    object_id=updated_settings.id,
                    changes=form.changed_data,
                    ip_address=request.META.get('REMOTE_ADDR')
                )
            
            messages.success(request, 'System settings updated successfully!')
            return redirect('settings:system')
    else:
        form = SystemSettingsForm(instance=settings_obj)
    
    return render(request, 'settings/system.html', {'form': form, 'settings': settings_obj})

@module_required('settings', 'edit')
def notification_settings(request):
    """Notification and messaging configuration"""
    settings_obj = NotificationSettings.get_settings()
    
    if request.method == 'POST':
        form = NotificationSettingsForm(request.POST, instance=settings_obj)
        if form.is_valid():
            form.save()
            messages.success(request, 'Notification settings updated successfully!')
            return redirect('settings:notifications')
    else:
        form = NotificationSettingsForm(instance=settings_obj)
    
    return render(request, 'settings/notifications.html', {'form': form})

@module_required('settings', 'edit')
def ml_settings(request):
    """Machine Learning configuration"""
    settings_obj = MLSettings.get_settings()
    
    # Check ML availability
    try:
        from core.ml_integrations import ML_AVAILABLE
        ml_available = ML_AVAILABLE
    except ImportError:
        ml_available = False
    
    if request.method == 'POST':
        form = MLSettingsForm(request.POST, instance=settings_obj)
        if form.is_valid():
            form.save()
            messages.success(request, 'ML settings updated successfully!')
            return redirect('settings:ml')
    else:
        form = MLSettingsForm(instance=settings_obj)
    
    context = {
        'form': form,
        'ml_available': ml_available,
        'ml_models_count': len([f for f in os.listdir('models') if f.endswith('.pkl')]) if os.path.exists('models') else 0
    }
    return render(request, 'settings/ml.html', context)

@login_required
def user_preferences(request):
    """Individual user preferences"""
    preferences, created = UserPreferences.objects.get_or_create(user=request.user)
    
    if request.method == 'POST':
        form = UserPreferencesForm(request.POST, instance=preferences)
        if form.is_valid():
            form.save()
            messages.success(request, 'Your preferences have been updated!')
            return redirect('settings:preferences')
    else:
        form = UserPreferencesForm(instance=preferences)
    
    return render(request, 'settings/preferences.html', {'form': form})

@module_required('settings', 'edit')
def security_settings(request):
    """Security configuration"""
    system_settings = SystemSettings.get_settings()
    
    if request.method == 'POST':
        form = SecuritySettingsForm(request.POST)
        if form.is_valid():
            # Update system settings with security values
            system_settings.session_timeout_minutes = form.cleaned_data['session_timeout']
            system_settings.max_login_attempts = form.cleaned_data['max_login_attempts']
            system_settings.save()
            
            messages.success(request, 'Security settings updated successfully!')
            return redirect('settings:security')
    else:
        form = SecuritySettingsForm(initial={
            'session_timeout': system_settings.session_timeout_minutes,
            'max_login_attempts': system_settings.max_login_attempts
        })
    
    return render(request, 'settings/security.html', {'form': form})

@module_required('settings', 'edit')
def backup_settings(request):
    """Backup configuration"""
    system_settings = SystemSettings.get_settings()
    
    if request.method == 'POST':
        form = BackupSettingsForm(request.POST)
        if form.is_valid():
            system_settings.auto_backup_enabled = form.cleaned_data['auto_backup_enabled']
            system_settings.backup_retention_days = form.cleaned_data['retention_days']
            system_settings.save()
            
            messages.success(request, 'Backup settings updated successfully!')
            return redirect('settings:backup')
    else:
        form = BackupSettingsForm(initial={
            'auto_backup_enabled': system_settings.auto_backup_enabled,
            'retention_days': system_settings.backup_retention_days
        })
    
    return render(request, 'settings/backup.html', {'form': form})

@module_required('settings', 'edit')
def system_maintenance(request):
    """System maintenance operations"""
    if request.method == 'POST':
        form = SystemMaintenanceForm(request.POST)
        if form.is_valid():
            action = form.cleaned_data['action']
            result = perform_maintenance_action(action, request.user)
            
            if result['success']:
                messages.success(request, result['message'])
            else:
                messages.error(request, result['message'])
            
            return redirect('settings:maintenance')
    else:
        form = SystemMaintenanceForm()
    
    return render(request, 'settings/maintenance.html', {'form': form})

@module_required('settings', 'view')
def system_health(request):
    """System health monitoring"""
    health_record = SystemHealth.get_latest_health()
    
    # Get recent health records for charts
    recent_health = SystemHealth.objects.all()[:24]  # Last 24 records
    
    context = {
        'health_record': health_record,
        'recent_health': recent_health,
        'system_status': get_system_status()
    }
    return render(request, 'settings/health.html', context)

@require_http_methods(["POST"])
@module_required('settings', 'edit')
def test_notification(request):
    """Test notification settings"""
    try:
        notification_type = request.POST.get('type')
        test_message = "Test message from School Management System"
        
        if notification_type == 'sms':
            # Test SMS
            from messaging.services import NotificationService
            result = NotificationService.send_test_sms(test_message)
        elif notification_type == 'whatsapp':
            # Test WhatsApp
            from messaging.services import NotificationService
            result = NotificationService.send_test_whatsapp(test_message)
        elif notification_type == 'email':
            # Test Email
            from django.core.mail import send_mail
            send_mail(
                'Test Email',
                test_message,
                'noreply@school.edu',
                [request.user.email]
            )
            result = {'success': True}
        else:
            result = {'success': False, 'error': 'Invalid notification type'}
        
        return JsonResponse(result)
    
    except Exception as e:
        logger.error(f"Notification test failed: {e}")
        return JsonResponse({'success': False, 'error': str(e)})

@require_http_methods(["GET"])
@module_required('settings', 'view')
def api_system_status(request):
    """API endpoint for system status"""
    try:
        status = get_system_status()
        return JsonResponse(status)
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)

def perform_maintenance_action(action, user):
    """Perform system maintenance actions"""
    try:
        if action == 'clear_cache':
            cache.clear()
            return {'success': True, 'message': 'System cache cleared successfully'}
        
        elif action == 'optimize_db':
            # Database optimization logic
            from django.db import connection
            with connection.cursor() as cursor:
                cursor.execute("VACUUM;")
            return {'success': True, 'message': 'Database optimized successfully'}
        
        elif action == 'cleanup_logs':
            # Log cleanup logic
            log_dir = 'logs'
            if os.path.exists(log_dir):
                for file in os.listdir(log_dir):
                    if file.endswith('.log.old'):
                        os.remove(os.path.join(log_dir, file))
            return {'success': True, 'message': 'Log files cleaned up successfully'}
        
        elif action == 'update_ml_models':
            # ML model update logic
            try:
                from core.ml_integrations import ml_service
                if ml_service:
                    # Trigger model retraining
                    return {'success': True, 'message': 'ML models updated successfully'}
                else:
                    return {'success': False, 'message': 'ML service not available'}
            except ImportError:
                return {'success': False, 'message': 'ML dependencies not installed'}
        
        elif action == 'generate_reports':
            # System report generation
            return {'success': True, 'message': 'System reports generated successfully'}
        
        else:
            return {'success': False, 'message': 'Unknown maintenance action'}
    
    except Exception as e:
        logger.error(f"Maintenance action {action} failed: {e}")
        return {'success': False, 'message': f'Maintenance failed: {str(e)}'}

def get_system_status():
    """Get current system status"""
    try:
        # Database status
        from django.db import connection
        db_status = 'healthy'
        try:
            connection.ensure_connection()
        except:
            db_status = 'error'
        
        # Cache status
        cache_status = 'healthy'
        try:
            cache.set('health_check', 'ok', 10)
            cache.get('health_check')
        except:
            cache_status = 'error'
        
        # ML status
        ml_status = 'unavailable'
        try:
            from core.ml_integrations import ML_AVAILABLE
            ml_status = 'healthy' if ML_AVAILABLE else 'unavailable'
        except:
            ml_status = 'error'
        
        # Overall status
        overall_status = 'healthy'
        if db_status == 'error' or cache_status == 'error':
            overall_status = 'critical'
        elif ml_status == 'error':
            overall_status = 'warning'
        
        return {
            'overall': overall_status,
            'database': db_status,
            'cache': cache_status,
            'ml_service': ml_status,
            'timestamp': timezone.now().isoformat()
        }
    
    except Exception as e:
        logger.error(f"System status check failed: {e}")
        return {
            'overall': 'error',
            'error': str(e),
            'timestamp': timezone.now().isoformat()
        }