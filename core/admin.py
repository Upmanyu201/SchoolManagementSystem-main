from django.contrib import admin
from .models import ExportJob, AuditLog

@admin.register(ExportJob)
class ExportJobAdmin(admin.ModelAdmin):
    list_display = ['request_id', 'user', 'module', 'data_type', 'format', 'status', 'created_at']
    list_filter = ['status', 'format', 'module', 'created_at']
    search_fields = ['request_id', 'user__username', 'module', 'data_type']
    readonly_fields = ['request_id', 'created_at', 'completed_at', 'file_size']

@admin.register(AuditLog)
class AuditLogAdmin(admin.ModelAdmin):
    list_display = ['user', 'action', 'module', 'ip_address', 'created_at']
    list_filter = ['action', 'module', 'created_at']
    search_fields = ['user__username', 'action', 'module']
    readonly_fields = ['created_at']