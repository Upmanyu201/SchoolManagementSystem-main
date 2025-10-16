from django import forms
from .models import SchoolProfile
from django.core.validators import FileExtensionValidator

class SchoolProfileForm(forms.ModelForm):
    class Meta:
        model = SchoolProfile
        fields = '__all__'
        widgets = {
            'start_date': forms.DateInput(attrs={'type': 'date'}),
            'end_date': forms.DateInput(attrs={'type': 'date'}),
            'address': forms.Textarea(attrs={'rows': 3}),
        }
    
    logo = forms.ImageField(
        required=False,
        validators=[FileExtensionValidator(allowed_extensions=['jpg', 'jpeg', 'png'])],
        widget=forms.FileInput(attrs={'accept': 'image/*'})
    )
    
    academic_calendar = forms.FileField(
        required=False,
        validators=[FileExtensionValidator(allowed_extensions=['pdf', 'docx', 'xlsx'])],
        widget=forms.FileInput(attrs={'accept': '.pdf,.docx,.xlsx'})
    )

    def clean(self):
        cleaned_data = super().clean()
        start_date = cleaned_data.get('start_date')
        end_date = cleaned_data.get('end_date')
        
        if start_date and end_date and start_date >= end_date:
            raise forms.ValidationError("End date must be after start date")
        
        return cleaned_data