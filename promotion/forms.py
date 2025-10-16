# promotion/forms.py
from django import forms
from .models import PromotionRule
from students.models import Student
from subjects.models import ClassSection
from django.core.exceptions import ValidationError

class PromotionRuleForm(forms.ModelForm):
    class Meta:
        model = PromotionRule
        fields = ['from_class_section', 'to_class_section', 'minimum_percentage', 'academic_year']
        widgets = {
            'from_class_section': forms.Select(attrs={
                'class': 'w-full p-2 border rounded-lg focus:ring-2 focus:ring-blue-500'
            }),
            'to_class_section': forms.Select(attrs={
                'class': 'w-full p-2 border rounded-lg focus:ring-2 focus:ring-blue-500'
            }),
            'minimum_percentage': forms.NumberInput(attrs={
                'class': 'w-full p-2 border rounded-lg focus:ring-2 focus:ring-blue-500',
                'min': '0',
                'max': '100'
            }),
            'academic_year': forms.TextInput(attrs={
                'class': 'w-full p-2 border rounded-lg focus:ring-2 focus:ring-blue-500',
                'placeholder': '2024-25'
            })
        }

class BulkPromotionForm(forms.Form):
    from_class_section = forms.ModelChoiceField(
        queryset=ClassSection.objects.all(),
        widget=forms.Select(attrs={
            'class': 'w-full p-2 border rounded-lg focus:ring-2 focus:ring-blue-500'
        })
    )
    to_class_section = forms.ModelChoiceField(
        queryset=ClassSection.objects.all(),
        widget=forms.Select(attrs={
            'class': 'w-full p-2 border rounded-lg focus:ring-2 focus:ring-blue-500'
        })
    )
    academic_year = forms.CharField(
        max_length=10,
        widget=forms.TextInput(attrs={
            'class': 'w-full p-2 border rounded-lg focus:ring-2 focus:ring-blue-500',
            'placeholder': '2024-25'
        })
    )
    
    def clean(self):
        cleaned_data = super().clean()
        from_class = cleaned_data.get('from_class_section')
        to_class = cleaned_data.get('to_class_section')
        
        if from_class and to_class and from_class == to_class:
            raise ValidationError("From and To class cannot be the same")
        
        return cleaned_data