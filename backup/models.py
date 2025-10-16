from django.db import models
from django.contrib.auth import get_user_model

User = get_user_model()

class BackupHistory(models.Model):
    file_name = models.CharField(max_length=255)
    date = models.DateTimeField(auto_now_add=True)
    operation_type = models.CharField(max_length=10, choices=[
        ('backup', 'Backup'),
        ('restore', 'Restore'),
    ], default='backup')

    def __str__(self):
        return self.file_name

class BackupJob(models.Model):
    created_at = models.DateTimeField(auto_now_add=True)
    status = models.CharField(
        max_length=16,
        choices=[('pending', 'pending'), ('running', 'running'), ('success', 'success'), ('failed', 'failed'), ('completed', 'completed')],
        default='pending'
    )
    file_path = models.TextField(blank=True, null=True)
    format = models.CharField(max_length=16, blank=True, null=True)  # json|jsonl|csv|zip|tar.gz
    checksum = models.CharField(max_length=128, blank=True, null=True)
    size_bytes = models.BigIntegerField(blank=True, null=True)
    schema_version = models.CharField(max_length=32, blank=True, null=True)
    report_json = models.JSONField(blank=True, null=True)
    error_text = models.TextField(blank=True, null=True)
    
    # Phase 4 compatibility fields
    backup_type = models.CharField(max_length=20, default='full')
    file_size = models.BigIntegerField(default=0)  # Alias for size_bytes
    duration_seconds = models.IntegerField(null=True, blank=True)
    created_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True)
    metadata = models.JSONField(default=dict, blank=True)

    class Meta:
        db_table = 'backup_jobs'
        indexes = [
            models.Index(fields=['created_at']),
            models.Index(fields=['status']),
        ]


class RestoreJob(models.Model):
    created_at = models.DateTimeField(auto_now_add=True)
    status = models.CharField(
        max_length=16,
        choices=[('pending', 'pending'), ('running', 'running'), ('success', 'success'), ('failed', 'failed')],
        default='pending'
    )
    source_type = models.CharField(
        max_length=16,
        choices=[('backup', 'backup'), ('uploaded', 'uploaded')],
        default='backup'
    )
    file_path = models.TextField(blank=True, null=True)
    format = models.CharField(max_length=16, blank=True, null=True)
    mode = models.CharField(
        max_length=16,
        choices=[('replace', 'replace'), ('merge', 'merge')],
        default='merge'
    )
    duplicate_strategy = models.CharField(
        max_length=16,
        choices=[('skip', 'skip'), ('update', 'update')],
        default='update'
    )
    schema_version = models.CharField(max_length=32, blank=True, null=True)
    validation_result_json = models.JSONField(blank=True, null=True)
    report_json = models.JSONField(blank=True, null=True)
    error_text = models.TextField(blank=True, null=True)

    class Meta:
        db_table = 'restore_jobs'
        indexes = [
            models.Index(fields=['created_at']),
            models.Index(fields=['status']),
        ]


# Phase 4 Compatibility - Model Aliases
BackupRecord = BackupJob


# Phase 4 Advanced Models
class ScheduledBackup(models.Model):
    name = models.CharField(max_length=100)
    backup_type = models.CharField(max_length=20, choices=[
        ('full', 'Full Backup'),
        ('incremental', 'Incremental Backup'),
    ], default='full')
    cron_expression = models.CharField(max_length=50)
    is_active = models.BooleanField(default=True)
    last_run = models.DateTimeField(null=True, blank=True)
    last_status = models.CharField(max_length=20, null=True, blank=True)
    description = models.TextField(blank=True)
    created_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        db_table = 'scheduled_backups'
        ordering = ['name']
    
    def __str__(self):
        return self.name