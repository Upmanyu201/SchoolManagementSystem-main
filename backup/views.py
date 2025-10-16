from django.shortcuts import render
from django.http import JsonResponse, HttpResponse
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from users.decorators import module_required
from .services.export_service import DataExportService

@module_required('backup', 'view')
def backup_restore_page(request):
    return render(request, 'backup/backup_restore.html')

@module_required('backup', 'edit')
def download_backup(request, backup_id):
    response = HttpResponse(content_type='application/json')
    response['Content-Disposition'] = f'attachment; filename="backup_{backup_id}.json"'
    return response

@module_required('backup', 'edit')
def delete_backup(request, backup_id):
    return JsonResponse({'success': True})

@module_required('backup', 'view')
def export_history(request):
    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = 'attachment; filename="backup_history.csv"'
    return response

@module_required('backup', 'view')
def system_status(request):
    try:
        from .models import BackupHistory
        import shutil
        from pathlib import Path
        from django.conf import settings
        
        backup_dir = Path(settings.BASE_DIR) / 'backups'
        total_backups = BackupHistory.objects.filter(operation_type='backup').count()
        last_backup = BackupHistory.objects.filter(operation_type='backup').order_by('-date').first()
        
        if backup_dir.exists():
            total, used, free = shutil.disk_usage(backup_dir)
            disk_usage = f"{(used / total * 100):.1f}%"
        else:
            disk_usage = "N/A"
        
        return JsonResponse({
            'status': 'success',
            'data': {
                'disk_usage': disk_usage,
                'backup_count': total_backups,
                'last_backup': last_backup.date.isoformat() if last_backup else None
            }
        })
    except Exception as e:
        return JsonResponse({'status': 'error', 'message': str(e)}, status=500)

@module_required('backup', 'edit')
def cleanup_old_backups(request):
    try:
        from .models import BackupHistory
        from django.utils import timezone
        from pathlib import Path
        from django.conf import settings
        
        cutoff_date = timezone.now() - timezone.timedelta(days=30)
        old_backups = BackupHistory.objects.filter(date__lt=cutoff_date, operation_type='backup')
        
        backup_dir = Path(settings.BASE_DIR) / 'backups'
        cleaned_count = 0
        
        for backup in old_backups:
            file_path = backup_dir / backup.file_name
            if file_path.exists():
                file_path.unlink()
                cleaned_count += 1
            backup.delete()
        
        return JsonResponse({'status': 'success', 'cleaned': cleaned_count})
    except Exception as e:
        return JsonResponse({'status': 'error', 'message': str(e)}, status=500)

# Export System - New functionality
@module_required('backup', 'view')
def export_module_data(request, module_name, format_type):
    """Export module data in specified format"""
    try:
        if module_name not in DataExportService.SUPPORTED_MODULES:
            return JsonResponse({'error': 'Module not supported'}, status=400)
        
        if format_type == 'csv':
            return DataExportService.export_to_csv(module_name, getattr(request, 'user', None))
        elif format_type == 'excel':
            return DataExportService.export_to_excel(module_name, getattr(request, 'user', None))
        elif format_type == 'pdf':
            return DataExportService.export_to_pdf(module_name, getattr(request, 'user', None))
        else:
            return JsonResponse({'error': 'Format not supported'}, status=400)
            
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)

@module_required('backup', 'view')
def get_export_modules(request):
    """Get list of available modules for export"""
    modules = [
        {'key': 'students', 'name': 'Students', 'icon': 'users'},
        {'key': 'teachers', 'name': 'Teachers', 'icon': 'user-check'},
        {'key': 'subjects', 'name': 'Subjects', 'icon': 'book'},
        {'key': 'transport', 'name': 'Transport', 'icon': 'truck'},
        {'key': 'fees', 'name': 'Fee Setup', 'icon': 'credit-card'},
        {'key': 'student_fees', 'name': 'Fee Deposits', 'icon': 'dollar-sign'},
        {'key': 'attendance', 'name': 'Attendance', 'icon': 'calendar-check'},
        {'key': 'users', 'name': 'Users', 'icon': 'user-cog'}
    ]
    return JsonResponse({'status': 'success', 'modules': modules})