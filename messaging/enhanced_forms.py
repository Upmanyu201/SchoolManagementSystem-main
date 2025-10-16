from django import forms
from students.models import Student
from subjects.models import ClassSection as StudentClass
from .models import MessageTemplate

class CustomMessageForm(forms.Form):
    """Form for sending custom messages"""
    
    RECIPIENT_CHOICES = [
        ('individual', 'Individual Student'),
        ('class', 'Entire Class'),
        ('multiple', 'Multiple Students'),
        ('all', 'All Students'),
    ]
    
    PROVIDER_CHOICES = [
        ('auto', 'Auto (Use Default)'),
        ('twilio', 'Twilio'),
        ('messagecentral', 'MessageCentral'),
    ]
    
    recipient_type = forms.ChoiceField(
        choices=RECIPIENT_CHOICES,
        widget=forms.Select(attrs={
            'class': 'form-select',
            'onchange': 'toggleRecipientFields(this.value)'
        })
    )
    
    student_class = forms.ModelChoiceField(
        queryset=StudentClass.objects.all(),
        required=False,
        empty_label="Select Class",
        widget=forms.Select(attrs={'class': 'form-select'})
    )
    
    individual_student = forms.ModelChoiceField(
        queryset=Student.objects.all(),
        required=False,
        empty_label="Select Student",
        widget=forms.Select(attrs={'class': 'form-select'})
    )
    
    selected_students = forms.ModelMultipleChoiceField(
        queryset=Student.objects.all(),
        required=False,
        widget=forms.CheckboxSelectMultiple(attrs={'class': 'form-check-input'})
    )
    
    message = forms.CharField(
        widget=forms.Textarea(attrs={
            'class': 'form-textarea',
            'rows': 5,
            'placeholder': 'Enter your message here...',
            'maxlength': 1000
        }),
        max_length=1000,
        help_text="Maximum 1000 characters"
    )
    
    send_to_parents = forms.BooleanField(
        initial=True,
        required=False,
        widget=forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        help_text="Send message to parent's mobile number"
    )
    
    provider = forms.ChoiceField(
        choices=PROVIDER_CHOICES,
        initial='auto',
        widget=forms.Select(attrs={'class': 'form-select'})
    )
    
    def clean(self):
        cleaned_data = super().clean()
        recipient_type = cleaned_data.get('recipient_type')
        
        if recipient_type == 'individual' and not cleaned_data.get('individual_student'):
            raise forms.ValidationError("Please select a student for individual message.")
        
        if recipient_type == 'class' and not cleaned_data.get('student_class'):
            raise forms.ValidationError("Please select a class for class message.")
        
        if recipient_type == 'multiple' and not cleaned_data.get('selected_students'):
            raise forms.ValidationError("Please select students for multiple message.")
        
        return cleaned_data

class MessageTemplateForm(forms.ModelForm):
    """Form for creating/editing message templates"""
    
    class Meta:
        model = MessageTemplate
        fields = ['name', 'message_type', 'template_content']
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-input'}),
            'message_type': forms.Select(attrs={'class': 'form-select'}),
            'template_content': forms.Textarea(attrs={
                'class': 'form-textarea',
                'rows': 6,
                'placeholder': 'Enter template content with variables like {{ student_name }}, {{ amount }}, etc.'
            })
        }

class BulkMessageForm(forms.Form):
    """Form for sending bulk messages"""
    
    target_classes = forms.ModelMultipleChoiceField(
        queryset=StudentClass.objects.all(),
        required=False,
        widget=forms.CheckboxSelectMultiple(attrs={'class': 'form-check-input'})
    )
    
    message = forms.CharField(
        widget=forms.Textarea(attrs={
            'class': 'form-textarea',
            'rows': 5,
            'placeholder': 'Enter bulk message...'
        }),
        max_length=1000
    )
    
    include_parents_only = forms.BooleanField(
        initial=True,
        required=False,
        widget=forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        help_text="Send only to students with parent mobile numbers"
    )
    
    provider = forms.ChoiceField(
        choices=[
            ('auto', 'Auto (Use Default)'),
            ('twilio', 'Twilio'),
            ('messagecentral', 'MessageCentral'),
        ],
        initial='auto',
        widget=forms.Select(attrs={'class': 'form-select'})
    )