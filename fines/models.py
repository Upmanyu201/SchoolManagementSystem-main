from django.db import models, transaction
from django.contrib.auth import get_user_model
from django.db.models.signals import post_save
from django.dispatch import receiver
from django.utils import timezone
from datetime import timedelta
from django.conf import settings
from core.models import BaseModel
import logging

logger = logging.getLogger('myapp')
User = get_user_model()

class FineType(BaseModel):
    FINE_CATEGORIES = [
        ('Late Fee', 'Late Fee'),
        ('Damage', 'Damage'),
        ('Discipline', 'Discipline'),
        ('Library', 'Library'),
        ('Other', 'Other'),
    ]
    name = models.CharField(max_length=100, unique=True)
    category = models.CharField(max_length=20, choices=FINE_CATEGORIES)
    description = models.TextField(blank=True)
    is_active = models.BooleanField(default=True)
    created_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT, null=True, blank=True)

    def __str__(self):
        return self.name

class FineTemplate(BaseModel):
    name = models.CharField(max_length=100, unique=True)
    fine_type = models.ForeignKey(FineType, on_delete=models.PROTECT)
    amount = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    dynamic_amount_percent = models.DecimalField(max_digits=5, decimal_places=2, null=True, blank=True)
    reason = models.TextField(blank=True)
    delay_days = models.IntegerField(default=7)
    fees_group = models.ForeignKey('fees.FeesGroup', on_delete=models.SET_NULL, null=True, blank=True)
    fees_type = models.ForeignKey('fees.FeesType', on_delete=models.SET_NULL, null=True, blank=True)
    created_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT)

    def __str__(self):
        return self.name

class Fine(BaseModel):
    class_section = models.ForeignKey('subjects.ClassSection', on_delete=models.CASCADE, null=True, blank=True)
    fine_type = models.ForeignKey(FineType, on_delete=models.PROTECT)
    fees_group = models.ForeignKey('fees.FeesGroup', on_delete=models.SET_NULL, null=True, blank=True)
    fees_types = models.ManyToManyField('fees.FeesType', blank=True)
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    dynamic_amount_percent = models.DecimalField(max_digits=5, decimal_places=2, null=True, blank=True)
    reason = models.TextField()
    due_date = models.DateField()
    delay_days = models.IntegerField(default=0)
    applied_date = models.DateTimeField(auto_now_add=True)
    auto_generated = models.BooleanField(default=False)
    is_active = models.BooleanField(default=True)
    target_scope = models.CharField(max_length=20, choices=[('Individual', 'Individual'), ('Class', 'Class'), ('All', 'All Students')], default='Individual')
    created_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT, null=True)
    SCOPE_TYPES = [('Individual', 'Individual'), ('Class', 'Class'), ('All', 'All Students')]

    class Meta:
        indexes = [
            models.Index(fields=['target_scope']),
            models.Index(fields=['class_section']),
            models.Index(fields=['applied_date']),
        ]

    @property
    def is_paid(self):
        """Check if all students have paid this fine"""
        return not self.fine_students.filter(is_paid=False).exists()
    
    @property
    def should_apply_now(self):
        """Check if fine should be applied based on due_date + delay_days"""
        from django.utils import timezone
        application_date = self.due_date + timedelta(days=self.delay_days)
        return timezone.now().date() >= application_date
    
    @property
    def status(self):
        """Get fine status for display"""
        if not self.is_active:
            return 'Deactivated'
        elif self.is_paid:
            return 'Paid'
        elif not self.should_apply_now:
            return 'Pending'
        else:
            return 'Active'
    
    def __str__(self):
        if self.target_scope == 'Class' and self.class_section:
            return f"Class {self.class_section} - {self.fine_type} (₹{self.amount}, Due: {self.due_date})"
        elif self.target_scope == 'All':
            return f"All Students - {self.fine_type} (₹{self.amount}, Due: {self.due_date})"
        else:
            return f"Individual - {self.fine_type} (₹{self.amount}, Due: {self.due_date})"

    def save(self, *args, **kwargs):
        user = kwargs.pop('user', None)
        with transaction.atomic():
            # Calculate amount from percentage if needed (will be done in form save)
            if user:
                self.created_by = self.created_by or user
            super().save(*args, **kwargs)
            logger.info(f"Saved fine ID {self.id} with scope {self.target_scope}")
            
            # Update due amounts for affected students
            if hasattr(self, 'fine_students'):
                for fs in self.fine_students.all():
                    fs.student.update_due_amount()

# FineWaiver removed - use student_fees discount system instead

# FeeDepositFine removed - fine payments handled directly in student_fees

class FineStudent(BaseModel):
    fine = models.ForeignKey(Fine, on_delete=models.CASCADE, related_name='fine_students')
    student = models.ForeignKey('students.Student', on_delete=models.CASCADE)
    is_paid = models.BooleanField(default=False)
    is_waived = models.BooleanField(default=False)
    waived_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True, related_name='waived_fines')
    waived_date = models.DateTimeField(null=True, blank=True)
    payment_date = models.DateField(null=True, blank=True)
    calculated_amount = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)

    class Meta:
        indexes = [
            models.Index(fields=['fine', 'student']),
            models.Index(fields=['is_paid']),
        ]
        unique_together = ('fine', 'student')

    def __str__(self):
        return f"{self.student} - {self.fine}"
    
    @property
    def status(self):
        """Get fine student status"""
        if self.is_waived:
            return 'Waived'
        elif self.is_paid:
            return 'Paid'
        else:
            return 'Pending'
    
    def save(self, *args, **kwargs):
        super().save(*args, **kwargs)
        # Update student due amount when fine status changes
        if hasattr(self.student, 'update_due_amount'):
            self.student.update_due_amount()

class FineAuditLog(BaseModel):
    fine = models.ForeignKey(Fine, on_delete=models.CASCADE, related_name='audit_logs')
    action = models.CharField(max_length=50)
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT)
    timestamp = models.DateTimeField(auto_now_add=True)
    details = models.JSONField(default=dict)

    def __str__(self):
        return f"{self.action} on Fine {self.fine.id} by {self.user} at {self.timestamp}"

@receiver(post_save, sender='student_fees.FeeDeposit')
def check_due_fees(sender, instance, **kwargs):
    try:
        with transaction.atomic():
            fine_application_date = instance.deposit_date.date() + timedelta(days=7)
            
            if instance.paid_amount < instance.amount and timezone.now().date() >= fine_application_date:
                # Get or create system user
                system_user, _ = User.objects.get_or_create(
                    username='system',
                    defaults={'email': 'system@school.local', 'is_active': False}
                )
                
                # Get or create Late Fee fine type
                late_fee_type, _ = FineType.objects.get_or_create(
                    name="Late Fee",
                    defaults={'category': 'Late Fee', 'description': 'Auto-generated late fee'}
                )
                
                fine, created = Fine.objects.get_or_create(
                    target_scope='Individual',
                    fine_type=late_fee_type,
                    defaults={
                        'amount': (instance.amount - instance.paid_amount) * 0.05,
                        'reason': "Auto-generated late fee for unpaid fee deposit",
                        'due_date': timezone.now().date() + timedelta(days=7),
                        'auto_generated': True,
                        'created_by': system_user
                    }
                )
                
                if created:
                    FineStudent.objects.create(fine=fine, student=instance.student)
                    instance.student.update_due_amount()
                    logger.info(f"Created auto fine ID {fine.id} for student {instance.student}")
    except Exception as e:
        logger.error(f"Error in check_due_fees signal: {str(e)}")
        # Don't raise exception to avoid breaking the fee deposit process
            