# D:\School-Management-System\School-Management-System-main\fees\models.py
from django.db import models
from core.models import BaseModel
from django.core.exceptions import ValidationError

class FeesGroup(BaseModel):
    # Fee Group Category Choices
    FEE_GROUP_CHOICES = [
        ('One Time', 'One Time'),
        ('Yearly', 'Yearly'),
        ("Half Yearly", 'Half Yearly'),
        ('Quarterly', 'Quarterly'),
        ('Monthly', 'Monthly'),
    ]

    # Group Type Choices
    GROUP_TYPE_CHOICES = [
        ('Admission Fees', 'Admission Fees'),
        ('Tuition Fee', 'Tuition Fee'),
        ('Transport', 'Transport'),
        ('Exam Fees', 'Exam Fees'),
        ('Development', 'Development'),
    ]

    # Fee Type Choices
    FEE_TYPE_CHOICES = [
        ('Class Based', 'Class Based'),
        ('Stoppage Based', 'Stoppage Based'),
        ('General', 'General'),
        ("Hostel Based", 'Hostel Based'),
    ]

    fee_group = models.CharField(max_length=50, choices=FEE_GROUP_CHOICES)
    group_type = models.CharField(max_length=50, choices=GROUP_TYPE_CHOICES)
    fee_type = models.CharField(max_length=50, choices=FEE_TYPE_CHOICES)
    related_class_section = models.ForeignKey('subjects.ClassSection', on_delete=models.SET_NULL, null=True, blank=True)
    related_stoppage = models.ForeignKey('transport.Stoppage', on_delete=models.SET_NULL, null=True, blank=True)

    def __str__(self):
        return f"{self.fee_group} - {self.group_type}"

class FeesType(BaseModel):
    # Core fields
    fee_group = models.ForeignKey('FeesGroup', on_delete=models.CASCADE, related_name='fee_types')
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    amount_type = models.CharField(max_length=50)  # USER INPUT: e.g., Jan25, Mar25, Quarterly
    
    # Context fields
    context_type = models.CharField(max_length=50, choices=[
        ('monthly', 'Monthly'),
        ('class_based', 'Class Based'),
        ('stoppage_based', 'Stoppage Based'),
        ('general', 'General'),
        ('quarterly', 'Quarterly'),
        ('yearly', 'Yearly'),
        ('one_time', 'One Time'),
    ], default='general')
    
    context_data = models.JSONField(default=dict)
    
    # Display fields (populated from context)
    month_name = models.CharField(max_length=50, blank=True, null=True)
    class_name = models.CharField(max_length=100, blank=True, null=True)
    stoppage_name = models.CharField(max_length=100, blank=True, null=True)
    
    # Legacy field for compatibility
    related_stoppage = models.ForeignKey(
        'transport.Stoppage',
        on_delete=models.SET_NULL,
        blank=True,
        null=True,
        related_name='fees_feestypes'
    )

    class Meta:
        unique_together = ('fee_group', 'amount_type', 'month_name', 'class_name', 'stoppage_name')

    def save(self, *args, **kwargs):
        """Populate display fields from context_data"""
        if self.context_type == 'monthly' and self.context_data.get('months'):
            self.month_name = ', '.join(self.context_data['months'])
        
        elif self.context_type == 'class_based' and self.context_data.get('classes'):
            self.class_name = ', '.join(self.context_data['classes'])
        
        elif self.context_type == 'stoppage_based' and self.context_data.get('stoppages'):
            self.stoppage_name = ', '.join(self.context_data['stoppages'])
        
        super().save(*args, **kwargs)
    
    @property
    def group_type(self):
        return self.fee_group.group_type if self.fee_group else 'Unknown'
    
    @property
    def fee_type(self):
        return self.fee_group.fee_type if self.fee_group else 'Unknown'
    
    @property
    def display_format(self):
        """Return: Group Type | Month Name | Class/Stoppage Name | Amount Type | Amount"""
        group_type = self.group_type
        month_part = self.month_name or 'General'
        class_stoppage_part = self.class_name or self.stoppage_name or 'General'
        
        return f"{group_type} | {month_part} | {class_stoppage_part} | {self.amount_type} | {self.amount}"

    def __str__(self):
        return self.display_format

