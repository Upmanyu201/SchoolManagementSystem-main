from django import forms
from .models import ClassSection, Subject, SubjectAssignment
from teachers.models import Teacher

class ClassSectionForm(forms.ModelForm):
    class Meta:
        model = ClassSection
        fields = ['class_name', 'section_name', 'room_number']
        widgets = {
            'class_name': forms.TextInput(attrs={'class': 'form-input', 'placeholder': 'e.g., Class 1, Grade 10'}),
            'section_name': forms.TextInput(attrs={'class': 'form-input', 'placeholder': 'e.g., A, B, C'}),
            'room_number': forms.TextInput(attrs={'class': 'form-input', 'placeholder': 'e.g., R-101, Room-A1'}),
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Make section_name and room_number optional
        self.fields['section_name'].required = False
        self.fields['room_number'].required = False

class SubjectForm(forms.ModelForm):
    class Meta:
        model = Subject
        fields = ['name']
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-input', 'placeholder': 'e.g., Mathematics, English'}),
        }

class SubjectAssignmentForm(forms.ModelForm):
    class Meta:
        model = SubjectAssignment
        fields = ['class_section', 'subject', 'teacher']
        widgets = {
            'class_section': forms.Select(attrs={'class': 'form-select'}),
            'subject': forms.Select(attrs={'class': 'form-select'}),
            'teacher': forms.Select(attrs={'class': 'form-select'}),
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['teacher'].empty_label = "Select Teacher (Optional)"
        self.fields['teacher'].queryset = self.fields['teacher'].queryset.order_by('name')
        self.fields['class_section'].queryset = ClassSection.objects.all().order_by('class_name', 'section_name')