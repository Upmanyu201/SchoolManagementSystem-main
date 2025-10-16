# D:\School-Management-System\School-Management-System-main\promotion\models.py
from django.db import models
from core.models import BaseModel
from django.core.exceptions import ValidationError

class PromotionRule(BaseModel):
    from_class_section = models.ForeignKey('subjects.ClassSection', on_delete=models.CASCADE, related_name='promotion_from', null=True, blank=True)
    to_class_section = models.ForeignKey('subjects.ClassSection', on_delete=models.CASCADE, related_name='promotion_to', null=True, blank=True)
    minimum_percentage = models.DecimalField(max_digits=5, decimal_places=2, default=0.00)
    academic_year = models.CharField(max_length=10, default='2024-25')
    
    # Legacy fields for backward compatibility
    current_class_section = models.ForeignKey('subjects.ClassSection', on_delete=models.CASCADE, related_name='legacy_promotion_from', null=True, blank=True)
    next_class_section = models.ForeignKey('subjects.ClassSection', on_delete=models.CASCADE, related_name='legacy_promotion_to', null=True, blank=True)
    name = models.CharField(max_length=100, blank=True)
    min_marks = models.IntegerField(null=True, blank=True)
    
    class Meta:
        unique_together = ('from_class_section', 'to_class_section', 'academic_year')

    def clean(self):
        super().clean()
        if self.from_class_section == self.to_class_section:
            raise ValidationError('From class and to class cannot be the same.')

    def __str__(self):
        return f"{self.from_class_section} → {self.to_class_section} ({self.academic_year})"

class StudentPromotion(BaseModel):
    student = models.ForeignKey('students.Student', on_delete=models.CASCADE, related_name='promotions')
    from_class_section = models.ForeignKey('subjects.ClassSection', on_delete=models.CASCADE, related_name='student_promotions_from')
    to_class_section = models.ForeignKey('subjects.ClassSection', on_delete=models.CASCADE, related_name='student_promotions_to')
    academic_year = models.CharField(max_length=10, default='2024-25')
    promotion_date = models.DateField(auto_now_add=True)
    remarks = models.TextField(blank=True)
    
    class Meta:
        unique_together = ('student', 'academic_year')
    
    def __str__(self):
        return f"{self.student.name} - {self.from_class_section} → {self.to_class_section}"
