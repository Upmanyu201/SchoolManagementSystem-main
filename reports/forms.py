# reports/forms.py
from django import forms
from students.models import Student
from subjects.models import ClassSection
from django.core.exceptions import ValidationError
from datetime import date, timedelta

class ReportFilterForm(forms.Form):
    REPORT_TYPE_CHOICES = [
        ('fees', 'Fees Report'),
        ('attendance', 'Attendance Report'),
        ('students', 'Students Report'),
        ('fines', 'Fines Report'),
        ('transport', 'Transport Report')
    ]
    
    EXPORT_FORMAT_CHOICES = [
        ('pdf', 'PDF'),
        ('excel', 'Excel'),
        ('csv', 'CSV')
    ]
    
    report_type = forms.ChoiceField(
        choices=REPORT_TYPE_CHOICES,
        widget=forms.Select(attrs={
            'class': 'w-full p-2 border rounded-lg focus:ring-2 focus:ring-blue-500'
        })
    )
    class_section = forms.ModelChoiceField(
        queryset=ClassSection.objects.all(),
        required=False,
        empty_label="All Classes",
        widget=forms.Select(attrs={
            'class': 'w-full p-2 border rounded-lg focus:ring-2 focus:ring-blue-500'
        })
    )
    start_date = forms.DateField(
        required=False,
        widget=forms.DateInput(attrs={
            'type': 'date',
            'class': 'w-full p-2 border rounded-lg focus:ring-2 focus:ring-blue-500'
        })
    )
    end_date = forms.DateField(
        required=False,
        widget=forms.DateInput(attrs={
            'type': 'date',
            'class': 'w-full p-2 border rounded-lg focus:ring-2 focus:ring-blue-500'
        })
    )
    export_format = forms.ChoiceField(
        choices=EXPORT_FORMAT_CHOICES,
        widget=forms.Select(attrs={
            'class': 'w-full p-2 border rounded-lg focus:ring-2 focus:ring-blue-500'
        })
    )
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Set default dates
        self.fields['start_date'].initial = date.today() - timedelta(days=30)
        self.fields['end_date'].initial = date.today()
    
    def clean(self):
        cleaned_data = super().clean()
        start_date = cleaned_data.get('start_date')
        end_date = cleaned_data.get('end_date')
        
        if start_date and end_date and start_date > end_date:
            raise ValidationError("Start date cannot be after end date")
        
        return cleaned_data

class FeesReportForm(forms.Form):
    class_section = forms.ModelChoiceField(
        queryset=ClassSection.objects.all(),
        required=False,
        empty_label="All Classes",
        widget=forms.Select(attrs={
            'class': 'w-full p-2 border rounded-lg focus:ring-2 focus:ring-blue-500'
        })
    )
    payment_status = forms.ChoiceField(
        choices=[
            ('all', 'All Students'),
            ('paid', 'Paid Only'),
            ('unpaid', 'Unpaid Only'),
            ('partial', 'Partial Payment')
        ],
        widget=forms.Select(attrs={
            'class': 'w-full p-2 border rounded-lg focus:ring-2 focus:ring-blue-500'
        })
    )
    month_year = forms.CharField(
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'w-full p-2 border rounded-lg focus:ring-2 focus:ring-blue-500',
            'placeholder': 'MM/YYYY (e.g., 03/2024)'
        })
    )