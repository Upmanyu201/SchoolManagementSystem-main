"""
Admin interface for backup system
"""

from django.contrib import admin
from .models import BackupHistory, BackupJob, RestoreJob, ScheduledBackup


@admin.register(BackupHistory)
class BackupHistoryAdmin(admin.ModelAdmin):
    list_display = ['file_name', 'operation_type', 'date']
    list_filter = ['operation_type', 'date']
    search_fields = ['file_name']
    readonly_fields = ['date']


@admin.register(BackupJob)
class BackupJobAdmin(admin.ModelAdmin):
    list_display = ['id', 'backup_type', 'status', 'file_size', 'duration_seconds', 'created_by', 'created_at']
    list_filter = ['backup_type', 'status', 'created_at']
    search_fields = ['id', 'file_path']
    readonly_fields = ['created_at', 'file_size', 'checksum']
    
    fieldsets = (
        ('Basic Info', {
            'fields': ('backup_type', 'status', 'created_by')
        }),
        ('File Details', {
            'fields': ('file_path', 'format', 'file_size', 'checksum')
        }),
        ('Performance', {
            'fields': ('duration_seconds', 'created_at')
        }),
        ('Advanced', {
            'fields': ('schema_version', 'metadata', 'report_json', 'error_text'),
            'classes': ('collapse',)
        })
    )


@admin.register(RestoreJob)
class RestoreJobAdmin(admin.ModelAdmin):
    list_display = ['id', 'status', 'source_type', 'mode', 'created_at']
    list_filter = ['status', 'source_type', 'mode', 'created_at']
    readonly_fields = ['created_at']


@admin.register(ScheduledBackup)
class ScheduledBackupAdmin(admin.ModelAdmin):
    list_display = ['name', 'backup_type', 'cron_expression', 'is_active', 'last_run', 'last_status', 'created_by']
    list_filter = ['backup_type', 'is_active', 'last_status', 'created_at']
    search_fields = ['name', 'description']
    readonly_fields = ['created_at', 'last_run']
    
    fieldsets = (
        ('Schedule Info', {
            'fields': ('name', 'description', 'backup_type', 'created_by')
        }),
        ('Schedule Configuration', {
            'fields': ('cron_expression', 'is_active')
        }),
        ('Status', {
            'fields': ('last_run', 'last_status', 'created_at'),
            'classes': ('collapse',)
        })
    )
    
    actions = ['activate_schedules', 'deactivate_schedules']
    
    def activate_schedules(self, request, queryset):
        updated = queryset.update(is_active=True)
        self.message_user(request, f'{updated} schedules activated.')
    activate_schedules.short_description = "Activate selected schedules"
    
    def deactivate_schedules(self, request, queryset):
        updated = queryset.update(is_active=False)
        self.message_user(request, f'{updated} schedules deactivated.')
    deactivate_schedules.short_description = "Deactivate selected schedules"