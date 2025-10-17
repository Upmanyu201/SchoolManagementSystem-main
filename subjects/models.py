from django.db import models
from django.core.exceptions import ValidationError
from teachers.models import Teacher
import re

class ClassSectionManager(models.Manager):
    def ordered(self):
        """Return class sections in proper educational order"""
        from core.utils import extract_class_number
        
        all_classes = list(self.get_queryset())
        
        def class_sort_key(class_section):
            class_num = extract_class_number(class_section.class_name)
            return (class_num, class_section.section_name)
        
        return sorted(all_classes, key=class_sort_key)

class ClassSection(models.Model):
    class_name = models.CharField(max_length=50)
    section_name = models.CharField(max_length=10, blank=True, null=True)
    room_number = models.CharField(max_length=20, blank=True, null=True, unique=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    objects = ClassSectionManager()
    
    class Meta:
        app_label = 'subjects'
        unique_together = ['class_name', 'section_name']
    
    def __str__(self):
        return f"{self.class_name}{self.section_name or ''}"
    
    @property
    def display_name(self):
        return f"{self.class_name}{self.section_name or ''}"

class Subject(models.Model):
    name = models.CharField(max_length=100, unique=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        app_label = 'subjects'
    
    def __str__(self):
        return self.name

class SubjectAssignment(models.Model):
    class_section = models.ForeignKey(ClassSection, on_delete=models.CASCADE)
    subject = models.ForeignKey(Subject, on_delete=models.CASCADE)
    teacher = models.ForeignKey(Teacher, on_delete=models.SET_NULL, null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        app_label = 'subjects'
        unique_together = ['class_section', 'subject']
    
    def __str__(self):
        teacher_name = f" ({self.teacher.name})" if self.teacher else ""
        return f"{self.class_section} - {self.subject.name}{teacher_name}"

# Legacy models for backward compatibility
class Class(models.Model):
    name = models.CharField(max_length=50, unique=True)
    
    def __str__(self):
        return self.name

class Section(models.Model):
    name = models.CharField(max_length=10, unique=True)
    
    def __str__(self):
        return self.name