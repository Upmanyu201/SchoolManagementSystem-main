# D:\School-Management-System\School-Management-System-main\school_profile\models.py
from django.db import models
from django.utils import timezone
from django.core.exceptions import ValidationError
from datetime import timedelta

class SchoolProfile(models.Model):
    school_name = models.CharField(max_length=255)
    principal_name = models.CharField(max_length=255)
    address = models.TextField()
    email = models.EmailField(unique=True)
    mobile = models.CharField(max_length=15)
    registration_number = models.CharField(max_length=50, unique=True)
    website = models.URLField(blank=True, null=True)
    logo = models.ImageField(upload_to='school_logos/', blank=True, null=True)
    academic_calendar = models.FileField(
        upload_to='academic_calendars/', 
        blank=True, 
        null=True
    )
    start_date = models.DateField(help_text="Start date of current academic session")
    end_date = models.DateField(help_text="End date of current academic session")
    academic_session_start_month = models.PositiveSmallIntegerField(
        default=4,
        choices=[(i, f'Month {i}') for i in range(1, 13)],
        help_text="Month when academic year starts (1-12)"
    )

    class Meta:
        verbose_name = "School Profile"
        verbose_name_plural = "School Profiles"
        ordering = ['school_name']

    def __str__(self):
        return self.school_name

    def save(self, *args, **kwargs):
        # Enforce singleton pattern
        if SchoolProfile.objects.exists() and not self.pk:
            raise ValidationError("Only one school profile is allowed")
        
        # Auto-set end_date = start_date + 1 year
        if self.start_date and not self.end_date:
            self.end_date = self.start_date + timedelta(days=365)
        
        super().save(*args, **kwargs)

    @property
    def current_academic_session(self):
        today = timezone.now().date()
        if self.start_date <= today <= self.end_date:
            return f"{self.start_date.year}-{self.end_date.year}"
        return "Session Expired"

class Class(models.Model):
    name = models.CharField(max_length=100, unique=True)
    display_order = models.PositiveIntegerField(default=0)

    class Meta:
        verbose_name_plural = "Classes"
        ordering = ['display_order']

    def __str__(self):
        return self.name

class PromotionRule(models.Model):
    current_class = models.ForeignKey(
        Class, 
        on_delete=models.CASCADE, 
        related_name='promotion_from'
    )
    next_class = models.ForeignKey(
        Class, 
        on_delete=models.CASCADE, 
        related_name='promotion_to'
    )
    is_active = models.BooleanField(default=True)

    class Meta:
        unique_together = ('current_class', 'next_class')
        verbose_name = "Promotion Rule"

    def __str__(self):
        return f"{self.current_class} → {self.next_class}"