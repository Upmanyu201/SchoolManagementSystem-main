from django.db import models
from django.conf import settings
from django.utils import timezone
from datetime import timedelta
import hashlib
import platform

class DemoStatus(models.Model):
    """Track demo status and license information"""
    machine_id = models.CharField(max_length=32, unique=True)
    demo_started = models.DateTimeField(auto_now_add=True)
    demo_expires = models.DateTimeField()
    is_licensed = models.BooleanField(default=False)
    license_key = models.CharField(max_length=200, blank=True, null=True)
    activated_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True)
    activated_at = models.DateTimeField(null=True, blank=True)
    
    class Meta:
        verbose_name = "Demo Status"
        verbose_name_plural = "Demo Statuses"
    
    def save(self, *args, **kwargs):
        if not self.demo_expires:
            self.demo_expires = timezone.now() + timedelta(days=15)
        super().save(*args, **kwargs)
    
    @property
    def days_remaining(self):
        if self.is_licensed:
            return float('inf')
        remaining = (self.demo_expires - timezone.now()).days
        return max(0, remaining)
    
    @property
    def is_active(self):
        return self.is_licensed or timezone.now() < self.demo_expires
    
    @classmethod
    def get_current_status(cls):
        """Get or create demo status for current machine"""
        from .services import LicenseService
        machine_id = LicenseService.get_machine_id()
        status, created = cls.objects.get_or_create(
            machine_id=machine_id,
            defaults={'demo_expires': timezone.now() + timedelta(days=15)}
        )
        return status

class LicenseActivation(models.Model):
    """Track license activation attempts"""
    demo_status = models.ForeignKey(DemoStatus, on_delete=models.CASCADE)
    license_key_attempted = models.CharField(max_length=200)
    attempted_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True)
    attempted_at = models.DateTimeField(auto_now_add=True)
    success = models.BooleanField(default=False)
    error_message = models.TextField(blank=True)
    
    class Meta:
        verbose_name = "License Activation"
        verbose_name_plural = "License Activations"