# student_fees/models.py - CLEANED (Business logic moved to service)
from django.db import models
from students.models import Student

class FeeDeposit(models.Model):
    """Fee Deposit - UI-compatible, logic moved to service layer"""
    
    # Keep all existing fields for template compatibility
    student = models.ForeignKey(Student, on_delete=models.CASCADE, related_name='fee_deposits')
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    discount = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    paid_amount = models.DecimalField(max_digits=10, decimal_places=2)
    receipt_no = models.CharField(max_length=50)
    deposit_date = models.DateTimeField(auto_now_add=True)
    payment_mode = models.CharField(max_length=20, default='Cash')
    transaction_no = models.CharField(max_length=50, blank=True, null=True)
    payment_source = models.CharField(max_length=100, blank=True, null=True)
    note = models.TextField(blank=True, null=True)

    class Meta:
        ordering = ['-deposit_date']
        verbose_name = 'Fee Deposit'
        verbose_name_plural = 'Fee Deposits'

    def __str__(self):
        return f"{self.receipt_no} - {self.student} (₹{self.paid_amount})"

    def clean(self):
        """Validate model data"""
        from django.core.exceptions import ValidationError
        
        # Prevent empty receipt numbers
        if not self.receipt_no or len(self.receipt_no.strip()) < 5:
            raise ValidationError("Receipt number cannot be empty or too short")
        
        # Validate amounts
        if self.amount < 0:
            raise ValidationError("Amount cannot be negative")
        
        if self.paid_amount < 0:
            raise ValidationError("Paid amount cannot be negative")
    
    def save(self, *args, **kwargs):
        # Validate before saving
        self.full_clean()
        
        # Calculate paid amount if not set
        if not self.paid_amount:
            self.paid_amount = self.amount - (self.discount or 0)
        if self.paid_amount < 0:
            self.paid_amount = 0
            
        # Final validation for receipt number
        if not self.receipt_no or len(self.receipt_no.strip()) < 5:
            raise ValueError("Cannot save deposit with empty receipt number")
            
        super().save(*args, **kwargs)
