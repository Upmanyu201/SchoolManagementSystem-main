from django import forms
from .models import Teacher

class TeacherForm(forms.ModelForm):
    class Meta:
        model = Teacher
        fields = ['name', 'mobile', 'email', 'qualification', 'joining_date', 'photo', 'resume', 'joining_letter']
