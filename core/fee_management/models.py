# core/fee_management/models.py
"""
Centralized Fee Management Models
These models coordinate between fees, fines, and student_fees modules
"""

from django.db import models
from core.models import BaseModel
from django.conf import settings

class StudentFee(BaseModel):
    """Centralized student fee tracking"""
    student = models.ForeignKey('students.Student', on_delete=models.CASCADE, related_name='assigned_fees')
    fee_type = models.ForeignKey('fees.FeesType', on_delete=models.CASCADE)
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    due_date = models.DateField()
    is_paid = models.BooleanField(default=False)
    paid_date = models.DateField(null=True, blank=True)
    academic_year = models.CharField(max_length=20, default='2024-25')

    class Meta:
        unique_together = ('student', 'fee_type', 'academic_year')
        indexes = [
            models.Index(fields=['student', 'is_paid']),
            models.Index(fields=['due_date']),
        ]

    def __str__(self):
        return f"{self.student} - {self.fee_type} (₹{self.amount})"

class AppliedFine(BaseModel):
    """Centralized fine tracking"""
    student = models.ForeignKey('students.Student', on_delete=models.CASCADE, related_name='applied_fines')
    fine_template = models.ForeignKey('fines.FineTemplate', on_delete=models.CASCADE)
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    reason = models.TextField()
    applied_date = models.DateTimeField(auto_now_add=True)
    due_date = models.DateField()
    is_paid = models.BooleanField(default=False)
    paid_date = models.DateField(null=True, blank=True)
    auto_generated = models.BooleanField(default=False)

    class Meta:
        indexes = [
            models.Index(fields=['student', 'is_paid']),
            models.Index(fields=['applied_date']),
        ]

    def __str__(self):
        return f"{self.student} - {self.fine_template.name} (₹{self.amount})"

class PaymentAllocation(BaseModel):
    """Track how payments are allocated to fees and fines"""
    fee_deposit = models.ForeignKey('student_fees.FeeDeposit', on_delete=models.CASCADE, related_name='allocations')
    student_fee = models.ForeignKey(StudentFee, on_delete=models.CASCADE, null=True, blank=True)
    applied_fine = models.ForeignKey(AppliedFine, on_delete=models.CASCADE, null=True, blank=True)
    allocated_amount = models.DecimalField(max_digits=10, decimal_places=2)
    allocation_date = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        target = self.student_fee or self.applied_fine
        return f"₹{self.allocated_amount} → {target}"