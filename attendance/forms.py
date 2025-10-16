# attendance/forms.py
from django import forms
from .models import Attendance
from students.models import Student
from subjects.models import ClassSection
from django.core.exceptions import ValidationError
from core.validators import EnhancedValidators
from core.security import SecurityEnhancements

class AttendanceForm(forms.ModelForm):
    class Meta:
        model = Attendance
        fields = ['student', 'date', 'status']
        widgets = {
            'date': forms.DateInput(attrs={
                'type': 'date',
                'class': 'w-full p-2 border rounded-lg focus:ring-2 focus:ring-blue-500'
            }),
            'status': forms.Select(attrs={
                'class': 'w-full p-2 border rounded-lg focus:ring-2 focus:ring-blue-500'
            })
        }

class BulkAttendanceForm(forms.Form):
    class_section = forms.ModelChoiceField(
        queryset=ClassSection.objects.all(),
        widget=forms.Select(attrs={
            'class': 'w-full p-2 border rounded-lg focus:ring-2 focus:ring-blue-500'
        })
    )
    date = forms.DateField(
        widget=forms.DateInput(attrs={
            'type': 'date',
            'class': 'w-full p-2 border rounded-lg focus:ring-2 focus:ring-blue-500'
        })
    )

class AttendanceReportForm(forms.Form):
    class_section = forms.ModelChoiceField(
        queryset=ClassSection.objects.all(),
        required=False,
        empty_label="All Classes",
        widget=forms.Select(attrs={
            'class': 'w-full p-2 border rounded-lg focus:ring-2 focus:ring-blue-500'
        })
    )
    start_date = forms.DateField(
        widget=forms.DateInput(attrs={
            'type': 'date',
            'class': 'w-full p-2 border rounded-lg focus:ring-2 focus:ring-blue-500'
        })
    )
    end_date = forms.DateField(
        widget=forms.DateInput(attrs={
            'type': 'date',
            'class': 'w-full p-2 border rounded-lg focus:ring-2 focus:ring-blue-500'
        })
    )
    
    def clean(self):
        cleaned_data = super().clean()
        start_date = cleaned_data.get('start_date')
        end_date = cleaned_data.get('end_date')
        
        if start_date and end_date:
            if start_date > end_date:
                raise ValidationError("Start date cannot be after end date")
            
            from datetime import timedelta
            if (end_date - start_date).days > 365:
                raise ValidationError("Date range cannot exceed 1 year")
        
        return SecurityEnhancements.sanitize_input(cleaned_data)